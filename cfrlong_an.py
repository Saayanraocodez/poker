"""Analysis of cfrlong.py's checkpointed ES-MCCFR runs: does the average strategy converge to the
Nash set, and is the off-family locus of R14 an artefact of averaging?

For every seed and checkpoint t:
  * the running average  p(t) = S(t) normalised      (what R14 measured, at t = 10^6);
  * the WINDOW average   w(t) = (S(t) - S(t_prev)) normalised, the play of the window alone.
Each is measured by cfrfull_run.measure: exploitability, certified distance to the complete Nash
set (reread14.certify, = the distance by reread14b), nearest sub-family, beta, payoffs, a32.

usage:  python cfrlong_an.py cfrlong_100000000.npz [workers]  -> log_cfrlong_an.txt (stdout), cfrlong_an.json
"""
import sys, json
import numpy as np
from multiprocessing import Pool
import cfrfull_run as CR


def norm(S):
    tot = S.sum(axis=1)
    return np.where(tot > 0, S[:, 1] / np.where(tot > 0, tot, 1), 0.5)


def job(args):
    seed, S, cps = args
    run, win = {}, {}
    for j, t in enumerate(cps):
        run[int(t)] = CR.measure(norm(S[j]))
        if j:
            win[int(t)] = CR.measure(norm(S[j] - S[j - 1]))
    return int(seed), run, win


def main():
    z = np.load(sys.argv[1]); nw = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    cps = [int(c) for c in z["cps"]]
    with Pool(nw) as pool:
        res = pool.map(job, [(s, S, cps) for s, S in zip(z["seeds"], z["S"])], chunksize=1)
    json.dump([dict(seed=s, run=r, win=w) for s, r, w in res], open("cfrlong_an.json", "w"))
    show = [c for c in cps if c in (10 ** 4, 10 ** 5, 10 ** 6, 10 ** 7, 10 ** 8) or c == cps[-1]]
    print("ES-MCCFR, %d seeds; running average p(t) (what R14 measured at t = 1e6)" % len(res))
    print("      t      expl(med)   dist(med)   dist(max)   a32(med)   |b11-b21|(med)  sub A/B/C   beta(mean)")
    for t in show:
        m = [r[t] for _, r, _ in res]
        e = np.median([x["expl"] for x in m]); d = [x["dist"] for x in m]
        from collections import Counter
        c = Counter(x["sub"] for x in m)
        print("   %8.0e   %.2e    %.4f      %.4f      %.4f     %.4f          %2d/%2d/%2d    %.4f" % (
            t, e, np.median(d), max(d), np.median([x["a32"] for x in m]),
            np.median([abs(x["b11"] - x["b21"]) for x in m]), c["A"], c["B"], c["C"], np.mean([x["beta"] for x in m])))
    print("\nwindow averages (play between consecutive checkpoints, ~0.25 decade each)")
    print("      t      expl(med)   dist(med)   sub A/B/C   beta(mean)   beta sd across windows of one seed (median)")
    for t in show[1:]:
        m = [w[t] for _, _, w in res]
        from collections import Counter
        c = Counter(x["sub"] for x in m)
        print("   %8.0e   %.2e    %.4f      %2d/%2d/%2d    %.4f" % (
            t, np.median([x["expl"] for x in m]), np.median([x["dist"] for x in m]), c["A"], c["B"], c["C"], np.mean([x["beta"] for x in m])))
    # per seed: does the window sub-family change over the last 2 decades?
    late = [c for c in cps if c > 10 ** 6]
    sw = [len({w[t]["sub"] for t in late}) for _, _, w in res]
    bsd = [np.std([w[t]["beta"] for t in late]) for _, _, w in res]
    print("\nlast two decades (t > 1e6, %d windows per seed):" % len(late))
    print("   seeds whose window sub-family changes: %d / %d;  beta sd across a seed's windows: median %.4f"
          % (sum(s > 1 for s in sw), len(sw), np.median(bsd)))
    d6 = np.array([r[10 ** 6]["dist"] for _, r, _ in res]); d8 = np.array([r[cps[-1]]["dist"] for _, r, _ in res])
    print("   distance 1e6 -> %.0e: median %.4f -> %.4f;  ratio median %.3f  (1/sqrt(100) = 0.1)" % (cps[-1], np.median(d6), np.median(d8), np.median(d8 / d6)))
    print("[cfrlong_an.json written]")


if __name__ == "__main__":
    main()
