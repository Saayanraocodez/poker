"""
Exact 3-player Kuhn poker engine (Abou Risk & Szafron variant, as described in
Szafron, Gibson & Sturtevant, "A Parameterized Family of Equilibrium Profiles
for Three-Player Kuhn Poker", AAMAS 2013, Section 2).

Rules
-----
  * 4-card deck {1,2,3,4}; each of P1,P2,P3 is dealt one card (24 deals, each
    with probability kappa = 1/24).
  * Every player antes 1 chip.  A bet/call is exactly 1 more chip.  No raises.
  * P1 acts, then P2, then P3.  If nobody has bet, the actor may check (K) or
    bet (B).  If somebody has bet, the actor may fold (F) or call (C).
  * If P1 bets, P2 then P3 answer -> terminal.
  * If P1 checks and P2 bets, P3 answers, then P1 answers -> terminal.
  * If P1 and P2 both check and P3 bets, P1 answers, then P2 answers -> terminal.
  * If all three check, showdown between all three.
  * Showdown: highest card among players who have not folded wins the pot.

Strategy parameterisation (paper's Table 1)
-------------------------------------------
  a_{jk}, b_{jk}, c_{jk} = probability that P1 / P2 / P3 takes the AGGRESSIVE
  action (B when no bet is out, C when facing a bet) while holding card j in
  betting situation k.  The passive action (K or F) has probability 1 - x_{jk}.

      situation k :   P1 history     P2 history      P3 history
              1   :   (root)         K               KK
              2   :   KKB            B               KB
              3   :   KBF            KKBF            BF
              4   :   KBC            KKBC            BC

  A full profile is the 48-vector [a_{11..44}, b_{11..44}, c_{11..44}].
"""

import itertools
from fractions import Fraction

import numpy as np

import os
NCARDS = int(os.environ.get('KUHN_CARDS', '5'))
CARDS = tuple(range(1, NCARDS + 1))
SITUATIONS = (1, 2, 3, 4)
NPARAM = 12 * NCARDS
DUMMY = NPARAM          # index of a constant-1 slot used to pad the leaf table
ND_ = NCARDS * (NCARDS - 1) * (NCARDS - 2)
KAPPA = 1.0 / ND_
KAPPA_F = Fraction(1, ND_)


# ---------------------------------------------------------------- indexing --
def pidx(player, card, situation):
    """player: 0=P1(a), 1=P2(b), 2=P3(c);  card 1..4;  situation 1..4."""
    return player * (4 * NCARDS) + (card - 1) * 4 + (situation - 1)


PARAM_NAME = {}
for _pl, _ch in enumerate("abc"):
    for _j in CARDS:
        for _k in SITUATIONS:
            PARAM_NAME[pidx(_pl, _j, _k)] = "%s%d%d" % (_ch, _j, _k)
NAME_IDX = {v: k for k, v in PARAM_NAME.items()}


# ------------------------------------------------------------ leaf builder --
def _payoff(cards, contrib, folded):
    """Chips won/lost by each player at a terminal node."""
    pot = sum(contrib)
    live = [i for i in range(3) if not folded[i]]
    winner = max(live, key=lambda i: cards[i])
    pay = [-contrib[i] for i in range(3)]
    pay[winner] += pot
    return tuple(pay)


def _leaves_for_deal(cards):
    """All terminal histories for one deal, as (factors, payoff).

    factors is a list of (param_index, aggressive?) pairs whose product of
    probabilities is the probability of reaching that leaf given the deal.
    """
    c1, c2, c3 = cards
    out = []

    for p1a in (0, 1):                                   # P1 situation 1: K / B
        f1 = (pidx(0, c1, 1), bool(p1a))

        if p1a:                                          # ---- P1 bet ----
            for p2a in (0, 1):                           # P2 situation 2: F / C
                f2 = (pidx(1, c2, 2), bool(p2a))
                contrib = [2, 2 if p2a else 1, 1]
                folded = [False, not p2a, False]
                sit3 = 4 if p2a else 3                   # BC or BF
                for p3a in (0, 1):                       # P3 situation 3/4
                    f3 = (pidx(2, c3, sit3), bool(p3a))
                    cc, ff = list(contrib), list(folded)
                    if p3a:
                        cc[2] = 2
                    else:
                        ff[2] = True
                    out.append(([f1, f2, f3], _payoff(cards, cc, ff)))

        else:                                            # ---- P1 checked ----
            for p2a in (0, 1):                           # P2 situation 1: K / B
                f2 = (pidx(1, c2, 1), bool(p2a))

                if p2a:                                  # ---- P2 bet (KB) ----
                    for p3a in (0, 1):                   # P3 situation 2: F / C
                        f3 = (pidx(2, c3, 2), bool(p3a))
                        contrib = [1, 2, 2 if p3a else 1]
                        folded = [False, False, not p3a]
                        sitp1 = 4 if p3a else 3          # KBC or KBF
                        for p1b in (0, 1):               # P1 situation 3/4
                            f4 = (pidx(0, c1, sitp1), bool(p1b))
                            cc, ff = list(contrib), list(folded)
                            if p1b:
                                cc[0] = 2
                            else:
                                ff[0] = True
                            out.append(([f1, f2, f3, f4],
                                        _payoff(cards, cc, ff)))

                else:                                    # ---- KK ----
                    for p3a in (0, 1):                   # P3 situation 1: K / B
                        f3 = (pidx(2, c3, 1), bool(p3a))
                        if not p3a:                      # KKK -> 3-way showdown
                            out.append(([f1, f2, f3],
                                        _payoff(cards, [1, 1, 1], [False] * 3)))
                        else:                            # ---- KKB ----
                            for p1b in (0, 1):           # P1 situation 2: F / C
                                f4 = (pidx(0, c1, 2), bool(p1b))
                                contrib = [2 if p1b else 1, 1, 2]
                                folded = [not p1b, False, False]
                                sitp2 = 4 if p1b else 3  # KKBC or KKBF
                                for p2b in (0, 1):       # P2 situation 3/4
                                    f5 = (pidx(1, c2, sitp2), bool(p2b))
                                    cc, ff = list(contrib), list(folded)
                                    if p2b:
                                        cc[1] = 2
                                    else:
                                        ff[1] = True
                                    out.append(([f1, f2, f3, f4, f5],
                                                _payoff(cards, cc, ff)))
    return out


