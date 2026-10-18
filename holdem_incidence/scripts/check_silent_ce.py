"""Independent re-check of every certificate written by scripts/silent_ce.py.

Independence from the prover:
* B_s (max of L over class-level pure profiles of the restricted game) is recomputed from the hinc
  ENGINE's class table (the prover used the rule-based class model), with the opposite decoupling:
  P1 x P3 class plans are enumerated (8^4 x 4^4 = 1,048,576) and P2's four classes separate.
* B_y (min over all 2^72 combo-level responses of lambda . Ebet) is recomputed from a RULE-BASED
  combo enumeration (the 24 combos of each seat built from the suits, card disjointness, and the
  class model's payoff function), not from the engine the prover used.
The multipliers are re-parsed from the stored JSON text.  A certificate passes iff both recomputed
bounds equal the stored ones exactly and B_s < B_y.

usage:  python scripts/check_silent_ce.py        -> results/silent_ce/check.json
"""
import glob
import itertools
import json
import math
import os
import sys
from fractions import Fraction as F

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import silent_ce as P                                          # noqa: E402  (plans, play, MU layout only)
import silent_threshold as ST                                  # noqa: E402

OUT = os.path.join(ROOT, "results", "silent_ce")
CLS = ST.CLS


def parse_mu(rec):
    mode = rec.get("mode", "cce")
    agents = [(0, k) for k in range(4)] + [(1, k) for k in range(4)] + [(2, k) for k in range(4)]
    nplan = {0: 8, 1: 5, 2: 4}
    if mode == "cce":
        index = [(a, None, t) for a in agents for t in range(nplan[a[0]])]
    else:
        index = [(a, r, t) for a in agents for r in range(nplan[a[0]]) for t in range(nplan[a[0]]) if r != t]
    mu = {k: F(0) for k in index}
    for name, v in rec["mu_nonzero"].items():
        tok = name.split()
        a = (int(tok[0][1]) - 1, CLS.index(tok[1]))
        if tok[2] == "->":
            key = (a, None, int(tok[3]))
        else:
            key = (a, int(tok[2]), int(tok[4]))
        assert key in mu, name
        mu[key] = F(v)
    return mode, [F(x) for x in rec["lambda"]], mu


def max_L_decouple_P2(T, lam, mu):
    """max over pure class profiles of L, enumerating P1 and P3 class plans; P2's classes separate."""
    deals = ST.DEALS
    den = math.lcm(*[x.denominator for x in lam + list(mu.values())])
    tden = math.lcm(*[x.denominator for v in T.values() for x in v])
    Ti = {k: [int(x * tden) for x in v] for k, v in T.items()}
    lamI = [int(x * den) for x in lam]
    muI = {k: int(v * den) for k, v in mu.items() if v != 0}
    # G[j][i1][i2][i3] = contribution of deal j (exact integers)
    G = np.zeros((len(deals), 8, 5, 4), dtype=object)
    for j, d in enumerate(deals):
        for i1 in range(8):
            for i2 in range(5):
                for i3 in range(4):
                    p = (i1, i2, i3)
                    v = lamI[d[0]] * Ti[(d, i1, i2, i3)][0]
                    for (a, r, t), w in muI.items():
                        i, k = a
                        if d[i] != k or (r is not None and p[i] != r):
                            continue
                        q = list(p)
                        q[i] = t
                        v += w * (Ti[(d, i1, i2, i3)][i] - Ti[(d, q[0], q[1], q[2])][i])
                    G[j, i1, i2, i3] = v
    assert max(abs(int(x)) for x in G.flat) * 64 < 2 ** 62
    G = G.astype(np.int64)
    P1A = np.array(list(itertools.product(range(8), repeat=4)))
    P3A = np.array(list(itertools.product(range(4), repeat=4)))
    total = np.zeros((len(P1A), len(P3A)), dtype=np.int64)
    for k in range(4):                                        # P2's class k separates
        acc = np.zeros((5, len(P1A), len(P3A)), dtype=np.int64)
        for j, d in enumerate(deals):
            if d[1] == k:
                sub = np.transpose(G[j], (1, 0, 2))           # [i2, i1, i3]
                acc += sub[:, P1A[:, d[0]], :][:, :, P3A[:, d[2]]]
        total += acc.max(axis=0)
    return F(int(total.max()), den * tden * 6480)


