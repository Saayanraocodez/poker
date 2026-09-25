"""Support enumeration with bnb6's contracting propagation (sequential-sound).

The label DFS of `bnb.run` (labels 0 / 1 / MIX / DC / unassigned, fixed
branching ORDER), but every node carries a BOX as well as labels, and is
propagated by bnb6.propagate in sequential mode: weak rules, and the chord
contractor with du_i = 0 imposed on every MIX coordinate.  Contraction narrows
boxes of unassigned coordinates too, which removes label options before they
are ever branched on (LO > 0 kills label 0, HI < 1 kills label 1).

Output per leaf: the complete label pattern AND its contracted box.  A leaf
box is a sound enclosure of every sequential equilibrium with that support.

Parallelism: the driver expands the top of the tree breadth-first to a few
hundred nodes and hands each to a worker, which finishes its subtree by DFS.

usage:  python enum6.py <spec> <workers> <tag> [maxnodes]
        spec as in treesize6.py ('silent', 'a11:MIX', 'a11:0.2', ...)
"""
import numpy as np, sys, time, os
from multiprocessing import Pool
import treesize6 as T6, kuhn3p as K

U, MIX, DC = T6.U, T6.MIX, T6.DC
ORDER = T6.ORDER


def _exact_alive(l):
    import enumx
    return bool(enumx.node_test(l)[0])


def dfs(a):
    lab0, LO0, HI0, weak, maxnodes = a
    stack = [(lab0[None], LO0[None], HI0[None])]
    leaves_l = []; leaves_lo = []; leaves_hi = []
    nodes = 0; abort = False
    while stack:
        lab, LO, HI = stack.pop()
        while stack and lab.shape[0] < 64:
            l2, a2, b2 = stack.pop()
            lab = np.concatenate([lab, l2]); LO = np.concatenate([LO, a2]); HI = np.concatenate([HI, b2])
        nodes += lab.shape[0]
        lab, LO, HI, al = T6.propagate(lab, LO, HI, weak)
        lab, LO, HI = lab[al], LO[al], HI[al]
        if lab.shape[0] == 0: continue
        hasU = (lab == U).any(axis=1)
        if (~hasU).any():
            leaves_l.append(lab[~hasU]); leaves_lo.append(LO[~hasU]); leaves_hi.append(HI[~hasU])
        lab, LO, HI = lab[hasU], LO[hasU], HI[hasU]
        if lab.shape[0] == 0: continue
        if maxnodes and nodes > maxnodes:
            abort = True; break
        # branch each row on its earliest unassigned coordinate in ORDER
        pos = np.full(lab.shape[0], 10**6)
        for rank, v in enumerate(ORDER):
            m = (lab[:, v] == U) & (pos == 10**6); pos[m] = rank
        for rank in np.unique(pos):
            v = ORDER[rank]; m = pos == rank
            l, a, b = lab[m], LO[m], HI[m]
            kids_l = []; kids_a = []; kids_b = []
            c0 = a[:, v] <= 0.0
            if c0.any():
                x = l[c0].copy(); x[:, v] = 0; y = b[c0].copy(); y[:, v] = 0.0
                kids_l.append(x); kids_a.append(a[c0]); kids_b.append(y)
            c1 = b[:, v] >= 1.0
            if c1.any():
                x = l[c1].copy(); x[:, v] = 1; y = a[c1].copy(); y[:, v] = 1.0
                kids_l.append(x); kids_a.append(y); kids_b.append(b[c1])
            cm = (b[:, v] > 0.0) & (a[:, v] < 1.0)       # box meets the open interval (0,1)
            if cm.any():
                x = l[cm].copy(); x[:, v] = MIX
                kids_l.append(x); kids_a.append(a[cm]); kids_b.append(b[cm])
            if kids_l:
                KL = np.concatenate(kids_l); KA = np.concatenate(kids_a); KB = np.concatenate(kids_b)
                for s0 in range(0, KL.shape[0], 256):        # bounded batches: a nash-mode
                    stack.append((KL[s0:s0+256], KA[s0:s0+256], KB[s0:s0+256]))   # run OOM'd at 82k rows
    L = np.concatenate(leaves_l) if leaves_l else np.zeros((0, 48), np.int8)
    A = np.concatenate(leaves_lo) if leaves_lo else np.zeros((0, 48))
    B = np.concatenate(leaves_hi) if leaves_hi else np.zeros((0, 48))
    return L.astype(np.int8), A, B, nodes, abort


