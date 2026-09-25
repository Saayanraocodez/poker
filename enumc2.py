"""FLOAT-GUIDED CERTIFIED enumeration of one P1-opening branch (third pass).

The label tree is the one enuml.py explores -- the float propagation
(treesize6.propagate under ivl's outward rounding) decides WHICH nodes to
try to kill and where to mark don't-care coordinates -- but every claim in
the tree is certified exactly:

  * a node the float propagation kills, and every child label it excludes
    (LO > 0 rules out 0, HI < 1 rules out 1, a collapsed box rules out MIX),
    gets a certbox certificate on the node's D-system (contraction, LP,
    exact tree rules, chord contractor, LP, at budget 1 then 60); if no
    certificate is found the node is kept alive and split instead (so the
    float verdict is never trusted);
  * every fourth level the exact node test of enuml (enumx.node_test) runs
    with a certificate;
  * a DC label (float reach bound 0, or private) needs no justification
    (Lemma 2: the DC pair covers every label);
  * a leaf (no U) is decided by certleaf with a certificate.

Output: enumc_<tag>.jsonl.gz in enumc.py's format, verified by checkenum.py.
usage:  [KUHN_MODE=nash] KUHN_ORDER=bet python enumc2.py <spec> <workers> <tag>
"""
import sys as _sys, os as _os
# Launched by pythonw.exe there is NO console and sys.stdout is None -- give the
# run a log file of its own.  Windowless on purpose: a `cmd /c ... > log` launcher
# opens a console window, and closing that window sends CTRL_CLOSE/CTRL_C to
# everything attached to it, which is what killed these runs on 2026-09-22.
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _f = open(_os.environ.get("KUHN_LOG", "log_%s.txt" % _os.path.splitext(_os.path.basename(__file__))[0]), "a", buffering=1, encoding="utf-8", errors="replace")
    _sys.stdout = _sys.stderr = _f

import numpy as np, sys, time, os, json, gzip
from multiprocessing import Pool
from fractions import Fraction as F
import treesize6 as T6, kuhn3p as K, certbox, certleaf, enumx, enumc

U, MIX, DC = T6.U, T6.MIX, T6.DC
ORDER = T6.ORDER
K_LAYER = 4


def kill_cert(lab):
    """certificate that the node (labels with U) has no D-everywhere profile, or None"""
    lab = [int(v) for v in lab]
    lab2 = [DC if v == U else v for v in lab]
    P, kinds, free, bounds, private = enumx.node_system(lab2)
    if not P: return None
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
    gidx = list(free)
    for budget, chord in ((1, False), (1, True), (20, False), (40, True)):     # LP-only B&B before the 2 s/node chord B&B
        r = certbox.prove_empty_cert(P, kinds, None, bounds, budget, origins=origins, lab=lab2, gidx=gidx, chord=chord, exact_dual=False)
        if r[0]:
            c = r[1]; c["gens"] = gidx
            return {"lab": lab2, "cert": c}
    return None