def combos():
    """The 24 combos of each seat: (class index, (card, card)) with card = (rank class, suit)."""
    out = []
    for k in range(4):
        for s1, s2 in itertools.combinations(range(4), 2):
            out.append((k, ((k, s1), (k, s2))))
    return out


def min_y_rules(lam, c):
    """min over combo-level responses of lambda . Ebet, from the rules (no engine)."""
    C = combos()
    den = math.lcm(*[x.denominator for x in lam])
    lamI = [int(x * den) for x in lam]
    pay = {}
    for h2c in range(4):
        for h3c in range(4):
            for h1c in range(4):
                for y2 in (0, 1):
                    for y3 in (0, 1):
                        hist = "B:1-" + ("C" if y2 else "F") + "-" + ("C" if y3 else "F")
                        pay[(h1c, h2c, h3c, y2, y3)] = F(ST.payoff(hist, (h1c, h2c, h3c), c)[0])
    eden = math.lcm(*[v.denominator for v in pay.values()])
    H = len(C)
    W0 = np.zeros((H, H, 2), dtype=np.int64)
    W1 = np.zeros((H, H, 2), dtype=np.int64)
    for a, (k1, c1) in enumerate(C):
        for b, (k2, c2) in enumerate(C):
            if set(c1) & set(c2):
                continue
            for e, (k3, c3) in enumerate(C):
                if set(c3) & set(c1) or set(c3) & set(c2):
                    continue
                for y in (0, 1):
                    W0[b, e, y] += lamI[k1] * int(pay[(k1, k2, k3, 0, y)] * eden)
                    W1[b, e, y] += lamI[k1] * int(pay[(k1, k2, k3, 1, y)] * eden)
    base = np.zeros((H, 4), dtype=np.int64)
    slope = np.zeros((H, H, 4), dtype=np.int64)
    for ch, (yf, yc) in enumerate(itertools.product((0, 1), repeat=2)):
        base[:, ch] = W0[:, :, yf].sum(axis=0)
        slope[:, :, ch] = W1[:, :, yc] - W0[:, :, yf]
    S2 = slope.reshape(H, H * 4)
    best = None
    chunk = 1 << 16
    for start in range(0, 1 << H, chunk):
        idx = np.arange(start, start + chunk, dtype=np.int64)
        Y = ((idx[:, None] >> np.arange(H)[None, :]) & 1).astype(np.int64)
        tot = (Y @ S2 + base.reshape(1, -1)).reshape(chunk, H, 4).min(axis=2).sum(axis=1)
        m = int(tot.min())
        best = m if best is None else min(best, m)
    return F(best, den * eden * 6480)


def check(rec, path):
    mode, lam, mu = parse_mu(rec)
    P.MODE = mode
    ends = [{"c": rec["c"], "B_s_max_L": rec["B_s_max_L"], "B_y_min_deterrence": rec["B_y_min_deterrence"]}] \
        if "ends" not in rec else rec["ends"]
    rows = []
    for e in ends:
        c = F(e["c"])
        Te, _ = P.engine_table(c)
        Bs = max_L_decouple_P2(Te, lam, mu)
        By = min_y_rules(lam, c)
        rows.append({"c": str(c), "B_s_recomputed": str(Bs), "B_y_recomputed": str(By),
                     "B_s_equal_stored": Bs == F(e["B_s_max_L"]), "B_y_equal_stored": By == F(e["B_y_min_deterrence"]),
                     "B_s_lt_B_y": Bs < By})
        print("  c = %-8s B_s %s %.9f  B_y %s %.9f  separates %s" % (
            c, "==" if rows[-1]["B_s_equal_stored"] else "!=", float(Bs),
            "==" if rows[-1]["B_y_equal_stored"] else "!=", float(By), Bs < By), flush=True)
    ok = all(r["B_s_equal_stored"] and r["B_y_equal_stored"] and r["B_s_lt_B_y"] for r in rows)
    return {"certificate": os.path.basename(path), "mode": mode, "ends": rows, "passes": ok}


def main():
    out = []
    for path in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        if os.path.basename(path) == "check.json":
            continue
        rec = json.load(open(path))
        if not rec.get("certified"):
            continue
        print(os.path.basename(path), flush=True)
        out.append(check(rec, path))
    json.dump({"independent_check": __doc__.strip(), "results": out,
               "all_pass": all(r["passes"] for r in out)}, open(os.path.join(OUT, "check.json"), "w"), indent=1)
    print("all %d certificates pass the independent check: %s" % (len(out), all(r["passes"] for r in out)))


if __name__ == "__main__":
    main()
