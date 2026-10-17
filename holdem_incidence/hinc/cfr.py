"""Tabular full-traversal CFR variants (candidate generators, not certifiers).

Variants
* ``cfr``  -- vanilla CFR: regret matching, simultaneous updates, uniform averaging.
* ``cfr+`` -- CFR+: regret matching+, regrets floored at 0, alternating updates (P1, P2, P3),
  linear averaging with weight max(t - delay, 0).
* ``dcfr`` -- discounted CFR (alpha=1.5, beta=0, gamma=2), alternating updates.

Averaging rule: the average strategy of information set I is
    sum_t w_t * own_reach^t(I) * sigma^t(I) / sum_t w_t * own_reach^t(I),
own_reach = the owner's own probability of reaching I under sigma^t.  The denominator is stored
per information set (``W``).  If it is exactly 0 (the owner never reached I with positive
averaging weight), the average is UNDEFINED; the documented fallback is the final CURRENT
strategy at I, and every such set is listed in the run record.  Off-path completion is part of
the research object, so this is never filled silently.

Initialisation: seed 0 = all regrets 0 (uniform current strategy).  Seed s > 0 = initial
cumulative regrets drawn i.i.d. Uniform(0, init_scale) on legal actions (numpy default_rng(s)),
i.e. a random initial current strategy.  No exploration floor is used, so the strategy that is
trained is the strategy that is evaluated.

Three-player CFR has no convergence guarantee to Nash; outputs are described by their measured
best-response residuals only.
"""
from __future__ import annotations

import json
import time
from typing import List, Optional

import numpy as np

from .bestresponse import residuals
from .evaluate import reach, values, utilities, infoset_reach

VARIANTS = ("cfr", "cfr+", "dcfr")


