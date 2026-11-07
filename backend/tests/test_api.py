from datetime import datetime,timedelta,timezone
from backend.app.core import Session,Record,add
from backend.app.main import app
from fastapi.testclient import TestClient

def test_auth_logout_and_unauthorized(clients):
    a,b=clients
    with TestClient(app) as anonymous:
        assert anonymous.get('/api/analytics/dashboard').status_code==401
        assert anonymous.post('/api/auth/login',json={'email':'bank_a@federguard.demo','password':'wrong-password!'}).status_code==401
    assert a.get('/api/auth/me').json()['role']=='admin'
    assert a.post('/api/auth/logout').status_code==200
    assert a.get('/api/auth/me').status_code==401

def test_tenant_isolation_cases_and_queries(clients):
    a,b=clients
    r=a.post('/api/investigations',json={'title':'Synthetic case'});assert r.status_code==201
    id=r.json()['id']
    assert b.get('/api/investigations/'+id).status_code==404
    assert b.post('/api/investigations/'+id+'/notes',json={'text':'Intrusion'}).status_code==404
    assert a.post('/api/investigations/'+id+'/notes',json={'text':'Reviewing evidence'}).status_code==200
    assert a.put('/api/investigations/'+id+'/status',json={'status':'FALSE_POSITIVE'}).status_code==200
    assert a.get('/api/investigations/'+id).json()['history'][-1]['to']=='FALSE_POSITIVE'
    q=a.post('/api/rag/query',json={'question':'velocity'}).json()
    assert b.get('/api/rag/evidence/'+q['id']).status_code==404

def test_documents_permissions_and_ingestion(clients):
    a,b=clients
    r=a.post('/api/rag/ingest',files={'file':('private.txt',b'Zephyrcode confidential test policy: never share this private evidence.')},data={'title':'Private Zephyrcode','sharing':'private'})
    assert r.status_code==201
    assert not any(d['title']=='Private Zephyrcode' for d in b.get('/api/rag/documents').json())
    assert b.post('/api/rag/query',json={'question':'Zephyrcode'}).json()['evidence']==[]
    assert a.post('/api/rag/query',json={'question':'Zephyrcode'}).json()['evidence']
    assert a.post('/api/rag/ingest',files={'file':('bad.exe',b'bad')},data={'title':'Invalid'}).status_code==415
    assert a.post('/api/rag/ingest',files={'file':('bad.pdf',b'bad')},data={'title':'Invalid'}).status_code==422
    assert a.post('/api/rag/ingest',files={'file':('large.txt',b'a'*(5*1024*1024+1))},data={'title':'Too large'}).status_code==413

def test_cross_bank_approval_and_no_self_review(clients):
    a,b=clients
    docs=a.get('/api/rag/documents').json()
    payload={'title':'Synthetic pattern review','category':'Velocity','summary':'Synthetic repeated payments warrant local investigation and corroboration.','evidence_refs':[docs[0]['id']],'confidence':.7,'sharing':'consortium','privacy_classification':'synthetic','expires_at':(datetime.now(timezone.utc)+timedelta(days=30)).isoformat()}
    r=a.post('/api/intelligence/contribute',json=payload);assert r.status_code==201
    id=r.json()['id']
    assert b.get('/api/intelligence/'+id).status_code==404
    assert a.post('/api/intelligence/'+id+'/review',json={'status':'approved'}).status_code==403
    assert b.post('/api/intelligence/'+id+'/review',json={'status':'approved'}).status_code==404
    payload['account_number']='not-allowed'
    assert a.post('/api/intelligence/contribute',json=payload).status_code==422

def test_role_enrollment_and_configuration(clients):
    a,b=clients
    assert b.post('/api/banks',json={'id':'bank_d','name':'Fourth bank'}).status_code==403
    assert a.post('/api/banks',json={'id':'bank_d','name':'Fourth bank'}).status_code==201
    assert a.post('/api/banks/bank_d/enroll-client').status_code==409
    assert a.put('/api/privacy/config',json={'noise_multiplier':0}).status_code==422
    assert a.put('/api/privacy/config',json={'enabled':True,'noise_multiplier':1.5}).status_code==200
    assert a.get('/api/privacy/config').json()['noise_multiplier']==1.5
    assert b.put('/api/privacy/config',json={}).status_code==403

def test_rag_citations_graph_and_agents(clients):
    a,b=clients
    r=a.post('/api/rag/query',json={'question':'suspicious velocity payments'});assert r.status_code==200
    answer=r.json();assert answer['evidence'];assert '[1]' in answer['answer']
    assert a.post('/api/rag/query',json={'question':'zyxwv nonexistent'}).json()['evidence']==[]
    g=a.get('/api/graph/patterns').json();assert g['nodes'] and g['edges'] and g['communities']
    r=a.post('/api/agents/run',json={'question':'suspicious velocity'});assert r.status_code==200
    assert r.json()['status']=='completed';assert len(r.json()['trace'])==13

def test_origin_and_registration(clients):
    a,b=clients
    assert a.post('/api/investigations',json={'title':'Injected case'},headers={'Origin':'https://untrusted.example'}).status_code==403
    assert a.post('/api/auth/register',json={'email':'new@bank.demo','password':'new-test-password','bank_id':'bank_a'}).status_code==403
    assert a.post('/api/auth/register',headers={'X-Registration-Invite':'test-invite'},json={'email':'new@bank.demo','password':'new-test-password','bank_id':'bank_a'}).status_code==201

def test_privacy_payload_and_round_validation(clients):
    a,b=clients
    assert a.post('/api/federated/rounds/start',json={'bank_ids':['bank_a','bank_a']}).status_code==422
    assert a.post('/api/federated/rounds/start',json={'bank_ids':['bank_a','unknown']}).status_code==422
    assert b.post('/api/federated/rounds/start',json={}).status_code==403
    status=a.get('/api/privacy/status').json();assert status['latest_epsilon'] is None
    assert 'SIMULATION' in status['secure_aggregation']

def test_no_customer_records_in_coordinator_schema():
    from backend.app.core import Base
    assert not any('transaction' in name for name in Base.metadata.tables)

def test_login_accepts_seeded_demo_password_but_signup_keeps_policy(clients):
    from backend.app.core import User,password_hash
    from sqlalchemy import select
    a,b=clients
    with Session() as db:
        user=db.scalar(select(User).where(User.email=='bank_a@federguard.demo'))
        user.password=password_hash('demo@2026');db.commit()
    assert a.post('/api/auth/login',json={'email':'bank_a@federguard.demo','password':'demo@2026'}).status_code==200
    assert a.post('/api/auth/register',json={'email':'short@demo.example','password':'demo@2026'}).status_code==422
