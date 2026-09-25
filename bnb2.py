"""Fused interval branch-and-bound over [0,1]^48.

Stage 1 (labels):  each coordinate is split into  {0} | {1} | [0,1]-interior.
Stage 2 (values):  interior coordinates get their boxes bisected.
Pruning is SOUND throughout: a box is discarded only when interval propagation
over the game tree proves that no point in it satisfies the first-order Nash
conditions.  Output: small boxes that may contain equilibria.
"""
import numpy as np, ivl

U, MIX, DC = 9, 2, 3
TOL = 1e-11

def propagate(lab, LO, HI, tol=TOL, rounds=4):
    alive = np.ones(lab.shape[0], bool)
    for _ in range(rounds):
        DLO, DHI, RH, DMIN, DMAX = ivl.bounds(LO, HI)
        bad = ((lab == 0) & ((DLO > tol) | (DMIN > tol))) \
            | ((lab == 1) & ((DHI < -tol) | (DMAX < -tol))) \
            | ((lab == MIX) & ((DLO > tol) | (DHI < -tol) | (DMIN > tol) | (DMAX < -tol)))
        alive &= ~bad.any(axis=1)
        if not alive.any(): break
        isU = (lab == U)
        f1 = isU & ((DLO > tol) | (DMIN > tol))
        f0 = isU & ((DHI < -tol) | (DMAX < -tol))
        dc = isU & (RH <= 0.0) & ~f1 & ~f0
        if not (f1.any() or f0.any() or dc.any()): break
        lab = lab.copy(); LO = LO.copy(); HI = HI.copy()
        lab[f1] = 1; LO[f1] = 1.0
        lab[f0] = 0; HI[f0] = 0.0
        lab[dc] = DC
    return lab, LO, HI, alive

def _sel(t, m):  return tuple(x[m] for x in t)

def search(lab0, order, wtol=0.03, bdepth=4, cap=2048, maxnodes=None, sink=None, log=None, bisect_mix_only=True):
    lab = lab0[None, :].astype(np.int8)
    LO = np.where(lab == 1, 1.0, 0.0); HI = np.where(lab == 0, 0.0, 1.0)
    lab, LO, HI, al = propagate(lab, LO, HI)
    if not al[0]: return dict(nodes=1, boxes=0)
    D = np.zeros(1, np.int16)
    stack = [(lab, LO, HI, D)]
    st = dict(nodes=0, boxes=0, batches=0)
    while stack:
        lab, LO, HI, D = stack.pop()
        st['nodes'] += lab.shape[0]; st['batches'] += 1
        hasU = (lab == U).any(axis=1)
        free = (lab == MIX) if bisect_mix_only else ((lab == MIX) | (lab == DC))
        W = np.where(free, HI - LO, 0.0)
        fin = (~hasU) & ((W.max(axis=1) < wtol) | (D >= bdepth))
        if fin.any():
            st['boxes'] += int(fin.sum())
            if sink is not None: sink(lab[fin], LO[fin], HI[fin])
        keep = ~fin
        if not keep.any(): continue
        lab, LO, HI, D = lab[keep], LO[keep], HI[keep], D[keep]
        hasU = hasU[keep]; W = W[keep]
        # --- rows with unassigned labels: 3-way label split -----------------
        if hasU.any():
            l, lo, hi, dd = lab[hasU], LO[hasU], HI[hasU], D[hasU]
            pos = np.full(l.shape[0], 10**6)
            for rank, v in enumerate(order):
                m = (l[:, v] == U) & (pos == 10**6); pos[m] = rank
            for rank in np.unique(pos):
                v = order[rank]; m = (pos == rank)
                sl, slo, shi, sd = l[m], lo[m], hi[m], dd[m]
                for s in range(0, sl.shape[0], cap):
                    a, b, c, e = sl[s:s+cap], slo[s:s+cap], shi[s:s+cap], sd[s:s+cap]
                    A = np.repeat(a, 3, axis=0); B = np.repeat(b, 3, axis=0); C = np.repeat(c, 3, axis=0)
                    A[0::3, v] = 0; C[0::3, v] = 0.0
                    A[1::3, v] = 1; B[1::3, v] = 1.0
                    A[2::3, v] = MIX
                    E = np.repeat(e, 3)
                    A, B, C, al = propagate(A, B, C)
                    if al.any(): stack.append((A[al], B[al], C[al], E[al]))
        # --- fully labelled rows: bisect the widest interior box ------------
        if (~hasU).any():
            l, lo, hi, dd = lab[~hasU], LO[~hasU], HI[~hasU], D[~hasU]
            w = W[~hasU]
            v = w.argmax(axis=1)
            for vv in np.unique(v):
                m = (v == vv)
                sl, slo, shi, sd = l[m], lo[m], hi[m], dd[m]
                for s in range(0, sl.shape[0], cap):
                    a, b, c, e = sl[s:s+cap], slo[s:s+cap], shi[s:s+cap], sd[s:s+cap]
                    mid = 0.5 * (b[:, vv] + c[:, vv])
                    A = np.repeat(a, 2, axis=0); B = np.repeat(b, 2, axis=0); C = np.repeat(c, 2, axis=0)
                    C[0::2, vv] = mid; B[1::2, vv] = mid
                    E = np.repeat(e, 2) + 1
                    A, B, C, al = propagate(A, B, C)
                    if al.any(): stack.append((A[al], B[al], C[al], E[al]))
        if maxnodes and st['nodes'] > maxnodes:
            st['ABORT'] = True; break
        if log and st['batches'] % log == 0:
            print("   nodes=%d stack=%d boxes=%d" % (st['nodes'], len(stack), st['boxes']), flush=True)
    return st
