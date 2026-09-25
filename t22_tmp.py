import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]
base = {n: F(0) for n in ("c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
for b32, c33 in ((F(1,2), F(0)), (F(1,4), F(1,4)), (F(0), F(5,8))):
    off = dict(base); off["b32"] = b32; off["c33"] = c33
    s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
    if seqset.verify_point(lab, s): print("  b32=%s c33=%s not Nash" % (b32, c33)); continue
    t0 = time.time(); st, orders, sol = seqset.seq_layered(lab, s)
    hi = {NAME[w]: k for w, k in orders.items() if k > 1}
    print("  b32=%-5s c33=%-5s -> %-15s orders>1: %s   (%.0fs)" % (b32, c33, st, hi, time.time()-t0), flush=True)
    if sol: print("      beliefs:", {a: str(b) for a, b in sol.items() if b != 0})
