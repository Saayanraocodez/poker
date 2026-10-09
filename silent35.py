"""(3, 5)-Kuhn: are there Nash equilibria in which P1 NEVER bets?

MCCFR drifts to the betting equilibrium (polish35), so search the RESTRICTED game instead: P1's
opening coordinates a_j1 fixed to 0, everything else learned.  A restricted equilibrium is a
FULL-game equilibrium iff P1 gains nothing by opening -- which the full-game exploitability decides.
Steps: MCCFR with fixed coordinates (external sampling; a fixed information set is played at its
fixed probability and gets no regret), Newton + support repair on the restricted interior support,
then the FULL-game exploitability (P1's gain from opening shows up there).
usage:  python silent35.py <iters> <seeds> <workers>"""
import os, sys, json, time
import numpy as np
import multiprocessing as mp
import kuhnGen as Q, certify as C, poletest as PT

G = Q.Kuhn(3, 5)
FIXED = {G.pidx(0, j, ""): 0.0 for j in G.cards}          # P1 never opens


def _sigma(regret, i):
    r0 = regret[i, 0] if regret[i, 0] > 0.0 else 0.0
    r1 = regret[i, 1] if regret[i, 1] > 0.0 else 0.0
    s = r0 + r1
    return (0.5, 0.5) if s <= 0.0 else (r0 / s, r1 / s)


def _es(g, hist, cards, trav, regret, strat, rng):
    term, actor, _ = g.state(hist)
    if term:
        return g.payoff(cards, hist)[trav]
    i = g.pidx(actor, cards[actor], hist)
    pas, agg = g.actions(hist)
    if i in FIXED:
        p1 = FIXED[i]
        if actor == trav:
            v = 0.0
            if p1 < 1: v += (1 - p1) * _es(g, hist + pas, cards, trav, regret, strat, rng)
            if p1 > 0: v += p1 * _es(g, hist + agg, cards, trav, regret, strat, rng)
            return v
        return _es(g, hist + (agg if rng.random() < p1 else pas), cards, trav, regret, strat, rng)
    p0, p1 = _sigma(regret, i)
    if actor == trav:
        v0 = _es(g, hist + pas, cards, trav, regret, strat, rng)
        v1 = _es(g, hist + agg, cards, trav, regret, strat, rng)
        v = p0 * v0 + p1 * v1
        regret[i, 0] += v0 - v; regret[i, 1] += v1 - v
        return v
    strat[i, 0] += p0; strat[i, 1] += p1
    return _es(g, hist + (agg if rng.random() < p1 else pas), cards, trav, regret, strat, rng)


def train(a):
    iters, seed = a
    rng = np.random.default_rng(seed)
    regret = np.zeros((G.nparam, 2)); strat = np.zeros((G.nparam, 2))
    for _ in range(iters):
        cards = G.deals[rng.integers(G.ndeal)]
        for trav in range(3):
            _es(G, "", cards, trav, regret, strat, rng)
    tot = strat.sum(axis=1); p = np.full(G.nparam, 0.5); nz = tot > 0
    p[nz] = strat[nz, 1] / tot[nz]
    for i, v in FIXED.items(): p[i] = v
    return p.tolist()


def main():
    iters, nseed, nw = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    cache = "cfr35_silent_%d.json" % iters
    if os.path.exists(cache):
        P = [np.array(x) for x in json.load(open(cache))]
    else:
        t = time.time()
        with mp.Pool(min(nw, nseed)) as pool:
            P = [np.array(x) for x in pool.map(train, [(iters, s) for s in range(nseed)])]
        json.dump([x.tolist() for x in P], open(cache, "w"))
        print("restricted MCCFR (P1 never opens): %d seeds x %d iters in %.0fs" % (nseed, iters, time.time() - t), flush=True)
    res = []
    for s, p in enumerate(P):
        e0 = G.exploitability_bi(p)
        off, p0s, p1s, inter = C.classify(G, [p])
        inter = [i for i in inter if i not in FIXED]
        q = PT.snap(G, p)
        for i, v in FIXED.items(): q[i] = v
        # restricted polish: Newton + repair on the interior support, P1's openings held at 0
        r, S, e, rep = C.certify(G, q, inter)
        for i, v in FIXED.items(): assert r[i] == v
        ex = G.exploitability_bi(r)
        # P1's gain from opening alone: best response of P1 vs the profile
        line = ("seed %2d: MCCFR full-game expl %s | polished: full-game expl %s  |S| %d  repairs %d" %
                (s, np.round(e0, 4).tolist(), ["%.2e" % x for x in ex], len(S), rep))
        print(line, flush=True)
        res.append({"seed": s, "expl": ex.tolist(), "interior": S, "profile": r.tolist()})
    json.dump(res, open("silent35_results.json", "w"))
    full = [x for x in res if max(abs(v) for v in x["expl"]) < 1e-12]
    print("%d of %d seeds give a FULL-game equilibrium with P1 silent (float exploitability < 1e-12)" % (len(full), len(res)), flush=True)


if __name__ == "__main__":
    main()
