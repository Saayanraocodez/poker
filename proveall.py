"""Push the P1-silent branch from 80.3 % PROVEN toward 100 %.

The branch is exhaustively enumerated (3,045,358 patterns) and fully screened,
but `pipe2` ran the proving stage -- `bisbatch.bisect` -- at depth 8, which
proves only 80.3 % infeasible.  The other 19.7 % rests on LM failing to find a
point there, and a failed search is not a proof.  That gap is the whole distance
between "the search found nothing outside the family in this branch" and
"nothing outside the family is there".

Depth is one argument, and unlike every other lever in this project its cost
grows roughly LINEARLY rather than geometrically (measured on a 4,000-pattern
sample, `log_depthproof.txt`):

    depth      8      10      12      14      16
    proven 81.30%  85.72%  89.72%  92.75%  95.28%
    sec         7      13      20      28      46

So this is cheap, and it converts search into proof.

Survivors are saved, so a later deeper pass runs only on the residual instead of
re-proving the whole branch -- iterative deepening, where each round is cheaper
than the last because the input shrinks.

CONTROL (pre-flight, refuses to run on failure): the support pattern of every
known certified equilibrium must SURVIVE bisection at this depth.  If the prover
ever kills one, every "proven infeasible" verdict it produces is worthless, and
the failure is silent -- the run still completes and reports a higher, wronger
number.  This is the same class of trap as an unsound prune passing unnoticed.

usage:  python proveall.py <patterns.npy> <depth> <workers> <tag>

state:  prove_<tag>.npz        counters + packed bitmask of finished chunks
        prove_surv_<tag>.npy   patterns NOT proven infeasible (the residual)
"""
import numpy as np, sys, os, time, subprocess
import bisbatch, bnb, classify, eqtools as E

MIX = bnb.MIX
STEP = 2000
CKEVERY = 25


def pattern_of(p, tol=1e-9):
    """The support pattern a profile induces: 0 / 1 / interior."""
    lab = np.full(48, MIX, np.int8)
    lab[p <= tol] = 0
    lab[p >= 1 - tol] = 1
    return lab


def preflight(depth, path, nctl=256, block=1024):
    """Known equilibria must survive the prover.  Refuse to run otherwise.

    The controls are EMBEDDED in a block of real patterns rather than bisected
    on their own, for one correctness reason and one speed reason.  `bisect`
    shares a single `keepcap` across a whole block, so the refinement any one
    pattern actually receives depends on its blockmates -- a control bisected
    alone is not being put through what the run puts patterns through.  And a
    block of nothing but feasible patterns prunes nothing, so it doubles at
    every level straight into `keepcap`: a standalone control set of 3,000 took
    minutes while testing less than this does.
    """
    # The controls must be the ENUMERATED patterns that carried the certified
    # equilibria (surv_pat_*), not patterns reconstructed from the profiles'
    # coordinate values.  Reconstruction cannot produce the DC label, because DC
    # means "this information set is provably unreachable" -- a fact about
    # propagation, not about the coordinate's value, which off path is whatever
    # the solver happened to leave there.  Labelling an off-path coordinate MIX
    # or 0/1 from its value asserts a condition propagation then contradicts, and
    # bisect correctly kills the pattern: reconstruction killed 235 of 256 at
    # depth 16 while the enumerated patterns lose 0 of 256 at the same depth.
    # That difference is the control, not the prover.  Same family as the
    # off-path-coordinates trap in s7.7.
    src = [f for f in ("surv_pat_samp.npy", "surv_pat_rest.npy") if os.path.exists(f)]
    if not src:
        sys.exit("no enumerated survivor patterns on disk (surv_pat_*.npy); "
                 "refusing to run without a control")
    S = np.concatenate([np.load(f) for f in src]).astype(np.int8)
    ctl = S if len(S) <= nctl else S[np.linspace(0, len(S) - 1, nctl).astype(np.int64)]
    ex = np.zeros(1)                       # these patterns are LM-feasible by
    if os.path.exists("certified_eq_all.npy"):   # construction; report the
        Q = np.load("certified_eq_all.npy")      # certified set's quality too
        ex = np.array([float(np.abs(E.expl(q)).max()) for q in Q[:256]])
        if not (ex < 1e-13).all():
            sys.exit("certified set contains non-equilibria; a bad control "
                     "proves nothing when it dies")

    real = np.load(path, mmap_mode='r')
    rng = np.random.default_rng(0)
    pick = np.sort(rng.choice(real.shape[0], size=max(block - len(ctl), 1),
                              replace=False))
    blk = np.concatenate([ctl, np.asarray(real[pick]).astype(np.int8)])
    pid, _, _, _ = bisbatch.bisect(blk, depth=depth)
    alive = set(np.unique(pid).tolist())
    killed = [i for i in range(len(ctl)) if i not in alive]
    print("pre-flight: %d enumerated patterns known to carry certified equilibria, "
          "embedded in a %d-pattern block (certified set max expl %.2e); "
          "killed at depth %d: %d"
          % (len(ctl), len(blk), ex.max(), depth, len(killed)), flush=True)
    if killed:
        sys.exit("PRE-FLIGHT FAILED: the prover killed %d enumerated patterns "
                 "that carry a real equilibrium. Every 'proven infeasible' "
                 "verdict at this depth would be unsound." % len(killed))
    print("pre-flight PASSED\n", flush=True)


def _alive(pid):
    try:
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return False
    return ("python" in out.lower()) and (str(pid) in out)


