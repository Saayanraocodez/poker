"""Silent-branch pipeline with checkpointing and resume.

Same algorithm and same outputs as pipe.py (sound bisection prune -> LM
feasibility), but results are flushed to disk as each job returns instead of
only after the whole pool finishes.  A multi-hour run over pats_rest.npy that
is interrupted -- killed, machine sleeps, competing job -- keeps everything it
had already proven, and a rerun with the same tag skips the finished jobs.

usage:  python pipe2.py <patterns.npy> <workers> <depth> <tag>

state:  ck_<tag>.npz          job bookkeeping + tallies (rewritten atomically)
        surv_pat_<tag>.npy    survivors so far
        surv_x_<tag>.npy      their LM points
        surv_r_<tag>.npy      their residuals
"""
import numpy as np, sys, time, os, subprocess
from pipe import process          # identical per-job work, imported not copied

STEP = 10000


def _alive(pid):
    """True if `pid` is a live python process.  tasklist, because the Store
    interpreter is named python3.13 and nothing else here matches reliably."""
    try:
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return False                      # cannot tell -> do not block the user
    return ("python" in out.lower()) and (str(pid) in out)


def take_lock(tag):
    """Refuse to start if another pipe2 already owns this tag.

    Two runs sharing a tag write the same ck_<tag>.npz and the same
    surv_<tag>.npy.  The checkpoints merely overwrite each other (jobs get
    redone -- wasteful, still sound), but the survivor arrays do not: each
    process writes its OWN accumulated list, so last-writer-wins can silently
    DROP certified survivors.  That is a wrong result, not a slow one.
    """
    lk = "lock_%s.pid" % tag
    if os.path.exists(lk):
        try:
            other = int(open(lk).read().strip())
        except Exception:
            other = -1
        if other != os.getpid() and _alive(other):
            sys.exit("tag '%s' is already owned by live pid %d (%s).\n"
                     "Two runs on one tag can drop survivors from surv_pat_%s.npy.\n"
                     "Use a different tag, or stop that run first."
                     % (tag, other, lk, tag))
        print("stale %s (pid %d not running) -- taking over" % (lk, other), flush=True)
    with open(lk, "w") as f:
        f.write(str(os.getpid()))
    return lk


def _job(a):
    """Carry the job's start index through the worker.

    imap_unordered returns results in completion order, so the arrival index
    says nothing about which job finished.  Without this the checkpoint would
    mark the wrong jobs done and a resume would silently skip unsearched
    patterns -- the exact failure mode that leaves a gap in an exhaustive
    claim while the run still looks healthy.
    """
    return a[0], process(a)


def _replace(tmp, path, tries=8):
    """os.replace, retried.

    Windows refuses to replace a file that anything holds open, raising
    PermissionError [WinError 5].  The cause here was our own un-closed
    NpzFile on resume (see the resume block) -- NOT OneDrive, which was the
    first and wrong diagnosis; the retries all failed because the handle was
    ours and permanent.  The retry stays as cheap insurance against a genuinely
    transient holder such as the sync client or a concurrent status read, but
    it is not a substitute for closing our own handles.
    """
    for k in range(tries):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if k == tries - 1:
                raise
            time.sleep(0.4 * (k + 1))


def _atomic_save(path, arr):
    tmp = path + ".tmp.npy"
    np.save(tmp, arr)
    _replace(tmp, path)


def _atomic_savez(path, **kw):
    tmp = path + ".tmp.npz"
    np.savez(tmp, **kw)
    _replace(tmp, path)


