"""Does LOOK-AHEAD propagation make the P1-betting branches tractable?

The betting branches are out of reach because of the bound, not the branching.
`treesize.py` measured 10^9-10^10 support patterns per branch with **100 % of
sampled root-to-leaf paths surviving pruning** -- propagation contributes
essentially nothing once P1 bets.  Changing the split rule bought 3x; changing
the branching cannot fix a bound that never fires.

The standard strengthening is singleton look-ahead (a.k.a. shaving / SAC): at
each node, for each still-unassigned coordinate, tentatively assign each label
in {0, 1, interior} and run ordinary propagation.  Labels that die are removed;
if one label survives, it is FORCED; if none survives, the node is dead.

Soundness is immediate and is the only reason this is allowed: a label is
removed only when `bnb.propagate` proves no completion carrying it can satisfy
the first-order conditions, which is exactly the test the search already trusts.
Look-ahead therefore only ever removes what the existing prune would have
removed later -- it just does it before the tree branches, which is where the
saving is.

Measured with the same Knuth estimator, so the numbers are directly comparable
to `log_treesize.txt`, and with the same control: the P1-silent branch, whose
true size is 3,045,358.  Under a sound strengthening that number must go DOWN or
stay equal -- never up.  If it rises, the look-ahead is removing labels it should
not, and nothing else it reports can be believed.

usage:  python lookahead.py <walks> <workers> [spec ...]
"""
import numpy as np, sys, time, bnb, kuhn3p as K
from multiprocessing import Pool
from treesize import ORDER, root_of

U, MIX = bnb.U, bnb.MIX
LABELS = (0, 1, MIX)


def shave(lab):
    """Singleton look-ahead on one row.  Returns (lab, alive).

    Repeats to a fixed point: forcing one coordinate can make another
    coordinate's labels die, which is where the compounding comes from.
    """
    lab = lab.copy()
    for _ in range(8):
        changed = False
        us = np.flatnonzero(lab == U)
        if us.size == 0:
            return lab, True
        for v in us:
            cand = []
            for L in LABELS:
                t = lab.copy()[None, :]
                t[0, v] = L
                t, al = bnb.propagate(t)
                if al[0]:
                    cand.append(t[0])
            if not cand:
                return lab, False              # no label works: node is dead
            if len(cand) == 1:
                lab = cand[0]                  # forced
                changed = True
                break
        if not changed:
            return lab, True
    return lab, True


def walk(a):
    """One random root-to-leaf path under look-ahead; Knuth weight."""
    spec, seed = a
    rng = np.random.default_rng(seed)
    lab = root_of(spec)[None, :].copy()
    lab, al = bnb.propagate(lab)
    if not al[0]:
        return 0.0
    lab, ok = shave(lab[0])
    if not ok:
        return 0.0
    w = 1.0
    while True:
        if not (lab == U).any():
            return w
        v = next(x for x in ORDER if lab[x] == U)
        kids = []
        for L in LABELS:
            t = lab.copy()[None, :]
            t[0, v] = L
            t, al = bnb.propagate(t)
            if not al[0]:
                continue
            s, ok = shave(t[0])
            if ok:
                kids.append(s)
        if not kids:
            return 0.0
        w *= len(kids)
        lab = kids[rng.integers(len(kids))]


if __name__ == "__main__":
    nwalk = int(sys.argv[1]); nw = int(sys.argv[2])
    specs = sys.argv[3:] or ["silent", "a11:MIX"]
    print("Knuth estimate WITH singleton look-ahead\n", flush=True)
    with Pool(nw) as pool:
        for spec in specs:
            t0 = time.time()
            W = np.array(pool.map(walk, [(spec, s) for s in range(nwalk)]))
            m = W.mean(); se = W.std(ddof=1) / np.sqrt(len(W))
            nz = 100.0 * (W > 0).mean()
            print("%-12s leaves ~ %.3e  +/- %.1e   paths surviving %.1f%%   %.0fs"
                  % (spec, m, se, nz, time.time() - t0), flush=True)
