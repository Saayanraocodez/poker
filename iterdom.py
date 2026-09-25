"""
Step 2: ITERATED conditional dominance.  Fixing a dominated action can make
another action dominated that was not before, so repeat until nothing changes.
Coordinates already fixed are held at their forced values while scanning.
"""
import json
import numpy as np
import kuhn3p as K

NP, EPS = 48, 1e-3


def adv(p, i, owner):
    r = K.reach(p)[i]
    return None if r < 1e-15 else K.exact_coord_derivative(p, i)[owner] / r


def extremum(i, sign, fixed, restarts=25, seed=0):
    owner = i // 16
    free = [k for k in range(NP) if k // 16 != owner and k not in fixed]
    rng = np.random.default_rng(seed + i * 7919 + (0 if sign > 0 else 3))
    best = -np.inf
    for _ in range(restarts):
        p = np.clip(rng.random(NP), EPS, 1 - EPS)
        for k, v in fixed.items():
            p[k] = np.clip(v, EPS, 1 - EPS)
        prev = None
        for _s in range(12):
            for k in free:
                p[k] = EPS
                a = adv(p, i, owner)
                lo = sign * a if a is not None else -np.inf
                p[k] = 1 - EPS
                a = adv(p, i, owner)
                hi = sign * a if a is not None else -np.inf
                p[k] = (1 - EPS) if hi >= lo else EPS
            a = adv(p, i, owner)
            v2 = sign * a if a is not None else -np.inf
            if prev is not None and abs(v2 - prev) < 1e-13:
                break
            prev = v2
        best = max(best, v2)
    return sign * best


def main():
    d = json.load(open("dominance.json"))
    fixed = {i: 0.0 for i in d["fix0"]}
    fixed.update({i: 1.0 for i in d["fix1"]})
    print("round 0: %d fixed, %d free" % (len(fixed), NP - len(fixed)))
    for rnd in range(1, 8):
        new = {}
        for i in range(NP):
            if i in fixed:
                continue
            mx = extremum(i, +1, fixed)
            if mx < -1e-12:
                new[i] = 0.0
                continue
            mn = extremum(i, -1, fixed)
            if mn > 1e-12:
                new[i] = 1.0
        if not new:
            print("round %d: nothing new -- fixed point reached" % rnd)
            break
        for i, v in new.items():
            fixed[i] = v
        print("round %d: +%d newly dominated (%s) -> %d fixed, %d free"
              % (rnd, len(new), " ".join("%s=%d" % (K.PARAM_NAME[i], v) for i, v in new.items()),
                 len(fixed), NP - len(fixed)))
    free = [i for i in range(NP) if i not in fixed]
    print("\n   FINAL: %d fixed by iterated dominance, %d free" % (len(fixed), len(free)))
    print("   free: %s" % " ".join(K.PARAM_NAME[i] for i in free))
    print("   search space 3^%d = %.3e" % (len(free), 3.0 ** len(free)))
    json.dump({"fixed": {str(k): v for k, v in fixed.items()}, "free": free},
              open("iterdom.json", "w"))


if __name__ == "__main__":
    main()
