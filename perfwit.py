"""A PERFECT witness for each surviving pattern: the enumeration's witness is
whatever point the search hit first, often a corner where some deterrence is
tight and the first-order test cannot decide.  Here the family parameters are
moved to generic interior rationals and `refine.perfect_cert` is applied, so a
success is a certificate that the pattern contains (extensive-form) PERFECT --
equivalently, by Lemma R1, extensive-form proper -- equilibria.
usage:  python perfwit.py [workers]"""
import sys as _sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _sys.stdout = _sys.stderr = open('log_perfwit.txt', 'a', buffering=1, encoding='utf-8', errors='replace')   # Windowless launch
import json, glob, sys, time, itertools
import numpy as np
from fractions import Fraction as F
import refine, seqset

L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
PAR = [F(1, 8), F(1, 6), F(3, 16), F(5, 24), F(1, 5), F(1, 4), F(1, 12), F(1, 10), F(0)]
MID = [F(9, 16), F(5, 8), F(11, 16), F(17, 32), F(19, 32), F(21, 32), F(3, 5), F(2, 3)]


def one(arg):
    path, idx = arg
    d = json.load(open(path)); k = d["leaf"]; lab = L[k]
    rec = d["cases"][idx]
    pieces = seqset.leaf_pieces(lab)
    J = refine.jac()
    assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
    mixed = [v for v, val in assign.items() if val == "mix"]
    free_par = [n for n in ("b11", "b21", "b23", "c11") if lab[I[n]] not in (0, 1)]
    fixed = {n: F(int(lab[I[n]])) for n in ("b11", "b21", "b23", "c11") if lab[I[n]] in (0, 1)}
    t0 = time.time()
    for pars in itertools.product(PAR, repeat=len(free_par)):
        pv = dict(zip(free_par, pars)); pv.update(fixed)
        for vals in itertools.product(MID, repeat=len(mixed)):
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
            st, m, r = seqset.is_sequential(pieces, s, lab)
            if st != "sequential": continue
            ok, info = refine.perfect_cert(s, J)
            if ok:
                return path, idx, {"perfect_witness": {NAME[i]: str(s[i]) for i in range(48)},
                                   "perfect_beliefs": {a: str(b) for a, b in r.items()},
                                   "perfect_s": str(info["s"]), "perfect_rank": info["rank"]}, time.time() - t0
            if time.time() - t0 > 240: return path, idx, None, time.time() - t0
    return path, idx, None, time.time() - t0


if __name__ == "__main__":
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    jobs = []
    for p in sorted(glob.glob("seq_*.json")):
        d = json.load(open(p))
        for i, rec in enumerate(d["cases"]):
            if rec["status"] == "SEQUENTIAL": jobs.append((p, i))
    print("%d sequential patterns" % len(jobs), flush=True)
    from multiprocessing import Pool
    upd = {}; got = 0
    with Pool(nw) as pool:
        for path, idx, extra, secs in pool.imap_unordered(one, jobs):
            if extra: upd.setdefault(path, []).append((idx, extra)); got += 1
            print("   %-12s case %d -> %s  (%.0fs)" % (path, idx, "PERFECT" if extra else "no perfect witness found", secs), flush=True)
    # a separate file: seq_<leaf>.json belongs to seqrun / resolve_seq
    json.dump({"%s#%d" % (p, i): e for p, items in upd.items() for i, e in items},
              open("perf_witnesses.json", "w"), indent=1)
    print("perfect witnesses: %d of %d -> perf_witnesses.json" % (got, len(jobs)))
