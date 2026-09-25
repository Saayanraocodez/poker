"""Does a better split rule change the box-count growth of bnb5?

bnb5 splits the WIDEST coordinate.  That is the obvious rule and it is probably
the wrong one here: after Table 2 there are ~26 free coordinates, many of them
UNREACHABLE inside a given box (ivl.bounds reports a reach upper bound of 0).
An unreachable coordinate cannot affect any leaf, so bisecting it buys nothing
and doubles the node count -- and with a depth budget of 26 over 26 coordinates,
every wasted split is a coordinate that never gets split at all.

The depth ladder says boxes grow ~1.46x per level at depth 26 and reaching a
real wtol needs ~104 more levels, so the route is dead ON THIS RULE.  It is only
honest to declare it dead after trying the obvious alternatives, because the
growth factor is a property of the rule, not of the problem.

Rules compared, all as `objsplit(LO, HI, W) -> score`, largest score is split:

  width     W                      (the current rule; the baseline)
  reach     W * (reach UB > 0)     never split a coordinate that cannot matter
  grad      W * (DHI - DLO)        split where the gradient bound is loosest
  reachgrad W * (DHI-DLO) * (RH>0) both

Run at a depth where the baseline is known and cheap, so the comparison is
apples to apples: depth 22 on bet_a41_lo is 847,044 nodes / 337,074 boxes.

usage:  python splitrule.py <maxdepth> <workers> [rule ...]
"""
import numpy as np, sys, time, bnb5, ivl, kuhn3p as K
from multiprocessing import Pool

I = K.NAME_IDX
CONS = [("a41", 0.02, 0.25)]          # bet_a41_lo, the cheapest bet task
EPS = 1e-12


def mk(rule):
    if rule == "width":
        return None
    def objsplit(LO, HI, W):
        DLO, DHI, RH, DMIN, DMAX = ivl.bounds(LO, HI)
        if rule == "reach":
            s = W * (RH > 0.0)
        elif rule == "grad":
            s = W * (DHI - DLO)
        elif rule == "reachgrad":
            s = W * (DHI - DLO) * (RH > 0.0)
        else:
            raise SystemExit("unknown rule %s" % rule)
        # A row whose score is all zero would never split and would spin at the
        # same node forever; fall back to width there.
        dead = s.max(axis=1) <= EPS
        if dead.any():
            s = s.copy(); s[dead] = W[dead]
        return s
    return objsplit


def job(a):
    rule, maxdepth = a
    LO = np.zeros(48); HI = np.ones(48)
    for n, lo, hi in CONS:
        LO[I[n]] = lo; HI[I[n]] = hi
    t0 = time.time()
    st, out = bnb5.search(LO0=LO, HI0=HI, wtol=0.06, maxdepth=maxdepth,
                          cap=4096, maxnodes=60000000, log=None,
                          objsplit=mk(rule), tag=rule)
    return rule, st, time.time() - t0


if __name__ == "__main__":
    maxdepth = int(sys.argv[1]); nw = int(sys.argv[2])
    rules = sys.argv[3:] or ["width", "reach", "grad", "reachgrad"]
    print("bet_a41_lo  maxdepth=%d\n" % maxdepth, flush=True)
    print("%-11s %12s %12s %10s %10s" % ("rule", "nodes", "boxes", "abort", "sec"), flush=True)
    base = {}
    with Pool(nw) as pool:
        for rule, st, dt in pool.imap_unordered(job, [(r, maxdepth) for r in rules]):
            base[rule] = st
            print("%-11s %12d %12d %10s %10.0f"
                  % (rule, st['nodes'], st['boxes'], st.get('ABORT', False), dt), flush=True)
    if "width" in base:
        b = base["width"]['boxes']
        print("\nrelative to the current rule (width):", flush=True)
        for r, st in base.items():
            print("   %-11s boxes x%.3f" % (r, st['boxes'] / max(b, 1)), flush=True)
