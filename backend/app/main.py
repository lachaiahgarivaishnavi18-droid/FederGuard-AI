import asyncio
import io
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, Request, Response, HTTPException, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, text
from .core import *
from .schemas import *
from .federation import latest_model, privacy_config, run_round
from .intelligence import records, permitted, unexpired, answer_query, graph_data

def seed(db):
    if db.get(Bank,'bank_a'): return
    for i,name in enumerate(['Aster Bank','Meridian Financial','Northstar Bank']):
        bank_id=f'bank_{chr(97+i)}'
        db.add(Bank(id=bank_id,name=name,endpoint=os.getenv(bank_id.upper()+'_ENDPOINT',f'http://127.0.0.1:{8101+i}'),client_hash=digest(os.getenv(bank_id.upper()+'_CLIENT_KEY',''))))
    db.flush()
    if settings.demo:
        password=os.getenv('DEMO_PASSWORD')
        if not password or len(password)<8: raise RuntimeError('Set DEMO_PASSWORD (at least 8 characters) before initializing demo')
        for bank_id in ['bank_a','bank_b','bank_c']:
            db.add(User(email=bank_id+'@federguard.demo',password=password_hash(password),role='admin' if bank_id=='bank_a' else 'reviewer',bank_id=bank_id))
        for i,(category,summary) in enumerate([
            ('Velocity','Suspicious transaction velocity can be associated with repeated payments in a short time window. Analysts should compare velocity against local account baselines and check for legitimate batch payments.'),
            ('Account takeover','Account takeover indicators include elevated device risk combined with unusual geographic deviation. Device risk alone does not establish fraud. Corroborate locally before escalating.'),
            ('Card-not-present','Card-not-present campaigns may involve repeated small payments followed by a larger payment. This synthetic scenario is an investigative hypothesis and requires local corroboration.')]):
            b=f'bank_{chr(97+i)}'; expiry=(datetime.now(timezone.utc)+timedelta(days=365)).isoformat()
            doc=add(db,'document',{'title':category+' investigation procedure','version':'1.0','source_type':'synthetic policy','sharing':'consortium','status':'approved','expires_at':expiry,'chunks':[{'chunk_id':uid(),'text':summary,'page':1,'section':category}]},b)
            add(db,'intelligence',{'title':category+' monitoring advisory','category':category,'summary':summary,'confidence':.78,'evidence_refs':[doc.id],'sharing':'consortium','privacy_classification':'synthetic','expires_at':expiry,'status':'approved','synthetic':True},b)
            add(db,'case',{'title':'Review '+category.lower()+' indicators','status':'NEW','notes':[],'history':[],'evidence_refs':[doc.id],'assigned_to':None,'synthetic':True},b)
    db.commit()

@asynccontextmanager
async def lifespan(app):
    if settings.cloud_schema_ready:
        yield
        return
    Base.metadata.create_all(engine)
    with Session() as db:
        if settings.demo: seed(db)
        # Interrupted jobs cannot remain running after restart; do not replay releases.
        for r in ([] if settings.serverless else db.scalars(select(Record).where(Record.kind=='round')).all()):
            if r.payload.get('status')=='running': r.payload={**r.payload,'status':'failed','error':'Coordinator restarted; inspect local spending before retry'}
        db.commit()
    yield

