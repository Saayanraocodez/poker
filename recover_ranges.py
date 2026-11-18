"""Re-prove stored range bounds from committed labels; never trust old verdicts.
Decimal bounds are rounded outward by one final displayed unit.
Output records certify outer bounds only; historical attainment flags are not copied.
"""
import gzip, json, sys, time
from pathlib import Path
from fractions import Fraction as F
import sympy as sp
import nefull, symleaf as SL, certbox
from family_data import family_labels

def recover(k):
    lab = family_labels()[k]
    X, syms, G, mixv, dcv, priv, gens, polys, kinds, origins = nefull.leaf_system(lab)
    gidx = mixv + dcv
    bounds = SL._bounds(lab, mixv, dcv)
    records = {}
    for line in Path("nefull_ranges.txt").read_text().splitlines():
        fields = line.split()
        if not fields or fields[0] != str(k): continue
        name = fields[2]; v = nefull.I[name]; g = syms[v]
        for sign, word, text in [(-1,"inf",fields[4]),(1,"sup",fields[5])]:
            T = F(text)
            if "." in text:
                T += sign * F(1,10**len(text.split(".")[1]))
            side = sign * (g - sp.Rational(T.numerator,T.denominator))
            result = None
            for budget, chord in [(1,False),(60,False),(400,True),(2000,True)]:
                r = certbox.prove_empty_cert(polys+[side],kinds+[">"],gens,bounds,budget,
                    origins=origins+[("side",)],lab=lab,gidx=gidx,chord=chord,exact_dual=chord)
                if r[0]: result=r[1]; break
            if result is None:
                raise RuntimeError(f"Could not certify {k}:{name}:{word} at {T}")
            result["gens"]=gidx
            key=f"{k}:{name}:{word}"
            records[key]={"T":certbox.fstr(T),"sign":sign,"attained":None,"cert":result,"witness":None,
                "provenance":"Regenerated outer bound; attainment not asserted"}
            print(key,str(T),"VERIFIED BY GENERATOR",flush=True)
            with gzip.open(f"recovered-ranges-{k}.json.gz","wt") as f: json.dump(records,f)
    assert len(records)==2*len(gens), (k,len(records),len(gens))
    return records
if __name__=="__main__":
    recover(int(sys.argv[1]))
