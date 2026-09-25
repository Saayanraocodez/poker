"""
The dynamical-systems reading of the incidence poles.

Learning dynamics on an extensive-form game with binary information sets take
the replicator form, one 2-simplex per set, driven by counterfactual value:

    dx_i/dt = x_i (1 - x_i) g_i(x),     g_i(x) = du_{owner(i)} / dx_i

Every point of the SGS family is a FIXED POINT of this flow: interior
coordinates have g_i = 0 (indifference) and pure coordinates have x_i(1-x_i) = 0.
So the family is a MANIFOLD of fixed points, not an isolated one.

Linearising, and using that u is multilinear so d^2u/dx_i^2 = 0:

    J_ij = delta_ij (1 - 2 x_i) g_i  +  x_i (1 - x_i) * d^2u_owner/(dx_i dx_j)

Two things follow, and they are what this module tests:

  1. A PURE coordinate contributes the single eigenvalue (1-2x_i) g_i.  For
     x_i = 0 that is +g_i, for x_i = 1 it is -g_i.  The equilibrium conditions
     are exactly g_i <= 0 and g_i >= 0 respectively, so every pure coordinate is
     stable -- and becomes NEUTRAL precisely when its incentive g_i hits zero.

  2. g_i = 0 for a pure coordinate is exactly the deterrence boundary, which is
     exactly where rho's denominator vanishes.

     => rho's pole and the loss of hyperbolicity are the SAME event.
"""
import numpy as np

import kuhn3p as K
import family as F
import kuhnGen as Q

I = K.NAME_IDX
OWN = np.arange(48) // 16

# kuhnGen(3,4) shares kuhn3p's coordinate layout under this permutation, and has
# a one-pass vectorised gradient -- 48x faster than 48 separate exact derivatives.
_G = Q.Kuhn(3, 4)
_P = np.empty(48, int)
for _pl in range(3):
    for _j in range(1, 5):
        for _h, _k in Q.SGS_SIT[_pl].items():
            _P[K.NAME_IDX["%s%d%d" % ("abc"[_pl], _j, _k)]] = _G.pidx(_pl, _j, _h)
_INV = np.empty(48, int)
_INV[_P] = np.arange(48)


def _grad(p):
    """(48, 3) gradient in kuhn3p coordinate order, via the fast engine."""
    q = np.empty(48)
    q[_P] = p
    return _G.gradient(q)[_P]


def g_vec(p):
    """g_i = du_owner(i)/dx_i for every coordinate."""
    return _grad(p)[np.arange(48), OWN]


def hess_rows(p):
    """H[i, j] = d^2 u_owner(i) / (dx_i dx_j), exact.  Diagonal is 0 by
    multilinearity.  Two vectorised gradient evaluations per column."""
    H = np.empty((48, 48))
    ar = np.arange(48)
    for j in range(48):
        a, b = p.copy(), p.copy()
        a[j], b[j] = 1.0, 0.0
        H[:, j] = (_grad(a) - _grad(b))[ar, OWN]
    np.fill_diagonal(H, 0.0)
    return H


def jacobian(p):
    """Linearisation of the replicator flow at p."""
    g = g_vec(p)
    H = hess_rows(p)
    w = p * (1.0 - p)
    J = w[:, None] * H
    J[np.arange(48), np.arange(48)] += (1.0 - 2.0 * p) * g
    return J


def spectrum(p, tol=1e-11):
    ev = np.linalg.eigvals(jacobian(p))
    re = ev.real
    return dict(n_zero=int((np.abs(ev) < tol).sum()),
                n_stable=int((re < -tol).sum()),
                n_unstable=int((re > tol).sum()),
                max_re=float(re.max()),
                min_re=float(re.min()),
                n_complex=int((np.abs(ev.imag) > tol).sum()),
                ev=ev)


def is_fixed_point(p, tol=1e-13):
    """Verify the family really is a manifold of fixed points."""
    return float(np.abs(p * (1.0 - p) * g_vec(p)).max()) < tol
