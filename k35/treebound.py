"""Exact (Fractions) tree-structured interval bounds on the own-reach-stripped
gradients D_i over a box of the 48 coordinates -- ivl.bounds' recursion with
the owner's reach factor stripped, in rational arithmetic.

Why.  exactbox bounds a constraint by summing the ranges of its monomials, which
throws away the game tree: on the 8 leaves of a11:0,a21:MIX,a31:0,a41:1 that
the LP relaxation could not close in 20,000 nodes, bnb6's interval rules (the
same recursion in floats) kill the leaf box in 50.  The recursion keeps the
shared prefixes of the paths, so its enclosure of D_i is far tighter than the
monomial one, and it is cheap: ~1,000 rational operations per box.

    d_bounds(lo, hi) -> (DLO, DHI): lists of 48 Fractions with
        DLO_i <= D_i(x) <= DHI_i  for every x in the box [lo, hi] (48 intervals in [0,1])

Soundness: V(n) = P + x (A - P) is affine in x and increasing in A and P for
x in [0, 1], so its extremes over the box are at (al, pl) / (ah, ph) and an
endpoint of x; R_{-k} is a product of numbers in [0, 1]; D_i sums
R_{-k}(n) * (V_k(agg) - V_k(pass)) over the six nodes of i, and a product of a
non-negative interval with an interval is bounded as in ivl.
"""
from fractions import Fraction as F
import tree as T
import kuhn3p as K

ND, NPOS = T.ND, T.NPOS
INT = list(T.INTERNAL); LEAF = list(T.LEAFPOS)
AGGC, PASC, COORD = T.AGGC, T.PASC, T.COORD
OWNER = [T.OWNER[p][0] for p in range(NPOS) if p in T.OWNER] if isinstance(T.OWNER, dict) else None
PAY = [[[F(int(T.PAYT[d, pos, i])) for i in range(3)] for pos in range(NPOS)] for d in range(ND)]
OWN = {pos: T.OWNER[pos][0] for pos in INT}


def d_bounds(lo, hi):
    DLO = [F(0)] * K.NPARAM; DHI = [F(0)] * K.NPARAM
    for d in range(ND):
        Vlo = [None] * NPOS; Vhi = [None] * NPOS
        for pos in LEAF:
            Vlo[pos] = PAY[d][pos]; Vhi[pos] = PAY[d][pos]
        for pos in INT[::-1]:
            c = COORD[d, pos]; xl, xh = lo[c], hi[c]
            al, ah = Vlo[AGGC[pos]], Vhi[AGGC[pos]]; pl, ph = Vlo[PASC[pos]], Vhi[PASC[pos]]
            vl = [None] * 3; vh = [None] * 3
            for i in range(3):
                dl = al[i] - pl[i]; dh = ah[i] - ph[i]
                vl[i] = min(pl[i] + xl * dl, pl[i] + xh * dl)
                vh[i] = max(ph[i] + xl * dh, ph[i] + xh * dh)
            Vlo[pos] = vl; Vhi[pos] = vh
        # reach with player k's own coordinates stripped, per player
        Rlo = {0: [F(1)] * 3}; Rhi = {0: [F(1)] * 3}
        for pos in INT:
            c = COORD[d, pos]; xl, xh = lo[c], hi[c]; own = OWN[pos]
            Rlo[AGGC[pos]] = [Rlo[pos][k] if k == own else Rlo[pos][k] * xl for k in range(3)]
            Rhi[AGGC[pos]] = [Rhi[pos][k] if k == own else Rhi[pos][k] * xh for k in range(3)]
            Rlo[PASC[pos]] = [Rlo[pos][k] if k == own else Rlo[pos][k] * (1 - xh) for k in range(3)]
            Rhi[PASC[pos]] = [Rhi[pos][k] if k == own else Rhi[pos][k] * (1 - xl) for k in range(3)]
        for pos in INT:
            k = OWN[pos]; c = COORD[d, pos]
            dlo = Vlo[AGGC[pos]][k] - Vhi[PASC[pos]][k]; dhi = Vhi[AGGC[pos]][k] - Vlo[PASC[pos]][k]
            rl, rh = Rlo[pos][k], Rhi[pos][k]
            DLO[c] += (rl * dlo if dlo >= 0 else rh * dlo)
            DHI[c] += (rh * dhi if dhi >= 0 else rl * dhi)
    return [v / 24 for v in DLO], [v / 24 for v in DHI]


def box48(lab, gens, box):
    """the 48-coordinate box of a leaf: labels 0/1 as points, the certificate's
    variables from `box` (list of [lo, hi, ...]), every other coordinate [0, 1]"""
    lo = [F(0)] * K.NPARAM; hi = [F(1)] * K.NPARAM
    for i in range(K.NPARAM):
        if lab[i] == 0: hi[i] = F(0)
        elif lab[i] == 1: lo[i] = F(1)
    for t, g in enumerate(gens):
        lo[g] = F(box[t][0]); hi[g] = F(box[t][1])
    return lo, hi


