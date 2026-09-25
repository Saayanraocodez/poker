"""Tabulate runbet6's ledgers (seq and nash) and state where the completeness
proof stands: which betting branches are decided, how many leaves, and whether
anything non-empty was found.

usage:  python summarize6.py [suffix]     (suffix R: the directed-rounding re-derivation ledgers)
"""
import os, re, sys

def table(path, branches_file, mode, XS=""):
    if not os.path.exists(path):
        print("%s: no ledger yet" % mode); return
    specs = [s.strip() for s in open(branches_file) if s.strip() and s.strip() != "a11:0,a21:0,a31:0,a41:0"]
    done = {}
    for line in open(path):
        if not line.strip() or "FAILED" in line: continue
        spec = line.split()[0]
        leaves = int(re.search(r"leaves\s+(\d+)", line).group(1))
        m = re.search(r"exact: empty (\d+) family (\d+) open (\d+)(?: timeout (\d+))? error (\d+)", line)
        pv = re.search(r"proven (\d+)\s+undecided (\d+)", line)
        if m:
            empty, fam, op, to, err = (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4) or 0), int(m.group(5)))
            if pv: empty += int(pv.group(1))        # old format: interval-proven + exact-stage empty
        else:
            # old-format lines: interval stage only, nothing left undecided
            empty = int(pv.group(1)) if pv else leaves; fam = op = to = err = 0
            if pv and int(pv.group(2)): op = int(pv.group(2))
        undec = op + to + err
        ip = re.search(r"interval-proven (\d+) of (\d+)", line)
        if ip: empty += int(ip.group(1)); undec -= int(ip.group(1))
        # post-pass resolution (resolve_left.py) of leaves left undecided on the ledger line
        tag = "b_" + "_".join(p.split(":")[1].replace("MIX", "M") for p in spec.split(",")) + ("N" if "nash" in mode else "") + XS
        if not ip and undec and os.path.exists("prove6pat_%s_left.npz" % tag):
            import numpy as np
            with np.load("prove6pat_%s_left.npz" % tag) as z: pv = z["proven"]
            empty += int(pv.sum()); undec -= int(pv.sum())
        done[spec] = (leaves, empty, fam, undec)
    print("=== %s mode: %d of %d betting branches decided ===" % (mode, len(done), len(specs)))
    print("%-34s %8s %8s %6s %6s" % ("branch", "leaves", "empty", "family", "open"))
    tl = te = tf = to_ = 0
    for spec in specs:
        if spec in done:
            l, e, f, o = done[spec]; tl += l; te += e; tf += f; to_ += o
            print("%-34s %8d %8d %6d %6d" % (spec, l, e, f, o))
        else:
            print("%-34s %8s" % (spec, "-- pending --"))
    print("%-34s %8d %8d %6d %6d" % ("TOTAL decided", tl, te, tf, to_))
    verdict = "no equilibrium with P1 betting in any decided branch" if tf == 0 and to_ == 0 else "*** NON-EMPTY OR UNDECIDED LEAVES: look at the ledger"
    print("   " + verdict + ("" if len(done) == len(specs) else "  (%d branches pending)" % (len(specs) - len(done))))
    print()

XS = sys.argv[1] if len(sys.argv) > 1 else ""
table("runbet6_summary%s.txt" % XS, "branches_alive%s.txt" % XS, "seq" + XS, XS)
table("runbet6_summary_nash%s.txt" % XS, "branches_alive_nash%s.txt" % XS, "nash" + XS, XS)
