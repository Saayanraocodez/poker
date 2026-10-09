"""Knuth-weighted estimate of where enumc2's time goes on the hard branches.
A random root-to-leaf walk that follows enumc2.subtree exactly: live children = float-live
children + float-dead children whose kill ladder FAILED (enumc2 keeps and splits those).  Every
ladder call is recorded with its Knuth weight w (product of live-child counts on the path), so
sum(w * t) over a walk is an unbiased estimate of that branch's total ladder time.  Contexts:
  layer     depth % 4 == 0 test on a node
  fdead     a float-dead child of a node with no uncertifiable ancestor
  fdead_u   a float-dead child below an uncertifiable (float-unsure) ancestor
usage:  python probe_knuth.py <walks per branch> <workers> [walk cap s]  -> probe_knuth.jsonl"""
import os, sys, time, json
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
import numpy as np
from multiprocessing import Pool
from probe_ladder import SPECS, ladder


def walk(a):
    spec, seed, cap = a
    import treesize6 as T6
    U, MIX, DC = T6.U, T6.MIX, T6.DC
    rng = np.random.default_rng(seed); weak = T6.WEAK; t0 = time.time()
    root_lab, LO, HI = T6.root_of(spec)
    labp, A, B, al = T6.propagate(root_lab[None], LO[None], HI[None], weak)
    lab = root_lab.copy(); lab[(lab == U) & (labp[0] == DC)] = DC; LO, HI = A[0], B[0]
    rows = []; depth = 0; w = 1.0; under = False; end = "?"
    while True:
        if time.time() - t0 > cap: end = "cap"; break
        if depth % 4 == 0 and depth > 0:
            k, ts = ladder(lab)
            rows.append({"ctx": "layer" + ("_u" if under else ""), "rung": k, "ts": ts, "w": w, "depth": depth})
            if k >= 0: end = "layer-kill"; break
        u = [x for x in T6.ORDER if lab[x] == U]
        if not u: end = "leaf"; break
        v = u[0]; kids = []
        for l in (0, 1, MIX):
            l2 = lab.copy(); a2 = LO.copy(); b2 = HI.copy(); l2[v] = l
            if l == 0: b2[v] = 0.0
            elif l == 1: a2[v] = 1.0
            kids.append((l2, a2, b2))
        allowed = [LO[v] <= 0.0, HI[v] >= 1.0, HI[v] > 0.0 and LO[v] < 1.0]
        L2, A2, B2, al2 = T6.propagate(np.array([q[0] for q in kids]), np.array([q[1] for q in kids]), np.array([q[2] for q in kids]), weak)
        live = []
        for t in range(3):
            if allowed[t] and al2[t]:
                lc = kids[t][0].copy(); lc[(lc == U) & (L2[t] == DC)] = DC
                live.append((lc, A2[t], B2[t], False)); continue
            k, ts = ladder(kids[t][0])
            rows.append({"ctx": "fdead" + ("_u" if under else ""), "rung": k, "ts": ts, "w": w, "depth": depth + 1})
            if k < 0: live.append((kids[t][0], kids[t][1], kids[t][2], True))
        if not live: end = "all-dead"; break
        pick = live[rng.integers(len(live))]; w *= len(live)
        lab, LO, HI = pick[0], pick[1], pick[2]; under = under or pick[3]; depth += 1
    return {"spec": spec, "seed": seed, "end": end, "depth": depth, "secs": round(time.time() - t0, 1), "rows": rows}


if __name__ == "__main__":
    nwalk, nw = int(sys.argv[1]), int(sys.argv[2]); cap = float(sys.argv[3]) if len(sys.argv) > 3 else 900
    jobs = [(s, 7000 + 1000 * i + j, cap) for j in range(nwalk) for i, s in enumerate(SPECS)]
    t0 = time.time(); n = 0
    with Pool(nw) as pool, open("probe_knuth.jsonl", "w") as f:
        for r in pool.imap_unordered(walk, jobs, chunksize=1):
            f.write(json.dumps(r) + "\n"); f.flush(); n += 1
            print("%3d/%d  %-30s end %-10s depth %2d  %6.0fs  (%.0fs)" % (n, len(jobs), r["spec"], r["end"], r["depth"], r["secs"], time.time() - t0), flush=True)
