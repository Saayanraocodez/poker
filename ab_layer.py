"""A/B test of the layer-test ladder on a branch enumc2 verified (a11:MIX,a21:MIX,a31:MIX,a41:1:
59,300 nodes, 1,024 s at 20 workers): KUHN_RUNGS_LAYER=0 (enumc5) vs 0,1,2,3 (enumc2), everything
else equal, both at once with the same workers.  usage:  python ab_layer.py [workers] [limit s]"""
import subprocess, sys, os, time, glob
os.chdir(os.path.dirname(os.path.abspath(__file__)))
SPEC = "a11:MIX,a21:MIX,a31:MIX,a41:1"
NW = sys.argv[1] if len(sys.argv) > 1 else "4"
LIMIT = float(sys.argv[2]) if len(sys.argv) > 2 else 7200
ARMS = {"c6ab_r0": "0", "c6ab_full": "0,1,2,3"}
procs = {}
for tag, rungs in ARMS.items():
    for f in glob.glob("enumc_%s.*" % tag): os.remove(f)
    env = dict(os.environ, KUHN_MODE="nash", KUHN_ORDER="bet", KUHN_RUNGS_LAYER=rungs, KUHN_RUNGS_FDEAD="0,1,2,3",
               KUHN_RUNGS_FDEADU="0", KUHN_JOBSECS="300", KUHN_CKPT="300")
    procs[tag] = (subprocess.Popen([sys.executable, "-u", "enumc6.py", SPEC, NW, tag], stdout=open("log_enumc6_%s.txt" % tag, "w"),
                                   stderr=subprocess.STDOUT, env=env), time.time())
while procs:
    time.sleep(10)
    for tag, (p, t0) in list(procs.items()):
        if p.poll() is not None:
            print("%s finished rc=%d after %.0fs" % (tag, p.returncode, time.time() - t0), flush=True); del procs[tag]
        elif time.time() - t0 > LIMIT:
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait(); print("%s stopped at the %.0fs limit" % (tag, LIMIT), flush=True); del procs[tag]
