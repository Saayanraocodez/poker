import json, numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
d = json.load(open("seq_18.json")); lab = L[18]; pieces = seqset.leaf_pieces(lab)
und = [(i, r) for i, r in enumerate(d["cases"]) if r["status"] == "UNDECIDED"][:3]
for i, rec in und:
    assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
    t0 = time.time()
    w = seqset.witness_for(lab, pieces, assign) or seqset.witness_guided(lab, pieces, assign)
    print("case %d %s -> %s (%.0fs)" % (i, {k: v for k, v in rec["assign"].items() if k in ("a33","a34","c32","c23")},
                                        "WITNESS, order %s" % (w[2],) if w else "none", time.time()-t0), flush=True)
