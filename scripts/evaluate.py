"""Measured synthetic-only model comparisons and privacy utility experiments."""
import argparse
import json
from pathlib import Path
import secrets
import tempfile
import numpy as np
from backend.ml import synthetic, transform, sigmoid, metrics, fedavg, evaluate, FEATURES

def optimize(x,y,w,steps=20,noise=None,clip=1,mu=0,anchor=None):
    rng=np.random.default_rng(secrets.randbits(128))
    for _ in range(steps):
        g=((sigmoid(x@w)-y)*np.where(y==1,1.0,.12))[:,None]*x
        if noise is not None:
            g*=np.minimum(1,clip/np.maximum(np.linalg.norm(g,axis=1),1e-12))[:,None]
            grad=(g.sum(0)+rng.normal(0,noise*clip,7))/len(x)
        else: grad=g.mean(0)
        if mu: grad+=mu*(w-anchor)
        w=w-3.0*grad
    return w
def main(rounds=5):
    output=Path('docs/reports'); output.mkdir(parents=True,exist_ok=True)
    cohorts=[synthetic(n,101+i,i,drift=i==2) for i,n in enumerate([4500,3500,2000])]
    hold,ytest=synthetic(3000,999,1); test=transform(hold)
    local=[]
    for i,(x,y) in enumerate(cohorts): local.append({'bank':f'bank_{chr(97+i)}','metrics':evaluate(optimize(transform(x),y,np.zeros(7),60).tolist())})
    x=np.vstack([transform(a) for a,b in cohorts]); y=np.concatenate([b for a,b in cohorts])
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from xgboost import XGBClassifier
    models={'LogisticRegression':LogisticRegression(max_iter=300),'DecisionTree':DecisionTreeClassifier(max_depth=6,random_state=42),'RandomForest':RandomForestClassifier(n_estimators=80,max_depth=8,random_state=42),'GradientBoosting':GradientBoostingClassifier(n_estimators=80,random_state=42),'XGBoost':XGBClassifier(n_estimators=80,max_depth=4,random_state=42,n_jobs=2)}
    baselines={}
    for name,model in models.items():
        model.fit(x[:,:6],y); baselines[name]=metrics(ytest,model.predict_proba(test[:,:6])[:,1])
    # SHAP on synthetic features only. Local/global operational model also has exact log-odds contributions.
    import shap
    explainer=shap.Explainer(models['LogisticRegression'],x[:100,:6])
    explanations=explainer(test[:10,:6])
    (output/'shap-example.json').write_text(json.dumps({'features':FEATURES,'values':explanations.values.tolist(),'base_values':explanations.base_values.tolist(),'notice':'Synthetic logistic SHAP log-odds, not causal proof'},indent=2))
    experiments=[]
    from opacus.accountants import RDPAccountant
    for noise in [None,.8,1.2,2.0]:
        w=np.zeros(7); history=[]; accountant=RDPAccountant()
        for r in range(rounds):
            updates=[]
            for i,(local_x,local_y) in enumerate(cohorts):
                weights=optimize(transform(local_x),local_y,w.copy(),steps=10,noise=noise)
                updates.append({'parameters':weights.tolist(),'weight':1})
            w=np.asarray(fedavg(updates)); history.append({'round':r+1,'metrics':evaluate(w.tolist())})
            if noise is not None:
                for _ in range(10): accountant.step(noise_multiplier=noise,sample_rate=1)
        experiments.append({'noise_multiplier':noise,'clipping_norm':1,'delta':1e-5,'epsilon':accountant.get_epsilon(1e-5) if noise else None,'accounting':'per-bank sequential RDP; parallel disjoint synthetic banks; q=1','history':history,'metrics':evaluate(w.tolist())})
    report={'synthetic_only':True,'records':10000,'local_models':local,'centralized_synthetic_baselines':baselines,'privacy_utility':experiments,'limitations':['Synthetic benchmark only; no real-bank claims','Equal public client weights','Fixed public preprocessing','Non-cryptographic RNG','Noise configurations have different privacy loss; compare epsilon with utility','Tree baselines are centralized synthetic experiments, not federatable parameters']}
    (output/'evaluation.json').write_text(json.dumps(report,indent=2))
    print('Wrote measured evaluation and SHAP reports to docs/reports')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--rounds',type=int,default=5); a=p.parse_args(); main(a.rounds)
