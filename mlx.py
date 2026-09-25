"""EXACT interval bounds and contractors for the 27 first-order Nash conditions
on the Table-2-reduced game (27 free coordinates), vectorised over boxes.

Every du_i is MULTILINEAR in the free coordinates (verified: no variable has
degree > 1 in any of the 27 polynomials).  A multilinear function attains its
min and max over a box at a vertex, so the exact range over a box is the min/max
of its 2^k vertex values, k = number of variables du_i depends on (4..14).

Vertex values are computed in O(k 2^k) per box per condition:
   1. affine substitution x_v = lo_v + w_v t_v   (t_v in {0,1})
      -- per variable, one pass over the 2^k coefficient table;
   2. zeta transform  V[T] = sum_{S subset T} c'[S]  -- k passes.

The same table gives, for every variable v of the condition, the value at
t_v = 0 (A) and the slope in t_v (B = V[t_v=1] - V[t_v=0]) at every vertex of
the other variables, hence sound ranges [A_lo,A_hi], [B_lo,B_hi] and a
HULL-CONSISTENCY contractor: the set of t_v in [0,1] for which the condition
du_i >= 0 (or <= 0) is still satisfiable, given only those ranges.

Semantics are bnb5's:  LO_i > 0 => du_i >= 0 ;  HI_i < 1 => du_i <= 0.

Numerical soundness: every kill compares against TOL, every narrowing is pushed
outward by TOL, so floating-point error of the order of 1e-15 per operation on
values of order 1 cannot flip a decision.
"""
import numpy as np, sympy as sp
import symbet, kuhn3p as K

I = K.NAME_IDX
TOL = 1e-12

_IDX = {}
def _bitidx(k):
    """for each bit b < k: (S1, S0) index arrays: masks with bit b set / cleared."""
    if k not in _IDX:
        out = []
        for b in range(k):
            S1 = np.array([m for m in range(1 << k) if m >> b & 1], dtype=np.int64)
            out.append((S1, S1 ^ (1 << b)))
        _IDX[k] = out
    return _IDX[k]


class Cond:
    __slots__ = ("name", "own", "vars", "k", "coef", "bits")
    def __init__(self, name, own, vars_, coef):
        self.name, self.own, self.vars, self.coef = name, own, np.array(vars_, dtype=np.int64), coef
        self.k = len(vars_)
        self.bits = _bitidx(self.k)

    def vertex_values(self, LO, HI):
        """(B, 2^k) exact values of du at every vertex of the boxes.  Vertex mask T:
        bit b set  <->  variable vars[b] at HI, else at LO."""
        B = LO.shape[0]
        lo = LO[:, self.vars]; w = HI[:, self.vars] - lo
        c = np.broadcast_to(self.coef, (B, 1 << self.k)).copy()
        for b, (S1, S0) in enumerate(self.bits):          # x_b = lo_b + w_b t_b
            c[:, S0] += c[:, S1] * lo[:, b:b+1]
            c[:, S1] *= w[:, b:b+1]
        for b, (S1, S0) in enumerate(self.bits):          # zeta transform
            c[:, S1] += c[:, S0]
        return c


def build():
    """-> vars_ (27 names in canonical order), pos, conds (27 Cond, index = position of owner var)."""
    X, syms = symbet.table2_only()
    G, U = symbet.build(X)
    vars_ = sorted(syms)
    order = [syms[v] for v in vars_]
    pos = {v: k for k, v in enumerate(vars_)}
    conds = []
    for v in vars_:
        e = sp.expand(G[I[v]])
        poly = sp.Poly(e, *order)
        deps = sorted({k for mon, _ in poly.terms() for k, ex in enumerate(mon) if ex})
        loc = {g: b for b, g in enumerate(deps)}
        coef = np.zeros(1 << len(deps))
        for mon, c in poly.terms():
            m = 0
            for k, ex in enumerate(mon):
                assert ex <= 1, "not multilinear"
                if ex: m |= 1 << loc[k]
            coef[m] += float(c)
        conds.append(Cond(v, pos[v], deps, coef))
    return vars_, pos, conds


def bounds(conds, LO, HI):
    """exact (B, n) lower/upper bounds on every du_i over each box."""
    B, n = LO.shape
    DLO = np.zeros((B, n)); DHI = np.zeros((B, n))
    for c in conds:
        V = c.vertex_values(LO, HI)
        DLO[:, c.own] = V.min(axis=1); DHI[:, c.own] = V.max(axis=1)
    return DLO, DHI


