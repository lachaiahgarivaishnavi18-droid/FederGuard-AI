"""Small labeled synthetic retrieval benchmark against the running API."""
import json
import math
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
load_dotenv()
cases=[('suspicious velocity payments','Velocity'),('account takeover device risk','Account takeover'),('card-not-present repeated payments','Card-not-present')]
with httpx.Client(base_url='http://127.0.0.1:8000',timeout=120,trust_env=False) as c:
    r=c.post('/api/auth/login',json={'email':'bank_a@federguard.demo','password':os.environ['DEMO_PASSWORD']});r.raise_for_status()
    docs=c.get('/api/rag/documents').json();intel=c.get('/api/intelligence').json()
    scores=[]
    for question,label in cases:
        gold={r['id'] for r in docs+intel if r['title'].startswith(label)}
        r=c.post('/api/rag/query',json={'question':question});r.raise_for_status();answer=r.json();evidence=answer['evidence']
        relevant=[1 if e['document_id'] in gold else 0 for e in evidence]
        dcg=sum(v/math.log2(i+2) for i,v in enumerate(relevant));idcg=sum(1/math.log2(i+2) for i in range(min(len(gold),5)))
        scores.append({'question':question,'precision_at_5':sum(relevant)/5,'recall_at_5':sum(relevant)/max(len(gold),1),'reciprocal_rank':next((1/(i+1) for i,v in enumerate(relevant) if v),0),'ndcg_at_5':dcg/idcg if idcg else 0,'citation_reference_validity':all(e['citation'] in answer['answer'] for e in evidence),'gold_source_ids':list(gold),'retrieved_source_ids':[e['document_id'] for e in evidence]})
    empty=c.post('/api/rag/query',json={'question':'qzxv-no-evidence-zzzz'}).json()
    result={'dataset':'three labeled synthetic queries; small smoke benchmark, not general QA evaluation','queries':scores,'mean_precision_at_5':sum(s['precision_at_5'] for s in scores)/len(scores),'mean_recall_at_5':sum(s['recall_at_5'] for s in scores)/len(scores),'mrr':sum(s['reciprocal_rank'] for s in scores)/len(scores),'ndcg_at_5':sum(s['ndcg_at_5'] for s in scores)/len(scores),'insufficient_evidence_pass':not empty['evidence'],'faithfulness':'Demo copies passages; no independent semantic entailment or external-LLM hallucination evaluation performed'}
    Path('docs/reports/rag-evaluation.json').write_text(json.dumps(result,indent=2));print('Wrote docs/reports/rag-evaluation.json')
