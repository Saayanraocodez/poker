"""Targeted exact witnesses for the sub-family-C leaves (97, 196, 198), whose
Table-3 region needs a SMALL positive b23 (b23 <= (b11-b21)/(2(1-b21))) that the
generic grid never samples.  Same exact pipeline: family point, every Nash
condition verified in Fractions, then the belief LP -- uniform scale first, then
every ordering of P1's openings."""
import json, itertools, time, sys
import numpy as np
from fractions import Fraction as F
import seqset, refine

L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
B11 = [F(1, 8), F(1, 6), F(3, 16), F(1, 5), F(1, 4), F(1, 10), F(1, 12)]
B21 = [F(0), F(1, 32), F(1, 24), F(1, 16), F(1, 12), F(1, 10)]
B23 = [F(0), F(1, 64), F(1, 48), F(1, 40), F(1, 32), F(1, 24), F(1, 20)]
C11 = [F(1, 2), F(1, 4), F(1, 3), F(3, 8), F(0)]
MIXV = [F(1, 64), F(1, 32), F(1, 16), F(1, 8), F(1, 2), F(9, 16), F(5, 8), F(11, 16), F(3, 4), F(13, 16)]


def search(path, idx, tlimit=900):
    d = json.load(open(path)); k = d["leaf"]; lab = L[k]; rec = d["cases"][idx]
    pieces = seqset.leaf_pieces(lab)
    assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
    mixed = [v for v, val in assign.items() if val == "mix"]
    fixed = {n: F(int(lab[I[n]])) for n in ("b11", "b21", "b23", "c11") if lab[I[n]] in (0, 1)}
    grids = {"b11": B11, "b21": B21, "b23": B23, "c11": C11}
    free = [n for n in ("b11", "b21", "b23", "c11") if n not in fixed]
    t0 = time.time(); tried = 0
    for pars in itertools.product(*[grids[n] for n in free]):
        pv = dict(zip(free, pars)); pv.update(fixed)
        for vals in itertools.product(MIXV, repeat=len(mixed)):
            if time.time() - t0 > tlimit: return None, tried
            off = {}
            for v, val in assign.items():
                if val in (0, 1): off[NAME[v]] = F(int(val))
            for i in range(48):
                if lab[i] == 0: off.setdefault(NAME[i], F(0))
                elif lab[i] == 1: off.setdefault(NAME[i], F(1))
            off.update({NAME[v]: x for v, x in zip(mixed, vals)})
            for n in ("b11", "b21", "b23", "c11"): off.pop(n, None)
            s = seqset.family_point(pv["b11"], pv["b21"], pv["b23"], pv["c11"], off)
            if seqset.verify_point(lab, s) is not None: continue
            tried += 1
            st, m, r = seqset.is_sequential(pieces, s, lab)
            if st == "sequential": return (s, r, {}), tried
            st2, order, sol = seqset.seq_orderings(lab, s, pieces)
            if st2 == "sequential": return (s, sol, order), tried
    return None, tried


if __name__ == "__main__":
    todo = [("seq_196.json", 1), ("seq_196.json", 0), ("seq_198.json", 0), ("seq_97.json", 0)]
    for path, idx in todo:
        t0 = time.time(); w, tried = search(path, idx)
        d = json.load(open(path)); rec = d["cases"][idx]
        tag = {k: v for k, v in rec["assign"].items() if k in ("b22", "c23", "c33")}
        if w is None:
            print("%-13s case %d %s -> no witness (%d Nash points tested, %.0fs)" % (path, idx, tag, tried, time.time() - t0), flush=True); continue
        s, r, order = w
        rec["status"] = "SEQUENTIAL"
        rec["witness"] = {NAME[i]: str(s[i]) for i in range(48)}
        rec["beliefs"] = {a: str(b) for a, b in r.items()}
        rec["tremble_order"] = {a: int(b) for a, b in (order or {}).items()}
        d["undecided"] -= 1; d["alive"] += 1
        json.dump(d, open(path, "w"), indent=1)
        print("%-13s case %d %s -> SEQUENTIAL  b11=%s b21=%s b23=%s c11=%s %s order %s  (%.0fs)" % (
            path, idx, tag, s[I["b11"]], s[I["b21"]], s[I["b23"]], s[I["c11"]],
            " ".join("%s=%s" % (NAME[v], s[v]) for v in range(48) if NAME[v] in ("c23", "c33")), order or "uniform", time.time() - t0), flush=True)
