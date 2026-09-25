"""Does the algebraic necessary condition for a11 > 0 collapse the search?

symbet.py gives, with only Table 2 substituted,

    du1/da11 = [ 2(1-c33)(1-b22) + 2(1-c23)(1-b32) - 3 ] / 12

verified against bgrad.grads_own to 5.6e-17.  It depends on FOUR coordinates out
of 48.  Since each product lies in [0,1], a11 > 0 needs du1/da11 >= 0, hence both
products > 1/2, hence

    c33 < 1/2,  b22 < 1/2,  c23 < 1/2,  b32 < 1/2.

That is sound and it is free: restricting those four coordinates to [0, 1/2] on
the a11-betting region discards nothing.  This measures what it buys, against
the identical run without the cut, same split rule and same depth.

usage:  python betcut.py <maxdepth> <workers>
"""
import numpy as np, sys, time, bnb5, splitrule, kuhn3p as K
from multiprocessing import Pool

I = K.NAME_IDX
CUT = ("c33", "b22", "c23", "b32")


def job(a):
    name, cons, maxdepth = a
    LO = np.zeros(48); HI = np.ones(48)
    for n, lo, hi in cons:
        LO[I[n]] = lo; HI[I[n]] = hi
    cnt = [0]

    def sink(x, y):
        cnt[0] += x.shape[0]

    t0 = time.time()
    st, _ = bnb5.search(LO0=LO, HI0=HI, wtol=0.06, maxdepth=maxdepth, cap=4096,
                        maxnodes=200000000, log=None, sink=sink,
                        objsplit=splitrule.mk("grad"), tag=name)
    return name, st, cnt[0], time.time() - t0


if __name__ == "__main__":
    md = int(sys.argv[1]); nw = int(sys.argv[2])
    base = [("a11", 0.02, 0.25)]
    tasks = [("a11_lo plain", base, md),
             ("a11_lo + cut", base + [(n, 0.0, 0.5) for n in CUT], md),
             ("a11_hi plain", [("a11", 0.25, 1.0)], md),
             ("a11_hi + cut", [("a11", 0.25, 1.0)] + [(n, 0.0, 0.5) for n in CUT], md)]
    print("grad split rule, maxdepth=%d\n" % md, flush=True)
    print("%-14s %12s %12s %8s" % ("task", "nodes", "boxes", "sec"), flush=True)
    res = {}
    with Pool(nw) as pool:
        for name, st, nb, dt in pool.imap_unordered(job, tasks):
            res[name] = nb
            print("%-14s %12d %12d %8.0f"
                  % (name, st['nodes'], nb, dt), flush=True)
    print(flush=True)
    for k in ("a11_lo", "a11_hi"):
        p, c = res.get(k + " plain"), res.get(k + " + cut")
        if p and c is not None:
            print("%s: %d -> %d boxes   x%.4f" % (k, p, c, c / max(p, 1)), flush=True)
