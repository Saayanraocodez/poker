"""From surviving interval boxes: rigorous enclosures + certified equilibria."""
import numpy as np, sys, ivl, bnb2, screen, solve2, bgrad, eqtools as E, classify, kuhn3p as K
I = K.NAME_IDX

def enclosure(LAB, LO, HI):
    """rigorous coordinate-wise enclosure of the equilibrium set"""
    return LO.min(axis=0), HI.max(axis=0)

def util_bounds(LO, HI, chunk=2048):
    lo = np.full(3, np.inf); hi = np.full(3, -np.inf)
    for s in range(0, LO.shape[0], chunk):
        ul, uh = ivl.util_box(LO[s:s+chunk], HI[s:s+chunk])
        lo = np.minimum(lo, ul.min(axis=0)); hi = np.maximum(hi, uh.max(axis=0))
    return lo, hi

def certify(LAB, LO, HI, rng, starts=4, chunk=1024):
    """LM from box centres + random points in the box; keep exact equilibria."""
    good = []
    for s in range(0, LAB.shape[0], chunk):
        lab = LAB[s:s+chunk]; lo = LO[s:s+chunk]; hi = HI[s:s+chunk]
        for k in range(starts):
            x0 = 0.5*(lo+hi) if k == 0 else lo + rng.random(lo.shape)*(hi-lo)
            X, r = screen.screen(lab, rng, iters=25, jac_every=5, x0=x0)
            m = r < 1e-11
            if m.any(): good.append(X[m])
    if not good: return np.zeros((0,48))
    return np.concatenate(good)

def summarize(X, tag=""):
    sig = {}
    for p in X:
        ex = np.abs(E.expl(p)).max()
        if ex > 1e-12: continue
        sig.setdefault(classify.signature(p), p)
    print("%s certified Nash: %d  distinct leaf-distributions: %d" % (tag, len(sig), len(sig)))
    if not sig: return {}
    U = np.array([E.util(p) for p in sig.values()])
    print("   u1 [%.9f, %.9f]" % (U[:,0].min(), U[:,0].max()))
    print("   u2 [%.9f, %.9f]" % (U[:,1].min(), U[:,1].max()))
    print("   u3 [%.9f, %.9f]" % (U[:,2].min(), U[:,2].max()))
    fg = np.array([classify.family_gap(p) for p in sig.values()])
    print("   family gap: max %.3e   outside-family (gap>1e-9): %d" % (fg.max(), (fg > 1e-9).sum()))
    return sig
