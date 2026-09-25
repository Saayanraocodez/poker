"""Multistart hunt for an equilibrium in which P1 bets.

Why this and not something exhaustive: as of 2026-09-07 both exhaustive routes
are closed by measurement.  The support enumeration of a betting branch is
10^9-10^10 patterns (treesize.py, with the silent branch reproducing its known
3,045,358 as a control), and the box partition grows ~1.5x per level while a
real wtol needs ~104 more levels (log_ladder.txt).  The depth-26 boxes cannot
even seed a search: control_pg.py recovers 0 of 9 known equilibria from a box
centre, because a width-0.5 slab centre is ~0.25 away and the basin is ~0.1.

So this is a search, and it is labelled a search.  It cannot prove the family
complete.  What it can do is find a counterexample if one exists, and pile up
evidence of the same kind s15.4 produced if one does not.

Design points that are not arbitrary:

* Table 2's 21 coordinates are FIXED, not searched.  They are forced by a
  rigorous global interval fixed point (s15.2) and -- shown this session by
  betencl.py -- separately forced across the whole P1-betting region.  Fixing
  them cuts the search from 48 dimensions to 27.
* Starts are mixed.  `bet` draws an opening coordinate from [betlo, 1] so the
  search begins where the answer would have to be; `unif` is a control arm that
  should keep reproducing family equilibria, and if it ever stops doing so the
  harness is broken rather than the conjecture.
* A converged residual is NEVER reported as an equilibrium.  pgsolve's residual
  is a first-order condition, and off-path information sets make it insufficient
  (s7.7): the pilot had 19 points at residual < 1e-12 of which only 8 were
  equilibria.  Certification is eqtools.expl < 1e-13, always.
* Checkpoint every batch, resume by batch index, one live owner per tag.  pipe.py
  lost whole runs to interruption before pipe2.py fixed exactly this, and a
  multi-day hunt is the same exposure.

usage:  python bethunt.py <batches> <batchsize> <workers> <tag> [betlo]

state:  hunt_<tag>.npz        counters + batches done  (rewritten atomically)
        hunt_eq_<tag>.npy     distinct certified equilibria found so far
"""
import numpy as np, sys, os, time, subprocess
import pgsolve, eqtools as E, classify, kuhn3p as K

I = K.NAME_IDX
T2_ZERO = ("a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24",
           "c12", "c13", "c14", "c24")
T2_ONE = ("a42", "a43", "a44", "b42", "b43", "b44", "c42", "c43", "c44")
Z = [I[n] for n in T2_ZERO]
O = [I[n] for n in T2_ONE]
OPEN = [I[n] for n in ("a11", "a21", "a31", "a41")]
EXPL_TOL = 1e-13
CKEVERY = 200       # batches between checkpoints (batches are small)
BET_TOL = 1e-9


def _alive(pid):
    try:
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return False
    return ("python" in out.lower()) and (str(pid) in out)


def take_lock(tag):
    """One live owner per tag: two runs would overwrite each other's
    hunt_eq_<tag>.npy with their own accumulated list, silently dropping
    equilibria.  That is a wrong result, not a slow one."""
    lk = "lockh_%s.pid" % tag
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
    tmp = path + ".tmp.npy"
    np.save(tmp, arr)
    _replace(tmp, path)


def _atomic_savez(path, **kw):
    tmp = path + ".tmp.npz"
    np.savez(tmp, **kw)
    _replace(tmp, path)


def starts(n, rng, mode, betlo):
    X = rng.random((n, 48))
    X[:, Z] = 0.0
    X[:, O] = 1.0
    if mode == "bet":
        j = rng.integers(0, 4, n)
        X[np.arange(n), np.array(OPEN)[j]] = betlo + (1 - betlo) * rng.random(n)
    return X


def job(a):
    """One batch.  Returns (index, certified profiles, counters)."""
    idx, n, seed, mode, betlo = a
    rng = np.random.default_rng(seed)
    X = starts(n, rng, mode, betlo)
    P, r = pgsolve.solve(X, rng, iters=60, jac_every=3, tol=1e-13)
    conv = int((r < 1e-12).sum())
    ex = np.array([float(np.abs(E.expl(q)).max()) for q in P])
    eq = ex < EXPL_TOL
    Q = P[eq]
    bet = int((Q[:, OPEN].max(axis=1) > BET_TOL).sum()) if len(Q) else 0
    return idx, Q, (n, conv, int(eq.sum()), bet)


