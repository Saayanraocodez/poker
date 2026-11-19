"""Second pass: stronger stored bounds, exact family grids, endpoint-equality proofs."""
import gzip,json,itertools,sys
from pathlib import Path
from fractions import Fraction as F
import sympy as sp
import nefull,seqset,symleaf as SL,certbox,checknefull as CN,checkcert as C
from family_data import family_labels

def main(k):
    path=Path(f"attainment/leaf-{k}.json.gz")
    with gzip.open(path,"rt") as f: data=json.load(f)
    lab=family_labels()[k]
    X,syms,G,mixv,dcv,priv,gens,polys,kinds,orig=nefull.leaf_system(lab)
    gidx=mixv+dcv; rows=C.leaf_system(lab)
    def compatible(x):
        return all(0<=q<=1 and (lab[i] not in (0,1) or q==lab[i]) and (lab[i]!=2 or 0<q<1) for i,q in enumerate(x))
    def valid(x):
        return compatible(x) and all((CN.evaluate(p,x)==0 if kind=="=" else CN.evaluate(p,x)>=0 if kind==">=" else CN.evaluate(p,x)>0) for p,kind in rows)
    parameters=["b11","b21","b23","c11"]
    grid=[F(0),F(1,64),F(1,16),F(1,8),F(1,6),F(1,4),F(1,2)]
    choices=[[F(lab[nefull.I[n]])] if lab[nefull.I[n]] in (0,1) else grid for n in parameters]
    candidates=[]
    for pars in itertools.product(*choices):
        x=seqset.family_point(*pars,{})
        if compatible(x): candidates.append(x)
    for key,r in data.items():
        if r["status"]!="UNKNOWN": continue
        _,name,word=key.split(":"); T=F(r["T"]); v=nefull.I[name]; sign=1 if word=="sup" else -1
        p=Path(f"ranges_sharpened/{k}_{name}_{word}.json")
        if p.exists():
            sharp=json.loads(p.read_text())
            assert sharp["leaf"]==k and sharp["coord"]==name and sharp["side"]==word
            if sign*(T-F(sharp["T"]))>0:
                r.update(status="EXCLUDED",kind="stronger_bound",stronger_T=sharp["T"],cert=sharp["cert"])
        if r["status"]=="UNKNOWN":
            for seed in candidates:
                x=list(seed); x[v]=T
                if valid(x):
                    r.update(status="ATTAINED",profile=[str(q) for q in x]); break
        if r["status"]=="UNKNOWN":
            t=gidx.index(v); side=sign*(gens[t]-sp.Rational(T.numerator,T.denominator))
            result=certbox.prove_empty_cert(polys+[side],kinds+["="],gens,SL._bounds(lab,mixv,dcv),200,
                origins=orig+[("side",)],lab=lab,gidx=gidx,chord=False,exact_dual=False)
            if result[0]:
                result[1]["gens"]=gidx
                r.update(status="EXCLUDED",kind="endpoint_equality",cert=result[1])
        print(key,r["status"],flush=True)
    with gzip.open(path,"wt") as f: json.dump(data,f,sort_keys=True)
if __name__=="__main__": main(int(sys.argv[1]))
