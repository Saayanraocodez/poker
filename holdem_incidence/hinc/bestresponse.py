"""Full unilateral best responses that respect information sets.

For player p with the others' behaviour fixed, the best response is computed by backward
induction over p's own information-set tree:

    at every node where p acts, for every hand h of p, the action chosen is
        argmax_a  sum over deals d with p holding h of  w(d, node) * V_p(child_a, d),
    where w = chance x the OTHER players' reach (p's own reach is common to the whole set),
    and V_p below the node already uses the best-response choices.

One action per information set is chosen for all the deals in it (never per revealed deal), and
earlier choices see the values of the optimised later ones, so coordinated changes to earlier and
later decisions are included.  This is the exact best-response value of the finite game (in
float64 up to rounding, or exactly in Fractions).

    r_p = BR_p - U_p(sigma),   NashConv = sum_p r_p.

``brute_force_best_response`` enumerates every pure strategy of p; it is the independent check
for small games (tests/test_bestresponse.py).
"""
from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import Dict, List, Tuple

import numpy as np

from .evaluate import group_sum, is_exact, payoff, prior, reach, strategy_at, utilities, _prod_obj
from .strategy import pure


def best_response(game, probs: np.ndarray, player: int, R=None, forced=None) -> Tuple[object, Dict[int, int], dict]:
    """``forced``: {infoset: action} the best response may NOT change (a restricted game, e.g. P1's
    opening fixed); every other information set of ``player`` is optimised."""
    forced = forced or {}
    exact = is_exact(probs)
    nodes = game.tree.nodes
    R = reach(game, probs) if R is None else R
    pr = prior(game, exact)
    V: List[np.ndarray] = [None] * len(nodes)  # type: ignore
    choice: Dict[int, int] = {}
    unreached = []
    for node in reversed(nodes):
        if node.terminal:
            V[node.id] = payoff(game, node.id, exact)[:, player]
            continue
        Q = [V[c] for c in node.children]
        if node.actor == player:
            others = np.delete(R[node.id], player, axis=1)
            w = pr * (_prod_obj(others) if exact else others.prod(axis=1))
            hands = game.deals[:, player]
            H = len(game.seats[player].hands)
            scores = [group_sum(hands, w * q, H) for q in Q]
            best = np.zeros(H, dtype=np.int64)
            for h in range(H):
                vals = [scores[a][h] for a in range(len(Q))]
                m = max(vals)
                best[h] = vals.index(m)          # ties -> the first maximal action
                if game.iset_base[node.id] + h in forced:
                    best[h] = forced[game.iset_base[node.id] + h]
                if all(v == 0 for v in vals):
                    unreached.append(game.iset_base[node.id] + h)
                choice[game.iset_base[node.id] + h] = int(best[h])
            bd = best[hands]
            out = Q[0].copy()
            for a in range(1, len(Q)):
                mask = bd == a
                out[mask] = Q[a][mask]
            V[node.id] = out
        else:
            s = strategy_at(game, probs, node.id)
            acc = s[:, 0] * Q[0]
            for a in range(1, len(Q)):
                acc = acc + s[:, a] * Q[a]
            V[node.id] = acc
    value = (pr * V[0]).sum()
    return value, choice, {"opponent_unreached_infosets": unreached}


def residuals(game, probs: np.ndarray, forced=None) -> dict:
    """r_i for every player, max_i r_i and NashConv (same arithmetic as ``probs``).
    ``forced`` = {infoset: action} restricts the best responses (restricted-game residuals)."""
    exact = is_exact(probs)
    R = reach(game, probs)
    u = utilities(game, probs)
    r, brv = [], []
    for p in range(game.n):
        v, _, _ = best_response(game, probs, p, R=R, forced=forced)
        brv.append(v)
        r.append(v - u[p])
    out = {"utilities": list(u), "br_values": brv, "r": r, "max_r": max(r), "nashconv": sum(r),
           "arithmetic": "exact rational" if exact else "float64 full enumeration"}
    return out


def br_profile(game, probs: np.ndarray, player: int, choice: Dict[int, int]) -> np.ndarray:
    """The profile with player's strategy replaced by the pure best response ``choice``."""
    return pure(game, choice, base=probs)


def brute_force_best_response(game, probs: np.ndarray, player: int, limit: int = 1 << 18):
    """Enumerate every pure strategy of ``player``; return (max value, argmax choice).

    Exponential: only for small games.  Independent of ``best_response`` (it only uses
    ``utilities``)."""
    isets = [I for I in game.isets if I.player == player]
    sizes = [len(I.actions) for I in isets]
    total = 1
    for k in sizes:
        total *= k
    if total > limit:
        raise ValueError("%d pure strategies exceed the brute-force limit" % total)
    best_v, best_c = None, None
    base = probs.copy()
    exact = is_exact(probs)
    one, zero = (Fraction(1), Fraction(0)) if exact else (1.0, 0.0)
    for combo in product(*[range(k) for k in sizes]):
        p = base
        for I, a in zip(isets, combo):
            for b in range(game.max_actions):
                p[I.index, b] = one if b == a else zero
        v = utilities(game, p)[player]
        if best_v is None or v > best_v:
            best_v, best_c = v, {I.index: a for I, a in zip(isets, combo)}
    return best_v, best_c


def brute_force_by_hand(game, probs: np.ndarray, player: int, limit: int = 1 << 18):
    """Brute force that enumerates, separately for each private hand h of ``player``, every pure
    choice at the information sets with hand h, and adds the per-hand maxima.

    Valid because a player's strategy for hand h only changes the deals in which they hold h, so
    U_player is a sum over hands of terms that depend on disjoint coordinates.  Still independent
    of ``best_response`` (it only calls ``utilities``); used where the full product is too large."""
    exact = is_exact(probs)
    one, zero = (Fraction(1), Fraction(0)) if exact else (1.0, 0.0)
    total = 0
    u0 = utilities(game, probs)[player]
    H = len(game.seats[player].hands)
    for h in range(H):
        isets = [I for I in game.isets if I.player == player and I.hand == h]
        sizes = [len(I.actions) for I in isets]
        n = 1
        for k in sizes:
            n *= k
        if n > limit:
            raise ValueError("hand %d: %d pure strategies exceed the limit" % (h, n))
        best = None
        p = probs.copy()
        for combo in product(*[range(k) for k in sizes]):
            for I, a in zip(isets, combo):
                for b in range(game.max_actions):
                    p[I.index, b] = one if b == a else zero
            v = utilities(game, p)[player]
            if best is None or v > best:
                best = v
        total += best - u0          # the gain available from hand h alone
    return u0 + total
