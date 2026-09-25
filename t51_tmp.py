import json, numpy as np, time, seqset, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
d = json.load(open("seq_18.json")); lab = L[18]; pieces = seqset.leaf_pieces(lab)
und = [r for r in d["cases"] if r["status"] == "UNDECIDED"]
for rec in und:
    assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
    tag = {k: v for k, v in rec["assign"].items() if k in ("a33","a34","c32")}
    c = seqset.one_signed_conflict(lab, pieces, assign)
    if c is not None:
        print("%-44s KILLED: A_%s one-signed" % (tag, NAME[c]), flush=True); continue
    t0 = time.time()
    ok, info = seqset.kill_by_orderings(lab, pieces, assign, ("b11", "b21", "b31", "b41"), 300)
    print("%-44s %s  (%.0fs)" % (tag, ("KILLED under all %d orderings of P2's openings" % info) if ok else ("survives ordering %s" % info), time.time()-t0), flush=True)
