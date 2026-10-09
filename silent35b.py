"""(3, 5) P1-silent equilibria, step 2 (fixes silent35's polish, which judged the FULL-game
exploitability -- dominated by P1's undeterred opening gain -- and so repaired every support away).
For each restricted MCCFR profile (cfr35_silent_*.json):
  1. Newton on the restricted interior support (P1's openings fixed at 0, off-path coordinates as they are);
  2. judge the CHECK-SUBGAME: P2's and P3's full-game exploitability, and P1's exploitability among
     plans that never open (per card: the 8 plans of situations 2-4 with situation 1 at 0);
  3. deterrence: minimise P1's best opening gain max_j du_1/da_j1 over the 15 responses to a bet.
A P1-silent Nash equilibrium needs 2 = 0 and 3 <= 0.
usage:  python silent35b.py <cache json> [starts]"""
import sys, json, itertools
import numpy as np
import kuhnGen as Q, certify as C, poletest as PT
from silent35_deter import gains, best_deterrence, OPEN, OFF

G = Q.Kuhn(3, 5)


def p1_restricted_expl(p):
    """P1's gain from deviating among plans that never open"""
    q = np.empty(G.nparam + 1); q[:G.nparam] = p; q[G.dummy] = 1.0
    u1 = G.utilities(p)[0]; tot = 0.0; ns = G.nsit[0]
    for j in G.cards:
        si, sa, sp = G.sub(0, j)
        own = [G.offset[0] + (j - 1) * ns + s for s in range(ns)]
        best = None
        for bits in itertools.product((0.0, 1.0), repeat=ns):
            if bits[G.sit[(0, "")]] != 0.0: continue           # never open
            qq = q.copy()
            for i, b in zip(own, bits): qq[i] = b
            v = G.kappa * float((np.where(sa, qq[si], 1.0 - qq[si]).prod(axis=1) * sp).sum())
            best = v if best is None or v > best else best
        tot += best
    return tot - u1


if __name__ == "__main__":
    P = [np.array(x) for x in json.load(open(sys.argv[1]))]
    starts = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    rng = np.random.default_rng(0); out = []
    for s, p in enumerate(P):
        off, p0s, p1s, inter = C.classify(G, [p])
        inter = [i for i in inter if i not in OPEN and i not in OFF]
        q = PT.snap(G, p)
        q[OPEN] = 0.0
        r, h = C.newton(G, q, inter, iters=60)
        ex = G.exploitability_bi(r); e1r = p1_restricted_expl(r)
        g, y = best_deterrence(r, starts, rng)
        rr = r.copy(); rr[OFF] = y; exf = G.exploitability_bi(rr)
        print("seed %2d: |S| %2d  Newton |F| %.1e | check-subgame expl: P1(no-open) %.1e  P2 %.1e  P3 %.1e | best deterrence: "
              "max opening gain %+.3e -> full expl %s" % (s, len(inter), h[-1] if h else 0, e1r, ex[1], ex[2], g,
                                                         ["%.1e" % v for v in exf]), flush=True)
        out.append({"seed": s, "interior": inter, "newton": h[-1] if h else 0, "sub_expl": [e1r, ex[1], ex[2]],
                    "max_gain": g, "profile": rr.tolist(), "full_expl": exf.tolist()})
    json.dump(out, open("silent35b.json", "w"))
    ok = [o for o in out if max(o["sub_expl"]) < 1e-12]
    print("check-subgame equilibria (float): %d of %d; of those, deterrable (max gain < 0): %d" % (
        len(ok), len(out), sum(1 for o in ok if o["max_gain"] < 0)))
