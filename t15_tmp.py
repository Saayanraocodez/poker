import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
lab = L[469]; pieces = seqset.leaf_pieces(lab); J = refine.jac()
off0 = {n: F(0) for n in ("b32","c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24","a13","a23","a34","c12","c22","c32","a12","a22","a32","a11","a21","a31","b13","b31","b34","c31","b22")}
for c33 in (F(1,2), F(5,8), F(3,4), F(7,8)):
    off = dict(off0); off["c33"] = c33
    s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
    bad = seqset.verify_point(lab, s)
    st, m, r = seqset.is_sequential(pieces, s, lab) if bad is None else ("invalid: %s" % bad, None, None)
    t0 = time.time(); lp = refine.lp_first_order(s, J) if bad is None else (None, None, None)
    print("c33=%-4s  nash=%-22s  sequential=%-12s m=%-6s   perfect-LP: %s s*=%s (%.0fs)" % (
        c33, bad or "OK", st, m, lp[0], lp[1], time.time()-t0), flush=True)
    if lp[2] is not None and lp[1]:
        print("      tremble direction:", ", ".join("%s%+g" % (NAME[i], float(lp[2][i])) for i in range(48) if lp[2][i] != 0))
