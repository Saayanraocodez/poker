"""Ask Windows not to idle-sleep while a long run is going.

On 2026-09-03 the box slept at 23:19 and woke at 10:23 -- 11h 4m in which the
screen completed zero jobs and the seven feasibility tasks advanced about as far
as they normally do in twelve minutes.  Nothing was lost (both runs checkpoint),
but nothing was gained either, and neither log says "asleep": pipe2 simply stops
printing, which reads exactly like a hang.

This is a *request*, not a settings change -- SetThreadExecutionState is the
same call a video player makes.  It lasts only as long as this process, so
killing it restores the machine's normal behaviour with nothing to undo.  Only
system sleep is held off; the display is deliberately left alone so the monitor
still blanks.  It does not stop a deliberate sleep (Start menu, lid, power
button), only the idle timer.

usage:  python keepawake.py            # hold until killed
        python keepawake.py <hours>    # hold for a while, then release
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

import ctypes, sys, time, datetime
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



ES_CONTINUOUS       = 0x80000000
ES_SYSTEM_REQUIRED  = 0x00000001

k32 = ctypes.windll.kernel32
hours = float(sys.argv[1]) if len(sys.argv) > 1 else None

if not k32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED):
    sys.exit("SetThreadExecutionState failed -- the machine may still sleep")
print("holding off idle sleep from %s (pid %d)%s"
      % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), __import__("os").getpid(),
         "" if hours is None else "  for %.1fh" % hours), flush=True)
try:
    t0 = time.time()
    while hours is None or time.time() - t0 < hours * 3600:
        time.sleep(300)
        # A heartbeat, so an idle log is never ambiguous about whether this is
        # still alive -- the failure it exists to prevent looked like a hang.
        print("   awake-hold ok  %s  %.1fh"
              % (datetime.datetime.now().strftime("%H:%M"),
                 (time.time() - t0) / 3600), flush=True)
finally:
    k32.SetThreadExecutionState(ES_CONTINUOUS)
    print("released; normal sleep behaviour restored", flush=True)
