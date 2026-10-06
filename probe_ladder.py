"""Where does enumc2's time go on the hard branches?  Random root-to-leaf walks with enumc2's
semantics (float box carried down, certificates from the label box); at every layer node
(depth % 4 == 0) and every float-dead child, run the kill-certificate ladder rung by rung and
record time and outcome.   usage:  python probe_ladder.py <walks per branch> <workers>
-> probe_ladder.jsonl (one line per ladder call) and a summary on stdout."""
import os, sys, time, json
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
import numpy as np
from multiprocessing import Pool

SPECS = ["a11:MIX,a21:MIX,a31:0,a41:MIX", "a11:0,a21:MIX,a31:0,a41:MIX", "a11:MIX,a21:0,a31:0,a41:MIX",
         "a11:0,a21:0,a31:MIX,a41:0", "a11:MIX,a21:MIX,a31:0,a41:1", "a11:0,a21:MIX,a31:MIX,a41:1"]
RUNGS = ((1, False), (1, True), (20, False), (40, True))


def ladder(lab):
    """enumc2.kill_cert, rung by rung -> (rung index that succeeded or -1, [seconds per rung tried])"""
    import enumx, certbox, treesize6 as T6
    U, MIX, DC = T6.U, T6.MIX, T6.DC
    lab = [int(v) for v in lab]
    lab2 = [DC if v == U else v for v in lab]
    P, kinds, free, bounds, private = enumx.node_system(lab2)
    if not P: return -2, []
    for i in private: lab2[i] = DC
    origins = []
    for i in range(48):
        if i in private: continue
        d = enumx._subst(enumx.D_ALL[i], lab2)
        if not d: continue
        l = lab2[i]
        if l == MIX: origins.append(("D", i))
        elif l == 0: origins.append(("0", i))
        elif l == 1: origins.append(("1", i))
        else: origins.append(("DCx", i)); origins.append(("DC1", i))
    ts = []
    for k, (budget, chord) in enumerate(RUNGS):
        t0 = time.time()
        r = certbox.prove_empty_cert(P, kinds, None, bounds, budget, origins=origins, lab=lab2, gidx=list(free), chord=chord, exact_dual=False)
        ts.append(round(time.time() - t0, 3))
        if r[0]: return k, ts
    return -1, ts


def walk(a):
    spec, seed = a
    import treesize6 as T6
    U, MIX, DC = T6.U, T6.MIX, T6.DC
    rng = np.random.default_rng(seed)
    weak = T6.WEAK
    root_lab, LO, HI = T6.root_of(spec)
    labp, A, B, al = T6.propagate(root_lab[None], LO[None], HI[None], weak)
    lab = root_lab.copy(); lab[(lab == U) & (labp[0] == DC)] = DC; LO, HI = A[0], B[0]
    out = []; depth = 0
    while True:
        if depth % 4 == 0 and depth > 0:
            k, ts = ladder(lab)
            out.append({"spec": spec, "seed": seed, "depth": depth, "ctx": "layer", "rung": k, "ts": ts})
            if k >= 0: break                        # the real run kills here
        u = [x for x in T6.ORDER if lab[x] == U]
        if not u: out.append({"spec": spec, "seed": seed, "depth": depth, "ctx": "leaf"}); break
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
            if allowed[t] and al2[t]: live.append(t); continue
            k, ts = ladder(kids[t][0])
            out.append({"spec": spec, "seed": seed, "depth": depth + 1, "ctx": "floatdead", "rung": k, "ts": ts})
        if not live: break
        t = live[rng.integers(len(live))]
        lab = kids[t][0].copy(); lab[(lab == U) & (L2[t] == DC)] = DC; LO, HI = A2[t], B2[t]; depth += 1
    return out


if __name__ == "__main__":
    nwalk, nw = int(sys.argv[1]), int(sys.argv[2])
    jobs = [(s, 1000 * i + j) for i, s in enumerate(SPECS) for j in range(nwalk)]
    t0 = time.time(); rows = []
    with Pool(nw) as pool, open("probe_ladder.jsonl", "w") as f:
        for out in pool.imap_unordered(walk, jobs):
            for r in out: f.write(json.dumps(r) + "\n")
            f.flush(); rows += out
            print("walk done (%d rows, %.0fs)" % (len(rows), time.time() - t0), flush=True)
    for ctx in ("layer", "floatdead"):
        R = [r for r in rows if r["ctx"] == ctx]
        print("== %s: %d ladder calls, %.0f s total" % (ctx, len(R), sum(sum(r["ts"]) for r in R)))
        for k in (0, 1, 2, 3, -1, -2):
            S = [r for r in R if r["rung"] == k]
            if S: print("   %-10s %5d calls  %8.0f s  (mean %.1f s)" % ({-1: "FAIL", -2: "no system"}.get(k, "rung %d" % k), len(S), sum(sum(r["ts"]) for r in S), sum(sum(r["ts"]) for r in S) / len(S)))
