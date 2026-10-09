"""Windowless launcher for enumc3.  enumc3 must run as a real __main__ script (its pool's
spawned workers re-import the main module), so it is started as a subprocess, not via runpy.
usage:  pythonw.exe start_enumc3.py <spec> <workers> <tag> [KEY=VALUE ...]"""
import os, sys, subprocess
os.chdir(os.path.dirname(os.path.abspath(__file__)))
env = dict(os.environ); env.setdefault("KUHN_MODE", "nash"); env.setdefault("KUHN_ORDER", "bet")
spec, nw, tag = sys.argv[1:4]
# extra KEY=VALUE settings, from the command line and from run_<tag>.env (schtasks truncates a
# task's command at 261 characters, which silently cut the last setting in half once)
extra = list(sys.argv[4:])
if os.path.exists("run_%s.env" % tag):
    extra += [l.strip() for l in open("run_%s.env" % tag) if "=" in l and not l.startswith("#")]
for kv in extra:
    k, v = kv.split("=", 1); env[k.strip()] = v.strip()
SCRIPT = env.get("KUHN_SCRIPT", "enumc3.py")
with open("log_enumc3_%s.txt" % tag, "w") as f:
    subprocess.call([sys.executable, "-u", SCRIPT, spec, nw, tag], stdout=f, stderr=subprocess.STDOUT, env=env)
