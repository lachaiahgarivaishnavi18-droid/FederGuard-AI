"""Optional native Flower gRPC transport for independent bank processes.

The web coordinator uses authenticated HTTP dispatch + Flower aggregation. This
runner exercises Flower's own round scheduling. Neither mode supplies SecAgg+.
"""
import argparse
import json
import os
from pathlib import Path
import numpy as np
import flwr as fl
from dotenv import load_dotenv
from backend.ml import evaluate

def server(rounds):
    class RegistryStrategy(fl.server.strategy.FedAvg):
        def aggregate_fit(self,server_round,results,failures):
            # Reject malformed tensors before Flower aggregation.
            valid=[]
            for proxy,result in results:
                arrays=fl.common.parameters_to_ndarrays(result.parameters)
                if len(arrays)==1 and arrays[0].shape==(7,) and np.isfinite(arrays[0]).all() and np.linalg.norm(arrays[0])<=100 and result.num_examples==1: valid.append((proxy,result))
            if len(valid)<2:return None,{}
            return super().aggregate_fit(server_round,valid,failures)
    def evaluation(server_round,parameters,config):
        metrics=evaluate(parameters[0].tolist())
        Path('runtime').mkdir(exist_ok=True)
        with Path('runtime/flower-evaluation.jsonl').open('a') as f:f.write(json.dumps({'round':server_round,'metrics':metrics,'synthetic':True})+'\n')
        return 1-metrics['accuracy'],{k:v for k,v in metrics.items() if isinstance(v,float)}
    strategy=RegistryStrategy(min_fit_clients=2,min_available_clients=3,min_evaluate_clients=0,fraction_evaluate=0,accept_failures=True,initial_parameters=fl.common.ndarrays_to_parameters([np.zeros(7)]),on_fit_config_fn=lambda r:{'round':r,'run_id':os.getenv('FLOWER_RUN_ID','research-run')},evaluate_fn=evaluation)
    certs=None
    if os.getenv('FLOWER_TLS_CERT'):
        certs=tuple(Path(os.environ[k]).read_bytes() for k in ['FLOWER_TLS_CA','FLOWER_TLS_CERT','FLOWER_TLS_KEY'])
    fl.server.start_server(server_address=os.getenv('FLOWER_ADDRESS','127.0.0.1:8088'),config=fl.server.ServerConfig(num_rounds=rounds),strategy=strategy,certificates=certs)
def client(bank):
    os.environ['BANK_ID']=bank
    os.environ['BANK_CLIENT_KEY']=os.getenv(bank.upper()+'_CLIENT_KEY','')
    from bank_clients.node import train
    from backend.app.schemas import TrainRequest,Privacy
    class Client(fl.client.NumPyClient):
        def get_parameters(self,config): return [np.zeros(7)]
        def fit(self,parameters,config):
            r=train(TrainRequest(round_id=f"flower-{config['run_id']}-{config['round']}",version=int(config['round'])-1,parameters=parameters[0].tolist(),steps=3,strategy='FedAvg',proximal_mu=0,privacy=Privacy()))
            return [np.asarray(r['parameters'])],1,{'epsilon':float(r['epsilon'])}
        def evaluate(self,parameters,config): return 0.,1,{}
    ca=Path(os.environ['FLOWER_TLS_CA']).read_bytes() if os.getenv('FLOWER_TLS_CA') else None
    fl.client.start_client(server_address=os.getenv('FLOWER_ADDRESS','127.0.0.1:8088'),client=Client().to_client(),root_certificates=ca,insecure=ca is None,max_retries=3)
if __name__=='__main__':
    load_dotenv();p=argparse.ArgumentParser();p.add_argument('target',choices=['server','bank_a','bank_b','bank_c']);p.add_argument('--rounds',type=int,default=3);a=p.parse_args()
    server(a.rounds) if a.target=='server' else client(a.target)
