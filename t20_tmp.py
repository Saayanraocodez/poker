import numpy as np, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]; pieces = seqset.leaf_pieces(lab); J = refine.jac()
off0 = {n: F(0) for n in ("b32","c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
print("Nash window for c33 here: [1/2, 23/32];  perfection along it")
for c33 in (F(1,2), F(33,64), F(45,64), F(23,32), F(47,64)):
    off = dict(off0); off["c33"] = c33
    s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
    bad = seqset.verify_point(lab, s)
    if bad: print("  c33=%-6s  not Nash (%s)" % (c33, bad)); continue
    st, m, r = seqset.is_sequential(pieces, s, lab)
    ok, info = refine.perfect_cert(s, J)
    print("  c33=%-6s (%.4f)  sequential=%-11s perfect=%s %s" % (c33, float(c33), st, ok, "" if ok else info))
