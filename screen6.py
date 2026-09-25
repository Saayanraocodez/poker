"""LM screen of the leaves prove6pat could not prove, seeded from their
contracted boxes, with certification by eqtools.expl and on-path classification
by classify.family_gap (plus the off-path census offpath.py taught us to do).

usage:  python screen6.py <tag> <workers> <starts>
"""
import numpy as np, sys, time
from multiprocessing import Pool
import screen2 as screen, solve2, eqtools as E, classify, kuhn3p as K

I = K.NAME_IDX
MIX, DC = 2, 3


def _job(a):
    P, LO, HI, seed, starts = a
    rng = np.random.default_rng(seed)
    var = (P == MIX) | (P == DC)
    best = None
    for k in range(starts):
        if k == 0: x0 = 0.5 * (LO + HI)
        else:      x0 = LO + (HI - LO) * rng.random(P.shape)
        X, r = screen.screen(P, rng, iters=40, jac_every=8, x0=x0)
        if best is None: best = (X, r)
        else:
            m = r < best[1]; best[0][m] = X[m]; best[1][m] = r[m]
    X, r = best
    out = []
    g = np.flatnonzero(r < 1e-6)
    if len(g):
        Pp, rp = solve2.solve(P[g].astype(np.int64), rng, iters=60, x0=X[g], tol=1e-14)
        for q, pat, gi in zip(Pp, P[g], g):
            out.append((pat, q, float(np.abs(E.expl(q)).max())))
    return out, len(P), float(r.min())


if __name__ == "__main__":
    tag, nw, starts = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    z = np.load("prove6pat_%s.npz" % tag)
    L = np.load("enum6_pat_%s.npy" % tag).astype(np.int8)
    und = np.flatnonzero(~z["proven"])
    P = L[und]; LO = z["bestlo"][und]; HI = z["besthi"][und]
    print("undecided leaves %d  starts/leaf %d  workers %d" % (len(P), starts, nw), flush=True)
    step = 50
    jobs = [(P[i:i+step], LO[i:i+step], HI[i:i+step], 104729 * i + 7, starts) for i in range(0, len(P), step)]
    t0 = time.time(); cand = []; tot = 0; rmin = np.inf
    with Pool(nw) as pool:
        for k, (out, n, rm) in enumerate(pool.imap_unordered(_job, jobs)):
            cand += out; tot += n; rmin = min(rmin, rm)
            if k % 10 == 0 or out:
                print("  %d/%d  scanned %d  LM-feasible %d  certified %d  best residual %.2e  %.0fs"
                      % (k + 1, len(jobs), tot, len(cand), sum(1 for c in cand if c[2] < 1e-13), rmin, time.time() - t0), flush=True)
    ncert = sum(1 for c in cand if c[2] < 1e-13)
    print("\nTOTAL scanned %d   LM-feasible %d   CERTIFIED Nash %d   best residual %.3e   %.0fs" % (tot, len(cand), ncert, rmin, time.time() - t0), flush=True)
    if cand:
        Q = np.array([c[1] for c in cand]); ex = np.array([c[2] for c in cand]); Pc = np.array([c[0] for c in cand])
        np.save("screen6_x_%s.npy" % tag, Q); np.save("screen6_pat_%s.npy" % tag, Pc); np.save("screen6_ex_%s.npy" % tag, ex)
        cert = Q[ex < 1e-13]
        if len(cert):
            fg = np.array([classify.family_gap(q) for q in cert])
            op = cert[:, [I[n] for n in ("a11", "a21", "a31", "a41")]].max(axis=1)
            print("certified: %d   on-path family gap max %.3e   OUTSIDE family on path (>1e-9): %d   max P1 opening frequency %.2e"
                  % (len(cert), fg.max(), (fg > 1e-9).sum(), op.max()), flush=True)
