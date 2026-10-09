"""Summarise the latest faulthandler dump of each worker: its innermost project frames.
usage:  python tracetops.py <prefix>      (reads trace_<prefix>_*.txt)"""
import glob, re, sys
pre = sys.argv[1] if len(sys.argv) > 1 else "c4"
for f in sorted(glob.glob("trace_%s_*.txt" % pre)):
    blocks = open(f, errors="replace").read().split("Timeout")
    last = blocks[-1] if len(blocks) > 1 else ""
    frames = re.findall(r'File "[^"]*\\([A-Za-z0-9_]+\.py)", line (\d+) in (\w+)', last)
    mine = [("%s:%s %s" % fr) for fr in frames if fr[0] not in ("pool.py", "process.py", "spawn.py", "queues.py", "synchronize.py", "connection.py")]
    state = "idle (waiting for work)" if not mine else " <- ".join(mine[:4])
    print("%-24s dumps %2d   %s" % (f, len(blocks) - 1, state))
