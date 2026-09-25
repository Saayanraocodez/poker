"""How many support patterns does a branch actually have?  (Knuth estimator.)

`runsilent.py` took 525 s to enumerate the P1-silent branch because that branch
has 3,045,358 patterns.  A P1-BETTING branch has more live coordinates, and the
question is whether it has 10^7 patterns (screenable in days by the same
pipeline) or 10^10 (not screenable at all).  Running the enumeration to find out
is the thing we cannot afford, so estimate instead.

Knuth 1975: walk a single random root-to-leaf path, multiplying the number of
surviving children at each node.  The product is an UNBIASED estimator of the
number of leaves; average over many walks.  Each walk is ~25 propagate calls on
three rows, so thousands of walks cost less than one second of the real search.

The estimator is unbiased but heavy-tailed, so the mean is reported with a
standard error and the quantiles alongside it -- a mean far above the median is
the signature of a few very heavy paths, and means the mean is the number to
trust for total size while the median describes a typical path.

CONTROL: the silent branch has a known answer, 3,045,358.  An estimator that
cannot reproduce that is not to be believed about anything else.

usage:  python treesize.py <walks> <workers> [spec ...]
        spec = coord:label, e.g. a11:MIX ; 'silent' = a11..a41 all 0
"""
import numpy as np, sys, time, bnb, kuhn3p as K
from multiprocessing import Pool

I = K.NAME_IDX
U, MIX = bnb.U, bnb.MIX
ORDER = [I[n] for n in ("c11", "c21", "c31", "c41", "b11", "b21", "b31", "b41",
                        "a22", "a32", "a33", "a34", "a23",
                        "b22", "b23", "b32", "b33", "b34",
                        "c22", "c23", "c32", "c33", "c34",
                        "a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24",
                        "c12", "c13", "c14", "c24", "a42", "a43", "a44",
                        "b42", "b43", "b44", "c42", "c43", "c44",
                        "a11", "a21", "a31", "a41")]
LABV = {"0": 0, "1": 1, "MIX": MIX}


def root_of(spec):
    lab = np.full(48, U)
    if spec == "silent":
        for n in ("a11", "a21", "a31", "a41"):
            lab[I[n]] = 0
    else:
        for part in spec.split(","):
            c, l = part.split(":")
            lab[I[c]] = LABV[l]
    return lab


def walk(a):
    """One random root-to-leaf path; returns the Knuth weight."""
    spec, seed = a
    rng = np.random.default_rng(seed)
    lab = root_of(spec)[None, :].copy()
    lab, al = bnb.propagate(lab)
    if not al[0]:
        return 0.0
    w = 1.0
    while True:
        u = np.flatnonzero(lab[0] == U)
        if u.size == 0:
            return w
        # branch on the earliest unassigned coordinate in ORDER, as bnb.run does
        v = next(x for x in ORDER if lab[0, x] == U)
        kids = bnb.expand(lab, v)
        kids, al = bnb.propagate(kids)
        kids = kids[al]
        c = kids.shape[0]
        if c == 0:
            return 0.0
        w *= c
        lab = kids[rng.integers(c)][None, :].copy()


if __name__ == "__main__":
    nwalk = int(sys.argv[1]); nw = int(sys.argv[2])
    specs = sys.argv[3:] or ["silent", "a11:MIX", "a21:MIX", "a11:1"]
    with Pool(nw) as pool:
        for spec in specs:
            t0 = time.time()
            W = np.array(pool.map(walk, [(spec, s) for s in range(nwalk)]))
            m = W.mean(); se = W.std(ddof=1) / np.sqrt(len(W))
            nz = (W > 0).mean()
            q = np.percentile(W[W > 0], [50, 90, 99]) if (W > 0).any() else [0, 0, 0]
            print("%-14s leaves ~ %.3e  +/- %.1e (se)   nonzero paths %.1f%%   "
                  "median %.2e  p90 %.2e  p99 %.2e   %.0fs"
                  % (spec, m, se, 100 * nz, q[0], q[1], q[2], time.time() - t0),
                  flush=True)
