import numpy as np, bnb, solve2, kuhn3p as K, family as F, eqtools as E
def labels_of(p, tol=1e-12):
    lab = np.where(p <= tol, 0, np.where(p >= 1-tol, 1, bnb.MIX))
    lab[K.reach(p) <= 1e-15] = bnb.DC
    return lab.astype(np.int64)
rng = np.random.default_rng(2)
for nm, p in [("A(1/8,1/4)", F.profile_A(0.125,0.25)[0]),
              ("B(1/8,0.2)",  F.profile_B(0.125,0.2)[0]),
              ("C(0.2,0.05)", F.profile_C(0.2,0.05)[0]),
              ("A(0,0)",      F.profile_A(0.0,0.0)[0])]:
    lab = labels_of(p)
    pats = np.repeat(lab[None,:], 300, axis=0)
    P, r = solve2.solve(pats, rng)
    hit = r < 1e-11
    ex = np.array([np.abs(E.expl(P[i])).max() for i in np.flatnonzero(hit)[:80]])
    print("%-12s feasible %3d/300   true-Nash among first 80: %d   max expl %.2e"
          % (nm, hit.sum(), (ex < 1e-12).sum() if len(ex) else 0,
             ex.max() if len(ex) else -1))
