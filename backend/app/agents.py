"""Typed LangGraph investigation workflow, with scoped inputs and traceable outputs."""
from typing import TypedDict
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from .intelligence import answer_query, graph_data, records, retrieve
from .core import serialize, add, Record
from .federation import latest_model, privacy_config
from sqlalchemy import select

class AgentOutput(BaseModel):
    agent: str
    status: str
    result: dict
    permission_scope: str
    attempts: int = 1
class State(TypedDict):
    question: str
    trace: list[dict]
    response: dict

def run(db,user,question):
    graph=StateGraph(State)
    def node(name,fn):
        def wrapped(s):
            result={};status='failed'
            for attempt in range(1,3):
                try:
                    result=fn(s);status='completed';break
                except Exception as e:result={'error':type(e).__name__,'message':'Dependency unavailable; no expanded permissions or fallback data access'}
            output=AgentOutput(agent=name,status=status,result=result,permission_scope=user.bank_id,attempts=attempt)
            return {'trace':s['trace']+[output.model_dump()],**({'response':result} if name=='Generative explanation' else {})}
        return wrapped
    # Bank-local agents execute in the isolated bank process, never against central raw data.
    def local_schema(s):
        from .main import local_call
        return local_call(db,user,'/status')
    def local_alerts(s):
        alerts=db.scalars(select(Record).where(Record.kind=='alert',Record.bank_id==user.bank_id).limit(100)).all()
        return {'local_alert_count':len(alerts),'risk_indicators':[{'reference':r.id,'score':r.payload['risk_score'],'category':r.payload['category']} for r in alerts],'new_scoring':'Requires a separate local assessment request; this workflow does not score unspecified transactions'}
    def retrieval(s):
        evidence,mode=retrieve(db,user,s['question'])
        return {'evidence':evidence,'mode':mode}
    def audit_claims(s):
        response=s.get('response',{})
        cited=response.get('evidence',[])
        add(db,'audit',{'actor':user.id,'action':'agents.validate-provenance','target':response.get('id','')},user.bank_id)
        return {'scope':user.bank_id,'provider':response.get('provider','unavailable'),'references_valid':all(db.get(Record,e['document_id']) is not None for e in cited),'semantic_entailment':'Human review required','citations':len(cited)}
    functions=[
      ('Bank data understanding',local_schema),
      ('Local fraud detection',local_alerts),
      ('Privacy protection',lambda s:{'scope':user.bank_id,'configuration':privacy_config(db).model_dump(),'raw_records_allowed':False}),
      ('Federated learning',lambda s:{'global_version':latest_model(db)['version'],'metrics':latest_model(db).get('metrics',{}),'training_triggered':False}),
      ('Secure aggregation',lambda s:{'mode':'plaintext academic simulation','cryptographic_protection':False,'latest_model_hash':latest_model(db).get('sha256')}),
      ('Cross-bank intelligence',lambda s:{'authorized_records':len(records(db,'intelligence',user))}),
      ('RAG retrieval',retrieval),
      ('Fraud knowledge graph',lambda s:graph_data(db,user)),
      ('Generative explanation',lambda s:answer_query(db,user,s['question'])),
      ('Explainable AI',lambda s:{'method':'additive logistic log-odds; local SHAP available through evaluation CLI','causal':False}),
      ('Investigation support',lambda s:{'next_steps':['Validate provenance','Corroborate signals locally','Record a human review'],'autonomous_actions':False}),
      ('Compliance and audit',audit_claims),
      ('Orchestrator',lambda s:{'status':'awaiting analyst review','steps':len(s['trace']),'failed_dependencies':[t['agent'] for t in s['trace'] if t['status']=='failed']})]
    previous=START
    for name,fn in functions:
        graph.add_node(name,node(name,fn)); graph.add_edge(previous,name); previous=name
    graph.add_edge(previous,END)
    try:
        result=graph.compile().invoke({'question':question,'trace':[],'response':{}})
        payload={'status':'completed',**result}
    except Exception as e:
        payload={'status':'failed','error':type(e).__name__,'question':question}
    return serialize(add(db,'agent-execution',payload,user.bank_id))