app=FastAPI(title='FederGuard AI',version='0.1.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin],allow_credentials=True,allow_methods=['GET','POST','PUT'],allow_headers=['Content-Type','X-Registration-Invite'])
limits=defaultdict(deque)
@app.middleware('http')
async def boundary(request,call_next):
    if request.method in ('POST','PUT','DELETE'):
        origin=request.headers.get('origin')
        if origin and origin!=settings.frontend_origin: return JSONResponse({'detail':'Origin rejected'},403)
    key=(request.client.host,request.url.path)
    q=limits[key]; clock=time.monotonic()
    while q and q[0]<clock-60: q.popleft()
    maximum=12 if request.url.path in ('/api/auth/login','/api/auth/register') else 180
    if len(q)>=maximum: return JSONResponse({'detail':'Rate limit exceeded'},429)
    q.append(clock)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Cache-Control']='no-store'
    response.headers['X-Frame-Options']='DENY'
    return response

def database():
    with Session() as db: yield db
def current(request: Request,db=Depends(database)):
    token=request.cookies.get('fg_session','')
    s=db.get(LoginSession,digest(token))
    if not s or s.expires<time.time(): raise HTTPException(401,'Authentication required')
    user=db.get(User,s.user_id)
    if not user or not db.get(Bank,user.bank_id).active: raise HTTPException(403,'Membership inactive')
    return user
def admin(user=Depends(current)):
    if user.role!='admin': raise HTTPException(403,'Administrator required')
    return user
def reviewer(user=Depends(current)):
    if user.role not in ('reviewer','admin'): raise HTTPException(403,'Human reviewer required')
    return user
def own(db,id,kind,user):
    r=db.get(Record,id)
    if not r or r.kind!=kind or r.bank_id!=user.bank_id: raise HTTPException(404,'Record not found')
    return r
def visible(db,id,kind,user):
    r=db.get(Record,id)
    if not r or r.kind!=kind or not permitted(r,user,db): raise HTTPException(404,'Record not found')
    return r
def list_owned(db,kind,user,offset=0,limit=50):
    return [serialize(r) for r in db.scalars(select(Record).where(Record.kind==kind,Record.bank_id==user.bank_id).order_by(Record.created_at.desc()).offset(max(offset,0)).limit(min(max(limit,1),100))).all()]
def list_global(db,kind):
    return [serialize(r) for r in db.scalars(select(Record).where(Record.kind==kind).order_by(Record.created_at.desc()).limit(100)).all()]
def validate_evidence(db,refs,user):
    for ref in refs:
        r=db.get(Record,ref)
        if not r or r.kind not in ('document','intelligence','alert') or not permitted(r,user,db): raise HTTPException(422,'Evidence unavailable')

@app.get('/health')
def health(): return {'status':'ok','mode':'synthetic research demo' if settings.demo else 'configured deployment','secure_aggregation':'plaintext simulation'}
@app.get('/api/auth/registration-options')
def registration_options(db=Depends(database)):
    return {'banks':[{'id':b.id,'name':b.name} for b in db.scalars(select(Bank).where(Bank.active==True)).all() if os.getenv(b.id.upper()+'_REGISTRATION_INVITE','')], 'invitation_required':True}

@app.post('/api/auth/register',status_code=201)
def register(body:Register,request:Request,db=Depends(database)):
    bank_id=body.bank_id
    if bank_id:
        invite=os.getenv(bank_id.upper()+'_REGISTRATION_INVITE','')
        if not invite or not secrets.compare_digest(request.headers.get('X-Registration-Invite',''),invite): raise HTTPException(403,'Institution-issued invitation required')
        bank=db.get(Bank,bank_id)
        if not bank or not bank.active: raise HTTPException(422,'Bank unavailable')
    elif not settings.demo:
        raise HTTPException(403,'Open registration is available only in demo mode')
    if db.scalar(select(User).where(User.email==body.email.lower())): raise HTTPException(409,'Registration unavailable')
    if not bank_id:
        bank_id='demo_'+uid()
        db.add(Bank(id=bank_id,name='Personal demo workspace',consent=False));db.flush()
    user=User(email=body.email.lower(),password=password_hash(body.password),bank_id=bank_id,role='analyst'); db.add(user); db.flush(); audit(db,user,'register'); db.commit()
    return {'id':user.id,'role':user.role}
@app.post('/api/auth/login')
def login(body:Credentials,response:Response,db=Depends(database)):
    user=db.scalar(select(User).where(User.email==body.email.lower()))
    if not user or not password_valid(body.password,user.password): raise HTTPException(401,'Invalid credentials')
    token=secrets.token_urlsafe(32); db.add(LoginSession(token_hash=digest(token),user_id=user.id,expires=time.time()+28800)); audit(db,user,'login'); db.commit()
    response.set_cookie('fg_session',token,httponly=True,secure=settings.cookie_secure,samesite='strict',max_age=28800)
    return {'email':user.email,'role':user.role,'bank_id':user.bank_id}
@app.post('/api/auth/logout')
def logout(request:Request,response:Response,user=Depends(current),db=Depends(database)):
    s=db.get(LoginSession,digest(request.cookies.get('fg_session','')))
    if s: db.delete(s)
    audit(db,user,'logout'); db.commit(); response.delete_cookie('fg_session'); return {'status':'logged out'}
@app.get('/api/auth/me')
def me(user=Depends(current)): return {'id':user.id,'email':user.email,'role':user.role,'bank_id':user.bank_id}

@app.post('/api/users',status_code=201)
def create_member(body:MemberInput,user=Depends(admin),db=Depends(database)):
    if db.scalar(select(User).where(User.email==body.email.lower())): raise HTTPException(409,'Member exists')
    member=User(email=body.email.lower(),password=password_hash(body.password),role=body.role,bank_id=user.bank_id)
    db.add(member);db.flush();audit(db,user,'member.create',member.id);db.commit()
    return {'id':member.id,'email':member.email,'role':member.role,'bank_id':member.bank_id}

@app.get('/api/banks')
def banks(user=Depends(current),db=Depends(database)):
    return [{'id':b.id,'name':b.name,'active':b.active,'consent':b.consent,'data_locality':'independent local store','synthetic':settings.demo} for b in db.scalars(select(Bank)).all()]
@app.post('/api/banks',status_code=201)
def create_bank(body:BankInput,user=Depends(admin),db=Depends(database)):
    if db.get(Bank,body.id): raise HTTPException(409,'Bank exists')
    db.add(Bank(id=body.id,name=body.name,endpoint=os.getenv(body.id.upper()+'_ENDPOINT',''))); audit(db,user,'bank.create',body.id); db.commit(); return body
@app.get('/api/banks/{id}')
def bank_detail(id:str,user=Depends(current),db=Depends(database)):
    b=db.get(Bank,id)
    if not b: raise HTTPException(404,'Bank not found')
    return {'id':b.id,'name':b.name,'active':b.active,'consent':b.consent}
@app.put('/api/banks/{id}')
def edit_bank(id:str,body:BankEdit,user=Depends(admin),db=Depends(database)):
    b=db.get(Bank,id)
    if not b: raise HTTPException(404,'Bank not found')
    b.active=body.active; b.consent=body.consent; audit(db,user,'bank.update',id); db.commit(); return body
@app.post('/api/banks/{id}/enroll-client')
def enroll(id:str,user=Depends(admin),db=Depends(database)):
    b=db.get(Bank,id)
    if not b: raise HTTPException(404,'Bank not found')
    key=os.getenv(id.upper()+'_CLIENT_KEY',''); endpoint=os.getenv(id.upper()+'_ENDPOINT','')
    if not key or not endpoint: raise HTTPException(409,'Configure bank-specific endpoint and key in deployment environment first')
    b.client_hash=digest(key); b.endpoint=endpoint; b.active=True; audit(db,user,'client.enroll',id); db.commit(); return {'status':'enrolled','bank_id':id}

def local_call(db,user,path,payload=None):
    b=db.get(Bank,user.bank_id); key=os.getenv(b.id.upper()+'_CLIENT_KEY','')
    if not key or not b.endpoint: raise HTTPException(503,'Bank node not configured')
    import httpx
    try:
        with httpx.Client(timeout=90,trust_env=False) as c:
            r=c.get(b.endpoint+path,headers={'X-Client-Key':key}) if payload is None else c.post(b.endpoint+path,headers={'X-Client-Key':key},json=payload)
        if r.status_code>=400: raise HTTPException(r.status_code,'Local bank operation rejected')
        return r.json()
    except httpx.HTTPError: raise HTTPException(503,'Local bank node unavailable')
@app.get('/api/bank-client/status')
@app.get('/api/bank-client/dataset-status')
def local_status(user=Depends(current),db=Depends(database)): return local_call(db,user,'/status')
@app.get('/api/bank-client/training-history')
def training_history(user=Depends(current),db=Depends(database)): return list_owned(db,'privacy-event',user)
@app.post('/api/bank-client/train-local')
def local_train(user=Depends(reviewer),db=Depends(database)):
    model=latest_model(db); r=add(db,'local-training',{'status':'started'},user.bank_id); db.commit()
    result=local_call(db,user,'/train',{'round_id':r.id,'version':model['version'],'parameters':model['parameters'],'steps':3,'strategy':'FedAvg','proximal_mu':0,'privacy':privacy_config(db).model_dump()})
    result.pop('parameters',None); r.payload=result; audit(db,user,'local.train',r.id); db.commit(); return result

round_lock=threading.Lock()
def background_round(id,body):
    try: run_round(id,body)
    except Exception as e:
        with Session() as db:
            r=db.get(Record,id); r.payload={**r.payload,'status':'failed','error':type(e).__name__}; db.commit()
    finally: round_lock.release()
@app.post('/api/federated/rounds/start',status_code=202)
def start_round(body:RoundInput,tasks:BackgroundTasks,user=Depends(admin),db=Depends(database)):
    banks=db.scalars(select(Bank).where(Bank.id.in_(body.bank_ids))).all()
    if len(banks)!=len(body.bank_ids) or any(not b.active for b in banks): raise HTTPException(422,'Client ineligible')
    if not round_lock.acquire(blocking=False): raise HTTPException(409,'A round is already running')
    lock_connection=None
    if settings.serverless:
        try:
            lock_connection=engine.connect()
            if not lock_connection.scalar(text('SELECT pg_try_advisory_lock(83174821)')):
                lock_connection.close(); round_lock.release(); raise HTTPException(409,'A round is already running')
        except HTTPException: raise
        except Exception:
            if lock_connection: lock_connection.close()
            round_lock.release(); raise
    try:
        r=add(db,'round',{'status':'running','strategy':body.strategy,'selected':body.bank_ids,'clients':[],'synthetic':True}); audit(db,user,'round.start',r.id); db.commit()
        if settings.serverless:
            # Finish work inside the invocation; no reliance on a detached worker.
            run_round(r.id,body.model_dump())
            db.refresh(r)
            return serialize(r)
        tasks.add_task(background_round,r.id,body.model_dump()); return serialize(r)
    except Exception:
        if not settings.serverless: round_lock.release()
        raise
    finally:
        if settings.serverless:
            try:
                if lock_connection: lock_connection.execute(text('SELECT pg_advisory_unlock(83174821)'))
            finally:
                if lock_connection: lock_connection.close()
                round_lock.release()
@app.get('/api/federated/rounds')
def rounds(user=Depends(current),db=Depends(database)): return list_global(db,'round')
@app.get('/api/federated/rounds/{id}')
def round_detail(id:str,user=Depends(current),db=Depends(database)):
    r=db.get(Record,id)
    if not r or r.kind!='round': raise HTTPException(404,'Round not found')
    return serialize(r)
@app.get('/api/federated/clients')
def clients(user=Depends(current),db=Depends(database)): return banks(user,db)
@app.get('/api/federated/models')
def models(user=Depends(current),db=Depends(database)): return [{k:v for k,v in r.items() if k!='parameters'} for r in list_global(db,'model')]
@app.get('/api/federated/metrics')
def model_metrics(user=Depends(current),db=Depends(database)): return latest_model(db).get('metrics',{})

@app.get('/api/privacy/config')
def get_privacy(user=Depends(current),db=Depends(database)): return privacy_config(db)
@app.put('/api/privacy/config')
def set_privacy(body:Privacy,user=Depends(admin),db=Depends(database)):
    if round_lock.locked(): raise HTTPException(409,'Wait for active round')
    r=db.get(Record,'privacy-config')
    if r: r.payload=body.model_dump()
    else: db.add(Record(id='privacy-config',kind='config',payload=body.model_dump()))
    audit(db,user,'privacy.configure'); db.commit(); return body
@app.get('/api/privacy/accounting')
@app.get('/api/privacy/audit')
def accounting(user=Depends(current),db=Depends(database)): return list_owned(db,'privacy-event',user)
@app.get('/api/privacy/status')
def privacy_status(user=Depends(current),db=Depends(database)):
    events=list_owned(db,'privacy-event',user)
    try: local=local_call(db,user,'/status')
    except HTTPException: local=None
    return {'configuration':privacy_config(db).model_dump(),'latest_epsilon':local['latest_epsilon'] if local else events[0].get('epsilon') if events else None,'completed_releases':local['completed_trainings'] if local else len(events),'accounting_source':'bank-local release journal' if local else 'coordinator metadata only; bank node unavailable','unprotected_history':local['unprotected_history'] if local else None,'secure_aggregation':'PLAINTEXT SIMULATION — coordinator can inspect individual updates','data_locality':'Raw datasets remain in bank node stores','mechanism':'full-batch per-record clipping + Gaussian; '+('Google dp-accounting RDP' if os.getenv('DP_ACCOUNTANT')=='google_rdp' else 'Opacus RDP')+'; q=1','guarantee':'Research assumptions only; non-cryptographic RNG; fixed public class weights; unprotected releases invalidate full-history claims; see privacy.md'}

@app.post('/api/fraud/detect')
def detect(body:Features,user=Depends(current),db=Depends(database)):
    result=local_call(db,user,'/predict',body.model_dump())
    category='Velocity' if body.velocity>5 else 'Account takeover' if body.device_risk>.5 else 'Card-not-present'
    r=add(db,'alert',{'transaction_reference':'SYN-'+uid()[:10],'risk_score':result['risk_score'],'category':category,'contributions':result['contributions'],'explanation':result['explanation_type'],'model_version':result['model_version'],'review_status':'NEW','synthetic':True},user.bank_id)
    audit(db,user,'fraud.detect',r.id); db.commit(); return serialize(r)
@app.get('/api/fraud/alerts')
def alerts(offset:int=0,limit:int=50,user=Depends(current),db=Depends(database)): return list_owned(db,'alert',user,offset,limit)
@app.get('/api/fraud/alerts/{id}')
def alert_detail(id:str,user=Depends(current),db=Depends(database)): return serialize(own(db,id,'alert',user))
@app.get('/api/fraud/metrics')
def fraud_metrics(user=Depends(current),db=Depends(database)): return latest_model(db).get('metrics',{})

@app.post('/api/intelligence/contribute',status_code=201)
def contribute(body:Contribution,user=Depends(current),db=Depends(database)):
    if not unexpired(body.model_dump()): raise HTTPException(422,'Future timezone-aware expiry required')
    validate_evidence(db,body.evidence_refs,user)
    if not db.get(Bank,user.bank_id).consent and body.sharing=='consortium': raise HTTPException(403,'Bank sharing consent disabled')
    # Structural minimization: no arbitrary records/identifier fields; content still requires human review.
    import re
    if re.search(r'\b\d{10,}\b|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',body.summary): raise HTTPException(422,'Potential direct identifier in summary')
    r=add(db,'intelligence',{**body.model_dump(),'status':'pending','submitted_by':user.id,'synthetic':settings.demo},user.bank_id); audit(db,user,'intelligence.contribute',r.id); db.commit(); return serialize(r)
@app.get('/api/intelligence')
def intelligence(offset:int=0,limit:int=50,user=Depends(current),db=Depends(database)): return [serialize(r) for r in records(db,'intelligence',user)][max(offset,0):max(offset,0)+min(max(limit,1),100)]
@app.get('/api/intelligence/trends')
def intelligence_trends(user=Depends(current),db=Depends(database)):
    counts=defaultdict(int)
    for r in records(db,'intelligence',user):
        if r.payload['status']=='approved' and unexpired(r.payload): counts[r.payload['category']]+=1
    return [{'category':k,'count':v} for k,v in counts.items()]
@app.get('/api/intelligence/{id}')
def intelligence_detail(id:str,user=Depends(current),db=Depends(database)): return serialize(visible(db,id,'intelligence',user))
@app.post('/api/intelligence/{id}/review')
def review_intel(id:str,body:Review,user=Depends(reviewer),db=Depends(database)):
    r=own(db,id,'intelligence',user)
    if r.payload.get('submitted_by')==user.id: raise HTTPException(403,'A second reviewer must approve this contribution')
    if body.status=='approved' and not db.get(Bank,user.bank_id).consent: raise HTTPException(403,'Bank consent disabled')
    r.payload={**r.payload,'status':body.status,'reviewer':user.id,'reviewed_at':now()}; audit(db,user,'intelligence.review',id); db.commit(); return serialize(r)

@app.post('/api/rag/ingest',status_code=201)
async def ingest(file:UploadFile=File(...),title:str=Form(...),sharing:Literal['private','consortium']=Form('private'),user=Depends(current),db=Depends(database)):
    if len(title)>200 or len(title)<3: raise HTTPException(422,'Title must be 3–200 characters')
    data=await file.read(5*1024*1024+1)
    if len(data)>5*1024*1024: raise HTTPException(413,'Maximum upload 5 MB')
    suffix=(file.filename or '').lower().split('.')[-1]; pages=[]
    try:
        if suffix=='pdf':
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(data))
            if len(reader.pages)>200: raise ValueError('Too many pages')
            pages=[(i+1,p.extract_text() or '') for i,p in enumerate(reader.pages)]
        elif suffix=='docx':
            import zipfile
            z=zipfile.ZipFile(io.BytesIO(data))
            if sum(i.file_size for i in z.infolist())>20*1024*1024: raise ValueError('Expanded file too large')
            from docx import Document
            pages=[(None,'\n'.join(p.text for p in Document(io.BytesIO(data)).paragraphs))]
        elif suffix in ('txt','md'): pages=[(1,data.decode('utf-8'))]
        else: raise HTTPException(415,'Supported types: PDF, DOCX, TXT, MD')
    except HTTPException: raise
    except Exception: raise HTTPException(422,'Document could not be parsed')
    if sum(len(text) for _,text in pages)>500000: raise HTTPException(413,'Extracted text too long')
    chunks=[]
    for page,text in pages:
        text=' '.join(text.split())
        for i in range(0,len(text),650):
            chunks.append({'chunk_id':uid(),'text':text[i:i+800],'page':page,'section':title})
    if not chunks: raise HTTPException(422,'No extractable text; OCR is not configured')
    r=add(db,'document',{'title':title,'version':'1.0','source_type':'upload','sharing':sharing,'status':'pending' if sharing=='consortium' else 'private','expires_at':(datetime.now(timezone.utc)+timedelta(days=90)).isoformat(),'chunks':chunks,'uploaded_by':user.id},user.bank_id)
    audit(db,user,'document.ingest',r.id); db.commit(); return {'id':r.id,'chunks':len(chunks),'status':r.payload['status']}
