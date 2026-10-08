"""(3, 5): where do ALL the MCCFR seeds go?  polish35's greedy support repair lost 13 of 20 seeds.
Here every seed gets (a) Newton on the CERTIFIED equilibrium's support (17 interior coordinates, its
pure values), started from the seed's own interior values, and if that fails (b) a distance-ordered
support search around the seed's own MCCFR reading (certify45's method).  Distinct float-certified
equilibria are reported by support and P1 behaviour.
usage:  python q2_polish35.py <budget per seed>"""
import sys, json, itertools
import numpy as np
import kuhnGen as Q, certify as C, poletest as PT

G = Q.Kuhn(3, 5)
OPEN = [G.pidx(0, j, "") for j in G.cards]


def distance_ordered(k, budget):
    seen = 0
    for d in range(k + 1):
        for flip in itertools.combinations(range(k), d):
            m = [1] * k
            for i in flip: m[i] = 0
            yield tuple(m); seen += 1
            if seen >= budget: return


if __name__ == "__main__":
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    P = [np.array(x) for x in json.load(open("cfr35_10000000.json"))]
    cand = json.load(open("polish35_candidates.json"))[0]
    # the certified support in kuhnGen order (polish35 stored it in kuhnGen order as "interior")
    S0 = cand["interior"]
    k35 = cand["float_profile_k35"]                      # the certified profile, k35 order -> kuhnGen order
    cert = np.zeros(G.nparam)
    for pl in range(3):
        for j in G.cards:
            for h in G.sit_hist[pl]:
                cert[G.pidx(pl, j, h)] = k35[pl * 20 + (j - 1) * 4 + Q.SGS_SIT[pl][h] - 1]
    found = []
    for s, p in enumerate(P):
        # (a) Newton on the certified support: its pure values, the seed's own interior values
        q = cert.copy(); q[S0] = p[S0]
        r, h = C.newton(G, q, S0, iters=60)
        e = float(np.abs(G.exploitability_bi(r)).max())
        how = "certified support"
        if e >= 1e-12:
            # (b) support search around the seed's own reading
            amb = [i for i in range(G.nparam) if 0.005 < p[i] < 0.995]
            q0 = p.copy()
            for i in range(G.nparam):
                if i not in amb: q0[i] = 1.0 if p[i] > 0.5 else 0.0
            best = None
            for mask in distance_ordered(len(amb), budget):
                q = q0.copy(); S = []
                for c, bit in zip(amb, mask):
                    if bit: S.append(c)
                    else: q[c] = 1.0 if p[c] > 0.5 else 0.0
                rr, hh = C.newton(G, q, S, iters=25)
                ee = float(np.abs(G.exploitability_bi(rr)).max())
                if best is None or ee < best[0]: best = (ee, rr, S)
                if ee < 1e-12: break
            e, r, S = best; how = "support search (%d ambiguous)" % len(amb)
        opn = [r[i] for i in OPEN]
        c1, c2 = r[G.pidx(2, 1, "KK")], r[G.pidx(2, 2, "KK")]
        print("seed %2d: %-34s expl %.1e  P1 opens %s  c11 %.4f c21 %.4f (sum %.6f)" % (
            s, how, e, np.round(opn, 4).tolist(), c1, c2, c1 + c2), flush=True)
        if e < 1e-12: found.append({"seed": s, "how": how, "profile": r.tolist(), "p1": opn})
    json.dump(found, open("q2_polish35.json", "w"))
    sig = {}
    for f in found:
        k = tuple(np.round(f["p1"], 6))
        sig.setdefault(k, []).append(f["seed"])
    print("%d of %d seeds float-certified; distinct P1 behaviours: %d" % (len(found), len(P), len(sig)))
    for k, v in sig.items(): print("   P1 opens %s : seeds %s" % (list(k), v))
