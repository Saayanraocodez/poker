"""Batched damped Gauss-Newton on the indifference system of a support pattern."""
import numpy as np, bgrad, bnb

MIXC, DC = bnb.MIX, bnb.DC
STEPS = np.array([1.0, 0.5, 0.2, 0.05])

def _midx(pats):
    B = pats.shape[0]; mask = (pats == MIXC)
    mmax = max(1, int(mask.sum(axis=1).max()))
    Midx = np.zeros((B, mmax), dtype=np.int64); Mok = np.zeros((B, mmax), bool)
    for b in range(B):
        w = np.flatnonzero(mask[b]); Midx[b, :len(w)] = w; Mok[b, :len(w)] = True
    return Midx, Mok, mmax

def solve_batch(pats, rng, iters=25, jac_every=3, lam=1e-10, x0=None, drop=True):
    B = pats.shape[0]
    Midx, Mok, mmax = _midx(pats)
    br = np.arange(B)[:, None]
    P = np.where(pats == 1, 1.0, 0.0)
    P[pats == DC] = 0.5
    m = (pats == MIXC)
    P[m] = rng.random(m.sum()) if x0 is None else x0[m]
    act = np.ones(B, bool)
    J = np.zeros((B, mmax, mmax))
    eye = lam * np.eye(mmax)
    for it in range(iters):
        ai = np.flatnonzero(act)
        if ai.size == 0: break
        Pa = P[ai]; Ma = Midx[ai]; Oa = Mok[ai]; ba = np.arange(len(ai))[:, None]
        G = bgrad.grads_own(Pa)
        F = np.where(Oa, G[ba, Ma], 0.0)
        base = np.abs(F).max(axis=1)
        conv = base < 1e-15
        if conv.any():
            act[ai[conv]] = False
            keep = ~conv
            if not keep.any(): break
            ai = ai[keep]; Pa = Pa[keep]; Ma = Ma[keep]; Oa = Oa[keep]
            F = F[keep]; base = base[keep]; ba = np.arange(len(ai))[:, None]
        if it % jac_every == 0:
            Jn = np.zeros((len(ai), mmax, mmax))
            for c in range(mmax):
                P1 = Pa.copy(); P1[np.arange(len(ai)), Ma[:, c]] = 1.0
                P0 = Pa.copy(); P0[np.arange(len(ai)), Ma[:, c]] = 0.0
                col = (bgrad.grads_own(P1) - bgrad.grads_own(P0))[ba, Ma]
                Jn[:, :, c] = np.where(Oa & Oa[:, c][:, None], col, 0.0)
            J[ai] = Jn
        Ja = J[ai]
        A = Ja.transpose(0, 2, 1) @ Ja + eye
        d = np.linalg.solve(A, -(Ja.transpose(0, 2, 1) @ F[:, :, None]))[:, :, 0]
        n = len(ai); ns = len(STEPS)
        Q = np.repeat(Pa, ns, axis=0)
        Mrep = np.repeat(Ma, ns, axis=0); drep = np.repeat(d, ns, axis=0)
        srep = np.tile(STEPS, n)[:, None]
        bq = np.arange(n * ns)[:, None]
        Q[bq, Mrep] = np.clip(Q[bq, Mrep] + srep * drep, 1e-13, 1 - 1e-13)
        GQ = bgrad.grads_own(Q)
        rq = np.abs(np.where(np.repeat(Oa, ns, axis=0), GQ[bq, Mrep], 0.0)).max(axis=1)
        rq = rq.reshape(n, ns); best = rq.argmin(axis=1)
        P[ai] = Q.reshape(n, ns, 48)[np.arange(n), best]
        if drop and it >= 10:
            act[ai[rq[np.arange(n), best] > 1e-4]] = False
    G = bgrad.grads_own(P)
    br = np.arange(B)[:, None]
    resid = np.abs(np.where(Mok, G[br, Midx], 0.0)).max(axis=1)
    return P, resid

def check(P, tol=1e-10):
    G = bgrad.grads_own(P)
    ok = ~(((P <= 1e-9) & (G > tol)).any(axis=1))
    ok &= ~(((P >= 1 - 1e-9) & (G < -tol)).any(axis=1))
    inte = (P > 1e-9) & (P < 1 - 1e-9)
    ok &= ~((inte & (np.abs(G) > tol)).any(axis=1))
    return ok
