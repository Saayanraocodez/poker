"""Active-set feasibility solve for one support pattern.

Variables : every coordinate labelled MIX (interior) or DC (own condition
            vacuous because the info set is unreachable -- but its VALUE still
            shapes other players' incentives, so it is a free variable, not a
            constant).
Equations : du_t = 0 for every MIX coordinate, plus every pure coordinate whose
            sign condition is currently violated (pushed to its boundary).
"""
import numpy as np, bgrad, bnb

MIXC, DCC = bnb.MIX, bnb.DC
STEPS = np.array([1.0, 0.5, 0.2, 0.05, 0.01])

def viol(P, pats, G=None):
    if G is None: G = bgrad.grads_own(P)
    v = np.zeros_like(G)
    z = (pats == 0); o = (pats == 1); m = (pats == MIXC)
    v[z] = np.maximum(0.0, G[z])
    v[o] = np.maximum(0.0, -G[o])
    v[m] = np.abs(G[m])
    return v, G

def solve(pats, rng, iters=30, jac_every=3, lam=1e-10, x0=None, tol=1e-11):
    B = pats.shape[0]
    var = (pats == MIXC) | (pats == DCC)
    P = np.where(pats == 1, 1.0, 0.0)
    if x0 is None: P[var] = rng.random(int(var.sum()))
    else:          P[var] = x0[var]
    J = np.zeros((B, 48, 48))
    eye = lam * np.eye(48)
    act = np.ones(B, bool)
    for it in range(iters):
        ai = np.flatnonzero(act)
        if ai.size == 0: break
        Pa = P[ai]; pa = pats[ai]; va = var[ai]
        v, G = viol(Pa, pa)
        done = v.max(axis=1) < tol
        if done.any():
            act[ai[done]] = False
            keep = ~done
            if not keep.any(): break
            ai = ai[keep]; Pa = Pa[keep]; pa = pa[keep]; va = va[keep]
            v = v[keep]; G = G[keep]
        eq = (pa == MIXC) | (v > tol)
        F = np.where(eq, G, 0.0)
        if it % jac_every == 0:
            Jn = np.zeros((len(ai), 48, 48))
            for s in range(48):
                P1 = Pa.copy(); P1[:, s] = 1.0
                P0 = Pa.copy(); P0[:, s] = 0.0
                Jn[:, :, s] = bgrad.grads_own(P1) - bgrad.grads_own(P0)
            J[ai] = Jn
        Ja = J[ai] * eq[:, :, None] * va[:, None, :]
        A = Ja.transpose(0, 2, 1) @ Ja + eye
        d = np.linalg.solve(A, -(Ja.transpose(0, 2, 1) @ F[:, :, None]))[:, :, 0]
        n = len(ai); ns = len(STEPS)
        Q = np.repeat(Pa, ns, axis=0)
        Q += np.tile(STEPS, n)[:, None] * np.repeat(d * va, ns, axis=0)
        np.clip(Q, 0.0, 1.0, out=Q)
        vq, _ = viol(Q, np.repeat(pa, ns, axis=0))
        rq = vq.max(axis=1).reshape(n, ns)
        best = rq.argmin(axis=1)
        cur = v.max(axis=1)
        newP = Q.reshape(n, ns, 48)[np.arange(n), best]
        imp = rq[np.arange(n), best] < cur
        P[ai[imp]] = newP[imp]
        if (~imp).any():        # stuck: random kick on the free coordinates
            st = ai[~imp]
            P[st] = np.where(var[st], np.clip(P[st] + rng.normal(0, .05, (len(st), 48)), 0, 1), P[st])
    v, _ = viol(P, pats)
    return P, v.max(axis=1)
