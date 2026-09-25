"""LAYERED exact enumeration: enum6's float label DFS, with symleaf's exact
root test applied every K levels all the way down -- not only at the top
expansion frontier.

Why.  enum6 with the frontier filter killed 88 % of the top-level subtrees of
a11:MIX,a21:MIX,a31:MIX,a41:1 and still enumerated 736,987 leaves in 17 h: the
surviving subtrees are the deep ones and hold nearly all the leaves, and the
float propagation prunes them weakly.  The exact test (own-reach-stripped
system, unassigned coordinates carrying the best-response pair, contraction +
rationally certified LP) kills ~90 % of the nodes it sees at the frontier and
100 % of the leaves; applying it every K levels turns the exponential into a
much smaller one.  It is exactly the same test as the frontier filter, so the
soundness argument is unchanged (enumx.py).

Per worker: a stack of (labels, LO, HI) nodes.  A node with no unassigned
coordinate is a leaf.  Otherwise it is expanded K levels by the float BFS
(treesize6.expand / propagate, KUHN_MODE honoured), every resulting node gets
the exact test, survivors go back on the stack.

Output is in enum6's format so runbet6 / symleaf consume it unchanged:
    enum6_pat_<tag>.npy, enum6_lo_<tag>.npy, enum6_hi_<tag>.npy
and the leaves are decided at the end (symleaf.decide) into symleaf_<tag>.npz.

usage:  [KUHN_MODE=nash] python enuml.py <spec> <workers> <tag> [K]
"""
import numpy as np, sys, time, os
from multiprocessing import Pool
import treesize6 as T6, enumx, kuhn3p as K

U, MIX, DC = T6.U, T6.MIX, T6.DC
ORDER = T6.ORDER


def expand_layer(node, k, weak):
    """float BFS k levels below node -> (open nodes, complete leaves)"""
    frontier = [node]; leaves = []
    for _ in range(k):
        nxt = []
        for l, a, b in frontier:
            u = [x for x in ORDER if l[x] == U]
            if not u:
                leaves.append((l, a, b)); continue
            kids = T6.expand(l, a, b, u[0])
            if not kids: continue
            Lk = np.array([q[0] for q in kids]); Ak = np.array([q[1] for q in kids]); Bk = np.array([q[2] for q in kids])
            Lk, Ak, Bk, alk = T6.propagate(Lk, Ak, Bk, weak)
            for i in np.flatnonzero(alk):
                nxt.append((Lk[i], Ak[i], Bk[i]))
        frontier = nxt
        if not frontier: break
    return frontier, leaves


def expand_layer_batch(nodes, k, weak):
    """expand_layer for MANY nodes at once: one float propagate per level for
    all of their children together.  bnb6's contractor costs ~100 ivl calls
    per propagate whatever the batch size, so this is ~10x cheaper per node
    than expanding nodes one by one (0.7 s per node measured)."""
    frontier = list(nodes); leaves = []
    for _ in range(k):
        kl = []; ka = []; kb = []
        for l, a, b in frontier:
            u = [x for x in ORDER if l[x] == U]
            if not u:
                leaves.append((l, a, b)); continue
            for q in T6.expand(l, a, b, u[0]):
                kl.append(q[0]); ka.append(q[1]); kb.append(q[2])
        if not kl: return [], leaves
        Lk = np.array(kl); Ak = np.array(ka); Bk = np.array(kb)
        nxt = []
        for s0 in range(0, len(Lk), 512):
            L2, A2, B2, al2 = T6.propagate(Lk[s0:s0+512], Ak[s0:s0+512], Bk[s0:s0+512], weak)
            for i in np.flatnonzero(al2):
                nxt.append((L2[i], A2[i], B2[i]))
        frontier = nxt
        if not frontier: break
    return frontier, leaves


def _alive(l):
    return bool(enumx.node_test(l)[0])


def _expand1(a):
    """one float level below a chunk of top-expansion nodes (pool job)"""
    nodes, weak = a
    return expand_layer_batch(nodes, 1, weak)


def worker(a):
    """DFS below one node with a budget of exact tests; when the budget runs
    out the unfinished stack is handed back to the driver and re-queued, so a
    deep subtree is shared by many workers instead of pinning one for hours
    (4 of 16 workers were busy for the last hour of a branch, 2026-09-19)."""
    node, k, weak, budget = a
    stack = [node]; leaves = []; tests = 0; killed = 0
    while stack:
        if budget and tests >= budget:
            break
        batch = [stack.pop() for _ in range(min(16, len(stack)))]
        opn, lv = expand_layer_batch(batch, k, weak)
        leaves.extend(lv)
        for m in opn:
            tests += 1
            alive, box, free, private = enumx.node_test(m[0])
            if not alive:
                killed += 1; continue
            l = m[0].copy()
            for i in private: l[i] = DC          # a private coordinate's label cannot matter
            stack.append((l, m[1], m[2]))
    Lf = np.array([q[0] for q in leaves], np.int8).reshape(-1, 48)
    Af = np.array([q[1] for q in leaves]).reshape(-1, 48); Bf = np.array([q[2] for q in leaves]).reshape(-1, 48)
    return Lf, Af, Bf, tests, killed, stack