def build_leaf_table():
    deals = list(itertools.permutations(CARDS, 3))
    rows, idx, agg, pay, holder = [], [], [], [], []
    maxf = 5
    for d in deals:
        for factors, p in _leaves_for_deal(d):
            ii = [f[0] for f in factors] + [DUMMY] * (maxf - len(factors))
            aa = [f[1] for f in factors] + [True] * (maxf - len(factors))
            idx.append(ii)
            agg.append(aa)
            pay.append(p)
            holder.append(d)
            rows.append((d, factors, p))
    return (np.array(idx, dtype=np.int64),
            np.array(agg, dtype=bool),
            np.array(pay, dtype=np.float64),
            np.array(holder, dtype=np.int64),
            rows,
            deals)


IDX, AGG, PAY, HOLDER, ROWS, DEALS = build_leaf_table()
NLEAF = IDX.shape[0]


# --------------------------------------------------------------- utilities --
def utilities(p):
    """Exact expected utility (u1,u2,u3) by full enumeration of all leaves of
    the 24-deal game tree.  No sampling.  p is the 48-vector."""
    q = np.empty(NPARAM + 1, dtype=np.float64)
    q[:NPARAM] = p
    q[DUMMY] = 1.0
    f = np.where(AGG, q[IDX], 1.0 - q[IDX])
    w = f.prod(axis=1)
    return KAPPA * (w[:, None] * PAY).sum(axis=0)


def utilities_batch(P):
    """utilities() for a stack of profiles.  P has shape (N, 48) -> (N, 3)."""
    P = np.asarray(P, dtype=np.float64)
    Q = np.empty((P.shape[0], NPARAM + 1), dtype=np.float64)
    Q[:, :NPARAM] = P
    Q[:, DUMMY] = 1.0
    w = np.ones((P.shape[0], NLEAF), dtype=np.float64)
    for k in range(IDX.shape[1]):                    # 5 factor slots
        g = Q[:, IDX[:, k]]                          # (N, L)
        w *= np.where(AGG[:, k][None, :], g, 1.0 - g)
    return KAPPA * (w @ PAY)                         # (N, 3)


def gradient_exact(p):
    """Full exact gradient G with G[i] = du/dp_i = u(p_i=1) - u(p_i=0).

    Valid because u is multilinear: u is affine in every single coordinate.
    Returns shape (48, 3).
    """
    P = np.repeat(p[None, :], 2 * NPARAM, axis=0)
    for i in range(NPARAM):
        P[2 * i, i] = 1.0
        P[2 * i + 1, i] = 0.0
    U = utilities_batch(P)
    return U[0::2] - U[1::2]


def gradient_central_diff(p, h=1e-5):
    """Full gradient by CENTRAL finite differences, one coordinate at a time."""
    P = np.repeat(p[None, :], 2 * NPARAM, axis=0)
    for i in range(NPARAM):
        P[2 * i, i] += h
        P[2 * i + 1, i] -= h
    U = utilities_batch(P)
    return (U[0::2] - U[1::2]) / (2.0 * h)


