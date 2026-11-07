"""Provision isolated Neon roles and deploy Vercel services. Secrets never print."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from urllib.parse import urlsplit,urlunsplit,quote
from dotenv import dotenv_values
import psycopg
from psycopg import sql

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'runtime/cloud'
PNPM=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.cjs'
CLI=['node',str(PNPM),'dlx','vercel']
FRONTEND='https://federguard-ai.vercel.app'
SENSITIVE=[]
def log(text): print(text,flush=True)
def redact(text):
    for value in SENSITIVE:
        if value:text=text.replace(value,'[redacted]')
    return text
def vc(args,cwd=ROOT,body=None,check=True):
    p=subprocess.run(CLI+args,cwd=cwd,input=body,text=True,encoding='utf-8',errors='replace',capture_output=True)
    if p.returncode and check:
        raise RuntimeError(redact((p.stdout+p.stderr)[-9000:]))
    return p
def api(endpoint,method='GET',data=None):
    args=['api',endpoint,'--method',method]
    temporary=None
    if data is not None:
        temporary=ROOT/'runtime'/('vercel-request-'+secrets.token_hex(8)+'.json')
        temporary.write_text(json.dumps(data),encoding='utf-8')
        args+=['--input',str(temporary)]
    try:p=vc(args)
    except Exception as e:raise RuntimeError(endpoint+': '+str(e))
    finally:
        if temporary:temporary.unlink(missing_ok=True)
    return json.loads(p.stdout) if p.stdout.strip() else {}
def stage(kind):
    folder=WORK/kind;folder.mkdir(parents=True,exist_ok=True)
    for name in ['backend','bank_clients']:
        shutil.copytree(ROOT/name,folder/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','tests','*.pyc'))
    bank=kind!='backend'
    entry="import os\nos.environ.setdefault('RUNTIME_DIR','/tmp/federguard')\n"
    if bank:entry+="os.environ.setdefault('BANK_DATA_DIR','/tmp/'+os.environ['BANK_ID'])\nfrom bank_clients.node import app\n"
    else:entry+="os.environ.setdefault('DP_ACCOUNTANT','google_rdp')\nfrom backend.app.main import app\n"
    (folder/'app.py').write_text(entry)
    (folder/'.python-version').write_text('3.12\n')
    deps=(ROOT/'backend/requirements-cloud.txt').read_text().splitlines()
    if bank:deps=['fastapi>=0.115,<1','uvicorn>=0.30,<1','pydantic-settings>=2,<3','numpy>=1.26,<3','scikit-learn>=1.5,<2','psycopg[binary]>=3,<4','dp-accounting>=0.6,<1']
    (folder/'requirements.txt').write_text('\n'.join(x for x in deps if x and not x.startswith('#'))+'\n')
    (folder/'vercel.json').write_text(json.dumps({'$schema':'https://openapi.vercel.sh/vercel.json','framework':'fastapi','functions':{'app.py':{'maxDuration':300,'excludeFiles':'{backend/tests/**,**/__pycache__/**,runtime/**,bank_clients/__pycache__/**}'}}},indent=2))
    (folder/'.vercelignore').write_text('.env*\nruntime\n**/__pycache__\n**/*.pyc\n')
    return folder
def linked(kind):
    folder=stage(kind);project='federguard-api' if kind=='backend' else 'federguard-'+kind.replace('_','-')
    if not (folder/'.vercel/project.json').exists():
        p=vc(['project','add',project],check=False)
        if p.returncode and 'already exists' not in (p.stdout+p.stderr).lower():raise RuntimeError(redact(p.stderr))
        vc(['link','--project',project,'--yes'],cwd=folder)
    meta=json.loads((folder/'.vercel/project.json').read_text())
    return folder,meta['projectId']
def env_set(project_id,values):
    for key,value in values.items():
        vc(['env','add',key,'--project',project_id,'--environment','production','--force','--yes'],body=str(value)+'\n')
def deploy(folder):
    log('Deploying '+folder.name+'...')
    p=vc(['--prod','--yes'],cwd=folder)
    combined=p.stdout+p.stderr
    import re
    match=re.search(r'\{\s*"status"\s*:\s*"ok"',combined)
    if match:
        obj=json.JSONDecoder().raw_decode(combined[match.start():])[0]
        url=obj['deployment']['productionUrl']
    else:
        urls=re.findall(r'https://[A-Za-z0-9.-]+\.vercel\.app',combined)
        if not urls:raise RuntimeError(redact(combined[-6000:]))
        url=urls[-1]
    log('Ready '+folder.name+': '+url)
    return url
def secrets_state():
    path=WORK/'service-secrets.json'
    if path.exists():return json.loads(path.read_text())
    state={k:{'role':'fg_'+k,'password':secrets.token_urlsafe(32),'client_key':secrets.token_urlsafe(32)} for k in ['backend','bank_a','bank_b','bank_c']}
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(state))
    return state
def provision(state):
    values=dotenv_values(ROOT/'runtime/neon-provision.env')
    source=values.get('DATABASE_URL_UNPOOLED') or values.get('POSTGRES_URL_NON_POOLING') or values.get('DATABASE_URL')
    if not source:raise RuntimeError('No Neon provisioning connection found')
    SENSITIVE.append(source)
    parts=urlsplit(source)
    # Non-pooled endpoint is needed for coordinator session advisory locks.
    hostname=parts.hostname.replace('-pooler.','.')
    with psycopg.connect(source,autocommit=True) as db:
        db.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
        for kind,item in state.items():
            role=item['role'];schema='coordinator' if kind=='backend' else kind
            exists=db.execute('SELECT 1 FROM pg_roles WHERE rolname=%s',(role,)).fetchone()
            if not exists:db.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role),sql.Literal(item['password'])))
            else:db.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role),sql.Literal(item['password'])))
            db.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(schema)))
            db.execute(sql.SQL('GRANT USAGE, CREATE ON SCHEMA {} TO {}').format(sql.Identifier(schema),sql.Identifier(role)))
            db.execute(sql.SQL('ALTER ROLE {} SET search_path TO {}').format(sql.Identifier(role),sql.Identifier(schema)))
            item['url']=urlunsplit((parts.scheme,quote(role)+':'+quote(item['password'])+'@'+hostname+((':'+str(parts.port)) if parts.port else ''),parts.path,parts.query, ''))
            SENSITIVE.extend([item['password'],item['client_key'],item['url']])
        check=db.execute("SELECT has_schema_privilege('fg_backend','bank_a','USAGE'),has_schema_privilege('fg_bank_a','bank_b','USAGE')").fetchone()
        if any(check):raise RuntimeError('Database role isolation check failed')
    log('Neon coordinator/bank roles isolated: coordinator cannot access bank schemas.')
    return state

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage-only',action='store_true');a=parser.parse_args()
    projects={k:linked(k) for k in ['backend','bank_a','bank_b','bank_c']}
    state=provision(secrets_state())
    # Remove integration owner connection variables before assigning restricted roles.
    p=vc(['integration','resource','disconnect','store_AoD9HJ65K9t3BBDZ','federguard-api','--yes'],check=False)
    if p.returncode and not any(s in (p.stdout+p.stderr).lower() for s in ['not connected','no connection','not found']):raise RuntimeError(redact(p.stdout+p.stderr))
    urls={}
    for bank in ['bank_a','bank_b','bank_c']:
        folder,id=projects[bank]
        env_set(id,{'BANK_ID':bank,'BANK_DATABASE_URL':state[bank]['url'],'BANK_CLIENT_KEY':state[bank]['client_key'],'DP_ACCOUNTANT':'google_rdp'})
    if a.stage_only:return
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(lambda b:(b,deploy(projects[b][0])),['bank_a','bank_b','bank_c']))
        urls.update(results)
    local=dotenv_values(ROOT/'.env')
    local['DEMO_PASSWORD']=local.get('CLOUD_DEMO_PASSWORD') or local['DEMO_PASSWORD']
    backend_env={'DATABASE_URL':state['backend']['url'].replace('postgresql://','postgresql+psycopg://',1),'SERVERLESS':'true','CLOUD_SCHEMA_READY':'true','DEMO':'true','DEMO_PASSWORD':local['DEMO_PASSWORD'],'FRONTEND_ORIGIN':FRONTEND,'COOKIE_SECURE':'true','LLM_PROVIDER':'demo','RUNTIME_DIR':'/tmp/federguard','DP_ACCOUNTANT':'google_rdp'}
    SENSITIVE.append(local['DEMO_PASSWORD'])
    for bank,url in urls.items():backend_env[bank.upper()+'_ENDPOINT']=url;backend_env[bank.upper()+'_CLIENT_KEY']=state[bank]['client_key']
    # Initialize the coordinator schema using only its own restricted role.
    env={**os.environ,**backend_env,'RUNTIME_DIR':str(WORK/'bootstrap')}
    p=subprocess.run([sys.executable,'-c','from backend.app.core import Base,engine,Session; from backend.app.main import seed; Base.metadata.create_all(engine); db=Session(); seed(db); db.close(); print("Coordinator schema initialized")'],cwd=ROOT,env=env,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(redact(p.stderr[-7000:]))
    folder,id=projects['backend'];env_set(id,backend_env);urls['backend']=deploy(folder)
    (WORK/'deployment.json').write_text(json.dumps(urls,indent=2))
    log('Backend services deployed. '+json.dumps(urls))

if __name__=='__main__':
    try:main()
    except Exception as e:log(redact(str(e)));raise SystemExit(1)
