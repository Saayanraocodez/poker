import json, numpy as np, refine, seqset
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
lab = L[469]; pieces = seqset.leaf_pieces(lab); J = refine.jac()
d = json.load(open("seq_469.json"))
rec = [r for r in d["cases"] if r["status"] == "SEQUENTIAL" and r["assign"].get("c23") == 0][0]
assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
print("assign:", {NAME[v]: x for v, x in assign.items()})
off = {}
for v, val in assign.items():
    if val in (0, 1): off[NAME[v]] = F(int(val))
for i in range(48):
    if lab[i] == 0: off.setdefault(NAME[i], F(0))
    elif lab[i] == 1: off.setdefault(NAME[i], F(1))
off["c33"] = F(9,16)
for n in ("b11","b21","b23","c11"): off.pop(n, None)
s = seqset.family_point(F(1,8), F(1,8), F(0), F(1,4), off)
print("verify:", seqset.verify_point(lab, s) or "Nash OK")
st, m, r = seqset.is_sequential(pieces, s, lab)
print("sequential:", st, m)
ok, info = refine.perfect_cert(s, J)
print("perfect:", ok, info if not ok else "s*=%s rank %d" % (info["s"], info["rank"]))
print("free_par would be:", [n for n in ("b11","b21","b23","c11") if lab[I[n]] not in (0,1)])
