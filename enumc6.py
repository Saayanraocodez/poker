"""RESUMABLE enumc5 (2026-09-30).  Same workers (enumc5.subtree / kill_cert, same rungs, same
record format, verified by checkenum.py); only the driver changes, so that no amount of work is
lost to a cap, a kill or a power cut.

DURABILITY.  The output enumc_<tag>.jsonl.gz is a chain of COMPLETE gzip members.  Every
KUHN_CKPT seconds (default 300) the driver closes the current member, fsyncs the file, and only
then records the byte offset atomically in enumc_<tag>.ckpt.  After a crash the file can only
be AHEAD of the checkpoint, never behind, and a resume truncates the excess -- the ordering
bnb5's checkpoints use.  Only whole jobs' records are ever written, but correctness does not
depend on it: any prefix of the record stream is a consistent partial tree (a split record
always precedes its children's records).

RESUME.  If the output exists, the run resumes from it: the unfinished nodes are exactly the
children of split records that have no record of their own.  Their states (labels with DC
marks, float box, "below an uncertifiable node") are recomputed by replaying the deterministic
float propagation from the root along the ancestor splits -- only the ancestors of unfinished
nodes -- and every replayed node is checked against its stored split record (the split variable
must be the node's first unassigned coordinate, and its DC set must match).  New ids start above
the largest id in the file.  A file without a .ckpt (a crash before the first checkpoint, or an
enumc2/enumc5 output) is migrated: its complete records are rewritten as one sealed member.
Resumed jobs count depth from the root, which only moves where the (optional) layer tests fall.

usage:  [KUHN_MODE=nash] KUHN_ORDER=bet python enumc6.py <spec> <workers> <tag>
"""
import sys as _sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _f = open(_os.environ.get("KUHN_LOG", "log_enumc6.txt"), "a", buffering=1, encoding="utf-8", errors="replace")
    _sys.stdout = _sys.stderr = _f

import numpy as np, sys, time, os, json, gzip, re, zlib
from multiprocessing import Pool
from collections import deque
import treesize6 as T6
from enumc5 import subtree, _kill_cert_top, kill_cert, RUNGS, U, MIX, DC, ORDER

RX = re.compile(r'^\{"id": (\d+), "kind": "(\w+)"')


