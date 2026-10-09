"""Run the option-2 prover (enumc7) on a list of branches, one at a time with all workers, and check
each output with the independent checker (checkenum2).  Resumable: enumc7 resumes its own output, and
a branch already in the ledger is skipped.  Ledger: enumc7_summary_nash.txt.
usage (windowless):  pythonw.exe run_enumc7.py <workers> <branch list file>"""
import sys as _sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _f = open("log_run_enumc7.txt", "a", buffering=1, encoding="utf-8", errors="replace")
    _sys.stdout = _sys.stderr = _f
import signal as _sig
for _s in ("SIGINT", "SIGBREAK"):
    if hasattr(_sig, _s):
        try: _sig.signal(getattr(_sig, _s), _sig.SIG_IGN)
        except Exception: pass
import subprocess, sys, os, time, re, json

NW = sys.argv[1] if len(sys.argv) > 1 else "26"
LIST = sys.argv[2] if len(sys.argv) > 2 else "branches_enumc7.txt"
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
SUM = "enumc7_summary_nash.txt"
specs = [s.strip() for s in open(LIST) if s.strip() and not s.startswith("#")]
done = {l.split()[0] for l in open(SUM)} if os.path.exists(SUM) else set()
todo = [s for s in specs if s not in done]
print("%s  enumc7 on %d branches (%d already in the ledger), %s workers" % (time.strftime("%m-%d %H:%M"), len(todo), len(specs) - len(todo), NW), flush=True)
for spec in todo:
    tag = "c7_" + "_".join(p.split(":")[1].replace("MIX", "M") for p in spec.split(",")) + "N"
    t0 = time.time()
    with open("log_enumc7_%s.txt" % tag, "a") as f:
        f.write("===== %s  enumc7\n" % time.strftime("%Y-%m-%d %H:%M")); f.flush()
        rc = subprocess.call([sys.executable, "-u", "enumc7.py", spec, NW, tag], stdout=f, stderr=subprocess.STDOUT)
    te = time.time() - t0
    ck = "enumc_%s.ckpt" % tag
    if rc != 0 or not (os.path.exists(ck) and json.load(open(ck)).get("complete")):
        line = "%-34s ERROR (rc %s after %.0fs; see log_enumc7_%s.txt)" % (spec, rc, te, tag)
    else:
        t1 = time.time()
        res = subprocess.run([sys.executable, "-u", "checkenum2.py", "enumc_%s.jsonl.gz" % tag, NW], capture_output=True, text=True)
        last = [l for l in res.stdout.splitlines() if " nodes " in l]
        m = re.search(r"(\d+) nodes\s+split (\d+)\s+pkill (\d+)\s+kill (\d+)\s+leaf (\d+) (\{.*?\})\s+failed (\d+)\s+children never seen (\d+).*(OK|NOT VERIFIED)", last[-1]) if last else None
        line = "%-34s nodes %7s split %7s pkill %7s kill %7s leaf %5s %s failed %s missing %s  %s  enum %.0fs check %.0fs" % (
            spec, *(m.groups() if m else ("?",) * 9), te, time.time() - t1)
    with open(SUM, "a") as f: f.write(line + "\n")
    print(time.strftime("%m-%d %H:%M  ") + line, flush=True)
print(time.strftime("%m-%d %H:%M  ") + "done", flush=True)
