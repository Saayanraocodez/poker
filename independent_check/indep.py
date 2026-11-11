"""Independent exact engine for n=3 player, N-card Kuhn poker (Abou Risk & Szafron rules).

Written from the rules only (history strings, recursive), sharing no code with the repo.
Everything is in fractions.Fraction.

profile: dict  name -> Fraction, names 'a11'..'c44'  (player letter, card, situation)
situations:   P1: 1 ''    2 'KKB'  3 'KBF'  4 'KBC'
              P2: 1 'K'   2 'B'    3 'KKBF' 4 'KKBC'
              P3: 1 'KK'  2 'KB'   3 'BF'   4 'BC'
"""
from fractions import Fraction as F
from itertools import permutations, product

SIT = [{'': 1, 'KKB': 2, 'KBF': 3, 'KBC': 4},
       {'K': 1, 'B': 2, 'KKBF': 3, 'KKBC': 4},
       {'KK': 1, 'KB': 2, 'BF': 3, 'BC': 4}]
LET = 'abc'
NAMES = [LET[p] + str(j) + str(k) for p in range(3) for j in range(1, 5) for k in range(1, 5)]


def actor(h):
    """who acts after history h (0,1,2), or None if terminal."""
    if 'B' not in h:
        return len(h) if len(h) < 3 else None        # KKK terminal
    # somebody bet at index ib; the other two answer in cyclic order after the bettor
    ib = h.index('B')
    answered = len(h) - ib - 1
    if answered == 2:
        return None
    return (ib + 1 + answered) % 3


def payoff(cards, h):
    contrib = [1, 1, 1]
    folded = [False] * 3
    if 'B' in h:
        ib = h.index('B')
        contrib[ib] += 1
        for t, act in enumerate(h[ib + 1:]):
            pl = (ib + 1 + t) % 3
            if act == 'C':
                contrib[pl] += 1
            else:
                assert act == 'F'
                folded[pl] = True
    pot = sum(contrib)
    live = [i for i in range(3) if not folded[i]]
    w = max(live, key=lambda i: cards[i])
    out = [-c for c in contrib]
    out[w] += pot
    return out


def name_at(pl, card, h):
    return LET[pl] + str(card) + str(SIT[pl][h])


def aggressive(h):
    return 'C' if 'B' in h else 'B'


def passive(h):
    return 'F' if 'B' in h else 'K'


def deals(N=4):
    return list(permutations(range(1, N + 1), 3))


def value(cards, h, prof):
    pl = actor(h)
    if pl is None:
        return [F(x) for x in payoff(cards, h)]
    x = prof[name_at(pl, cards[pl], h)]
    va = value(cards, h + aggressive(h), prof) if x != 0 else None
    vp = value(cards, h + passive(h), prof) if x != 1 else None
    if va is None:
        return vp
    if vp is None:
        return va
    return [x * a + (1 - x) * b for a, b in zip(va, vp)]


def utilities(prof, N=4):
    ds = deals(N)
    tot = [F(0)] * 3
    for d in ds:
        v = value(d, '', prof)
        tot = [t + x for t, x in zip(tot, v)]
    return [t / len(ds) for t in tot]


def terminal_histories():
    out = []

    def rec(h):
        if actor(h) is None:
            out.append(h)
            return
        rec(h + aggressive(h))
        rec(h + passive(h))
    rec('')
    return out


# ------------------------------------------------------------------ best response
def br_value(prof, pl, N=4):
    """Exact best-response value of player pl against prof, by information-set DP.

    For each own card: collect (deal, history, opp-reach) and solve the single-agent decision
    problem by recursion on the player's own information sets (perfect recall).
    """
    ds = deals(N)
    total = F(0)
    plan = {}
    for card in range(1, N + 1):
        # nodes: list of (deal, history, weight) with weight = chance * opponents' reach
        start = [(d, '', F(1, len(ds))) for d in ds if d[pl] == card]

        def advance(nodes):
            """push nodes forward through opponents' moves until pl acts or terminal.
            returns (terminal_value, {own_history: [nodes]})"""
            tv = F(0)
            groups = {}
            stack = list(nodes)
            while stack:
                d, h, w = stack.pop()
                if w == 0:
                    continue
                a = actor(h)
                if a is None:
                    tv += w * payoff(d, h)[pl]
                elif a == pl:
                    groups.setdefault(h, []).append((d, h, w))
                else:
                    x = prof[name_at(a, d[a], h)]
                    stack.append((d, h + aggressive(h), w * x))
                    stack.append((d, h + passive(h), w * (1 - x)))
            return tv, groups

        def solve(nodes):
            tv, groups = advance(nodes)
            tot = tv
            for h, ns in groups.items():
                va = solve([(d, hh + aggressive(hh), w) for d, hh, w in ns])
                vp = solve([(d, hh + passive(hh), w) for d, hh, w in ns])
                plan[name_at(pl, card, h)] = (va, vp)
                tot += max(va, vp)
            return tot
        total += solve(start)
    return total, plan


