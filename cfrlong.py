"""Open problem 5 (which equilibrium does CFR pick, and does it favour a seat?), part 1: long
ES-MCCFR runs with checkpoints.

cfr3p.train (the R14 solver) only returns the final average.  Here the same solver (cfr3p._es,
unchanged) runs for ITERS iterations per seed and saves the cumulative strategy sums at
log-spaced checkpoints, so that both the running average at each checkpoint AND the average over
each window between checkpoints (difference of sums) can be measured afterwards (cfrlong_an.py).

usage:  python cfrlong.py [iters] [nseed] [workers] [seed0]   -> cfrlong_<iters>.npz
"""
import sys, time
import numpy as np
from multiprocessing import Pool
import cfr3p as C


def checkpoints(iters):
    out = sorted({int(round(10 ** e)) for e in np.arange(3, np.log10(iters) + 1e-9, 0.25)} | {iters})
    return [c for c in out if c <= iters]


def run(args):
    iters, seed = args
    rng = np.random.default_rng(seed)
    regret = np.zeros((C.NI, 2)); strat = np.zeros((C.NI, 2))
    cps = checkpoints(iters); S = np.zeros((len(cps), C.NI, 2)); j = 0
    nd = len(C.DEALS); t0 = time.time()
    for it in range(1, iters + 1):
        cards = C.DEALS[rng.integers(nd)]
        for trav in (0, 1, 2):
            C._es("", cards, trav, regret, strat, rng)
        if it == cps[j]:
            S[j] = strat; j += 1
    return seed, S, regret, time.time() - t0


def main():
    iters = int(float(sys.argv[1])) if len(sys.argv) > 1 else 10 ** 7
    nseed = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    nw = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    seed0 = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    seeds = list(range(seed0, seed0 + nseed))
    with Pool(nw) as pool:
        res = pool.map(run, [(iters, s) for s in seeds], chunksize=1)
    np.savez_compressed("cfrlong_%d.npz" % iters, seeds=np.array([r[0] for r in res]),
                        S=np.array([r[1] for r in res]), regret=np.array([r[2] for r in res]),
                        cps=np.array(checkpoints(iters)), secs=np.array([r[3] for r in res]))
    print("done: %d seeds x %d iterations, %.0f s per seed (mean)" % (nseed, iters, np.mean([r[3] for r in res])))


if __name__ == "__main__":
    main()
