"""Markdown tables from nefull_ranges.txt: the union window of every coordinate
over the complete Nash set, and per sub-family, with attainment marks.

2026-11-16 (erratum 12): the union used to run only over the leaves in which a coordinate has a
row in nefull_ranges.txt.  A leaf in which the coordinate is PRIVATE (D = 0, "free" in
nefull_systems.txt) or OWN-UNREACHED (b43, b44 where b41 = 1: Theorem 5 frees them) has no row, and
there the coordinate ranges over all of [0, 1].  Leaving those leaves out gave b44 the window
[17/32, 1] "over all equilibria"; the family point b11 = b21 = 1/4 with b44 = 0 is an exact Nash
equilibrium (independent_check/check_34.py, section 4).  Both kinds of leaf now contribute [0, 1],
attained, and a footnote keeps the bounds that hold where the coordinate is constrained.

usage:  python ranges_table.py > ranges_table.md"""
import re, sys, os, json, ast
from fractions import Fraction as F
import kuhn3p as K
I = K.NAME_IDX
rows = []
for l in open("nefull_ranges.txt"):
    m = re.match(r"\s*(\d+)\s+([ABC])\s+(\S+)\s+(MIX|DC)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", l)
    if m: rows.append(m.groups())
# sharper certificates (sharpen_ranges.py; replayed by check_sharpened.py) and exact witnesses
import glob
_sh = {}
for _f in glob.glob(os.path.join("ranges_sharpened", "*_*_*.json")):
    _d = json.load(open(_f)); _sh[(str(_d["leaf"]), _d["coord"], _d["side"])] = F(_d["T"])
_wit = set()
if os.path.exists(os.path.join("ranges_sharpened", "witnesses.json")):
    for _k in json.load(open(os.path.join("ranges_sharpened", "witnesses.json"))):
        _l, _c, _side, _T = _k.split(":"); _wit.add((_l, _c, _side, F(_T)))
def _num(s_):
    return F(s_) if "/" in s_ or s_.isdigit() else F(s_)
_rows2 = []; NSHARP = 0
for leaf, sub, name, lbl, lo, hi, alo, ahi in rows:
    T = _sh.get((leaf, name, "sup"))
    if T is not None and T < _num(hi): hi = str(T); ahi = "None"; NSHARP += 1
    T = _sh.get((leaf, name, "inf"))
    if T is not None and T > _num(lo): lo = str(T); alo = "None"; NSHARP += 1
    if (leaf, name, "sup", _num(hi)) in _wit: ahi = "True"
    if (leaf, name, "inf", _num(lo)) in _wit: alo = "True"
    _rows2.append((leaf, sub, name, lbl, lo, hi, alo, ahi))
rows = _rows2
def val(s):
    if s == "?": return None
    return F(s) if "/" in s or s.isdigit() else F(float(s)).limit_denominator(10**6)
def show(v, att):
    if v is None: return "?"
    txt = str(v) if v.denominator <= 100 else "%.5f" % float(v)
    return txt + ("" if att == "True" else ("⁻" if att == "False" else "ᶜ"))
by = {}
for leaf, sub, name, lbl, lo, hi, alo, ahi in rows:
    by.setdefault(name, []).append((sub, int(leaf), lbl, val(lo), val(hi), alo, ahi))
# the label vectors of the 12 FAMILY leaves: the run's own files if present, else the committed copy
# (independent_check/family_leaves.json, keyed by the same leaf ids)
NAME = K.PARAM_NAME
if os.path.exists("enum6_pat_silentR.npy") and os.path.exists("symleaf_silentR.npz"):
    import numpy as np, symleaf as SL
    L = np.load("enum6_pat_silentR.npy")
    with np.load("symleaf_silentR.npz") as z: vd = z["verdict"]
    LEAVES = {int(k): [int(v) for v in L[k]] for k in np.flatnonzero(vd == SL.VC["FAMILY"])}
else:
    LEAVES = {int(k): v for k, v in json.load(open(os.path.join("independent_check", "family_leaves.json"))).items()}
# private coordinates per leaf (D = 0 on the leaf: free in [0, 1]), from nefull_systems.txt
PRIV = {}
for blk in open("nefull_systems.txt").read().split("=== leaf ")[1:]:
    PRIV[int(blk.split()[0])] = ast.literal_eval(re.search(r"free \(private, D = 0\): (\[.*?\])", blk).group(1))
constrained = {name: [e for e in es] for name, es in by.items()}        # rows of nefull_ranges.txt only
for k, lab in sorted(LEAVES.items()):
    sub = "A" if lab[I["c11"]] == 0 else ("B" if lab[I["c21"]] == 2 else "C")
    # coordinates pinned by a 0/1 LABEL in a leaf are attained there at that value
    for i in range(48):
        if lab[i] in (0, 1) and NAME[i] in by:
            e = (sub, int(k), "LAB", F(int(lab[i])), F(int(lab[i])), "True", "True")
            by[NAME[i]].append(e); constrained[NAME[i]].append(e)
    # private in this leaf: all of [0, 1]
    for name in PRIV.get(k, []):
        if name in by: by[name].append((sub, int(k), "FREE", F(0), F(1), "True", "True"))
    # own-unreached (Theorem 5): P2 never reaches KKBF / KKBC with card j when b_j1 = 1
    for j in "1234":
        if lab[I["b" + j + "1"]] == 1:
            for name in ("b" + j + "3", "b" + j + "4"):
                if name in by: by[name].append((sub, int(k), "FREE", F(0), F(1), "True", "True"))
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
freed = sorted((n for n in by if any(e[2] == "FREE" for e in by[n]) and [min(e[3] for e in by[n]), max(e[4] for e in by[n])] !=
                [min(e[3] for e in constrained[n] if e[3] is not None), max(e[4] for e in constrained[n] if e[4] is not None)]), key=lambda n: I[n])
for name in freed:
    es = constrained[name]
    def cell(sel):
        if not sel: return "–"
        l = min(e[3] for e in sel); h = max(e[4] for e in sel)
        la = "True" if any(e[5] == "True" for e in sel if e[3] == l) else ("False" if all(e[5] == "False" for e in sel if e[3] == l) else "None")
        ha = "True" if any(e[6] == "True" for e in sel if e[4] == h) else ("False" if all(e[6] == "False" for e in sel if e[4] == h) else "None")
        return "[%s, %s]" % (show(l, la), show(h, ha))
    where = sorted({e[1] for e in by[name] if e[2] == "FREE"})
    print("‡ `%s` is free in [0, 1] in leaves %s (private, or own-unreached where `b41 = 1`). In the leaves where it is constrained: all %s, A %s, B %s, C %s."
          % (name, ", ".join(map(str, where)), cell(es), cell([e for e in es if e[0] == "A"]), cell([e for e in es if e[0] == "B"]), cell([e for e in es if e[0] == "C"])))
print("‡ `b43` equals 1 wherever `b41 < 1` (a reached call with the top card); in the two leaves with `b41 = 1` (70, 440) it is own-unreached and free.")
print()
print("%d bounds are sharper than nefull_ranges.txt: certified by sharpen_ranges.py at a rational just outside the best equilibrium value found, and replayed by check_sharpened.py (2026-11-17)." % NSHARP)
print()
print("Marks: a bare number is attained (exact rational witness in the leaf, verified); ⁻ = certified strict bound (not attained); ᶜ = certified bound, attainment undecided at the search precision (the true extremum lies between the best known equilibrium value and this bound).")
