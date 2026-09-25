import numpy as np, bnb, solvepat, bgrad, eqtools as E, kuhn3p as K, family as F
I = K.NAME_IDX
def labels_of(p, tol=1e-12):
    lab = np.where(p <= tol, 0, np.where(p >= 1-tol, 1, bnb.MIX))
    r = K.reach(p)
    lab[r <= 1e-15] = bnb.DC
    return lab.astype(np.int64)

for nm, p in [("A(1/8,1/4)", F.profile_A(0.125,0.25)[0]),
              ("B(1/8,0.2)",  F.profile_B(0.125,0.2)[0]),
              ("C(0.2,0.05)", F.profile_C(0.2,0.05)[0]),
              ("A(0,0)",      F.profile_A(0.0,0.0)[0])]:
    lab = labels_of(p)
    mix = [K.PARAM_NAME[i] for i in range(48) if lab[i]==bnb.MIX]
    dc  = [K.PARAM_NAME[i] for i in range(48) if lab[i]==bnb.DC]
    l2, alive = bnb.propagate(lab[None,:].copy())
    consistent = alive[0] and np.array_equal(l2[0], lab)
    print("%-12s MIX(%d)=%s" % (nm, len(mix), ",".join(mix)))
    print("             DC(%d)=%s" % (len(dc), ",".join(dc)))
    print("             survives propagation: %s (alive=%s, unchanged=%s)"
          % (consistent, alive[0], np.array_equal(l2[0], lab)))
    if alive[0] and not np.array_equal(l2[0],lab):
        for i in range(48):
            if l2[0,i]!=lab[i]: print("               changed", K.PARAM_NAME[i], lab[i],"->",l2[0,i])
    print("             firstorder-check on exact profile:", solvepat.check(p[None,:])[0],
          " expl", np.abs(E.expl(p)).max())
    # can the solver recover it from random starts?
    rng = np.random.default_rng(1)
    pats = np.repeat(lab[None,:], 200, axis=0)
    P, r = solvepat.solve_batch(pats, rng, drop=False)
    ok = solvepat.check(P) & (r < 1e-12)
    print("             solver: resid<1e-12 %d/200, first-order-ok %d, "
          "true-Nash %d" % ((r<1e-12).sum(), ok.sum(),
          sum(1 for i in np.flatnonzero(ok)[:50] if np.abs(E.expl(P[i])).max()<1e-12)))
