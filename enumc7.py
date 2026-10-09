"""OPTION 2 prover (2026-10-05): the label enumeration of one P1-opening branch with EXACT propagation
(xprop.py) -- no float arithmetic anywhere -- and a certificate for every claim, replayed by the
independent checker checkenum2.py (exact propagation certificates via xcheck.py, box certificates
via checkcert).

Every node record carries the node's FINAL labels ("lab"), its exact box ("box": [lo, hi] per
coordinate) and the certificate of that box ("psteps": how exact propagation narrows the parent's
box, with the split coordinate set by the node's label, to this one).  Kinds:
  split  "var", "children" (labels 0, 1, MIX), written before its children's records;
  pkill  a child exact propagation closes ("psteps" ends in a kill step, or ["X"] when the parent's
         box already excludes the label);
  kill   a layer test (every K_LAYER levels): a certbox certificate on the node's D-system starting
         from the node's exact box (KUHN_RUNGS_LAYER, default the full ladder);
  leaf   no unassigned coordinate left: a certleaf certificate.
The labels a box implies (lo >= 1 -> 1, hi <= 0 -> 0) are part of the node's labels; a coordinate
whose reach bound is 0 is marked DC ("dc", Lemma 2).

DURABILITY: enumc6's output (a chain of sealed gzip members, offset in enumc_<tag>.ckpt).  RESUME:
an unfinished node is a child of a split with no record; its state is one exact propagation away
from its parent's record (box and labels), recomputed and compared with nothing (it is new work).

usage:  KUHN_MODE=nash KUHN_ORDER=bet python enumc7.py <spec> <workers> <tag>
"""
import sys as _sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _f = open(_os.environ.get("KUHN_LOG", "log_enumc7.txt"), "a", buffering=1, encoding="utf-8", errors="replace")
    _sys.stdout = _sys.stderr = _f

import sys, os, time, json, gzip, re, zlib
from collections import deque
from multiprocessing import Pool
from fractions import Fraction as F
import xprop as X
import treesize6 as T6                     # ORDER only (the label order); no float propagation is used
from enumc6 import Out

U, MIX, DC = X.U, X.MIX, X.DC
ORDER = T6.ORDER
K_LAYER = 4
LADDER = ((1, False), (1, True), (20, False), (40, True))
RX = re.compile(r'^\{"id": (\d+), "kind": "(\w+)"')


def _rungs(name, default):
    v = os.environ.get(name, default).strip()
    return () if v.lower() == "none" else tuple(int(x) for x in v.split(",") if x.strip())


RUNGS_LAYER = _rungs("KUHN_RUNGS_LAYER", "0,1,2,3")


def fs(q): return str(q.numerator) if q.denominator == 1 else "%d/%d" % (q.numerator, q.denominator)
def boxstr(lo, hi): return [[fs(a), fs(b)] for a, b in zip(lo, hi)]
def boxparse(b): return [F(x[0]) for x in b], [F(x[1]) for x in b]


def kill_cert_box(lab, lo, hi, rungs):
    """certbox certificate that the node (labels, exact box) holds no D-everywhere profile, or None"""
    import enumx, certbox
    lab2 = [DC if v == U else v for v in lab]
    P, kinds, free, bounds, private = enumx.node_system(lab2)
    if not P: return None
    for i in private: lab2[i] = DC
    bounds = [[max(F(b[0]), lo[g]), min(F(b[1]), hi[g]), lab2[g] == MIX and lo[g] <= 0, lab2[g] == MIX and hi[g] >= 1]
              for g, b in zip(free, bounds)]
    if any(b[0] > b[1] for b in bounds): return None
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
    for k in rungs:
        budget, chord = LADDER[k]
        r = certbox.prove_empty_cert(P, kinds, None, bounds, budget, origins=origins, lab=lab2, gidx=gidx, chord=chord, exact_dual=False)
        if r[0]:
            c = r[1]; c["gens"] = gidx
            return {"lab": lab2, "cert": c}
    return None


def node_rec(nid, kind, st, **kw):
    lab, lo, hi, psteps = st[0], st[1], st[2], st[3]
    r = {"id": nid, "kind": kind, "lab": [int(v) for v in lab], "dc": [i for i in range(48) if lab[i] == DC],
         "box": boxstr(lo, hi), "psteps": psteps}
    r.update(kw)
    return r


STATS = {}


