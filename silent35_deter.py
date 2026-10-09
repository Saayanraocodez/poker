"""(3, 5): can a P1-silent check-subgame equilibrium be completed into a FULL Nash equilibrium?

In a profile where P1 never opens, the responses to a P1 bet are off the path of play: Nash does not
constrain them, they only have to DETER P1.  After P1 bets P1 never acts again, so P1's opening with
card j is unprofitable iff  du_1/da_j1 = u_1(a_j1 = 1) - u_1(a_j1 = 0) <= 0  given the rest.  The 15
off-path coordinates: P2's call after "B" and P3's call after "BF" / "BC", each per own card.
For each polished restricted profile (silent35_results.json): minimise max_j du_1/da_j1 over the 15,
multistart SLSQP.  A minimum < 0 means deterrence is possible (and P2/P3/P1-continuation must already
be optimal: their exploitabilities are reported); > 0 means this profile cannot be completed.
usage:  python silent35_deter.py [starts]"""
import sys, json
import numpy as np
from scipy.optimize import minimize
import kuhnGen as Q

G = Q.Kuhn(3, 5)
OPEN = [G.pidx(0, j, "") for j in G.cards]
OFF = [G.pidx(1, c, "B") for c in G.cards] + [G.pidx(2, c, h) for c in G.cards for h in ("BF", "BC")]


def gains(p, y):
    q = np.array(p, float); q[OFF] = y
    out = []
    for i in OPEN:
        a = q.copy(); b = q.copy(); a[i] = 1.0; b[i] = 0.0
        out.append(G.utilities(a)[0] - G.utilities(b)[0])
    return np.array(out)


def best_deterrence(p, starts, rng):
    best = None
    for k in range(starts):
        y0 = rng.random(len(OFF)) if k else np.array(p)[OFF]
        res = minimize(lambda z: z[-1], np.append(y0, gains(p, y0).max()), method="SLSQP",
                       bounds=[(0, 1)] * len(OFF) + [(None, None)],
                       constraints=[{"type": "ineq", "fun": lambda z: z[-1] - gains(p, z[:-1])}],
                       options={"maxiter": 400, "ftol": 1e-14})
        y = np.clip(res.x[:-1], 0, 1); g = gains(p, y).max()
        if best is None or g < best[0]: best = (g, y)
    return best


if __name__ == "__main__":
    starts = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    rng = np.random.default_rng(0)
    res = json.load(open("silent35_results.json"))
    out = []
    for r in res:
        p = np.array(r["profile"])
        ex = G.exploitability_bi(p)                      # P1's entry includes the (undeterred) opening deviation
        g0 = gains(p, p[OFF])
        g, y = best_deterrence(p, starts, rng)
        q = p.copy(); q[OFF] = y; exq = G.exploitability_bi(q)
        print("seed %2d: P2/P3 expl %.1e %.1e | P1 opening gains as learned %s | best deterrence: max gain %+.3e  -> full-game expl %s" % (
            r["seed"], ex[1], ex[2], np.round(g0, 4).tolist(), g, ["%.1e" % v for v in exq]), flush=True)
        out.append({"seed": r["seed"], "max_gain": g, "offpath": y.tolist(), "profile": q.tolist(), "expl": exq.tolist()})
    json.dump(out, open("silent35_deter.json", "w"))
    print("deterrable (max opening gain < 0): %d of %d" % (sum(1 for o in out if o["max_gain"] < 0), len(out)))