@app.get('/api/rag/documents')
def documents(user=Depends(current),db=Depends(database)): return [{k:v for k,v in serialize(r).items() if k!='chunks'} for r in records(db,'document',user)]
@app.post('/api/rag/documents/{id}/review')
def review_doc(id:str,body:Review,user=Depends(reviewer),db=Depends(database)):
    r=own(db,id,'document',user)
    if r.payload.get('uploaded_by')==user.id: raise HTTPException(403,'Second reviewer required')
    if not db.get(Bank,user.bank_id).consent: raise HTTPException(403,'Bank sharing consent disabled')
    r.payload={**r.payload,'status':body.status,'reviewer':user.id}; audit(db,user,'document.review',id); db.commit(); return {'status':body.status}
@app.post('/api/rag/query')
@app.post('/api/ai/chat')
@app.post('/api/ai/explain')
@app.post('/api/ai/report')
def chat(body:Query,user=Depends(current),db=Depends(database)):
    try: result=answer_query(db,user,body.question)
    except Exception as e: raise HTTPException(502,'Generation unavailable: '+type(e).__name__)
    audit(db,user,'rag.query',result['id']); db.commit(); return result
@app.get('/api/rag/evidence/{query_id}')
def evidence(query_id:str,user=Depends(current),db=Depends(database)):
    r=own(db,query_id,'query',user)
    # Re-check current permissions to honor revocation after query creation.
    return [e for e in r.payload['evidence'] if (d:=db.get(Record,e['document_id'])) and permitted(d,user,db) and unexpired(d.payload)]

