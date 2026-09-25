"""Partition-based interval branch-and-bound over [0,1]^48.

No labels.  A box [lo,hi] per coordinate implies its own Nash condition:
    lo > 0  (x is always > 0)  ==>  du/dx >= 0
    hi < 1  (x is always < 1)  ==>  du/dx <= 0
    both                       ==>  du/dx = 0
    lo = 0 and hi = 1          ==>  no condition yet
Splitting [0,1] at m yields [0,m] (needs du<=0) and [m,1] (needs du>=0): both
children carry a condition immediately and the two halves do not overlap in
their conditions, so there is none of the redundancy of a 0/1/interior label
alphabet.

Sound pruning only, modulo leaf-distribution equivalence (the two "weak"
rules move a coordinate whose information set can only be unreachable to its
dominant pure value, which never changes the leaf distribution).
"""
import numpy as np, ivl, os, time

TOL = 1e-11

def propagate(LO, HI, tol=TOL, rounds=5):
    alive = np.ones(LO.shape[0], bool)
    for _ in range(rounds):
        DLO, DHI, RH, DMIN, DMAX = ivl.bounds(LO, HI)
        f1 = (DLO > tol) | (DMIN > tol)          # x must be 1 (or irrelevant)
        f0 = (DHI < -tol) | (DMAX < -tol)        # x must be 0 (or irrelevant)
        bad = (f1 & (HI < 1.0)) | (f0 & (LO > 0.0))
        alive &= ~bad.any(axis=1)
        if not alive.any(): break
        nLO = np.where(f1, 1.0, LO)
        nHI = np.where(f0, 0.0, HI)
        if np.array_equal(nLO, LO) and np.array_equal(nHI, HI): break
        LO, HI = nLO, nHI
    return LO, HI, alive

# ---------------------------------------------------------------------------
# Durable search state.
#
# `search` is a DFS whose whole progress lives in two places: `stack` (work not
# yet done) and the emitted boxes.  With no way to save either, a kill at hour
# 22 costs hour 1 through 22 -- which is exactly what happened to bet_a31_hi and
# bet_a41_hi.  The stack is tiny (the logs show 4-10 entries), so the only bulky
# thing is the emitted boxes, and those are append-only.  So: spill boxes to a
# raw file as they are produced, and checkpoint only the stack + counters.
#
# The ordering below is what makes a resume SOUND rather than merely fast:
# the spill is flushed and fsynced BEFORE the checkpoint records its row count,
# so after a crash the spill can only be AHEAD of the checkpoint, never behind.
# Extra rows are re-derived by the restored stack, so a resume truncates them.
# Losing rows would silently shrink an exhaustive claim; duplicating them would
# silently inflate it.  Truncation makes both impossible.
# ---------------------------------------------------------------------------

def _sig(LO0, HI0, wtol, maxdepth, cap):
    """Fingerprint of the problem this checkpoint belongs to.

    Resuming a checkpoint under different constraints would splice two
    different searches into one 'exhaustive' answer.  Refuse instead."""
    h = np.array([wtol, maxdepth, cap], float)
    a = np.zeros(48) if LO0 is None else np.asarray(LO0, float)
    b = np.ones(48) if HI0 is None else np.asarray(HI0, float)
    return np.concatenate([h, a, b])


def _replace(tmp, path, tries=8):
    for k in range(tries):
        try:
            os.replace(tmp, path); return
        except PermissionError:
            if k == tries - 1: raise
            time.sleep(0.4 * (k + 1))


def _spill_paths(ckpt):
    return ckpt + "_lo.f64", ckpt + "_hi.f64"


def _ck_save(ckpt, stack, st, nrows, sig, elapsed, done=False):
    lens = np.array([s[0].shape[0] for s in stack], np.int64)
    if stack:
        slo = np.concatenate([s[0] for s in stack])
        shi = np.concatenate([s[1] for s in stack])
        sd = np.concatenate([s[2] for s in stack])
    else:
        slo = np.zeros((0, 48)); shi = np.zeros((0, 48)); sd = np.zeros(0, np.int16)
    tmp = ckpt + ".tmp.npz"
    np.savez(tmp, slo=slo, shi=shi, sd=sd, lens=lens, sig=sig,
             nodes=st['nodes'], boxes=st['boxes'], batches=st['batches'],
             hits=st['hits'], abort=bool(st.get('ABORT', False)),
             nrows=nrows, elapsed=elapsed, done=done)
    _replace(tmp, ckpt + ".npz")


