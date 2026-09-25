import json, numpy as np, sympy as sp, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
d = json.load(open("seq_62.json")); lab = L[62]
case = [c for c in d["cases"] if c["status"] == "SEQUENTIAL" and c["assign"].get("c23") == "mix"][0]
s = [F(case["witness"][NAME[i]]) for i in range(48)]
print("Nash check:", seqset.verify_point(lab, s) or "OK")
pieces = seqset.leaf_pieces(lab)
polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
sub = {syms[i]: sp.Rational(s[i].numerator, s[i].denominator) for i in sorted(syms)}
bel = {sp.Symbol(k): sp.Rational(F(v).numerator, F(v).denominator) for k, v in case["beliefs"].items()}
print("beliefs:", {str(k): str(v) for k, v in bel.items()})
bad = 0
for v in unreached:
    a = sp.expand(A[v].subs(sub))
    if a == 0: continue
    val = sp.nsimplify(a.subs(bel))
    free = [x for x in a.free_symbols if x not in bel]
    x = s[v]; need = "=0" if 0 < x < 1 else (">=0" if x == 1 else "<=0")
    ok = (val == 0) if need == "=0" else (val >= 0 if need == ">=0" else val <= 0)
    if free: ok = "?"
    if ok is not True: bad += 1
    print("   A_%-4s (x=%-6s need %-4s) = %-10s %s%s" % (NAME[v], x, need, val, "OK" if ok is True else ("UNRESOLVED %s" % free if ok == "?" else "*** VIOLATED"), ""))
print("violations:", bad)
