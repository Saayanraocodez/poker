"""Compact LM feasibility screen: Jacobian restricted to free columns only."""
import numpy as np, bgrad, bnb, solve2
MIXC, DCC = bnb.MIX, bnb.DC
STEPS = np.array([1.0, 0.4, 0.1])

def screen(pats, rng, iters=12, jac_every=6, lam=1e-10, x0=None):
    B = pats.shape[0]
    var = (pats == MIXC) | (pats == DCC)
    cols = np.flatnonzero(var.any(axis=0))
    nc = len(cols)
    if nc == 0:
        v, _ = solve2.viol(np.where(pats == 1, 1.0, 0.0), pats)
        return np.where(pats == 1, 1.0, 0.0), v.max(axis=1)
    rows = np.flatnonzero(((pats == MIXC) | (pats == 0) | (pats == 1)).any(axis=0))
    nr = len(rows)
    P = np.where(pats == 1, 1.0, 0.0)
    P[var] = rng.random(int(var.sum())) if x0 is None else x0[var]
    vmask = var[:, cols]
    J = np.zeros((B, nr, nc))
    eye = lam * np.eye(nc)
    for it in range(iters):
        v, G = solve2.viol(P, pats)
        eq = ((pats == MIXC) | (v > 1e-11))[:, rows]
        F = np.where(eq, G[:, rows], 0.0)
        if it % jac_every == 0:
            for a, s in enumerate(cols):
                P1 = P.copy(); P1[:, s] = 1.0
                P0 = P.copy(); P0[:, s] = 0.0
                J[:, :, a] = (bgrad.grads_own(P1) - bgrad.grads_own(P0))[:, rows]
        Ja = J * eq[:, :, None] * vmask[:, None, :]
        A = Ja.transpose(0, 2, 1) @ Ja + eye
        d = np.linalg.solve(A, -(Ja.transpose(0, 2, 1) @ F[:, :, None]))[:, :, 0]
        dd = np.zeros((B, 48)); dd[:, cols] = d * vmask
        ns = len(STEPS)
        Q = np.repeat(P, ns, axis=0) + np.tile(STEPS, B)[:, None] * np.repeat(dd, ns, axis=0)
        np.clip(Q, 0.0, 1.0, out=Q)
        vq, _ = solve2.viol(Q, np.repeat(pats, ns, axis=0))
        rq = vq.max(axis=1).reshape(B, ns)
        b = rq.argmin(axis=1)
        newP = Q.reshape(B, ns, 48)[np.arange(B), b]
        imp = rq[np.arange(B), b] < v.max(axis=1)
        P[imp] = newP[imp]
    v, _ = solve2.viol(P, pats)
    return P, v.max(axis=1)