def propagate(conds, LO, HI, rounds=8, contract=True, hyp_ge=None, hyp_le=None):
    """Kill / force / contract to a fixpoint (or `rounds`).
    hyp_ge, hyp_le : optional bool (n,) or (B, n) -- conditions du_i >= 0 / <= 0
             imposed BY HYPOTHESIS regardless of the box.  Uses: the open-interval
             claim a_j1 > 0 (hyp_ge on a_j1), and support-pattern semantics
             (MIX coordinate: both, i.e. du_i = 0 on the whole [0,1] box).
    returns LO, HI, alive, DLO, DHI, SL (per-(cond,var) slope magnitude, for splitting)."""
    B, n = LO.shape
    LO = LO.copy(); HI = HI.copy()
    alive = np.ones(B, bool)
    SL = np.zeros((B, n, n))            # SL[b, i, v] = max |slope of du_i in t_v| on box b
    DLO = np.zeros((B, n)); DHI = np.zeros((B, n))
    HG = None if hyp_ge is None else np.broadcast_to(np.asarray(hyp_ge, bool), (B, n))
    HL = None if hyp_le is None else np.broadcast_to(np.asarray(hyp_le, bool), (B, n))
    for r in range(rounds):
        changed = False
        for c in conds:
            i = c.own
            V = c.vertex_values(LO, HI)
            mn = V.min(axis=1); mx = V.max(axis=1)
            DLO[:, i] = mn; DHI[:, i] = mx
            need_ge = LO[:, i] > 0.0
            need_le = HI[:, i] < 1.0
            if HG is not None: need_ge = need_ge | HG[:, i]
            if HL is not None: need_le = need_le | HL[:, i]
            dead = (need_ge & (mx < -TOL)) | (need_le & (mn > TOL))
            alive &= ~dead
            # forcing: du_i provably > 0 -> x_i = 1 ; provably < 0 -> x_i = 0
            f1 = mn > TOL; f0 = mx < -TOL
            alive &= ~((f1 & (HI[:, i] < 1.0)) | (f0 & (LO[:, i] > 0.0)))
            if f1.any(): LO[f1, i] = 1.0; changed = True
            if f0.any(): HI[f0, i] = 0.0; changed = True
            if not contract:
                continue
            act = (need_ge | need_le) & alive
            for b, (S1, S0) in enumerate(c.bits):
                A = V[:, S0]; Bs = V[:, S1] - A
                Alo = A.min(1); Ahi = A.max(1); Blo = Bs.min(1); Bhi = Bs.max(1)
                v = c.vars[b]
                SL[:, i, v] = np.maximum(np.abs(Blo), np.abs(Bhi))
                lo = LO[:, v]; w = HI[:, v] - lo
                ok = act & (w > 0.0)
                if not ok.any(): continue
                tlo = np.zeros(B); thi = np.ones(B)
                # du >= 0 satisfiable at t  <=  Ahi + Bhi t >= 0
                g = ok & need_ge
                m = g & (Bhi > TOL) & (Ahi < -TOL)          # t >= -Ahi/Bhi
                tlo[m] = np.maximum(tlo[m], (-Ahi[m] / Bhi[m]) - TOL)
                m = g & (Bhi < -TOL) & (Ahi >= -TOL)        # t <= Ahi/(-Bhi)
                thi[m] = np.minimum(thi[m], (Ahi[m] / (-Bhi[m])) + TOL)
                # du <= 0 satisfiable at t  <=  Alo + Blo t <= 0
                g = ok & need_le
                m = g & (Blo < -TOL) & (Alo > TOL)          # t >= Alo/(-Blo)
                tlo[m] = np.maximum(tlo[m], (Alo[m] / (-Blo[m])) - TOL)
                m = g & (Blo > TOL) & (Alo <= TOL)          # t <= -Alo/Blo
                thi[m] = np.minimum(thi[m], (-Alo[m] / Blo[m]) + TOL)
                tlo = np.clip(tlo, 0.0, 1.0); thi = np.clip(thi, 0.0, 1.0)
                emp = ok & (tlo > thi + TOL)
                alive &= ~emp
                nlo = lo + w * tlo; nhi = lo + w * thi
                upd = ok & ((nlo > LO[:, v] + TOL) | (nhi < HI[:, v] - TOL))
                if upd.any():
                    LO[upd, v] = np.maximum(LO[upd, v], nlo[upd])
                    HI[upd, v] = np.minimum(HI[upd, v], nhi[upd])
                    changed = True
        if not alive.any() or not changed:
            break
    return LO, HI, alive, DLO, DHI, SL
