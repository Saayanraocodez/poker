"""Open problem 5, part 2: full-width CFR variants on three-player Kuhn poker (vectorised over the
24 deals), with checkpoints, so that "which equilibrium does CFR pick?" can be asked per algorithm.

Variants (Zinkevich et al. 2008; Tammelin 2014; Brown & Sandholm 2019):
  cfr     vanilla CFR: regret matching, simultaneous updates, uniform averaging
  cfrp    CFR+: regret matching+, alternating updates, linear averaging (weight t)
  lcfr    Linear CFR: regrets and average both weighted by t, simultaneous updates
  dcfr    DCFR(alpha=1.5, beta=0, gamma=2), alternating updates
Full width is deterministic; a run's 'seed' perturbs the initial cumulative regrets by
N(0, 0.01) so that different runs start from different strategies (seed 0 = no perturbation).

Game: tree.py (positions, owners, coordinates per deal, payoffs), the same tree every exact
computation uses.  The average strategy is returned in the kuhn3p 48-vector layout.

usage:  python cfrfull.py <variant> <iters> <seed>   (or import run())
"""
import sys
import numpy as np
import tree as T

ND, NPOS = T.ND, T.NPOS
INT = list(T.INTERNAL)
OWN = np.array([T.OWNER[p][0] if p in T.OWNER else -1 for p in range(NPOS)])
CO = T.COORD                                   # (24, 25) info-set index at each internal position
PLAYER_OF = np.arange(48) // 16


def sweep(sig):
    """reach per player (24, 25, 3) and values (24, 25, 3) under behaviour profile sig (48,)."""
    Rp = np.ones((ND, NPOS, 3))
    for pos in INT:
        x = sig[CO[:, pos]]; i = OWN[pos]
        Rp[:, T.AGGC[pos]] = Rp[:, pos]; Rp[:, T.PASC[pos]] = Rp[:, pos]
        Rp[:, T.AGGC[pos], i] *= x; Rp[:, T.PASC[pos], i] *= 1 - x
    V = np.zeros((ND, NPOS, 3)); V[:, T.LEAFPOS] = T.PAYT[:, T.LEAFPOS]
    for pos in INT[::-1]:
        x = sig[CO[:, pos]][:, None]
        V[:, pos] = x * V[:, T.AGGC[pos]] + (1 - x) * V[:, T.PASC[pos]]
    return Rp, V


def regret_matching(R, plus=False):
    Rp = np.maximum(R, 0.0)
    s = Rp.sum(axis=1)
    sig = np.where(s > 0, Rp[:, 1] / np.where(s > 0, s, 1), 0.5)
    return sig


def instant(sig, players):
    """instantaneous counterfactual regrets (48, 2) for the given players, and own-reach-weighted
    strategy increments (48, 2)."""
    Rp, V = sweep(sig)
    r = np.zeros((48, 2)); ssum = np.zeros((48, 2))
    for pos in INT:
        i = OWN[pos]
        if i not in players: continue
        cf = np.prod(np.delete(Rp[:, pos], i, axis=1), axis=1) / ND          # others' reach x chance
        v0 = V[:, pos, i]
        da = cf * (V[:, T.AGGC[pos], i] - v0); dp = cf * (V[:, T.PASC[pos], i] - v0)
        np.add.at(r[:, 1], CO[:, pos], da); np.add.at(r[:, 0], CO[:, pos], dp)
        x = sig[CO[:, pos]]; own = Rp[:, pos, i]
        np.add.at(ssum[:, 1], CO[:, pos], own * x); np.add.at(ssum[:, 0], CO[:, pos], own * (1 - x))
    # each information set appears at one position per deal it occurs in: fine (sums over deals)
    return r, ssum


def run(variant, iters, seed=0, checkpoints=()):
    rng = np.random.default_rng(seed)
    R = np.zeros((48, 2)); S = np.zeros((48, 2))
    if seed: R += rng.normal(0.0, 0.01, size=(48, 2))
    cps = set(checkpoints); snaps = {}
    for t in range(1, iters + 1):
        if variant in ("cfr", "lcfr"):
            sig = regret_matching(R)
            r, s = instant(sig, (0, 1, 2))
            w = t if variant == "lcfr" else 1.0
            R += w * r; S += w * s
        elif variant in ("cfrp", "dcfr"):
            for i in (0, 1, 2):                                  # alternating updates
                sig = regret_matching(R)
                r, s = instant(sig, (i,))
                m = PLAYER_OF == i
                if variant == "cfrp":
                    R[m] = np.maximum(R[m] + r[m], 0.0)
                    S[m] += t * s[m]
                else:
                    a = t ** 1.5 / (t ** 1.5 + 1.0)
                    Rm = R[m] + r[m]
                    R[m] = np.where(Rm > 0, Rm * a, Rm * 0.0)     # beta = 0: negative regrets reset
                    S[m] = S[m] * ((t - 1) / t) ** 2 + s[m]        # gamma = 2
        else:
            raise ValueError(variant)
        if t in cps:
            snaps[t] = S.copy()
    tot = S.sum(axis=1)
    p = np.where(tot > 0, S[:, 1] / np.where(tot > 0, tot, 1), 0.5)
    return p, snaps


def avg_of(S):
    tot = S.sum(axis=1)
    return np.where(tot > 0, S[:, 1] / np.where(tot > 0, tot, 1), 0.5)


if __name__ == "__main__":
    import kuhn3p as K
    v, it, sd = sys.argv[1], int(float(sys.argv[2])), int(sys.argv[3])
    p, _ = run(v, it, sd)
    print(v, it, sd, "exploitability", K.exploitability(p), "u", K.utilities(p))
