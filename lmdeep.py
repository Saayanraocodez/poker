"""Aggressive LM on the UNDECIDED silent patterns.

After the depth-36 proof chain, 13,779 patterns remain that bisection could not
prove infeasible and that pipe2's LM (one start, from the box centre, 14 iters)
found no point in.  That is the honest remainder of the branch.  Two things it
could be: infeasible-but-hard-to-prove, or feasible-but-hard-to-find.  The
second would be a new equilibrium -- possibly outside the family -- so it is
worth a search far more aggressive than the one that failed.

Same machinery as lmscreen.py (screen2.screen), but many random starts per
pattern, more iterations, small jobs for parallelism, and every survivor is
polished with solve2 and CERTIFIED by eqtools.expl before it counts.

usage:  python lmdeep.py <patterns.npy> <workers> <starts> <tag>
"""
import numpy as np, sys, time
from multiprocessing import Pool
import screen2 as screen, solve2, eqtools as E, classify

def _job(a):
    lo, hi, path, seed, starts = a
    P = np.load(path, mmap_mode='r')[lo:hi].astype(np.int8)
    rng = np.random.default_rng(seed)
    best = None
    for k in range(starts):
        x0 = np.full(P.shape, 0.5) if k == 0 else None
        X, r = screen.screen(P, rng, iters=40, jac_every=8, x0=x0)
        if best is None: best = (X, r)
        else:
            m = r < best[1]; best[0][m] = X[m]; best[1][m] = r[m]
    X, r = best
    out = []
    g = np.flatnonzero(r < 1e-6)
    if len(g):
        Pp, rp = solve2.solve(P[g].astype(np.int64), rng, iters=60, x0=X[g], tol=1e-14)
        for q, pat in zip(Pp, P[g]):
            ex = float(np.abs(E.expl(q)).max())
            out.append((pat, q, ex))
    return out, P.shape[0], float(r.min())

if __name__ == "__main__":
    path, nw, starts, tag = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    N = np.load(path, mmap_mode='r').shape[0]
    step = 200
    jobs = [(i, min(i+step, N), path, 7919*i+1, starts) for i in range(0, N, step)]
    print("patterns %d  jobs %d  starts/pattern %d  workers %d" % (N, len(jobs), starts, nw), flush=True)
    t0 = time.time(); cand = []; tot = 0; rmin = np.inf
    with Pool(nw) as pool:
        for k, (out, nt, rm) in enumerate(pool.imap_unordered(_job, jobs)):
            cand += out; tot += nt; rmin = min(rmin, rm)
            if k % 10 == 0 or out:
                print("  %d/%d  scanned %d  LM-feasible %d  certified %d  best residual %.2e  %.0fs"
                      % (k+1, len(jobs), tot, len(cand), sum(1 for c in cand if c[2] < 1e-13), rmin, time.time()-t0), flush=True)
    print("\nTOTAL scanned %d   LM-feasible candidates %d   CERTIFIED Nash %d   best residual %.3e   %.0fs"
          % (tot, len(cand), sum(1 for c in cand if c[2] < 1e-13), rmin, time.time()-t0), flush=True)
    if cand:
        Q = np.array([c[1] for c in cand]); ex = np.array([c[2] for c in cand])
        np.save("lmdeep_x_%s.npy" % tag, Q); np.save("lmdeep_pat_%s.npy" % tag, np.array([c[0] for c in cand]))
        cert = Q[ex < 1e-13]
        if len(cert):
            fg = np.array([classify.family_gap(q) for q in cert])
            print("certified: %d   family gap max %.3e   OUTSIDE family (>1e-9): %d" % (len(cert), fg.max(), (fg > 1e-9).sum()), flush=True)
