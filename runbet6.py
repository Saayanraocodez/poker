"""Enumerate every P1-betting branch that survives the root with enum6,
smallest estimated first, then screen and prove each leaf set.

For each branch spec (from branches_alive.txt, minus the silent one):
   1. enum6.py <spec> <workers> <tag>            -> enum6_pat_<tag>.npy (+ boxes)
   2. symleaf (exact algebra) on EVERY leaf: empty / family / open
   3. screen6-style LM on the leaves not proven empty, seeded from their
      boxes; certify by expl and classify on path
Everything is logged to log_runbet6.txt and a summary table is written to
runbet6_summary.txt after every branch, so a killed run loses one branch at most;
branches whose enum6_pat_<tag>.npy already exists are skipped.

usage:  [KUHN_MODE=nash] [KUHN_ENUM=layered] [KUHN_SUFFIX=R] python runbet6.py <workers> [symleaf maxnodes]
"""
import numpy as np, subprocess, sys, os, time

nw = int(sys.argv[1]); budget = int(sys.argv[2]) if len(sys.argv) > 2 else 300
# KUHN_MODE=nash: strong rules only (every Nash equilibrium); branches from
# root81.py's branches_alive_nash.txt, every file name gets the suffix N so the
# two modes never share a file.  Default seq: bnb6's weak rules.
NASH = os.environ.get("KUHN_MODE", "seq") == "nash"
# KUHN_SUFFIX (2026-09-20): extra file-name suffix for a full re-derivation
# under changed numerics (R = ivl directed rounding), so the old ledger, leaf
# sets and checkpoints are never touched or resumed from.
XS = os.environ.get("KUHN_SUFFIX", "")
SUF = ("N" if NASH else "") + XS
BRANCHES = ("branches_alive_nash%s.txt" if NASH else "branches_alive%s.txt") % XS   # root81 honours KUHN_SUFFIX too
SUMMARY = "runbet6_summary%s%s.txt" % ("_nash" if NASH else "", XS)
LOG = "log_runbet6%s%s.txt" % ("_nash" if NASH else "", XS)
specs = [s.strip() for s in open(BRANCHES) if s.strip() and s.strip() != "a11:0,a21:0,a31:0,a41:0"]
# order by Knuth estimate, smallest first
est = {}
for line in open("log_treesize6_branches.txt"):
    if "leaves ~" in line:
        est[line.split()[0]] = float(line.split()[3])
specs.sort(key=lambda s: est.get(s, 1e12))

def tag_of(s):
    return "b_" + "_".join(p.split(":")[1].replace("MIX", "M") for p in s.split(",")) + SUF

def run(cmd, log, expect=None, tries=3):
    """run cmd with output appended to log; retry when the process fails to
    start or exits non-zero (on 2026-09-15 thirty-one enum6 launches in a row
    died in 2 s with no output and the old driver marked every branch FAILED)."""
    for t in range(tries):
        with open(log, "a") as f:
            f.write("\n$ " + " ".join(cmd) + "\n"); f.flush()
            rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)
            if rc == 0 and (expect is None or os.path.exists(expect)):
                return rc
            f.write("*** exit code %d%s -- retry %d/%d in 30s\n" % (rc, "" if expect is None or os.path.exists(expect) else ", %s missing" % expect, t + 1, tries)); f.flush()
        time.sleep(30)
    return rc


done = set()
if os.path.exists(SUMMARY):
    for line in open(SUMMARY):
        if line.strip() and "FAILED" not in line:
            done.add(line.split()[0])

