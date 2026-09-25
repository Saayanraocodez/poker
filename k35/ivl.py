"""Rigorous interval propagation over the game tree, vectorised over a batch of
partial support assignments.  Gives outer bounds on du_owner/dx for all 48
coordinates, plus reach upper bounds (for detecting don't-care coordinates).

DIRECTED ROUNDING (2026-09-20).  Every floating-point operation is followed by
an outward rounding step, so every bound returned is a true bound on the real
quantity -- not "up to ~1e-13 of accumulated rounding".  The argument: numpy's
+, -, *, / are IEEE-754 correctly rounded to nearest, and if a real r rounds
to the double f then pred(f) <= r <= succ(f) (a neighbour of f nearer to r
would contradict f being nearest), so nextafter(f, -inf) is a lower bound on r
and nextafter(f, +inf) an upper bound.  Exact zeros are preserved: a sum that
rounds to 0 is exactly 0; a product / quotient that rounds to 0 is exactly 0
unless it underflowed, which is detected (both factors nonzero) and raised
rather than rounded -- it cannot happen with box endpoints of the sizes the
enumeration produces (every nonzero width is >= TOL = 1e-11), but the check
makes the claim unconditional.  Zero preservation matters for the reach upper
bound (RH == 0 marks a coordinate don't-care) and costs nothing else.

KUHN_ROUND=nearest restores the old plain-float arithmetic (comparison only)."""
import numpy as np, os
import tree as T

ND, NPOS, KAP = T.ND, T.NPOS, T.KAP
INT = list(T.INTERNAL)          # 12 internal positions, parents first
LEAF = list(T.LEAFPOS)
AGGC, PASC, COORD, PAYT = T.AGGC, T.PASC, T.COORD, T.PAYT
OWNER_PL = np.array([T.OWNER[p][0] for p in INT])          # (12,)
DIRECTED = os.environ.get("KUHN_ROUND", "directed") != "nearest"
assert KAP == 1.0 / ND                                     # the scale below divides by the exact integer 24

# scatter matrix: (12*24, 48) one-hot on the coordinate each (pos,deal) touches
import kuhn3p as K
NP = K.NPARAM; NPC = len(INT) * ND // NP           # nodes per coordinate
S = np.zeros((len(INT) * ND, NP))
for a, pos in enumerate(INT):
    for d in range(ND):
        S[a * ND + d, COORD[d, pos]] = 1.0

NODES_OF = np.zeros((NP, NPC), dtype=np.int64)
_cnt = np.zeros(NP, dtype=np.int64)
for a, pos in enumerate(INT):
    for d in range(ND):
        t = COORD[d, pos]
        NODES_OF[t, _cnt[t]] = a * ND + d
        _cnt[t] += 1
assert (_cnt == NPC).all()

# ------------------------------------------------------------ directed rounding
_NEG = -np.inf; _POS = np.inf


class Underflow(ArithmeticError):
    pass


def _dn(x):
    """lower bound on the real result of an exact-zero-preserving operation that produced x"""
    y = np.nextafter(x, _NEG); y[x == 0] = 0.0; return y


def _up(x):
    y = np.nextafter(x, _POS); y[x == 0] = 0.0; return y


def _mulchk(p, a, b):
    z = p == 0
    if z.any() and ((a != 0) & (b != 0) & z).any():
        raise Underflow("product underflowed to zero")
    return z


def add_dn(a, b): return _dn(np.add(a, b))
def add_up(a, b): return _up(np.add(a, b))
def sub_dn(a, b): return _dn(np.subtract(a, b))
def sub_up(a, b): return _up(np.subtract(a, b))


def mul_dn(a, b):
    p = np.multiply(a, b); z = _mulchk(p, a, b)
    y = np.nextafter(p, _NEG); y[z] = 0.0; return y


def mul_up(a, b):
    p = np.multiply(a, b); z = _mulchk(p, a, b)
    y = np.nextafter(p, _POS); y[z] = 0.0; return y


def div_dn(a, b):
    q = np.divide(a, b); z = _mulchk(q, a, np.ones_like(q))
    y = np.nextafter(q, _NEG); y[z] = 0.0; return y


def div_up(a, b):
    q = np.divide(a, b); z = _mulchk(q, a, np.ones_like(q))
    y = np.nextafter(q, _POS); y[z] = 0.0; return y


def _sum6_dn(x):
    """x : (B, 12*24) per-node values -> (B, NP) sum over the 6 nodes of each coordinate, rounded down"""
    g = x[:, NODES_OF]; s = g[:, :, 0].copy()
    for k in range(1, NPC): s = add_dn(s, g[:, :, k])
    return s


def _sum6_up(x):
    g = x[:, NODES_OF]; s = g[:, :, 0].copy()
    for k in range(1, NPC): s = add_up(s, g[:, :, k])
    return s


