"""Coordinator orchestration: authenticated calls, no filesystem access to bank data."""
import os
import time
from concurrent.futures import ThreadPoolExecutor
import httpx
from sqlalchemy import select
from backend.ml import fedavg, evaluate
from .core import Session, Bank, Record, Participation, add, serialize, now
from .schemas import RoundInput, Privacy

def latest_model(db):
    records=db.scalars(select(Record).where(Record.kind=='model').order_by(Record.created_at.desc())).all()
    return records[0].payload if records else {'version':0,'parameters':[0.0]*7}
def privacy_config(db):
    r=db.get(Record,'privacy-config')
    return Privacy(**r.payload) if r else Privacy()
def run_round(round_id: str, config: dict):
    req=RoundInput(**config)
    with Session() as db:
        record=db.get(Record,round_id); model=latest_model(db); privacy=privacy_config(db)
        banks=db.scalars(select(Bank).where(Bank.id.in_(req.bank_ids),Bank.active==True)).all()
        body={'round_id':round_id,'version':model['version'],'parameters':model['parameters'],'steps':req.steps,'strategy':req.strategy,'proximal_mu':req.proximal_mu,'privacy':privacy.model_dump()}
        start=time.perf_counter()
        def call(bank):
            if bank.id==req.dropout_bank: return bank.id,None,'Simulated dropout'
            try:
                key=os.environ.get(f'{bank.id.upper()}_CLIENT_KEY','')
                with httpx.Client(timeout=90,trust_env=False) as client:
                    response=client.post(bank.endpoint+'/train',json=body,headers={'X-Client-Key':key})
                    response.raise_for_status(); u=response.json()
                allowed={'bank_id','round_id','version','parameters','weight','duration','epsilon','delta','dp_enabled','mechanism','synthetic'}
                if set(u)!=allowed or u['bank_id']!=bank.id or u['round_id']!=round_id or u['version']!=model['version'] or u['weight']!=1:
                    raise ValueError('Rejected update envelope')
                if u['dp_enabled']!=privacy.enabled: raise ValueError('Privacy mismatch')
                import math
                if privacy.enabled and (not isinstance(u['epsilon'],(int,float)) or not math.isfinite(u['epsilon']) or u['epsilon']>privacy.max_epsilon or u['delta']!=privacy.delta): raise ValueError('Invalid privacy accounting')
                return bank.id,u,None
            except Exception as e: return bank.id,None,type(e).__name__
        with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(call,banks))
        updates=[]; clients=[]
        for bank_id,u,error in results:
            meta={k:v for k,v in (u or {}).items() if k!='parameters'}
            clients.append({'bank_id':bank_id,'status':'failed' if error else 'completed','error':error,**meta})
            db.add(Participation(round_id=round_id,bank_id=bank_id,status='failed' if error else 'completed',metadata_json=meta))
            if u:
                updates.append(u)
                add(db,'privacy-event',{'round_id':round_id,**meta},bank_id)
        agg_start=time.perf_counter()
        payload={**record.payload,'clients':clients,'successful':len(updates),'failed':len(results)-len(updates),'duration':time.perf_counter()-start,'completed_at':now()}
        try:
            parameters=fedavg(updates)
            version=model['version']+1
            evaluation=evaluate(parameters)
            import hashlib,json
            artifact=hashlib.sha256(json.dumps(parameters).encode()).hexdigest()
            add(db,'model',{'version':version,'parameters':parameters,'metrics':evaluation,'sha256':artifact,'round_id':round_id,'evaluation_source':'public synthetic holdout','aggregation':'Flower FedAvg; plaintext simulation','privacy':privacy.model_dump()})
            payload.update(status='completed',version=version,metrics=evaluation,aggregation_duration=time.perf_counter()-agg_start)
        except Exception as e: payload.update(status='failed',error=str(e))
        record.payload=payload; db.commit()
