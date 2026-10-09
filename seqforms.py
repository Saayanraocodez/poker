"""CHECKER-SIDE belief forms for Theorem 6, sympy-free.

Rebuilds, from the game tree alone (tree.py), in Fractions on dict-polynomials:
  D_v -- the own-reach-stripped gradient (same recursion as checkD.py),
  R_v -- the reach of v's information set with the owner's own choices stripped,
and the LEADING COEFFICIENT of D_v along a tremble: every coordinate the profile puts
at 0 trembles as eps*r_w, at 1 as 1 - eps*r_w, the rest stay symbolic (or take given
rational values).  Variables: x_0..x_47 are indices 0..47, r_0..r_47 are 48..95.
Nothing here imports sympy, seqset, refine or certbox.
"""
from fractions import Fraction as F
from itertools import combinations
import tree as T

NX = 48; NVAR = 96
def R_(w): return NX + w


def _var(j, n=NX):
    return {tuple(1 if t == j else 0 for t in range(n)): F(1)}
def _const(c, n=NX): return {tuple([0] * n): F(c)} if c else {}
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

_DR = None
def DR():
    """(D, R): lists of 48 dict-polys over x (48-tuples)."""
    global _DR
    if _DR is not None: return _DR
    D = [{} for _ in range(NX)]; RE = [{} for _ in range(NX)]
    INT = list(T.INTERNAL); LEAF = list(T.LEAFPOS)
    for d in range(T.ND):
        V = {}
        for pos in LEAF: V[pos] = [_const(F(int(T.PAYT[d, pos, i]))) for i in range(3)]
        for pos in INT[::-1]:
            x = _var(T.COORD[d, pos]); ox = padd(_const(1), x, F(-1))
            V[pos] = [padd(pmul(x, V[T.AGGC[pos]][i]), pmul(ox, V[T.PASC[pos]][i])) for i in range(3)]
        Rr = {0: [_const(1)] * 3}
        for pos in INT:
            x = _var(T.COORD[d, pos]); ox = padd(_const(1), x, F(-1)); own = T.OWNER[pos][0]
            Rr[T.AGGC[pos]] = [Rr[pos][i] if i == own else pmul(Rr[pos][i], x) for i in range(3)]
            Rr[T.PASC[pos]] = [Rr[pos][i] if i == own else pmul(Rr[pos][i], ox) for i in range(3)]
        for pos in INT:
            i = T.OWNER[pos][0]; c = T.COORD[d, pos]
            D[c] = padd(D[c], pscale(pmul(Rr[pos][i], padd(V[T.AGGC[pos]][i], V[T.PASC[pos]][i], F(-1))), F(1, 24)))
            RE[c] = padd(RE[c], pscale(Rr[pos][i], F(1, 24)))
    _DR = (D, RE)
    return _DR


def leading(poly, pin0, pin1, values=None, maxorder=12):
    """Lowest eps-order coefficient of `poly` (a dict-poly over x) under the tremble
    x_w -> eps r_w (w in pin0), x_w -> 1 - eps r_w (w in pin1); coordinates in `values`
    are replaced by the given Fractions; the rest stay x_w.  -> (order, coefficient as a
    dict-poly over the 96 variables) or (None, {})."""
    values = values or {}
    pin0 = set(pin0); pin1 = set(pin1)
    for k in range(maxorder + 1):
        out = {}
        for mon, c in poly.items():
            ws = [w for w, e in enumerate(mon) if e]
            z = [w for w in ws if w in pin0]
            if len(z) > k: continue
            o = [w for w in ws if w in pin1]
            fr_ = [w for w in ws if w not in pin0 and w not in pin1]
            coef = c
            skip = False
            for w in fr_:
                if w in values:
                    coef = coef * values[w]
                    if coef == 0: skip = True; break
            if skip: continue
            base = [0] * NVAR
            for w in z: base[R_(w)] += 1
            for w in fr_:
                if w not in values: base[w] += 1
            need = k - len(z)
            if need > len(o): continue
            for T_ in combinations(o, need):
                m = list(base)
                for w in T_: m[R_(w)] += 1
                cc = coef * (-1) ** need
                m = tuple(m); out[m] = out.get(m, F(0)) + cc
        out = {m: c for m, c in out.items() if c}
        if out: return k, out
    return None, {}


def one_signed(p):
    """-1 / +1 if every coefficient of p has that sign (all variables are >= 0), else 0."""
    cs = list(p.values())
    if not cs: return 0
    if all(c < 0 for c in cs): return -1
    if all(c > 0 for c in cs): return 1
    return 0


def evaluate(p, vals):
    """exact value of a dict-poly over the 96 variables at vals {index: Fraction}
    (missing variables are 0)."""
    s = F(0)
    for m, c in p.items():
        t = c
        for j, e in enumerate(m):
            if e:
                t *= vals.get(j, F(0)) ** e
                if t == 0: break
        s += t
    return s
