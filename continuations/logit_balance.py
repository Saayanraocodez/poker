"""Where does the limiting logit AQRE sit in the family?  A first-order ("logit balance") condition.

Along the principal branch a mixed coordinate i has  D_i / R_i = logit(x_i) / lambda, so to first
order in 1/lambda the indifference system of the family is perturbed by the vector
        g_i = R_i(x*) * logit(x*_i)            (i on path and mixed),
while trembles are exponentially small.  The family is a manifold of solutions, so the Jacobian J of
(D_i) with respect to the mixed coordinates is singular there, and the perturbed system is solvable
only if g is in the range of J.  That is a system of equations in the family's parameters: its
solutions are the only possible limits.  For sub-family B (b11 = b21 = beta, 0 < c11 < 1/2) it is two
equations in (beta, c11).
usage: python logit_balance.py
"""
import numpy as np
from scipy.optimize import minimize
import g34, perturbed_eq as P

g = g34.Game(1.0); IX = g34.IX
ON = ['a33', 'b11', 'b21', 'b33', 'b41', 'c11', 'c21']
M = [IX[n] for n in ON]


def famB(beta, c11):
    x = np.zeros(48)
    for l in 'abc':
        for s_ in ('42', '43', '44'): x[IX[l + s_]] = 1.0
    x[IX['a33']] = .5; x[IX['b11']] = x[IX['b21']] = beta; x[IX['b33']] = .5 + 1.5 * beta; x[IX['b41']] = 4 * beta
    x[IX['c11']] = c11; x[IX['c21']] = .5 - c11; x[IX['c41']] = 1.0
    w = 1.75 * beta; x[IX['c33']] = .5 + w / 3
    return x


def resid(v):
    beta, c11 = v
    if not (1e-4 < beta < .2499 and 1e-4 < c11 < .4999): return 1e6
    x = famB(beta, c11)
    D, R = g.DR(x)
    J = P.jac(g, x, M, M)
    gv = R[M] * np.log(x[M] / (1 - x[M]))
    r = gv - J @ np.linalg.lstsq(J, gv, rcond=1e-10)[0]
    return float(r @ r) * 1e6


if __name__ == "__main__":
    x = famB(.16, .25); J = P.jac(g, x, M, M)
    print("singular values of the on-path indifference Jacobian in B:", np.round(np.linalg.svd(J, compute_uv=False), 6))
    best = None
    for b0 in (.05, .1, .16, .22):
        for c0 in (.1, .25, .4):
            r = minimize(resid, [b0, c0], method='Nelder-Mead', options=dict(xatol=1e-13, fatol=1e-22, maxiter=4000))
            if best is None or r.fun < best.fun: best = r
            print("start (%.2f, %.2f) -> beta %.10f  c11 %.10f  residual %.2e" % (b0, c0, r.x[0], r.x[1], r.fun))
    b, c = best.x
    print("logit-balance point in sub-family B: beta* = %.10f, c11* = %.10f ; w = %.6f, c33* = 1/2 + w/3 = %.8f ; u = %s"
          % (b, c, 1.75 * b, .5 + 1.75 * b / 3, np.round(g.util(famB(b, c)), 8)))
