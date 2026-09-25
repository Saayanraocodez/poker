"""Support patterns implied by the P1-betting box cover, one file per tag.

The 36.1M feas.py boxes cost about five CPU-days and are a rigorous COVER of
the betting region: every equilibrium with a_j1 >= 0.02 lies in one of them.
They are far too coarse to certify anything themselves (all emitted on
maxdepth, width 0.5, and their enclosure recovers nothing beyond Table 2), but
each box does imply a support pattern, and those patterns can go through the
same bisection+LM pipeline that settled the silent branch -- where the
bisection stage PROVES infeasibility rather than merely failing to find a point.

Two readings per box, because one is not enough:

  A "interior"  every unpinned coordinate is MIX (du = 0).
                Catches an equilibrium strictly inside the box.
  B "boundary"  lo == 0 & hi < 1 -> 0 ;  lo > 0 & hi == 1 -> 1 ;
                0 < lo, hi < 1   -> MIX.
                Catches an equilibrium on a face the box was split at.

Neither is a support COVER: an equilibrium mixing boundary and interior
coordinates has a pattern in neither set.  So this is a SEARCH over a rigorous
cover, not a proof of emptiness -- the same standing as s15.4's LM stage, and
it is written down that way rather than dressed up.

Dedup is per tag, not global.  A running global unique would re-sort a
35M x 48 array on every chunk; per tag it is a single np.unique on at most
~15M rows, which fits, and cross-tag duplicates are rare because the tags carry
disjoint constraint ranges.

usage:  python boxpats.py <tag> [tag ...]
"""
import numpy as np, sys, time, os, bnb, kuhn3p as K

MIX = bnb.MIX
CH = 500000
I = K.NAME_IDX
OPEN = [I[n] for n in ("a11", "a21", "a31", "a41")]


def patterns(L, H):
    pin1 = (L >= 1.0)
    pin0 = (H <= 0.0)
    A = np.full(L.shape, MIX, np.int8)
    A[pin1] = 1
    A[pin0] = 0
    B = A.copy()
    B[(L <= 0.0) & (H < 1.0) & ~pin0] = 0
    B[(L > 0.0) & (H >= 1.0) & ~pin1] = 1
    return A, B


def run(tag):
    out = "pats_%s.npy" % tag
    if os.path.exists(out):
        n = np.load(out, mmap_mode='r').shape[0]
        print("%-14s already done: %d patterns" % (tag, n), flush=True)
        return
    lo = np.load("fbox_lo_%s.npy" % tag, mmap_mode='r')
    hi = np.load("fbox_hi_%s.npy" % tag, mmap_mode='r')
    n = lo.shape[0]
    raw = "pats_%s.i8" % tag
    t0 = time.time()
    with open(raw, "wb") as f:
        for s in range(0, n, CH):
            L = np.asarray(lo[s:s+CH], float); H = np.asarray(hi[s:s+CH], float)
            A, B = patterns(L, H)
            A.tofile(f); B.tofile(f)
        f.flush(); os.fsync(f.fileno())
    m = os.path.getsize(raw) // 48
    P = np.fromfile(raw, dtype=np.int8).reshape(m, 48)
    P = np.unique(P, axis=0)
    np.save(out, P)
    os.remove(raw)
    bets = ((P[:, OPEN] == 1) | (P[:, OPEN] == MIX)).any(axis=1)
    print("%-14s %9d boxes -> %9d patterns -> %9d distinct   P1 bets in %d (%.1f%%)   %.0fs"
          % (tag, n, m, len(P), bets.sum(), 100 * bets.mean(), time.time() - t0),
          flush=True)


if __name__ == "__main__":
    for t in sys.argv[1:]:
        run(t)
    print("DONE", flush=True)
