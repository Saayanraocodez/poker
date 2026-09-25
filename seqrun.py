"""Driver: the sequential-equilibrium set of every FAMILY leaf (seqset.py).
usage:  python seqrun.py [workers] [leaf ...]     -> seq_<leaf>.json, seq_summary.txt"""
import numpy as np, sympy as sp, sys, time, json, gzip
from fractions import Fraction as F
import seqset, refine, certbox

L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME


def run(k, budget=60, leaf_budget=400):
    lab = L[k]; t0 = time.time()
    pieces = seqset.leaf_pieces(lab)
    out, pin = refine.closure(lab, verbose=False)
    assign0 = {v: r[0] for v, r in out.items()}
    # proved for every leaf (MASTER_DATA 16.13): c43 = 1 and c13 = 0 from the coefficient
    # bounds of their leading forms over Table 4's windows; b32 = 0 and c34 = 0 by the
    # two-step arguments.  Injecting them leaves the genuinely coupled coordinates.
    for nm, val in (("b32", 0), ("c34", 0), ("c13", 0), ("c43", 1)):
        v = seqset.I[nm]
        if lab[v] == seqset.DC and v not in assign0: assign0[v] = val
    rest = [v for v in pieces[6] if v not in assign0 and lab[v] == seqset.DC]
    res = {"leaf": int(k), "closure": {NAME[v]: [r[0], r[1], str(r[2])] for v, r in out.items()},
           "decide": [NAME[v] for v in rest], "cases": [], "killed": 0, "alive": 0, "undecided": 0}
    stack = [dict(assign0)]
    while stack:
        assign = stack.pop()
        fo = seqset.propagate(lab, pieces, assign)
        if any(v in assign and assign[v] != val for v, val in fo.items()):
            res["killed"] += 1; continue
        assign = dict(assign); assign.update({v: val for v, val in fo.items() if v not in assign})
        todo = [v for v in rest if v not in assign]
        built = seqset.build_case(lab, pieces, assign)
        if built[0] is None: res["killed"] += 1; continue
        P, Kd, gens, bounds, deg = built
        e, cert = seqset.empty(P, Kd, gens, bounds, leaf_budget if not todo else budget)
        if e: res["killed"] += 1; continue
        if todo:
            v = todo[0]
            for val in (0, 1, "mix"):
                a2 = dict(assign); a2[v] = val; stack.append(a2)
            continue
        full = seqset.full_case_system(lab, pieces, assign)
        if full is None: res["killed"] += 1; continue
        P, Kd, gens, bounds, why = full
        w = seqset.witness_for(lab, pieces, assign)      # cheap; a witness settles it
        if w is None: w = seqset.witness_guided(lab, pieces, assign)
        if w is None:
            e, cert = seqset.empty(P, Kd, gens, bounds, 1500)
            if e: res["killed"] += 1; continue
        rec = {"assign": {NAME[v]: (val if val == "mix" else int(val)) for v, val in assign.items()},
               "gens": [str(g) for g in gens]}
        if w is not None:
            s, r, order = w
            rec["witness"] = {NAME[i]: str(s[i]) for i in range(48)}
            rec["beliefs"] = {a: str(b) for a, b in r.items()}
            # the belief is a limit along trembles of these RELATIVE orders (class 0 the
            # largest); empty means one uniform scale.  Without it the witness cannot be
            # rechecked: a leading form keeps only the terms of its own lowest class.
            rec["tremble_order"] = {k: int(v) for k, v in (order or {}).items()}
            res["alive"] += 1; rec["status"] = "SEQUENTIAL"
        else:
            res["undecided"] += 1; rec["status"] = "UNDECIDED"
        res["cases"].append(rec)
        print("   leaf %d %-9s %s" % (k, rec["status"], seqset.fmt_assign({v: val for v, val in assign.items() if v in rest})), flush=True)
    res["seconds"] = time.time() - t0
    json.dump(res, open("seq_%d.json" % k, "w"), indent=1)
    return res


if __name__ == "__main__":
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    leaves = [int(a) for a in sys.argv[2:]] or seqset.FAM
    from multiprocessing import Pool
    t0 = time.time()
    with open("seq_summary.txt", "a") as f:
        with Pool(nw) as pool:
            for res in pool.imap_unordered(run, leaves):
                line = "leaf %4d  closure %2d  decided %d coords  killed %4d  sequential %3d  undecided %3d  %.0fs" % (
                    res["leaf"], len(res["closure"]), len(res["decide"]), res["killed"], res["alive"], res["undecided"], res["seconds"])
                f.write(line + "\n"); f.flush(); print(line, flush=True)
    print("total %.0fs" % (time.time() - t0))