def subtree(a):
    """DFS below one node (local ids, 0 = this node), with a node budget and a time budget; the
    unfinished stack is handed back.  A state is (labels, lo, hi, psteps, depth)."""
    st0, budget, secs = a
    import certleaf
    t0 = time.time(); recs = []; nid = 0; done = 0
    cnt = {"split": 0, "pkill": 0, "kill": 0, "leaf": 0, "verd": {}, "layer_fail": 0, "t_prop": 0.0, "t_layer": 0.0, "t_leaf": 0.0}
    stack = [(0, st0)]
    while stack:
        if (budget and done >= budget) or (secs and done and time.time() - t0 > secs): break
        cur, st = stack.pop(); done += 1
        lab, lo, hi, psteps, depth = st
        if depth % K_LAYER == 0 and depth > 0 and RUNGS_LAYER:
            t1 = time.time(); kc = kill_cert_box(lab, lo, hi, RUNGS_LAYER); cnt["t_layer"] += time.time() - t1
            if kc is not None:
                recs.append(node_rec(cur, "kill", st, cert=kc["cert"], klab=kc["lab"])); cnt["kill"] += 1; continue
            cnt["layer_fail"] += 1
        u = [x for x in ORDER if lab[x] == U]
        if not u:
            t1 = time.time(); import numpy as np
            rc = certleaf.certify(np.array(lab, dtype=np.int8), 300); cnt["t_leaf"] += time.time() - t1
            rc["leaf"] = cur
            recs.append(node_rec(cur, "leaf", st, leafcert=rc)); cnt["leaf"] += 1
            cnt["verd"][rc["verdict"]] = cnt["verd"].get(rc["verdict"], 0) + 1
            continue
        v = u[0]; ids = [nid + 1, nid + 2, nid + 3]; nid += 3
        recs.append(node_rec(cur, "split", st, var=int(v), children=ids)); cnt["split"] += 1
        for cid, l in zip(ids, (0, 1, MIX)):
            steps = []; t1 = time.time()
            cl, clo, chi, cal, why = X.child(lab, lo, hi, v, l, steps=steps); cnt["t_prop"] += time.time() - t1
            if not cal:
                recs.append({"id": cid, "kind": "pkill", "psteps": steps}); cnt["pkill"] += 1
            else:
                stack.append((cid, (cl, clo, chi, steps, depth + 1)))
    cnt["maxid"] = nid
    return recs, cnt, stack


def scan(path):
    """complete records of an output -> header, seen, splits {id: (var, children)}, states of split
    nodes {id: (labels, box)}, counts, max id, tail"""
    seen = set(); splits = {}; sbox = {}; cnt = {}; maxid = 0; tail = "clean"; header = None
    f = gzip.open(path, "rt")
    try:
        line = f.readline()
        if not line.endswith("\n"): return None, seen, splits, sbox, cnt, 0, "no header"
        header = json.loads(line)
        for line in f:
            if not line.endswith("\n"): tail = "partial line dropped"; break
            m = RX.match(line)
            if not m: tail = "unparsable line: stopped there"; break
            i, k = int(m.group(1)), m.group(2)
            if i in seen: raise SystemExit("record for node %d twice in %s -- refusing to resume" % (i, path))
            if k == "split":
                r = json.loads(line); splits[i] = (r["var"], tuple(r["children"])); sbox[i] = (r["lab"], r["box"])
                maxid = max(maxid, *r["children"])
            seen.add(i); cnt[k] = cnt.get(k, 0) + 1; maxid = max(maxid, i)
    except (EOFError, OSError, zlib.error) as e:
        tail = "truncated stream (%s)" % type(e).__name__
    finally:
        f.close()
    return header, seen, splits, sbox, cnt, maxid, tail


def _reopen(a):
    """state of an unfinished child, from its parent's record"""
    cid, plab, pbox, v, l, depth = a
    lo, hi = boxparse(pbox)
    steps = []
    cl, clo, chi, cal, why = X.child(plab, lo, hi, v, l, steps=steps)
    return cid, (cl, clo, chi, steps, depth) if cal else None, steps


