import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); I = refine.I; NAME = refine.NAME
lab = L[469]; pieces = seqset.leaf_pieces(lab)
base = {I["a44"]:1, I["b12"]:0, I["b42"]:1, I["b44"]:1, I["c14"]:0, I["c24"]:0, I["c44"]:1}
a = dict(base); a.update({I["b22"]:0, I["b32"]:0, I["c13"]:0, I["c23"]:"mix", I["c33"]:"mix", I["c34"]:0, I["c43"]:1})
w = seqset.witness_for(lab, pieces, a) or seqset.witness_guided(lab, pieces, a)
s, r = w
print("profile:", ", ".join("%s=%s" % (NAME[i], s[i]) for i in range(48) if 0 < s[i] < 1))
print("verify :", seqset.verify_point(lab, s) or "exact Nash point")
st, m, rr = seqset.is_sequential(pieces, s, lab)
print("uniform-scale LP:", st, "m =", m)
st2, order, sol = seqset.seq_orderings(lab, s, pieces)
print("with orderings  :", st2, " order", order)
print("beliefs         :", {a_: str(b) for a_, b in (sol or {}).items() if b != 0})
ok, info = refine.perfect_cert(s)
print("perfect         :", ok, info if not ok else "s*=%s rank %d" % (info["s"], info["rank"]))
