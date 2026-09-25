"""Run the B&B on one top-level branch (a fixed label pattern for P1's opening)."""
import numpy as np, sys, time, os, bnb, kuhn3p as K
I = K.NAME_IDX
ORDER = [I[n] for n in
         ("c11","c21","c31","c41","b11","b21","b31","b41",
          "a22","a32","a33","a34","a23","c22","c32","b23","b33","b34","b41",
          "b22","b32","c23","c33","c34",
          "a12","a13","a14","a24","b12","b13","b14","b24","c12","c13","c14","c24",
          "a42","a43","a44","b42","b43","b44","c42","c43","c44",
          "a11","a21","a31","a41")]
ORDER = list(dict.fromkeys(ORDER))
A1 = [I[n] for n in ("a11","a21","a31","a41")]

def work(args):
    code, cap, maxnodes = args
    lab = np.full(48, bnb.U)
    for k, t in enumerate(A1):
        lab[t] = code[k]
    cnt = [0]
    keep = []
    def sink(blk):
        cnt[0] += blk.shape[0]
        if cnt[0] <= 4_000_000: keep.append(blk.astype(np.int8))
    t0 = time.time()
    pats, st = bnb.run(lab, ORDER, cap=cap, maxnodes=maxnodes, sink=sink)
    out = np.concatenate(keep) if keep else np.zeros((0,48), np.int8)
    return code, cnt[0], st, time.time()-t0, out
