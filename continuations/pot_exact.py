"""Continuation 3, exact part: the ante A as a parameter (bet = 1; the standard game is A = 1).

Regime "P2 always bets the 4" (roughly 1.1 <= A <= A2).  Closed-form profile F_A(b32, c33), q = 3A + 1:
    P1:  a_j1 = 0;  a32 = (3A-1)/q;  a33 = (6A-4)/q;  a42 = a43 = a44 = 1
    P2:  b11 = b21 = 1/q;  b33 = (3A-1)/q;  b41 = b42 = b43 = b44 = 1;  b32 free (off path)
    P3:  c11 = c21 = 1/q;  c41 = c42 = c43 = c44 = 1;  c33 free (off path);  everything else 0.
P1's deterrence window for the off-path calls with the 3:
    L(A) = (6A - 4)/q   <=   b32 + c33   <=   U(A) = (12A + 3)/q^2
(below L, P1 gains by bluffing cards 1 and 2; above U, by betting the 4).  L <= U iff 18A^2 - 18A - 7 <= 0,
i.e.  A <= A2 = (3 + sqrt(23))/6 = 1.29930...   Past A2 this silent family is gone.

Everything below is exact (Fractions, the independent engine with indep.ANTE = A).
usage: python pot_exact.py
"""
import os, sys
from fractions import Fraction as F
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'independent_check'))
import indep as I


def profile(A, b32, c33):
    q = 3 * A + 1
    p = {n: F(0) for n in I.NAMES}
    for l in 'abc':
        for s in ('42', '43', '44'): p[l + s] = F(1)
    p.update(a32=(3 * A - 1) / q, a33=(6 * A - 4) / q, b11=1 / q, b21=1 / q, b33=(3 * A - 1) / q, b41=F(1), b32=F(b32),
             c11=1 / q, c21=1 / q, c41=F(1), c33=F(c33))
    return p


def L(A): return (6 * A - 4) / (3 * A + 1)
def U(A): return (12 * A + 3) / (3 * A + 1) ** 2


if __name__ == "__main__":
    fails = 0
    for A in (F(11, 10), F(6, 5), F(5, 4), F(129, 100)):
        I.ANTE = A
        lo, hi = L(A), U(A)
        assert lo <= hi
        row = []
        for label, tot in (("L", lo), ("mid", (lo + hi) / 2), ("U", hi)):
            for b32 in (F(0), tot / 2):
                p = profile(A, b32, tot - b32)
                e = I.exploitability(p); row.append(max(e))
                fails += max(e) != 0
        below = I.exploitability(profile(A, 0, lo - F(1, 1000))); above = I.exploitability(profile(A, 0, hi + F(1, 1000)))
        fails += not (below[0] > 0 and above[0] > 0)
        u = I.utilities(profile(A, 0, lo))
        print("A = %-7s window [%s, %s] = [%.5f, %.5f]: exploitability exactly 0 at 6 points of the window: %s ; just outside P1 gains %s (below), %s (above) ; u = %s"
              % (A, lo, hi, float(lo), float(hi), all(v == 0 for v in row), below[0], above[0], [str(v) for v in u]))
    # past the threshold: the window is empty
    for A in (F(13, 10), F(7, 5)):
        print("A = %-7s L - U = %s > 0: the window is empty" % (A, L(A) - U(A))); fails += not (L(A) > U(A))
    # the threshold: L = U  <=>  18 A^2 - 18 A - 7 = 0
    import sympy as sp
    a = sp.symbols('A', positive=True)
    num = sp.factor(sp.together((6 * a - 4) / (3 * a + 1) - (12 * a + 3) / (3 * a + 1) ** 2))
    print("L(A) - U(A) =", num, "  roots:", sp.solve(sp.numer(num), a), " A2 = (3 + sqrt(23))/6 =", float((3 + sp.sqrt(23)) / 6))
    I.ANTE = 1
    print("ALL EXACT CHECKS PASSED" if not fails else "%d FAILED" % fails)
