"""(3,5)-Kuhn feasibility sweep: layered enumeration (enuml.py, exact tests,
directed-rounding floats) of every root-alive P1-opening cell, each with a
wall-clock cap.  Ledger cells_summary_<n>.txt: cell, leaves, exact tests,
kills, seconds, or TIMEOUT.  Only EMPTY leaf verdicts are meaningful here
(symleaf's FAMILY checks are 4-card specific).
usage:  KUHN_CARDS=5 KUHN_MODE=nash KUHN_ORDER=bet python runcells.py <workers-per-cell> <parallel-cells> <cap-seconds>
"""
import subprocess, sys, os, re, time
from concurrent.futures import ThreadPoolExecutor
import kuhn3p as K
nw, par, cap = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
cells = [l.strip() for l in open("cells_alive_nash_%d.txt" % K.NCARDS) if l.strip()]
silent = ",".join("a%d1:0" % j for j in K.CARDS)
cells = [c for c in cells if c != silent]
SUM = "cells_summary_%d.txt" % K.NCARDS
done = set(l.split()[0] for l in open(SUM)) if os.path.exists(SUM) else set()
def tag_of(c): return "k%d_" % K.NCARDS + "_".join(p.split(":")[1].replace("MIX", "M") for p in c.split(","))
def run(cell):
    tag = tag_of(cell); t0 = time.time()
    with open("log_cell_%s.txt" % tag, "w") as f:
        p = subprocess.Popen([sys.executable, "-u", "enuml.py", cell, nw, tag, "4"], stdout=f, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=cap); status = "done"
        except subprocess.TimeoutExpired:
            # kill the whole tree: a bare kill() orphans the pool workers, which
            # keep computing (and holding GB of RAM) until their chunk ends
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait(); status = "TIMEOUT"
    s = open("log_cell_%s.txt" % tag, errors="replace").read()
    m = re.search(r": (\d+) leaves, (\d+) exact tests \((\d+) killed\), (\d+)s", s)
    v = re.search(r"leaf verdicts (\{.*?\})", s)
    line = "%-50s %s  leaves %s  tests %s  killed %s  %s  %.0fs" % (cell, status, m.group(1) if m else "?", m.group(2) if m else "?", m.group(3) if m else "?", v.group(1) if v else "", time.time() - t0)
    with open(SUM, "a") as f: f.write(line + "\n")
    print(line, flush=True)
with ThreadPoolExecutor(par) as ex:
    list(ex.map(run, [c for c in cells if c not in done]))
