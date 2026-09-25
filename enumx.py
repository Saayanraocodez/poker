"""EXACT support enumeration: the label DFS of enum6 with symleaf's exact root
test as the pruning engine at EVERY node, instead of bnb6's float propagation.

Why.  On the finished Nash-mode branches the exact root test (contraction +
rationally certified LP relaxation on the own-reach-stripped system) killed
~92 % of enum6's top-level subtrees outright -- subtrees enum6 then spent
hours enumerating into thousands of leaves that the same test killed one by
one.  Pruning with it at every node makes the tree small, and every verdict
along the way is an exact certificate (no floating point in any prune).

Node = label vector over the 48 coordinates: 0 / 1 / MIX / DC / U(nassigned).
Its system, from D_all.pkl (symbet.build_D with all 48 coordinates symbolic,
labels substituted exactly):
    MIX i : D_i = 0,  x_i in (0,1) open
    0 / 1 : D_i <= 0 / D_i >= 0
    DC, U : x_i D_i >= 0,  (1 - x_i) D_i <= 0,  x_i in [0,1]
      -- for an unassigned coordinate this pair is exactly the necessary
      condition whatever its label turns out to be, so the node system is a
      sound relaxation of every leaf below it (up to re-choosing coordinates at
      own-unreached sets, which never changes on-path play).
A coordinate that occurs in no constraint but its own pair is PRIVATE: its
label cannot matter, it is marked DC and never branched on (this subsumes
"provably unreached").  Children of a node branch the first unassigned
coordinate in treesize6.ORDER into the labels its contracted box allows.

Leaves (no U left) are decided by symleaf.decide (identities and ranges if not
empty).  Output: enumx_pat_<tag>.npy (leaf labels), enumx_verdict_<tag>.npy.

usage:  python enumx.py <spec> <workers> <tag>
"""
import numpy as np, sys, time, pickle, os
from fractions import Fraction as F
from multiprocessing import Pool
import treesize6 as T6, exactbox, kuhn3p as K

U, MIX, DC = T6.U, T6.MIX, T6.DC
ORDER = T6.ORDER; NAME = K.PARAM_NAME
D_ALL = pickle.load(open("D_all.pkl", "rb"))       # 48 dict-polys over 48 gens


def _subst(poly, lab):
    """substitute the 0/1 labels into a dict-poly over 48 gens."""
    out = {}
    for m, c in poly.items():
        skip = False; mm = list(m)
        for j, e in enumerate(m):
            if e and lab[j] == 0: skip = True; break
            if e and lab[j] == 1: mm[j] = 0
        if skip: continue
        mm = tuple(mm); out[mm] = out.get(mm, F(0)) + c
    return {m: c for m, c in out.items() if c != 0}


def _project(poly, cols):
    """restrict exponent tuples to the free columns."""
    return {tuple(m[j] for j in cols): c for m, c in poly.items()}


def node_system(lab):
    """-> (polys, kinds, free (global indices), bounds, private (global indices))"""
    free = [i for i in range(48) if lab[i] in (MIX, DC, U)]
    col = {i: k for k, i in enumerate(free)}
    D = {i: _subst(D_ALL[i], lab) for i in range(48)}
    polys = []; kinds = []; owner = []          # owner: the coordinate whose pair a row is, else -1
    for i in range(48):
        d = D[i]
        if not d: continue
        if lab[i] == MIX:   polys.append(d); kinds.append("="); owner.append(-1)
        elif lab[i] == 0:   polys.append({m: -c for m, c in d.items()}); kinds.append(">="); owner.append(-1)
        elif lab[i] == 1:   polys.append(d); kinds.append(">="); owner.append(-1)
        else:                                   # DC or U: x D >= 0 and (1 - x) D <= 0
            xd = {}
            for m, c in d.items():
                mm = list(m); mm[i] += 1; xd[tuple(mm)] = c
            polys.append(xd); kinds.append(">="); owner.append(i)
            q = {m: -c for m, c in d.items()}
            for m, c in xd.items(): q[m] = q.get(m, F(0)) + c
            polys.append({m: c for m, c in q.items() if c != 0}); kinds.append(">="); owner.append(i)
    # private coordinates: occur in no row but their own pair
    occ = {i: set() for i in free}
    for r, p in enumerate(polys):
        for m in p:
            for j, e in enumerate(m):
                if e: occ[j].add(r)
    private = [i for i in free if lab[i] in (DC, U) and all(owner[r] == i for r in occ[i])]
    if private:
        drop = {r for i in private for r in occ[i]}
        polys = [p for r, p in enumerate(polys) if r not in drop]; kinds = [k for r, k in enumerate(kinds) if r not in drop]
        free = [i for i in free if i not in private]
    P = [_project(p, free) for p in polys]
    bounds = [(F(0), F(1), lab[i] == MIX, lab[i] == MIX) for i in free]
    return P, kinds, free, bounds, private


