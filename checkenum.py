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
import sys, os, json, gzip, time
import checkcert as C

U, MIX, DC = 9, 2, 3


from fractions import Fraction as _F


def label_box48(lab):
    """the box a node's labels allow, per coordinate"""
    out = {}
    for i, v in enumerate(lab):
        if v == 0: out[i] = [_F(0), _F(0), False, False]
        elif v == 1: out[i] = [_F(1), _F(1), False, False]
        elif v == MIX: out[i] = [_F(0), _F(1), True, True]
        else: out[i] = [_F(0), _F(1), False, False]
    return out


def child_box(box, v, l):
    """the parent's certified box with the split coordinate v set by the child's label"""
    b = {i: list(x) for i, x in box.items()}
    if l == 0: b[v] = [_F(0), _F(0), False, False]
    elif l == 1: b[v] = [_F(1), _F(1), False, False]
    else:
        lo, hi, lo_o, hi_o = b[v]
        b[v] = [lo, hi, lo_o or lo <= 0, hi_o or hi >= 1]
        if lo < 0: b[v][0] = _F(0)
        if hi > 1: b[v][1] = _F(1)
    return b


def replay_contraction(r, lab, box):
    """a split that records the contraction of its own system (enumc3): rebuild the rows
    from their origins, start from the node's certified box, replay every step; the result
    is the box the node's children inherit."""
    lab2 = [DC if v == U else v for v in lab]
    gens = r["cgens"]
    rowof = C.rowof_for(lab2, gens)
    polys = []; kinds = []
    for og in r["corigins"]:
        p, k = rowof(tuple(og)); polys.append(p); kinds.append(k)
    b0 = C.parse_box(r["cbox0"])
    # the declared start may be LOOSER than the box computed here (enumc4 rounds inherited
    # bounds outward to keep denominators small) -- never tighter; replay from the declared box
    C.need(C.box_contains(b0, [list(box[g]) for g in gens]), "contraction starts from a box tighter than the node's certified box")
    b = [list(x) for x in b0]
    for st in r["csteps"]:
        if st[0] in ("lo", "hi"):
            C.check_step(polys, kinds, b, st)
        elif st[0] in ("tlo", "thi"):                      # enumc4: tree-structured pins
            C.need(C.check_tree_step(lab2, gens, b, st), "a tree step closes the node -- it should be a kill")
        elif st[0] == "chord":                             # enumc4: chord contractor
            C.need(C.check_chord_step(lab2, gens, b, st), "a chord step closes the node -- it should be a kill")
        else:
            C.need(False, "a split's contraction closes the node -- it should be a kill")
    out = {i: list(x) for i, x in box.items()}
    for t, g in enumerate(gens): out[g] = b[t]
    return out


def _check_one(a):
    nid, kind, lab, payload = a
    try:
        if kind == "kill":
            lab2 = [int(v) for v in payload["lab"]]
            for i in range(48):
                if lab[i] in (0, 1, MIX): C.need(lab2[i] == lab[i], "kill system changes an assigned label")
                else: C.need(lab2[i] == DC, "kill system leaves a coordinate unassigned")
            cert = payload["cert"]
            outer = [payload["box"][g] for g in cert["gens"]] if payload.get("box") else None
            C.check_box_cert(cert, C.rowof_for(lab2, cert["gens"]), lab2, outer)
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
    boxes = {}; ncontract = 0
    jobs = []
    # 2026-09-30: certificates are checked in bounded batches WHILE reading (the checks are the
    # same).  Holding every certificate first would need tens of GB for the million-record trees
    # of the six long branches (a 1.1 GB .gz holds ~830k records).
    BATCH = int(os.environ.get("KUHN_CHECK_BATCH", "20000"))
    pool = Pool(nw)

    def drain():
        nonlocal bad
        for nid, kind, v, err in pool.imap_unordered(_check_one, jobs, chunksize=4):
            if err: bad += 1; print("node %d (%s): %s" % (nid, kind, err))
            else:
                kinds[kind] += 1
                if kind == "leaf": leafverd[v] = leafverd.get(v, 0) + 1
        jobs.clear()

    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line); nodes += 1
            if "kind" not in r:
                labs[r["id"]] = [int(v) for v in r["lab"]]; continue
            nid = r["id"]
            if nid not in labs: bad += 1; print("node %d: unknown (no parent split)" % nid); continue
            if nid in seen: bad += 1; print("node %d: duplicate" % nid); continue
            seen.add(nid); lab = labs.pop(nid)
            box = boxes.pop(nid, None)
            if box is None: box = label_box48(lab)
            try:
                for i in r.get("dc", []):
                    C.need(lab[i] in (U, DC), "DC marking of an assigned coordinate"); lab[i] = DC
                if r["kind"] == "split":
                    v = r["var"]; C.need(lab[v] == U, "split on an assigned coordinate")
                    C.need(len(r["children"]) == 3, "split without three children")
                    if "csteps" in r:
                        box = replay_contraction(r, lab, box); ncontract += 1
                    for l, cid in zip((0, 1, MIX), r["children"]):
                        C.need(cid not in labs and cid not in seen, "child id reused")
                        l2 = list(lab); l2[v] = l; labs[cid] = l2
                        boxes[cid] = child_box(box, v, l)
                    kinds["split"] += 1
                elif r["kind"] == "kill":
                    jobs.append((nid, "kill", lab, {"lab": r["lab"], "cert": r["cert"],
                                                    "box": {g: box[g] for g in r["cert"].get("gens", [])} if "cert" in r and "trivial" not in r["cert"] else None}))
                else:
                    jobs.append((nid, "leaf", lab, r["leafcert"]))
            except C.Bad as ex:
                bad += 1; print("node %d (%s): FAILED %s" % (nid, r["kind"], ex))
            if len(jobs) >= BATCH: drain()
    missing = len(labs)
    drain(); pool.close(); pool.join()
    print("%s: %d nodes  kill %d  split %d  leaf %d %s  failed %d  children never seen %d   (%.0fs)  %s"
          % (path, nodes, kinds["kill"], kinds["split"], kinds["leaf"], leafverd, bad, missing, time.time() - t0, "OK" if bad == 0 and missing == 0 else "*** NOT VERIFIED"))
    return bad == 0 and missing == 0


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8)