def _ck_load(ckpt, sig):
    """Restore (stack, st, nrows, elapsed, done) or None if there is nothing to
    resume.  Mismatched constraints raise rather than silently mixing runs."""
    p = ckpt + ".npz"
    if not os.path.exists(p):
        return None
    # np.load on an .npz returns a LAZY NpzFile holding the file open, and
    # Windows will not os.replace onto a path with a live handle.  Pull
    # everything out inside the context manager.
    with np.load(p) as z:
        old = z['sig']
        if not np.array_equal(old, sig):
            raise SystemExit(
                "checkpoint %s belongs to a DIFFERENT problem "
                "(constraints/wtol/maxdepth/cap changed). Delete it or use "
                "another tag; resuming it would splice two searches into one "
                "exhaustive claim." % p)
        lens = z['lens']; slo = z['slo']; shi = z['shi']; sd = z['sd']
        st = dict(nodes=int(z['nodes']), boxes=int(z['boxes']),
                  batches=int(z['batches']), hits=int(z['hits']))
        if bool(z['abort']): st['ABORT'] = True
        nrows = int(z['nrows']); elapsed = float(z['elapsed'])
        done = bool(z['done'])
    stack = []
    o = 0
    for n in lens:
        n = int(n)
        stack.append((slo[o:o + n].copy(), shi[o:o + n].copy(), sd[o:o + n].copy()))
        o += n
    return stack, st, nrows, elapsed, done


def _spill_truncate(ckpt, nrows):
    """Drop any rows the last checkpoint did not account for."""
    want = nrows * 48 * 8
    for p in _spill_paths(ckpt):
        if not os.path.exists(p):
            if want:
                raise SystemExit("checkpoint claims %d boxes but %s is missing"
                                 % (nrows, p))
            open(p, "wb").close(); continue
        sz = os.path.getsize(p)
        if sz < want:
            raise SystemExit("spill %s is SHORT (%d < %d bytes): boxes were lost, "
                             "the claim would be incomplete" % (p, sz, want))
        if sz > want:
            with open(p, "r+b") as f:
                f.truncate(want)


def spill_to_npy(ckpt, lo_out, hi_out, chunk=200000):
    """Turn the raw spill into the .npy pair, without holding it all in RAM."""
    import numpy.lib.format as fmt
    n = os.path.getsize(_spill_paths(ckpt)[0]) // (48 * 8)
    for src, dst in zip(_spill_paths(ckpt), (lo_out, hi_out)):
        m = fmt.open_memmap(dst, mode='w+', dtype=np.float64, shape=(n, 48))
        with open(src, "rb") as f:
            o = 0
            while o < n:
                k = min(chunk, n - o)
                m[o:o + k] = np.frombuffer(f.read(k * 48 * 8),
                                           dtype=np.float64).reshape(k, 48)
                o += k
        m.flush(); del m
    return n


