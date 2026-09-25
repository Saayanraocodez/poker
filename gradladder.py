"""Depth ladder under the `grad` split rule.

The width rule's ladder settles at ~1.5x boxes per level, which is what kills
the refinement route: a real wtol=0.06 needs ~104 more levels.  At depth 22 the
`grad` rule (split the coordinate whose own gradient bound is loosest, weighted
by width) gives 111,627 boxes against width's 337,074 -- 3.0x fewer.

A constant 3x is worth little on its own.  What matters is whether the GROWTH
PER LEVEL is lower, because that is the exponent.  This runs the same ladder
under `grad` so the two exponents can be compared directly.

Boxes are counted through a sink and discarded -- at depth 30 keeping them would
be gigabytes, and only the count is wanted.

usage:  python gradladder.py <workers> <depth> [depth ...]
"""
import numpy as np, sys, time, bnb5, splitrule, kuhn3p as K
from multiprocessing import Pool

I = K.NAME_IDX


def job(depth):
    LO = np.zeros(48); HI = np.ones(48)
    for n, lo, hi in splitrule.CONS:
        LO[I[n]] = lo; HI[I[n]] = hi
    cnt = [0]

    def sink(a, b):
        cnt[0] += a.shape[0]

    t0 = time.time()
    st, _ = bnb5.search(LO0=LO, HI0=HI, wtol=0.06, maxdepth=depth, cap=4096,
                        maxnodes=200000000, log=None, sink=sink,
                        objsplit=splitrule.mk("grad"), tag="d%d" % depth)
    return depth, st, cnt[0], time.time() - t0


if __name__ == "__main__":
    nw = int(sys.argv[1]); depths = [int(x) for x in sys.argv[2:]]
    print("bet_a41_lo, split rule = grad\n", flush=True)
    print("%6s %12s %12s %8s %8s" % ("depth", "nodes", "boxes", "abort", "sec"), flush=True)
    res = {}
    with Pool(nw) as pool:
        for depth, st, nb, dt in pool.imap_unordered(job, depths):
            res[depth] = nb
            print("%6d %12d %12d %8s %8.0f"
                  % (depth, st['nodes'], nb, st.get('ABORT', False), dt), flush=True)
    ds = sorted(res)
    print("\ngrowth per level:", flush=True)
    for a, b in zip(ds, ds[1:]):
        if res[a] > 0:
            print("   %d -> %d : x%.3f over %d levels = %.3f/level"
                  % (a, b, res[b] / res[a], b - a, (res[b] / res[a]) ** (1.0 / (b - a))),
                  flush=True)