@app.get('/api/graph/patterns')
def graph(user=Depends(current),db=Depends(database)): return graph_data(db,user)
@app.get('/api/graph/entities')
def entities(user=Depends(current),db=Depends(database)): return graph_data(db,user)['nodes']
@app.get('/api/graph/relationships')
def relationships(user=Depends(current),db=Depends(database)): return graph_data(db,user)['edges']

@app.post('/api/investigations',status_code=201)
def create_case(body:CaseInput,user=Depends(current),db=Depends(database)):
    if body.alert_id: own(db,body.alert_id,'alert',user)
    validate_evidence(db,body.evidence_refs,user)
    r=add(db,'case',{**body.model_dump(),'status':'NEW','notes':[],'history':[],'assigned_to':user.id,'synthetic':settings.demo},user.bank_id); audit(db,user,'case.create',r.id); db.commit(); return serialize(r)
@app.get('/api/investigations')
def cases(offset:int=0,limit:int=50,user=Depends(current),db=Depends(database)): return list_owned(db,'case',user,offset,limit)
@app.get('/api/investigations/{id}')
def case_detail(id:str,user=Depends(current),db=Depends(database)): return serialize(own(db,id,'case',user))
@app.post('/api/investigations/{id}/notes')
def case_note(id:str,body:Note,user=Depends(current),db=Depends(database)):
    r=own(db,id,'case',user); r.payload={**r.payload,'notes':r.payload['notes']+[{'text':body.text,'author':user.id,'created_at':now()}]}; audit(db,user,'case.note',id); db.commit(); return serialize(r)
