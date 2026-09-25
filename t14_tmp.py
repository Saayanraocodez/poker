import time, numpy as np, seqset, refine
L = np.load("enum6_pat_silentR.npy")
t0=time.time(); refine.build_DR(); print("first build %.1fs" % (time.time()-t0))
t0=time.time(); refine.build_DR(); print("cached      %.3fs" % (time.time()-t0))
lab = L[469]; t0=time.time(); pieces = seqset.leaf_pieces(lab); print("leaf_pieces %.1fs" % (time.time()-t0))
from fractions import Fraction as F
I = refine.I
a = {I["a44"]:1, I["b12"]:0, I["b42"]:1, I["b44"]:1, I["c14"]:0, I["c24"]:0, I["c44"]:1,
     I["b22"]:0, I["b32"]:0, I["c13"]:0, I["c23"]:0, I["c33"]:"mix", I["c34"]:0, I["c43"]:1}
t0=time.time(); full = seqset.full_case_system(lab, pieces, a); print("full_case_system %.1fs" % (time.time()-t0))
P,Kd,gens,bounds,why = full
t0=time.time(); e,c = seqset.empty(P,Kd,gens,bounds,600); print("emptiness -> %s  %.1fs" % (e, time.time()-t0))
t0=time.time(); w = seqset.witness_for(lab, pieces, a); print("witness -> %s  %.1fs" % ("found" if w else "none", time.time()-t0))
