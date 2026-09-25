"""Levenberg-Marquardt on the PROJECTED-GRADIENT residual.  No support labels.

Why this exists: `control_boxpats.py` showed that a support pattern derived from
a coarse bnb5 box cannot express a family equilibrium -- 0 of 9 known points
were recovered.  The boundary reading pins coordinates that are interior (a33 =
1/2 sits on a slab edge and gets pinned to 0, and bisection then PROVES that
pattern infeasible, correctly); the interior reading demands du = 0 on
coordinates that really are hard against 0 or 1.  A real equilibrium mixes the
two in a way no single labelling of the box captures, and enumerating the
mixtures is 2^21 per box.

The projected-gradient residual has no such hypothesis in it:

    F_i(x) = x_i - clip(x_i + du_i(x), 0, 1)

F(x) = 0 holds exactly when every coordinate is a best response --
x_i = 0 with du_i <= 0, or x_i = 1 with du_i >= 0, or 0 < x_i < 1 with
du_i = 0 -- so one formulation covers all three cases and the solver never has
to be told which is which.

The Jacobian is cheap for the same reason solve2's is: utilities are multilinear
in each coordinate, so dG/dx_s = grads_own(x | x_s=1) - grads_own(x | x_s=0)
exactly, no finite differences.  Then

    dF_i/dx_s = -dG_i/dx_s        where 0 < x_i + du_i < 1
    dF_i/dx_s = delta_is          where the clip is active

A converged point is only ever a CANDIDATE here; it earns the name equilibrium
from eqtools.expl, never from this residual.
"""
import numpy as np, bgrad

STEPS = np.array([1.0, 0.5, 0.2, 0.05, 0.01])


def resid(P, G=None):
    if G is None:
        G = bgrad.grads_own(P)
    return P - np.clip(P + G, 0.0, 1.0), G


def solve(P0, rng, iters=40, jac_every=3, lam=1e-9, tol=1e-12, kick=0.05):
    """Batched LM from starting points P0 (B,48).  Returns (P, |F|_inf)."""
    P = np.clip(np.asarray(P0, float).copy(), 0.0, 1.0)
    B = P.shape[0]
    J = np.zeros((B, 48, 48))
    eye = lam * np.eye(48)
    act = np.ones(B, bool)
    for it in range(iters):
        ai = np.flatnonzero(act)
        if ai.size == 0:
            break
        Pa = P[ai]
        F, G = resid(Pa)
        cur = np.abs(F).max(axis=1)
        done = cur < tol
        if done.any():
            act[ai[done]] = False
            keep = ~done
            if not keep.any():
                break
            ai = ai[keep]; Pa = Pa[keep]; F = F[keep]; G = G[keep]; cur = cur[keep]
        S = Pa + G
        free = (S > 0.0) & (S < 1.0)          # clip inactive -> F_i = -G_i
        if it % jac_every == 0:
            Jn = np.zeros((len(ai), 48, 48))
            for s in range(48):
                P1 = Pa.copy(); P1[:, s] = 1.0
                P0_ = Pa.copy(); P0_[:, s] = 0.0
                Jn[:, :, s] = bgrad.grads_own(P1) - bgrad.grads_own(P0_)
            J[ai] = Jn
        Ja = -J[ai] * free[:, :, None]
        idx = np.arange(48)
        Ja[:, idx, idx] = np.where(free, Ja[:, idx, idx], 1.0)
        A = Ja.transpose(0, 2, 1) @ Ja + eye
        d = np.linalg.solve(A, -(Ja.transpose(0, 2, 1) @ F[:, :, None]))[:, :, 0]
        n = len(ai); ns = len(STEPS)
        Q = np.repeat(Pa, ns, axis=0) + np.tile(STEPS, n)[:, None] * np.repeat(d, ns, axis=0)
        np.clip(Q, 0.0, 1.0, out=Q)
        Fq, _ = resid(Q)
        rq = np.abs(Fq).max(axis=1).reshape(n, ns)
        b = rq.argmin(axis=1)
        newP = Q.reshape(n, ns, 48)[np.arange(n), b]
        imp = rq[np.arange(n), b] < cur
        P[ai[imp]] = newP[imp]
        if (~imp).any():                       # stuck: random kick, stay in [0,1]
            st = ai[~imp]
            P[st] = np.clip(P[st] + rng.normal(0, kick, (len(st), 48)), 0.0, 1.0)
    F, _ = resid(P)
    return P, np.abs(F).max(axis=1)
