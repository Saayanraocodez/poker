import numpy as np, bnb, solve2, branchrun, kuhn3p as K, family as F, eqtools as E
ORDER = branchrun.ORDER
def bnb_label(p, tol=1e-12):
    """the leaf label pattern the DFS actually reaches for profile p"""
    tgt = np.where(p <= tol, 0, np.where(p >= 1-tol, 1, bnb.MIX))
    lab = np.full((1,48), bnb.U)
    while True:
        lab, alive = bnb.propagate(lab)
        assert alive[0], "propagation killed a real equilibrium!"
        u = [v for v in ORDER if lab[0,v]==bnb.U]
        if not u: return lab[0].copy()
        lab[0,u[0]] = tgt[u[0]]
rng = np.random.default_rng(2)
tests = [("A(1/8,1/4)", F.profile_A(0.125,0.25)[0]),
         ("B(1/8,0.2)",  F.profile_B(0.125,0.2)[0]),
         ("C(0.2,0.05)", F.profile_C(0.2,0.05)[0]),
         ("A(0,0)",      F.profile_A(0.0,0.0)[0]),
         ("A(1/4,1/4)",  F.profile_A(0.25,0.25)[0]),
         ("C(1/4,0)",    F.profile_C(0.25,0.0)[0])]
for nm, p in tests:
    lab = bnb_label(p)
    mix=[K.PARAM_NAME[i] for i in range(48) if lab[i]==bnb.MIX]
    dc =[K.PARAM_NAME[i] for i in range(48) if lab[i]==bnb.DC]
    pats = np.repeat(lab[None,:], 200, axis=0)
    P, r = solve2.solve(pats, rng, iters=45)
    hit = r < 1e-12
    n_nash = 0; mx = -1
    for i in np.flatnonzero(hit)[:60]:
        e = np.abs(E.expl(P[i])).max(); mx = max(mx,e); n_nash += (e < 1e-13)
    print("%-11s MIX%d %s | DC%d %s\n            feasible %3d/200  Nash %d  maxexpl %.1e"
          % (nm, len(mix), ",".join(mix), len(dc), ",".join(dc), hit.sum(), n_nash, mx))
