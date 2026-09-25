"""Layer 1: unconstrained + constrained descent on the Nash gap."""
import numpy as np, eqtools as E, kuhn3p as K
from scipy.optimize import minimize

NP = 48
B = [(0.0, 1.0)] * NP

def polish(p0, cons=None, iters=3):
    p = np.clip(np.asarray(p0, float), 0, 1)
    for _ in range(iters):
        if cons is None:
            r = minimize(E.nashgap_grad, p, jac=True, method="L-BFGS-B",
                         bounds=B, options=dict(maxiter=3000, ftol=1e-18, gtol=1e-14))
        else:
            r = minimize(lambda x: E.nashgap_grad(x)[0], p,
                         jac=lambda x: E.nashgap_grad(x)[1],
                         method="SLSQP", bounds=B, constraints=cons,
                         options=dict(maxiter=800, ftol=1e-16))
        if not np.all(np.isfinite(r.x)): break
        p = np.clip(r.x, 0, 1)
    return p

def newton_polish(p, steps=60):
    """Newton on the active indifference system, holding the support fixed."""
    p = p.copy()
    for _ in range(steps):
        G = E.grad(p)
        free, F = [], []
        for i in range(3):
            for k in range(16):
                t = 16 * i + k
                if 1e-9 < p[t] < 1 - 1e-9:
                    free.append(t); F.append(G[t, i])
        if not free: return p
        F = np.array(F); 
        if np.abs(F).max() < 1e-15: return p
        J = np.zeros((len(free), len(free)))
        for cj, t2 in enumerate(free):
            for s in (1.0, 0.0):
                q = p.copy(); q[t2] = s
                Gs = E.grad(q)
                col = np.array([Gs[t, t // 16] for t in free])
                J[:, cj] += col if s == 1.0 else -col
        try: d = np.linalg.lstsq(J, -F, rcond=1e-8)[0]
        except Exception: return p
        step = 1.0
        base = np.abs(F).max()
        for _ in range(30):
            q = p.copy()
            for idx, t in enumerate(free): q[t] = np.clip(p[t] + step * d[idx], 0, 1)
            Gq = E.grad(q)
            nf = max(abs(Gq[t, t // 16]) for t in free)
            if nf < base: p = q; break
            step *= 0.5
        else: return p
    return p
