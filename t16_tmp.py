import numpy as np, sympy as sp, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
lab = L[469]; pieces = seqset.leaf_pieces(lab); J = refine.jac(); D = refine.D_all()
off0 = {n: F(0) for n in ("b32","c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
for c33 in (F(1,2), F(5,8)):
    off = dict(off0); off["c33"] = c33
    s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
    M = [v for v in range(48) if 0 < s[v] < 1]
    JM = sp.Matrix([[sp.Rational(refine.ev(J[v][w], s).numerator, refine.ev(J[v][w], s).denominator) if w in J[v] else 0 for w in M] for v in M])
    det = JM.det()
    st, val, delta = refine.lp_first_order(s, J)
    strict = []; tight = []
    for v in range(48):
        d0 = refine.ev(D[v], s)
        if s[v] in (0, 1) and d0 == 0:
            g = sum((refine.ev(J[v][w], s) * delta[w]) for w in J[v])
            (tight if g == 0 else strict).append((NAME[v], g))
    zero_tremble = [NAME[v] for v in range(48) if s[v] in (0, 1) and delta[v] == 0]
    print("c33=%s:  MIX %s" % (c33, [NAME[v] for v in M]))
    print("   det of the indifference Jacobian = %s  (%s)" % (det, "NONSINGULAR" if det != 0 else "singular"))
    print("   LP %s s*=%s;  first-order conditions strict at %d coordinates, TIGHT at %s" % (st, val, len(strict), [t[0] for t in tight]))
    print("   coordinates with no first-order tremble: %s" % (zero_tremble or "none"))
