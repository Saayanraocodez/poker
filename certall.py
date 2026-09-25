"""Certificates for every leaf set of a runbet6 ledger (both modes) plus the
silent branch: certleaf.py then checkcert.py per tag, one summary table.

usage:  python certall.py <suffix> <workers> [maxnodes]
        e.g.  python certall.py R 16      -> cert_<tag>.json.gz for every tag,
              cert_summary_R.txt (leaves, certified by class, verified, failed, seconds)
"""
import subprocess, sys, os, re, time, json, gzip

XS = sys.argv[1]; nw = sys.argv[2]; maxnodes = sys.argv[3] if len(sys.argv) > 3 else "300"

def tag_of(spec, nash):
    return "b_" + "_".join(p.split(":")[1].replace("MIX", "M") for p in spec.split(",")) + ("N" if nash else "") + XS

tags = [("silent", "silent" + XS)]
for nash in (True, False):
    path = "runbet6_summary%s%s.txt" % ("_nash" if nash else "", XS)
    if not os.path.exists(path): continue
    for line in open(path):
        if not line.strip() or "FAILED" in line: continue
        spec = line.split()[0]
        n = int(re.search(r"leaves\s+(\d+)", line).group(1))
        if n: tags.append((spec + (" [nash]" if nash else " [seq]"), tag_of(spec, nash)))
out = "cert_summary_%s.txt" % XS
done = set()
if os.path.exists(out):
    for line in open(out):
        if line.strip() and not line.startswith("#"): done.add(line.split()[0])
with open(out, "a") as f:
    if not done: f.write("# tag  leaves  certified{class:n}  verified  failed  gen_s  check_s\n")
for name, tag in tags:
    if tag in done or not os.path.exists("enum6_pat_%s.npy" % tag): continue
    t0 = time.time()
    subprocess.call([sys.executable, "-u", "certleaf.py", tag, nw, maxnodes], stdout=open("log_certleaf_%s.txt" % tag, "w"), stderr=subprocess.STDOUT)
    tg = time.time() - t0; t1 = time.time()
    res = subprocess.run([sys.executable, "-u", "checkcert.py", "cert_%s.json.gz" % tag], capture_output=True, text=True)
    tc = time.time() - t1
    last = [l for l in res.stdout.splitlines() if l.startswith("checked")]
    m = re.search(r"checked (\d+) leaves: (\d+) verified (\{.*\}), (\d+) failed", last[-1]) if last else None
    with gzip.open("cert_%s.json.gz" % tag, "rt") as fz: data = json.load(fz)
    cnt = {}
    for r in data["leaves_cert"]: cnt[r["verdict"]] = cnt.get(r["verdict"], 0) + 1
    line = "%-28s %7d  %s  verified %s  failed %s  gen %.0fs  check %.0fs   # %s" % (
        tag, len(data["leaves_cert"]), json.dumps(cnt, sort_keys=True), m.group(2) if m else "?", m.group(4) if m else "?", tg, tc, name)
    with open(out, "a") as f: f.write(line + "\n")
    print(line, flush=True)
