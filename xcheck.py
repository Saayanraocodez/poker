"""INDEPENDENT checker of exact propagation certificates (option 2, 2026-10-05).

Written separately from the prover (xprop.py): it imports only the game definition (tree.py) and
Fractions -- not ivl, bnb6, treesize6 or xprop -- and evaluates the interval bounds with its own
recursion over an explicit per-deal game tree.  A certificate is a list of steps; each step is
verified on the box as it stands at that step, with exact rational comparisons only.

THE BOUNDS.  For a box of strategy intervals, per deal, by recursion from the leaves:
  value interval of a decision node with action probability x in [xl, xh]:
      V = (1 - x) P + x A is increasing in A and P, affine in x, so
      Vhi = max over x in {xl, xh} of (1 - x) Phi + x Ahi,  Vlo likewise with Plo, Alo and min;
  reach interval: products of [xl, xh] (aggressive edge) and [1 - xh, 1 - xl] (passive edge);
  at a node of coordinate i owned by player o: D = V_A - V_P for player o lies in
      [Dl, Dh] = [Alo_o - Phi_o, Ahi_o - Plo_o], and reach * D in [f_lo, f_hi] with
      f_hi = rh * Dh if Dh >= 0 else rl * Dh,   f_lo = rl * Dl if Dl >= 0 else rh * Dl;
  24 * du_i lies in [sum f_lo, sum f_hi] over the 6 nodes of i (the 1/24 deal weight is dropped:
  only signs are used).  DMIN_i / DMAX_i = min Dl / max Dh over the 6 nodes; RH_i = sum rh.

THE STEPS (each a necessary condition for every Nash equilibrium in the box with the node's
labels, so no equilibrium is ever discarded):
  hypotheses at the current box: NG_i = lo_i > 0 or label MIX  (then du_i >= 0),
                                 NL_i = hi_i < 1 or label MIX  (then du_i <= 0);
  ["F", [[i, 1|0], ...]]  du_i > 0 on the box (or, at an information set the labels prove reached,
                          DMIN_i > 0) forces x_i = 1; symmetric for 0.  Needs hi_i = 1 (lo_i = 0);
  ["C", v, [[side, i, value], ...]]  chord: pin x_v at lo_v and at hi_v; with U_i(t) the pinned
                          upper bound at x_v = lo_v + w t, U_i is convex in t (lemma, MASTER_DATA),
                          so if NG_i and U_i(0) < 0 <= U_i(1), du_i >= 0 is impossible for
                          t < t_c = -U_i(0) / (U_i(1) - U_i(0)): a new lo_v <= lo_v + w t_c is
                          valid.  Symmetric (concave lower bound) for NL_i, and for the hi side;
  ["K", ...]              the contradiction: ge/le (a hypothesis against the bound), f1/f0 (a force
                          against the box), cge/cle (both pins on the wrong side: convexity), cx
                          (the narrowed lo above the narrowed hi), mix (a MIX coordinate whose box
                          has no interior).
"""
from fractions import Fraction as F
import tree as T

U, MIX, DC = 9, 2, 3


class Bad(Exception):
    pass


def need(c, msg):
    if not c: raise Bad(msg)


def fr(s):
    return F(s)


# ---- the game, per deal, as an explicit tree -----------------------------------------------
def _build():
    deals = []
    for d in range(T.ND):
        def node(p):
            if int(T.AGGC[p]) < 0:
                return ("leaf", tuple(int(T.PAYT[d, p, k]) for k in range(3)))
            return ("dec", int(T.COORD[d, p]), T.OWNER[p][0], node(int(T.AGGC[p])), node(int(T.PASC[p])))
        deals.append(node(0))
    return deals
DEALS = _build()


def _val(n, lo, hi, memo):
    """(Vlo, Vhi) per player at node n"""
    if n[0] == "leaf": return n[1], n[1]
    key = id(n)
    if key in memo: return memo[key]
    _, c, o, a, p = n
    alo, ahi = _val(a, lo, hi, memo); plo, phi = _val(p, lo, hi, memo)
    xl, xh = lo[c], hi[c]
    vlo = tuple(min((1 - xl) * plo[k] + xl * alo[k], (1 - xh) * plo[k] + xh * alo[k]) for k in range(3))
    vhi = tuple(max((1 - xl) * phi[k] + xl * ahi[k], (1 - xh) * phi[k] + xh * ahi[k]) for k in range(3))
    memo[key] = (vlo, vhi)
    return vlo, vhi


