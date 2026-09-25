import json, numpy as np, sympy as sp, seqset, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
d = json.load(open("seq_18.json")); lab = L[18]; pieces = seqset.leaf_pieces(lab)
print("leaf 18 labels: MIX", [NAME[i] for i in range(48) if lab[i] == 2])
und = [r for r in d["cases"] if r["status"] == "UNDECIDED"]
print("%d undecided; decided-coordinate patterns:" % len(und))
for r in und: print("   ", {k: v for k, v in r["assign"].items() if k in ("a33","a34","a43","c22","c32")})
rec = und[0]
assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
P, Kd, gens, bounds, why = seqset.full_case_system(lab, pieces, assign)
print("\ncase", {k: v for k, v in rec["assign"].items() if k in ("a33","a34","a43","c22","c32")})
print("gens:", [str(g) for g in gens])
for p, k, w in zip(P, Kd, why):
    if w.startswith("belief") and any(str(s).startswith("r_") for s in p.free_symbols):
        print("   %-12s %s %s 0" % (w, sp.factor(p), k))
print("order-0 (profile) conditions involving the decided coordinates:")
for p, k, w in zip(P, Kd, why):
    fs = {str(s) for s in p.free_symbols}
    if not any(x.startswith("r_") for x in fs) and fs & {"a33","a34","c32","c33","c22"}:
        print("   %-12s %s %s 0" % (w, sp.factor(p), k))
