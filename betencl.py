"""Rigorous enclosure of the P1-betting region from the surviving boxes.

The feas.py boxes all hit maxdepth=26, so they are coarse -- but coarse is not
unsound.  Every box that propagation could not kill is still there, so the UNION
of the boxes for a tag contains every equilibrium of that tag's region.  Two
things follow without any further search, and both are proofs rather than
searches:

  * coordinate enclosure:  min(LO) .. max(HI) per coordinate bounds every
    equilibrium with (say) a11 in [0.25,1];
  * utility enclosure:  ivl.util_box is an outer bound on (u1,u2,u3) over a box,
    so the min/max over all boxes bounds the payoffs of any such equilibrium.

A coordinate that comes back pinned is forced on the whole region -- that is how
Table 2 shows up here, and it doubles as a control: if Table 2's 21 values were
not pinned in every box, the box set would be wrong.

usage:  python betencl.py <workers> <tag> [tag ...]
"""
import numpy as np, sys, time, ivl, kuhn3p as K
from multiprocessing import Pool

CH = 20000
NAME = K.PARAM_NAME


def one(tag):
    lo = np.load("fbox_lo_%s.npy" % tag, mmap_mode='r')
    hi = np.load("fbox_hi_%s.npy" % tag, mmap_mode='r')
    n = lo.shape[0]
    cl = np.full(48, np.inf); ch = np.full(48, -np.inf)
    ul = np.full(3, np.inf); uh = np.full(3, -np.inf)
    t0 = time.time()
    for s in range(0, n, CH):
        L = np.asarray(lo[s:s+CH], float); H = np.asarray(hi[s:s+CH], float)
        cl = np.minimum(cl, L.min(axis=0)); ch = np.maximum(ch, H.max(axis=0))
        a, b = ivl.util_box(L, H)
        ul = np.minimum(ul, a.min(axis=0)); uh = np.maximum(uh, b.max(axis=0))
        if (s // CH) % 50 == 0:
            print("   [%s] %d/%d  %.0fs" % (tag, s, n, time.time() - t0), flush=True)
    np.savez("encl_%s.npz" % tag, cl=cl, ch=ch, ul=ul, uh=uh, n=n)
    return tag, n, cl, ch, ul, uh, time.time() - t0


if __name__ == "__main__":
    nw = int(sys.argv[1]); tags = sys.argv[2:]
    k = 1 / 24
    with Pool(nw) as pool:
        for tag, n, cl, ch, ul, uh, dt in pool.imap_unordered(one, tags):
            print("\n=== %s : %d boxes  %.0fs" % (tag, n, dt), flush=True)
            print("    u1 [%+.6f, %+.6f]   family [%+.6f, %+.6f]"
                  % (ul[0], uh[0], -k*.75, -k*.5), flush=True)
            print("    u2 [%+.6f, %+.6f]   family  %+.6f"
                  % (ul[1], uh[1], -k*.5), flush=True)
            print("    u3 [%+.6f, %+.6f]   family [%+.6f, %+.6f]"
                  % (ul[2], uh[2], k, k*1.25), flush=True)
            forced = [(NAME[i], cl[i]) for i in range(48) if ch[i] - cl[i] <= 0]
            print("    coordinates FORCED on the whole region (%d): %s"
                  % (len(forced), ", ".join("%s=%g" % f for f in forced)), flush=True)
            part = [(NAME[i], cl[i], ch[i]) for i in range(48)
                    if 0 < ch[i] - cl[i] < 1.0]
            print("    partially constrained (%d): %s"
                  % (len(part), ", ".join("%s in [%.4g,%.4g]" % p for p in part)), flush=True)
    print("\nDONE", flush=True)
