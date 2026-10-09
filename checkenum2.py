"""Independent checker for an enumc7 tree (option 2, 2026-10-05): exact propagation, no float.

Every node is checked on its own, from its PARENT's record, so the checks run in parallel; the
chain of verified links makes every recorded box sound by induction down the tree:
  * the node's state before propagation: its parent's labels and box with the split coordinate set
    by the node's label (the root: the branch spec);
  * "psteps": the propagation certificate, replayed by xcheck.replay (an independent exact
    implementation), must end in a kill for a 'pkill' node (or be ["X"], a label the parent's box
    excludes), and must end alive with a box CONTAINED in the recorded box otherwise;
  * the node's labels must be exactly: the pre-propagation labels, the labels the recorded box
    implies (lo >= 1 -> 1, hi <= 0 -> 0), and DC marks ("dc", unassigned coordinates only; Lemma 2);
  * split: the variable is unassigned; its three children (labels 0, 1, MIX) must all appear;
  * kill: a box certificate (checkcert.check_box_cert) for a system whose labels agree with the
    node's on 0/1/MIX and are DC elsewhere, starting from a box that CONTAINS the node's recorded box;
  * leaf: no unassigned coordinate; a leaf certificate (checkcert.check_leaf).
Coverage: every child of every split has exactly one record.

usage:  python checkenum2.py enumc_<tag>.jsonl.gz [workers]
"""
import sys, os, json, gzip, time
from fractions import Fraction as F
import checkcert as C, xcheck as XC

U, MIX, DC = 9, 2, 3


def _pre(ctx):
    """labels and box of a node before its own propagation"""
    if ctx[0] == "root":
        return list(ctx[1]), list(ctx[2]), list(ctx[3])
    _, plab, plo, phi, v, l = ctx
    lab = list(plab); lab[v] = l; lo = list(plo); hi = list(phi)
    if l == 0: hi[v] = F(0)
    elif l == 1: lo[v] = F(1)
    return lab, lo, hi


def _check(a):
    nid, ctx, r = a
    kind = r["kind"]
    try:
        lab0, lo0, hi0 = _pre(ctx)
        ps = r["psteps"]
        if kind == "pkill":
            if ps == [["X"]]:
                C.need(ctx[0] != "root", "the root cannot be excluded by a parent")
                C.need(XC.excluded(ctx[2], ctx[3], ctx[4], ctx[5]), "label not excluded by the parent's box")
            else:
                _, _, al = XC.replay(lab0, lo0, hi0, ps)
                C.need(not al, "propagation certificate does not close the node")
            return nid, "pkill", None, None
        if ctx[0] != "root":
            C.need(not XC.excluded(ctx[2], ctx[3], ctx[4], ctx[5]), "an excluded label carries a live node")
        rlo, rhi, al = XC.replay(lab0, lo0, hi0, ps)
        C.need(al, "propagation certificate closes a node recorded as live")
        blo = [F(x[0]) for x in r["box"]]; bhi = [F(x[1]) for x in r["box"]]
        C.need(all(blo[i] <= rlo[i] and rhi[i] <= bhi[i] for i in range(48)), "recorded box tighter than the certificate gives")
        C.need(all(0 <= blo[i] <= bhi[i] <= 1 for i in range(48)), "recorded box malformed")
        lab = XC.implied_labels(lab0, blo, bhi)
        for i in r.get("dc", []):
            C.need(lab[i] in (U, DC), "DC marking of an assigned coordinate"); lab[i] = DC
        C.need(lab == [int(x) for x in r["lab"]], "recorded labels differ from the derived ones")
        if kind == "split":
            C.need(lab[r["var"]] == U and len(r["children"]) == 3, "bad split")
            return nid, "split", None, None
        if kind == "kill":
            klab = [int(v) for v in r["klab"]]
            for i in range(48):
                if lab[i] in (0, 1, MIX): C.need(klab[i] == lab[i], "kill system changes an assigned label")
                else: C.need(klab[i] == DC, "kill system leaves a coordinate unassigned")
            cert = r["cert"]
            if "trivial" not in cert:
                outer = [[blo[g], bhi[g], lab[g] == MIX and blo[g] <= 0, lab[g] == MIX and bhi[g] >= 1] for g in cert["gens"]]
                C.check_box_cert(cert, C.rowof_for(klab, cert["gens"]), klab, outer)
            return nid, "kill", None, None
        if kind == "leaf":
            C.need(all(v != U for v in lab), "leaf with an unassigned coordinate")
            v = C.check_leaf(lab, r["leafcert"])
            return nid, "leaf", v, None
        return nid, kind, None, "unknown kind"
    except (C.Bad, XC.Bad) as ex:
        return nid, kind, None, "FAILED %s" % ex
    except Exception as ex:
        return nid, kind, None, "ERROR %r" % ex


def main(path, nw=8):
    from multiprocessing import Pool
    t0 = time.time()
    BATCH = int(os.environ.get("KUHN_CHECK_BATCH", "4000"))
    kinds = {"split": 0, "pkill": 0, "kill": 0, "leaf": 0}; verd = {}; bad = 0; nodes = 0
    pending = {}; seen = set(); jobs = []
    pool = Pool(nw)

    def drain():
        nonlocal bad
        for nid, kind, v, err in pool.imap_unordered(_check, jobs, chunksize=2):
            if err: bad += 1; print("node %d (%s): %s" % (nid, kind, err), flush=True)
            else:
                kinds[kind] += 1
                if kind == "leaf": verd[v] = verd.get(v, 0) + 1
        jobs.clear()

    with gzip.open(path, "rt") as f:
        header = json.loads(f.readline())
        if header.get("method") != "enumc7": raise SystemExit("not an enumc7 output")
        lab0 = [int(v) for v in header["lab"]]
        root = ("root", lab0, [F(1) if v == 1 else F(0) for v in lab0], [F(0) if v == 0 else F(1) for v in lab0])
        for line in f:
            r = json.loads(line); nodes += 1; nid = r["id"]
            if nid in seen: bad += 1; print("node %d: duplicate" % nid); continue
            if nid == 0: ctx = root
            elif nid in pending: ctx = pending.pop(nid)
            else: bad += 1; print("node %d: unknown (no parent split)" % nid); continue
            seen.add(nid)
            if r["kind"] == "split":
                blo = [F(x[0]) for x in r["box"]]; bhi = [F(x[1]) for x in r["box"]]
                for cid, l in zip(r["children"], (0, 1, MIX)):
                    if cid in seen or cid in pending: bad += 1; print("node %d: child id reused" % cid); continue
                    pending[cid] = ("child", [int(x) for x in r["lab"]], blo, bhi, r["var"], l)
            jobs.append((nid, ctx, r))
            if len(jobs) >= BATCH: drain()
    drain(); pool.close(); pool.join()
    missing = len(pending)
    ok = bad == 0 and missing == 0 and 0 in seen
    print("%s: %d nodes  split %d  pkill %d  kill %d  leaf %d %s  failed %d  children never seen %d   (%.0fs)  %s"
          % (path, nodes, kinds["split"], kinds["pkill"], kinds["kill"], kinds["leaf"], verd, bad, missing, time.time() - t0,
             "OK" if ok else "*** NOT VERIFIED"), flush=True)
    return ok


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8)
