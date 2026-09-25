import numpy as np, json, gzip, sympy as sp, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
with gzip.open("nefull_certs.json.gz","rt") as f: C = json.load(f)
k = 469; lab = L[k]; pieces = seqset.leaf_pieces(lab)
polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
kk, w = [(a, b["witness"]) for a, b in C.items() if a.startswith("469:") and b.get("witness")][0]
vals = {nm: F(*map(int, s.split("/"))) for nm, s in w.items()}; vals["b24"] = F(0)
sig = refine.profile_from(lab, vals)
print("point", kk, ":", ", ".join("%s=%s" % (NAME[i], sig[i]) for i in range(48) if 0 < sig[i] < 1))
sub = {syms[i]: sp.Rational(sig[i].numerator, sig[i].denominator) for i in sorted(syms)}
print("\nbelief conditions at this point (A_v, with the required sign):")
for v in unreached:
    a = sp.expand(A[v].subs(sub))
    if a == 0: print("   %-4s : vacuous at leading order" % NAME[v]); continue
    x = sig[v]; need = "= 0" if 0 < x < 1 else (">= 0" if x == 1 else "<= 0")
    print("   %-4s (x=%s) : %s %s" % (NAME[v], x, sp.nsimplify(sp.factor(a)), need))
