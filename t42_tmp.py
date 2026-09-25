"""which of the enumeration's sequential witnesses are PERFECT?"""
import json, glob, numpy as np, refine, seqset
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
J = refine.jac()
ok = no = 0
for p in sorted(glob.glob("seq_*.json")):
    d = json.load(open(p)); k = d["leaf"]
    for rec in d["cases"]:
        if rec["status"] != "SEQUENTIAL": continue
        s = [F(rec["witness"][NAME[i]]) for i in range(48)]
        good, info = refine.perfect_cert(s, J)
        tag = {n: v for n, v in rec["assign"].items() if n in ("b22", "c23", "c33", "a33", "a34", "c32")}
        print("leaf %4d %-46s perfect=%-5s %s" % (k, str(tag), good, "" if good is True else str(info)[:70]), flush=True)
        ok += bool(good); no += (not good)
print("perfect %d, not certified perfect %d" % (ok, no))
