"""INDEPENDENT re-check of a correlated-equilibrium certificate for the (3,5) restricted game G_c
(see ceverify.py for the claim and why it proves "every NE of G_c has V_5 < 19/8").

Independent of ceverify.py and of tree.py / kuhn3p.py: the payoffs come from a direct simulation of the
betting (antes 1, bet 1, showdown among the players still in), the certificate is re-parsed, and the
maximum over the 2^40 pure profiles is found by a DIFFERENT exhaustion: all P3 plans (4^5) and P2 plans
(8^5), with P1 solved EXACTLY for each (each P1 agent (P1, card j) only meets the 12 deals with P1 holding
j, so P1's best plans decouple); ceverify.py instead decouples P2.  Integers only (one common denominator,
numpy int64 below a 2^62 guard).
usage:  python ceverify2.py <certificate.json>"""
import sys, json, itertools, time
from fractions import Fraction as F
from math import lcm

CARDS = (1, 2, 3, 4, 5)
NPLAN = {0: 8, 1: 8, 2: 4}


def bits_of(pl, n):
    """plan index n -> bit tuple, first bit most significant (same order as the certificate)"""
    w = 3 if pl < 2 else 2
    return tuple((n >> (w - 1 - i)) & 1 for i in range(w))


def play(cards, p1, p2, p3):
    """G_c, one deal.  p1 = (call after KKB, call after KBF, call after KBC);
    p2 = (bet after K, call after KKBF, call after KKBC);  p3 = (bet after KK, call after KB)."""
    put = [1, 1, 1]; out = [False, False, False]
    # P1 checks (G_c)
    if p2[0]:                                  # P2 bets
        put[1] += 1
        if p3[1]: put[2] += 1                  # P3 calls
        else: out[2] = True
        if p1[2] if not out[2] else p1[1]:     # P1: after KBC uses p1[2], after KBF p1[1]
            put[0] += 1
        else: out[0] = True
    elif p3[0]:                                # K K, P3 bets
        put[2] += 1
        if p1[0]: put[0] += 1                  # P1 calls the KKB
        else: out[0] = True
        if p2[2] if not out[0] else p2[1]:     # P2: after KKBC p2[2], after KKBF p2[1]
            put[1] += 1
        else: out[1] = True
    live = [i for i in range(3) if not out[i]]
    win = max(live, key=lambda i: cards[i])
    pay = [-put[i] for i in range(3)]
    pay[win] += sum(put)
    return pay


def main(path):
    t0 = time.time()
    cert = json.load(open(path))
    mu = {}
    for pl, c, rho, tau, q in cert["mu"]:
        q = F(q)
        if q < 0: raise SystemExit("negative multiplier: not a certificate")
        r = int("".join(map(str, rho)), 2); t = int("".join(map(str, tau)), 2)
        if r == t: raise SystemExit("rho == tau entry")
        mu[pl, c, r, t] = mu.get((pl, c, r, t), F(0)) + q
    deals = [d for d in itertools.permutations(CARDS, 3)]
    # G[d][(r1, r2, r3)] = 12 * (contribution of deal d to L)
    G = []
    for d in deals:
        pays = {}
        for r in itertools.product(range(8), range(8), range(4)):
            pays[r] = play(d, bits_of(0, r[0]), bits_of(1, r[1]), bits_of(2, r[2]))
        tab = {}
        for r, pay in pays.items():
            v = F(pay[0]) if d[0] == 5 else F(0)
            for pl in range(3):
                for t in range(NPLAN[pl]):
                    m = mu.get((pl, d[pl], r[pl], t))
                    if m:
                        rt = list(r); rt[pl] = t
                        v += m * (pay[pl] - pays[tuple(rt)][pl])
            tab[r] = v
        G.append(tab)
    den = 1
    for tab in G:
        for v in tab.values(): den = lcm(den, v.denominator)
    G = [{r: int(v * den) for r, v in tab.items()} for tab in G]
    print("tables: %d deals, common denominator %d (%.0fs)" % (len(deals), den, time.time() - t0), flush=True)
    # exhaustion, mirrored: fix P3 (4^5) and P2 (8^5); each P1 agent (P1, card j) then decouples
    import numpy as np
    big = max(abs(v) for tab in G for v in tab.values())
    if big * len(deals) >= 2 ** 62: raise SystemExit("int64 guard")
    A = np.zeros((len(deals), 8, 8, 4), dtype=np.int64)
    for n, tab in enumerate(G):
        for r, v in tab.items(): A[n][r] = v
    idx = {d: n for n, d in enumerate(deals)}
    R2 = np.array(list(itertools.product(range(8), repeat=5)))          # P2 plans for cards 1..5
    best = None
    for c3 in itertools.product(range(4), repeat=5):
        tot = np.zeros(len(R2), dtype=np.int64)
        for j in CARDS:                                                 # P1 agent j, best plan per P2 combo
            S = np.zeros((8, len(R2)), dtype=np.int64)
            for k in CARDS:
                if k == j: continue
                Hjk = sum(A[idx[(j, k, l)], :, :, c3[l - 1]] for l in CARDS if l not in (j, k))   # (8, 8)
                S += Hjk[:, R2[:, k - 1]]
            tot += S.max(axis=0)
        i = int(tot.argmax())
        if best is None or int(tot[i]) > best[0]: best = (int(tot[i]), tuple(int(x) for x in R2[i]), c3)
    m = F(best[0], 12 * den)
    print("max over all 2^40 pure profiles of L = %s = %.6f  (%.0fs)" % (m, float(m), time.time() - t0))
    print("argmax opponents (plan index per card 1..5): P2 %s  P3 %s" % (best[1], best[2]))
    print("CERTIFIED (independent check): every NE of G_c has V_5 < 19/8" if m < F(19, 8) else "NOT a certificate")


if __name__ == "__main__":
    main(sys.argv[1])
