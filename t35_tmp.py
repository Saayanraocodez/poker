import numpy as np, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
base = {n: F(0) for n in ("b32","c34","c13","c23","b22","a14","a24","b12","b14","b24","c14","c24")}
for leaf, b11, b21, c11 in ((469, F(1,4), F(1,4), F(1,4)), (18, F(0), F(0), F(0)), (211, F(0), F(0), F(1,4))):
    lab = L[leaf]
    off = dict(base); off["c33"] = F(1,2)
    s = seqset.family_point(b11, b21, F(0), c11, off)
    print("leaf %d b11=%s b21=%s c11=%s -> %s" % (leaf, b11, b21, c11, seqset.verify_point(lab, s) or "Nash OK"))
    print("   leaf labels: MIX %s" % [NAME[i] for i in range(48) if lab[i] == 2], " 1:", [NAME[i] for i in range(48) if lab[i] == 1])
