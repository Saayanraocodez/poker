import numpy as np, json, gzip, time, itertools, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
with gzip.open("nefull_certs.json.gz","rt") as f: C = json.load(f)
RANK = {"sequential": 3, "boundary": 2, "infeasible": 1, "no tremble": 0, "nonlinear": 0}
out = {}
for k in seqset.FAM:
    lab = L[k]; pieces = seqset.leaf_pieces(lab)
    ws = [(kk, r["witness"]) for kk, r in C.items() if kk.startswith("%d:" % k) and r.get("witness")]
    miss = sorted({NAME[i] for i in range(48) if lab[i] == 3} - set(ws[0][1])) if ws else []
    cnt = {}
    for kk, w in ws:
        best = ("infeasible", None)
        for comb in itertools.product([F(0), F(1), F(1, 3)], repeat=len(miss)):
            vals = {nm: F(*map(int, s.split("/"))) for nm, s in w.items()}
            vals.update(dict(zip(miss, comb)))
            sig = refine.profile_from(lab, vals)
            st, m, r = seqset.is_sequential(pieces, sig, lab)
            if RANK.get(st, 0) > RANK.get(best[0], 0): best = (st, comb)
            if best[0] == "sequential": break
        cnt[best[0]] = cnt.get(best[0], 0) + 1
        out.setdefault(best[0], []).append(kk)
    print("leaf %4d: %2d witnesses, free-private %s -> %s" % (k, len(ws), miss, cnt), flush=True)
print("\ntotals:", {s: len(v) for s, v in out.items()})
json.dump(out, open("seq_witness_class.json", "w"))
