"""THEOREM ATTEMPT:  no Nash equilibrium has a11 >= delta.  (P1 never bluffs card 1.)

Version 2.  Version 1 used six hand-picked conditions and found a survivor on the
origin face (a11 = e, a41 = 2e, everything else 0), where the omitted conditions
on b11, b21, c11, c21 are what kill it.  So this version uses ALL 27 first-order
conditions, each in box semantics:

     LO[i] > 0  =>  du_i >= 0      HI[i] < 1  =>  du_i <= 0

exactly as bnb5 does -- but with two things bnb5 does not have.

  * Every du_i is an explicit multilinear polynomial with only Table 2
    substituted (461 monomials across all 27, max degree 4), verified against
    bgrad.grads_own to ~1e-16.  A monomial's range over a box in [0,1]^27 is
    [c*prod(lo), c*prod(hi)] sign-adjusted, and the sum is a sound outer bound.
  * The exact DEPENDENCY GRAPH: which variables each du_i involves.  The split
    rule picks the least-decided condition and splits the widest variable that
    condition actually depends on.  bnb5 splits the widest coordinate overall,
    which on the betting branches spends the depth budget on coordinates that do
    not matter for the conditions that are close to firing.

Forcing, as in bnb5: du_i provably > 0 on a box forces x_i = 1 (kills the box if
HI[i] < 1); provably < 0 forces x_i = 0.

Strictness: the claim is proved for a11 >= delta, a closed condition.  Run with
several deltas; bounded node counts as delta -> 0 are the evidence about the
limit, and the limit itself is a separate argument.

CONTROLS (both run before the theorem):
  * polynomials re-verified against bgrad;
  * the search with the a11 >= delta restriction REMOVED must find a survivor
    (the family equilibria live at a11 = 0), which shows the prover does not kill
    boxes for spurious reasons.

usage:  python provea11.py <delta> [maxnodes] [cap]
"""
import numpy as np, sympy as sp, sys, time
import symbet, bgrad, kuhn3p as K

I = K.NAME_IDX
NAME = K.PARAM_NAME
TOL = 1e-12


def build():
    X, syms = symbet.table2_only()
    G, U = symbet.build(X)
    vars_ = sorted(syms)
    order = [syms[v] for v in vars_]
    pos = {v: k for k, v in enumerate(vars_)}
    conds = []                       # per variable i: list of (coeff, var-positions)
    deps = []
    exprs = {}
    for v in vars_:
        e = sp.expand(G[I[v]])
        exprs[v] = e
        poly = sp.Poly(e, *order) if e != 0 else None
        mons = []
        if poly is not None:
            for mon, c in poly.terms():
                vs = []
                for k, ex in enumerate(mon):
                    vs += [k] * ex
                mons.append((float(c), tuple(vs)))
        conds.append(mons)
        deps.append(sorted({k for _, vs in mons for k in vs}))
    return vars_, pos, conds, deps, exprs, syms


def verify(exprs, syms):
    rng = np.random.default_rng(5)
    P = rng.random((2000, 48))
    for nm in symbet.T2_ZERO: P[:, I[nm]] = 0.0
    for nm in symbet.T2_ONE:  P[:, I[nm]] = 1.0
    Gn = bgrad.grads_own(P)
    worst = 0.0
    for v, e in exprs.items():
        fn = sp.lambdify([syms[s] for s in sorted(syms)], e, "numpy")
        val = fn(*[P[:, I[s]] for s in sorted(syms)])
        val = np.broadcast_to(val, (len(P),))
        worst = max(worst, float(np.abs(val - Gn[:, I[v]]).max()))
    return worst


def bounds(conds, LO, HI):
    """Sound outer bounds (B, n) on every du_i over each box."""
    B, n = LO.shape
    DLO = np.zeros((B, n)); DHI = np.zeros((B, n))
    for i, mons in enumerate(conds):
        lo = np.zeros(B); hi = np.zeros(B)
        for c, vs in mons:
            pl = np.ones(B); ph = np.ones(B)
            for v in vs:
                pl *= LO[:, v]; ph *= HI[:, v]
            if c >= 0:
                lo += c * pl; hi += c * ph
            else:
                lo += c * ph; hi += c * pl
        DLO[:, i] = lo; DHI[:, i] = hi
    return DLO, DHI


def propagate(conds, LO, HI, rounds=6):
    alive = np.ones(LO.shape[0], bool)
    for _ in range(rounds):
        DLO, DHI = bounds(conds, LO, HI)
        need_ge = LO > 0.0
        need_le = HI < 1.0
        dead = (need_ge & (DHI < -TOL)) | (need_le & (DLO > TOL))
        alive &= ~dead.any(axis=1)
        if not alive.any():
            return LO, HI, alive, DLO, DHI
        f1 = DLO > TOL                 # du provably > 0: x must be 1
        f0 = DHI < -TOL                # du provably < 0: x must be 0
        nLO = np.where(f1, 1.0, LO); nHI = np.where(f0, 0.0, HI)
        # forcing into a contradiction with the box kills it
        alive &= ~((f1 & (HI < 1.0)) | (f0 & (LO > 0.0))).any(axis=1)
        if np.array_equal(nLO, LO) and np.array_equal(nHI, HI):
            break
        LO, HI = nLO, nHI
    DLO, DHI = bounds(conds, LO, HI)
    return LO, HI, alive, DLO, DHI


