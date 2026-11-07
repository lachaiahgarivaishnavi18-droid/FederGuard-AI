import httpx
from backend.app.core import Session,Record,add
from backend.app.federation import run_round

def test_round_dropout_and_versioning(clients,monkeypatch):
    a,b=clients
    def post(self,url,json,headers):
        bank='bank_a' if ':8101' in url else 'bank_b'
        return httpx.Response(200,request=httpx.Request('POST',url),json={'bank_id':bank,'round_id':json['round_id'],'version':json['version'],'parameters':[.1]*7,'weight':1,'duration':.1,'epsilon':7.,'delta':1e-5,'dp_enabled':True,'mechanism':'test fixture','synthetic':True})
    monkeypatch.setattr(httpx.Client,'post',post)
    with Session() as db:
        r=add(db,'round',{'status':'running'});id=r.id;db.commit()
    run_round(id,{'dropout_bank':'bank_c'})
    with Session() as db:
        r=db.get(Record,id)
        assert r.payload['status']=='completed' and r.payload['successful']==2 and r.payload['failed']==1
        assert r.payload['version']==1
        assert 'parameters' not in str(r.payload['clients'])

def test_round_rejects_raw_payload_and_insufficient_quorum(clients,monkeypatch):
    a,b=clients
    def post(self,url,json,headers):
        return httpx.Response(200,request=httpx.Request('POST',url),json={'transactions':[{'account':'forbidden'}]})
    monkeypatch.setattr(httpx.Client,'post',post)
    with Session() as db:
        r=add(db,'round',{'status':'running'});id=r.id;db.commit()
    run_round(id,{})
    with Session() as db:
        r=db.get(Record,id)
        assert r.payload['status']=='failed' and r.payload['successful']==0
        assert 'account' not in str(r.payload)
