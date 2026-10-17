"""Derivative vectors of unilateral deviations, incidence ratios, and their classification.

For a feasible unilateral direction d of player A,
    D_i = d U_i(sigma_A + eps d, sigma_-A) / d eps  at eps = 0,     i = 1..n.
At one information set I, U is affine in the row sigma_I (perfect recall: I occurs at most once
on any path), so moving probability mass from action b to action a has the EXACT derivative
    D_i = U_i(I -> a) - U_i(I -> b)          (all other entries fixed).
For a binary set this is U(x = 1) - U(x = 0).  No finite differences are used.  A direction that
moves several information sets of the same player is the sum of the per-set derivatives
(first order; the cross terms are second order).

    rho(A -> X) = -D_X / D_A          only when D_A is resolved and nonzero.

Units: D_i is in big blinds (chips) per unit of probability moved, as an expectation over the
declared root prior of the conditional river game.

Classification of a direction (tolerances are recorded with every result):
    inert              max_i |D_i| <= tol_num
    costless_transfer  |D_A| <= tol_num  <  max_{i != A} |D_i|
    unresolved         tol_num < |D_A| <= tol_eq   (the denominator is within the profile's
                       equilibrium error, so its sign and size are not established)
    costly             D_A < -tol_eq
    profitable         D_A > +tol_eq               (possible only away from an exact equilibrium)
``tol_num`` is the arithmetic floor (0 in exact arithmetic; 1e-12 bb by default in float64 full
enumeration).  ``tol_eq`` defaults to max(tol_num, 10 * max_i r_i): a first-order effect smaller
than ten times the largest best-response residual is not treated as resolved.  rho is computed
for costly and profitable directions only; raw D is stored for every direction.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional

import numpy as np

from .evaluate import is_exact, reach, values, prior, utilities, with_action, _prod_obj

TOL_NUM_FLOAT = 1e-12
TOL_EQ_FACTOR = 10.0


def derivative_vector(game, probs, iset: int, a_to: int, a_from: int):
    """Exact (or float) derivative of moving mass from ``a_from`` to ``a_to`` at ``iset``."""
    u_to = utilities(game, with_action(game, probs, iset, a_to))
    u_from = utilities(game, with_action(game, probs, iset, a_from))
    return u_to - u_from


def all_partials(game, probs) -> np.ndarray:
    """P[I, a, i] = U_i(I -> a), the value of forcing action a at I, for every I at once.

    Uses U_i(I -> a) = sum over deals/nodes of I of prior * reach(node) * V_i(child_a) plus the
    contribution of paths not through I; differences over a cancel the latter, so
    P[I, a] - P[I, b] is the transfer derivative.  Returned array holds only the through-I part
    (enough for differences).  Cross-checked against ``derivative_vector`` in the tests."""
    exact = is_exact(probs)
    R = reach(game, probs)
    V = values(game, probs)
    pr = prior(game, exact)
    shape = (game.n_isets, game.max_actions, game.n)
    out = np.full(shape, Fraction(0), dtype=object) if exact else np.zeros(shape)
    for nid, base in game.iset_base.items():
        node = game.tree.nodes[nid]
        p = node.actor
        H = len(game.seats[p].hands)
        w = pr * (_prod_obj(R[nid]) if exact else R[nid].prod(axis=1))
        hands = game.deals[:, p]
        for a, c in enumerate(node.children):
            for i in range(game.n):
                vals = w * V[c][:, i]
                if exact:
                    acc = np.array([Fraction(0)] * H, dtype=object)
                    np.add.at(acc, hands, vals)
                else:
                    acc = np.bincount(hands, weights=vals, minlength=H)
                out[base:base + H, a, i] = acc
    return out


def classify(D, A: int, tol_num: float, tol_eq: float) -> str:
    dA = D[A]
    others = max(abs(D[i]) for i in range(len(D)) if i != A)
    if max(abs(x) for x in D) <= tol_num:
        return "inert"
    if abs(dA) <= tol_num:
        return "costless_transfer" if others > tol_num else "inert"
    if abs(dA) <= tol_eq:
        return "unresolved"
    return "costly" if dA < 0 else "profitable"


def incidence_record(game, probs, iset: int, a_to: int, a_from: int, max_r=None,
                     tol_num: Optional[float] = None, tol_eq: Optional[float] = None) -> dict:
    """Full record for one transfer direction at one information set."""
    exact = is_exact(probs)
    I = game.isets[iset]
    A = I.player
    if tol_num is None:
        tol_num = 0 if exact else TOL_NUM_FLOAT
    if tol_eq is None:
        tol_eq = max(tol_num, TOL_EQ_FACTOR * (max_r if max_r is not None else 0))
    feasible = probs[iset, a_from] > 0
    D = derivative_vector(game, probs, iset, a_to, a_from)
    cls = classify(D, A, tol_num, tol_eq)
    rho = {}
    if cls in ("costly", "profitable"):
        for X in range(game.n):
            if X != A:
                rho["P%d" % (X + 1)] = float(-D[X] / D[A])
    rec = {"infoset": I.id, "player": A + 1, "hand": I.hand_label, "history": I.history,
           "move": "%s->%s" % (I.actions[a_from], I.actions[a_to]),
           "prob_from": float(probs[iset, a_from]), "prob_to": float(probs[iset, a_to]),
           "feasible": bool(feasible),
           "D": [float(x) for x in D] if not exact else [str(x) for x in D],
           "D_sum": float(sum(D)), "class": cls, "rho": rho,
           "rho_sum": (sum(rho.values()) if rho else None),
           "tol_num": float(tol_num), "tol_eq": float(tol_eq),
           "units": "bb per unit probability moved, expectation over the root prior"}
    return rec


def binary_records(game, probs, max_r, isets=None) -> List[dict]:
    """For every binary information set: the feasible direction that INCREASES the aggressive
    action (index 1) if x < 1, otherwise the decrease (orientation-invariant rho)."""
    out = []
    for I in (game.isets if isets is None else [game.isets[i] for i in isets]):
        if len(I.actions) != 2:
            continue
        x = probs[I.index, 1]
        if x < 1:
            out.append(incidence_record(game, probs, I.index, 1, 0, max_r))
        else:
            out.append(incidence_record(game, probs, I.index, 0, 1, max_r))
    return out