if __name__ == "__main__":
    spec, nw, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    k = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    weak = T6.WEAK
    print("mode %s   layer depth %d" % ("seq (weak rules)" if weak else "nash (strong rules only)", k), flush=True)
    t0 = time.time()
    lab, LO, HI = T6.root_of(spec)
    lab, LO, HI, al = T6.propagate(lab[None], LO[None], HI[None], weak)
    if not al[0]:
        print("%s: dead at the root" % spec); sys.exit(0)
    # top expansion to ~40*nw nodes, then the exact filter, as enum6 does
    frontier = [(lab[0], LO[0], HI[0])]; top_leaves = []
    # KUHN_FRONTIER subtrees per worker (default 200): a big frontier keeps the
    # tail short -- with 40 per worker the last 8 of 508 subtrees ran alone for
    # an hour on 8 of 16 workers (2026-09-19)
    target = int(os.environ.get("KUHN_FRONTIER", "200")) * nw
    # batched (2026-09-20): one propagate per 512 children instead of one per
    # node -- the node-by-node loop took 1225 s on the silent branch under
    # directed rounding (per-call overhead dominates on 1-3 row batches) --
    # and spread over the pool once the frontier holds >= 4 nodes per worker:
    # the single-process top expansion was 2.1 h of the 5.3 h nash run.
    with Pool(nw) as pool:
        while 0 < len(frontier) < target:
            if len(frontier) < 4 * nw:
                frontier, lv = expand_layer_batch(frontier, 1, weak); top_leaves.extend(lv)
            else:
                res = pool.map(_expand1, [(frontier[i::nw], weak) for i in range(nw) if frontier[i::nw]], chunksize=1)
                frontier = [n for o, lv in res for n in o]; top_leaves.extend(l for o, lv in res for l in lv)
        print("%s: top expansion -> %d subtrees, %d complete, %.0fs" % (spec, len(frontier), len(top_leaves), time.time() - t0), flush=True)
        alive_x = pool.map(_alive, [n[0] for n in frontier], chunksize=1)
    frontier = [n for n, ok in zip(frontier, alive_x) if ok]
    print("%s: exact frontier filter -> %d subtrees survive (%.0fs)" % (spec, len(frontier), time.time() - t0), flush=True)
    allL = [np.array([q[0] for q in top_leaves], np.int8).reshape(-1, 48)]
    allA = [np.array([q[1] for q in top_leaves]).reshape(-1, 48)]; allB = [np.array([q[2] for q in top_leaves]).reshape(-1, 48)]
    done = 0; tests = 0; killed = 0; leaves = len(top_leaves)
    budget = int(os.environ.get("KUHN_BUDGET", "400"))       # exact tests per job before it hands back its stack
    from collections import deque
    pending = deque(frontier); active = []; jobs = 0; requeued = 0; lastp = time.time()
    with Pool(nw) as pool:
        while pending or active:
            while pending and len(active) < 2 * nw:
                active.append(pool.apply_async(worker, ((pending.popleft(), k, weak, budget),))); jobs += 1
            fin = [r for r in active if r.ready()]
            if not fin:
                time.sleep(0.2); continue
            for r in fin:
                active.remove(r)
                Lf, Af, Bf, ts, kl, rest = r.get()
                done += 1; tests += ts; killed += kl; leaves += len(Lf)
                allL.append(Lf); allA.append(Af); allB.append(Bf)
                if rest:
                    requeued += len(rest); pending.extend(rest)
            if time.time() - lastp > 60 or (not pending and not active):
                lastp = time.time()
                print("   jobs %d done (%d queued, %d running, %d handed back)  exact tests %d  killed %d (%.1f%%)  leaves %d  %.0fs"
                      % (done, len(pending), len(active), requeued, tests, killed, 100.0 * killed / max(1, tests), leaves, time.time() - t0), flush=True)
    L = np.concatenate(allL); A = np.concatenate(allA); B = np.concatenate(allB)
    np.save("enum6_pat_%s.npy" % tag, L); np.save("enum6_lo_%s.npy" % tag, A); np.save("enum6_hi_%s.npy" % tag, B)
    print("%s: %d leaves, %d exact tests (%d killed), %.0fs  -> enum6_pat_%s.npy" % (spec, len(L), tests, killed, time.time() - t0, tag), flush=True)
    # decide the leaves (same as runbet6's exact stage) so the driver finds them done
    if len(L):
        import symleaf
        verd = np.full(len(L), -1, np.int8); tsec = np.zeros(len(L))
        for kk, v, info, dt in symleaf.run_pool([(kk, L[kk], 300) for kk in range(len(L))], min(nw, len(L)), 600.0):
            verd[kk] = symleaf.VC[v]; tsec[kk] = dt
            if v not in ("EMPTY_GB", "EMPTY_MIX", "EMPTY_BOX", "EMPTY_CONST"):
                print("   leaf %d  %s  %s" % (kk, v, {a: b for a, b in info.items() if a != "box"}), flush=True)
        np.savez("symleaf_%s.npz" % tag, verdict=verd, tsec=tsec, idx=np.arange(len(L)))
        cnt = {v: int((verd == symleaf.VC[v]).sum()) for v in symleaf.VERD if (verd == symleaf.VC[v]).sum()}
        print("%s: leaf verdicts %s   %.0fs" % (spec, cnt, time.time() - t0), flush=True)
    else:
        import symleaf
        np.savez("symleaf_%s.npz" % tag, verdict=np.zeros(0, np.int8), tsec=np.zeros(0), idx=np.zeros(0, np.int64))
