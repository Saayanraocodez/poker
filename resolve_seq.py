"""Second pass over seqrun's UNDECIDED cases: a much larger emptiness budget
(with the chord contractor) and a wider exact witness search.  Updates
seq_<leaf>.json in place.
usage:  python resolve_seq.py [workers]"""
import json, glob, sys, time
import numpy as np
import seqset, refine, certbox

L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I


def one(arg):
    path, idx = arg
    d = json.load(open(path)); k = d["leaf"]; lab = L[k]
    rec = d["cases"][idx]
    pieces = seqset.leaf_pieces(lab)
    assign = {}
    for n, v in rec["assign"].items():
        assign[I[n]] = v if v == "mix" else int(v)
    t0 = time.time()
    w = seqset.witness_for(lab, pieces, assign)
    if w is None: w = seqset.witness_guided(lab, pieces, assign)
    if w is not None:
        s, r, order = w
        return path, idx, "SEQUENTIAL", {"witness": {NAME[i]: str(s[i]) for i in range(48)},
                                         "beliefs": {a: str(b) for a, b in r.items()},
                                         "tremble_order": {a: int(b) for a, b in (order or {}).items()}}, time.time() - t0
    built = seqset.full_case_system(lab, pieces, assign)
    if built is None: return path, idx, "EMPTY", {}, time.time() - t0
    P, Kd, gens, bounds, why = built
    # a ladder: the chord contractor costs ~1 s a node, so try a wider cheap
    # search first (the 30,000-node chord search did not finish one case in 45 min)
    for budget, chord in ((4000, False), (1200, True)):
        r = certbox.prove_empty_cert(P, Kd, gens, bounds, budget, chord=chord, exact_dual=False)
        if r[0]: return path, idx, "EMPTY", {"cert": r[1]}, time.time() - t0
    return path, idx, "UNDECIDED", {}, time.time() - t0


if __name__ == "__main__":
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    jobs = []
    for p in sorted(glob.glob("seq_*.json")):
        d = json.load(open(p))
        for i, rec in enumerate(d["cases"]):
            if rec["status"] == "UNDECIDED": jobs.append((p, i))
    print("%d undecided cases" % len(jobs), flush=True)
    from multiprocessing import Pool
    upd = {}
    with Pool(nw) as pool:
        for path, idx, st, extra, secs in pool.imap_unordered(one, jobs):
            upd.setdefault(path, []).append((idx, st, extra))
            print("   %s case %d -> %-10s (%.0fs)" % (path, idx, st, secs), flush=True)
    for path, items in upd.items():
        d = json.load(open(path))
        for idx, st, extra in items:
            d["cases"][idx]["status"] = st; d["cases"][idx].update(extra)
            if st == "EMPTY": d["killed"] += 1; d["undecided"] -= 1
            elif st == "SEQUENTIAL": d["alive"] += 1; d["undecided"] -= 1
        json.dump(d, open(path, "w"), indent=1)
    print("done")
