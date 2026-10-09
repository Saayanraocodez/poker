"""Re-verify EVERY stored certificate after the checker was tightened (2026-09-26):
check_box_cert now requires a certificate's starting box to contain everything the
node's labels allow (previously the declared box was taken on trust).

  1. leaf certificates   -- checkcert.py on every tag of cert_summary_R.txt (66,699 leaves)
  2. range certificates  -- checknefull.py (the complete Nash set's 522 ranges)
  3. certificate trees   -- checkenum.py on every branch the ledger calls OK (71 branches)

Writes recheck_summary.txt.  usage (windowless):  pythonw.exe recheck_all.py [workers]"""
import sys as _sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _sys.stdout = _sys.stderr = open("log_recheck_all.txt", "a", buffering=1, encoding="utf-8", errors="replace")
import subprocess, sys, time, re
from concurrent.futures import ThreadPoolExecutor

NW = sys.argv[1] if len(sys.argv) > 1 else "24"
OUT = "recheck_summary.txt"
out = open(OUT, "w", buffering=1)
def say(s):
    line = time.strftime("%m-%d %H:%M  ") + s
    out.write(line + "\n"); print(line, flush=True)

say("checker: check_box_cert requires the starting box to contain the label box")
# 1. leaf certificates
tags = []
for l in open("cert_summary_R.txt"):
    if l.startswith("#") or not l.strip(): continue
    tags.append(l.split()[0])
def leafcheck(tag):
    t0 = time.time()
    r = subprocess.run([sys.executable, "-u", "checkcert.py", "cert_%s.json.gz" % tag], capture_output=True, text=True)
    last = [x for x in r.stdout.splitlines() if x.startswith("checked")]
    fails = [x for x in r.stdout.splitlines() if "FAILED" in x or "ERROR" in x]
    return tag, (last[-1] if last else "NO SUMMARY LINE: " + (r.stderr.strip().splitlines() or ["?"])[-1]), fails[:3], time.time() - t0
tot_ok = tot_bad = 0
with ThreadPoolExecutor(8) as ex:
    for tag, last, fails, secs in ex.map(leafcheck, tags):
        m = re.search(r"(\d+) verified.*?(\d+) failed", last)
        if m: tot_ok += int(m.group(1)); tot_bad += int(m.group(2))
        else: tot_bad += 1
        say("leaf  %-22s %s  (%.0fs)" % (tag, last, secs))
        for f in fails: say("      " + f)
say("LEAF CERTIFICATES: %d verified, %d failed" % (tot_ok, tot_bad))

# 2. range certificates of the complete Nash set
r = subprocess.run([sys.executable, "-u", "checknefull.py"], capture_output=True, text=True)
say("RANGES: " + " | ".join(x for x in r.stdout.splitlines()[-3:] if x.strip()))

# 3. the certified enumeration trees
ok_specs = [l.split()[0] for l in open("enumc_summary_nash.txt") if " OK " in l]
bad_trees = 0; nodes = 0
for spec in ok_specs:
    tag = "c_" + "_".join(p.split(":")[1].replace("MIX", "M") for p in spec.split(",")) + "N"
    t0 = time.time()
    r = subprocess.run([sys.executable, "-u", "checkenum.py", "enumc_%s.jsonl.gz" % tag, NW], capture_output=True, text=True)
    last = [x for x in r.stdout.splitlines() if " nodes " in x]
    line = last[-1] if last else "NO SUMMARY LINE: " + (r.stderr.strip().splitlines() or ["?"])[-1]
    m = re.search(r"(\d+) nodes", line)
    if m: nodes += int(m.group(1))
    if "OK" not in line: bad_trees += 1
    say("tree  %-34s %s" % (spec, line.split(":", 1)[-1].strip()[:150]))
say("CERTIFICATE TREES: %d of %d branches OK, %d nodes replayed" % (len(ok_specs) - bad_trees, len(ok_specs), nodes))
say("done")
