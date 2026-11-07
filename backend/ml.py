"""Fixed, public preprocessing and a federatable logistic model."""
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix, brier_score_loss

FEATURES = ['amount', 'velocity', 'device_risk', 'geo_deviation', 'account_age', 'hour']
def transform(raw):
    x = np.asarray(raw, dtype=float).copy()
    defaults = np.array([100, 1, .1, .1, 365, 12])
    x = np.where(np.isfinite(x), x, defaults)
    x[:, 0] = np.log1p(np.clip(x[:, 0], 0, 1e6)) / np.log1p(1e6)
    x[:, 1] = np.clip(x[:, 1], 0, 100) / 100
    x[:, 2:4] = np.clip(x[:, 2:4], 0, 1)
    x[:, 4] = 1 - np.clip(x[:, 4], 0, 3650) / 3650
    x[:, 5] = (np.clip(x[:, 5], 0, 23) < 6).astype(float)
    return np.column_stack([x, np.ones(len(x))])
def sigmoid(z): return 1 / (1 + np.exp(-np.clip(z, -40, 40)))
def synthetic(n=1000, seed=42, bank_index=0, drift=False):
    rng = np.random.default_rng(seed)
    x = np.column_stack([rng.lognormal(4 + bank_index * .45, 1.3, n), rng.poisson(2 + bank_index * 2, n), rng.beta(1 + bank_index * .3, 5, n), rng.beta(1, 4, n), rng.exponential(700, n), rng.integers(0, 24, n)])
    risk = -5.2 + 4*x[:,2] + 3*x[:,3] + .18*x[:,1] + .0004*x[:,0] + .7*(x[:,5]<6) + (.8 if drift else 0)*x[:,2]
    y = rng.binomial(1, sigmoid(risk))
    x[rng.random(x.shape)<.015] = np.nan
    return x, y
def metrics(y, probabilities):
    pred = probabilities >= .5
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
    return {'accuracy':float(accuracy_score(y,pred)), 'precision':float(precision_score(y,pred,zero_division=0)), 'recall':float(recall_score(y,pred,zero_division=0)), 'f1':float(f1_score(y,pred,zero_division=0)), 'roc_auc':float(roc_auc_score(y,probabilities)), 'pr_auc':float(average_precision_score(y,probabilities)), 'false_positive_rate':float(fp/max(tn+fp,1)), 'false_negative_rate':float(fn/max(fn+tp,1)), 'confusion_matrix':[[int(tn),int(fp)],[int(fn),int(tp)]], 'brier_score':float(brier_score_loss(y,probabilities))}
def evaluate(parameters):
    x,y=synthetic(3000,seed=999,bank_index=1)
    return metrics(y,sigmoid(transform(x)@np.asarray(parameters)))
def fedavg(updates):
    if len(updates)<2: raise ValueError('At least two successful clients required')
    arrays = np.asarray([u['parameters'] for u in updates],float)
    weights = np.asarray([u['weight'] for u in updates],float)
    if arrays.shape[1:]!=(7,) or not np.isfinite(arrays).all() or np.any(weights<=0) or np.any(np.linalg.norm(arrays,axis=1)>100):
        raise ValueError('Invalid or anomalous update')
    # Flower's supported aggregation implementation is the primary FedAvg engine.
    from flwr.server.strategy.aggregate import aggregate
    return aggregate([([a],int(w)) for a,w in zip(arrays,weights)])[0].tolist()
