import numpy as np, sympy as sp, seqset, refine, itertools
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
lab = L[469]; J = refine.jac()
onpath = [i for i in range(48) if lab[i] == 2]
off0 = {n: F(0) for n in ("b32","c34","b22","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
off = dict(off0); off["c33"] = F(1,2)
s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
interior = [w for w in range(48) if 0 < s[w] < 1]
Mfull = sp.Matrix([[sp.Rational(refine.ev(J[v][w], s)) if w in J[v] else sp.Integer(0) for w in range(48)] for v in onpath])
Mint = sp.Matrix([[sp.Rational(refine.ev(J[v][w], s)) if w in J[v] else sp.Integer(0) for w in interior] for v in onpath])
print("rank of the 7x48 indifference Jacobian:", Mfull.rank())
print("rank restricted to interior coordinates %s: %d" % ([NAME[w] for w in interior], Mint.rank()))
r = Mint.rank()
if r == len(onpath):
    for cols in itertools.combinations(range(len(interior)), r):
        sub = Mint[:, list(cols)]
        if sub.det() != 0:
            print("nonsingular minor on", [NAME[interior[c]] for c in cols], "det =", sub.det()); break
else:
    # which equations are dependent?
    print("nullspace of the transpose (dependencies among the equations):")
    for v in Mfull.T.nullspace(): print("   ", {NAME[onpath[i]]: v[i] for i in range(len(onpath)) if v[i] != 0})
