"""Per-leaf bisection with bnb6's contracting propagation (sequential-sound).

Input: enum6 leaves (label pattern + contracted box).  For each leaf, a DFS
that splits the (condition, coordinate) pair the contractor rates most likely
to decide -- bnb6.choose_split -- and propagates with du_i = 0 imposed on every
MIX coordinate.  A leaf is PROVEN when its whole tree dies; otherwise the
surviving boxes are returned (their centres seed the LM screen in screen6.py).

Unlike bisbatch.bisect this splits DC coordinates too (an unreachable
coordinate is still a variable in other players' incentives), and there is no
shared keepcap: every leaf gets the same node budget.

usage:  python prove6pat.py <tag> <workers> <maxnodes_per_leaf> [outtag] [index.npy]
"""
import numpy as np, sys, time
from multiprocessing import Pool
import bnb6, treesize6 as T6

U, MIX, DC = T6.U, T6.MIX, T6.DC


def prove_leaf(a):
    lab, LO, HI, maxnodes = a
    mix = (lab == MIX)
    stack = [(LO[None].copy(), HI[None].copy())]
    nodes = 0; best = None
    while stack:
        lo, hi = stack.pop()
        while stack and lo.shape[0] < 64:
            l2, h2 = stack.pop(); lo = np.concatenate([lo, l2]); hi = np.concatenate([hi, h2])
        nodes += lo.shape[0]
        lo, hi, al, DLO, DHI, SL, SK = bnb6.propagate(lo, hi, weak=T6.WEAK, hyp_ge=mix, hyp_le=mix)
        lo, hi, SL, SK = lo[al], hi[al], SL[al], SK[al]
        # a MIX coordinate whose box collapsed to 0 or 1 contradicts 'interior'
        okm = ~(((lo >= 1.0) | (hi <= 0.0)) & mix[None, :]).any(axis=1)
        lo, hi, SL, SK = lo[okm], hi[okm], SL[okm], SK[okm]
        if lo.shape[0] == 0: continue
        W = hi - lo
        wmax = W.max(axis=1)
        k = int(wmax.argmin())
        if best is None or wmax[k] < best[0]: best = (float(wmax[k]), lo[k].copy(), hi[k].copy())
        if nodes > maxnodes:
            stack.append((lo, hi))
            left = sum(s[0].shape[0] for s in stack)
            return False, nodes, left, best
        j = bnb6.choose_split(lo, hi, SL, SK, "slope")
        for jj in np.unique(j):
            m = j == jj
            b_, c_ = lo[m], hi[m]
            mid = 0.5 * (b_[:, jj] + c_[:, jj])
            Bl = np.repeat(b_, 2, axis=0); Ch = np.repeat(c_, 2, axis=0)
            Ch[0::2, jj] = mid; Bl[1::2, jj] = mid
            stack.append((Bl, Ch))
    return True, nodes, 0, best


if __name__ == "__main__":
    tag, nw, maxnodes = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    out = sys.argv[4] if len(sys.argv) > 4 else tag
    L = np.load("enum6_pat_%s.npy" % tag).astype(np.int8)
    A = np.load("enum6_lo_%s.npy" % tag); B = np.load("enum6_hi_%s.npy" % tag)
    if len(sys.argv) > 5:                      # optional index file: prove only these leaves
        sel = np.load(sys.argv[5]); L, A, B = L[sel], A[sel], B[sel]
        np.save("prove6pat_idx_%s.npy" % out, sel)
        print("restricted to %d leaves from %s" % (len(sel), sys.argv[5]), flush=True)
    print("leaves %d  workers %d  node budget %d per leaf  mode %s" % (len(L), nw, maxnodes, "seq" if T6.WEAK else "nash"), flush=True)
    t0 = time.time()
    proven = np.zeros(len(L), bool); nodes = np.zeros(len(L), np.int64); left = np.zeros(len(L), np.int64)
    bestlo = A.copy(); besthi = B.copy(); bestw = np.full(len(L), np.inf)
    with Pool(nw) as pool:
        for k, (pv, n, lf, best) in enumerate(pool.imap(prove_leaf, [(L[i], A[i], B[i], maxnodes) for i in range(len(L))], chunksize=4)):
            proven[k] = pv; nodes[k] = n; left[k] = lf
            if best is not None:
                bestw[k], bestlo[k], besthi[k] = best
            if (k + 1) % 200 == 0 or k + 1 == len(L):
                print("   %d/%d  proven %d  (%.1f%%)  nodes %d  %.0fs" % (k + 1, len(L), proven[:k+1].sum(), 100 * proven[:k+1].mean(), nodes.sum(), time.time() - t0), flush=True)
    np.savez("prove6pat_%s.npz" % out, proven=proven, nodes=nodes, left=left, bestlo=bestlo, besthi=besthi, bestw=bestw)
    print("\nTOTAL leaves %d   PROVEN infeasible %d (%.2f%%)   undecided %d   nodes %d   %.0fs" % (len(L), proven.sum(), 100 * proven.mean(), (~proven).sum(), nodes.sum(), time.time() - t0), flush=True)
    if (~proven).any():
        print("undecided: smallest surviving box width  min %.2e  median %.2e  max %.2e" % (bestw[~proven].min(), np.median(bestw[~proven]), bestw[~proven].max()))
