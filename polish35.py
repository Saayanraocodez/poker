"""(3, 5)-Kuhn: polish MCCFR profiles into equilibria, looking for ones in which P1 BETS.

Part 9's MCCFR has P1 opening up to 0.83 at (3, 5).  If an equilibrium with P1 betting exists it
lies in one of the 49 cells the exhaustive sweep could not decide (MASTER_DATA 16.11).  Steps:
  1. MCCFR (cfrGen, external sampling) on kuhnGen.Kuhn(3, 5): SEEDS x ITERS, cached in cfr35_<ITERS>.json;
  2. per seed: snap, classify, Newton + greedy support repair (certify.certify) until the float
     exploitability is < 1e-12;
  3. RATIONAL FIXING: the equilibrium components are positive-dimensional, so a Newton point is
     generically irrational.  Fix interior coordinates one at a time to a nearby simple rational,
     re-solving the rest by Newton after each, until every coordinate is rational;
  4. write the candidates (k35 coordinate order, exact fractions) to polish35_candidates.json for
     the INDEPENDENT exact verifier k35/xeq35.py (a different implementation of the game; Fractions;
     exploitability must be exactly 0).  Nothing here is a claim -- only xeq35's verdict is.
usage:  python polish35.py <iters> <seeds> <workers>"""
import os, sys, json, time
import numpy as np
from fractions import Fraction as Fr
import multiprocessing as mp
import kuhnGen as Q, cfrGen as CG, certify as C, poletest as PT

G = Q.Kuhn(3, 5)


def to_k35(p):
    """kuhnGen index -> k35 index (player, card, SGS situation)"""
    out = [None] * G.nparam
    for pl in range(3):
        for j in G.cards:
            for h in G.sit_hist[pl]:
                out[pl * 20 + (j - 1) * 4 + Q.SGS_SIT[pl][h] - 1] = p[G.pidx(pl, j, h)]
    return out


def p1_open(p):
    return [p[G.pidx(0, j, "")] for j in G.cards]


def _train(a):
    it, s = a
    return CG.train(G, it, seed=s).tolist()


DENOMS = (2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 48, 64, 96, 128, 256, 1024)


def rational_fix(p, S):
    """Fix interior coordinates to nearby simple rationals one at a time, re-solving the rest by
    Newton after each.  A coordinate that no rational can be fixed to without breaking the
    equilibrium is DETERMINED by the others: it stays a Newton variable.  -> (p, fixed, determined)"""
    p = np.array(p, float); free = list(S); determined = []; fixed = {}
    while free:
        cands = []
        for i in free:                                 # simplest nearby rational per coordinate
            for D in DENOMS:
                if abs(float(Fr(p[i]).limit_denominator(D)) - p[i]) < 1e-3:
                    cands.append((D, i)); break
        cands.sort(); progressed = False
        for D, i in cands:
            for D2 in [d for d in DENOMS if d >= D]:
                q = Fr(p[i]).limit_denominator(D2)
                r = p.copy(); r[i] = float(q); rest = [k for k in free + determined if k != i]
                r2 = C.newton(G, r, rest, iters=40)[0] if rest else r
                if float(np.abs(G.exploitability_bi(r2)).max()) < 1e-12:
                    p = r2; fixed[i] = q; free.remove(i); progressed = True; break
            if progressed: break
        if not progressed:
            determined += free; free = []
    return p, fixed, determined


def main():
    iters, nseed, nw = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    cache = "cfr35_%d.json" % iters
    if os.path.exists(cache):
        P = [np.array(x) for x in json.load(open(cache))]; print("(loaded %s)" % cache, flush=True)
    else:
        t = time.time()
        with mp.Pool(min(nw, nseed)) as pool:
            P = [np.array(x) for x in pool.map(_train, [(iters, s) for s in range(nseed)])]
        json.dump([x.tolist() for x in P], open(cache, "w"))
        print("MCCFR: %d seeds x %d iters in %.0fs" % (nseed, iters, time.time() - t), flush=True)
    out = []
    for s, p in enumerate(P):
        e0 = float(np.abs(G.exploitability_bi(p)).max())
        off, p0s, p1s, inter = C.classify(G, [p])
        q = PT.snap(G, p)
        r, S, e, rep = C.certify(G, q, inter)
        opn = p1_open(r)
        line = "seed %2d: MCCFR expl %.4f, P1 opens %s | polish: expl %.1e, |S| %d, %d repairs, P1 opens %s" % (
            s, e0, np.round(p1_open(p), 3).tolist(), e, len(S), rep, np.round(opn, 4).tolist())
        print(line, flush=True)
        if e >= 1e-12: continue
        if max(opn) < 1e-9:
            print("         -> P1 SILENT after polishing", flush=True); continue
        rp, fixed, det = rational_fix(r, S)
        # every coordinate as a rational: the fixed ones exactly, the rest (pure, off-path, determined)
        # rationalised -- whether the result is an equilibrium is for the exact verifier to say
        ex = [Fr(x).limit_denominator(1 << 16) for x in rp]
        for i, v in fixed.items(): ex[i] = v
        print("         -> %d fixed, %d determined; P1 opens %s" % (len(fixed), len(det), [str(ex[G.pidx(0, j, '')]) for j in G.cards]), flush=True)
        out.append({"seed": s, "k35": [str(x) for x in to_k35(ex)], "float_expl": e, "interior": S,
                    "fixed": sorted(fixed), "determined": det, "float_profile_k35": [float(x) for x in to_k35(list(rp))]})
    json.dump(out, open("polish35_candidates.json", "w"), indent=0)
    print("%d rational candidates with P1 betting -> polish35_candidates.json (verify with k35/xeq35.py)" % len(out), flush=True)


if __name__ == "__main__":
    main()
