"""Pure feasibility: is there ANY equilibrium inside a restricted box?

Restartable.  Each task drives `bnb5.search` with a checkpoint prefix, so an
interruption costs at most `ckevery` seconds instead of the whole task -- the
two 22-hour tasks lost to a shutdown on 2026-09-02 are the reason.  Rerunning
the same command resumes every unfinished task and skips the finished ones.

The emitted boxes are converted from the spill to fbox_{lo,hi}_<tag>.npy inside
the worker.  They used to be pickled back through the pool, which for a
2.4M-box task meant shipping ~1.8 GB down a pipe for no reason.

usage:  python feas.py "<list of (tag, cons, maxnodes, wtol, maxdepth)>" <workers>
"""
import numpy as np, sys, time, ast, os, subprocess, bnb5, kuhn3p as K
from multiprocessing import Pool
I = K.NAME_IDX
CK = "ckf_%s"                      # checkpoint/spill prefix, one per task tag


def _alive(pid):
    """True if pid is a live python process.  tasklist, not Get-Process: the
    Store interpreter is named python3.13 and nothing else matches reliably."""
    try:
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return False
    return ("python" in out.lower()) and (str(pid) in out)


def take_lock(tag):
    """One live owner per tag.

    Now that boxes are appended to a shared spill file, two runs on one tag
    interleave their writes and the .npy pair is neither run's answer -- a
    wrong result, not a slow one.  This box has form: five duplicate runs once
    stacked on 28 cores because a liveness check silently reported nothing."""
    lk = "lockf_%s.pid" % tag
    if os.path.exists(lk):
        try:
            other = int(open(lk).read().strip())
        except Exception:
            other = -1
        if other != os.getpid() and _alive(other):
            raise SystemExit("task '%s' is already owned by live pid %d (%s); "
                             "two runs would interleave writes into the same "
                             "spill file." % (tag, other, lk))
        print("   [%s] stale %s (pid %d gone) -- taking over" % (tag, lk, other),
              flush=True)
    with open(lk, "w") as f:
        f.write(str(os.getpid()))
    return lk

def _job(a):
    tag, cons, maxnodes, wtol, maxdepth = a
    lk = take_lock(tag)
    LO = np.zeros(48); HI = np.ones(48)
    for n, lo, hi in cons:
        LO[I[n]] = lo; HI[I[n]] = hi
    t0 = time.time()
    try:
        st, _ = bnb5.search(LO0=LO, HI0=HI, wtol=wtol, maxdepth=maxdepth,
                            cap=4096, maxnodes=maxnodes, log=2000, tag=tag,
                            ckpt=CK % tag, ckevery=900)
        n = 0
        if os.path.exists(bnb5._spill_paths(CK % tag)[0]):
            n = bnb5.spill_to_npy(CK % tag, "fbox_lo_%s.npy" % tag,
                                  "fbox_hi_%s.npy" % tag)
    finally:
        # Release on the way out however we leave, so a crashed task does not
        # need a human to clear its lock before the rerun.  A kill -9 still
        # leaves the file, which is why take_lock checks liveness rather than
        # mere existence.
        try: os.remove(lk)
        except OSError: pass
    # The spill and the box counter are written by two different mechanisms; if
    # they disagree the .npy pair is not the search's answer, and saying so
    # loudly beats shipping a quietly wrong box set to the LM stage.
    if n != st['boxes']:
        return tag, st, st.get('elapsed', time.time() - t0), n, \
               "*** MISMATCH spill=%d st.boxes=%d" % (n, st['boxes'])
    return tag, st, st.get('elapsed', time.time() - t0), n, ""

if __name__ == "__main__":
    tasks = ast.literal_eval(sys.argv[1]); nw = int(sys.argv[2])
    bad = 0
    with Pool(nw) as pool:
        for tag, st, dt, n, warn in pool.imap_unordered(_job, tasks):
            verdict = "EMPTY (proven)" if (st['boxes'] == 0 and not st.get('ABORT')) \
                      else ("open: %d boxes" % st['boxes'])
            print("%-22s nodes=%-9d %-22s abort=%-5s %.0fs %s"
                  % (tag, st['nodes'], verdict, st.get('ABORT', False), dt, warn),
                  flush=True)
            bad += bool(warn)
    print("DONE" if not bad else "DONE WITH %d MISMATCHES" % bad, flush=True)
