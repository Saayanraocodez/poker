import numpy as np, json, gzip, time, sympy as sp, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
with gzip.open("nefull_certs.json.gz","rt") as f: C = json.load(f)
k = 469; lab = L[k]; pieces = seqset.leaf_pieces(lab)
ws = [(kk, r["witness"]) for kk, r in C.items() if kk.startswith("%d:" % k) and r.get("witness")]
print("%d witnesses of leaf %d" % (len(ws), k))
for kk, w in ws[:6]:
    vals = {nm: F(*map(int, s.split("/"))) for nm, s in w.items()}
    sig = refine.profile_from(lab, vals)
    t0 = time.time(); st, m, r = seqset.is_sequential(pieces, sig, lab)
    print("  %-16s -> %-12s m=%-8s %s (%.1fs)" % (kk, st, m, {a: str(b) for a, b in list(r.items())[:4]} if r else "", time.time()-t0), flush=True)
