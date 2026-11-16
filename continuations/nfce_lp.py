"""Continuation 2, the strong form: NORMAL-FORM correlated equilibria.

In a normal-form correlated equilibrium each player is told its WHOLE pure strategy (a plan for every
card) and no deviation that may depend on all of it gains.  Payoffs are additive over the player's
cards, so the constraints are: for every player i, recommended strategy sigma_i, card c and plan tau,
     sum_{s_-i} pi(sigma_i, s_-i) ( u_(i,c)(s) - u_(i,c)(tau, s_-i) ) >= 0.
This is the smallest correlated-equilibrium set of the normal form: if P1 can bet in one of these, no
Lagrangian / correlated-equilibrium certificate of any kind proves P1's silence.

LP on a product set S1 x S2 x S3 of candidate strategies, with ALL deviation rows of every candidate;
maximise P(P1 bets).  The candidate sets grow by adding, for each player, the strategies that best
respond card by card to the conditional distributions of the current solution, and "bet" variants.
usage:  python nfce_lp.py [rounds=6] [seed=0] [cap per player=40]
"""
import sys, json, itertools, time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
import ce_lp as C

rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
CAP = int(sys.argv[3]) if len(sys.argv) > 3 else 40
rng = np.random.default_rng(seed)
NPL = C.NPL


def strat_of(s, pl): return tuple(s[C.AIDX[(pl, c)]] for c in range(1, 5))


_colcache = {}
def col(s):
    if s not in _colcache: _colcache[s] = C.column(s)
    return _colcache[s]


def build_and_solve(SS):
    """SS[pl] = list of strategies (4-tuples of plan indices).  -> value, pi (dict profile -> weight), duals"""
    idx = [{st: i for i, st in enumerate(SS[pl])} for pl in range(3)]
    rowbase = []; nrows = 0
    for pl in range(3):
        rowbase.append(nrows); nrows += len(SS[pl]) * 4 * NPL[pl]
    def rowid(pl, si, c, tau): return rowbase[pl] + (si * 4 + (c - 1)) * NPL[pl] + tau
    profiles = [s1 + s2 + s3 for s1 in SS[0] for s2 in SS[1] for s3 in SS[2]]
    R = []; Cc = []; V = []; f = np.zeros(len(profiles))
    for j, s in enumerate(profiles):
        f[j] = C.fobj(s)
        cc = col(s)
        for (k, rho, tau), v in cc.items():
            if v == 0: continue
            pl, c = C.AG[k]
            R.append(rowid(pl, idx[pl][strat_of(s, pl)], c, tau)); Cc.append(j); V.append(v)
    A = coo_matrix((V, (R, Cc)), shape=(nrows, len(profiles))).tocsr()
    res = linprog(-f, A_ub=-A, b_ub=np.zeros(nrows), A_eq=np.ones((1, len(profiles))), b_eq=[1.0], bounds=(0, None), method='highs')
    if res.status != 0: return None, None, None, profiles
    return -res.fun, res.x, -res.ineqlin.marginals, profiles


def best_card_responses(profiles, pi, pl):
    """strategies of player pl that best respond, card by card, to the conditional distribution given each recommended strategy."""
    out = set()
    groups = {}
    for s, w in zip(profiles, pi):
        if w > 1e-9: groups.setdefault(strat_of(s, pl), []).append((s, w))
    for st, lst in groups.items():
        best = []
        for c in range(1, 5):
            k = C.AIDX[(pl, c)]; vals = np.zeros(NPL[pl])
            for s, w in lst:
                for tau in range(NPL[pl]):
                    s2 = list(s); s2[k] = tau; vals[tau] += w * C.u_agent(tuple(s2), (pl, c))
            best.append(int(np.argmax(vals)))
        out.add(tuple(best))
    return out


if __name__ == "__main__":
    t0 = time.time()
    d = json.load(open('ce_witness.json'))
    prof = [tuple(s) for s, w in d['support']]
    wts = np.array([float(w) for s, w in d['support']]); wts /= wts.sum()
    SS = []
    for pl in range(3):
        score = {}
        for s, w in zip(prof, wts): score[strat_of(s, pl)] = score.get(strat_of(s, pl), 0) + w
        SS.append([st for st, _ in sorted(score.items(), key=lambda t: -t[1])[:CAP]])
    print("candidate strategies from the type-agent equilibrium: %s" % [len(x) for x in SS], flush=True)
    best = (0.0, None)
    for rd in range(rounds):
        val, pi, mu, profiles = build_and_solve(SS)
        if val is None: print("LP failed"); break
        print("round %d  strategies %s  profiles %d  max P(P1 bets) over normal-form CE on this product set = %.10f   (%.0fs)"
              % (rd, [len(x) for x in SS], len(profiles), val, time.time() - t0), flush=True)
        if val > best[0] + 1e-12:
            best = (val, [(list(map(int, s)), float(w)) for s, w in zip(profiles, pi) if w > 1e-10])
            json.dump(dict(value=val, support=best[1], strategies=[[list(map(int, st)) for st in x] for x in SS]), open('nfce_lp_%d.json' % seed, 'w'))
        # grow the candidate sets
        added = 0
        for pl in range(3):
            new = best_card_responses(profiles, pi, pl)
            # variants: one card's plan replaced at random / P1 opening bets
            cur = list(SS[pl])
            for _ in range(12):
                st = list(cur[rng.integers(len(cur))]); st[rng.integers(4)] = int(rng.integers(NPL[pl])); new.add(tuple(st))
            if pl == 0:
                betplan = int(np.flatnonzero(C.OPEN)[0])
                for st in cur[:8]:
                    for c in range(4):
                        t = list(st); t[c] = betplan; new.add(tuple(t))
            for st in new:
                if st not in SS[pl] and len(SS[pl]) < CAP + 14 * (rd + 1): SS[pl].append(st); added += 1
        if added == 0: break
    print("best value %.10f" % best[0])
