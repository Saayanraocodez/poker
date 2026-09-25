import numpy as np, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
lab = L[469]; pieces = seqset.leaf_pieces(lab)
base = {n: F(0) for n in ("b32","c34","c13","a14","a24","b12","b14","b24","c14","c24","c23")}
print("is b22 > 2/5 with c33 interior sequential?")
for b22 in (F(0), F(1,4), F(2,5), F(1,2), F(9,16)):
    for c33 in (F(1,2), F(5,8)):
        off = dict(base); off["b22"] = b22; off["c33"] = c33
        s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
        bad = seqset.verify_point(lab, s)
        if bad: print("  b22=%-5s c33=%-5s not Nash (%s)" % (b22, c33, bad)); continue
        st, m, r = seqset.is_sequential(pieces, s, lab)
        st2 = st
        if st != "sequential":
            st2, order, sol = seqset.seq_orderings(lab, s, pieces)
        print("  b22=%-5s c33=%-5s  uniform=%-11s any-ordering=%s" % (b22, c33, st, st2), flush=True)
