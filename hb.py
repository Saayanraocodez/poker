"""Heartbeat probe: does a detached python survive on this box at all?"""
import signal, time, datetime, os, sys
for s in ("SIGINT", "SIGBREAK"):
    if hasattr(signal, s):
        try: signal.signal(getattr(signal, s), signal.SIG_IGN)
        except Exception: pass
with open("log_hb.txt", "a", buffering=1) as f:
    f.write("start %s pid %d ppid %d\n" % (datetime.datetime.now().strftime("%H:%M:%S"), os.getpid(), os.getppid()))
    for i in range(240):
        time.sleep(5)
        f.write("alive %s  %d\n" % (datetime.datetime.now().strftime("%H:%M:%S"), i))
