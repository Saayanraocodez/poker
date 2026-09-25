"""
Directional-derivative machinery for a strategy profile p.

A "direction" for player A is a vector d supported on A's 16 parameters.
We use single-coordinate directions d = +-e_i, which are exactly the extreme
rays of the feasible perturbation cone at p (the feasible set is a box), so
they span every feasible unilateral deviation.

Because u_i is multilinear, u_i(p + eps*e_j) is AFFINE in eps, so the central
difference is exact to machine precision and equals u(p_j=1) - u(p_j=0).
"""
import numpy as np

import kuhn3p as K

TOL = 1e-11
PLAYER_NAME = ("P1", "P2", "P3")


def feasible_coord_directions(p, player, edge=1e-9):
    """All feasible single-coordinate directions for `player` at p.

    +e_i is feasible when p_i < 1, -e_i when p_i > 0.
    """
    out = []
    for i in range(player * 16, (player + 1) * 16):
        if p[i] < 1.0 - edge:
            out.append((i, +1.0))
        if p[i] > edge:
            out.append((i, -1.0))
    return out


def dirvec(i, sign):
    d = np.zeros(K.NPARAM)
    d[i] = sign
    return d


def derivatives(p, i, sign, h=1e-5):
    """(du1,du2,du3)/d eps along +-e_i, by CENTRAL finite difference,
    plus the exact multilinear derivative for cross-checking."""
    d = dirvec(i, sign)
    fd = K.central_diff(p, d, h)
    ex = sign * K.exact_coord_derivative(p, i)
    return fd, ex


def scan(p, player, h=1e-5):
    """Every feasible coordinate direction for `player`, with derivatives."""
    rows = []
    for i, s in feasible_coord_directions(p, player):
        fd, ex = derivatives(p, i, s, h)
        rows.append(dict(param=K.PARAM_NAME[i], idx=i, sign=s,
                         fd=fd, exact=ex,
                         fd_err=float(np.abs(fd - ex).max()),
                         zerosum=float(abs(fd.sum())),
                         dA=fd[player]))
    return rows


def rho(fd, A, C):
    """rho = -(du_C/d eps) / (du_A/d eps).  None if the denominator is ~0."""
    dA = fd[A]
    if abs(dA) < TOL:
        return None
    return -fd[C] / dA
