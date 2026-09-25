"""
Tools for characterising the FULL equilibrium set of 3-player 4-card Kuhn poker.

Canonical object: a profile's LEAF DISTRIBUTION w in R^312 (reach prob of each
terminal history, given the deal).  Two profiles are strategically identical
iff w matches; this quotients out all off-path indeterminacy automatically.
"""
import itertools
import numpy as np
import kuhn3p as K

NP = K.NPARAM                 # 48
IDX, AGG, PAY = K.IDX, K.AGG, K.PAY
NLEAF = K.NLEAF               # 312
KAP = K.KAPPA
I = K.NAME_IDX
NAME = K.PARAM_NAME

# ---------------------------------------------------------------- leaf wts --
def leafw(p):
    q = np.append(np.asarray(p, float), 1.0)
    f = np.where(AGG, q[IDX], 1.0 - q[IDX])
    return f.prod(axis=1)

def leafw_batch(P):
    P = np.asarray(P, float)
    Q = np.empty((P.shape[0], NP + 1)); Q[:, :NP] = P; Q[:, NP] = 1.0
    w = np.ones((P.shape[0], NLEAF))
    for k in range(IDX.shape[1]):
        g = Q[:, IDX[:, k]]
        w *= np.where(AGG[:, k][None, :], g, 1.0 - g)
    return w

def util(p):   return KAP * (leafw(p) @ PAY)
def util_b(P): return KAP * (leafw_batch(P) @ PAY)

def grad(p):
    """(48,3) exact multilinear gradient du_t/dp_i."""
    P = np.repeat(np.asarray(p, float)[None, :], 2 * NP, axis=0)
    ar = np.arange(NP)
    P[2 * ar, ar] = 1.0
    P[2 * ar + 1, ar] = 0.0
    U = util_b(P)
    return U[0::2] - U[1::2]

# ------------------------------------------------------------- best resp ----
_SUB = {}
for _pl in range(3):
    for _j in K.CARDS:
        m = K.HOLDER[:, _pl] == _j
        _SUB[(_pl, _j)] = (IDX[m], AGG[m], PAY[m][:, _pl])
_BITS = np.array(list(itertools.product((0.0, 1.0), repeat=4)))   # (16,4)

def br(p, player):
    """exact BR value for `player` + the 16-vector of its pure BR coords."""
    q = np.append(np.asarray(p, float), 1.0)
    tot = 0.0
    out = np.empty(16)
    for j in K.CARDS:
        si, sa, sp = _SUB[(player, j)]
        own = [K.pidx(player, j, k) for k in K.SITUATIONS]
        Q = np.repeat(q[None, :], 16, axis=0)
        Q[:, own] = _BITS
        g = Q[:, si]                                   # (16,L,5)
        f = np.where(sa[None, :, :], g, 1.0 - g)
        val = KAP * (f.prod(axis=2) @ sp)              # (16,)
        a = int(val.argmax())
        tot += val[a]
        out[(j - 1) * 4:(j - 1) * 4 + 4] = _BITS[a]
    return tot, out

def nashgap(p):
    p = np.asarray(p, float)
    u = util(p)
    return sum(br(p, i)[0] - u[i] for i in range(3))

def expl(p):
    p = np.asarray(p, float)
    u = util(p)
    return np.array([br(p, i)[0] - u[i] for i in range(3)])

def nashgap_grad(p):
    """(value, exact-a.e. gradient) of  sum_i (BR_i - u_i)."""
    p = np.asarray(p, float)
    u = util(p)
    Gp = grad(p)                       # (48,3)
    val = 0.0
    g = np.zeros(NP)
    for i in range(3):
        v, s = br(p, i)
        val += v - u[i]
        q = p.copy(); q[16 * i:16 * i + 16] = s
        Gq = grad(q)[:, i]             # d u_i(BR_i, p_-i) / dp
        mask = np.ones(NP); mask[16 * i:16 * i + 16] = 0.0   # envelope thm
        g += mask * Gq - Gp[:, i]
    return val, g

# ----------------------------------------------------------- equilibrium ----
def eq_residual(p):
    """max violation of the first-order Nash conditions (KKT-style)."""
    p = np.asarray(p, float)
    G = grad(p)
    r = 0.0
    for i in range(3):
        for k in range(16):
            t = 16 * i + k
            d = G[t, i]
            x = p[t]
            if x <= 1e-12:   v = max(0.0, d)
            elif x >= 1 - 1e-12: v = max(0.0, -d)
            else:            v = abs(d)
            r = max(r, v)
    return r

def canon(p, tol=1e-11):
    """canonical signature of a profile = its leaf distribution, rounded."""
    return np.round(leafw(p), 9)
