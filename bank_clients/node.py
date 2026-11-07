"""Independent bank process. This module is never imported by the coordinator."""
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
import numpy as np
from fastapi import FastAPI, Depends, Header, HTTPException
from backend.ml import synthetic, transform, sigmoid, FEATURES
from backend.app.schemas import TrainRequest, Features

BANK = os.getenv('BANK_ID','bank_a')
ROOT = Path(os.getenv('BANK_DATA_DIR',f'runtime/{BANK}'))
ROOT.mkdir(parents=True,exist_ok=True)
KEY = os.getenv('BANK_CLIENT_KEY','')
DB = ROOT/'local.db'
REMOTE_DB=os.getenv('BANK_DATABASE_URL','')
app = FastAPI(title=f'FederGuard {BANK} local node')

class RemoteConnection:
    def __init__(self):
        import psycopg
        self.connection=psycopg.connect(REMOTE_DB,prepare_threshold=None)
        self.connection.execute('CREATE TABLE IF NOT EXISTS training (seq BIGSERIAL UNIQUE, round_id TEXT PRIMARY KEY, response TEXT NOT NULL)')
        self.connection.execute('CREATE TABLE IF NOT EXISTS node_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    def execute(self,sql,params=()):
        if sql=='BEGIN IMMEDIATE': return self.connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(BANK,))
        sql=sql.replace('INSERT INTO training VALUES','INSERT INTO training (round_id,response) VALUES').replace('rowid','seq').replace('?','%s')
        return self.connection.execute(sql,params)
    def __enter__(self): return self
    def __exit__(self,*args): return self.connection.__exit__(*args)

def connection():
    if REMOTE_DB: return RemoteConnection()
    c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS training (round_id TEXT PRIMARY KEY, response TEXT NOT NULL)'); return c

def read_state(c,key,default=None):
    if REMOTE_DB:
        row=c.execute('SELECT value FROM node_state WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default
    if key=='unprotected': return (ROOT/'unprotected_release.flag').exists()
    path=ROOT/(key+'.json')
    return json.loads(path.read_text()) if path.exists() else default

def write_state(c,key,value):
    if REMOTE_DB:
        c.execute('INSERT INTO node_state (key,value) VALUES (?,?) ON CONFLICT (key) DO UPDATE SET value=excluded.value',(key,json.dumps(value)))
    elif key=='unprotected': (ROOT/'unprotected_release.flag').write_text('Unprotected release occurred; no full-history DP claim.')
    else:
        path=ROOT/(key+'.json');tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value));tmp.replace(path)

class GoogleAccountant:
    def __init__(self):
        from dp_accounting import rdp
        self.accountant=rdp.RdpAccountant()
    def step(self,noise_multiplier,sample_rate):
        from dp_accounting import GaussianDpEvent
        if sample_rate!=1: raise ValueError('This adapter supports full-batch accounting only')
        self.accountant.compose(GaussianDpEvent(noise_multiplier))
    def get_epsilon(self,delta): return self.accountant.get_epsilon(delta)
def authorize(x_client_key: str = Header(default='')):
    if not KEY or not secrets.compare_digest(x_client_key,KEY): raise HTTPException(401,'Invalid client credential')
def seed():
    if (ROOT/'transactions.npz').exists(): return
    index=['bank_a','bank_b','bank_c'].index(BANK) if BANK in ['bank_a','bank_b','bank_c'] else 0
    n=[4500,3500,2000][index]
    x,y=synthetic(n,101+index,index,drift=index==2)
    np.savez_compressed(ROOT/'transactions.npz',x=x,y=y)
    with connection(): pass
seed()

