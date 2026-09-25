"""
Q5: does MCCFR -- the algorithm SGS used to discover the family -- select a
particular member of it, and if so which?

Order of operations follows the task list exactly: exploitability FIRST, family
membership SECOND, and no interpretation of anything until both are in hand.
"""
import json
import multiprocessing as mp
import time

import numpy as np

import cfr3p as C
import kuhn3p as K
import family as F

I = K.NAME_IDX
ITERS = 1000000
NSEED = 150


def run_one(seed):
    p = C.train(ITERS, seed=seed)
    e = K.exploitability(p)
    return seed, p.tolist(), e.tolist()


def main():
    t0 = time.time()
    with mp.Pool(processes=max(1, mp.cpu_count() - 1)) as pool:
        out = pool.map(run_one, range(NSEED))
    dt = time.time() - t0
    P = np.array([o[1] for o in out])
    E = np.array([o[2] for o in out])

    rec = dict(iters=ITERS, nseed=NSEED, seconds=dt,
               profiles=P.tolist(), exploitability=E.tolist())
    with open("cfr_sweep.json", "w") as f:
        json.dump(rec, f)

    print("=" * 78)
    print("STEP 0.  EXPLOITABILITY FIRST (%d seeds x %d iters, %.0fs)"
          % (NSEED, ITERS, dt))
    print("=" * 78)
    mx = E.max(axis=1)
    print("   max_i (BR_i - u_i) per seed:")
    print("      min %.6f   median %.6f   mean %.6f   max %.6f"
          % (mx.min(), np.median(mx), mx.mean(), mx.max()))
    for q in (50, 75, 90, 100):
        print("      %3d%% of seeds below %.6f" % (q, np.percentile(mx, q)))
    print("   per player (mean): P1 %.6f  P2 %.6f  P3 %.6f" % tuple(E.mean(axis=0)))
    print("   kappa = %.6f, so median exploitability is %.1f%% of kappa"
          % (K.KAPPA, 100 * np.median(mx) / K.KAPPA))

    print("\n" + "=" * 78)
    print("STEP 1.  IS THE OUTPUT IN THE FAMILY?")
    print("=" * 78)
    names = ["b11", "b21", "b23", "b32", "c11", "c33", "c34"]
    proj = {n: P[:, I[n]] for n in names}
    beta = np.maximum(proj["b11"], proj["b21"])
    print("   Table 2/3 parameters that should be pinned (mean +- sd over seeds):")
    for n, want in (("a11", 0.), ("a21", 0.), ("a31", 0.), ("a41", 0.),
                    ("a33", .5), ("b22", 0.), ("b31", 0.), ("b34", 0.),
                    ("c22", 0.), ("c23", 0.), ("c31", 0.), ("c32", 0.),
                    ("c41", 1.)):
        v = P[:, I[n]]
        print("      %-4s want %.2f   got %.4f +- %.4f   max dev %.4f"
              % (n, want, v.mean(), v.std(), np.abs(v - want).max()))
    print("\n   Table 3 dependent relations (should hold identically):")
    b33w = np.array([F.b33_of(a, b, c) for a, b, c in
                     zip(proj["b11"], proj["b21"], proj["b23"])])
    print("      b41 vs 2(b11+b21):  mean |dev| %.4f  max %.4f"
          % (np.abs(P[:, I["b41"]] - 2 * (proj["b11"] + proj["b21"])).mean(),
             np.abs(P[:, I["b41"]] - 2 * (proj["b11"] + proj["b21"])).max()))
    print("      c21 vs 1/2 - c11 :  mean |dev| %.4f  max %.4f"
          % (np.abs(P[:, I["c21"]] - (0.5 - proj["c11"])).mean(),
             np.abs(P[:, I["c21"]] - (0.5 - proj["c11"])).max()))
    print("      b33 vs Table 3    :  mean |dev| %.4f  max %.4f"
          % (np.abs(P[:, I["b33"]] - b33w).mean(),
             np.abs(P[:, I["b33"]] - b33w).max()))
    print("\n   Table 3 inequality constraints:")
    print("      b11 <= 1/4: %d/%d    b21 <= 1/4: %d/%d    b11 <= b21: %d/%d"
          % ((proj["b11"] <= .25 + .02).sum(), NSEED,
             (proj["b21"] <= .25 + .02).sum(), NSEED,
             (proj["b11"] <= proj["b21"] + .02).sum(), NSEED))
    lo = 0.5 - proj["b32"]
    hi = np.array([F.b32_max(a, b) for a, b in zip(proj["b11"], proj["b21"])]) - proj["b32"]
    inwin = (proj["c33"] >= lo - .02) & (proj["c33"] <= hi + .02)
    print("      c33 inside its Table 3 window (+-0.02): %d/%d" % (inwin.sum(), NSEED))

    print("\n" + "=" * 78)
    print("STEP 2-3.  DISTRIBUTION AND CONCENTRATION")
    print("=" * 78)
    print("   param    mean      sd        min       25%%       50%%       75%%       max")
    for n, v in list(proj.items()) + [("beta", beta)]:
        print("   %-7s %8.4f  %8.4f  %8.4f  %8.4f  %8.4f  %8.4f  %8.4f"
              % (n, v.mean(), v.std(), v.min(), np.percentile(v, 25),
                 np.median(v), np.percentile(v, 75), v.max()))
    print("\n   beta concentration: sd %.4f over a valid range of [0, 0.25]"
          % beta.std())
    print("   beta at the extremes: %d seeds < 0.02, %d seeds > 0.23"
          % ((beta < .02).sum(), (beta > .23).sum()))

    print("\n" + "=" * 78)
    print("STEP 4.  WHERE IN THE WINDOW DOES c33 LAND?")
    print("=" * 78)
    w = hi - lo
    ok = w > 1e-6
    frac = np.full(NSEED, np.nan)
    frac[ok] = (proj["c33"][ok] - lo[ok]) / w[ok]
    good = np.isfinite(frac)
    print("   position of c33 in [lo, hi], as a fraction (0 = lower pole,")
    print("   1 = upper pole, 1/3 = the properness point lo + w/3):")
    print("      n=%d usable seeds   mean %.4f   sd %.4f   median %.4f"
          % (good.sum(), frac[good].mean(), frac[good].std(), np.median(frac[good])))
    for lbl, a, b in (("near lower pole  (<0.10)", -9, .10),
                      ("properness band  (0.23-0.43)", .23, .43),
                      ("middle           (0.43-0.90)", .43, .90),
                      ("near upper pole  (>0.90)", .90, 9)):
        print("      %-30s %3d / %d" % (lbl, ((frac[good] > a) & (frac[good] <= b)).sum(),
                                        good.sum()))
    print("   distance to each hypothesis (mean |frac - x|):")
    for lbl, x in (("lower pole 0", 0.), ("properness 1/3", 1 / 3),
                   ("midpoint 1/2", .5), ("upper pole 1", 1.)):
        print("      %-18s %.4f" % (lbl, np.abs(frac[good] - x).mean()))

    print("\n" + "=" * 78)
    print("STEP 5.  DOES IT LAND ON THE REFINED FACE (b32 = 0, c34 = 0)?")
    print("=" * 78)
    for n in ("b32", "c34"):
        v = proj[n]
        print("   %-4s: mean %.4f  median %.4f  frac < 0.02: %d/%d  frac < 0.05: %d/%d"
              % (n, v.mean(), np.median(v), (v < .02).sum(), NSEED,
                 (v < .05).sum(), NSEED))
    print("\n   reach of the off-path sets in the CFR output (median over seeds):")
    R = np.array([K.reach(p) for p in P])
    for n in ("b32", "c33", "c34", "c44"):
        print("      %-4s %.3e" % (n, np.median(R[:, I[n]])))
    print("\n[cfr_sweep.json written]")


if __name__ == "__main__":
    main()
