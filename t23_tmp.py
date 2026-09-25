import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]; pieces = seqset.leaf_pieces(lab)
base = {n: F(0) for n in ("c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
print("complete over the orderings of P1's opening trembles:")
for b32, c33 in ((F(0), F(5,8)), (F(1,2), F(0)), (F(1,4), F(1,4)), (F(1,2), F(1,8)), (F(1,8), F(1,2))):
    off = dict(base); off["b32"] = b32; off["c33"] = c33
    s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
    if seqset.verify_point(lab, s): print("  b32=%-5s c33=%-5s not Nash" % (b32, c33)); continue
    t0 = time.time(); st, order, sol = seqset.seq_orderings(lab, s, pieces)
    print("  b32=%-5s c33=%-5s -> %-15s order %s  (%.0fs)" % (b32, c33, st, order, time.time()-t0), flush=True)