def gradients_batch(P, h=None, chunk=100):
    """Gradients for a stack of profiles.  P (N,48) -> G (N,48,3).

    h=None  -> exact multilinear gradient  u(p_i=1) - u(p_i=0).
    h=float -> central finite difference   [u(p+h e_i) - u(p-h e_i)] / 2h.
    """
    P = np.asarray(P, dtype=np.float64)
    N = P.shape[0]
    G = np.empty((N, NPARAM, 3), dtype=np.float64)
    eye = np.eye(NPARAM)
    for s in range(0, N, chunk):
        blk = P[s:s + chunk]
        n = blk.shape[0]
        hi = np.repeat(blk[:, None, :], NPARAM, axis=1)      # (n,48,48)
        lo = hi.copy()
        if h is None:
            hi[:, np.arange(NPARAM), np.arange(NPARAM)] = 1.0
            lo[:, np.arange(NPARAM), np.arange(NPARAM)] = 0.0
            scale = 1.0
        else:
            hi = hi + h * eye[None, :, :]
            lo = lo - h * eye[None, :, :]
            scale = 1.0 / (2.0 * h)
        U = utilities_batch(np.concatenate([hi.reshape(-1, NPARAM),
                                            lo.reshape(-1, NPARAM)], axis=0))
        m = n * NPARAM
        G[s:s + n] = scale * (U[:m] - U[m:]).reshape(n, NPARAM, 3)
    return G


def utilities_exact(p):
    """Same computation in exact rational arithmetic.  p: 48 Fractions."""
    q = list(p) + [Fraction(1)]
    tot = [Fraction(0)] * 3
    for r in range(NLEAF):
        w = Fraction(1)
        for k in range(IDX.shape[1]):
            i = int(IDX[r, k])
            w = w * (q[i] if AGG[r, k] else (1 - q[i]))
            if w == 0:
                break
        if w == 0:
            continue
        for t in range(3):
            tot[t] += w * int(PAY[r, t])
    return tuple(KAPPA_F * t for t in tot)


# --------------------------------------------------------- best responses ---
# u_i decomposes over the card player i holds, and player i's parameters for
# card j appear only in deals where i holds j.  So the best response splits
# into 4 independent 4-decision problems -> 4 * 2^4 = 64 exact evaluations.
_CARD_MASK = {(pl, j): (HOLDER[:, pl] == j) for pl in range(3) for j in CARDS}
_SUB = {k: (IDX[m], AGG[m], PAY[m]) for k, m in _CARD_MASK.items()}


def best_response_value(p, player):
    """Exact max_{sigma_i} u_i(sigma_i, p_{-i}) by enumeration."""
    q = np.empty(NPARAM + 1, dtype=np.float64)
    q[:NPARAM] = p
    q[DUMMY] = 1.0
    total = 0.0
    best_strategy = {}
    for j in CARDS:
        sub_idx, sub_agg, sub_pay = _SUB[(player, j)]
        sub_pay = sub_pay[:, player]
        own = [pidx(player, j, k) for k in SITUATIONS]
        best, arg = None, None
        for bits in itertools.product((0.0, 1.0), repeat=4):
            qq = q.copy()
            for i, v in zip(own, bits):
                qq[i] = v
            f = np.where(sub_agg, qq[sub_idx], 1.0 - qq[sub_idx])
            val = KAPPA * float((f.prod(axis=1) * sub_pay).sum())
            if best is None or val > best:
                best, arg = val, bits
        total += best
        best_strategy[j] = arg
    return total, best_strategy


def exploitability(p):
    """(BR_i - u_i) for each player.  All zero  <=>  p is a Nash equilibrium."""
    u = utilities(p)
    return np.array([best_response_value(p, i)[0] - u[i] for i in range(3)])


def reach(p):
    """Reach probability of each parameter's information set.

    Each reaching history is counted once per available action, hence the /2.
    A value of 0 means the information set is off-path under p.
    """
    q = np.append(p, 1.0)
    f = np.where(AGG, q[IDX], 1.0 - q[IDX])         # (L,5)
    tot = f.prod(axis=1)
    r = np.zeros(NPARAM + 1)
    for k in range(IDX.shape[1]):
        with np.errstate(divide="ignore", invalid="ignore"):
            other = np.where(f[:, k] != 0, tot / f[:, k], 0.0)
        # recompute exactly where a factor is 0
        bad = f[:, k] == 0
        if bad.any():
            o = np.ones(bad.sum())
            for j in range(IDX.shape[1]):
                if j != k:
                    o = o * f[bad, j]
            other[bad] = o
        np.add.at(r, IDX[:, k], other)
    return (KAPPA * r[:NPARAM]) / 2.0                 # each history counted twice


# ------------------------------------------------------------ derivatives ---
def central_diff(p, d, h=1e-5):
    """Central finite difference of (u1,u2,u3) along direction d at eps = 0.

    u_i is multilinear in the 48 parameters, so along a direction supported on
    ONE parameter it is affine in eps and this difference is exact to machine
    precision.  Evaluating at eps = +-h may step marginally outside [0,1]; the
    multilinear extension is still well defined, and this is only a numerical
    device for reading off the one-sided derivative at a boundary parameter.
    """
    return (utilities(p + h * d) - utilities(p - h * d)) / (2.0 * h)


def exact_coord_derivative(p, i):
    """du/dp_i exactly, using multilinearity:  u(p_i = 1) - u(p_i = 0)."""
    p1, p0 = p.copy(), p.copy()
    p1[i], p0[i] = 1.0, 0.0
    return utilities(p1) - utilities(p0)