def bounds(LO, HI):
    """LO,HI : (B,NP) coordinate interval bounds.
    returns DLO,DHI : (B,NP) outer bounds on du_owner/dx ; RHI : (B,NP) reach UB;
            DMIN,DMAX : (B,NP) bounds on the per-node continuation difference (min / max over the 6 nodes)."""
    if not DIRECTED:
        return _bounds_nearest(LO, HI)
    B = LO.shape[0]
    LO = np.asarray(LO, float); HI = np.asarray(HI, float)
    Vlo = [None] * NPOS; Vhi = [None] * NPOS
    for pos in LEAF:
        Vlo[pos] = np.broadcast_to(PAYT[:, pos], (B, ND, 3))
        Vhi[pos] = Vlo[pos]
    for pos in INT[::-1]:
        c = COORD[:, pos]                       # (24,)
        xl = LO[:, c][:, :, None]; xh = HI[:, c][:, :, None]
        al, ah = Vlo[AGGC[pos]], Vhi[AGGC[pos]]
        pl, ph = Vlo[PASC[pos]], Vhi[PASC[pos]]
        # V = P + x (A - P) = (1 - x) P + x A: increasing in A and P for fixed
        # x in [0, 1], affine in x -> extremes at (al, pl) / (ah, ph) and at
        # the endpoints of x.  x >= 0, so a lower bound on A - P gives one on V.
        dl = sub_dn(al, pl); dh = sub_up(ah, ph)
        Vlo[pos] = np.minimum(add_dn(pl, mul_dn(xl, dl)), add_dn(pl, mul_dn(xh, dl)))
        Vhi[pos] = np.maximum(add_up(ph, mul_up(xl, dh)), add_up(ph, mul_up(xh, dh)))
    Rlo = np.zeros((B, ND, NPOS)); Rhi = np.zeros((B, ND, NPOS))
    Rlo[:, :, 0] = 1.0; Rhi[:, :, 0] = 1.0
    for pos in INT:
        c = COORD[:, pos]
        xl = LO[:, c]; xh = HI[:, c]
        Rlo[:, :, AGGC[pos]] = mul_dn(Rlo[:, :, pos], xl)
        Rhi[:, :, AGGC[pos]] = mul_up(Rhi[:, :, pos], xh)
        Rlo[:, :, PASC[pos]] = mul_dn(Rlo[:, :, pos], sub_dn(1.0, xh))
        Rhi[:, :, PASC[pos]] = mul_up(Rhi[:, :, pos], sub_up(1.0, xl))
    dlo = np.empty((B, len(INT), ND)); dhi = np.empty((B, len(INT), ND))
    Dl = np.empty((B, len(INT), ND)); Dh = np.empty((B, len(INT), ND))
    for a, pos in enumerate(INT):
        i = OWNER_PL[a]
        Dlo = sub_dn(Vlo[AGGC[pos]][:, :, i], Vhi[PASC[pos]][:, :, i])
        Dhi = sub_up(Vhi[AGGC[pos]][:, :, i], Vlo[PASC[pos]][:, :, i])
        rl = Rlo[:, :, pos]; rh = Rhi[:, :, pos]
        # reach r in [rl, rh], r >= 0: r*D >= rl*Dlo if Dlo >= 0, else >= rh*Dlo
        dlo[:, a] = np.where(Dlo >= 0, mul_dn(rl, Dlo), mul_dn(rh, Dlo))
        dhi[:, a] = np.where(Dhi >= 0, mul_up(rh, Dhi), mul_up(rl, Dhi))
        Dl[:, a] = Dlo; Dh[:, a] = Dhi
    DLO = div_dn(_sum6_dn(dlo.reshape(B, -1)), float(ND))
    DHI = div_up(_sum6_up(dhi.reshape(B, -1)), float(ND))
    RH = _sum6_up(Rhi[:, :, INT].transpose(0, 2, 1).reshape(B, -1))
    Dl = Dl.reshape(B, -1); Dh = Dh.reshape(B, -1)
    DMIN = Dl[:, NODES_OF].min(axis=2)      # (B,NP) min over the 6 nodes
    DMAX = Dh[:, NODES_OF].max(axis=2)
    return DLO, DHI, RH, DMIN, DMAX


def util_box(LO, HI):
    """Rigorous interval bounds on (u1,u2,u3) over the box [LO,HI]."""
    if not DIRECTED:
        return _util_box_nearest(LO, HI)
    B = LO.shape[0]
    LO = np.asarray(LO, float); HI = np.asarray(HI, float)
    Vlo = [None]*NPOS; Vhi = [None]*NPOS
    for pos in LEAF:
        Vlo[pos] = np.broadcast_to(PAYT[:, pos], (B, ND, 3)); Vhi[pos] = Vlo[pos]
    for pos in INT[::-1]:
        c = COORD[:, pos]
        xl = LO[:, c][:, :, None]; xh = HI[:, c][:, :, None]
        al, ah = Vlo[AGGC[pos]], Vhi[AGGC[pos]]
        pl, ph = Vlo[PASC[pos]], Vhi[PASC[pos]]
        dl = sub_dn(al, pl); dh = sub_up(ah, ph)
        Vlo[pos] = np.minimum(add_dn(pl, mul_dn(xl, dl)), add_dn(pl, mul_dn(xh, dl)))
        Vhi[pos] = np.maximum(add_up(ph, mul_up(xl, dh)), add_up(ph, mul_up(xh, dh)))
    sl = Vlo[0][:, 0].copy(); sh = Vhi[0][:, 0].copy()
    for d in range(1, ND):
        sl = add_dn(sl, Vlo[0][:, d]); sh = add_up(sh, Vhi[0][:, d])
    return div_dn(sl, float(ND)), div_up(sh, float(ND))


