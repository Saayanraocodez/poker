import numpy as np, time, bnb, branchrun, solvepat, eqtools as E, kuhn3p as K, family as F
lab = np.full(48, bnb.U)
for n in ("a11","a21","a31","a41"): lab[K.NAME_IDX[n]] = 0
pats, st = bnb.run(lab, branchrun.ORDER, cap=4096, maxnodes=60000)
print("sample patterns", pats.shape, st, flush=True)
rng = np.random.default_rng(0)
sel = pats[rng.choice(len(pats), size=min(3000, len(pats)), replace=False)]
t = time.time()
P, r = solvepat.solve_batch(sel, rng)
print("solve %.1fs  resid<1e-12: %d/%d" % (time.time()-t, (r < 1e-12).sum(), len(r)), flush=True)
ok = solvepat.check(P) & (r < 1e-12)
print("first-order Nash:", ok.sum())
if ok.sum():
    idx = np.flatnonzero(ok)
    ex = np.array([E.expl(P[i]) for i in idx])
    good = idx[np.abs(ex).max(axis=1) < 1e-12]
    print("TRUE Nash (zero exploitability):", len(good), "of", len(idx))
    W = np.round(np.array([E.leafw(P[i]) for i in good]), 9)
    uw = np.unique(W, axis=0)
    print("distinct leaf distributions:", len(uw))
    U = np.array([E.util(P[i]) for i in good])
    print("distinct utility vectors:", len(np.unique(np.round(U,10),axis=0)))
    print("u2 range", U[:,1].min(), U[:,1].max(), " (family: -1/48 =", -1/48, ")")
    np.save("sample_eq.npy", P[good])
