import multiprocessing as mp, time, json
import numpy as np
import kuhnGen as Q, cfrGen as CG, certify as C, poletest as PT, properness as PR

CONFIGS = [(3, 4, 800000, 4), (4, 5, 400000, 4)]

def _tr(a):
    n, N, it, s = a
    return CG.train(Q.Kuhn(n, N), it, seed=s).tolist()

def main():
    jobs = [(n, N, it, s) for n, N, it, ns in CONFIGS for s in range(ns)]
    t = time.time()
    with mp.Pool(min(8, mp.cpu_count() - 1)) as pool:
        raw = pool.map(_tr, jobs)
    print("CFR: %d profiles in %.0fs\n" % (len(raw), time.time() - t))
    out = {}
    k = 0
    for n, N, it, ns in CONFIGS:
        g = Q.Kuhn(n, N)
        P = [np.array(raw[k + i]) for i in range(ns)]
        k += ns
        off, p0s, p1s, inter = C.classify(g, P)
        print("=" * 70)
        print("(%d,%d): %d off-path, %d pure0, %d pure1, %d interior"
              % (n, N, len(off), len(p0s), len(p1s), len(inter)))
        best = min(P, key=lambda q: np.abs(g.exploitability_bi(q)).max())
        q = PT.snap(g, best)
        own = PT.owners(g); idx = np.array(inter)
        f0 = float(np.abs(g.gradient(q)[idx, own[idx]]).max())
        e0 = float(np.abs(g.exploitability_bi(q)).max())
        print("   CFR start : max|F| %.3e   exploitability %.3e" % (f0, e0))
        t0 = time.time()
        r, h = C.newton(g, q, inter, iters=30)
        e1 = np.abs(g.exploitability_bi(r))
        print("   Newton    : max|F| %.3e -> %.3e in %d steps (%.0fs)"
              % (h[0], h[-1], len(h), time.time() - t0))
        print("   result    : max exploitability %.3e" % e1.max())
        print("               per player %s" % np.round(e1, 12))
        if e1.max() < 1e-12:
            print("   *** EXACT EQUILIBRIUM CERTIFIED ***")
            pr = PR.analyse(g, r)
            print("   properness on the certified profile: off %d slack %d inert %d pinned %d"
                  " | d_free %d d_cond %d -> %s"
                  % (pr["off"], pr["slack"], pr["inert"], pr["pinned"],
                     pr["d_free"], pr["d_cond"], pr["verdict"]))
            if pr.get("solved"):
                print("               equal-cost solution in window: %s"
                      % pr["solved"]["in_window"])
        out["%d,%d" % (n, N)] = dict(profile=r.tolist(), expl=e1.tolist(),
                                     interior=inter, off=off)
    json.dump(out, open("certified.json", "w"))

if __name__ == "__main__":
    main()