class Out:
    """append-only output as a chain of complete gzip members, with durable checkpoints."""

    def __init__(self, path, ck, offset):
        self.path, self.ck = path, ck
        self.raw = open(path, "r+b" if os.path.exists(path) else "w+b")
        self.raw.truncate(offset); self.raw.seek(offset)
        self.gz = gzip.GzipFile(fileobj=self.raw, mode="wb", compresslevel=6)

    def write(self, rec):
        self.gz.write((rec if isinstance(rec, str) else json.dumps(rec) + "\n").encode())

    def _seal(self, info):
        self.gz.close(); self.raw.flush(); os.fsync(self.raw.fileno())          # data first ...
        info = dict(info); info["offset"] = self.raw.tell(); info["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.ck + ".tmp", "w") as f:
            json.dump(info, f); f.flush(); os.fsync(f.fileno())
        os.replace(self.ck + ".tmp", self.ck)                                   # ... then the offset

    def checkpoint(self, **info):
        self._seal(info)
        self.gz = gzip.GzipFile(fileobj=self.raw, mode="wb", compresslevel=6)

    def close(self, **info):
        self._seal(info); self.raw.close()


def scan(path, copy_to=None):
    """complete records of an output (a truncated tail is tolerated) ->
    header, seen ids, splits {id: (var, children, dc)}, counts, max id.  copy_to: an Out that
    receives the header and every complete record verbatim (migration)."""
    seen = set(); splits = {}; cnt = {"kill": 0, "split": 0, "leaf": 0, "verd": {}}; maxid = 0; tail = "clean"
    f = gzip.open(path, "rt")
    try:
        line = f.readline()
        if not line.endswith("\n"): return None, seen, splits, cnt, 0, "no header"
        header = json.loads(line)
        if copy_to: copy_to.write(line)
        for line in f:
            if not line.endswith("\n"): tail = "partial line dropped"; break
            m = RX.match(line)
            if not m: tail = "unparsable line: stopped there"; break
            i, k = int(m.group(1)), m.group(2)
            if k == "split":
                r = json.loads(line); splits[i] = (r["var"], tuple(r["children"]), tuple(r["dc"]))
                maxid = max(maxid, *r["children"])
            elif k == "leaf":
                v = json.loads(line)["leafcert"]["verdict"]; cnt["verd"][v] = cnt["verd"].get(v, 0) + 1
            if i in seen: raise SystemExit("record for node %d twice in %s -- refusing to resume" % (i, path))
            seen.add(i); cnt[k] = cnt.get(k, 0) + 1; maxid = max(maxid, i)
            if copy_to: copy_to.write(line)
    except (EOFError, OSError, zlib.error) as e:
        tail = "truncated stream (%s)" % type(e).__name__
    finally:
        f.close()
    return header, seen, splits, cnt, maxid, tail


def _step(x, st, info):
    """replay one split: node x in state st, info = (var, children, dc, child status 'o'pen/'n'eed/'d'one)
    -> [(child id, child state, status)].  Refuses when the replay disagrees with the stored record."""
    lab, LO, HI, under, d = st
    var, ch, dc, status = info
    u = [i for i in ORDER if lab[i] == U]
    if not u or u[0] != var or sorted(int(i) for i in range(48) if lab[i] == DC) != sorted(dc):
        raise RuntimeError("replay disagrees with the split record of node %d -- refusing to resume" % x)
    kids = []
    for l in (0, 1, MIX):
        l2 = lab.copy(); a2 = LO.copy(); b2 = HI.copy(); l2[var] = l
        if l == 0: b2[var] = 0.0
        elif l == 1: a2[var] = 1.0
        kids.append((l2, a2, b2))
    allowed = [LO[var] <= 0.0, HI[var] >= 1.0, HI[var] > 0.0 and LO[var] < 1.0]
    L2, A2, B2, al2 = T6.propagate(np.array([q[0] for q in kids]), np.array([q[1] for q in kids]), np.array([q[2] for q in kids]), T6.WEAK)
    res = []
    for t in range(3):
        if allowed[t] and al2[t]:
            lc = kids[t][0].copy(); lc[(lc == U) & (L2[t] == DC)] = DC
            cs = (lc, A2[t], B2[t], under, d + 1)
        else:
            cs = (kids[t][0], kids[t][1], kids[t][2], True, d + 1)         # kept after a failed kill ladder
        res.append((ch[t], cs, status[t]))
    return res


_INFO = None


def _replay_init(info):
    global _INFO
    _INFO = info


def _replay_task(a):
    """replay below the given nodes for at most `budget` steps (a worker task; the ancestor tree is
    very unbalanced, so work is shared like the enumeration's) -> (unfinished nodes, stack left)"""
    stack, budget = a
    out = []; steps = 0
    while stack and steps < budget:
        x, st = stack.pop(); steps += 1
        for c, cs, s in _step(x, st, _INFO[x]):
            if s == "o": out.append((c, cs))
            elif s == "n": stack.append((c, cs))
    return out, stack


def replay(spec, seen, splits, nw):
    """states of the unfinished nodes, by replaying the float propagation down their ancestors:
    serially from the root to ~3*nw subtree roots, then the subtrees in a pool."""
    parent = {c: i for i, (v, ch, dc) in splits.items() for c in ch}
    openset = [c for i, (v, ch, dc) in splits.items() for c in ch if c not in seen]
    need = set()
    for c in openset:
        p = parent[c]
        while p not in need:
            need.add(p)
            if p == 0: break
            p = parent[p]
    info = {x: (splits[x][0], splits[x][1], splits[x][2],
                tuple("o" if c not in seen else "n" if c in need else "d" for c in splits[x][1])) for x in need}
    root_lab, LO, HI = T6.root_of(spec)
    labp, A, B, al = T6.propagate(root_lab[None], LO[None], HI[None], T6.WEAK)
    lab = root_lab.copy(); lab[(lab == U) & (labp[0] == DC)] = DC
    out = []; front = deque([(0, (lab, A[0], B[0], False, 0))] if 0 in need else [])
    while front and len(front) < 3 * nw:                                  # serial top of the ancestor tree
        x, st = front.popleft()
        for c, cs, s in _step(x, st, info[x]):
            if s == "o": out.append((c, cs))
            elif s == "n": front.append((c, cs))
    if front:
        pend = deque([[item] for item in front]); active = []
        with Pool(nw, initializer=_replay_init, initargs=(info,)) as pool:
            while pend or active:
                while pend and len(active) < 2 * nw:
                    active.append(pool.apply_async(_replay_task, ((pend.popleft(), 40),)))
                fin = [r for r in active if r.ready()]
                if not fin: time.sleep(0.05); continue
                for r in fin:
                    active.remove(r); part, left = r.get()
                    out.extend(part)
                    pend.extend([item] for item in left)                   # hand the rest back out
    return [(c,) + cs for c, cs in out], len(need)


def top_expansion(spec, lab, LO, HI, nw, weak, out):
    """enumc5's float top expansion to ~KUHN_FRONTIER*nw subtrees -> (frontier, und, next id)."""
    frontier = [(0, lab, LO, HI)]; nxt = 1; records = []; complete = []; und = {0: False}
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
                cid = nxt; nxt += 1; ids.append(cid); und[cid] = und[cur]
                if allowed[t] and al2[t]:
                    lc = kids[t][0].copy(); lc[(lc == U) & (L2[t] == DC)] = DC
                    nf.append((cid, lc, A2[t], B2[t]))
                else: nf.append((cid, kids[t][0], kids[t][1], kids[t][2], "check"))
            records.append({"id": cur, "kind": "split", "dc": [int(i) for i in range(48) if l[i] == DC], "var": int(v), "children": ids})
        frontier = [x[:4] for x in nf if len(x) == 4]; unsure = [x[:4] for x in nf if len(x) == 5]
        if unsure:
            with Pool(min(nw, len(unsure))) as pool:
                for (cid, l, a, b), kc in zip(unsure, pool.map(_kill_cert_top, [x[1] for x in unsure], chunksize=1)):
                    if kc is not None: records.append({"id": cid, "kind": "kill", "dc": [], "lab": kc["lab"], "cert": kc["cert"]})
                    else: frontier.append((cid, l, a, b)); und[cid] = True
    for r in records: out.write(r)
    return [(cur, l, a, b, 0, und.get(cur, False)) for cur, l, a, b in frontier + complete], nxt


if __name__ == "__main__":
    spec, nw, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    weak = T6.WEAK; t0 = time.time()
    OUTP, CK = "enumc_%s.jsonl.gz" % tag, "enumc_%s.ckpt" % tag
    CKEVERY = float(os.environ.get("KUHN_CKPT", "300"))
    tot = {"kill": 0, "split": 0, "leaf": 0, "float_unsure": 0, "verd": {}, "stats": {}}
    pending = None
    if not os.path.exists(OUTP) and os.path.exists(OUTP + ".premigrate"):
        os.replace(OUTP + ".premigrate", OUTP)                           # a migration was cut off: redo it
        print("restored %s from an interrupted migration" % OUTP, flush=True)
    if os.path.exists(OUTP):
        ck = json.load(open(CK)) if os.path.exists(CK) else None
        if ck is not None:
            if ck.get("complete"):
                print("%s: already complete (%s) -> %s" % (spec, CK, OUTP), flush=True); sys.exit(0)
            with open(OUTP, "r+b") as f: f.truncate(ck["offset"])        # past the checkpoint: an unsealed member
            header, seen, splits, cnt, maxid, tail = scan(OUTP)
            out = None
        else:                                                            # migrate: rewrite complete records, sealed
            if os.path.exists(OUTP + ".new"): os.remove(OUTP + ".new")
            tmp = Out(OUTP + ".new", CK + ".new", 0)
            header, seen, splits, cnt, maxid, tail = scan(OUTP, copy_to=tmp)
            tmp.close(migrated_from=OUTP)
            os.replace(OUTP, OUTP + ".premigrate"); os.replace(OUTP + ".new", OUTP); os.replace(CK + ".new", CK)
            ck = json.load(open(CK)); out = None
            print("migrated %s (%d records, tail: %s); original kept as %s.premigrate" % (OUTP, len(seen), tail, OUTP), flush=True)
        if header is not None and (header.get("spec") != spec or header.get("order") != list(ORDER)):
            raise SystemExit("%s does not belong to %s with this order -- refusing to touch it" % (OUTP, spec))
        if header is not None and splits:
            t1 = time.time()
            try:
                opens, nneed = replay(spec, seen, splits, nw)
            except RuntimeError as ex:
                raise SystemExit(str(ex))
            pending = deque((c, l, a, b, d, un) for c, l, a, b, un, d in opens)
            nxt = maxid + 1
            for k_ in ("kill", "split", "leaf"): tot[k_] = cnt.get(k_, 0)
            tot["verd"] = cnt["verd"]
            out = Out(OUTP, CK, ck["offset"])
            print("%s: RESUMED from %s: %d records (kill %d split %d leaf %d), tail %s; %d unfinished nodes, "
                  "%d ancestor splits replayed and matched in %.0fs" % (spec, OUTP, len(seen), cnt.get("kill", 0), cnt.get("split", 0),
                  cnt.get("leaf", 0), tail, len(pending), nneed, time.time() - t1), flush=True)
        else:
            print("%s: %s has %s -- starting afresh" % (spec, OUTP, "no split records" if header else "no complete header (cut off before the first checkpoint)"), flush=True)
            os.remove(OUTP)
            if os.path.exists(CK): os.remove(CK)
    if pending is None:                                                  # a fresh run
        root_lab, LO, HI = T6.root_of(spec)
        labp, LO, HI, al = T6.propagate(root_lab[None], LO[None], HI[None], weak)
        labp, LO, HI = labp[0], LO[0], HI[0]
        lab = root_lab.copy(); lab[(lab == U) & (labp == DC)] = DC
        out = Out(OUTP, CK, 0)
        out.write({"id": 0, "parent": -1, "lab": [int(v) for v in root_lab], "spec": spec, "order": ORDER})
        if not al[0]:
            kc = kill_cert(root_lab)
            if kc is None: print("root float-dead but not certifiable at the root; falling through", flush=True)
            else:
                out.write({"id": 0, "kind": "kill", "dc": [], "lab": kc["lab"], "cert": kc["cert"]}); out.close(complete=True)
                print("%s: dead at the root (certified)" % spec); sys.exit(0)
        jobs, nxt = top_expansion(spec, lab, LO, HI, nw, weak, out)
        pending = deque(jobs)
        out.checkpoint()
        print("%s: top expansion -> %d subtrees, %.0fs" % (spec, len(pending), time.time() - t0), flush=True)
    budget = int(os.environ.get("KUHN_BUDGET", "300"))
    print("   rungs %s  job budget %s nodes / %s s  checkpoint every %.0fs" % (RUNGS, budget, os.environ.get("KUHN_JOBSECS", "-"), CKEVERY), flush=True)
    active = []; done = 0; handed = 0; lastp = lastck = time.time()
    with Pool(nw) as pool:
        while pending or active:
            while pending and len(active) < 2 * nw:
                cur, l, a, b, d, un = pending.popleft()
                active.append((cur, pool.apply_async(subtree, ((l, a, b, weak, d, budget, un),))))
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
                    out.write(rec)
                for c, l, a, b, d, un in left:
                    pending.append((cur if c == 0 else c + base, np.array(l), np.array(a), np.array(b), d, un)); handed += 1
                for k_ in ("kill", "split", "leaf", "float_unsure"): tot[k_] += counts[k_]
                for k_, v_ in counts["verd"].items(): tot["verd"][k_] = tot["verd"].get(k_, 0) + v_
                for k_, v_ in counts["stats"].items():
                    s_ = tot["stats"].setdefault(k_, [0, 0.0, 0, 0.0])
                    for j_ in range(4): s_[j_] += v_[j_]
                done += 1
            if time.time() - lastck > CKEVERY:
                out.checkpoint(); lastck = time.time()
            if time.time() - lastp > 60 or (not pending and not active):
                lastp = time.time()
                print("   jobs %d done (%d queued, %d running, %d handed back)  kill %d split %d leaf %d %s  float-unsure %d  %.0fs  | %s" % (done, len(pending), len(active), handed, tot["kill"], tot["split"], tot["leaf"], tot["verd"], tot["float_unsure"], time.time() - t0,
                      "  ".join("%s %d calls %d fail %.0fs (%.0fs in fails)" % (k_, v_[0], v_[2], v_[1], v_[3]) for k_, v_ in sorted(tot["stats"].items()))), flush=True)
    out.close(complete=True)
    print("%s: kill %d split %d leaf %d %s  float-unsure %d   %.0fs  -> enumc_%s.jsonl.gz" % (spec, tot["kill"], tot["split"], tot["leaf"], tot["verd"], tot["float_unsure"], time.time() - t0, tag), flush=True)