def node_test(lab, LO=None, HI=None, widen=1e-9):
    """exact root test.  -> (alive, contracted box over `free`, free, private).
    With LO/HI (the float propagation's box for this node, a sound enclosure
    up to the quantified rounding caveat -- the same trust the enumeration
    already places in it to restrict children labels) the exact variables
    start from that box, widened by `widen` and clipped to [0,1]; a MIX
    coordinate keeps its open endpoint only where the box still touches 0 / 1."""
    P, kinds, free, bounds, private = node_system(lab)
    if LO is not None:
        bounds = []
        for i in free:
            lo = max(0.0, float(LO[i]) - widen); hi = min(1.0, float(HI[i]) + widen)
            lo = F(lo).limit_denominator(1 << 40); hi = F(hi).limit_denominator(1 << 40)
            lo = max(F(0), lo - F(1, 1 << 40)); hi = min(F(1), hi + F(1, 1 << 40))   # outward, still sound
            bounds.append((lo, hi, lab[i] == MIX and lo == 0, lab[i] == MIX and hi == 1))
    cons = exactbox.prepare(P, kinds, None, factor=False)
    if cons is None: return False, None, free, private
    box = [list(b) for b in bounds]
    if not exactbox.contract(cons, box): return False, None, free, private
    dead, hint = exactbox.lp_infeasible(cons, box)
    if dead: return False, None, free, private
    return True, box, free, private


def children(lab, box, free, v):
    """labels of coordinate v allowed by its contracted box."""
    b = box[free.index(v)]
    out = []
    if b[0] <= 0: l = lab.copy(); l[v] = 0; out.append(l)
    if b[1] >= 1: l = lab.copy(); l[v] = 1; out.append(l)
    if b[1] > 0 and b[0] < 1: l = lab.copy(); l[v] = MIX; out.append(l)
    return out


def dfs(a):
    lab0, maxnodes = a
    stack = [lab0]; leaves = []; nodes = 0; abort = False
    while stack:
        lab = stack.pop(); nodes += 1
        alive, box, free, private = node_test(lab)
        if not alive: continue
        lab = lab.copy()
        for i in private: lab[i] = DC
        u = [x for x in ORDER if lab[x] == U]
        if not u:
            leaves.append(lab); continue
        if maxnodes and nodes > maxnodes: abort = True; break
        stack.extend(children(lab, box, free, u[0]))
    return (np.array(leaves, np.int8).reshape(-1, 48), nodes, abort)


if __name__ == "__main__":
    spec, nw, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    t0 = time.time()
    lab, _, _ = T6.root_of(spec)
    alive, box, free, private = node_test(lab)
    if not alive:
        print("%s: dead at the root (exact)" % spec, flush=True)
        np.save("enumx_pat_%s.npy" % tag, np.zeros((0, 48), np.int8)); sys.exit(0)
    for i in private: lab[i] = DC
    frontier = [lab]; nodes = 1; top_leaves = []
    while 0 < len(frontier) < 40 * nw:
        nxt = []
        for l in frontier:
            u = [x for x in ORDER if l[x] == U]
            if not u: top_leaves.append(l); continue
            al, bx, fr, pr = node_test(l)
            nodes += 1
            if not al: continue
            l = l.copy()
            for i in pr: l[i] = DC
            nxt.extend(children(l, bx, fr, u[0]))
        frontier = nxt
    print("%s: top expansion -> %d subtrees, %d complete, %d nodes, %.0fs" % (spec, len(frontier), len(top_leaves), nodes, time.time() - t0), flush=True)
    allL = [np.array(top_leaves, np.int8).reshape(-1, 48)]; leaves = len(top_leaves); done = 0; aborted = 0
    with Pool(nw) as pool:
        for L, n, ab in pool.imap_unordered(dfs, [(l, 0) for l in frontier], chunksize=1):
            nodes += n; done += 1; aborted += ab; leaves += len(L); allL.append(L)
            if done % 100 == 0 or done == len(frontier):
                print("   %d/%d subtrees  nodes %d  leaves %d  %.0fs" % (done, len(frontier), nodes, leaves, time.time() - t0), flush=True)
    L = np.concatenate(allL)
    np.save("enumx_pat_%s.npy" % tag, L)
    print("%s: %d leaves from %d nodes, %.0fs  -> enumx_pat_%s.npy" % (spec, len(L), nodes, time.time() - t0, tag), flush=True)
    # decide the leaves
    if len(L):
        import symleaf
        with Pool(nw) as pool:
            res = pool.map(symleaf._job, [(k, L[k], 300) for k in range(len(L))], chunksize=1)
        verd = np.array([symleaf.VC[v] for k, v, info, dt in sorted(res)], np.int8)
        np.save("enumx_verdict_%s.npy" % tag, verd)
        cnt = {v: int((verd == symleaf.VC[v]).sum()) for v in symleaf.VERD if (verd == symleaf.VC[v]).sum()}
        print("%s: leaf verdicts %s   %.0fs" % (spec, cnt, time.time() - t0), flush=True)
        for k, v, info, dt in sorted(res):
            if v not in ("EMPTY_GB", "EMPTY_MIX", "EMPTY_BOX", "EMPTY_CONST"):
                print("   leaf %d  %s  %s" % (k, v, {a: b for a, b in info.items() if a != "box"}), flush=True)