def subtree(a):
    """DFS below one float node with certificates, with a node BUDGET: when it
    runs out the unfinished stack is handed back to the driver and re-queued
    (enuml's work sharing -- without it 12 deep subtrees pinned 12 workers for
    an hour).  -> (local records, counters, leftovers); ids local, 0 = this
    subtree's root; leftovers = [(local id, lab, LO, HI, depth)]."""
    lab0, LO0, HI0, weak, depth0, budget = a
    recs = []; nid = 0; processed = 0
    stack = [(0, lab0, LO0, HI0, depth0)]           # (id, lab, LO, HI, depth)
    counts = {"kill": 0, "split": 0, "leaf": 0, "float_unsure": 0, "verd": {}}
    while stack:
        if budget and processed >= budget: break
        cur, lab, LO, HI, depth = stack.pop(); processed += 1
        lab = np.array(lab); LO = np.array(LO); HI = np.array(HI)
        # exact test every K_LAYER levels (with certificate)
        if depth % K_LAYER == 0 and depth > 0:
            kc = kill_cert(lab)
            if kc is not None:
                recs.append({"id": cur, "kind": "kill", "dc": [], "lab": kc["lab"], "cert": kc["cert"]}); counts["kill"] += 1; continue
        u = [x for x in ORDER if lab[x] == U]
        if not u:
            rec = certleaf.certify(lab.astype(np.int8), 300); rec["leaf"] = cur
            recs.append({"id": cur, "kind": "leaf", "dc": [], "lab": [int(v) for v in lab], "leafcert": rec})
            counts["leaf"] += 1; counts["verd"][rec["verdict"]] = counts["verd"].get(rec["verdict"], 0) + 1; continue
        v = u[0]
        kids = {}
        for l in (0, 1, MIX):
            l2 = lab.copy(); a2 = LO.copy(); b2 = HI.copy(); l2[v] = l
            if l == 0: b2[v] = 0.0
            elif l == 1: a2[v] = 1.0
            kids[l] = (l2, a2, b2)
        Lk = np.array([kids[l][0] for l in (0, 1, MIX)]); Ak = np.array([kids[l][1] for l in (0, 1, MIX)]); Bk = np.array([kids[l][2] for l in (0, 1, MIX)])
        # float verdicts (a heuristic only): excluded labels, dead children, DC marks
        allowed = {0: LO[v] <= 0.0, 1: HI[v] >= 1.0, MIX: HI[v] > 0.0 and LO[v] < 1.0}
        L2, A2, B2, al2 = T6.propagate(Lk, Ak, Bk, weak)
        ids = [nid + 1, nid + 2, nid + 3]; nid += 3
        # the split record goes out BEFORE its children's records (the checker reads in order)
        recs.append({"id": cur, "kind": "split", "dc": [int(i) for i in range(48) if lab[i] == DC], "var": int(v), "children": ids}); counts["split"] += 1
        for t, l in enumerate((0, 1, MIX)):
            cid = ids[t]
            if allowed[l] and al2[t]:
                # alive child: keep the parent's labels + the split (a float-implied 0/1 is only a
                # hint; the box keeps it) and take the float DC marks (Lemma 2: free)
                lc = kids[l][0].copy(); lc[(lc == U) & (L2[t] == DC)] = DC
                stack.append((cid, lc, A2[t], B2[t], depth + 1)); continue
            kc = kill_cert(kids[l][0])
            if kc is not None:
                recs.append({"id": cid, "kind": "kill", "dc": [], "lab": kc["lab"], "cert": kc["cert"]}); counts["kill"] += 1
            else:
                counts["float_unsure"] += 1
                stack.append((cid, kids[l][0], kids[l][1], kids[l][2], depth + 1))
    counts["maxid"] = nid
    return recs, counts, [(c, list(int(v) for v in l), list(map(float, a_)), list(map(float, b_)), d) for c, l, a_, b_, d in stack]


def _relabel(recs, base):
    out = []
    for r in recs:
        r = dict(r); r["id"] = r["id"] + base
        if r["kind"] == "split": r["children"] = [c + base for c in r["children"]]
        out.append(r)
    return out


