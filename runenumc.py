"""Driver for the CERTIFIED enumeration of every P1-betting branch (third pass):
enumc.py per branch, then checkenum.py, one ledger line each in
enumc_summary_<mode>.txt; branches already ledgered are skipped.

A branch that exceeds KUHN_CAP seconds (default 4h) is abandoned with a
PARTIAL ledger line and its truncated output removed, so one hard branch
cannot eat the pass; PARTIAL branches keep the directed-rounding interval
enumeration as their proof (sound, but not replayable) and can be retried
later with a tuned kill ladder.

usage:  KUHN_MODE=nash KUHN_ORDER=bet [KUHN_CAP=14400] python runenumc.py <workers>
"""
import sys as _sys, os as _os
# Launched by pythonw.exe there is NO console and sys.stdout is None -- give the
# run a log file of its own.  Windowless on purpose: a `cmd /c ... > log` launcher
# opens a console window, and closing that window sends CTRL_CLOSE/CTRL_C to
# everything attached to it, which is what killed these runs on 2026-09-22.
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _f = open(_os.environ.get("KUHN_LOG", "log_%s.txt" % _os.path.splitext(_os.path.basename(__file__))[0]), "a", buffering=1, encoding="utf-8", errors="replace")
    _sys.stdout = _sys.stderr = _f

import subprocess, sys, os, time, re
import signal as _sig
# This box delivers stray CTRL_C/CTRL_BREAK events to every console process in the
# session (2026-09-22: three launch methods -- Start-Process, WMI Win32_Process.Create
# and Task Scheduler -- all had their python killed with "^C" in the log within
# seconds).  A long run must not die of someone else's Ctrl+C; the pool workers
# inherit these handlers.
for _s in ("SIGINT", "SIGBREAK"):
    if hasattr(_sig, _s):
        try: _sig.signal(getattr(_sig, _s), _sig.SIG_IGN)
        except Exception: pass



nw = sys.argv[1]
CAP = float(os.environ.get("KUHN_CAP", "14400"))
NASH = os.environ.get("KUHN_MODE", "seq") == "nash"
BR = "branches_alive_nashR.txt" if NASH else "branches_aliveR.txt"
SUM = "enumc_summary_%s.txt" % ("nash" if NASH else "seq")
specs = [s.strip() for s in open(BR) if s.strip() and s.strip() != "a11:0,a21:0,a31:0,a41:0"]
est = {}
for line in open("log_treesize6_branches.txt"):
    if "leaves ~" in line: est[line.split()[0]] = float(line.split()[3])
specs.sort(key=lambda s: est.get(s, 1e12))
done = set()
if os.path.exists(SUM):
    for l in open(SUM):
        if l.strip(): done.add(l.split()[0])
for spec in specs:
    if spec in done: continue
    tag = "c_" + "_".join(p.split(":")[1].replace("MIX", "M") for p in spec.split(",")) + ("N" if NASH else "")
    t0 = time.time(); capped = False
    with open("log_enumc_%s.txt" % tag, "w") as f:
        p = subprocess.Popen([sys.executable, "-u", "enumc2.py", spec, nw, tag], stdout=f, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=CAP)
        except subprocess.TimeoutExpired:
            # /T: a bare kill orphans the pool workers, which keep computing
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait(); capped = True
    te = time.time() - t0; t1 = time.time()
    if capped:
        prog = [l for l in open("log_enumc_%s.txt" % tag, errors="replace") if "jobs" in l]
        m = re.search(r"kill (\d+) split (\d+) leaf (\d+) (\{.*?\})\s+float-unsure (\d+)", prog[-1]) if prog else None
        line = "%-34s PARTIAL (cap %.0fs) %s" % (spec, te, ("kill %s split %s leaf %s %s float-unsure %s" % m.groups()) if m else "no progress line")
        with open(SUM, "a") as f: f.write(line + chr(10))
        print(line, flush=True)
        try: os.remove("enumc_%s.jsonl.gz" % tag)
        except OSError: pass
        continue
    res = subprocess.run([sys.executable, "-u", "checkenum.py", "enumc_%s.jsonl.gz" % tag, "8"], capture_output=True, text=True)
    last = [l for l in res.stdout.splitlines() if "nodes" in l]
    m = re.search(r"(\d+) nodes\s+kill (\d+)\s+split (\d+)\s+leaf (\d+) (\{.*?\})\s+failed (\d+)\s+children never seen (\d+).*(OK|NOT VERIFIED)", last[-1]) if last else None
    line = "%-34s nodes %8s kill %8s split %8s leaf %6s %s failed %s missing %s  %s  enum %.0fs check %.0fs" % (
        spec, *(m.groups() if m else ("?",) * 8), te, time.time() - t1)
    with open(SUM, "a") as f: f.write(line + "\n")
    print(line, flush=True)