def exploitability(prof, N=4):
    u = utilities(prof, N)
    return [br_value(prof, i, N)[0] - u[i] for i in range(3)]


# ------------------------------------------------------------------ own-reach-stripped gradient D
def D_all(prof, N=4):
    """D_i = sum over nodes n of info set i:  chance * R_{-k}(n) * (V_k(agg) - V_k(pass)),
    own coordinates on the path replaced by 1, continuation values under prof."""
    ds = deals(N)
    D = {}
    R = {}

    def rec(d, h, w_others):
        pl = actor(h)
        if pl is None:
            return
        nm = name_at(pl, d[pl], h)
        ha, hp = h + aggressive(h), h + passive(h)
        if w_others[pl] != 0:
            va = value(d, ha, prof)[pl]
            vp = value(d, hp, prof)[pl]
            D[nm] = D.get(nm, F(0)) + w_others[pl] * (va - vp)
            R[nm] = R.get(nm, F(0)) + w_others[pl]
        x = prof[nm]
        wa = [w if i == pl else w * x for i, w in enumerate(w_others)]
        wp = [w if i == pl else w * (1 - x) for i, w in enumerate(w_others)]
        rec(d, ha, wa)
        rec(d, hp, wp)
    for d in ds:
        rec(d, '', [F(1, len(ds))] * 3)
    for nm in NAMES:
        D.setdefault(nm, F(0))
        R.setdefault(nm, F(0))
    return D, R


def dcond(prof):
    """list of coordinates violating the D-condition."""
    D, _ = D_all(prof)
    bad = []
    for nm in NAMES:
        x, d = prof[nm], D[nm]
        if (x > 0 and d < 0) or (x < 1 and d > 0):
            bad.append((nm, x, d))
    return bad


def grad(prof, nm):
    """du/dx_nm = u(x=1) - u(x=0), exact."""
    p1 = dict(prof); p1[nm] = F(1)
    p0 = dict(prof); p0[nm] = F(0)
    return [a - b for a, b in zip(utilities(p1), utilities(p0))]


# ------------------------------------------------------------------ the SGS family
def family(b11, b21, b23, b32, c11, c33, c34):
    b11, b21, b23, b32, c11, c33, c34 = map(F, (b11, b21, b23, b32, c11, c33, c34))
    p = {}
    for x in LET:
        for nm in ('12', '13', '14', '24'):
            p[x + nm] = F(0)
        for nm in ('42', '43', '44'):
            p[x + nm] = F(1)
    for nm in ('a11', 'a21', 'a22', 'a23', 'a31', 'a32', 'a34', 'a41'):
        p[nm] = F(0)
    p['a33'] = F(1, 2)
    beta = max(b11, b21)
    p.update(b11=b11, b21=b21, b22=F(0), b23=b23, b31=F(0), b32=b32, b34=F(0),
             b33=F(1, 2) + (b11 + b21) / 2 + beta / 2 - b23 * (1 - b21), b41=2 * b11 + 2 * b21)
    p.update(c11=c11, c21=F(1, 2) - c11, c22=F(0), c23=F(0), c31=F(0), c32=F(0), c33=c33, c34=c34, c41=F(1))
    assert set(p) == set(NAMES)
    return p


def window(b11, b21, b32):
    b11, b21, b32 = map(F, (b11, b21, b32))
    beta = max(b11, b21)
    w = F(3, 4) * (b11 + b21) + beta / 4
    lo = F(1, 2) - b32
    return lo, lo + w, w


def vec(prof):
    return [prof[n] for n in NAMES]


def from_vec(v):
    return {n: F(x) for n, x in zip(NAMES, v)}
