"""D_all.pkl for the (3, 4) game: the 48 own-reach-stripped gradients D_i as dict-polynomials
{exponent tuple over the 48 coordinates: Fraction} -- the data checkcert.py, enumx.py, refine.py
and checkD.py load.  D_all.pkl is git-ignored, so a fresh clone has to regenerate it first.

Generator: symbet.build_D (sympy) with all 48 coordinates symbolic, as documented in enumx.py.
checkD.py then recomputes the 48 gradients from tree.py with its own Fraction recursion and
compares, so generator and check stay independent.

usage:  python makeD.py ; python checkD.py
"""
import pickle, time
from fractions import Fraction as F
import sympy as sp
import symbet, kuhn3p as K

t0 = time.time()
X = [sp.Symbol(K.PARAM_NAME[i]) for i in range(48)]
D = symbet.build_D(X)
out = []
for g in D:
    poly = sp.Poly(g, *X)
    out.append({tuple(int(e) for e in m): F(int(c.p), int(c.q)) for m, c in poly.terms() if c != 0})
pickle.dump(out, open("D_all.pkl", "wb"))
print("D_all.pkl: 48 gradients, %d terms, %.0fs" % (sum(len(p) for p in out), time.time() - t0))
