"""Control for enumc6's durability: an interrupted, tampered, resumed run must replay OK in
checkenum, like an uninterrupted one.  Not bit-identical by design (resumed jobs get fresh ids
and count depth from the root), so the checks are: every record replays, no child is missing,
no id is written twice, and the verdicts agree with the uninterrupted run.
usage:  python control_resume.py [workers]"""
import subprocess, sys, os, time, gzip, json, random, re, glob
os.chdir(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.environ.get("CTL_SPEC", "a11:MIX,a21:0,a31:1,a41:1")
NW = sys.argv[1] if len(sys.argv) > 1 else "8"
ENV = dict(os.environ, KUHN_MODE="nash", KUHN_ORDER="bet", KUHN_RUNGS_LAYER="0", KUHN_RUNGS_FDEAD="0,1,2,3",
           KUHN_RUNGS_FDEADU="0", KUHN_JOBSECS="60", KUHN_CKPT="15", KUHN_BUDGET="100")


def clean(tag):
    for f in glob.glob("enumc_%s.*" % tag) + glob.glob("log_enumc6_%s.txt" % tag): os.remove(f)


def run(tag, secs=None):
    with open("log_enumc6_%s.txt" % tag, "a") as f:
        f.write("----- run (limit %s)\n" % secs); f.flush()
        p = subprocess.Popen([sys.executable, "-u", "enumc6.py", SPEC, NW, tag], stdout=f, stderr=subprocess.STDOUT, env=ENV)
        try:
            p.wait(timeout=secs); return "finished rc=%d" % p.returncode
        except subprocess.TimeoutExpired:
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait(); return "KILLED"


def check(tag):
    r = subprocess.run([sys.executable, "-u", "checkenum.py", "enumc_%s.jsonl.gz" % tag, NW], capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if "nodes" in l][-1:] or r.stdout.splitlines()[-3:] + r.stderr.splitlines()[-3:]


def ids(tag):
    seen = {}; dup = 0
    with gzip.open("enumc_%s.jsonl.gz" % tag, "rt") as f:
        f.readline()
        for l in f:
            m = re.match(r'^\{"id": (\d+), "kind": "(\w+)"', l)
            i = int(m.group(1)); dup += i in seen; seen[i] = m.group(2)
    return len(seen), dup


if __name__ == "__main__":
    t0 = time.time()
    if not os.environ.get("SKIP_A"):
        clean("c6ctlA"); print("A uninterrupted:", run("c6ctlA"), "%.0fs" % (time.time() - t0), flush=True)
        print("   check:", check("c6ctlA"), " records/dups:", ids("c6ctlA"), flush=True)
    tag = "c6ctlB"; clean(tag); t1 = time.time()
    print("B1 kill in the top expansion:", run(tag, 4), flush=True)
    print("B2 kill in the pool phase:   ", run(tag, 170), flush=True)
    print("B3 kill again:               ", run(tag, 90), flush=True)
    with open("enumc_%s.jsonl.gz" % tag, "ab") as f: f.write(bytes(random.getrandbits(8) for _ in range(5000)))
    print("   appended 5000 junk bytes past the checkpoint", flush=True)
    print("B4 resume over junk, kill:   ", run(tag, 90), flush=True)
    os.remove("enumc_%s.ckpt" % tag); print("   deleted the .ckpt (forces the migration path)", flush=True)
    print("B5 migrate, resume, kill:    ", run(tag, 90), flush=True)
    os.replace("enumc_%s.jsonl.gz" % tag, "enumc_%s.jsonl.gz.premigrate" % tag); os.remove("enumc_%s.ckpt" % tag)
    print("   simulated a kill between the migration's renames (output moved aside, no .ckpt)", flush=True)
    print("B6 resume to the end:        ", run(tag), "%.0fs" % (time.time() - t1), flush=True)
    print("   check:", check(tag), " records/dups:", ids(tag), flush=True)
    print("resume lines:"); os.system('findstr /C:"RESUMED" /C:"migrated" /C:"afresh" /C:"restored" log_enumc6_%s.txt' % tag)
