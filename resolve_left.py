"""Post-pass for a runbet6 ledger: every branch whose line still has undecided
leaves (open / timeout / error) gets prove6pat -- bnb6's rigorous interval B&B
from the leaf box, weak rules in seq mode -- on exactly those leaves, writing
prove6pat_<tag>_left.npz, which summarize6 folds into the table.

usage:  [KUHN_MODE=nash] python resolve_left.py <suffix> <workers> [maxnodes]
"""
import numpy as np, subprocess, sys, os, re
import symleaf as SL

XS = sys.argv[1]; nw = int(sys.argv[2]); maxnodes = sys.argv[3] if len(sys.argv) > 3 else "200000"
NASH = os.environ.get("KUHN_MODE", "seq") == "nash"
SUMMARY = "runbet6_summary%s%s.txt" % ("_nash" if NASH else "", XS)
EMPTY = [SL.VC[v] for v in ("EMPTY_GB", "EMPTY_MIX", "EMPTY_BOX", "EMPTY_CONST")]
for line in open(SUMMARY):
    m = re.search(r"exact: empty (\d+) family (\d+) open (\d+) timeout (\d+) error (\d+)", line)
    if not m or not (int(m.group(3)) + int(m.group(4)) + int(m.group(5))): continue
    spec = line.split()[0]
    tag = "b_" + "_".join(p.split(":")[1].replace("MIX", "M") for p in spec.split(",")) + ("N" if NASH else "") + XS
    if os.path.exists("prove6pat_%s_left.npz" % tag):
        with np.load("prove6pat_%s_left.npz" % tag) as z: pv = z["proven"]
        print("%-34s already resolved: %d of %d interval-proven" % (spec, pv.sum(), len(pv))); continue
    with np.load("symleaf_%s.npz" % tag) as z: vd = z["verdict"]
    left = np.flatnonzero(~np.isin(vd, EMPTY))
    np.save("idx_left_%s.npy" % tag, left)
    print("%-34s %d undecided leaves -> prove6pat" % (spec, len(left)), flush=True)
    subprocess.call([sys.executable, "-u", "prove6pat.py", tag, str(nw), maxnodes, tag + "_left", "idx_left_%s.npy" % tag])