def search(vars_, pos, conds, deps, delta, maxnodes, cap=2048, log=200000):
    n = len(vars_)
    LO = np.zeros((1, n)); HI = np.ones((1, n))
    if delta is not None:
        LO[0, pos["a11"]] = delta
    LO, HI, al, _, _ = propagate(conds, LO, HI)
    if not al[0]:
        return True, 1, None
    stack = [(LO[al], HI[al])]
    nodes = 0; maxd = 0
    while stack:
        LO, HI = stack.pop()
        nodes += LO.shape[0]
        if maxnodes and nodes > maxnodes:
            return None, nodes, (LO[0], HI[0])
        W = HI - LO
        fin = W.max(axis=1) < 1e-9
        if fin.any():
            return False, nodes, (LO[fin][0], HI[fin][0])
        LO, HI, al, DLO, DHI = propagate(conds, LO, HI)
        LO, HI, DLO, DHI = LO[al], HI[al], DLO[al], DHI[al]
        if LO.shape[0] == 0:
            continue
        W = HI - LO
        # slack of each condition: how far it is from being decided
        need_ge = LO > 0.0; need_le = HI < 1.0
        slack = np.zeros_like(W)
        s_ge = np.where(need_ge & (DLO < 0.0), -DLO, 0.0)
        s_le = np.where(need_le & (DHI > 0.0), DHI, 0.0)
        slack = np.maximum(s_ge, s_le)
        # variables with zero width cannot be split; mask them out per condition
        j = np.empty(LO.shape[0], int)
        for b in range(LO.shape[0]):
            order = np.argsort(-slack[b])
            chosen = -1
            for ci in order:
                if slack[b, ci] <= 0:
                    break
                cand = [v for v in deps[ci] if W[b, v] > 1e-9]
                if cand:
                    chosen = max(cand, key=lambda v: W[b, v]); break
            if chosen < 0:
                chosen = int(W[b].argmax())
            j[b] = chosen
        for jj in np.unique(j):
            m = j == jj
            b_, c_ = LO[m], HI[m]
            for s in range(0, b_.shape[0], cap):
                bl, ch = b_[s:s+cap], c_[s:s+cap]
                mid = 0.5 * (bl[:, jj] + ch[:, jj])
                Bl = np.repeat(bl, 2, axis=0); Ch = np.repeat(ch, 2, axis=0)
                Ch[0::2, jj] = mid; Bl[1::2, jj] = mid
                stack.append((Bl, Ch))
        if log and nodes // log != (nodes - LO.shape[0]) // log:
            print("   nodes %d  stack %d" % (nodes, sum(s[0].shape[0] for s in stack)), flush=True)
    return True, nodes, None


if __name__ == "__main__":
    delta = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02
    maxnodes = int(sys.argv[2]) if len(sys.argv) > 2 else 20000000
    t0 = time.time()
    vars_, pos, conds, deps, exprs, syms = build()
    print("free variables: %d ; monomials: %d" % (len(vars_), sum(len(c) for c in conds)))
    w = verify(exprs, syms)
    print("verification vs bgrad.grads_own: max error %.2e  %s" % (w, "OK" if w < 1e-12 else "*** MISMATCH"))
    assert w < 1e-12

    print("\n=== CONTROL: no a11 restriction -- must find a survivor (family lives at a11=0) ===", flush=True)
    ok, nn, box = search(vars_, pos, conds, deps, None, 400000, log=None)
    if ok is False:
        LO, HI = box
        print("   survivor after %d nodes: " % nn + ", ".join("%s=%.3f" % (v, 0.5*(LO[k]+HI[k])) for k, v in enumerate(vars_) if 0.5*(LO[k]+HI[k]) > 1e-6))
    elif ok is True:
        print("   *** CONTROL FAILED: whole cube reported empty, but the family exists"); sys.exit(1)
    else:
        print("   inconclusive at cap (did not claim emptiness) -- acceptable")

    print("\n=== THEOREM: a11 >= %g is infeasible? ===" % delta, flush=True)
    ok, nn, box = search(vars_, pos, conds, deps, delta, maxnodes)
    dt = time.time() - t0
    if ok is True:
        print("\nPROVED (a11 >= %g): %d nodes, %.0fs.  No equilibrium has a11 >= %g." % (delta, nn, dt, delta))
    elif ok is False:
        LO, HI = box
        print("\nNOT PROVED: surviving point after %d nodes:" % nn)
        print("   " + ", ".join("%s=%.6f" % (v, 0.5*(LO[k]+HI[k])) for k, v in enumerate(vars_)))
    else:
        print("\nINCONCLUSIVE at %d nodes (%.0fs)" % (nn, dt))
