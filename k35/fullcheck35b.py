"""INDEPENDENT exact check of a full-game (3,5) emptiness certificate (see fullcheck35.py for the claim).

Independent of fullcheck35.py and of tree.py / kuhn3p.py: payoffs come from a direct simulation of the
betting (antes 1, one bet of 1, showdown among the players still in), plan classes are recomputed from
those payoffs, the certificate is re-parsed, and the search runs in the OTHER order: all P2 plan
combinations outside; for each, P1's five agents are assigned level by level and a branch is closed when
its exact bound  sum_l max_c sum_{j != l} (H_jl[a_j, c], or max_a H_jl[a, c] while unassigned)  is < 0;
each P3 agent decouples.  Integers only (numpy int64 under a 2^62 guard).
Plans: bits for situations 1..4:  P1 (open, KKB call, KBF call, KBC call);
P2 (K bet, B call, KKBF call, KKBC call);  P3 (KK bet, KB call, BF call, BC call).
usage:  python fullcheck35b.py <certificate.json>"""
import sys, json, itertools, time
import numpy as np
from fractions import Fraction as F
from math import lcm

CARDS = (1, 2, 3, 4, 5)


def bits(n):
    return ((n >> 3) & 1, (n >> 2) & 1, (n >> 1) & 1, n & 1)


def play(cards, p1, p2, p3):
    put = [1, 1, 1]; out = [False] * 3
    if p1[0]:                                        # P1 bets
        put[0] += 1
        if p2[1]: put[1] += 1                        # P2 calls the bet
        else: out[1] = True
        if (p3[3] if not out[1] else p3[2]):         # P3: after B,C uses BC; after B,F uses BF
            put[2] += 1
        else: out[2] = True
    elif p2[0]:                                      # K, P2 bets
        put[1] += 1
        if p3[1]: put[2] += 1                        # P3 calls (KB)
        else: out[2] = True
        if (p1[3] if not out[2] else p1[2]):         # P1: KBC or KBF
            put[0] += 1
        else: out[0] = True
    elif p3[0]:                                      # K K, P3 bets
        put[2] += 1
        if p1[1]: put[0] += 1                        # P1 calls (KKB)
        else: out[0] = True
        if (p2[3] if not out[0] else p2[2]):         # P2: KKBC or KKBF
            put[1] += 1
        else: out[1] = True
    live = [i for i in range(3) if not out[i]]
    w = max(live, key=lambda i: cards[i])
    pay = [-put[i] for i in range(3)]
    pay[w] += sum(put)
    return pay


