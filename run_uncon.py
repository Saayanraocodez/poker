import numpy as np, eqtools as E, srch, sys, time
from multiprocessing import Pool

def one(seed):
    rng = np.random.default_rng(seed)
    mode = seed % 3
    if mode == 0:   p0 = rng.random(48)
    elif mode == 1: p0 = rng.integers(0, 2, 48).astype(float)
    else:           p0 = rng.choice([0.0, 0.5, 1.0], 48)
    p = srch.polish(p0)
    p = srch.newton_polish(p)
    g = E.nashgap(p)
    return (g, p)

if __name__ == "__main__":
    n = int(sys.argv[1]); t0 = time.time()
    with Pool(14) as pool:
        res = pool.map(one, range(n), chunksize=8)
    ok = [(g, p) for g, p in res if g < 1e-11]
    print("starts %d  converged %d  time %.1fs" % (n, len(ok), time.time() - t0))
    gs = np.array([g for g, _ in res])
    print("gap quantiles", np.quantile(gs, [0, .1, .25, .5, .75, .9, 1]))
    np.save("uncon_eq.npy", np.array([p for _, p in ok]) if ok else np.zeros((0, 48)))
    np.save("uncon_all.npy", np.array([p for _, p in res]))
    np.save("uncon_gap.npy", gs)
