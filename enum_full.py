"""
Step 3: pruned support enumeration, with HONEST coverage reporting.

Pruning applied, in order:
  1. iterated conditional dominance  -> 48 coords down to 26 free
  2. branch on P1's opening pattern  -> 81 branches
  3. reachability inside each branch -> unreachable coords need no branching
Total surviving space is still ~1.1e12, so this is a BOUNDED search: branches
small enough are enumerated exhaustively, the rest are sampled, and the fraction
covered is reported.  A null result here is evidence, not proof.
"""
import itertools, json, multiprocessing as mp, time
import numpy as np
import kuhn3p as K, kuhnGen as Q, certify as C, family as F

g = Q.Kuhn(3, 4)
I = K.NAME_IDX
PERM = np.empty(48, int)
for _pl in range(3):
    for _j in range(1, 5):
        for _h, _k in Q.SGS_SIT[_pl].items():
            PERM[I["%s%d%d" % ("abc"[_pl], _j, _k)]] = g.pidx(_pl, _j, _h)
D = json.load(open("iterdom.json"))
FIXED = {int(k): v for k, v in D["fixed"].items()}
FREE = D["free"]
A1 = [I["a%d1" % j] for j in (1, 2, 3, 4)]
REST = [i for i in FREE if i not in A1]
BUDGET = 4000                     # hypotheses per branch


def branch(args):
    pat, seed = args
    rng = np.random.default_rng(seed)
    base = np.full(48, 0.5)
    for i, v in FIXED.items():
        base[i] = v
    for i, v in zip(A1, pat):
        base[i] = v
    r = K.reach(base)
    live = [i for i in REST if r[i] > 1e-12]
    inter0 = [i for i, v in zip(A1, pat) if 0 < v < 1]
    total = 3 ** len(live)
    exhaustive = total <= BUDGET
    hyps = (itertools.product((0.0, 0.5, 1.0), repeat=len(live)) if exhaustive
            else (tuple(rng.choice([0.0, 0.5, 1.0], len(live))) for _ in range(BUDGET)))
    found, tried = [], 0
    for h in hyps:
        tried += 1
        p = base.copy()
        S = list(inter0)
        for i, v in zip(live, h):
            p[i] = v
            if v == 0.5:
                S.append(i)
        pg = np.empty(48)
        pg[PERM] = p                                   # to kuhnGen ordering
        rr, _ = C.newton(g, pg, S, iters=20)
        if float(np.abs(g.exploitability_bi(rr)).max()) < 1e-12:
            q = rr[PERM]
            u = K.utilities(q)
            beta = max(q[I["b11"]], q[I["b21"]])
            pred = np.array([-K.KAPPA * (0.5 + beta), -K.KAPPA / 2, K.KAPPA * (1 + beta)])
            found.append(dict(udev=float(np.abs(u - pred).max()),
                              p1bet=float(max(q[I["a%d1" % j]] for j in (1, 2, 3, 4))),
                              u=u.tolist()))
    return dict(pat=pat, live=len(live), total=total, tried=tried,
                exhaustive=exhaustive, found=found)


def main():
    pats = list(itertools.product((0.0, 0.5, 1.0), repeat=4))
    t = time.time()
    with mp.Pool(max(1, mp.cpu_count() - 1)) as pool:
        res = pool.map(branch, [(p, 100 + i) for i, p in enumerate(pats)])
    print("81 branches in %.0fs\n" % (time.time() - t))
    tot_space = sum(r["total"] for r in res)
    tot_tried = sum(r["tried"] for r in res)
    nfound = sum(len(r["found"]) for r in res)
    nex = sum(1 for r in res if r["exhaustive"])
    print("   branches enumerated exhaustively : %d / 81" % nex)
    print("   hypotheses tested                : %d of %.3e  (%.2e of the space)"
          % (tot_tried, tot_space, tot_tried / tot_space))
    print("   exact equilibria certified       : %d\n" % nfound)
    allf = [f for r in res for f in r["found"]]
    if allf:
        ud = np.array([f["udev"] for f in allf])
        pb = np.array([f["p1bet"] for f in allf])
        print("   max |u - family closed form|     : %.3e" % ud.max())
        print("   equilibria violating it (>1e-9)  : %d" % int((ud > 1e-9).sum()))
        print("   max P1 opening probability       : %.3e" % pb.max())
        print("   equilibria with P1 betting       : %d" % int((pb > 1e-6).sum()))
        odd = [f for f in allf if f["udev"] > 1e-9 or f["p1bet"] > 1e-6]
        if odd:
            print("\n   *** OUTSIDE THE FAMILY: %d ***" % len(odd))
            for f in sorted(odd, key=lambda z: -z["udev"])[:8]:
                print("      u=%s  udev %.2e  P1 bet %.4f"
                      % (np.round(f["u"], 6), f["udev"], f["p1bet"]))
            json.dump(odd, open("outside_family.json", "w"))
        else:
            print("\n   Every certified equilibrium lies in the family.")
    print("\n   Branches where P1 bets (a_j1 > 0 for some j):")
    nb = [r for r in res if any(v > 0 for v in r["pat"])]
    print("      %d branches, %d hypotheses tested, %d equilibria found"
          % (len(nb), sum(r["tried"] for r in nb), sum(len(r["found"]) for r in nb)))


if __name__ == "__main__":
    main()
