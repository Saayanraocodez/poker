"""The off-path mechanism: an unreached response parameter theta that changes the payoff split of
an upstream deviation by ANOTHER player.

theta is the probability of one action (or a class of information sets moved together, e.g. all
combos of a hand class at one history).  The upstream deviation moves mass at information set(s)
U of player A.  Because every payoff is multilinear and theta and U lie on a common path:

    D_i(theta) = D_i(0) + theta * (D_i(1) - D_i(0))        (affine in theta, exactly),

so the cross effect  C_i = D_i(1) - D_i(0)  is a mixed second difference, and the root
theta* = -D_A(0) / C_A is exact (rational in exact arithmetic).

A simple pole of rho(A -> X) along the family sigma(theta) needs ALL of:
    (a) D_A(theta*) = 0 with theta* in [0, 1];
    (b) D_X(theta*) != 0 (non-vanishing numerator);
    (c) C_A != 0 (non-zero slope of the denominator);
    (d) the equilibrium (or stated approximate-equilibrium) condition along the family near
        theta*, checked with full best responses: every r_i(theta) on the side(s) of theta*
        kept by the family stays within the declared tolerance.
A large ratio alone is never reported as a pole.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Sequence

import numpy as np

from .bestresponse import residuals
from .evaluate import infoset_reach, is_exact, utilities, with_action


def set_theta(game, probs, theta_isets: Sequence[int], action: int, theta):
    """Rows of theta_isets: probability theta on ``action``, 1 - theta on the other (binary)."""
    p = probs.copy()
    for i in theta_isets:
        assert len(game.isets[i].actions) == 2
        p[i, action] = theta
        p[i, 1 - action] = 1 - theta
    return p


def upstream_D(game, probs, up_isets: Sequence[int], a_to: int, a_from: int):
    """Sum over the upstream sets of the per-set transfer derivatives (first-order)."""
    tot = None
    for i in up_isets:
        d = utilities(game, with_action(game, probs, i, a_to)) - utilities(game, with_action(game, probs, i, a_from))
        tot = d if tot is None else tot + d
    return tot


def deviate(game, probs, up_isets, a_to):
    p = probs.copy()
    for i in up_isets:
        p = with_action(game, p, i, a_to)
    return p


def sweep(game, probs, theta_isets, theta_action, up_isets, up_to, up_from, thetas) -> List[dict]:
    out = []
    for th in thetas:
        p = set_theta(game, probs, theta_isets, theta_action, th)
        res = residuals(game, p)
        u = res["utilities"]
        D = upstream_D(game, p, up_isets, up_to, up_from)
        rb = infoset_reach(game, p)["total"]
        rd = infoset_reach(game, deviate(game, p, up_isets, up_to))["total"]
        A = game.isets[up_isets[0]].player
        rho = {("P%d" % (X + 1)): (float(-D[X] / D[A]) if D[A] != 0 else None) for X in range(game.n) if X != A}
        out.append({"theta": float(th), "u": [float(x) for x in u], "r": [float(x) for x in res["r"]],
                    "nashconv": float(res["nashconv"]), "D": [float(x) for x in D],
                    "rho_raw": rho,
                    "theta_reach_baseline": float(sum(rb[i] for i in theta_isets)),
                    "theta_reach_under_deviation": float(sum(rd[i] for i in theta_isets)),
                    "up_reach_baseline": float(sum(rb[i] for i in up_isets))})
    return out


def root_analysis(game, probs, theta_isets, theta_action, up_isets, up_to, up_from) -> Dict:
    """Exact affine structure of D(theta) and the root theta*."""
    one = Fraction(1) if is_exact(probs) else 1.0
    zero = Fraction(0) if is_exact(probs) else 0.0
    D0 = upstream_D(game, set_theta(game, probs, theta_isets, theta_action, zero), up_isets, up_to, up_from)
    D1 = upstream_D(game, set_theta(game, probs, theta_isets, theta_action, one), up_isets, up_to, up_from)
    A = game.isets[up_isets[0]].player
    C = D1 - D0
    rec = {"D_at_0": [float(x) for x in D0], "D_at_1": [float(x) for x in D1],
           "cross_effect": [float(x) for x in C], "deviator": A + 1}
    if C[A] == 0:
        rec["theta_star"] = None
        rec["status"] = "no root: denominator does not depend on theta"
        return rec
    ts = -D0[A] / C[A]
    rec["theta_star"] = float(ts)
    rec["theta_star_exact"] = str(ts) if is_exact(probs) else None
    rec["in_unit_interval"] = bool(0 <= ts <= 1)
    num = D0 + ts * C
    rec["D_at_theta_star"] = [float(x) for x in num]
    return rec