if __name__ == "__main__":
    from multiprocessing import Pool
    path = sys.argv[1]; nw = int(sys.argv[2]); depth = int(sys.argv[3]); tag = sys.argv[4]
    lk = take_lock(tag)

    N = np.load(path, mmap_mode='r').shape[0]
    starts = list(range(0, N, STEP))
    ck = "ck_%s.npz" % tag
    pat_f = "surv_pat_%s.npy" % tag
    x_f = "surv_x_%s.npy" % tag
    r_f = "surv_r_%s.npy" % tag

    # ---- resume ----------------------------------------------------------
    done = set(); pv = 0; bx = 0; tot = 0; elapsed = 0.0
    AP = np.zeros((0, 48), np.int8); AX = np.zeros((0, 48)); AR = np.zeros(0)
    if os.path.exists(ck):
        # np.load on an .npz returns a LAZY NpzFile that holds the file open.
        # Leaving it open makes every later os.replace onto this path fail with
        # PermissionError [WinError 5] -- Windows will not replace a file with a
        # live handle.  Only resumed runs hit it (a fresh run never opens the
        # checkpoint), which is exactly the shape of the two crashes here.
        # Read everything out inside the context manager and close it.
        with np.load(ck) as z:
            done = set(int(v) for v in z['done'])
            pv, bx, tot = int(z['pv']), int(z['bx']), int(z['tot'])
            elapsed = float(z['elapsed'])
            ns_ck = int(z['nsurv']) if 'nsurv' in z.files else None
        if os.path.exists(pat_f):
            AP = np.load(pat_f); AX = np.load(x_f); AR = np.load(r_f)
            # The survivor arrays are written BEFORE the checkpoint, so a crash
            # between the two leaves them ahead of the record.  Those extra rows
            # belong to a job that is NOT marked done and will be re-run, so
            # keeping them would double-count survivors.  The checkpoint's count
            # is authoritative; trim back to it.
            ns = len(AP) if ns_ck is None else ns_ck
            if len(AP) > ns:
                print("  trimming %d survivor rows written past the last checkpoint"
                      % (len(AP) - ns), flush=True)
                AP, AX, AR = AP[:ns], AX[:ns], AR[:ns]
        print("resuming %s: %d/%d jobs already done, %d proven infeasible, %d survivors, %.0fs prior"
              % (tag, len(done), len(starts), pv, len(AP), elapsed), flush=True)

    todo = [(i, min(i + STEP, N), path, depth, i) for i in starts if i not in done]
    print("patterns %d  jobs %d  remaining %d  workers %d  depth %d"
          % (N, len(starts), len(todo), nw, depth), flush=True)
    if not todo:
        print("nothing to do", flush=True); sys.exit(0)

    t0 = time.time()
    try:
        with Pool(nw) as pool:
            for k, (lo, (sp, sx, sr, npv, nb, nt)) in enumerate(
                    pool.imap_unordered(_job, todo)):
                done.add(int(lo))
                if len(sp):
                    AP = np.concatenate([AP, sp]); AX = np.concatenate([AX, sx])
                    AR = np.concatenate([AR, sr])
                pv += npv; bx += nb; tot += nt
                _atomic_save(pat_f, AP); _atomic_save(x_f, AX); _atomic_save(r_f, AR)
                _atomic_savez(ck, done=np.array(sorted(done)), pv=pv, bx=bx, tot=tot,
                              nsurv=len(AP), elapsed=elapsed + time.time() - t0)
                nd = len(done)
                frac = nd / len(starts)
                rate = (time.time() - t0) / (k + 1)
                eta = rate * (len(todo) - k - 1)
                print("  %d/%d (%.1f%%)  proven-infeasible %d/%d (%.1f%%)  survivors %d"
                      "  %.0fs elapsed  ETA %.0fm"
                      % (nd, len(starts), 100 * frac, pv, tot,
                         100 * pv / max(tot, 1), len(AP),
                         time.time() - t0, eta / 60), flush=True)
    except KeyboardInterrupt:
        print("\ninterrupted -- checkpoint holds %d/%d jobs" % (len(done), len(starts)), flush=True)
        sys.exit(130)

    print("TOTAL patterns %d  proven infeasible %d (%.2f%%)  boxes %d  LM survivors %d  %.0fs"
          % (tot, pv, 100 * pv / max(tot, 1), bx, len(AP), time.time() - t0), flush=True)
