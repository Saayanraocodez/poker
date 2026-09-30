"""Independent checker for a certified enumeration tree (enumc.py / enumc2.py output).

Every record is a node of the label tree.  The root's labels are the branch
spec; a 'split' node names its variable (must be unassigned, U) and its three
children (labels 0, 1, MIX); a 'kill' node carries a box certificate for a
system whose labels agree with the node's on every 0/1/MIX coordinate and are
DC elsewhere (a relaxation of the node's cell, Lemma 3), verified by
checkcert.check_box_cert with the rows rebuilt from the labels; a 'leaf' node
has no U left and carries a leaf certificate verified by checkcert.check_leaf.
A 'dc' list marks unassigned coordinates don't-care (Lemma 2: no
justification needed).  Coverage: every node is exactly one of the three, and
every child of a split is a node.  Hence the branch's profiles satisfying the
D-condition everywhere lie in its FAMILY leaves (none, on a betting branch).

The tree walk (labels, coverage) is sequential; the certificate checks are
independent and run in a pool.

usage:  python checkenum.py enumc_<tag>.jsonl.gz [workers]
"""
import sys, json, gzip, time
import checkcert as C

U, MIX, DC = 9, 2, 3


def _check_one(a):
    nid, kind, lab, payload = a
    try:
        if kind == "kill":
            lab2 = [int(v) for v in payload["lab"]]
            for i in range(48):
                if lab[i] in (0, 1, MIX): C.need(lab2[i] == lab[i], "kill system changes an assigned label")
                else: C.need(lab2[i] == DC, "kill system leaves a coordinate unassigned")
            cert = payload["cert"]
            C.check_box_cert(cert, C.rowof_for(lab2, cert["gens"]), lab2)
            return nid, "kill", None, None
        C.need(all(v != U for v in lab), "leaf with an unassigned coordinate")
        v = C.check_leaf(lab, payload)
        return nid, "leaf", v, None
    except C.Bad as ex:
        return nid, kind, None, "FAILED %s" % ex
    except Exception as ex:
        return nid, kind, None, "ERROR %r" % ex


def main(path, nw=8):
    from multiprocessing import Pool
    t0 = time.time()
    labs = {}; seen = set(); kinds = {"kill": 0, "split": 0, "leaf": 0}; leafverd = {}; bad = 0; nodes = 0
    jobs = []
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line); nodes += 1
            if "kind" not in r:
                labs[r["id"]] = [int(v) for v in r["lab"]]; continue
            nid = r["id"]
            if nid not in labs: bad += 1; print("node %d: unknown (no parent split)" % nid); continue
            if nid in seen: bad += 1; print("node %d: duplicate" % nid); continue
            seen.add(nid); lab = labs.pop(nid)
            try:
                for i in r.get("dc", []):
                    C.need(lab[i] in (U, DC), "DC marking of an assigned coordinate"); lab[i] = DC
                if r["kind"] == "split":
                    v = r["var"]; C.need(lab[v] == U, "split on an assigned coordinate")
                    C.need(len(r["children"]) == 3, "split without three children")
                    for l, cid in zip((0, 1, MIX), r["children"]):
                        C.need(cid not in labs and cid not in seen, "child id reused")
                        l2 = list(lab); l2[v] = l; labs[cid] = l2
                    kinds["split"] += 1
                elif r["kind"] == "kill":
                    jobs.append((nid, "kill", lab, {"lab": r["lab"], "cert": r["cert"]}))
                else:
                    jobs.append((nid, "leaf", lab, r["leafcert"]))
            except C.Bad as ex:
                bad += 1; print("node %d (%s): FAILED %s" % (nid, r["kind"], ex))
    missing = len(labs)
    with Pool(nw) as pool:
        for nid, kind, v, err in pool.imap_unordered(_check_one, jobs, chunksize=4):
            if err: bad += 1; print("node %d (%s): %s" % (nid, kind, err))
            else:
                kinds[kind] += 1
                if kind == "leaf": leafverd[v] = leafverd.get(v, 0) + 1
    print("%s: %d nodes  kill %d  split %d  leaf %d %s  failed %d  children never seen %d   (%.0fs)  %s"
          % (path, nodes, kinds["kill"], kinds["split"], kinds["leaf"], leafverd, bad, missing, time.time() - t0, "OK" if bad == 0 and missing == 0 else "*** NOT VERIFIED"))
    return bad == 0 and missing == 0


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8)