def tree_rules(lab, gens, box):
    """apply the D-condition to the tree bounds on the leaf's 48-box.
    -> ('dead', i, rule) | list of ('lo'|'hi', t, value) tightenings (t = index in gens) | None
    rules: MIX i needs D_i = 0; label 1 needs D_i >= 0; label 0 needs D_i <= 0;
    DC i: x_i > 0 on the box needs D_i >= 0, x_i < 1 needs D_i <= 0, and
    D_i > 0 forces x_i = 1, D_i < 0 forces x_i = 0."""
    lo, hi = box48(lab, gens, box)
    DLO, DHI = d_bounds(lo, hi)
    pos = {g: t for t, g in enumerate(gens)}
    tight = []
    for i in range(K.NPARAM):
        l = lab[i]
        if l == 2:                                          # MIX
            if DLO[i] > 0 or DHI[i] < 0: return ("dead", i, "mix")
        elif l == 1:
            if DHI[i] < 0: return ("dead", i, "one")
        elif l == 0:
            if DLO[i] > 0: return ("dead", i, "zero")
        elif l == 3 and i in pos:                            # DC with a box variable
            t = pos[i]
            if lo[i] > 0 and DHI[i] < 0: return ("dead", i, "dc>0")
            if hi[i] < 1 and DLO[i] > 0: return ("dead", i, "dc<1")
            if DLO[i] > 0 and lo[i] < 1: tight.append(("lo", t, F(1)))
            if DHI[i] < 0 and hi[i] > 0: tight.append(("hi", t, F(0)))
    return tight or None


def _need(lab, lo, hi):
    ge = [False] * K.NPARAM; le = [False] * K.NPARAM
    for i in range(K.NPARAM):
        l = lab[i]
        if l == 2: ge[i] = le[i] = True
        elif l == 1: ge[i] = True
        elif l == 0: le[i] = True
        elif l == 3:
            if lo[i] > 0: ge[i] = True
            if hi[i] < 1: le[i] = True
    return ge, le


def chord_contract(lab, gens, box, floor=None, ceil=None):
    """One round of the exact CHORD contractor on the leaf's 48-box (bnb6's
    argument in rational arithmetic).  For a free variable v = gens[t] of
    positive width, pin x_v at its lower and upper end and take the tree
    bounds U(0), U(1) (upper) / L(0), L(1) (lower) on every D_i.  The true
    maximum of D_i over the box with x_v = lo + t w is CONVEX in t (D_i is
    affine in x_v, a maximum of affine functions is convex), so it lies below
    the chord (1-t) U(0) + t U(1); where the chord is negative a condition
    D_i >= 0 is impossible.  Symmetrically the minimum is concave, above the
    chord of L.  -> (steps, slopes): steps ('clo'|'chi', t, value, i) applied
    to box, or [('cdead', t, i, 'ge'|'le')]; slopes[t] = max_i |U1-U0| or
    |L1-L0| over active conditions, for the split choice."""
    lo, hi = box48(lab, gens, box)
    ge, le = _need(lab, lo, hi)
    steps = []; slopes = [F(0)] * len(gens)
    for t, v in enumerate(gens):
        w = hi[v] - lo[v]
        if w <= 0: continue
        l0 = list(lo); h0 = list(hi); h0[v] = lo[v]
        L0, U0 = d_bounds(l0, h0)
        l1 = list(lo); h1 = list(hi); l1[v] = hi[v]
        L1, U1 = d_bounds(l1, h1)
        tlo = F(0); thi = F(1)
        for i in range(K.NPARAM):
            if i == v: continue
            if ge[i]:
                slopes[t] = max(slopes[t], abs(U1[i] - U0[i]))
                if U0[i] < 0 and U1[i] < 0: return steps + [("cdead", t, i, "ge")], slopes
                if U0[i] < 0 <= U1[i]: tlo = max(tlo, -U0[i] / (U1[i] - U0[i]))
                if U1[i] < 0 <= U0[i]: thi = min(thi, U0[i] / (U0[i] - U1[i]))
            if le[i]:
                slopes[t] = max(slopes[t], abs(L1[i] - L0[i]))
                if L0[i] > 0 and L1[i] > 0: return steps + [("cdead", t, i, "le")], slopes
                if L0[i] > 0 >= L1[i]: tlo = max(tlo, L0[i] / (L0[i] - L1[i]))
                if L1[i] > 0 >= L0[i]: thi = min(thi, -L0[i] / (L1[i] - L0[i]))
        if tlo > thi: return steps + [("cdead", t, -1, "cross")], slopes
        nlo = lo[v] + w * tlo; nhi = lo[v] + w * thi
        if floor is not None: nlo = floor(nlo); nhi = ceil(nhi)
        # both bounds come from the SAME pinned evaluation, so they are one step:
        # a checker that applied one and re-derived the other would see a
        # different chord (2026-09-21, leaf 928 of b_0_M_0_1R)
        ch = False
        if nlo > box[t][0]:
            box[t][0] = nlo; box[t][2] = False; lo[v] = nlo; ch = True
        if nhi < box[t][1]:
            box[t][1] = nhi; box[t][3] = False; hi[v] = nhi; ch = True
        if ch: steps.append(("chord", t, box[t][0], box[t][1]))
        if lo[v] > hi[v]: return steps + [("cdead", t, -1, "empty")], slopes
    return steps, slopes