class CFR:
    def __init__(self, game, variant: str = "cfr+", seed: int = 0, init_scale: float = 1.0,
                 avg_delay: int = 0, dcfr=(1.5, 0.0, 2.0), fixed=None):
        if variant not in VARIANTS:
            raise ValueError("variant must be one of %s" % (VARIANTS,))
        self.game, self.variant, self.seed = game, variant, seed
        self.init_scale, self.avg_delay, self.dcfr = init_scale, avg_delay, dcfr
        # fixed rows: {infoset index: probability row}; never updated (a RESTRICTED game, e.g.
        # P1's opening forced to check).  Recorded in the run state.
        self.fixed = {int(k): np.asarray(v, dtype=float) for k, v in (fixed or {}).items()}
        shape = (game.n_isets, game.max_actions)
        self.legal = game.legal.astype(float)
        self.R = np.zeros(shape)
        if seed > 0:
            rng = np.random.default_rng(seed)
            self.R = rng.uniform(0.0, init_scale, size=shape) * self.legal
        self.S = np.zeros(shape)
        self.W = np.zeros(game.n_isets)
        self.t = 0
        self.history: List[dict] = []
        self.wall = 0.0
        # per player: the decision nodes it owns
        self.player_nodes = {p: [nd for nd in game.tree.decision_nodes if nd.actor == p] for p in range(game.n)}

    # ---------------------------------------------------------------- strategies
    def current(self) -> np.ndarray:
        pos = np.maximum(self.R, 0.0) * self.legal
        tot = pos.sum(axis=1, keepdims=True)
        k = self.legal.sum(axis=1, keepdims=True)
        cur = np.where(tot > 0, pos / np.where(tot > 0, tot, 1.0), self.legal / k)
        for i, row in self.fixed.items():
            cur[i] = row
        return cur

    def average(self, fallback: str = "current"):
        """(profile, zero-weight information sets).  Fallback rule documented above."""
        cur = self.current()
        avg = np.where(self.W[:, None] > 0, self.S / np.where(self.W[:, None] > 0, self.W[:, None], 1.0), cur)
        zero = [int(i) for i in np.nonzero(self.W == 0)[0]]
        if fallback != "current":
            raise ValueError("only the documented 'current' fallback is implemented")
        # exact renormalisation of tiny float drift
        avg = avg * self.legal
        avg = avg / avg.sum(axis=1, keepdims=True)
        return avg, zero

    # ---------------------------------------------------------------- one pass
    def _cf(self, sigma, players):
        """Regret increments and own reach for the listed players under sigma."""
        g = self.game
        Rr = reach(g, sigma)
        V = values(g, sigma)
        inc = np.zeros_like(self.R)
        own = np.zeros(g.n_isets)
        for p in players:
            for nd in self.player_nodes[p]:
                base = g.iset_base[nd.id]
                H = len(g.seats[p].hands)
                others = np.delete(Rr[nd.id], p, axis=1).prod(axis=1)
                w = g.prior_f * others
                hands = g.deals[:, p]
                s = sigma[base:base + H, :len(nd.actions)]
                Q = np.stack([V[c][:, p] for c in nd.children], axis=1)        # [D, A]
                v = (s[hands] * Q).sum(axis=1)
                for a in range(len(nd.actions)):
                    inc[base:base + H, a] = np.bincount(hands, weights=w * (Q[:, a] - v), minlength=H)
                own[base:base + H] = Rr[nd.id][g.first_deal[p], p]
        return inc, own

    def iterate(self) -> None:
        self.t += 1
        t = self.t
        g = self.game
        if self.variant == "cfr":
            sigma = self.current()
            inc, own = self._cf(sigma, range(g.n))
            for i in self.fixed:
                inc[i] = 0.0
            self.R += inc
            self.S += own[:, None] * sigma
            self.W += own
            return
        for p in range(g.n):
            sigma = self.current()
            inc, own = self._cf(sigma, [p])
            for i in self.fixed:
                inc[i] = 0.0
            mask = np.array([I.player == p for I in g.isets])
            if self.variant == "cfr+":
                self.R[mask] = np.maximum(self.R[mask] + inc[mask], 0.0)
                w = max(t - self.avg_delay, 0)
            else:  # dcfr: discount accumulated regrets, then add; average weight t^gamma, which
                # equals DCFR's multiplicative (t/(t+1))^gamma discounting of the running sum
                a_, b_, gm = self.dcfr
                Rp = self.R[mask]
                Rp = np.where(Rp > 0, Rp * (t ** a_ / (t ** a_ + 1)), Rp * (t ** b_ / (t ** b_ + 1)))
                self.R[mask] = Rp + inc[mask]
                w = float(t) ** gm
            self.S[mask] += w * own[mask, None] * sigma[mask]
            self.W[mask] += w * own[mask]

    # ---------------------------------------------------------------- run with records
    def measure(self) -> dict:
        avg, zero = self.average()
        cur = self.current()
        ra, rc = residuals(self.game, avg), residuals(self.game, cur)
        reach_avg = infoset_reach(self.game, avg)["total"]
        return {"t": self.t, "wall_s": round(self.wall, 3),
                "avg": {"u": [float(x) for x in ra["utilities"]], "r": [float(x) for x in ra["r"]],
                        "max_r": float(ra["max_r"]), "nashconv": float(ra["nashconv"])},
                "cur": {"u": [float(x) for x in rc["utilities"]], "r": [float(x) for x in rc["r"]],
                        "max_r": float(rc["max_r"]), "nashconv": float(rc["nashconv"])},
                "zero_weight_infosets": len(zero), "min_avg_weight": float(self.W.min()),
                "infosets_reach_below_1e-9": int((reach_avg < 1e-9).sum()),
                "infosets_reach_exactly_0": int((reach_avg == 0).sum())}

    def run(self, iters: int, checkpoints: Optional[List[int]] = None, ckpt_path: Optional[str] = None,
            log=None) -> None:
        checkpoints = sorted(set(checkpoints or [])) or [iters]
        while self.t < iters:
            t0 = time.perf_counter()
            self.iterate()
            self.wall += time.perf_counter() - t0
            if self.t in checkpoints or self.t == iters:
                rec = self.measure()
                self.history.append(rec)
                if log:
                    log("t=%d  avg NashConv=%.3e max_r=%.3e | cur NashConv=%.3e | %.1fs" % (
                        self.t, rec["avg"]["nashconv"], rec["avg"]["max_r"], rec["cur"]["nashconv"], self.wall))
                if ckpt_path:
                    self.save(ckpt_path)

    # ---------------------------------------------------------------- persistence
    def state(self) -> dict:
        return {"variant": self.variant, "seed": self.seed, "init_scale": self.init_scale,
                "avg_delay": self.avg_delay, "dcfr": list(self.dcfr), "t": self.t, "wall": self.wall,
                "fixed": {str(k): v.tolist() for k, v in self.fixed.items()},
                "game_fingerprint": self.game.fingerprint()}

    def save(self, path: str) -> None:
        np.savez(path + ".npz", R=self.R, S=self.S, W=self.W)
        with open(path + ".json", "w", encoding="utf-8") as f:
            json.dump({"state": self.state(), "history": self.history}, f, indent=1)

    @staticmethod
    def load(game, path: str) -> "CFR":
        with open(path + ".json", encoding="utf-8") as f:
            meta = json.load(f)
        st = meta["state"]
        if st["game_fingerprint"] != game.fingerprint():
            raise ValueError("checkpoint belongs to a different game")
        c = CFR(game, st["variant"], st["seed"], st["init_scale"], st["avg_delay"], tuple(st["dcfr"]),
                fixed={int(k): v for k, v in st.get("fixed", {}).items()})
        with np.load(path + ".npz") as z:
            c.R, c.S, c.W = z["R"].copy(), z["S"].copy(), z["W"].copy()
        c.t, c.wall, c.history = st["t"], st["wall"], meta["history"]
        return c
