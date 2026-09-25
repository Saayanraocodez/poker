"""Interval B&B with the MIX label split into `nsplit` sub-intervals at the
moment it is created -- interval propagation is far sharper on [0,1/2] than on
[0,1], so this kills subtrees long before the labelling is complete."""
import numpy as np, ivl, bnb2
U, MIX, DC = bnb2.U, bnb2.MIX, bnb2.DC
propagate = bnb2.propagate

def search(lab0, order, nsplit=2, bdepth=8, cap=2048, maxnodes=None,
           sink=None, log=None, LO0=None, HI0=None):
    lab = lab0[None, :].astype(np.int8)
    LO = np.where(lab == 1, 1.0, 0.0) if LO0 is None else LO0[None, :].copy()
    HI = np.where(lab == 0, 0.0, 1.0) if HI0 is None else HI0[None, :].copy()
    lab, LO, HI, al = propagate(lab, LO, HI)
    st = dict(nodes=0, boxes=0, batches=0)
    if not al[0]: return st
    D = np.zeros(1, np.int16)
    stack = [(lab, LO, HI, D)]
    edges = np.linspace(0.0, 1.0, nsplit + 1)
    while stack:
        lab, LO, HI, D = stack.pop()
        st['nodes'] += lab.shape[0]; st['batches'] += 1
        hasU = (lab == U).any(axis=1)
        W = np.where(lab == MIX, HI - LO, 0.0)
        fin = (~hasU) & ((W.max(axis=1) <= 0) | (D >= bdepth))
        if fin.any():
            st['boxes'] += int(fin.sum())
            if sink is not None: sink(lab[fin], LO[fin], HI[fin])
        k = ~fin
        if not k.any(): continue
        lab, LO, HI, D, hasU, W = lab[k], LO[k], HI[k], D[k], hasU[k], W[k]
        if hasU.any():
            l, lo, hi, dd = lab[hasU], LO[hasU], HI[hasU], D[hasU]
            pos = np.full(l.shape[0], 10**6)
            for rank, v in enumerate(order):
                m = (l[:, v] == U) & (pos == 10**6); pos[m] = rank
            for rank in np.unique(pos):
                v = order[rank]; m = (pos == rank)
                sl, slo, shi, sd = l[m], lo[m], hi[m], dd[m]
                nch = 2 + nsplit
                for s in range(0, sl.shape[0], cap):
                    a, b, c, e = sl[s:s+cap], slo[s:s+cap], shi[s:s+cap], sd[s:s+cap]
                    A = np.repeat(a, nch, axis=0); B = np.repeat(b, nch, axis=0)
                    C = np.repeat(c, nch, axis=0); E = np.repeat(e, nch)
                    A[0::nch, v] = 0; C[0::nch, v] = 0.0
                    A[1::nch, v] = 1; B[1::nch, v] = 1.0
                    for q in range(nsplit):
                        A[2+q::nch, v] = MIX
                        B[2+q::nch, v] = edges[q]; C[2+q::nch, v] = edges[q+1]
                    A, B, C, al = propagate(A, B, C)
                    if al.any(): stack.append((A[al], B[al], C[al], E[al]))
        if (~hasU).any():
            l, lo, hi, dd, w = lab[~hasU], LO[~hasU], HI[~hasU], D[~hasU], W[~hasU]
            v = w.argmax(axis=1)
            for vv in np.unique(v):
                m = (v == vv)
                sl, slo, shi, sd = l[m], lo[m], hi[m], dd[m]
                for s in range(0, sl.shape[0], cap):
                    a, b, c, e = sl[s:s+cap], slo[s:s+cap], shi[s:s+cap], sd[s:s+cap]
                    mid = 0.5 * (b[:, vv] + c[:, vv])
                    A = np.repeat(a, 2, axis=0); B = np.repeat(b, 2, axis=0)
                    C = np.repeat(c, 2, axis=0); E = np.repeat(e, 2) + 1
                    C[0::2, vv] = mid; B[1::2, vv] = mid
                    A, B, C, al = propagate(A, B, C)
                    if al.any(): stack.append((A[al], B[al], C[al], E[al]))
        if maxnodes and st['nodes'] > maxnodes:
            st['ABORT'] = True; break
        if log and st['batches'] % log == 0:
            print("   nodes=%d stack=%d boxes=%d" % (st['nodes'], len(stack), st['boxes']), flush=True)
    return st
