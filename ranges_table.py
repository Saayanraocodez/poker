"""Markdown tables from nefull_ranges.txt: the union window of every coordinate
over the complete Nash set, and per sub-family, with attainment marks.
usage:  python ranges_table.py > ranges_table.md"""
import re, sys
from fractions import Fraction as F
import kuhn3p as K
I = K.NAME_IDX
rows = []
for l in open("nefull_ranges.txt"):
    m = re.match(r"\s*(\d+)\s+([ABC])\s+(\S+)\s+(MIX|DC)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", l)
    if m: rows.append(m.groups())
def val(s):
    if s == "?": return None
    return F(s) if "/" in s or s.isdigit() else F(float(s)).limit_denominator(10**6)
def show(v, att):
    if v is None: return "?"
    txt = str(v) if v.denominator <= 100 else "%.4f" % float(v)
    return txt + ("" if att == "True" else ("⁻" if att == "False" else "ᶜ"))
by = {}
for leaf, sub, name, lbl, lo, hi, alo, ahi in rows:
    by.setdefault(name, []).append((sub, int(leaf), lbl, val(lo), val(hi), alo, ahi))
# coordinates pinned by a 0/1 LABEL in a leaf are attained there at that value
import numpy as np, symleaf as SL
L = np.load("enum6_pat_silentR.npy")
with np.load("symleaf_silentR.npz") as z: vd = z["verdict"]
NAME = K.PARAM_NAME
for k in np.flatnonzero(vd == SL.VC["FAMILY"]):
    lab = L[k]; sub = "A" if lab[I["c11"]] == 0 else ("B" if lab[I["c21"]] == 2 else "C")
    for i in range(48):
        if lab[i] in (0, 1) and NAME[i] in by:
            by[NAME[i]].append((sub, int(k), "LAB", F(int(lab[i])), F(int(lab[i])), "True", "True"))
print("| coordinate | role | over all equilibria | A | B | C |")
print("|---|---|---|---|---|---|")
for name in sorted(by, key=lambda n: I[n]):
    entries = by[name]
    lo = min(e[3] for e in entries if e[3] is not None); hi = max(e[4] for e in entries if e[4] is not None)
    lo_att = any(e[5] == "True" for e in entries if e[3] == lo); hi_att = any(e[6] == "True" for e in entries if e[4] == hi)
    role = "on path (Table 3)" if any(e[2] == "MIX" for e in entries) else "off path"
    cells = []
    for sub in "ABC":
        es = [e for e in entries if e[0] == sub]
        if not es: cells.append("–"); continue
        l = min(e[3] for e in es if e[3] is not None); h = max(e[4] for e in es if e[4] is not None)
        la = "True" if any(e[5] == "True" for e in es if e[3] == l) else ("False" if all(e[5] == "False" for e in es if e[3] == l) else "None")
        ha = "True" if any(e[6] == "True" for e in es if e[4] == h) else ("False" if all(e[6] == "False" for e in es if e[4] == h) else "None")
        cells.append("[%s, %s]" % (show(l, la), show(h, ha)))
    print("| `%s` | %s | [%s, %s] | %s | %s | %s |" % (name, role, show(lo, "True" if lo_att else "None"), show(hi, "True" if hi_att else "None"), *cells))
print()
print("Marks: a bare number is attained (exact rational witness in the leaf, verified); ⁻ = certified strict bound (not attained); ᶜ = certified bound, attainment undecided at the search precision (the true extremum lies between the best known equilibrium value and this bound).")
