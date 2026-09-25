import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); I = refine.I; NAME = refine.NAME
lab = L[469]; pieces = seqset.leaf_pieces(lab)
base = {I["a44"]:1, I["b12"]:0, I["b42"]:1, I["b44"]:1, I["c14"]:0, I["c24"]:0, I["c44"]:1}
cases = [
  {I["b22"]:0, I["b32"]:0, I["c13"]:0, I["c23"]:0, I["c33"]:"mix", I["c34"]:0, I["c43"]:"mix"},
  {I["b22"]:0, I["b32"]:0, I["c13"]:"mix", I["c23"]:0, I["c33"]:"mix", I["c34"]:0, I["c43"]:1},
  {I["b22"]:0, I["b32"]:"mix", I["c13"]:0, I["c23"]:0, I["c33"]:0, I["c34"]:0, I["c43"]:1},
]
for c in cases:
    a = dict(base); a.update(c); t0 = time.time()
    w = seqset.witness_for(lab, pieces, a) or seqset.witness_guided(lab, pieces, a)
    print("%-62s -> %s (%.0fs)" % (seqset.fmt_assign(c), "WITNESS" if w else "none", time.time()-t0), flush=True)
    if w: print("     ", ", ".join("%s=%s" % (NAME[i], w[0][i]) for i in range(48) if 0 < w[0][i] < 1))
