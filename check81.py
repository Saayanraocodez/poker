"""Theorem 4 as ONE replayable object: the 81 opening cells, each closed by an exact-propagation
certificate tree (enumc7.py) that the independent checker (checkenum2.py) replays.

P1's four opening coordinates a11, a21, a31, a41 each carry a label 0 / 1 / MIX, so the 3^4 = 81
cells partition the profile space (Lemma 4).  This driver

  1. replays every tree it is given with checkenum2 (which binds each tree's root to the cell its
     header names: the four opening labels, everything else unassigned, the box [0,1]^48);
  2. checks COVERAGE: every one of the 81 cells has exactly one verified tree;
  3. checks the VERDICT: no support leaf survives in any of the 80 betting cells, and the silent cell
     a11:0,a21:0,a31:0,a41:0 has only EMPTY leaves and FAMILY leaves, whose label vectors are exactly
     the twelve of independent_check/family_leaves.json.

With all three, Lemma 1 + Lemma 5 give Theorem 4: every Nash equilibrium has P1 silent and plays the
SGS family on path.  Nothing here depends on float arithmetic, on the 66,699 leaf certificates of the
R ledger or on the 4.4M-node enumc2 trees: those are independent cross-checks, not part of this proof.

usage:  python makeD.py                      (once: D_all.pkl)
        python check81.py [dir or tree files ...] [-j workers]        default: proof34/
Writes <dir>/ledger.txt.  Exit status 0 only if all 81 cells are covered and verified.
"""
import sys, os, glob, itertools, json, time
import checkenum2 as C2

MIX, DC, U = 2, 3, 9


def cells():
    names = ("a11", "a21", "a31", "a41")
    return [",".join("%s:%s" % (n, l) for n, l in zip(names, combo)) for combo in itertools.product(("0", "1", "MIX"), repeat=4)]


def main(argv):
    nw = 4; paths = []
    it = iter(argv)
    for a in it:
        if a == "-j": nw = int(next(it))
        else: paths.append(a)
    if not paths: paths = ["proof34"]
    files = []
    for p in paths:
        files += sorted(glob.glob(os.path.join(p, "*.jsonl.gz"))) if os.path.isdir(p) else [p]
    outdir = paths[0] if os.path.isdir(paths[0]) else "."
    SILENT = "a11:0,a21:0,a31:0,a41:0"
    got = {}; lines = []; t0 = time.time(); problems = []
    for f in files:
        ok = C2.main(f, nw)
        r = dict(C2.LAST); spec = r.get("spec")
        line = "%-34s nodes %6d split %5d pkill %5d kill %5d leaf %4d %s failed %d missing %d  %s   %s" % (
            spec, r["nodes"], r["kinds"]["split"], r["kinds"]["pkill"], r["kinds"]["kill"], r["kinds"]["leaf"], r["verdicts"],
            r["failed"], r["missing"], "OK" if ok else "NOT VERIFIED", os.path.basename(f))
        lines.append(line)
        if not ok: problems.append("%s: not verified (%s)" % (spec, f)); continue
        if spec in got: problems.append("%s: covered twice (%s)" % (spec, f)); continue
        got[spec] = r
    allc = cells()
    missing = [c for c in allc if c not in got]
    extra = [c for c in got if c not in allc]
    if extra: problems.append("trees for unknown cells: %s" % extra)
    fam = []
    for spec, r in got.items():
        bad = {v: n for v, n in r["verdicts"].items() if not v.startswith("EMPTY") and not (spec == SILENT and v == "FAMILY")}
        if bad: problems.append("%s: surviving leaves %s" % (spec, bad))
        if spec == SILENT: fam = r["family"]
    fam_ok = None
    if SILENT in got:
        ref = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "independent_check", "family_leaves.json")))
        want = sorted(tuple(v) for v in ref.values()); have = sorted(tuple(v) for v in fam)
        fam_ok = (want == have)
        if not fam_ok: problems.append("silent cell: its %d FAMILY leaves are not the twelve of family_leaves.json" % len(fam))
    nodes = sum(r["nodes"] for r in got.values()); leaves = sum(r["kinds"]["leaf"] for r in got.values())
    summary = ["",
               "cells verified: %d of 81   (betting %d of 80, silent %s)" % (len(got), len([c for c in got if c != SILENT]), "yes" if SILENT in got else "NO"),
               "nodes replayed: %d   support leaves: %d   FAMILY leaves: %d%s" % (nodes, leaves, len(fam), "" if fam_ok is None else ("  (the twelve of family_leaves.json: %s)" % fam_ok)),
               "missing cells (%d): %s" % (len(missing), " ".join(missing) if missing else "none"),
               "problems: %s" % ("; ".join(problems) if problems else "none"),
               "THEOREM 4 %s  (%.0fs)" % ("VERIFIED: all 81 cells closed" if not missing and not problems else "NOT YET VERIFIED BY THIS SET OF TREES", time.time() - t0)]
    with open(os.path.join(outdir, "ledger.txt"), "w") as f:
        f.write("\n".join(sorted(lines) + summary) + "\n")
    print("\n".join(summary))
    return 0 if not missing and not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
