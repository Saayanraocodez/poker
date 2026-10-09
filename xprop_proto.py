"""PROTOTYPE (feasibility only): bnb6.propagate in exact rational arithmetic, one box at a time.
Measures the cost of an exact propagation and whether it reproduces the float kills.
Box endpoints are kept dyadic: a contracted endpoint is rounded OUTWARD to the grid 2^-GRID
(a weaker bound, so still sound); everything else is exact."""
import numpy as np, os
from fractions import Fraction as F
import tree as T

ND, NPOS = T.ND, T.NPOS
INT = [int(p) for p in T.INTERNAL]
LEAF = [int(p) for p in T.LEAFPOS]
AGGC = [int(x) for x in T.AGGC]; PASC = [int(x) for x in T.PASC]
COORD = [[int(T.COORD[d, p]) for p in range(NPOS)] for d in range(ND)]
PAY = [[[int(T.PAYT[d, p, k]) for k in range(3)] for p in range(NPOS)] for d in range(ND)]
OWNER = {int(p): T.OWNER[int(p)][0] for p in INT}
NODES = [[] for _ in range(48)]                 # (deal, position) of each coordinate's 6 nodes
for d in range(ND):
    for p in INT: NODES[COORD[d][p]].append((d, p))
GRID = 60
ZERO, ONE = F(0), F(1)


def bounds(lo, hi):
    """exact interval bounds over the box: -> DLO, DHI (x24), RH, DMIN, DMAX (lists of 48)"""
    Vlo = {}; Vhi = {}
    for d in range(ND):
        for p in LEAF: Vlo[d, p] = Vhi[d, p] = PAY[d][p]
        for p in reversed(INT):
            c = COORD[d][p]; xl, xh = lo[c], hi[c]
            al, ah = Vlo[d, AGGC[p]], Vhi[d, AGGC[p]]; pl, ph = Vlo[d, PASC[p]], Vhi[d, PASC[p]]
            vl = []; vh = []
            for k in range(3):
                dl = al[k] - pl[k]; dh = ah[k] - ph[k]
                vl.append(min(pl[k] + xl * dl, pl[k] + xh * dl)); vh.append(max(ph[k] + xl * dh, ph[k] + xh * dh))
            Vlo[d, p] = vl; Vhi[d, p] = vh
    Rlo = {}; Rhi = {}
    for d in range(ND):
        Rlo[d, 0] = Rhi[d, 0] = ONE
        for p in INT:
            c = COORD[d][p]; xl, xh = lo[c], hi[c]
            Rlo[d, AGGC[p]] = Rlo[d, p] * xl; Rhi[d, AGGC[p]] = Rhi[d, p] * xh
            Rlo[d, PASC[p]] = Rlo[d, p] * (1 - xh); Rhi[d, PASC[p]] = Rhi[d, p] * (1 - xl)
    DLO = [ZERO] * 48; DHI = [ZERO] * 48; RH = [ZERO] * 48; DMIN = [None] * 48; DMAX = [None] * 48
    for i in range(48):
        for d, p in NODES[i]:
            o = OWNER[p]
            Dl = Vlo[d, AGGC[p]][o] - Vhi[d, PASC[p]][o]; Dh = Vhi[d, AGGC[p]][o] - Vlo[d, PASC[p]][o]
            rl, rh = Rlo[d, p], Rhi[d, p]
            DLO[i] += rl * Dl if Dl >= 0 else rh * Dl
            DHI[i] += rh * Dh if Dh >= 0 else rl * Dh
            RH[i] += rh
            DMIN[i] = Dl if DMIN[i] is None else min(DMIN[i], Dl)
            DMAX[i] = Dh if DMAX[i] is None else max(DMAX[i], Dh)
    return DLO, DHI, RH, DMIN, DMAX


def _down(q):
    return F((q.numerator << GRID) // q.denominator, 1 << GRID)


def _up(q):
    return F(-((-q.numerator << GRID) // q.denominator), 1 << GRID)


import bnb6
DEPS = [set(int(v) for v in np.flatnonzero(bnb6.DEPM[:, v])) for v in range(48)]   # conditions that depend on v


def propagate(lo, hi, hg, hl, wk, rounds=8):
    """exact bnb6.propagate for one box. hg/hl: hypothesis masks (MIX), wk: weak-rule mask (or None).
    -> lo, hi, alive, n_bounds_calls"""
    lo = list(lo); hi = list(hi); calls = 0
    for _ in range(rounds):
        DLO, DHI, RH, DMIN, DMAX = bounds(lo, hi); calls += 1
        ng = [lo[i] > 0 or hg[i] for i in range(48)]; nl = [hi[i] < 1 or hl[i] for i in range(48)]
        if any((ng[i] and DHI[i] < 0) or (nl[i] and DLO[i] > 0) for i in range(48)): return lo, hi, False, calls
        f1 = [DLO[i] > 0 or (wk is not None and wk[i] and DMIN[i] > 0) for i in range(48)]
        f0 = [DHI[i] < 0 or (wk is not None and wk[i] and DMAX[i] < 0) for i in range(48)]
        if any((f1[i] and hi[i] < 1) or (f0[i] and lo[i] > 0) for i in range(48)): return lo, hi, False, calls
        nlo = [ONE if f1[i] else lo[i] for i in range(48)]; nhi = [ZERO if f0[i] else hi[i] for i in range(48)]
        changed = nlo != lo or nhi != hi
        lo, hi = nlo, nhi
        ng = [lo[i] > 0 or hg[i] for i in range(48)]; nl = [hi[i] < 1 or hl[i] for i in range(48)]
        act = [(ng[i] and DLO[i] < 0) or (nl[i] and DHI[i] > 0) for i in range(48)]     # conditions with slack
        cols = [v for v in range(48) if hi[v] > lo[v] and any(act[i] for i in DEPS[v])]
        for v in cols:
            pins = []
            for val in (lo[v], hi[v]):
                L = list(lo); H = list(hi); L[v] = H[v] = val
                r = bounds(L, H); calls += 1; pins.append((r[0], r[1]))
            (l0, u0), (l1, u1) = pins
            tlo, thi = ZERO, ONE
            for i in DEPS[v]:
                if ng[i]:
                    if u0[i] < 0 <= u1[i]: tlo = max(tlo, -u0[i] / (u1[i] - u0[i]))
                    if u1[i] < 0 <= u0[i]: thi = min(thi, u0[i] / (u0[i] - u1[i]))
                    if u0[i] < 0 and u1[i] < 0: return lo, hi, False, calls
                if nl[i]:
                    if l0[i] > 0 >= l1[i]: tlo = max(tlo, l0[i] / (l0[i] - l1[i]))
                    if l1[i] > 0 >= l0[i]: thi = min(thi, -l0[i] / (l1[i] - l0[i]))
                    if l0[i] > 0 and l1[i] > 0: return lo, hi, False, calls
            if tlo > thi: return lo, hi, False, calls
            w = hi[v] - lo[v]
            nl_ = _down(lo[v] + w * tlo); nh_ = _up(lo[v] + w * thi)
            nl_ = max(nl_, lo[v]); nh_ = min(nh_, hi[v])
            if nl_ > lo[v] or nh_ < hi[v]:
                lo[v], hi[v] = nl_, nh_; changed = True
        if not changed: break
    return lo, hi, True, calls
