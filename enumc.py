"""CERTIFIED support enumeration of one P1-opening branch: every node of the
label tree is either killed with a certificate (certbox on the node's
D-system), split into its three children on the first unassigned coordinate
of treesize6.ORDER, or a leaf decided with a certificate (certleaf).  No
floating-point prune anywhere: the tree, with its certificates, is the whole
proof that the branch contains no support outside its FAMILY leaves, and
checkenum.py replays it with Fractions only.

Node = label vector over the 48 coordinates: 0 / 1 / MIX / DC / U.  Its
system (Lemma 3): 0/1 substituted into every D_i; D_i = 0 for MIX; -D_i >= 0
for 0; D_i >= 0 for 1; the pair x_i D_i >= 0, (1 - x_i) D_i <= 0 for DC and
U.  A coordinate occurring in no row but its own pair is marked DC (dropping
its pair is a relaxation, so nothing needs justifying).  The node test is
certbox.prove_empty_cert at budget 1 (contraction, LP, exact tree rules,
chord contractor, LP, exact dual) -- the same order as at a leaf.

Output: enumc_<tag>.jsonl.gz, one record per node:
    {"id", "parent", "lab", "kind": "kill"|"split"|"leaf", "cert"|"var"|"leafcert"}
usage:  KUHN_ORDER=bet python enumc.py <spec> <workers> <tag>
"""
import numpy as np, sys, time, os, json, gzip
from multiprocessing import Pool
from fractions import Fraction as F
import treesize6 as T6, kuhn3p as K, certbox, certleaf, enumx

U, MIX, DC = T6.U, T6.MIX, T6.DC
ORDER = T6.ORDER


def dc_by_labels(lab):
    """coordinates whose label need not be enumerated (Lemma 2: the pair covers every
    label): every node of the information set is cut off by a 0/1 label on its path
    (the label version of the reach bound RH == 0), or D_i is identically 0 after
    substituting the labels (own condition vacuous), or the coordinate is private."""
    out = set()
    cut = {}
    for i, edges in T6.PATHS:
        dead = any(lab[c] == (0 if agg else 1) for c, agg in edges)
        cut[i] = cut.get(i, True) and dead
    for i in range(48):
        if lab[i] == U and (cut.get(i, False) or not enumx._subst(enumx.D_ALL[i], lab)):
            out.add(i)
    return out


def node_job(a):
    """-> (nid, kind, payload, dc): kind 'kill' (cert) | 'split' (var) | 'leaf' (leafrec);
    dc = coordinates that were U and are marked DC at this node (children inherit)"""
    nid, lab = a
    lab = list(int(v) for v in lab)
    dc = sorted(int(i) for i in dc_by_labels(lab))
    for i in dc: lab[i] = DC
    u = [x for x in ORDER if lab[x] == U]
    if not u:
        rec = certleaf.certify(np.array(lab, np.int8), 300)
        return nid, "leaf", rec, dc
    # node system with U as DC; private coordinates dropped (and marked DC in the tree)
    lab2 = [DC if v == U else v for v in lab]
    P, kinds, free, bounds, private = enumx.node_system(lab2)
    for i in private:
        lab2[i] = DC
        if lab[i] == U: dc.append(int(i)); lab[i] = DC
    if not P:
        return nid, "split", u[0], dc
    gidx = [i for i in free]
    origins = []
    # enumx.node_system row order: for i in range(48): MIX -> ("D", i); 0 -> ("0", i); 1 -> ("1", i); DC/U -> ("DCx", i), ("DC1", i)
    # (rows of private coordinates dropped) -- rebuild the same order to name the rows
    D = None
    for i in range(48):
        if i in private: continue
        l = lab2[i]
        # a row exists only when the substituted D_i is nonzero; node_system already dropped zero rows,
        # so count rows per coordinate from P's construction: replicate the test
        d = enumx._subst(enumx.D_ALL[i], lab2)
        if not d: continue
        if l == MIX: origins.append(("D", i))
        elif l == 0: origins.append(("0", i))
        elif l == 1: origins.append(("1", i))
        else: origins.append(("DCx", i)); origins.append(("DC1", i))
    assert len(origins) == len(P), (len(origins), len(P))
    # internal node: contraction, tree rules, LP (HiGHS duals) only -- the chord contractor
    # (2 s/node, kills nothing here) and the exact dual (minutes on a 40-variable root) are
    # for leaves; a node the cheap test cannot kill is simply split
    r = certbox.prove_empty_cert(P, kinds, None, bounds, 1, origins=origins, lab=lab2, gidx=gidx, chord=False, exact_dual=False)
    if r[0]:
        c = r[1]; c["gens"] = gidx
        return nid, "kill", {"lab": lab2, "cert": c}, dc
    u = [x for x in ORDER if lab[x] == U]
    return nid, "split", u[0], dc


if __name__ == "__main__":
    spec, nw, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    t0 = time.time()
    lab0, LO, HI = T6.root_of(spec)
    lab0 = [int(v) for v in lab0]
    out = gzip.open("enumc_%s.jsonl.gz" % tag, "wt")
    out.write(json.dumps({"id": 0, "parent": -1, "lab": lab0, "spec": spec, "order": ORDER}) + "\n")
    nodes = {0: lab0}; nxt = 1
    pending = [0]; stats = {"kill": 0, "split": 0, "leaf": 0, "leafverd": {}}
    lastp = time.time()
    with Pool(nw) as pool:
        while pending:
            batch = pending[:4 * nw]; pending = pending[4 * nw:]
            for nid, kind, payload, dc in pool.imap_unordered(node_job, [(n, nodes[n]) for n in batch], chunksize=1):
                lab = nodes.pop(nid)
                for i in dc: lab[i] = DC
                stats[kind] += 1
                if kind == "kill":
                    out.write(json.dumps({"id": nid, "kind": "kill", "dc": dc, "lab": payload["lab"], "cert": payload["cert"]}) + "\n")
                elif kind == "leaf":
                    v = payload["verdict"]; stats["leafverd"][v] = stats["leafverd"].get(v, 0) + 1
                    payload["leaf"] = nid
                    out.write(json.dumps({"id": nid, "kind": "leaf", "dc": dc, "lab": lab, "leafcert": payload}) + "\n")
                else:
                    var = payload; kids = []
                    for l in (0, 1, MIX):
                        lab2 = list(lab); lab2[var] = l
                        nodes[nxt] = lab2; kids.append(nxt); pending.append(nxt); nxt += 1
                    out.write(json.dumps({"id": nid, "kind": "split", "dc": dc, "var": int(var), "children": kids}) + "\n")
            if time.time() - lastp > 60:
                lastp = time.time()
                print("   nodes %d (kill %d split %d leaf %d %s) pending %d  %.0fs" % (nxt, stats["kill"], stats["split"], stats["leaf"], stats["leafverd"], len(pending), time.time() - t0), flush=True)
    out.close()
    print("%s: %d nodes: kill %d split %d leaf %d %s   %.0fs  -> enumc_%s.jsonl.gz" % (spec, nxt, stats["kill"], stats["split"], stats["leaf"], stats["leafverd"], time.time() - t0, tag), flush=True)
