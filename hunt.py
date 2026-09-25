"""
Look for equilibria OUTSIDE the Szafron-Gibson-Sturtevant family.

The earlier enumeration only explored support patterns near one CFR profile, so
it could not find an equilibrium in a different basin.  Here we restart Newton
on the indifference system from RANDOM support patterns and random starting
points, which samples the whole space rather than one neighbourhood.

Two screens, in order of strength:

  1. UTILITIES.  Every family member pays exactly
        u1 = -k(1/2+beta),  u2 = -k/2,  u3 = k(1+beta),   beta = max(b11,b21).
     An equilibrium whose payoffs violate this is outside the family, whatever
     its coordinates look like.  This is behavioural, so it cannot be fooled by
     a different labelling of off-path coordinates.

  2. P1 SILENCE.  The family requires a_j1 = 0 for every card.  An equilibrium
     in which P1 bets with positive probability is outside it by construction.
"""
import json, multiprocessing as mp, time
import numpy as np
import kuhn3p as K, family as F, certify as C, poletest as PT, kuhnGen as Q

I = K.NAME_IDX
g = Q.Kuhn(3, 4)
PERM = np.empty(48, int)
for _pl in range(3):
    for _j in range(1, 5):
        for _h, _k in Q.SGS_SIT[_pl].items():
            PERM[I["%s%d%d" % ("abc"[_pl], _j, _k)]] = g.pidx(_pl, _j, _h)


def random_support(rng, force_p1_bet=False):
    """Random 0 / 1 / interior assignment, in kuhnGen coordinates."""
    p = np.zeros(g.nparam)
    inter = []
    for i in range(g.nparam):
        u = rng.random()
        if u < 0.42:
            p[i] = 0.0
        elif u < 0.62:
            p[i] = 1.0
        else:
            p[i] = rng.uniform(0.05, 0.95)
            inter.append(i)
    if force_p1_bet:
        j = int(rng.integers(1, 5))
        i = g.pidx(0, j, "")
        p[i] = rng.uniform(0.05, 0.95)
        if i not in inter:
            inter.append(i)
    return p, sorted(inter)


def one(args):
    seed, force = args
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(60):
        p0, inter = random_support(rng, force)
        r, h = C.newton(g, p0, inter, iters=30)
        e = float(np.abs(g.exploitability_bi(r)).max())
        if e < 1e-12:
            q = r[PERM]                               # kuhn3p ordering
            u = K.utilities(q)
            beta = max(q[I["b11"]], q[I["b21"]])
            pred = np.array([-K.KAPPA * (0.5 + beta), -K.KAPPA / 2,
                             K.KAPPA * (1 + beta)])
            out.append(dict(expl=e, u=u.tolist(), udev=float(np.abs(u - pred).max()),
                            u2dev=float(abs(u[1] + K.KAPPA / 2)),
                            p1bet=float(max(q[I["a%d1" % j]] for j in (1, 2, 3, 4))),
                            profile=q.tolist()))
    return out


def main():
    NJOB, t = 420, time.time()
    jobs = [(s, False) for s in range(NJOB)] + [(10000 + s, True) for s in range(NJOB)]
    with mp.Pool(max(1, mp.cpu_count() - 1)) as pool:
        res = [x for chunk in pool.map(one, jobs) for x in chunk]
    print("%d random restarts (%d unforced + %d forcing P1 to bet) in %.0fs"
          % (len(jobs) * 60, NJOB * 60, NJOB * 60, time.time() - t))
    print("   certified exact equilibria found: %d\n" % len(res))
    if not res:
        return
    ud = np.array([r["udev"] for r in res])
    u2 = np.array([r["u2dev"] for r in res])
    pb = np.array([r["p1bet"] for r in res])
    print("SCREEN 1 -- utilities against the family closed form")
    print("   max |u - family form| over all found equilibria : %.3e" % ud.max())
    print("   max |u2 + kappa/2|                              : %.3e" % u2.max())
    print("   equilibria violating the closed form (>1e-9)    : %d" % int((ud > 1e-9).sum()))
    print("\nSCREEN 2 -- does P1 ever bet?")
    print("   max P1 opening probability over all found       : %.3e" % pb.max())
    print("   equilibria with P1 betting (>1e-6)              : %d" % int((pb > 1e-6).sum()))
    odd = [r for r in res if r["udev"] > 1e-9 or r["p1bet"] > 1e-6]
    if odd:
        print("\n   *** CANDIDATES OUTSIDE THE FAMILY: %d ***" % len(odd))
        for r in sorted(odd, key=lambda z: -z["udev"])[:6]:
            print("      expl %.1e  u=%s  udev %.2e  P1 bet %.4f"
                  % (r["expl"], np.round(r["u"], 6), r["udev"], r["p1bet"]))
        json.dump(odd[:50], open("outside_family.json", "w"))
    else:
        print("\n   No equilibrium found outside the family.")
    b = np.array([max(np.array(r["profile"])[I["b11"]],
                      np.array(r["profile"])[I["b21"]]) for r in res])
    print("\n   beta range over found equilibria: [%.4f, %.4f]  (family allows [0, 0.25])"
          % (b.min(), b.max()))
    print("   distinct utility vectors (rounded to 1e-6): %d"
          % len({tuple(np.round(r["u"], 6)) for r in res}))


if __name__ == "__main__":
    main()
