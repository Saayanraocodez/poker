"""A/B of the layer-test ladder for the 5-card exact-propagation prover on one timed-out cell:
arms run at once with equal workers and a time limit; compare completion, nodes, queue.
usage (from k35/):  KUHN_CARDS=5 python ab_k5.py <spec> <workers per arm> <limit s> <arm=rungs> ...
e.g.  python ab_k5.py "a11:MIX,a21:0,a31:0,a41:0,a51:1" 9 5400 full=0,1,2,3 r0=0 r02=0,2"""
import subprocess, sys, os, time, glob
os.chdir(os.path.dirname(os.path.abspath(__file__)))
spec, nw, limit = sys.argv[1], sys.argv[2], float(sys.argv[3])
arms = dict(a.split("=", 1) for a in sys.argv[4:])
procs = {}
for name, rungs in arms.items():
    tag = "k5ab_%s" % name
    for f in glob.glob("enumc_%s.*" % tag): os.remove(f)
    env = dict(os.environ, KUHN_CARDS="5", KUHN_MODE="nash", KUHN_ORDER="bet", KUHN_RUNGS_LAYER=rungs, KUHN_CKPT="300")
    procs[name] = (subprocess.Popen([sys.executable, "-u", "enumc7.py", spec, nw, tag], stdout=open("log_enumc7_%s.txt" % tag, "w"),
                                    stderr=subprocess.STDOUT, env=env), time.time())
while procs:
    time.sleep(10)
    for name, (p, t0) in list(procs.items()):
        if p.poll() is not None:
            print("%s (%s) finished rc=%d after %.0fs" % (name, arms[name], p.returncode, time.time() - t0), flush=True); del procs[name]
        elif time.time() - t0 > limit:
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait(); print("%s (%s) stopped at the %.0fs limit" % (name, arms[name], limit), flush=True); del procs[name]
