"""Exact endpoint evidence checker, independent of numerical search."""
import gzip,json,sys
from pathlib import Path
from fractions import Fraction as F
import checkcert as C
import kuhn3p as K
from family_data import family_labels
sys.path.insert(0,str(Path(__file__).parent/"independent_check"))
import indep

def check(paths,full=True):
    with gzip.open("nefull_certs.json.gz","rt") as f: bounds=json.load(f)
    data={}
    for p in paths:
        with gzip.open(p,"rt") as f: part=json.load(f)
        assert not data.keys() & part.keys(), "Duplicate endpoint"
        data.update(part)
    assert data and data.keys() <= bounds.keys(), "Empty or unknown endpoint set"
    if full: assert data.keys()==bounds.keys(), "Incomplete endpoint coverage"
    labels=family_labels(); counts=dict(ATTAINED=0,EXCLUDED=0,UNKNOWN=0); seen={}
    for key,r in data.items():
        k,name,word=key.split(":"); lab=labels[int(k)]; T=F(r["T"]); b=bounds[key]
        assert T==F(b["T"]), "Wrong bound"
        status=r["status"]; assert status in counts
        if status=="ATTAINED":
            x=tuple(F(q) for q in r["profile"]); assert len(x)==48
            assert all(0<=q<=1 for q in x)
            assert all((lab[i] not in (0,1) or x[i]==lab[i]) and (lab[i]!=2 or 0<x[i]<1) for i in range(48)), "Wrong leaf"
            assert x[K.NAME_IDX[name]]==T, "Endpoint not reached"
            if x not in seen:
                p={K.PARAM_NAME[i]:x[i] for i in range(48)}
                assert indep.exploitability(p)==[F(0)]*3, "Profitable deviation"
                assert not indep.dcond(p), "Leaf D-condition violated"
                seen[x]=True
        elif status=="EXCLUDED":
            if r["kind"]=="open_label":
                assert lab[K.NAME_IDX[name]]==2 and T in (0,1)
            else:
                assert r["kind"]=="closed_side"
                cert=r["cert"]; gens=cert["gens"]; n=len(gens); t=gens.index(K.NAME_IDX[name])
                sign=1 if word=="sup" else -1
                side=C.pscale(C.padd(C.var(t,n),C.const(-T,n)),F(sign))
                base=C.rowof_for(lab,gens)
                def rowof(o):
                    return (side,">=") if o[0]=="side" else base(o)
                C.check_box_cert(cert,rowof,lab)
        counts[status]+=1
    print(json.dumps(counts),flush=True)
    return counts
if __name__=="__main__":
    paths=sorted(Path("attainment").glob("leaf-*.json.gz"))
    counts=check(paths)
    Path("attainment/summary.json").write_text(json.dumps({"counts":counts,"coverage":sum(counts.values()),
        "meaning":"ATTAINED: exact leaf equilibrium at bound. EXCLUDED: bound cannot be reached, not necessarily a tight infimum/supremum. UNKNOWN: no conclusion."},indent=2)+"\n")
    print("ALL ENDPOINT EVIDENCE VERIFIED")
