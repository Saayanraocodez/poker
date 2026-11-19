"""Bounded endpoint search. Only exact evidence changes UNKNOWN."""
import gzip,json,sys
from pathlib import Path
from fractions import Fraction as F
import numpy as np
import sympy as sp
from scipy.optimize import least_squares
import nefull, symleaf as SL, certbox, checkcert as C, checknefull as CN
from family_data import family_labels

def search(k):
    lab=family_labels()[k]
    X,syms,G,mixv,dcv,priv,gens,polys,kinds,orig=nefull.leaf_system(lab)
    gidx=mixv+dcv
    D=C.leaf_D(lab); rows=C.leaf_system(lab)
    def valid(x):
        if any(not 0<=q<=1 for q in x): return False
        if any((lab[i] in (0,1) and x[i]!=lab[i]) or (lab[i]==2 and not 0<x[i]<1) for i in range(48)): return False
        return all((CN.evaluate(p,x)==0 if kind=="=" else CN.evaluate(p,x)>=0 if kind==">=" else CN.evaluate(p,x)>0) for p,kind in rows)
    seeds=[]
    with gzip.open(f"seqcert_{k}.jsonl.gz","rt") as f:
        for line in f:
            r=json.loads(line)
            if r.get("kind")=="witness":
                x=[F(r["witness"][nefull.NAME[i]]) for i in range(48)]
                if valid(x): seeds.append(x)
    assert seeds
    def complete(vals):
        x=[F(int(v)) if v in (0,1) else F(0) for v in lab]
        for i,q in zip(gidx,vals): x[i]=q
        for i in priv: x[i]=F(int(CN.evaluate(D[i],x)>0))
        return x
    funcs=[sp.lambdify(gens,p,"numpy",cse=True) for p in polys]
    with gzip.open("nefull_certs.json.gz","rt") as f: bounds=json.load(f)
    out={}
    for key,rec in bounds.items():
        if not key.startswith(f"{k}:"): continue
        _,name,word=key.split(":"); v=nefull.I[name]; t=gidx.index(v); T=F(rec["T"]); sign=rec["sign"]
        evidence={"T":str(T),"status":"UNKNOWN"}
        if lab[v]==2 and T in (0,1):
            evidence.update(status="EXCLUDED",kind="open_label")
        else:
            # Exact coordinate replacements on already verified profiles.
            for seed in seeds:
                x=list(seed); x[v]=T
                if valid(x):
                    evidence.update(status="ATTAINED",profile=[str(q) for q in x]); break
        if evidence["status"]=="UNKNOWN":
            free=[j for j in range(len(gens)) if j!=t]
            lo=np.array([1e-6 if lab[gidx[j]]==2 else 0.0 for j in free])
            hi=np.array([1-1e-6 if lab[gidx[j]]==2 else 1.0 for j in free])
            def residual(y):
                x=np.empty(len(gens)); x[t]=float(T); x[free]=y
                return np.array([float(fn(*x)) if kind=="=" else min(0.0,float(fn(*x))) for fn,kind in zip(funcs,kinds)])
            for seed in seeds[:2]:
                try:
                    fit=least_squares(residual,np.clip([float(seed[gidx[j]]) for j in free],lo+1e-9,hi-1e-9),
                        bounds=(lo,hi),max_nfev=180,gtol=1e-13,ftol=1e-13,xtol=1e-13)
                except ValueError: continue
                vals=np.empty(len(gens)); vals[t]=float(T); vals[free]=fit.x
                for den in (2,4,8,16,32,64,128,256,1024,10000,1000000):
                    q=[T if j==t else F(float(a)).limit_denominator(den) for j,a in enumerate(vals)]
                    x=complete(q)
                    if valid(x):
                        evidence.update(status="ATTAINED",profile=[str(a) for a in x]); break
                if evidence["status"]=="ATTAINED": break
        if evidence["status"]=="UNKNOWN":
            side=sign*(gens[t]-sp.Rational(T.numerator,T.denominator))
            r=certbox.prove_empty_cert(polys+[side],kinds+[">="],gens,SL._bounds(lab,mixv,dcv),40,
                origins=orig+[("side",)],lab=lab,gidx=gidx,chord=False,exact_dual=False)
            if r[0]:
                r[1]["gens"]=gidx
                evidence.update(status="EXCLUDED",kind="closed_side",cert=r[1])
        out[key]=evidence
        print(key,evidence["status"],flush=True)
        Path("attainment").mkdir(exist_ok=True)
        with gzip.open(f"attainment/leaf-{k}.json.gz","wt") as f: json.dump(out,f,sort_keys=True)
    assert len(out)==2*len(gens)
if __name__=="__main__": search(int(sys.argv[1]))