def train(request: TrainRequest):
    start=time.perf_counter()
    with connection() as c:
        # Immediate lock serializes training and protects privacy composition/replay.
        c.execute('BEGIN IMMEDIATE')
        prior=c.execute('SELECT response FROM training WHERE round_id=?',(request.round_id,)).fetchone()
        if prior: return json.loads(prior[0])
        data=np.load(ROOT/'transactions.npz'); x=transform(data['x']); y=data['y']
        w=np.array(request.parameters,float); initial=w.copy(); p=request.privacy
        accountant_name='Google dp-accounting RDP' if os.getenv('DP_ACCOUNTANT')=='google_rdp' else 'Opacus RDP'
        if os.getenv('DP_ACCOUNTANT')=='google_rdp': accountant=GoogleAccountant()
        else:
            from opacus.accountants import RDPAccountant
            accountant=RDPAccountant()
        history=read_state(c,'privacy_history',[])
        if p.enabled:
            if read_state(c,'unprotected',False): raise HTTPException(409,'Unprotected training history: use a new isolated synthetic experiment before enabling DP')
            for event in history:
                for _ in range(event['steps']): accountant.step(noise_multiplier=event['noise'],sample_rate=1)
            for _ in range(request.steps): accountant.step(noise_multiplier=p.noise_multiplier,sample_rate=1)
            epsilon=accountant.get_epsilon(delta=p.delta)
            if epsilon>p.max_epsilon: raise HTTPException(409,'Local composed privacy budget would be exceeded')
        else: epsilon=None
        # Full-batch per-record gradient clipping. No data-dependent preprocessing.
        # Fixed public denominator and public cohort weights; no sampling amplification.
        rng=np.random.default_rng(secrets.randbits(128))
        for _ in range(request.steps):
            # Public fixed class weights address imbalance without revealing label counts.
            # These are risk-ranking scores, not calibrated fraud probabilities.
            g=((sigmoid(x@w)-y)*np.where(y==1,1.0,.12))[:,None]*x
            if p.enabled:
                g*=np.minimum(1,p.clipping_norm/np.maximum(np.linalg.norm(g,axis=1),1e-12))[:,None]
                grad=(g.sum(axis=0)+rng.normal(0,p.noise_multiplier*p.clipping_norm,7))/len(x)
            else: grad=g.mean(axis=0)
            if request.strategy=='FedProx': grad+=request.proximal_mu*(w-initial)
            w-=3.0*grad
        # Journal the spending before any response can leave this node.
        if p.enabled:
            history.append({'steps':request.steps,'noise':p.noise_multiplier})
            write_state(c,'privacy_history',history)
        else:
            write_state(c,'unprotected',True)
        response={'bank_id':BANK,'round_id':request.round_id,'version':request.version,'parameters':w.tolist(),'weight':1,'duration':time.perf_counter()-start,'epsilon':epsilon,'delta':p.delta,'dp_enabled':p.enabled,'mechanism':f'full-batch clipped Gaussian gradients; {accountant_name}; add/remove adjacency; fixed public cohort size','synthetic':True}
        c.execute('INSERT INTO training VALUES (?,?)',(request.round_id,json.dumps(response)))
        if REMOTE_DB: write_state(c,'model',w.tolist())
        else: np.save(ROOT/'model.npy',w)
        write_state(c,'model_metadata',{'version':request.version,'training_id':request.round_id})
        return response

@app.get('/health')
def health(): return {'bank_id':BANK,'status':'online','data_locality':'local only','synthetic':True}
@app.post('/train',dependencies=[Depends(authorize)])
def train_route(request: TrainRequest): return train(request)
@app.get('/status',dependencies=[Depends(authorize)])
def status():
    with connection() as c:
        count=c.execute('SELECT COUNT(*) FROM training').fetchone()[0]
        last=c.execute('SELECT response FROM training ORDER BY rowid DESC LIMIT 1').fetchone()
        unprotected=read_state(c,'unprotected',False)
    latest=json.loads(last[0]) if last else {}
    return {'bank_id':BANK,'completed_trainings':count,'latest_epsilon':latest.get('epsilon'),'latest_delta':latest.get('delta'),'unprotected_history':unprotected,'data_locality':'bank-only data store','synthetic':True,'features':FEATURES}
@app.post('/predict',dependencies=[Depends(authorize)])
def predict(features: Features):
    path=ROOT/'model.npy'
    with connection() as c:
        stored=read_state(c,'model') if REMOTE_DB else np.load(path).tolist() if path.exists() else None
        metadata=read_state(c,'model_metadata')
    if stored is None or not metadata: raise HTTPException(409,'Train a local model first')
    w=np.asarray(stored); x=transform([[getattr(features,k) for k in FEATURES]])[0]
    contributions=(x*w)[:-1]
    return {'risk_score':float(sigmoid(x@w)),'contributions':dict(zip(FEATURES,contributions.tolist())),'model_version':f"local-from-global-v{metadata['version']}",'training_id':metadata['training_id'],'explanation_type':'additive log-odds; not causal; synthetic calibration only'}

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=int(os.getenv('BANK_PORT','8101')))