if __name__ == "__main__":
    from multiprocessing import Pool
    nb = int(sys.argv[1]); bs = int(sys.argv[2]); nw = int(sys.argv[3])
    tag = sys.argv[4]
    betlo = float(sys.argv[5]) if len(sys.argv) > 5 else 0.02
    lk = take_lock(tag)

    ck = "hunt_%s.npz" % tag
    eqf = "hunt_eq_%s.npy" % tag
    donemask = np.zeros(nb, bool)
    tot = conv = ncert = nbet = 0; elapsed = 0.0
    EQ = np.zeros((0, 48)); sigs = set()
    if os.path.exists(ck):
        with np.load(ck) as z:                 # lazy NpzFile holds the file open
            # `done` is a packed bitmask, not a list of indices.  The winning
            # configuration is ~30-start batches, so a 20M-start run is ~600k
            # batches: as an int64 list that is 5 MB rewritten on every
            # checkpoint, which is hundreds of GB of pointless I/O over a
            # multi-day run.  Packed it is ~75 kB.
            if 'donebits' in z.files:
                m = np.unpackbits(z['donebits'])[:nb].astype(bool)
                donemask[:len(m)] = m[:nb]
            else:                              # older checkpoint: index list
                idx = np.asarray(z['done'], np.int64)
                donemask[idx[idx < nb]] = True
            tot, conv, ncert, nbet = (int(z['tot']), int(z['conv']),
                                      int(z['ncert']), int(z['nbet']))
            elapsed = float(z['elapsed'])
        if os.path.exists(eqf):
            EQ = np.load(eqf)
            sigs = {classify.signature(q) for q in EQ}
        print("resuming %s: %d batches done, %d starts, %d certified, %d distinct"
              % (tag, int(donemask.sum()), tot, ncert, len(EQ)), flush=True)
    EQL = [q for q in EQ]          # grown as a list; concatenating it per
    last_save = 0.0                # discovery is O(n^2) over millions of starts

    todo = [(i, bs, 1000003 * i + 7, "bet" if i % 4 else "unif", betlo)
            for i in np.flatnonzero(~donemask).tolist()]
    print("batches %d x %d starts, %d remaining, %d workers, betlo=%.3f"
          % (nb, bs, len(todo), nw, betlo), flush=True)
    if not todo:
        print("nothing to do", flush=True); sys.exit(0)

    t0 = time.time()
    try:
        with Pool(nw) as pool:
            for k, (idx, Q, c) in enumerate(pool.imap_unordered(job, todo)):
                donemask[idx] = True
                tot += c[0]; conv += c[1]; ncert += c[2]; nbet += c[3]
                new = 0
                for q in Q:
                    sg = classify.signature(q)
                    if sg not in sigs:
                        sigs.add(sg)
                        EQL.append(q)
                        new += 1
                # Rewriting the whole array on every discovery is O(n^2) I/O; a
                # betting hit is the one thing worth flushing immediately.
                if new and (c[3] or time.time() - last_save > 60):
                    _atomic_save(eqf, np.array(EQL))
                    last_save = time.time()
                # Checkpoint every CKEVERY batches, not every batch: with 256-start
                # batches the `done` array is rewritten every few seconds for no
                # gain.  Resuming redoes at most CKEVERY batches, and since the
                # counters are written together with `done`, a redone batch is
                # counted exactly once either way.
                if (k % CKEVERY) == 0:
                    _atomic_savez(ck, donebits=np.packbits(donemask), tot=tot,
                                  conv=conv, ncert=ncert, nbet=nbet,
                                  elapsed=elapsed + time.time() - t0)
                if k % 10 == 0 or c[3]:
                    rate = (time.time() - t0) / (k + 1)
                    print("  %d/%d  starts %d  certified %d (%.2f%%)  distinct %d"
                          "  P1-BETTING %d  %.0fs  ETA %.0fm"
                          % (int(donemask.sum()), nb, tot, ncert, 100.0 * ncert / max(tot, 1),
                             len(EQL), nbet, time.time() - t0,
                             rate * (len(todo) - k - 1) / 60), flush=True)
                if c[3]:
                    print("  *** a certified equilibrium with P1 BETTING was found "
                          "in batch %d -- see %s" % (idx, eqf), flush=True)
    except KeyboardInterrupt:
        print("\ninterrupted -- checkpoint holds %d/%d batches"
              % (int(donemask.sum()), nb), flush=True)
        sys.exit(130)
    finally:
        # The last discoveries since the 60s flush are only in memory; losing
        # them would understate the search, so save on the way out however we
        # leave -- including the KeyboardInterrupt path above.
        if EQL:
            _atomic_save(eqf, np.array(EQL))
        _atomic_savez(ck, donebits=np.packbits(donemask), tot=tot, conv=conv,
                      ncert=ncert, nbet=nbet, elapsed=elapsed + time.time() - t0)
        try: os.remove(lk)
        except OSError: pass
    EQ = np.array(EQL) if EQL else np.zeros((0, 48))

    print("\nTOTAL starts %d  residual-converged %d  CERTIFIED %d  distinct %d"
          % (tot, conv, ncert, len(EQ)), flush=True)
    print("certified equilibria with P1 betting: %d" % nbet, flush=True)
    if len(EQ):
        fg = np.array([classify.family_gap(q) for q in EQ])
        print("family leaf-distribution gap: max %.3e   OUTSIDE family (>1e-9): %d of %d"
              % (fg.max(), int((fg > 1e-9).sum()), len(EQ)), flush=True)
        U = np.array([E.util(q) for q in EQ])
        k = 1 / 24
        print("u1 [%.9f, %.9f]  u2 [%.9f, %.9f]  u3 [%.9f, %.9f]"
              % (U[:, 0].min(), U[:, 0].max(), U[:, 1].min(), U[:, 1].max(),
                 U[:, 2].min(), U[:, 2].max()), flush=True)
        print("family: u1 [%.9f, %.9f]  u2 %.9f  u3 [%.9f, %.9f]"
              % (-k * .75, -k * .5, -k * .5, k, k * 1.25), flush=True)