@app.put('/api/investigations/{id}/status')
def case_status(id:str,body:CaseStatus,user=Depends(reviewer),db=Depends(database)):
    r=own(db,id,'case',user); r.payload={**r.payload,'status':body.status,'history':r.payload['history']+[{'from':r.payload['status'],'to':body.status,'reviewer':user.id,'created_at':now()}]}; audit(db,user,'case.status',id); db.commit(); return serialize(r)

@app.post('/api/agents/run')
def agents(body:Query,user=Depends(current),db=Depends(database)):
    from .agents import run
    result=run(db,user,body.question); audit(db,user,'agents.run',result['id']); db.commit(); return result
@app.get('/api/agents/executions')
def agent_executions(user=Depends(current),db=Depends(database)): return list_owned(db,'agent-execution',user)
@app.get('/api/agents/executions/{id}')
def agent_detail(id:str,user=Depends(current),db=Depends(database)): return serialize(own(db,id,'agent-execution',user))

@app.get('/api/analytics/dashboard')
def dashboard(user=Depends(current),db=Depends(database)):
    model=latest_model(db); rounds=list_global(db,'round')
    return {'banks':len(db.scalars(select(Bank).where(Bank.active==True)).all()),'model_version':model['version'],'metrics':model.get('metrics',{}),'alerts':db.scalar(select(func.count()).select_from(Record).where(Record.kind=='alert',Record.bank_id==user.bank_id)),'intelligence':len(records(db,'intelligence',user)),'cases':len(list_owned(db,'case',user)),'rounds':rounds[:8],'synthetic':True,'activity':list_owned(db,'audit',user,0,8)}
