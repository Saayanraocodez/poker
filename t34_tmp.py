import numpy as np, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
J = refine.jac()
base = {n: F(0) for n in ("b32","c34","c13","c23","b22","a14","a24","b12","b14","b24","c14","c24")}
print("c33's window over the SEQUENTIAL set (Nash window is [0, 15/16])")
for (b11, b21, c11, leaf) in ((F(1,4), F(1,4), F(1,4), 469), (F(1,4), F(1,4), F(0), 469),
                              (F(1,8), F(1,8), F(1,4), 469), (F(0), F(0), F(1,4), 18)):
    hi = F(1,2) + F(3,4)*(b11+b21) + max(b11,b21)/4
    lab = L[leaf]; pieces = seqset.leaf_pieces(lab)
    out = []
    for c33 in (F(1,4), F(1,2), (F(1,2)+hi)/2, hi):
        off = dict(base); off["c33"] = c33
        s = seqset.family_point(b11, b21, F(0), c11, off)
        bad = seqset.verify_point(lab, s)
        if bad: out.append("%s:notNash" % c33); continue
        st, m, r = seqset.is_sequential(pieces, s, lab)
        if st != "sequential":
            st = seqset.seq_orderings(lab, s, pieces)[0]
        ok, info = refine.perfect_cert(s, J)
        out.append("%s: %s%s" % (c33, "SEQ" if st == "sequential" else st, "+PERF" if ok else ""))
    print("  b11=%-4s b21=%-4s c11=%-4s (leaf %d, Nash hi=%s):  %s" % (b11, b21, c11, leaf, hi, "   ".join(out)), flush=True)
