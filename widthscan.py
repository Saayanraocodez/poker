"""Were the emitted boxes finished by width tolerance, or by the depth cap?

feas.py ran every task with wtol=0.06 and maxdepth=26.  bnb5 emits a box when
`W.max < wtol OR depth >= maxdepth`, so those two settings are only coherent if
26 splits can drive ~26 free coordinates below 0.06 -- they cannot: 26 splits is
about one halving per coordinate, and 0.06 needs five.  If every emitted box is
wider than wtol, then NO box was emitted on the tolerance and the verdict
"open: N boxes" means "ran out of depth", not "refined and survived".

Reads the fbox pair for each tag in chunks; nothing is held in RAM.
"""
import numpy as np, sys, os

WTOL = 0.06
CH = 200000

def scan(tag):
    lo = np.load("fbox_lo_%s.npy" % tag, mmap_mode='r')
    hi = np.load("fbox_hi_%s.npy" % tag, mmap_mode='r')
    n = lo.shape[0]
    mn = np.inf; mx = -np.inf; nfine = 0; free = 0
    for s in range(0, n, CH):
        W = np.asarray(hi[s:s+CH]) - np.asarray(lo[s:s+CH])
        m = W.max(axis=1)
        mn = min(mn, float(m.min())); mx = max(mx, float(m.max()))
        nfine += int((m < WTOL).sum())
        free += int((W > 0).sum())
    return n, mn, mx, nfine, free / max(n, 1)

if __name__ == "__main__":
    tags = sys.argv[1:]
    print("%-14s %10s %8s %8s %12s %8s" % ("tag", "boxes", "minmaxW", "maxmaxW",
                                           "W<wtol", "free/box"), flush=True)
    tot = 0; totfine = 0
    for t in tags:
        n, mn, mx, nf, fr = scan(t)
        tot += n; totfine += nf
        print("%-14s %10d %8.4f %8.4f %12d %8.2f" % (t, n, mn, mx, nf, fr), flush=True)
    print("TOTAL boxes %d   emitted on width tolerance: %d (%.4f%%)"
          % (tot, totfine, 100 * totfine / max(tot, 1)), flush=True)
    print("=> every other box was emitted because depth hit maxdepth.", flush=True)
