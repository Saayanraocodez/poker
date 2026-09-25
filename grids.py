"""Grids over the valid range of the family's free parameters."""
import numpy as np

import kuhn3p as K
import family as F

FREE_KEYS = ("b11", "b21", "b23", "b32", "c11", "c33", "c34", "beta",
             "t_b23", "t_b32", "t_c33", "sub")
SUBCODE = {"A": 0, "B": 1, "C": 2}


def _pack(items):
    P = np.array([it[0] for it in items], dtype=np.float64)
    meta = {k: np.array([it[1][k] for it in items], dtype=np.float64)
            for k in FREE_KEYS}
    return P, meta


def _meta(m, sub, t_b23=0.0, t_b32=0.0, t_c33=0.0):
    d = dict(m)
    d["beta"] = F.beta_of(m["b11"], m["b21"])
    d["t_b23"], d["t_b32"], d["t_c33"] = t_b23, t_b32, t_c33
    d["sub"] = SUBCODE[sub]
    return d


# --------------------------------------------------------------------------
def grid_A(nb=21, ns=6, tb=(0.0, 0.5, 1.0), tc=(0.0, 0.5, 1.0), c34s=(0.0, 1.0)):
    """c11 = 0:  0 <= b11 <= b21 <= 1/4,  beta = b21."""
    items = []
    for b21 in np.linspace(0.0, 0.25, nb):
        for s in np.linspace(0.0, 1.0, ns):
            b11 = s * b21
            for t_b32 in tb:
                for t_c33 in tc:
                    for c34 in c34s:
                        p, m = F.profile_A(b11, b21, t_b32, t_c33, c34)
                        items.append((p, _meta(m, "A", 0.0, t_b32, t_c33)))
    return _pack(items)


def grid_B(nb=21, nc=6, tb=(0.0, 0.5, 1.0), tc=(0.0, 0.5, 1.0), c34s=(0.0, 1.0)):
    """0 < c11 < 1/2:  b21 = b11 <= 1/4,  beta = b11."""
    items = []
    for b11 in np.linspace(0.0, 0.25, nb):
        cmax = F.c11_max(b11, b11)
        for tc11 in np.linspace(0.02, 0.98, nc):
            c11 = tc11 * cmax
            for t_b32 in tb:
                for t_c33 in tc:
                    for c34 in c34s:
                        p, m = F.profile_B(b11, c11, t_b32, t_c33, c34)
                        items.append((p, _meta(m, "B", 0.0, t_b32, t_c33)))
    return _pack(items)


def grid_C(nb=21, ns=6, t23=(0.0, 0.5, 1.0), tb=(0.0, 1.0),
           tc=(0.0, 0.5, 1.0), c34s=(0.0, 1.0)):
    """c11 = 1/2:  b11 <= 1/4,  b21 <= min{b11, 1/2 - 2 b11},  beta = b11."""
    items = []
    for b11 in np.linspace(0.0, 0.25, nb):
        b21max = min(b11, 0.5 - 2 * b11)
        for s in np.linspace(0.0, 1.0, ns):
            b21 = s * b21max
            for t_b23 in t23:
                for t_b32 in tb:
                    for t_c33 in tc:
                        for c34 in c34s:
                            p, m = F.profile_C(b11, b21, t_b23, t_b32,
                                               t_c33, c34)
                            items.append((p, _meta(m, "C", t_b23, t_b32,
                                                   t_c33)))
    return _pack(items)


def full_grid():
    PA, MA = grid_A()
    PB, MB = grid_B()
    PC, MC = grid_C()
    P = np.concatenate([PA, PB, PC], axis=0)
    M = {k: np.concatenate([MA[k], MB[k], MC[k]]) for k in FREE_KEYS}
    return P, M


# ---------------------------------------------- dense 1-D sweeps for plots --
def line_A_beta(n=201, t_b32=0.5, t_c33=0.5, c34=0.0, s=1.0):
    """Sub-family A along b11 = s * b21, b21 = beta from 0 to 1/4."""
    betas = np.linspace(0.0, 0.25, n)
    P = np.array([F.profile_A(s * b, b, t_b32, t_c33, c34)[0] for b in betas])
    return betas, P


def line_B_c11(n=201, b11=0.15, t_b32=0.5, t_c33=0.5, c34=0.0):
    """Sub-family B: c11 sweeps its valid range at fixed b11."""
    cmax = F.c11_max(b11, b11)
    cs = np.linspace(1e-4, cmax - 1e-4, n)
    P = np.array([F.profile_B(b11, c, t_b32, t_c33, c34)[0] for c in cs])
    return cs, P


def line_C_b21(n=201, b11=0.2, t_b23=0.5, t_b32=0.5, t_c33=0.5, c34=0.0):
    """Sub-family C: b21 from 0 to min{b11, 1/2-2 b11} at fixed b11."""
    hi = min(b11, 0.5 - 2 * b11)
    xs = np.linspace(0.0, hi, n)
    P = np.array([F.profile_C(b11, x, t_b23, t_b32, t_c33, c34)[0]
                  for x in xs])
    return xs, P


def line_A_tc33(n=201, b11=0.1, b21=0.2, t_b32=0.5, c34=0.0):
    """Sub-family A: c33 sweeps its valid interval (a NON-reached parameter,
    but P1's incentive to deviate to a11>0 depends on it)."""
    ts = np.linspace(0.0, 1.0, n)
    P = np.array([F.profile_A(b11, b21, t_b32, t, c34)[0] for t in ts])
    return ts, P
