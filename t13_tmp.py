import numpy as np, itertools, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]; pieces = seqset.leaf_pieces(lab)
found = 0; t0 = time.time()
for b11 in (F(1,8), F(1,6)):
  for b21 in (F(1,8), F(1,6)):
    for c11 in (F(1,4), F(1,3)):
      for c33 in (F(1,2), F(5,8), F(3,4)):
        off = {"c33": c33, "b32": F(0), "c34": F(0), "b22": F(0), "c13": F(0), "c23": F(0),
               "a14": F(0), "a24": F(0), "b12": F(0), "b14": F(0), "b24": F(0), "c14": F(0), "c24": F(0)}
        s = seqset.family_point(b11, b21, F(0), c11, off)
        bad = seqset.verify_point(lab, s)
        if bad: continue
        st, m, r = seqset.is_sequential(pieces, s, lab)
        found += 1
        print("  b11=%s b21=%s c11=%s c33=%-4s -> %-12s m=%s %s" % (b11, b21, c11, c33, st, m, {a: str(b) for a, b in r.items() if b != 0} if r else ""), flush=True)
print("%d valid family points, %.0fs" % (found, time.time()-t0))
