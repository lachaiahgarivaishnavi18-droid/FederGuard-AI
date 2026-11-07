"""End-to-end synthetic smoke test against the public Vercel frontend/API proxy."""
import json
import os
from pathlib import Path
import time
import httpx
from dotenv import load_dotenv

load_dotenv('.env')
ORIGIN='https://federguard-ai.vercel.app'
with httpx.Client(base_url=ORIGIN,timeout=180,headers={'Origin':ORIGIN},follow_redirects=True) as client:
    def call(method,path,**kwargs):
        response=client.request(method,path,**kwargs)
        if response.status_code>=400: raise RuntimeError(f'{path}: {response.status_code}: {response.text[:800]}')
        return response.json()
    login=call('POST','/api/auth/login',json={'email':'bank_a@federguard.demo','password':os.getenv('CLOUD_DEMO_PASSWORD') or os.environ['DEMO_PASSWORD']})
    assert call('GET','/api/auth/me')['role']=='admin'
    print('Live login and secure same-origin cookie: PASS',flush=True)
    round=call('POST','/api/federated/rounds/start',json={'strategy':'FedAvg','steps':3})
    for _ in range(90):
        if round['status']!='running':break
        time.sleep(1);round=call('GET','/api/federated/rounds/'+round['id'])
    assert round['status']=='completed',round
    assert round['successful']==3,round
    print('Live federated round: PASS; version',round['version'],flush=True)
    alert=call('POST','/api/fraud/detect',json={'amount':1800,'velocity':12,'device_risk':.8,'geo_deviation':.7,'account_age':60,'hour':2})
    answer=call('POST','/api/ai/chat',json={'question':'What patterns are associated with suspicious transaction velocity?'})
    assert answer['evidence'] and '[1]' in answer['answer']
    case=call('POST','/api/investigations',json={'title':'Cloud deployment verification: '+alert['transaction_reference'],'alert_id':alert['id'],'evidence_refs':list(dict.fromkeys(e['document_id'] for e in answer['evidence']))})
    case=call('PUT','/api/investigations/'+case['id']+'/status',json={'status':'UNDER_REVIEW'})
    case=call('POST','/api/investigations/'+case['id']+'/notes',json={'text':'Automated synthetic deployment verification. Reviewed cited velocity evidence and model contributions. Human assessment remains pending; no customer decision was made.'})
    assert call('GET','/api/investigations/'+case['id'])['notes']
    graph=call('GET','/api/graph/patterns');assert graph['nodes']
    privacy=call('GET','/api/privacy/status')
    assert privacy['latest_epsilon']>0
    assert 'Google' in privacy['mechanism']
    report={'origin':ORIGIN,'backend':'https://federguard-api.vercel.app','synthetic_only':True,'checks':{'login':True,'session_cookie':True,'three_bank_round':True,'local_risk_scoring':True,'cited_retrieval':True,'case_creation_notes_and_review':True,'graph':True,'persistent_privacy_accounting':True},'round':round,'alert':alert,'case':case,'privacy':privacy,'evidence_source_count':len(answer['evidence'])}
    Path('docs/reports/cloud-deployment.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Live scoring, cited retrieval, case review, graph and Neon accounting: PASS',flush=True)
    print(json.dumps({'app':ORIGIN,'case_title':case['title'],'model_version':round['version'],'epsilon':privacy['latest_epsilon']}),flush=True)
