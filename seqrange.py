"""Ranges over the SEQUENTIAL set: for every coordinate still free after the
refinement, the exact inf/sup over each leaf's surviving cases, each bound an
emptiness certificate ({case system, x_v > T} has no point) the way nefull.py
does it for the Nash set.
usage:  python seqrange.py [workers]"""
import json, glob, sys, time
import numpy as np, sympy as sp
from fractions import Fraction as F
import seqset, refine, certbox

L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
CAND = [F(n, d) for d in (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128) for n in range(d + 1)]
CAND = sorted(set(CAND))


def bound(arg):
    path, idx, name, sign = arg
    d = json.load(open(path)); k = d["leaf"]; lab = L[k]
    rec = d["cases"][idx]
    assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
    pieces = seqset.leaf_pieces(lab)
    built = seqset.full_case_system(lab, pieces, assign)
    if built is None: return path, idx, name, sign, None, 0
    P, Kd, gens, bounds, why = built
    names = [str(g) for g in gens]
    if name not in names: return path, idx, name, sign, None, 0
    j = names.index(name)
    t0 = time.time(); best = None
    cands = [c for c in CAND if 0 <= c <= 1]
    for T in (sorted(cands, reverse=True) if sign > 0 else sorted(cands)):
        b2 = [list(b) for b in bounds]
        if sign > 0: b2[j][0] = T; b2[j][2] = False
        else: b2[j][1] = T; b2[j][3] = False
        r = certbox.prove_empty_cert(P, Kd, gens, b2, 1500, chord=False, exact_dual=False)
        if r[0]: best = T                      # {x >= T} (or <= T) is empty
        else: break
        if time.time() - t0 > 600: break
    return path, idx, name, sign, best, time.time() - t0


if __name__ == "__main__":
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    jobs = []
    for p in sorted(glob.glob("seq_*.json")):
        d = json.load(open(p))
        for i, rec in enumerate(d["cases"]):
            if rec["status"] != "SEQUENTIAL": continue
            for n, v in rec["assign"].items():
                if v == "mix":
                    jobs.append((p, i, n, +1)); jobs.append((p, i, n, -1))
    print("%d bounds to compute" % len(jobs), flush=True)
    from multiprocessing import Pool
    out = []
    with Pool(nw) as pool:
        for path, idx, name, sign, T, secs in pool.imap_unordered(bound, jobs):
            out.append((path, idx, name, sign, T))
            print("   %-12s case %d  %-4s %s -> %s  (%.0fs)" % (path, idx, name, "sup" if sign > 0 else "inf", T, secs), flush=True)
    with open("seq_ranges.txt", "w") as f:
        for path, idx, name, sign, T in sorted(out, key=lambda t: (t[0], t[1], t[2], -t[3])):
            f.write("%-14s case %d  %-4s  %s  %s\n" % (path, idx, name, "sup" if sign > 0 else "inf", T))
    print("wrote seq_ranges.txt")
