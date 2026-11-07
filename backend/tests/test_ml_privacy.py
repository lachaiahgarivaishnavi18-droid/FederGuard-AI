import json
import os
import numpy as np
import pytest
from backend.ml import synthetic,transform,sigmoid,fedavg,evaluate

def test_fedavg_weighting_and_validation():
    w=fedavg([{'parameters':[1.]*7,'weight':1},{'parameters':[3.]*7,'weight':3}])
    assert w==pytest.approx([2.5]*7)
    with pytest.raises(ValueError):fedavg([{'parameters':[1.]*7,'weight':1}])
    with pytest.raises(ValueError):fedavg([{'parameters':[float('nan')]*7,'weight':1},{'parameters':[1.]*7,'weight':1}])
def test_non_iid_and_training_converges():
    a,ya=synthetic(4500,101,0);b,yb=synthetic(3500,102,1)
    assert np.nanmean(a[:,0])!=pytest.approx(np.nanmean(b[:,0]))
    x=transform(a);w=np.zeros(7)
    before=np.mean(np.logaddexp(0,x@w)-ya*(x@w))
    for _ in range(20):w-=1.5*((sigmoid(x@w)-ya)[:,None]*x).mean(0)
    assert np.mean(np.logaddexp(0,x@w)-ya*(x@w))<before
    assert 'pr_auc' in evaluate(w.tolist())

def test_local_accounting_replay_and_budget(tmp_path,monkeypatch):
    monkeypatch.setenv('BANK_ID','bank_a');monkeypatch.setenv('BANK_DATA_DIR',str(tmp_path));monkeypatch.setenv('BANK_CLIENT_KEY','test-key')
    from bank_clients import node
    monkeypatch.setattr(node,'ROOT',tmp_path);monkeypatch.setattr(node,'DB',tmp_path/'local.db');node.seed()
    from backend.app.schemas import TrainRequest
    def request(id,**privacy):return TrainRequest(round_id=id,version=0,parameters=[0]*7,steps=2,strategy='FedAvg',proximal_mu=0,privacy=privacy)
    r=node.train(request('one'));second=node.train(request('two'))
    assert second['epsilon']>r['epsilon']>0
    assert node.train(request('one'))==r
    assert len(json.loads((tmp_path/'privacy_history.json').read_text()))==2
    assert 'transactions' not in r and 'x' not in r and 'y' not in r
    from fastapi import HTTPException
    with pytest.raises(HTTPException):node.train(request('three',max_epsilon=.01))
    assert len(json.loads((tmp_path/'privacy_history.json').read_text()))==2

def test_fedprox_anchor_reduces_drift():
    from scripts.evaluate import optimize
    raw,y=synthetic(1000);x=transform(raw);anchor=np.zeros(7)
    plain=optimize(x,y,anchor.copy(),mu=0)
    prox=optimize(x,y,anchor.copy(),mu=.1,anchor=anchor)
    assert np.linalg.norm(prox-anchor)<np.linalg.norm(plain-anchor)

def test_google_rdp_accountant_matches_full_batch_assumptions(tmp_path,monkeypatch):
    pytest.importorskip('dp_accounting')
    monkeypatch.setenv('BANK_DATA_DIR',str(tmp_path))
    from bank_clients.node import GoogleAccountant
    a=GoogleAccountant();a.step(1.2,1)
    first=a.get_epsilon(1e-5)
    a.step(1.2,1)
    assert a.get_epsilon(1e-5)>first>0
    with pytest.raises(ValueError):a.step(1.2,.5)
