import numpy as np, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
J = refine.jac()
base = {n: F(0) for n in ("b32","c34","c13","c23","b22","a14","a24","b12","b14","b24","c14","c24")}
print("top of the window: b11 = b21 = 1/4 (b41 = 1), leaf 70 / 440, c11 = 0")
for leaf in (70, 440):
    lab = L[leaf]; pieces = seqset.leaf_pieces(lab)
    for c33 in (F(7,16), F(1,2), F(3,4), F(7,8), F(15,16), F(1)):
        off = dict(base); off["c33"] = c33
        s = seqset.family_point(F(1,4), F(1,4), F(0), F(0), off)
        bad = seqset.verify_point(lab, s)
        if bad: print("  leaf %3d c33=%-5s -> not Nash (%s)" % (leaf, c33, bad)); continue
        st, m, r = seqset.is_sequential(pieces, s, lab)
        if st != "sequential": st = seqset.seq_orderings(lab, s, pieces)[0]
        ok, info = refine.perfect_cert(s, J)
        print("  leaf %3d c33=%-5s -> %-12s perfect=%s" % (leaf, c33, st, ok if ok is True else str(info)[:60]), flush=True)