def take_lock(tag):
    lk = "lockp_%s.pid" % tag
    if os.path.exists(lk):
        try:
            other = int(open(lk).read().strip())
        except Exception:
            other = -1
        if other != os.getpid() and _alive(other):
            sys.exit("tag '%s' is owned by live pid %d (%s)" % (tag, other, lk))
        print("stale %s (pid %d gone) -- taking over" % (lk, other), flush=True)
    with open(lk, "w") as f:
        f.write(str(os.getpid()))
    return lk


def _replace(tmp, path, tries=8):
    for k in range(tries):
        try:
            os.replace(tmp, path); return
        except PermissionError:
            if k == tries - 1:
                raise
            time.sleep(0.4 * (k + 1))


def _atomic_save(path, arr):
    tmp = path + ".tmp.npy"; np.save(tmp, arr); _replace(tmp, path)


def _atomic_savez(path, **kw):
    tmp = path + ".tmp.npz"; np.savez(tmp, **kw); _replace(tmp, path)


def job(a):
    lo, hi, path, depth = a
    P = np.asarray(np.load(path, mmap_mode='r')[lo:hi]).astype(np.int8)
    proven = 0
    surv = []
    # `bisect` shares ONE keepcap across a whole block, so the block size decides
    # how much refinement each pattern actually gets.  At depth 8 that is
    # invisible (measured: 81.10 % proven at every block size from 32 to 1024,
    # so the published 80.3 % is unaffected).  Deeper it dominates -- on the
    # depth-16 residual, same depth, same patterns:
    #
    #     block 1024 ->   33 of 2048 proven (1.61 %)
    #     block  128 ->  651 of 2048 proven (31.79 %)
    #     block   32 ->  651 of 2048 proven (31.79 %), and faster than 128
    #
    # A 20x difference from a batching constant.  Keep this small; the extra
    # boxes are the entire point.
    CH = 32
    for s in range(0, P.shape[0], CH):
        b = P[s:s+CH]
        pid, _, _, _ = bisbatch.bisect(b, depth=depth)
        alive = np.unique(pid)
        proven += b.shape[0] - len(alive)
        if len(alive):
            surv.append(b[alive])
    S = np.concatenate(surv) if surv else np.zeros((0, 48), np.int8)
    return lo, proven, P.shape[0], S


if __name__ == "__main__":
    from multiprocessing import Pool
    path = sys.argv[1]; depth = int(sys.argv[2])
    nw = int(sys.argv[3]); tag = sys.argv[4]

    preflight(depth, path)
    lk = take_lock(tag)

    N = np.load(path, mmap_mode='r').shape[0]
    starts = list(range(0, N, STEP))
    ck = "prove_%s.npz" % tag
    sf = "prove_surv_%s.npy" % tag
    donemask = np.zeros(len(starts), bool)
    proven = tot = 0; elapsed = 0.0
    SURV = []
    if os.path.exists(ck):
        with np.load(ck) as z:                 # lazy NpzFile holds the file open
            m = np.unpackbits(z['donebits'])[:len(starts)].astype(bool)
            donemask[:len(m)] = m
            proven, tot = int(z['proven']), int(z['tot'])
            elapsed = float(z['elapsed'])
        if os.path.exists(sf):
            SURV = [np.load(sf)]
        print("resuming %s: %d/%d chunks, %d proven of %d"
              % (tag, int(donemask.sum()), len(starts), proven, tot), flush=True)

    todo = [(starts[i], min(starts[i] + STEP, N), path, depth)
            for i in np.flatnonzero(~donemask).tolist()]
    print("%s: %d patterns, %d chunks, %d remaining, depth %d, %d workers"
          % (path, N, len(starts), len(todo), depth, nw), flush=True)
    if not todo:
        print("nothing to do", flush=True); sys.exit(0)

    idx_of = {s: i for i, s in enumerate(starts)}
    t0 = time.time()
    try:
        with Pool(nw) as pool:
            for k, (lo, pv, nt, S) in enumerate(pool.imap_unordered(job, todo)):
                donemask[idx_of[lo]] = True
                proven += pv; tot += nt
                if len(S):
                    SURV.append(S)
                if (k % CKEVERY) == 0:
                    _atomic_save(sf, np.concatenate(SURV) if SURV
                                 else np.zeros((0, 48), np.int8))
                    _atomic_savez(ck, donebits=np.packbits(donemask), proven=proven,
                                  tot=tot, elapsed=elapsed + time.time() - t0)
                if k % 100 == 0:
                    rate = (time.time() - t0) / (k + 1)
                    print("  %d/%d chunks  proven %d/%d (%.2f%%)  %.0fs  ETA %.0fm"
                          % (int(donemask.sum()), len(starts), proven, tot,
                             100.0 * proven / max(tot, 1), time.time() - t0,
                             rate * (len(todo) - k - 1) / 60), flush=True)
    except KeyboardInterrupt:
        print("\ninterrupted -- checkpoint holds %d/%d chunks"
              % (int(donemask.sum()), len(starts)), flush=True)
        sys.exit(130)
    finally:
        A = np.concatenate(SURV) if SURV else np.zeros((0, 48), np.int8)
        _atomic_save(sf, A)
        _atomic_savez(ck, donebits=np.packbits(donemask), proven=proven, tot=tot,
                      elapsed=elapsed + time.time() - t0)
        try: os.remove(lk)
        except OSError: pass

    print("\nTOTAL patterns %d  PROVEN INFEASIBLE %d (%.3f%%)  residual %d  %.0fs"
          % (tot, proven, 100.0 * proven / max(tot, 1), len(A), time.time() - t0),
          flush=True)
    print("residual saved to %s -- run again at a greater depth on THAT file "
          "to deepen only what is left" % sf, flush=True)
