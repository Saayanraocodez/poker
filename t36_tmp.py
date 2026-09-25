import numpy as np, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
J = refine.jac()
print("leaves by b41 label:", {k: int(L[k][I["b41"]]) for k in seqset.FAM})
base = {n: F(0) for n in ("b32","c34","c13","c23","b22","a14","a24","b12","b14","b24","c14","c24")}
tests = [(18, F(0), F(0), F(0), F(1,2)), (211, F(0), F(0), F(1,4), F(1,2)),
         (70, F(1,4), F(1,4), F(1,4), F(1,2)), (70, F(1,4), F(1,4), F(1,4), F(15,16)),
         (70, F(1,4), F(1,4), F(1,4), F(3,4)), (70, F(1,4), F(1,4), F(1,4), F(1,4))]
for leaf, b11, b21, c11, c33 in tests:
    lab = L[leaf]; pieces = seqset.leaf_pieces(lab)
    off = dict(base); off["c33"] = c33
    s = seqset.family_point(b11, b21, F(0), c11, off)
    bad = seqset.verify_point(lab, s)
    if bad: print("  leaf %3d b11=%-4s c11=%-4s c33=%-5s -> not Nash (%s)" % (leaf, b11, c11, c33, bad)); continue
    st, m, r = seqset.is_sequential(pieces, s, lab)
    if st != "sequential": st = seqset.seq_orderings(lab, s, pieces)[0]
    ok, info = refine.perfect_cert(s, J)
    print("  leaf %3d b11=%-4s c11=%-4s c33=%-5s -> %-12s perfect=%s" % (leaf, b11, c11, c33, st, ok if ok else info), flush=True)