if __name__ == "__main__":
    spec, nw, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    maxnodes = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    weak = T6.WEAK                       # KUHN_MODE=nash -> strong rules only (see treesize6)
    print("mode %s" % ("seq (weak rules)" if weak else "nash (strong rules only)"), flush=True)
    t0 = time.time()
    lab, LO, HI = T6.root_of(spec)
    lab, LO, HI, al = T6.propagate(lab[None], LO[None], HI[None], weak)
    if not al[0]:
        print("%s: dead at the root" % spec); sys.exit(0)
    # breadth-first top expansion (single process) until >= 8*nw open nodes
    frontier = [(lab[0], LO[0], HI[0])]
    top_leaves = []
    nodes = 1
    while 0 < len(frontier) < 40 * nw:
        nxt = []
        for l, a, b in frontier:
            u = [x for x in ORDER if l[x] == U]
            if not u:
                top_leaves.append((l, a, b)); continue
            kids = T6.expand(l, a, b, u[0])
            if not kids: continue
            Lk = np.array([k[0] for k in kids]); Ak = np.array([k[1] for k in kids]); Bk = np.array([k[2] for k in kids])
            Lk, Ak, Bk, alk = T6.propagate(Lk, Ak, Bk, weak)
            nodes += len(kids)
            for i in np.flatnonzero(alk):
                nxt.append((Lk[i], Ak[i], Bk[i]))
        frontier = nxt
    print("%s: top expansion -> %d subtrees, %d complete, %d nodes, %.0fs" % (spec, len(frontier), len(top_leaves), nodes, time.time() - t0), flush=True)
    # EXACT FILTER of the frontier (2026-09-17): symleaf's exact root test on
    # each subtree's label pattern (unassigned coordinates carry the
    # best-response pair x D >= 0, (1-x) D <= 0, a sound relaxation of every
    # leaf below).  On the finished Nash-mode branches it kills ~92 % of the
    # subtrees that the float DFS would otherwise spend hours enumerating.
    if os.environ.get("KUHN_EXACT_FILTER", "1") == "1" and os.path.exists("D_all.pkl"):
        t1 = time.time()
        with Pool(nw) as pool:
            alive_x = pool.map(_exact_alive, [l for l, a, b in frontier], chunksize=1)
        kept = [f for f, ok in zip(frontier, alive_x) if ok]
        print("%s: exact frontier filter -> %d of %d subtrees survive (%.0fs)" % (spec, len(kept), len(frontier), time.time() - t1), flush=True)
        frontier = kept
    jobs = [(l, a, b, weak, maxnodes) for l, a, b in frontier]
    allL = [np.array([t[0] for t in top_leaves], np.int8).reshape(-1, 48)]
    allA = [np.array([t[1] for t in top_leaves]).reshape(-1, 48)]
    allB = [np.array([t[2] for t in top_leaves]).reshape(-1, 48)]
    aborted = 0; done = 0; leaves = len(top_leaves)
    with Pool(nw) as pool:
        for L, A, B, n, ab in pool.imap_unordered(dfs, jobs, chunksize=1):
            nodes += n; done += 1; aborted += ab; leaves += len(L)
            allL.append(L); allA.append(A); allB.append(B)
            if done % 200 == 0 or done == len(jobs):
                print("   %d/%d subtrees  nodes %d  leaves %d  aborted %d  %.0fs" % (done, len(jobs), nodes, leaves, aborted, time.time() - t0), flush=True)
    L = np.concatenate(allL); A = np.concatenate(allA); B = np.concatenate(allB)
    np.save("enum6_pat_%s.npy" % tag, L); np.save("enum6_lo_%s.npy" % tag, A); np.save("enum6_hi_%s.npy" % tag, B)
    print("%s: %d leaves from %d nodes, %d subtrees aborted (node cap), %.0fs  -> enum6_pat_%s.npy" % (spec, len(L), nodes, aborted, time.time() - t0, tag), flush=True)
    if aborted:
        print("*** INCOMPLETE: %d subtrees hit the node cap; the leaf set is not exhaustive" % aborted)