for spec in specs:
    tag = tag_of(spec); t0 = time.time()
    if spec in done:
        print("%-34s already in %s, skipped" % (spec, SUMMARY), flush=True); continue
    if not os.path.exists("enum6_pat_%s.npy" % tag):
        # KUHN_ENUM=layered (2026-09-19): enuml.py -- the exact test every 4
        # levels of the label DFS; reaches 0 leaves on betting branches where
        # enum6 produced 10^5-10^6, and the 12 FAMILY leaves on the silent one.
        # It writes enum6_pat_<tag>.npy AND a complete symleaf_<tag>.npz, so the
        # symleaf call below resumes from a finished checkpoint.
        if os.environ.get("KUHN_ENUM", "float") == "layered":
            run([sys.executable, "-u", "enuml.py", spec, str(nw), tag, "4"], LOG, expect="enum6_pat_%s.npy" % tag)
        else:
            run([sys.executable, "-u", "enum6.py", spec, str(nw), tag], LOG, expect="enum6_pat_%s.npy" % tag)
    if not os.path.exists("enum6_pat_%s.npy" % tag):
        with open(SUMMARY, "a") as f: f.write("%-34s enumeration FAILED\n" % spec)
        continue
    L = np.load("enum6_pat_%s.npy" % tag)
    n = len(L)
    line = "%-34s est %.1e  leaves %7d  enum %.0fs" % (spec, est.get(spec, float("nan")), n, time.time() - t0)
    if n > 0:
        # exact stage on EVERY leaf.  (The interval stage prove6pat is no longer
        # run first: on the 2026-09-15 branches it proved 20-35 % in hours and
        # symleaf then decided the rest in seconds -- it is complete and faster.)
        import symleaf as SL
        run([sys.executable, "-u", "symleaf.py", tag, str(nw), "-", "0", str(budget)], LOG, expect="symleaf_%s.npz" % tag)
        with np.load("symleaf_%s.npz" % tag) as z:
            vd = z["verdict"]
        cnt = {v: int((vd == SL.VC[v]).sum()) for v in SL.VERD}
        nempty = cnt["EMPTY_GB"] + cnt["EMPTY_MIX"] + cnt["EMPTY_BOX"] + cnt["EMPTY_CONST"]
        left = np.flatnonzero(~np.isin(vd, [SL.VC[v] for v in ("EMPTY_GB", "EMPTY_MIX", "EMPTY_BOX", "EMPTY_CONST")]))
        line += "  exact: empty %d family %d open %d timeout %d error %d" % (nempty, cnt["FAMILY"], cnt["OPEN"], cnt["TIMEOUT"], cnt["ERROR"] + int((vd < 0).sum()))
        # numerical look at whatever is not proven empty: LM from the leaf boxes,
        # certified by expl and classified on path (screen6 reads the prove6pat
        # format, so write the leaf boxes in that format with 'proven' = empty)
        if len(left):
            # interval fallback (2026-09-20): leaves the exact B&B could not
            # decide in its budget go to prove6pat, bnb6's B&B from the leaf
            # box -- rigorous since ivl rounds outward; in seq mode it also
            # has the weak rules, which is why the 8 leaves of
            # a11:0,a21:MIX,a31:0,a41:1 that time out at 3000 exact nodes
            # die there in 420 nodes.  Recorded as 'interval-proven'.
            np.save("idx_left_%s.npy" % tag, left)
            run([sys.executable, "-u", "prove6pat.py", tag, str(nw), "200000", tag + "_left", "idx_left_%s.npy" % tag], LOG, expect="prove6pat_%s_left.npz" % tag)
            if os.path.exists("prove6pat_%s_left.npz" % tag):
                with np.load("prove6pat_%s_left.npz" % tag) as z: pv = z["proven"]
                line += "  interval-proven %d of %d" % (int(pv.sum()), len(left))
                left = left[~pv]
        if len(left):
            np.savez("prove6pat_%s.npz" % tag, proven=~np.isin(np.arange(n), left), nodes=np.zeros(n, np.int64), left=np.zeros(n, np.int64),
                     bestlo=np.load("enum6_lo_%s.npy" % tag), besthi=np.load("enum6_hi_%s.npy" % tag), bestw=np.zeros(n))
            run([sys.executable, "-u", "screen6.py", tag, str(nw), "8"], LOG)
            ncert = 0; nbet = 0
            if os.path.exists("screen6_ex_%s.npy" % tag):
                ex = np.load("screen6_ex_%s.npy" % tag); X = np.load("screen6_x_%s.npy" % tag)
                import kuhn3p as K
                I = K.NAME_IDX
                cert = X[ex < 1e-13]; ncert = len(cert)
                if ncert:
                    nbet = int((cert[:, [I[c] for c in ("a11", "a21", "a31", "a41")]].max(axis=1) > 1e-9).sum())
            line += "  LM-certified %d (with P1 betting: %d)" % (ncert, nbet)
    with open(SUMMARY, "a") as f: f.write(line + "\n")
    print(line, flush=True)
