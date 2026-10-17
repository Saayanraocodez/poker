"""Behavioural profiles: one probability row per information set.

A profile is an array ``probs[n_isets, max_actions]`` (float64, or dtype=object holding exact
Fractions).  Columns beyond an information set's legal actions are zero.  Saved profiles always
carry the full information-set table (stable ids, actions) and the game fingerprint, so a policy
file can never be read against the wrong game.
"""
from __future__ import annotations

import json
from fractions import Fraction
from typing import Dict, Optional

import numpy as np


def uniform(game, exact: bool = False) -> np.ndarray:
    if exact:
        p = np.full((game.n_isets, game.max_actions), Fraction(0), dtype=object)
    else:
        p = np.zeros((game.n_isets, game.max_actions))
    for I in game.isets:
        k = len(I.actions)
        for a in range(k):
            p[I.index, a] = Fraction(1, k) if exact else 1.0 / k
    return p


def to_exact(probs: np.ndarray, max_den: Optional[int] = None) -> np.ndarray:
    """Float -> Fraction.  With ``max_den`` each row is rationalised by limit_denominator and the
    LAST legal action absorbs the rounding so the row sums to 1 exactly.  This is a rounding, so
    the result must be re-verified (exact best responses) before any claim is made about it."""
    out = np.empty(probs.shape, dtype=object)
    for i in range(probs.shape[0]):
        row = []
        for a in range(probs.shape[1]):
            x = Fraction(probs[i, a]) if not isinstance(probs[i, a], Fraction) else probs[i, a]
            if max_den is not None:
                x = x.limit_denominator(max_den)
            row.append(x)
        out[i] = row
    return out


def normalise_exact(game, probs: np.ndarray) -> np.ndarray:
    """Make every row sum to exactly 1 by adjusting its last legal action (exact rows only)."""
    p = probs.copy()
    for I in game.isets:
        k = len(I.actions)
        s = sum(p[I.index, a] for a in range(k - 1))
        p[I.index, k - 1] = 1 - s
        if p[I.index, k - 1] < 0:
            raise ValueError("row %s cannot be normalised" % I.id)
    return p


def validate_profile(game, probs: np.ndarray, tol: float = 1e-12) -> None:
    exact = probs.dtype == object
    if probs.shape != (game.n_isets, game.max_actions):
        raise ValueError("profile shape does not match the game")
    for I in game.isets:
        row = probs[I.index]
        k = len(I.actions)
        for a in range(game.max_actions):
            if a >= k and row[a] != 0:
                raise ValueError("probability on an illegal action at %s" % I.id)
            if row[a] < (0 if exact else -tol):
                raise ValueError("negative probability at %s" % I.id)
        s = sum(row[:k])
        if exact:
            if s != 1:
                raise ValueError("row %s sums to %s, not exactly 1" % (I.id, s))
        elif abs(s - 1) > tol:
            raise ValueError("row %s sums to %r" % (I.id, s))


def pure(game, choice: Dict[int, int], base: Optional[np.ndarray] = None) -> np.ndarray:
    """Copy of ``base`` (or uniform) with the listed information sets set to a pure action."""
    p = (uniform(game) if base is None else base.copy())
    exact = p.dtype == object
    for i, a in choice.items():
        for b in range(game.max_actions):
            p[i, b] = (Fraction(1) if exact else 1.0) if b == a else (Fraction(0) if exact else 0.0)
    return p


def save_profile(path, game, probs: np.ndarray, extra: Optional[dict] = None) -> None:
    exact = probs.dtype == object
    rows = []
    for I in game.isets:
        k = len(I.actions)
        row = {"id": I.id, "player": I.player + 1, "hand": I.hand_label, "history": I.history,
               "actions": list(I.actions)}
        if exact:
            row["probs"] = [str(probs[I.index, a]) for a in range(k)]
        else:
            row["probs"] = [float(probs[I.index, a]) for a in range(k)]
        rows.append(row)
    doc = {"game": game.record(), "exact": exact, "infosets": rows}
    if extra:
        doc.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)


def load_profile(path, game) -> np.ndarray:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if doc["game"]["fingerprint"] != game.fingerprint():
        raise ValueError("policy file was made for a different game (fingerprint mismatch)")
    exact = doc.get("exact", False)
    probs = np.full((game.n_isets, game.max_actions), Fraction(0), dtype=object) if exact \
        else np.zeros((game.n_isets, game.max_actions))
    for row in doc["infosets"]:
        i = game.iset_by_id[row["id"]]
        if tuple(row["actions"]) != game.isets[i].actions:
            raise ValueError("action list mismatch at %s" % row["id"])
        for a, x in enumerate(row["probs"]):
            probs[i, a] = Fraction(x) if exact else float(x)
    return probs
