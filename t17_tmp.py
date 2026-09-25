import numpy as np, sympy as sp, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
lab = L[469]; J = refine.jac(); D = refine.D_all()
onpath = [i for i in range(48) if lab[i] == 2]
print("on-path MIX:", [NAME[i] for i in onpath])
off0 = {n: F(0) for n in ("b32","c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
for c33 in (F(1,2), F(5,8)):
    off = dict(off0); off["c33"] = c33
    s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
    JM = sp.Matrix([[sp.Rational(refine.ev(J[v][w], s)) if w in J[v] else sp.Integer(0) for w in onpath] for v in onpath])
    det = JM.det()
    # derivative of the c33 belief condition w.r.t. the ratio it pins
    pieces = seqset.leaf_pieces(lab)
    A = pieces[3][I["c33"]]
    syms = pieces[2]
    sub = {syms[i]: sp.Rational(s[i]) for i in sorted(syms)}
    a = sp.expand(A.subs(sub))
    dr = sp.diff(a, sp.Symbol("r_a41"))
    print("c33=%-4s  det(on-path indifference Jacobian) = %-12s %s   dA_c33/dr_a41 = %s" %
          (c33, det, "NONSINGULAR" if det != 0 else "SINGULAR", dr))
