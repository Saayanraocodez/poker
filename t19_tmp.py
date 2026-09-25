import numpy as np, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]; pieces = seqset.leaf_pieces(lab); J = refine.jac()
off0 = {n: F(0) for n in ("b32","c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
print("leaf 469, b11 = b21 = 1/8, c11 = 1/4:  which c33 give a sequential / perfect equilibrium?")
for c33 in (F(1,2), F(9,16), F(5,8), F(11,16), F(3,4), F(13,16)):
    off = dict(off0); off["c33"] = c33
    s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
    bad = seqset.verify_point(lab, s)
    if bad: print("  c33=%-5s  not Nash (%s)" % (c33, bad)); continue
    st, m, r = seqset.is_sequential(pieces, s, lab)
    ok, info = refine.perfect_cert(s, J)
    print("  c33=%-5s  Nash OK   sequential=%-11s  perfect=%-5s %s" % (c33, st, ok, info if not ok else "s*=%s, %d indifference equations, rank %d" % (info["s"], len(info["equations"]), info["rank"])))