def main(path):
    t0 = time.time()
    c = json.load(open(path))
    faces = {tuple(int(v) for v in k.split(",")): [int(x) for x in vals] for k, vals in c["faces"].items()}
    brs = [((int(b[0]), int(b[1])), int(b[2])) for b in c["brs"]]
    mu = {}
    for pl, cd, t, q in c["mu"]:
        mu[(int(pl), int(cd)), int(t)] = F(q)
    blocks = [(a, rho) for a in [(pl, cd) for pl in range(3) for cd in CARDS] for (b, rho) in brs if b == a]
    lam = {}
    for n, q in c["lam"]:
        a, rho = blocks[int(n) // 16]; lam[a, rho, int(n) % 16] = F(q)
    ce = {}
    for pl, cd, rho, t, q in c.get("ce", []):
        ce[(int(pl), int(cd)), int(rho), int(t)] = F(q)
    if any(v < 0 for v in list(mu.values()) + list(lam.values()) + list(ce.values())): raise SystemExit("negative multiplier")
    deals = list(itertools.permutations(CARDS, 3))
    P = {}
    for d in deals:
        for r in itertools.product(range(16), repeat=3):
            P[d, r] = play(d, bits(r[0]), bits(r[1]), bits(r[2]))
    dom = {(pl, cd): faces.get((pl, cd), list(range(16))) for pl in range(3) for cd in CARDS}
    rep = {}
    for (pl, cd), allowed in dom.items():
        seen = {}
        for p in allowed:
            key = tuple(tuple(P[d, tuple(r[:pl]) + (p,) + tuple(r[pl:])]) for d in deals if d[pl] == cd
                        for r in itertools.product(range(16), repeat=2))
            seen.setdefault(key, p)
        rep[(pl, cd)] = sorted(seen.values())

    if any(k[1] not in rep[k[0]] for k in ce): raise SystemExit("CE multiplier off a class representative")

    def term(d, r):
        v = F(0)
        for pl in range(3):
            a = (pl, d[pl])
            for t in range(16):
                m = mu.get((a, t))
                if m:
                    rt = list(r); rt[pl] = t
                    v += m * (P[d, r][pl] - P[d, tuple(rt)][pl])
            for (aa, rho, t), m in lam.items():
                if aa == a:
                    r1 = list(r); r1[pl] = rho; r2 = list(r); r2[pl] = t
                    v += m * (P[d, tuple(r1)][pl] - P[d, tuple(r2)][pl])
            for t in range(16):
                m = ce.get((a, r[pl], t))
                if m:
                    rt = list(r); rt[pl] = t
                    v += m * (P[d, r][pl] - P[d, tuple(rt)][pl])
        return v

    T = {}
    for d in deals:
        A, B, C = rep[(0, d[0])], rep[(1, d[1])], rep[(2, d[2])]
        T[d] = [[[term(d, (a, b, cc)) for cc in C] for b in B] for a in A]
    den = 1
    for d in T:
        for x in T[d]:
            for y in x:
                for v in y: den = lcm(den, v.denominator)
    G = {}; big = 0
    for d in T:
        ints = [[[int(v * den) for v in y] for y in x] for x in T[d]]
        big = max(big, max(abs(v) for x in ints for y in x for v in y))
        G[d] = np.array(ints, dtype=np.int64)               # axes: (P1 class, P2 class, P3 class)
    if big * len(deals) >= 2 ** 62: raise SystemExit("int64 guard")
    print("region %s: tables built, classes %s, denominator %d (%.0fs)" % (
        c["region"], [len(rep[a]) for a in sorted(rep)], den, time.time() - t0), flush=True)
    nA = [len(rep[(0, j)]) for j in CARDS]
    nC = {l: len(rep[(2, l)]) for l in CARDS}
    P2 = list(itertools.product(*[range(len(rep[(1, k)])) for k in CARDS]))
    bad = None; closed = [0] * 6; nodes = 0
    for n, b in enumerate(P2):
        H = {}
        for j in CARDS:
            for l in CARDS:
                if j != l:
                    H[j, l] = sum(G[(j, k, l)][:, b[k - 1], :] for k in CARDS if k not in (j, l))     # (P1-j class, P3-l class)
        Ma = {jl: h.max(axis=0) for jl, h in H.items()}
        surv = np.zeros((1, 0), dtype=np.int64); lev = 0
        for lev, j in enumerate(CARDS):          # P1's agents one at a time; P3 decoupled
            N = len(surv)
            cand = np.hstack([np.repeat(surv, nA[j - 1], 0), np.tile(np.arange(nA[j - 1]), N)[:, None]])
            bound = np.zeros(len(cand), dtype=np.int64)
            for l in CARDS:
                S = np.zeros((len(cand), nC[l]), dtype=np.int64)
                for jj in CARDS:
                    if jj == l: continue
                    S += H[jj, l][cand[:, jj - 1], :] if jj <= j else Ma[jj, l][None, :]
                bound += S.max(axis=1)
            nodes += len(cand)
            surv = cand[bound >= 0]
            if len(surv) == 0: break
        if len(surv) == 0:
            closed[lev] += 1
        else:
            i = int(np.argmax(bound)); bad = (int(bound[i]), b, tuple(int(x) for x in cand[i])); break
        if (n + 1) % 20000 == 0:
            print("   %d/%d P2 combinations, closed at P1 level %s (%.0fs)" % (n + 1, len(P2), closed[:5], time.time() - t0), flush=True)
    if bad is None:
        print("every branch closed with an exact bound < 0  (%d P2 combinations, closed at P1 level %s, %d nodes, %.0fs)" % (
            len(P2), closed[:5], nodes, time.time() - t0))
        print("CERTIFIED (independent check): region %s contains no Nash equilibrium" % c["region"])
        return
    m = F(bad[0], 12 * den)
    print("a pure profile has value %s = %.6g >= 0 (P2 classes %s, P1 classes %s, %.0fs)" % (m, float(m), bad[1], bad[2], time.time() - t0))
    print("NOT a certificate")


if __name__ == "__main__":
    main(sys.argv[1])
