"""Independent recomputation of the 48 own-reach-stripped gradients D_i from
the game tree (tree.py: positions, owners, coordinates per deal, leaf payoffs),
in Fractions on dict-polynomials, compared with D_all.pkl -- the data every
leaf certificate (checkcert.py) starts from.

    D_i = (1/24) sum over the nodes n of coordinate i's information set of
          R_{-i}(n) * (V_owner(agg child) - V_owner(pass child))
    R_{-i}(n): product of the OTHER players' coordinates (x or 1 - x) on the
    path to n, own coordinates replaced by 1;  V: continuation values below n,
    V(n) = x V(agg) + (1 - x) V(pass) with x = the coordinate at n.

Also prints the tree in words (owner, coordinate name, payoffs per deal) so
the game definition itself can be read against the paper.

usage:  python checkD.py [-v]
"""
import sys, pickle
from fractions import Fraction as F
import tree as T, kuhn3p as K

NV = 48
def var(j): return {tuple(1 if t == j else 0 for t in range(NV)): F(1)}
def const(c): return {tuple([0] * NV): F(c)} if c else {}
def padd(p, q, s=F(1)):
    out = dict(p)
    for m, c in q.items(): out[m] = out.get(m, F(0)) + s * c
    return {m: c for m, c in out.items() if c}
def pmul(p, q):
    out = {}
    for m1, c1 in p.items():
        for m2, c2 in q.items():
            m = tuple(a + b for a, b in zip(m1, m2)); out[m] = out.get(m, F(0)) + c1 * c2
    return {m: c for m, c in out.items() if c}
def pscale(p, c): return {m: c * v for m, v in p.items()} if c else {}

INT = list(T.INTERNAL); LEAF = list(T.LEAFPOS)
assert T.ND == 24 and K.KAPPA == 1 / 24
D = [{} for _ in range(NV)]
for d in range(T.ND):
    V = {}
    for pos in LEAF:
        V[pos] = [const(F(int(T.PAYT[d, pos, i]))) for i in range(3)]
        assert float(T.PAYT[d, pos, 0]) == int(T.PAYT[d, pos, 0])
    for pos in INT[::-1]:
        x = var(T.COORD[d, pos]); one_x = padd(const(1), x, F(-1))
        V[pos] = [padd(pmul(x, V[T.AGGC[pos]][i]), pmul(one_x, V[T.PASC[pos]][i])) for i in range(3)]
    R = {0: [const(1)] * 3}
    for pos in INT:
        x = var(T.COORD[d, pos]); one_x = padd(const(1), x, F(-1)); own = T.OWNER[pos][0]
        R[T.AGGC[pos]] = [R[pos][i] if i == own else pmul(R[pos][i], x) for i in range(3)]
        R[T.PASC[pos]] = [R[pos][i] if i == own else pmul(R[pos][i], one_x) for i in range(3)]
    for pos in INT:
        i = T.OWNER[pos][0]; c = T.COORD[d, pos]
        D[c] = padd(D[c], pscale(pmul(R[pos][i], padd(V[T.AGGC[pos]][i], V[T.PASC[pos]][i], F(-1))), F(1, 24)))
D_ALL = pickle.load(open("D_all.pkl", "rb"))
bad = 0
for i in range(NV):
    ref = {m: F(c) for m, c in D_ALL[i].items() if F(c)}
    if ref != D[i]: bad += 1; print("D_%s differs" % K.PARAM_NAME[i])
print("D_all.pkl: %d of 48 gradients agree with the independent tree computation  %s" % (48 - bad, "OK" if bad == 0 else "*** FAIL"))
if "-v" in sys.argv:
    print("\ninternal positions (owner, coordinate per deal):")
    for pos in INT:
        print("  pos %2d owner P%d  coords: %s" % (pos, T.OWNER[pos][0] + 1, " ".join(K.PARAM_NAME[T.COORD[d, pos]] for d in range(T.ND))))
    print("leaf payoffs (deal 0..23) per position:")
    for pos in LEAF:
        print("  pos %2d  " % pos + " ".join("(%d,%d,%d)" % tuple(int(T.PAYT[d, pos, i]) for i in range(3)) for d in range(T.ND)))
