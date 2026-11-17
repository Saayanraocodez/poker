"""Replay stored CE witnesses with the independent exact rules engine; no LP."""
import sys, json, itertools
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
sys.path.insert(0, "independent_check")
import indep as I

def verify(path, normal):
    d = json.loads(Path(path).read_text())
    plans = [[tuple(x) for x in p] for p in d["plans"]]
    agents = [tuple(x) for x in d["agents"]]
    expected = [[b for b in itertools.product((0, 1), repeat=4)
                 if not (pl == 0 and b[0] and any(b[1:]))
                 and not (pl == 1 and b[0] and any(b[2:]))] for pl in range(3)]
    assert plans == expected
    assert agents == [(pl, c) for pl in range(3) for c in range(1, 5)]
    ai = {a: k for k, a in enumerate(agents)}
    support = [(tuple(s), int(w)) for s, w in d["support"]]
    den = int(d["denominator"])
    assert den > 0 and all(w > 0 for s, w in support)
    assert sum(w for s, w in support) == den
    assert len(set(s for s, w in support)) == len(support)
    for s, w in support:
        assert len(s) == 12
        assert all(0 <= v < len(plans[agents[k][0]]) for k, v in enumerate(s))

    @lru_cache(None)
    def util(s, pl, card):
        total = F(0)
        for cards in I.deals():
            if cards[pl] != card: continue
            h = ""
            while I.actor(h) is not None:
                actor = I.actor(h)
                bit = plans[actor][s[ai[(actor, cards[actor])]]][I.SIT[actor][h] - 1]
                h += I.aggressive(h) if bit else I.passive(h)
            total += I.payoff(cards, h)[pl]
        return total

    rows = 0
    minimum = None
    for pl in range(3):
        groups = {}
        for s, w in support:
            key = tuple(s[ai[(pl,c)]] for c in range(1,5)) if normal else None
            if normal: groups.setdefault(key, []).append((s,w))
        for card in range(1,5):
            k = ai[(pl,card)]
            gs = groups if normal else {}
            if not normal:
                for s,w in support: gs.setdefault(s[k], []).append((s,w))
            for key, items in gs.items():
                rho = key[card-1] if normal else key
                base = sum(w * util(s,pl,card) for s,w in items)
                for tau in range(len(plans[pl])):
                    if tau == rho: continue
                    dev = F(0)
                    for s,w in items:
                        other = list(s); other[k] = tau
                        dev += w * util(tuple(other),pl,card)
                    gap = base-dev
                    assert gap >= 0, (path,pl,card,key,tau,gap)
                    minimum = gap if minimum is None else min(minimum,gap)
                    rows += 1
    pbet = F(sum(w * sum(plans[0][s[ai[(0,c)]]][0] for c in range(1,5)) for s,w in support),4*den)
    pay = [sum(w * sum(util(s,pl,c) for c in range(1,5)) for s,w in support)/(24*den) for pl in range(3)]
    assert pbet == F(d["p_bet"]) and pbet > 0
    assert pay == [F(v) for v in d["payoffs"]] and sum(pay) == 0
    print(path, "PASS", len(support), "profiles;", rows, "rows; minimum", minimum, "; P1 bets", pbet, flush=True)
verify("continuations/ce_witness.json", False)
verify("continuations/nfce_witness.json", True)
print("ALL STORED CE WITNESSES VERIFIED")
