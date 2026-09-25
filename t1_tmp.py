import numpy as np, json, gzip, time
import refine, exlp
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
with gzip.open("nefull_certs.json.gz","rt") as f: C = json.load(f)
k = 469
key, w = [(kk, r["witness"]) for kk, r in C.items() if kk.startswith("469:") and r.get("witness")][0]
lab = L[k]; vals = {nm: F(*map(int, s.split("/"))) for nm, s in w.items()}
sig = refine.profile_from(lab, vals); D = refine.D_all(); J = refine.jac()

Z = [v for v in range(48) if sig[v] == 0]; O = [v for v in range(48) if sig[v] == 1]
M = [v for v in range(48) if 0 < sig[v] < 1]
col = {}; n = 0
for v in Z: col[("p", v)] = n; n += 1
for v in O: col[("n", v)] = n; n += 1
for v in M: col[("u", v)] = n; n += 1; col[("w", v)] = n; n += 1
def gvec(v):
    a = [F(0)] * n
    for ww, dp in J[v].items():
        g = refine.ev(dp, sig)
        if g == 0: continue
        if ("p", ww) in col: a[col[("p", ww)]] += g
        elif ("n", ww) in col: a[col[("n", ww)]] -= g
        else: a[col[("u", ww)]] += g; a[col[("w", ww)]] -= g
    return a
A_ub = []; b_ub = []; A_eq = []; b_eq = []
for v in range(48):
    d0 = refine.ev(D[v], sig)
    if 0 < sig[v] < 1: A_eq.append(gvec(v)); b_eq.append(F(0))
    elif sig[v] == 0 and d0 == 0: A_ub.append(gvec(v)); b_ub.append(F(0))
    elif sig[v] == 1 and d0 == 0: A_ub.append([-x for x in gvec(v)]); b_ub.append(F(0))
u = [F(1)] * n
print("blocked-at-first-order test: max delta_v over the cone (0 = cannot tremble at the leading scale)")
for v in Z + O:
    c = [F(0)] * n; c[col[("p", v)] if v in Z else col[("n", v)]] = F(1)
    st, val, x = exlp.solve(c, A_ub, b_ub, A_eq, b_eq, u, maxpiv=20000)
    print("  %-4s (at %s)  max = %-8s %s" % (NAME[v], sig[v], val, "BLOCKED" if val == 0 else ""), flush=True)
