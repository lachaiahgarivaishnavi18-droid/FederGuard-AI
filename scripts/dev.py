"""Cross-platform local launcher; credentials stay in .env, never command arguments."""
import argparse
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
def initialize():
    path=ROOT/'.env'
    if path.exists(): print('.env already exists; preserving existing configuration.'); return
    lines=['DEMO=true','DEMO_PASSWORD='+secrets.token_urlsafe(20),'DATABASE_URL=sqlite:///runtime/coordinator.db','FRONTEND_ORIGIN=http://localhost:5173','LLM_PROVIDER=demo']
    for i,b in enumerate(['BANK_A','BANK_B','BANK_C']):
        lines += [b+'_CLIENT_KEY='+secrets.token_urlsafe(32),b+'_ENDPOINT=http://127.0.0.1:'+str(8101+i),b+'_REGISTRATION_INVITE='+secrets.token_urlsafe(32)]
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Created ignored .env with unique credentials. Read DEMO_PASSWORD there to sign in.')
def command(target):
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    env=os.environ.copy()
    if target=='backend': cmd=[sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000']
    else:
        index=['bank_a','bank_b','bank_c'].index(target)
        env.update(BANK_ID=target,BANK_CLIENT_KEY=os.getenv(target.upper()+'_CLIENT_KEY',''))
        cmd=[sys.executable,'-m','uvicorn','bank_clients.node:app','--host','127.0.0.1','--port',str(8101+index)]
    return cmd,env
def run(target):
    cmd,env=command(target)
    subprocess.run(cmd,cwd=ROOT,env=env,check=True)
def all_services():
    children=[]
    try:
        for target in ['backend','bank_a','bank_b','bank_c']:
            cmd,env=command(target)
            children.append(subprocess.Popen(cmd,cwd=ROOT,env=env))
        print('Coordinator http://127.0.0.1:8000/docs; nodes 8101–8103. Start frontend in a second terminal. Ctrl+C stops services.')
        while all(p.poll() is None for p in children): time.sleep(1)
    except KeyboardInterrupt: pass
    finally:
        for child in children:
            child.terminate()
        for child in children:
            try: child.wait(timeout=10)
            except subprocess.TimeoutExpired: child.kill()
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('target',choices=['init','all','backend','bank_a','bank_b','bank_c']); args=parser.parse_args()
    if args.target=='init': initialize()
    elif args.target=='all': all_services()
    else: run(args.target)