if __name__ == "__main__":
    spec, nw, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    t0 = time.time()
    OUTP, CK = "enumc_%s.jsonl.gz" % tag, "enumc_%s.ckpt" % tag
    CKEVERY = float(os.environ.get("KUHN_CKPT", "300"))
    budget = int(os.environ.get("KUHN_BUDGET", "40")); secs = float(os.environ.get("KUHN_JOBSECS", "120"))
    tot = {"split": 0, "pkill": 0, "kill": 0, "leaf": 0, "verd": {}, "layer_fail": 0, "t_prop": 0.0, "t_layer": 0.0, "t_leaf": 0.0}
    pending = deque(); out = None
    if os.path.exists(OUTP):
        if not os.path.exists(CK): raise SystemExit("%s exists without %s -- refusing to touch it" % (OUTP, CK))
        ck = json.load(open(CK))
        if ck.get("complete"):
            print("%s: already complete (%s) -> %s" % (spec, CK, OUTP), flush=True); sys.exit(0)
        with open(OUTP, "r+b") as f: f.truncate(ck["offset"])
        header, seen, splits, sbox, cnt, maxid, tail = scan(OUTP)
        if header is None or header.get("spec") != spec or header.get("order") != list(ORDER) or header.get("method") != "enumc7":
            raise SystemExit("%s does not belong to %s / enumc7 -- refusing to touch it" % (OUTP, spec))
        if 0 not in seen:
            print("%s: no root record -- starting afresh" % spec, flush=True); os.remove(OUTP); os.remove(CK)
        else:
            depth = {0: 0}
            for i in sorted(splits):                        # ids grow down the tree within a job; depth via parents
                for c in splits[i][1]: depth[c] = depth.get(i, 0) + 1
            todo = [(c, sbox[i][0], sbox[i][1], splits[i][0], l, depth[c]) for i in splits
                    for c, l in zip(splits[i][1], (0, 1, MIX)) if c not in seen]
            nxt = maxid + 1
            for k_, v_ in cnt.items(): tot[k_] = v_
            out = Out(OUTP, CK, ck["offset"])
            t1 = time.time()
            with Pool(nw) as pool:
                for cid, st, steps in pool.imap_unordered(_reopen, todo, chunksize=4):
                    if st is None: out.write({"id": cid, "kind": "pkill", "psteps": steps}); tot["pkill"] += 1
                    else: pending.append((cid, st))
            print("%s: RESUMED from %s: %d records %s, tail %s; %d unfinished nodes re-derived in %.0fs" % (
                spec, OUTP, len(seen), cnt, tail, len(todo), time.time() - t1), flush=True)
    if out is None:                                         # a fresh run
        lab0, lo0, hi0 = X.spec_state(spec)
        out = Out(OUTP, CK, 0)
        out.write({"id": 0, "parent": -1, "lab": [int(v) for v in lab0], "spec": spec, "order": ORDER, "method": "enumc7"})
        steps = []
        lab, lo, hi, al = X.propagate(lab0, lo0, hi0, steps=steps)
        if not al:
            out.write({"id": 0, "kind": "pkill", "psteps": steps}); out.close(complete=True)
            print("%s: dead at the root (exact propagation)" % spec, flush=True); sys.exit(0)
        pending.append((0, (lab, lo, hi, steps, 0))); nxt = 1
        out.checkpoint()
    print("   layer rungs %s  job budget %d nodes / %.0f s  checkpoint every %.0fs" % (RUNGS_LAYER, budget, secs, CKEVERY), flush=True)
    active = []; done = 0; handed = 0; lastp = lastck = time.time()
    with Pool(nw) as pool:
        while pending or active:
            while pending and len(active) < 2 * nw:
                cur, st = pending.popleft()
                active.append((cur, pool.apply_async(subtree, ((st, budget, secs),))))
            fin = [(cur, r) for cur, r in active if r.ready()]
            if not fin:
                time.sleep(0.1); continue
            for cur, r in fin:
                active.remove((cur, r))
                recs, cnt, left = r.get()
                base = nxt; nxt += cnt["maxid"] + 1
                for rec in recs:
                    rec["id"] = cur if rec["id"] == 0 else rec["id"] + base
                    if rec["kind"] == "split": rec["children"] = [c + base for c in rec["children"]]
                    if rec["kind"] == "leaf": rec["leafcert"]["leaf"] = rec["id"]
                    out.write(rec)
                for c, st in left:
                    pending.append((cur if c == 0 else c + base, st)); handed += 1
                for k_ in ("split", "pkill", "kill", "leaf", "layer_fail", "t_prop", "t_layer", "t_leaf"): tot[k_] += cnt[k_]
                for k_, v_ in cnt["verd"].items(): tot["verd"][k_] = tot["verd"].get(k_, 0) + v_
                done += 1
            if time.time() - lastck > CKEVERY:
                out.checkpoint(); lastck = time.time()
            if time.time() - lastp > 60 or (not pending and not active):
                lastp = time.time()
                print("   jobs %d done (%d queued, %d running, %d handed back)  split %d pkill %d kill %d leaf %d %s  layer-fail %d  "
                      "prop %.0fs layer %.0fs leaf %.0fs  %.0fs" % (done, len(pending), len(active), handed, tot["split"], tot["pkill"], tot["kill"],
                      tot["leaf"], tot["verd"], tot["layer_fail"], tot["t_prop"], tot["t_layer"], tot["t_leaf"], time.time() - t0), flush=True)
    out.close(complete=True)
    print("%s: split %d pkill %d kill %d leaf %d %s   %.0fs  -> %s" % (spec, tot["split"], tot["pkill"], tot["kill"], tot["leaf"], tot["verd"],
          time.time() - t0, OUTP), flush=True)
