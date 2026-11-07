"""Authenticated command-line demo operations, using environment credentials."""
import argparse
import os
from pathlib import Path
import time
import httpx
from dotenv import load_dotenv
load_dotenv()
p=argparse.ArgumentParser();p.add_argument('action',choices=['round','query','ingest','agents']);p.add_argument('--text',default='Explain suspicious transaction velocity');p.add_argument('--file');p.add_argument('--bank',default='bank_a');args=p.parse_args()
with httpx.Client(base_url='http://127.0.0.1:8000',timeout=120,trust_env=False) as c:
    r=c.post('/api/auth/login',json={'email':args.bank+'@federguard.demo','password':os.environ['DEMO_PASSWORD']});r.raise_for_status()
    if args.action=='round':
        r=c.post('/api/federated/rounds/start',json={});r.raise_for_status();id=r.json()['id']
        while True:
            r=c.get('/api/federated/rounds/'+id);r.raise_for_status()
            if r.json()['status']!='running':break
            time.sleep(1)
    elif args.action=='ingest':
        if not args.file:p.error('--file is required')
        with open(args.file,'rb') as f:r=c.post('/api/rag/ingest',files={'file':(Path(args.file).name,f)},data={'title':Path(args.file).stem,'sharing':'private'})
    else:r=c.post('/api/agents/run' if args.action=='agents' else '/api/rag/query',json={'question':args.text})
    r.raise_for_status();print(r.text)
