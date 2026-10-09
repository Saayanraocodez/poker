"""(3, 5): look for MORE betting equilibrium components (float exploration, decides nothing).
New MCCFR seeds (polish35._train, external sampling), each polished like q2_polish35: Newton on the
certified support (component I) from the seed's own interior values, else a distance-ordered support
search around the seed's own reading.  Float-certified equilibria (exploitability < 1e-12) are grouped
by P1's opening probabilities and by support; anything not matching I / II / III is flagged NEW and
must then be certified exactly (k35/cert35gen.py).
usage:  python explore35.py <iters> <first seed> <last seed+1> <workers> [budget]"""
import sys, json, time
import numpy as np
import multiprocessing as mp
import kuhnGen as Q, certify as C
import polish35 as P35
from q2_polish35 import distance_ordered

G = Q.Kuhn(3, 5)
OPEN = [G.pidx(0, j, "") for j in G.cards]
KNOWN = {"I": [0.1615, 0.1615, 0.0404, 0.0, 0.8478], "II": [0.3227, 0.0, 0.0365, 0.0, 0.8381]}


def polish(p, cert, S0, budget):
    q = cert.copy(); q[S0] = p[S0]
    r, h = C.newton(G, q, S0, iters=60)
    e = float(np.abs(G.exploitability_bi(r)).max())
    if e < 1e-12: return e, r, S0, "certified support"
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
    return best[0], best[1], best[2], "support search (%d ambiguous)" % len(amb)


if __name__ == "__main__":
    iters, s0, s1, nw = (int(a) for a in sys.argv[1:5])
    budget = int(sys.argv[5]) if len(sys.argv) > 5 else 300
    t = time.time()
    with mp.Pool(min(nw, s1 - s0)) as pool:
        P = [np.array(x) for x in pool.map(P35._train, [(iters, s) for s in range(s0, s1)])]
    json.dump([x.tolist() for x in P], open("cfr35_%d_s%d_%d.json" % (iters, s0, s1), "w"))
    print("MCCFR: seeds %d..%d x %d iters in %.0fs" % (s0, s1 - 1, iters, time.time() - t), flush=True)
    cand = json.load(open("polish35_candidates.json"))[0]
    S0 = cand["interior"]; k35 = cand["float_profile_k35"]
    cert = np.zeros(G.nparam)
    for pl in range(3):
        for j in G.cards:
            for h in G.sit_hist[pl]:
                cert[G.pidx(pl, j, h)] = k35[pl * 20 + (j - 1) * 4 + Q.SGS_SIT[pl][h] - 1]
    found = []
    for n, p in enumerate(P):
        s = s0 + n
        e, r, S, how = polish(p, cert, S0, budget)
        opn = [float(r[i]) for i in OPEN]
        tag = next((k for k, v in KNOWN.items() if np.allclose(opn, v, atol=2e-3)), None)
        if tag is None and e < 1e-12:
            tag = "III?" if abs(opn[0] - 0.1593) < 0.01 and abs(opn[0] - opn[1]) < 1e-6 else "NEW"
        print("seed %2d: %-34s expl %.1e  P1 opens %s  -> %s" % (s, how, e, np.round(opn, 4).tolist(), tag if e < 1e-12 else "not polished"), flush=True)
        if e < 1e-12:
            found.append({"seed": s, "how": how, "profile": r.tolist(), "p1": opn, "support": sorted(int(i) for i in S), "tag": tag})
    json.dump(found, open("explore35_s%d_%d.json" % (s0, s1), "w"))
    print("%d of %d seeds float-certified; tags: %s" % (len(found), len(P), sorted(f["tag"] for f in found)))