def search(LO0=None, HI0=None, order=None, objf=None, thresh=None,
           wtol=0.02, maxdepth=60, cap=2048, maxnodes=None, sink=None,
           log=None, objsplit=None, tag="", ckpt=None, ckevery=900):
    """Set `ckpt` to a path prefix to make the search restartable.

    Without it the behaviour is byte-identical to before: boxes accumulate in
    `out` and are returned.  With it, boxes are spilled to `<ckpt>_lo.f64` /
    `<ckpt>_hi.f64` as they are emitted, the stack is checkpointed to
    `<ckpt>.npz` every `ckevery` seconds, and re-calling with the same prefix
    picks up where the last checkpoint left off.  `out` is then empty and the
    caller reads the spill (see `spill_to_npy`)."""
    if ckpt is not None and sink is not None:
        raise SystemExit("ckpt and sink are mutually exclusive: a resume cannot "
                         "replay the sink() calls made before the interruption.")
    t0 = time.time(); elapsed0 = 0.0; nrows = 0; fh = None
    resumed = _ck_load(ckpt, _sig(LO0, HI0, wtol, maxdepth, cap)) if ckpt else None

    if resumed is not None:
        stack, st, nrows, elapsed0, was_done = resumed
        _spill_truncate(ckpt, nrows)
        print("   [%s] RESUME nodes=%d boxes=%d stack=%d  %.0fs prior%s"
              % (tag, st['nodes'], st['boxes'], len(stack), elapsed0,
                 "  (already complete)" if was_done else ""), flush=True)
        if was_done:
            st['elapsed'] = elapsed0; st['spill'] = ckpt
            return st, []
        # A previous run that hit its node cap can be extended by resuming with
        # a larger maxnodes, so the stale ABORT must not survive the restart.
        st.pop('ABORT', None)
        out = []
    else:
        B = 1
        LO = np.zeros((1, 48)) if LO0 is None else LO0[None, :].copy()
        HI = np.ones((1, 48)) if HI0 is None else HI0[None, :].copy()
        LO, HI, al = propagate(LO, HI)
        st = dict(nodes=0, boxes=0, batches=0, hits=0)
        if ckpt is not None:
            for p in _spill_paths(ckpt): open(p, "wb").close()
        if not al[0]:
            if ckpt is not None:
                _ck_save(ckpt, [], st, 0, _sig(LO0, HI0, wtol, maxdepth, cap),
                         0.0, done=True)
                st['elapsed'] = 0.0; st['spill'] = ckpt
            return st, []
        D = np.zeros(1, np.int16)
        stack = [(LO, HI, D)]
        out = []

    if ckpt is not None:
        sig = _sig(LO0, HI0, wtol, maxdepth, cap)
        fh = [open(p, "ab") for p in _spill_paths(ckpt)]
        tck = time.time()

    def _checkpoint(done=False):
        for f in fh:
            f.flush(); os.fsync(f.fileno())      # spill first, then the record
        _ck_save(ckpt, stack, st, nrows, sig,
                 elapsed0 + time.time() - t0, done=done)

    while stack:
        # Top of the loop: `stack` is exactly the work left and the spill holds
        # exactly the boxes emitted, so this is the one place the two are
        # consistent.  (The loop body has `continue`s; a checkpoint at the
        # bottom would be skipped by them.)
        if fh is not None and time.time() - tck > ckevery:
            _checkpoint()
            tck = time.time()
            print("   [%s] ck nodes=%d stack=%d boxes=%d  %.0fs"
                  % (tag, st['nodes'], len(stack), st['boxes'],
                     elapsed0 + time.time() - t0), flush=True)
        LO, HI, D = stack.pop()
        st['nodes'] += LO.shape[0]; st['batches'] += 1
        if objf is not None:
            ub = objf(LO, HI)
            k = ub > thresh
            if not k.any(): continue
            LO, HI, D = LO[k], HI[k], D[k]
        W = HI - LO
        fin = (W.max(axis=1) < wtol) | (D >= maxdepth)
        if fin.any():
            st['boxes'] += int(fin.sum())
            if fh is not None:
                LO[fin].tofile(fh[0]); HI[fin].tofile(fh[1])
                nrows += int(fin.sum())
            elif sink is not None: sink(LO[fin], HI[fin])
            else: out.append((LO[fin].copy(), HI[fin].copy()))
        k = ~fin
        if not k.any(): continue
        LO, HI, D, W = LO[k], HI[k], D[k], W[k]
        score = W.copy()
        if objsplit is not None: score = objsplit(LO, HI, W)
        v = score.argmax(axis=1)
        for vv in np.unique(v):
            m = (v == vv)
            slo, shi, sd = LO[m], HI[m], D[m]
            for s in range(0, slo.shape[0], cap):
                b, c, e = slo[s:s+cap], shi[s:s+cap], sd[s:s+cap]
                mid = 0.5 * (b[:, vv] + c[:, vv])
                Bl = np.repeat(b, 2, axis=0); Ch = np.repeat(c, 2, axis=0)
                Ee = np.repeat(e, 2) + 1
                Ch[0::2, vv] = mid; Bl[1::2, vv] = mid
                Bl, Ch, al = propagate(Bl, Ch)
                if al.any(): stack.append((Bl[al], Ch[al], Ee[al]))
        if maxnodes and st['nodes'] > maxnodes:
            st['ABORT'] = True; break
        if log and st['batches'] % log == 0:
            print("   [%s] nodes=%d stack=%d boxes=%d" % (tag, st['nodes'], len(stack), st['boxes']), flush=True)

    if fh is not None:
        # `stack` is empty here unless the node cap broke the loop; either way
        # the final record must match the spill, and `done` must be true only
        # when the search really exhausted its stack.
        finished = (not stack) and not st.get('ABORT', False)
        _checkpoint(done=finished)
        for f in fh: f.close()
        st['elapsed'] = elapsed0 + time.time() - t0
        st['spill'] = ckpt
    return st, out