def bounds(lo, hi):
    """-> SL, SH (sums of reach * D over each coordinate's 6 nodes), RH, DMIN, DMAX"""
    SL = [F(0)] * 48; SH = [F(0)] * 48; RH = [F(0)] * 48; DMIN = [None] * 48; DMAX = [None] * 48
    for root in DEALS:
        memo = {}
        stack = [(root, F(1), F(1))]
        while stack:
            n, rl, rh = stack.pop()
            if n[0] == "leaf": continue
            _, c, o, a, p = n
            alo, ahi = _val(a, lo, hi, memo); plo, phi = _val(p, lo, hi, memo)
            Dl = alo[o] - phi[o]; Dh = ahi[o] - plo[o]
            SL[c] += (rl * Dl) if Dl >= 0 else (rh * Dl)
            SH[c] += (rh * Dh) if Dh >= 0 else (rl * Dh)
            RH[c] += rh
            DMIN[c] = Dl if DMIN[c] is None else min(DMIN[c], Dl)
            DMAX[c] = Dh if DMAX[c] is None else max(DMAX[c], Dh)
            xl, xh = lo[c], hi[c]
            stack.append((a, rl * xl, rh * xh))
            stack.append((p, rl * (1 - xh), rh * (1 - xl)))
    return SL, SH, RH, DMIN, DMAX


# ---- information sets the labels prove reached ----------------------------------------------
def reached(lab):
    """coordinate i is reached with positive probability in every profile of the label cell:
    some node of i has a path whose aggressive edges are labelled 1 / MIX and passive edges 0 / MIX"""
    out = [False] * 48
    for root in DEALS:
        stack = [(root, True)]
        while stack:
            n, ok = stack.pop()
            if n[0] == "leaf": continue
            _, c, o, a, p = n
            if ok: out[c] = True
            stack.append((a, ok and lab[c] in (1, MIX)))
            stack.append((p, ok and lab[c] in (0, MIX)))
    return out


# ---- step verification -----------------------------------------------------------------------
def _pins(lo, hi, v):
    L = list(lo); H = list(hi); L[v] = H[v] = lo[v]; b0 = bounds(L, H)
    L = list(lo); H = list(hi); L[v] = H[v] = hi[v]; b1 = bounds(L, H)
    return b0[0], b0[1], b1[0], b1[1]                    # L0, U0, L1, U1


def _tlo(i, ng, nl, L0, U0, L1, U1):
    """the largest t the lo side may move to for condition i (None if it gives none)"""
    ts = []
    if ng[i] and U0[i] < 0 <= U1[i]: ts.append(-U0[i] / (U1[i] - U0[i]))
    if nl[i] and L0[i] > 0 >= L1[i]: ts.append(L0[i] / (L0[i] - L1[i]))
    return max(ts) if ts else None


def _thi(i, ng, nl, L0, U0, L1, U1):
    ts = []
    if ng[i] and U1[i] < 0 <= U0[i]: ts.append(U0[i] / (U0[i] - U1[i]))
    if nl[i] and L1[i] > 0 >= L0[i]: ts.append(-L0[i] / (L1[i] - L0[i]))
    return min(ts) if ts else None


