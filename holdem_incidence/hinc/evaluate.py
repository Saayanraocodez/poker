"""Full-enumeration evaluation: reach, values, utilities, information-set reach.

Every function works in two arithmetics:
* float64 (``probs`` a float array): deterministic floating-point enumeration;
* exact (``probs`` a dtype=object array of Fractions): rational arithmetic, used for
  certification of small games and of selected witnesses.

Nodes are stored parent-before-child, so a forward pass in id order and a backward pass in
reverse id order visit every node once.  Arrays are per deal: shape [D] or [D, n_players].
"""
from __future__ import annotations

from fractions import Fraction
from typing import List

import numpy as np


def is_exact(probs: np.ndarray) -> bool:
    return probs.dtype == object


def prior(game, exact: bool) -> np.ndarray:
    return np.array(game.prior_x, dtype=object) if exact else game.prior_f


def payoff(game, tid: int, exact: bool) -> np.ndarray:
    if exact:
        if not hasattr(game, "_payoff_obj"):
            game._payoff_obj = {}
        if tid not in game._payoff_obj:
            arr = np.empty((game.D, game.n), dtype=object)
            for d, row in enumerate(game.payoff_x[tid]):
                for i in range(game.n):
                    arr[d, i] = row[i]
            game._payoff_obj[tid] = arr
        return game._payoff_obj[tid]
    return game.payoff_f[tid]


def group_sum(idx: np.ndarray, vals: np.ndarray, size: int) -> np.ndarray:
    """Sum ``vals`` into ``size`` buckets by ``idx`` (exact for object arrays)."""
    if vals.dtype == object:
        out = np.array([Fraction(0)] * size, dtype=object)
        np.add.at(out, idx, vals)
        return out
    return np.bincount(idx, weights=vals, minlength=size)


def strategy_at(game, probs: np.ndarray, nid: int) -> np.ndarray:
    k = len(game.tree.nodes[nid].actions)
    return probs[game.node_iset[nid], :k]


def reach(game, probs: np.ndarray) -> List[np.ndarray]:
    """R[node][d, q] = product of player q's own action probabilities on the path to node."""
    exact = is_exact(probs)
    nodes = game.tree.nodes
    R: List[np.ndarray] = [None] * len(nodes)  # type: ignore
    if exact:
        R[0] = np.full((game.D, game.n), Fraction(1), dtype=object)
    else:
        R[0] = np.ones((game.D, game.n))
    for node in nodes:
        if node.terminal:
            continue
        s = strategy_at(game, probs, node.id)
        for a, c in enumerate(node.children):
            r = R[node.id].copy()
            r[:, node.actor] = r[:, node.actor] * s[:, a]
            R[c] = r
    return R


def values(game, probs: np.ndarray) -> List[np.ndarray]:
    """V[node][d, i] = player i's expected payoff from node in deal d under the profile."""
    exact = is_exact(probs)
    nodes = game.tree.nodes
    V: List[np.ndarray] = [None] * len(nodes)  # type: ignore
    for node in reversed(nodes):
        if node.terminal:
            V[node.id] = payoff(game, node.id, exact)
        else:
            s = strategy_at(game, probs, node.id)
            acc = s[:, 0:1] * V[node.children[0]]
            for a in range(1, len(node.children)):
                acc = acc + s[:, a:a + 1] * V[node.children[a]]
            V[node.id] = acc
    return V


def utilities(game, probs: np.ndarray) -> np.ndarray:
    exact = is_exact(probs)
    V0 = values(game, probs)[0]
    return (prior(game, exact)[:, None] * V0).sum(axis=0)


def infoset_reach(game, probs: np.ndarray, R=None) -> dict:
    """Per information set: ``total`` = P(the set is reached), ``own`` = the owner's own reach
    (identical over the set's nodes by perfect recall), ``cf`` = chance x opponents' reach."""
    exact = is_exact(probs)
    R = reach(game, probs) if R is None else R
    pr = prior(game, exact)
    total = np.array([Fraction(0)] * game.n_isets, dtype=object) if exact else np.zeros(game.n_isets)
    cf = total.copy()
    own = total.copy()
    for nid, base in game.iset_base.items():
        node = game.tree.nodes[nid]
        p = node.actor
        H = len(game.seats[p].hands)
        allr = R[nid].prod(axis=1) if not exact else _prod_obj(R[nid])
        others = _prod_obj(np.delete(R[nid], p, axis=1)) if exact else np.delete(R[nid], p, axis=1).prod(axis=1)
        hands = game.deals[:, p]
        total[base:base + H] = group_sum(hands, pr * allr, H)
        cf[base:base + H] = group_sum(hands, pr * others, H)
        own[base:base + H] = R[nid][game.first_deal[p], p]
    return {"total": total, "own": own, "cf": cf}


def _prod_obj(a: np.ndarray) -> np.ndarray:
    out = a[:, 0].copy()
    for j in range(1, a.shape[1]):
        out = out * a[:, j]
    return out


def with_action(game, probs: np.ndarray, iset: int, action: int) -> np.ndarray:
    """Copy of the profile with one information set forced to a pure action."""
    p = probs.copy()
    exact = is_exact(probs)
    for b in range(game.max_actions):
        p[iset, b] = (Fraction(1) if exact else 1.0) if b == action else (Fraction(0) if exact else 0.0)
    return p
