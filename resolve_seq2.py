"""Third pass over seqrun's UNDECIDED patterns, with the two tests that close
the corner leaves (2026-09-24):

  1. one-signed forms on ASSIGNED coordinates (seqset.one_signed_conflict):
     a leading form with all coefficients of one sign settles its coordinate at
     every order, so an interior or opposite value is impossible;
  2. an exhaustive kill over the orderings of a tremble group
     (seqset.kill_by_orderings): under each ordering every form keeps its own
     lowest class, each class is normalised on its own and its ratios are
     strictly positive; empty under all orderings = no consistent belief.

Tried with P1's openings (the generic leaves' beliefs) and P2's openings (the
corner leaves', where b11 = b21 = 0 and P2's bet is the unreached one).  A
pattern that survives both gets the ordering-aware witness search.
usage (windowless):  pythonw.exe resolve_seq2.py [workers]"""
import sys as _sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _sys.stdout = _sys.stderr = open("log_resolve_seq2.txt", "a", buffering=1, encoding="utf-8", errors="replace")
import json, glob, sys, time
import numpy as np
import seqset, refine

L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
G_A = ("a11", "a21", "a31", "a41"); G_B = ("b11", "b21", "b31", "b41")


def one(arg):
    path, idx = arg
    d = json.load(open(path)); k = d["leaf"]; lab = L[k]
    rec = d["cases"][idx]
    pieces = seqset.leaf_pieces(lab)
    assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
    t0 = time.time()
    c = seqset.one_signed_conflict(lab, pieces, assign)
    if c is not None:
        return path, idx, "EMPTY", {"why": "one-signed leading form at %s" % NAME[c]}, time.time() - t0
    for gname, g in (("P2 openings", G_B), ("P1 openings", G_A)):
        ok, info = seqset.kill_by_orderings(lab, pieces, assign, g, 300)
        if ok:
            return path, idx, "EMPTY", {"why": "empty under all %d orderings of %s" % (info, gname)}, time.time() - t0
    w = seqset.witness_for(lab, pieces, assign)
    if w is None: w = seqset.witness_guided(lab, pieces, assign)
    if w is not None:
        s, r, order = w
        return path, idx, "SEQUENTIAL", {"witness": {NAME[i]: str(s[i]) for i in range(48)},
                                         "beliefs": {a: str(b) for a, b in r.items()},
                                         "tremble_order": {a: int(b) for a, b in (order or {}).items()}}, time.time() - t0
    return path, idx, "UNDECIDED", {}, time.time() - t0


if __name__ == "__main__":
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    jobs = []
    for p in sorted(glob.glob("seq_*.json")):
        d = json.load(open(p))
        for i, rec in enumerate(d["cases"]):
            if rec["status"] == "UNDECIDED": jobs.append((p, i))
    print(time.strftime("%m-%d %H:%M  ") + "%d undecided patterns" % len(jobs), flush=True)
    from multiprocessing import Pool
    upd = {}
    with Pool(nw) as pool:
        for path, idx, st, extra, secs in pool.imap_unordered(one, jobs):
            upd.setdefault(path, []).append((idx, st, extra))
            print("   %-13s case %2d -> %-10s %s  (%.0fs)" % (path, idx, st, extra.get("why", ""), secs), flush=True)
    for path, items in upd.items():
        d = json.load(open(path))
        for idx, st, extra in items:
            d["cases"][idx]["status"] = st; d["cases"][idx].update(extra)
            if st == "EMPTY": d["undecided"] -= 1; d["killed"] += 1
            elif st == "SEQUENTIAL": d["undecided"] -= 1; d["alive"] += 1
        json.dump(d, open(path, "w"), indent=1)
    print(time.strftime("%m-%d %H:%M  ") + "done", flush=True)
