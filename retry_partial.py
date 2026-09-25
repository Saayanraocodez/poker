"""Second attempt at the third pass's PARTIAL branches, with a long clock and
several branches at once.

runenumc.py ran all 77 nash-mode betting branches at a 2 h cap (2026-09-22/23):
71 verified end to end, 6 abandoned as PARTIAL.  Five of the six were simply
big (0-62 float-unsure nodes, 50k-124k kills at the cap); one is the
pathological branch with 228 float-unsure.  This runs them again, PAR branches
at a time with NW workers each, at KUHN_CAP seconds (default 12 h), and appends
the new ledger lines.  The PARTIAL lines it replaces are moved to
enumc_partial_history.txt first, so the ledger ends with one line per branch.

usage (windowless):  pythonw.exe retry_partial.py [PAR] [NW]
"""
import sys as _sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _f = open("log_retry_partial.txt", "a", buffering=1, encoding="utf-8", errors="replace")
    _sys.stdout = _sys.stderr = _f
import signal as _sig
for _s in ("SIGINT", "SIGBREAK"):
    if hasattr(_sig, _s):
        try: _sig.signal(getattr(_sig, _s), _sig.SIG_IGN)
        except Exception: pass

import subprocess, sys, os, time, re
from concurrent.futures import ThreadPoolExecutor

PAR = int(sys.argv[1]) if len(sys.argv) > 1 else 3
NW = sys.argv[2] if len(sys.argv) > 2 else "9"
CAP = float(os.environ.get("KUHN_CAP", "43200"))
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
SUM = "enumc_summary_nash.txt"

lines = [l for l in open(SUM) if l.strip()]
partial = [l for l in lines if "PARTIAL" in l]
if partial:
    with open("enumc_partial_history.txt", "a") as h:
        for l in partial: h.write(time.strftime("%Y-%m-%d %H:%M  ") + l)
    with open(SUM, "w") as f:
        for l in lines:
            if "PARTIAL" not in l: f.write(l)
specs = [l.split()[0] for l in partial]
if not specs:                                   # a restart: retry whatever is missing
    done = {l.split()[0] for l in lines}
    specs = [s.strip() for s in open("branches_alive_nashR.txt") if s.strip() and s.strip() not in done
             and s.strip() != "a11:0,a21:0,a31:0,a41:0"]
print("%s  retrying %d branches, %d at a time, %s workers each, cap %.0fs" % (time.strftime("%m-%d %H:%M"), len(specs), PAR, NW, CAP), flush=True)


def run(spec):
    tag = "c_" + "_".join(p.split(":")[1].replace("MIX", "M") for p in spec.split(",")) + "N"
    t0 = time.time(); capped = False
    with open("log_enumc_%s.txt" % tag, "w") as f:
        p = subprocess.Popen([sys.executable, "-u", "enumc2.py", spec, NW, tag], stdout=f, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=CAP)
        except subprocess.TimeoutExpired:
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait(); capped = True
    te = time.time() - t0
    if capped:
        prog = [l for l in open("log_enumc_%s.txt" % tag, errors="replace") if "jobs" in l]
        m = re.search(r"kill (\d+) split (\d+) leaf (\d+) (\{.*?\})\s+float-unsure (\d+)", prog[-1]) if prog else None
        line = "%-34s PARTIAL (cap %.0fs) %s" % (spec, te, ("kill %s split %s leaf %s %s float-unsure %s" % m.groups()) if m else "no progress line")
        try: os.remove("enumc_%s.jsonl.gz" % tag)
        except OSError: pass
    else:
        t1 = time.time()
        res = subprocess.run([sys.executable, "-u", "checkenum.py", "enumc_%s.jsonl.gz" % tag, "4"], capture_output=True, text=True)
        last = [l for l in res.stdout.splitlines() if "nodes" in l]
        m = re.search(r"(\d+) nodes\s+kill (\d+)\s+split (\d+)\s+leaf (\d+) (\{.*?\})\s+failed (\d+)\s+children never seen (\d+).*(OK|NOT VERIFIED)", last[-1]) if last else None
        line = "%-34s nodes %8s kill %8s split %8s leaf %6s %s failed %s missing %s  %s  enum %.0fs check %.0fs" % (
            spec, *(m.groups() if m else ("?",) * 8), te, time.time() - t1)
    with open(SUM, "a") as f: f.write(line + "\n")
    print(time.strftime("%m-%d %H:%M  ") + line, flush=True)


with ThreadPoolExecutor(PAR) as ex:
    list(ex.map(run, specs))
print(time.strftime("%m-%d %H:%M  ") + "done", flush=True)
