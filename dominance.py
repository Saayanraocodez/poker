"""
Step 1 of pruned support enumeration: find every action that is CONDITIONALLY
DOMINATED, i.e. whose sign is the same for every strategy of everyone else.

du_owner/dx is multilinear in the other 47 coordinates, so it is affine in each
one separately.  Coordinate ascent therefore converges to a local optimum in a
single sweep per coordinate, and random restarts give the global optimum with
high confidence.

  max over all others < 0  ->  the aggressive action is always worse  -> fix 0
  min over all others > 0  ->  it is always better                    -> fix 1
  otherwise                ->  genuinely free; the search must branch on it
"""
import multiprocessing as mp, time, json
import numpy as np
import kuhn3p as K

NP = 48


EPS = 1e-3


def adv(p, i, owner):
    """Per-unit-reach advantage: the gain from the aggressive action GIVEN that
    the information set is actually reached.  Without this normalisation an
    unreachable set gives du/dx = 0 exactly, so no action ever looks dominated."""
    r = K.reach(p)[i]
    if r < 1e-15:
        return None
    return K.exact_coord_derivative(p, i)[owner] / r


def extremum(i, sign, restarts=20, seed=0):
    """sign=+1 maximises the conditional advantage, sign=-1 minimises it.
    Other coordinates are confined to [EPS, 1-EPS] so every set stays reached."""
    owner = i // 16
    others = [k for k in range(NP) if k // 16 != owner]
    rng = np.random.default_rng(seed + i * 7919 + (0 if sign > 0 else 3))
    best = -np.inf
    for _ in range(restarts):
        p = np.clip(rng.random(NP), EPS, 1 - EPS)
        prev = None
        for _sweep in range(12):
            for k in others:
                p[k] = EPS
                a = adv(p, i, owner)
                lo = sign * a if a is not None else -np.inf
                p[k] = 1 - EPS
                a = adv(p, i, owner)
                hi = sign * a if a is not None else -np.inf
                p[k] = (1 - EPS) if hi >= lo else EPS
            a = adv(p, i, owner)
            v = sign * a if a is not None else -np.inf
            if prev is not None and abs(v - prev) < 1e-13:
                break
            prev = v
        if v > best:
            best = v
    return sign * best


def one(i):
    return i, float(extremum(i, +1)), float(extremum(i, -1))


def main():
    t = time.time()
    with mp.Pool(max(1, mp.cpu_count() - 1)) as pool:
        res = pool.map(one, range(NP))
    print("dominance scan over all 48 coordinates in %.0fs\n" % (time.time() - t))
    fix0, fix1, free = [], [], []
    for i, mx, mn in sorted(res):
        if mx < -1e-12:
            fix0.append(i)
        elif mn > 1e-12:
            fix1.append(i)
        else:
            free.append(i)
    print("   always worse  -> fix to 0 : %2d  %s" % (len(fix0), " ".join(K.PARAM_NAME[i] for i in fix0)))
    print("   always better -> fix to 1 : %2d  %s" % (len(fix1), " ".join(K.PARAM_NAME[i] for i in fix1)))
    print("   genuinely free            : %2d  %s" % (len(free), " ".join(K.PARAM_NAME[i] for i in free)))
    print("\n   search space: 3^%d = %.3e  (was 3^48 = %.3e)"
          % (len(free), 3.0 ** len(free), 3.0 ** 48))
    # cross-check against the paper's Table 2
    T2 = {"a12": 0, "a13": 0, "a14": 0, "a24": 0, "a42": 1, "a43": 1, "a44": 1,
          "b12": 0, "b13": 0, "b14": 0, "b24": 0, "b42": 1, "b43": 1, "b44": 1,
          "c12": 0, "c13": 0, "c14": 0, "c24": 0, "c42": 1, "c43": 1, "c44": 1}
    agree = dis = 0
    notes = []
    for n, w in T2.items():
        i = K.NAME_IDX[n]
        got = 0 if i in fix0 else (1 if i in fix1 else None)
        if got == w:
            agree += 1
        else:
            dis += 1
            notes.append("%s: Table 2 says %d, dominance scan says %s" % (n, w, got))
    print("\n   vs the paper's Table 2 (21 values it calls necessary):")
    print("      confirmed by dominance : %d / 21" % agree)
    print("      NOT confirmed          : %d" % dis)
    for x in notes:
        print("         %s" % x)
    json.dump(dict(fix0=fix0, fix1=fix1, free=free), open("dominance.json", "w"))


if __name__ == "__main__":
    main()
