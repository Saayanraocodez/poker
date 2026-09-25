import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
sub_of = lambda lab: "A" if lab[I["c11"]] == 0 else ("B" if lab[I["c21"]] == 2 else "C")
print("sub-family per leaf:", {k: sub_of(L[k]) for k in seqset.FAM})
base = {n: F(0) for n in ("b32","c34","c13","c23","a14","a24","b12","b14","b24","c14","c24")}
print("\ncan b22 be interior?  (needs b22 > 2/5 and 3 r_a11 = 2(r_a31 + r_a41))")
for k in seqset.FAM:
    lab = L[k]; pieces = seqset.leaf_pieces(lab)
    hits = []
    for b22 in (F(5,12), F(1,2), F(9,16), F(7,12)):
        for c33 in (F(1,2), F(9,16), F(5,8), F(3,4)):
            for b11, b21, c11 in ((F(0),F(0),F(0)), (F(1,8),F(1,8),F(1,4)), (F(1,4),F(1,4),F(0)), (F(1,6),F(1,6),F(1,6)), (F(0),F(0),F(1,4))):
                off = dict(base); off["b22"] = b22; off["c33"] = c33
                s = seqset.family_point(b11, b21, F(0), c11, off)
                if seqset.verify_point(lab, s): continue
                st, m, r = seqset.is_sequential(pieces, s, lab)
                if st != "sequential":
                    st = seqset.seq_orderings(lab, s, pieces)[0]
                if st == "sequential": hits.append((b22, c33, b11, c11))
    print("  leaf %4d (%s): %s" % (k, sub_of(lab), ("SEQUENTIAL with b22 = %s, c33 = %s, b11 = %s, c11 = %s" % hits[0]) if hits else "no witness found"), flush=True)
