import numpy as np, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]; pieces = seqset.leaf_pieces(lab); J = refine.jac()
base = {n: F(0) for n in ("c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
print("the OTHER branch: c33 at a corner, b32 free")
for b32, c33 in ((F(1,2), F(0)), (F(5,8), F(0)), (F(23,32), F(0)), (F(1,2), F(1,8)), (F(3,8), F(1,8)), (F(1,4), F(1,4))):
    off = dict(base); off["b32"] = b32; off["c33"] = c33
    s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
    bad = seqset.verify_point(lab, s)
    if bad: print("  b32=%-5s c33=%-5s  not Nash (%s)" % (b32, c33, bad)); continue
    st, m, r = seqset.is_sequential(pieces, s, lab)
    ok, info = refine.perfect_cert(s, J)
    rr = ", ".join("%s=%s" % (a, b) for a, b in r.items() if str(a) in ("r_a11","r_a21","r_a31","r_a41")) if r else ""
    print("  b32=%-5s c33=%-5s  sequential=%-11s perfect=%-5s  %s %s" % (b32, c33, st, ok, rr, "" if ok else info))
