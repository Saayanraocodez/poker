"""Cheap first-pass feasibility screen for support patterns."""
import numpy as np, bgrad, bnb, solve2

MIXC, DCC = bnb.MIX, bnb.DC
STEPS = np.array([1.0, 0.4, 0.1])

def screen(pats, rng, iters=12, jac_every=6, lam=1e-10, x0=None):
    B = pats.shape[0]
    var = (pats == MIXC) | (pats == DCC)
    cols = np.flatnonzero(var.any(axis=0))          # only these matter
    P = np.where(pats == 1, 1.0, 0.0)
    P[var] = rng.random(int(var.sum())) if x0 is None else x0[var]
    J = np.zeros((B, 48, 48))
    eye = lam * np.eye(48)
    for it in range(iters):
        v, G = solve2.viol(P, pats)
        eq = (pats == MIXC) | (v > 1e-11)
        F = np.where(eq, G, 0.0)
        if it % jac_every == 0:
            for s in cols:
                P1 = P.copy(); P1[:, s] = 1.0
                P0 = P.copy(); P0[:, s] = 0.0
                J[:, :, s] = bgrad.grads_own(P1) - bgrad.grads_own(P0)
        Ja = J * eq[:, :, None] * var[:, None, :]
        A = Ja.transpose(0, 2, 1) @ Ja + eye
        d = np.linalg.solve(A, -(Ja.transpose(0, 2, 1) @ F[:, :, None]))[:, :, 0]
        ns = len(STEPS)
        Q = np.repeat(P, ns, axis=0) + np.tile(STEPS, B)[:, None] * np.repeat(d * var, ns, axis=0)
        np.clip(Q, 0.0, 1.0, out=Q)
        vq, _ = solve2.viol(Q, np.repeat(pats, ns, axis=0))
        rq = vq.max(axis=1).reshape(B, ns)
        b = rq.argmin(axis=1)
        cur = v.max(axis=1)
        newP = Q.reshape(B, ns, 48)[np.arange(B), b]
        imp = rq[np.arange(B), b] < cur
        P[imp] = newP[imp]
    v, _ = solve2.viol(P, pats)
    return P, v.max(axis=1)
