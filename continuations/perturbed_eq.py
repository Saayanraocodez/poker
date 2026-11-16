"""Equilibria of the PERTURBED game (every action has probability >= its floor), solved to machine
precision by an active-set Newton method -- CFR+ does not converge on these games (its exploitability
stalls near 6e-5 at 2e5 iterations), so averages of CFR runs are not equilibria.

A profile x with lo <= x <= hi is an equilibrium of the perturbed game iff for every coordinate
    x_i = lo_i  and D_i <= 0,   or   x_i = hi_i  and D_i >= 0,   or   lo_i < x_i < hi_i  and D_i = 0
(with floors every information set is own-reachable, so the own-reach-stripped D is the exact condition).

solve(game, lo, hi, x0): guess the active set from x0, Newton on {D_M = 0} with the exact Jacobian
(least-squares step, so a degenerate system still converges), then repair the active set and repeat.
Returns x, the mixed set M, the residual, and the singular values of dD_M/dx_M -- its rank deficiency
is the local dimension of the perturbed game's equilibrium set.
"""
import numpy as np
import g34


def jac(g, x, rows, cols):
    J = np.zeros((48, len(cols)))
    for t, j in enumerate(cols):
        x1 = x.copy(); x1[j] = 1.0; x0 = x.copy(); x0[j] = 0.0
        J[:, t] = g.DR(x1)[0] - g.DR(x0)[0]
    return J[rows]


def violation(g, x, lo, hi, tol=1e-12):
    D = g.DR(x)[0]; v = 0.0
    for i in range(48):
        if x[i] <= lo[i] + tol: v = max(v, D[i])
        elif x[i] >= hi[i] - tol: v = max(v, -D[i])
        else: v = max(v, abs(D[i]))
    return v


def solve(g, lo, hi, x0, maxouter=60, verbose=False):
    x = np.clip(x0.copy(), lo, hi)
    gap = 0.02 * np.minimum(1.0, (hi - lo))
    M = [i for i in range(48) if lo[i] + gap[i] < x[i] < hi[i] - gap[i]]
    for outer in range(maxouter):
        for i in range(48):
            if i not in M: x[i] = lo[i] if x[i] < 0.5 * (lo[i] + hi[i]) else hi[i]
        # Newton on the mixed set
        for it in range(60):
            D = g.DR(x)[0]
            if not M or np.abs(D[M]).max() < 1e-15: break
            J = jac(g, x, M, M)
            step = np.linalg.lstsq(J, -D[M], rcond=1e-11)[0]
            t = 1.0
            xm = x[M] + step
            # stay inside the floors: damp
            while np.any(xm < lo[M] - 1e-12) or np.any(xm > hi[M] + 1e-12):
                t *= 0.5; xm = x[M] + t * step
                if t < 1e-6: break
            x[M] = np.clip(xm, lo[M], hi[M])
            if np.abs(t * step).max() < 1e-15: break
        D = g.DR(x)[0]
        changed = False
        # mixed coordinates stuck at a floor leave M; floor coordinates with the wrong sign enter M
        for i in list(M):
            if x[i] <= lo[i] + 1e-13 and D[i] < -1e-13: M.remove(i); x[i] = lo[i]; changed = True
            elif x[i] >= hi[i] - 1e-13 and D[i] > 1e-13: M.remove(i); x[i] = hi[i]; changed = True
        worst = None
        for i in range(48):
            if i in M: continue
            bad = D[i] if x[i] <= lo[i] + 1e-13 else -D[i]
            if bad > 1e-13 and (worst is None or bad > worst[0]): worst = (bad, i)
        if worst is not None:
            i = worst[1]; M.append(i); M.sort()
            x[i] = lo[i] + 1e-6 * (hi[i] - lo[i]) if x[i] <= lo[i] + 1e-13 else hi[i] - 1e-6 * (hi[i] - lo[i]); changed = True
        if verbose: print("outer %d  |M| %d  viol %.2e" % (outer, len(M), violation(g, x, lo, hi)))
        if not changed: break
    sv = np.linalg.svd(jac(g, x, M, M), compute_uv=False) if M else np.array([])
    return x, M, violation(g, x, lo, hi), sv
