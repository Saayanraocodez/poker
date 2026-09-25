"""What does deeper bisection buy in PROOF on the P1-silent branch?

The silent branch is exhaustively enumerated and screened, but only 80.3 % of its
3,045,358 patterns are PROVEN infeasible.  The other 19.7 % rest on LM failing to
find a point, which is not a proof -- that gap is the whole distance between
"the search found nothing outside the family" and "nothing outside the family
exists here".

The proving stage is `bisbatch.bisect`, and `pipe2` ran it at depth=8.  Depth is
a single argument.  This measures the marginal proof rate per extra level on a
sample, so the cost of closing the gap can be estimated before committing.

Note `bisect` also has `keepcap=60000`, which aborts the refinement of a block
once it holds too many boxes; if the proof rate stalls, that cap is the suspect,
not the depth.

usage:  python depthproof.py <sample> <depth> [depth ...]
"""
import numpy as np, sys, time, bisbatch

if __name__ == "__main__":
    n = int(sys.argv[1]); depths = [int(x) for x in sys.argv[2:]]
    P = np.load("pats_rest.npy", mmap_mode='r')
    idx = np.linspace(0, P.shape[0] - 1, n).astype(np.int64)
    blk = np.asarray(P[idx]).astype(np.int8)
    print("sample %d of %d patterns from pats_rest.npy\n" % (n, P.shape[0]), flush=True)
    print("%6s %14s %12s %10s" % ("depth", "proven", "boxes left", "sec"), flush=True)
    prev = None
    for d in depths:
        t0 = time.time()
        proven = 0; boxes = 0
        CH = 1024
        for s in range(0, blk.shape[0], CH):
            b = blk[s:s+CH]
            pid, lab, LO, HI = bisbatch.bisect(b, depth=d)
            proven += b.shape[0] - len(np.unique(pid))
            boxes += len(pid)
        pct = 100.0 * proven / n
        delta = "" if prev is None else "  (%+.2f pp)" % (pct - prev)
        prev = pct
        print("%6d %8d (%.2f%%)%s %12d %10.0f"
              % (d, proven, pct, delta, boxes, time.time() - t0), flush=True)