@app.get('/api/analytics/fraud-trends')
def fraud_trends(user=Depends(current),db=Depends(database)): return intelligence_trends(user,db)
@app.get('/api/analytics/federated-performance')
def performance(user=Depends(current),db=Depends(database)): return models(user,db)
@app.get('/api/analytics/privacy-utility')
def utility(user=Depends(current),db=Depends(database)):
    return [{'version':r['version'],'privacy':r.get('privacy'),'metrics':r['metrics']} for r in models(user,db)]
@app.get('/api/audit')
def audits(offset:int=0,limit:int=50,user=Depends(reviewer),db=Depends(database)): return list_owned(db,'audit',user,offset,limit)

@app.websocket('/ws/rounds')
async def socket(ws:WebSocket):
    if ws.headers.get('origin')!=settings.frontend_origin: await ws.close(code=1008); return
    with Session() as db:
        s=db.get(LoginSession,digest(ws.cookies.get('fg_session','')))
        if not s or s.expires<time.time(): await ws.close(code=1008); return
    await ws.accept()
    try:
        for _ in range(240):
            with Session() as db:
                s=db.get(LoginSession,digest(ws.cookies.get('fg_session','')))
                if not s or s.expires<time.time(): await ws.close(code=1008); return
                await ws.send_json(list_global(db,'round')[:5])
            await asyncio.sleep(3)
    except WebSocketDisconnect: pass