# ------------------------------------------------ the old round-to-nearest code
def _bounds_nearest(LO, HI):
    B = LO.shape[0]
    Vlo = [None] * NPOS; Vhi = [None] * NPOS
    for pos in LEAF:
        Vlo[pos] = np.broadcast_to(PAYT[:, pos], (B, ND, 3))
        Vhi[pos] = Vlo[pos]
    for pos in INT[::-1]:
        c = COORD[:, pos]                       # (24,)
        xl = LO[:, c][:, :, None]; xh = HI[:, c][:, :, None]
        al, ah = Vlo[AGGC[pos]], Vhi[AGGC[pos]]
        pl, ph = Vlo[PASC[pos]], Vhi[PASC[pos]]
        t1 = xl * al + (1 - xl) * pl
        t2 = xh * al + (1 - xh) * pl
        Vlo[pos] = np.minimum(t1, t2)
        t1 = xl * ah + (1 - xl) * ph
        t2 = xh * ah + (1 - xh) * ph
        Vhi[pos] = np.maximum(t1, t2)
    Rlo = np.zeros((B, ND, NPOS)); Rhi = np.zeros((B, ND, NPOS))
    Rlo[:, :, 0] = 1.0; Rhi[:, :, 0] = 1.0
    for pos in INT:
        c = COORD[:, pos]
        xl = LO[:, c]; xh = HI[:, c]
        Rlo[:, :, AGGC[pos]] = Rlo[:, :, pos] * xl
        Rhi[:, :, AGGC[pos]] = Rhi[:, :, pos] * xh
        Rlo[:, :, PASC[pos]] = Rlo[:, :, pos] * (1 - xh)
        Rhi[:, :, PASC[pos]] = Rhi[:, :, pos] * (1 - xl)
    dlo = np.empty((B, len(INT), ND)); dhi = np.empty((B, len(INT), ND))
    Dl = np.empty((B, len(INT), ND)); Dh = np.empty((B, len(INT), ND))
    for a, pos in enumerate(INT):
        i = OWNER_PL[a]
        Dlo = Vlo[AGGC[pos]][:, :, i] - Vhi[PASC[pos]][:, :, i]
        Dhi = Vhi[AGGC[pos]][:, :, i] - Vlo[PASC[pos]][:, :, i]
        rl = Rlo[:, :, pos]; rh = Rhi[:, :, pos]
        dlo[:, a] = np.where(Dlo >= 0, rl * Dlo, rh * Dlo)
        dhi[:, a] = np.where(Dhi >= 0, rh * Dhi, rl * Dhi)
        Dl[:, a] = Dlo; Dh[:, a] = Dhi
    DLO = KAP * (dlo.reshape(B, -1) @ S)
    DHI = KAP * (dhi.reshape(B, -1) @ S)
    RH  = (Rhi[:, :, INT].transpose(0, 2, 1).reshape(B, -1) @ S)
    Dl = Dl.reshape(B, -1); Dh = Dh.reshape(B, -1)
    DMIN = Dl[:, NODES_OF].min(axis=2)      # (B,NP) min over the 6 nodes
    DMAX = Dh[:, NODES_OF].max(axis=2)
    return DLO, DHI, RH, DMIN, DMAX


def _util_box_nearest(LO, HI):
    B = LO.shape[0]
    Vlo = [None]*NPOS; Vhi = [None]*NPOS
    for pos in LEAF:
        Vlo[pos] = np.broadcast_to(PAYT[:, pos], (B, ND, 3)); Vhi[pos] = Vlo[pos]
    for pos in INT[::-1]:
        c = COORD[:, pos]
        xl = LO[:, c][:, :, None]; xh = HI[:, c][:, :, None]
        al, ah = Vlo[AGGC[pos]], Vhi[AGGC[pos]]
        pl, ph = Vlo[PASC[pos]], Vhi[PASC[pos]]
        Vlo[pos] = np.minimum(xl*al + (1-xl)*pl, xh*al + (1-xh)*pl)
        Vhi[pos] = np.maximum(xl*ah + (1-xl)*ph, xh*ah + (1-xh)*ph)
    return KAP*Vlo[0].sum(axis=1), KAP*Vhi[0].sum(axis=1)
