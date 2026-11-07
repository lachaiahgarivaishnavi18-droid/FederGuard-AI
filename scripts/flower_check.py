"""Smoke test of native Flower round scheduling with three isolated local clients."""
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

def main():
    run_id=uuid.uuid4().hex
    root=Path('runtime')/('flower-smoke-'+run_id);root.mkdir(parents=True)
    env=os.environ.copy();env.update(FLOWER_RUN_ID=run_id,FLOWER_ADDRESS='127.0.0.1:8088')
    children=[];logs=[]
    try:
        f=(root/'server.log').open('w');logs.append(f)
        children.append(subprocess.Popen([sys.executable,'-m','backend.federated.flower','server','--rounds','1'],env=env,stdout=f,stderr=f))
        time.sleep(3)
        for bank in ['bank_a','bank_b','bank_c']:
            e={**env,'BANK_DATA_DIR':str(root/bank)}
            f=(root/(bank+'.log')).open('w');logs.append(f)
            children.append(subprocess.Popen([sys.executable,'-m','backend.federated.flower',bank],env=e,stdout=f,stderr=f))
        code=children[0].wait(timeout=150)
        if code:raise RuntimeError('Flower server failed; inspect '+str(root/'server.log'))
        content=(root/'server.log').read_text()
        if 'round 1' not in content.lower() and '[round 1]' not in content.lower():raise RuntimeError('No round completion in server log')
        print('PASS: native Flower server and 3 independent clients; logs in '+str(root))
    finally:
        for p in children:
            if p.poll() is None:p.terminate()
        for p in children:
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill()
        for f in logs:f.close()
if __name__=='__main__':main()
