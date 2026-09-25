"""Branch-and-bound enumeration of ALL support patterns that can carry a Nash
equilibrium of 3-player 4-card Kuhn poker.

label codes per coordinate:  0 = exactly 0, 1 = exactly 1, 2 = interior (0,1),
                             3 = don't care (info set provably unreachable),
                             9 = unassigned
Sound pruning only: a pattern is discarded únicamente when interval propagation
proves NO completion can satisfy the first-order Nash conditions.
"""
import numpy as np
import ivl, kuhn3p as K

U, MIX, DC = 9, 2, 3
TOL = 1e-11
NPARAM = 48
OWN = np.repeat([0, 1, 2], 16)

def lohi(lab):
    LO = np.where(lab == 1, 1.0, 0.0)
    HI = np.where(lab == 0, 0.0, 1.0)
    return LO, HI

def propagate(lab, tol=TOL, rounds=4):
    """Returns (lab, alive_mask).  Fix-point of forcing + feasibility."""
    alive = np.ones(lab.shape[0], bool)
    for _ in range(rounds):
        LO, HI = lohi(lab)
        DLO, DHI, RH, DMIN, DMAX = ivl.bounds(LO, HI)
        bad = ((lab == 0) & (DLO > tol)) | ((lab == 1) & (DHI < -tol)) \
            | ((lab == MIX) & ((DLO > tol) | (DHI < -tol)))
        alive &= ~bad.any(axis=1)
        if not alive.any():
            return lab, alive
        isU = (lab == U)
        # strict forcing (du has a definite sign on the whole box)
        f1 = isU & ((DLO > tol) | (DMIN > tol))
        f0 = isU & ((DHI < -tol) | (DMAX < -tol))
        dc = isU & (RH <= 0.0)
        new = lab.copy()
        new[f1] = 1; new[f0] = 0
        new[dc & ~f1 & ~f0] = DC
        if np.array_equal(new, lab):
            return lab, alive
        lab = new
    return lab, alive

def expand(lab, var):
    """triple each row, assigning `var` = 0 / 1 / interior."""
    n = lab.shape[0]
    out = np.repeat(lab, 3, axis=0)
    out[0::3, var] = 0
    out[1::3, var] = 1
    out[2::3, var] = MIX
    return out

def run(root_lab, order, cap=4096, log=None, maxnodes=None, sink=None):
    """DFS over the support tree.  Returns list of complete label patterns.
    If `sink` is given it is called with each block of completed patterns and
    they are not accumulated in memory."""
    root = root_lab[None, :].copy()
    root, alive = propagate(root)
    if not alive[0]:
        return [], dict(nodes=1, pruned=1)
    stack = [root]
    done = []
    stats = dict(nodes=0, batches=0)
    while stack:
        cur = stack.pop()
        stats['nodes'] += cur.shape[0]; stats['batches'] += 1
        # split off completed rows
        hasU = (cur == U).any(axis=1)
        if (~hasU).any():
            blk = cur[~hasU]
            stats['leaves'] = stats.get('leaves', 0) + blk.shape[0]
            if sink is None: done.append(blk)
            else: sink(blk)
        cur = cur[hasU]
        if cur.shape[0] == 0:
            continue
        # branch on the earliest unassigned variable in `order`
        pos = np.full(cur.shape[0], 10 ** 6)
        for rank, v in enumerate(order):
            m = (cur[:, v] == U) & (pos == 10 ** 6)
            pos[m] = rank
        for rank in np.unique(pos):
            v = order[rank]
            sub = cur[pos == rank]
            for s in range(0, sub.shape[0], cap):
                blk = expand(sub[s:s + cap], v)
                blk, al = propagate(blk)
                blk = blk[al]
                if blk.shape[0]:
                    stack.append(blk)
        if maxnodes and stats['nodes'] > maxnodes:
            stats['ABORT'] = True
            break
        if log and stats['batches'] % log == 0:
            print("  nodes=%d stack=%d leaves=%d" % (stats['nodes'], len(stack),
                  stats.get('leaves', 0)), flush=True)
    pats = np.concatenate(done) if done else np.zeros((0, NPARAM), np.int64)
    return pats, stats