def replay(lab, lo, hi, steps):
    """verify a propagation certificate for labels `lab` from the box (lo, hi).
    -> (lo, hi, alive).  Raises Bad on any step that does not follow."""
    lo = list(lo); hi = list(hi)
    mix = [lab[i] == MIX for i in range(48)]
    wk = reached(lab)
    for k, st in enumerate(steps):
        need(isinstance(st, list) and st, "malformed step")
        ng = [lo[i] > 0 or mix[i] for i in range(48)]; nl = [hi[i] < 1 or mix[i] for i in range(48)]
        if st[0] == "F":
            SL, SH, RH, DMIN, DMAX = bounds(lo, hi)
            for i, val in st[1]:
                if val == 1:
                    need(SL[i] > 0 or (wk[i] and DMIN[i] > 0), "force to 1 of %d does not follow" % i)
                    need(hi[i] == 1, "force to 1 of %d against hi < 1" % i)
                    lo[i] = F(1)
                else:
                    need(SH[i] < 0 or (wk[i] and DMAX[i] < 0), "force to 0 of %d does not follow" % i)
                    need(lo[i] == 0, "force to 0 of %d against lo > 0" % i)
                    hi[i] = F(0)
        elif st[0] == "C":
            v = st[1]; L0, U0, L1, U1 = _pins(lo, hi, v); w = hi[v] - lo[v]
            nlo, nhi = lo[v], hi[v]
            for side, i, val in st[2]:
                val = fr(val); need(i != v, "a chord on its own condition")
                if side == "lo":
                    t = _tlo(i, ng, nl, L0, U0, L1, U1)
                    need(t is not None and lo[v] <= val <= lo[v] + w * t, "chord lo of %d by %d does not follow" % (v, i))
                    nlo = max(nlo, val)
                else:
                    t = _thi(i, ng, nl, L0, U0, L1, U1)
                    need(t is not None and lo[v] + w * t <= val <= hi[v], "chord hi of %d by %d does not follow" % (v, i))
                    nhi = min(nhi, val)
            need(nlo <= nhi, "a chord step empties the box -- it must be a kill")
            lo[v], hi[v] = nlo, nhi
        elif st[0] == "K":
            need(k == len(steps) - 1, "steps after a kill")
            r = st[1]
            if r in ("ge", "le", "f1", "f0"):
                i = st[2]; SL, SH, RH, DMIN, DMAX = bounds(lo, hi)
                if r == "ge": need(ng[i] and SH[i] < 0, "kill ge %d does not follow" % i)
                elif r == "le": need(nl[i] and SL[i] > 0, "kill le %d does not follow" % i)
                elif r == "f1": need((SL[i] > 0 or (wk[i] and DMIN[i] > 0)) and hi[i] < 1, "kill f1 %d does not follow" % i)
                else: need((SH[i] < 0 or (wk[i] and DMAX[i] < 0)) and lo[i] > 0, "kill f0 %d does not follow" % i)
            elif r in ("cge", "cle"):
                v, i = st[2], st[3]; need(i != v, "a chord on its own condition")
                L0, U0, L1, U1 = _pins(lo, hi, v)
                if r == "cge": need(ng[i] and U0[i] < 0 and U1[i] < 0, "kill cge does not follow")
                else: need(nl[i] and L0[i] > 0 and L1[i] > 0, "kill cle does not follow")
            elif r == "cx":
                v, i, j = st[2], st[3], st[4]; need(i != v and j != v, "a chord on its own condition")
                L0, U0, L1, U1 = _pins(lo, hi, v)
                a = _tlo(i, ng, nl, L0, U0, L1, U1); b = _thi(j, ng, nl, L0, U0, L1, U1)
                need(a is not None and b is not None and a > b, "kill cx does not follow")
            elif r == "mix":
                i = st[2]; need(mix[i] and (lo[i] >= 1 or hi[i] <= 0), "kill mix does not follow")
            else:
                need(False, "unknown kill")
            return lo, hi, False
        else:
            need(False, "unknown step %r" % (st[0],))
    return lo, hi, True


def implied_labels(lab, lo, hi):
    """labels a box implies on unassigned coordinates (lo >= 1 -> 1, hi <= 0 -> 0)"""
    lab = list(lab)
    for i in range(48):
        if lab[i] == U:
            if lo[i] >= 1: lab[i] = 1
            elif hi[i] <= 0: lab[i] = 0
    return lab


def excluded(lo, hi, v, l):
    """label l of coordinate v is impossible in the box"""
    return (l == 0 and lo[v] > 0) or (l == 1 and hi[v] < 1) or (l == MIX and not (hi[v] > 0 and lo[v] < 1))