if __name__ == "__main__":
    spec, nw, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    weak = T6.WEAK; t0 = time.time()
    root_lab, LO, HI = T6.root_of(spec)
    labp, LO, HI, al = T6.propagate(root_lab[None], LO[None], HI[None], weak)
    labp, LO, HI = labp[0], LO[0], HI[0]
    lab = root_lab.copy(); lab[(lab == U) & (labp == DC)] = DC     # float-implied 0/1 labels are hints only
    out = gzip.open("enumc_%s.jsonl.gz" % tag, "wt")
    out.write(json.dumps({"id": 0, "parent": -1, "lab": [int(v) for v in root_lab], "spec": spec, "order": ORDER}) + "\n")
    if not al[0]:
        kc = kill_cert(root_lab)
        if kc is None: print("root float-dead but not certifiable at the root; falling through", flush=True)
        else:
            out.write(json.dumps({"id": 0, "kind": "kill", "dc": [], "lab": kc["lab"], "cert": kc["cert"]}) + "\n"); out.close()
            print("%s: dead at the root (certified)" % spec); sys.exit(0)
    # top expansion (float) to ~KUHN_FRONTIER*nw subtrees, recording the splits (DC marks from propagate)
    frontier = [(0, lab, LO, HI)]; nxt = 1; records = []; complete = []
    target = int(os.environ.get("KUHN_FRONTIER", "60")) * nw
    while 0 < len(frontier) < target:
        nf = []
        for cur, l, a, b in frontier:
            u = [x for x in ORDER if l[x] == U]
            if not u: complete.append((cur, l, a, b)); continue
            v = u[0]; kids = []
            for lb in (0, 1, MIX):
                l2 = l.copy(); a2 = a.copy(); b2 = b.copy(); l2[v] = lb
                if lb == 0: b2[v] = 0.0
                elif lb == 1: a2[v] = 1.0
                kids.append((l2, a2, b2))
            Lk = np.array([q[0] for q in kids]); Ak = np.array([q[1] for q in kids]); Bk = np.array([q[2] for q in kids])
            allowed = [a[v] <= 0.0, b[v] >= 1.0, b[v] > 0.0 and a[v] < 1.0]
            L2, A2, B2, al2 = T6.propagate(Lk, Ak, Bk, weak)
            ids = []
            for t in range(3):
                cid = nxt; nxt += 1; ids.append(cid)
                if allowed[t] and al2[t]:
                    lc = kids[t][0].copy(); lc[(lc == U) & (L2[t] == DC)] = DC
                    nf.append((cid, lc, A2[t], B2[t]))
                else: nf.append((cid, kids[t][0], kids[t][1], kids[t][2], "check"))
            records.append({"id": cur, "kind": "split", "dc": [int(i) for i in range(48) if l[i] == DC], "var": int(v), "children": ids})
        # float-dead / excluded children of this level: certify (in the pool) or keep
        frontier = [x[:4] for x in nf if len(x) == 4]; unsure = [x[:4] for x in nf if len(x) == 5]
        if unsure:
            with Pool(min(nw, len(unsure))) as pool:
                for (cid, l, a, b), kc in zip(unsure, pool.map(kill_cert, [x[1] for x in unsure], chunksize=1)):
                    if kc is not None: records.append({"id": cid, "kind": "kill", "dc": [], "lab": kc["lab"], "cert": kc["cert"]})
                    else: frontier.append((cid, l, a, b))
    for r in records: out.write(json.dumps(r) + "\n")
    records = []
    print("%s: top expansion -> %d subtrees, %d complete leaves, %.0fs" % (spec, len(frontier), len(complete), time.time() - t0), flush=True)
    tot = {"kill": 0, "split": 0, "leaf": 0, "float_unsure": 0, "verd": {}}
    budget = int(os.environ.get("KUHN_BUDGET", "300"))
    from collections import deque
    pending = deque((cur, l, a, b, 0) for cur, l, a, b in frontier + complete)
    active = []; done = 0; handed = 0; lastp = time.time()
    with Pool(nw) as pool:
        while pending or active:
            while pending and len(active) < 2 * nw:
                cur, l, a, b, d = pending.popleft()
                active.append((cur, pool.apply_async(subtree, ((l, a, b, weak, d, budget),))))
            fin = [(cur, r) for cur, r in active if r.ready()]
            if not fin:
                time.sleep(0.2); continue
            for cur, r in fin:
                active.remove((cur, r))
                recs, counts, left = r.get()
                base = nxt; nxt += counts["maxid"] + 1
                for rec in recs:
                    rec = dict(rec)
                    rec["id"] = cur if rec["id"] == 0 else rec["id"] + base
                    if rec["kind"] == "split": rec["children"] = [c + base for c in rec["children"]]
                    if rec["kind"] == "leaf": rec["leafcert"]["leaf"] = rec["id"]
                    out.write(json.dumps(rec) + "\n")
                for c, l, a, b, d in left:
                    pending.append((cur if c == 0 else c + base, np.array(l), np.array(a), np.array(b), d)); handed += 1
                for k_ in ("kill", "split", "leaf", "float_unsure"): tot[k_] += counts[k_]
                for k_, v_ in counts["verd"].items(): tot["verd"][k_] = tot["verd"].get(k_, 0) + v_
                done += 1
            if time.time() - lastp > 60 or (not pending and not active):
                lastp = time.time()
                print("   jobs %d done (%d queued, %d running, %d handed back)  kill %d split %d leaf %d %s  float-unsure %d  %.0fs" % (done, len(pending), len(active), handed, tot["kill"], tot["split"], tot["leaf"], tot["verd"], tot["float_unsure"], time.time() - t0), flush=True)
    out.close()
    print("%s: kill %d split %d leaf %d %s  float-unsure %d   %.0fs  -> enumc_%s.jsonl.gz" % (spec, tot["kill"], tot["split"], tot["leaf"], tot["verd"], tot["float_unsure"], time.time() - t0, tag), flush=True)
