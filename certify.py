"""
A: drive a CFR profile to an EXACT equilibrium.

CFR gives the support pattern (which coordinates are 0, which are 1, which are
interior); it does not give the interior values to better than ~3e-3.  But at an
equilibrium every strictly-interior coordinate must leave its owner indifferent:

    F_i(p) = du_{owner(i)} / dp_i = 0     for every interior coordinate i

That is a square multilinear system, and because u is multilinear its Jacobian
    J_ij = d^2 u_{owner(i)} / (dp_i dp_j)
is computable exactly from two gradient evaluations per column.  Newton from the
CFR profile converges to machine precision in a handful of steps.

The equilibrium component is generally positive-dimensional (free family
directions), so J is singular; the pseudo-inverse step keeps the iterate on the
component nearest the CFR start rather than failing.
"""
import numpy as np
import poletest as PT


def classify(g, P, tol=2e-2, snap_tol=4e-2):
    """Split coordinates using several CFR seeds: pure0 / pure1 / offpath / interior."""
    # CFR leaves opening probabilities around 1e-2, so a 5e-3 snap misses
    # the off-path structure entirely; use a looser threshold and take the
    # off-path set that is common to every seed.
    off = set(range(g.nparam))
    for q in P:
        off &= set(PT.offpath(g, PT.snap(g, q, tol=snap_tol)))
    V = np.array(P)
    pure0, pure1, interior = [], [], []
    for i in range(g.nparam):
        if i in off:
            continue
        v = V[:, i]
        if v.max() < tol:
            pure0.append(i)
        elif v.min() > 1 - tol:
            pure1.append(i)
        else:
            interior.append(i)
    return sorted(off), pure0, pure1, interior


def newton(g, p0, interior, iters=60, verbose=False):
    own = PT.owners(g)
    p = np.array(p0, float)
    idx = np.array(interior, dtype=int)
    hist = []
    if idx.size == 0:                      # all-pure hypothesis: nothing to solve
        return p, [0.0]
    for it in range(iters):
        F = g.gradient(p)[idx, own[idx]]
        hist.append(float(np.abs(F).max()))
        if hist[-1] < 1e-15:
            break
        J = np.empty((len(idx), len(idx)))
        for c, j in enumerate(idx):
            a, b = p.copy(), p.copy()
            a[j], b[j] = 1.0, 0.0
            Ga, Gb = g.gradient(a), g.gradient(b)
            J[:, c] = (Ga[idx, own[idx]] - Gb[idx, own[idx]])
        step = np.linalg.pinv(J, rcond=1e-6) @ F
        lam, ok = 1.0, False
        for _ in range(40):                       # damped: require real progress
            q = p.copy()
            q[idx] = np.clip(p[idx] - lam * step, 0.0, 1.0)
            if np.abs(g.gradient(q)[idx, own[idx]]).max() < hist[-1]:
                ok = True
                break
            lam *= 0.5
        if not ok:
            break                                 # stalled: do NOT take a bad step
        p = q
        if verbose:
            print("      it %2d  |F| %.3e  lam %.4f" % (it, hist[-1], lam))
    return p, hist


def certify(g, p0, interior, max_repair=40, verbose=False):
    """Newton + greedy support repair.

    If a coordinate's indifference condition cannot be satisfied, that
    coordinate is not interior at equilibrium: it should be pure.  The sign of
    its own-derivative says which way -- du/dx > 0 means the owner wants more of
    the aggressive action, so it goes to 1; du/dx < 0 sends it to 0.  Drop the
    worst offender, refit, repeat.
    """
    own = PT.owners(g)
    p = np.array(p0, float)
    S = list(interior)
    for rep in range(max_repair):
        p, h = newton(g, p, S)
        e = float(np.abs(g.exploitability_bi(p)).max())
        if verbose:
            print("      repair %2d: |S|=%-3d max|F| %.2e  expl %.2e"
                  % (rep, len(S), h[-1], e))
        if e < 1e-12:
            return p, S, e, rep
        if not S:
            break
        idx = np.array(S)
        Fv = g.gradient(p)[idx, own[idx]]
        k = int(np.argmax(np.abs(Fv)))
        worst = S[k]
        p[worst] = 1.0 if Fv[k] > 0 else 0.0
        S = [i for i in S if i != worst]
    return p, S, float(np.abs(g.exploitability_bi(p)).max()), max_repair
