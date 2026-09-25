"""
Close A: exhaustive support enumeration at (3,4).

CFR tells us which coordinates are confidently pure and which are ambiguous.
For each ambiguous coordinate the only question is binary -- is it interior at
equilibrium, or is it pure at the nearest of {0,1}?  With k ambiguous
coordinates that is 2^k support hypotheses; each one fixes a square indifference
system that Newton either solves to machine precision or fails to solve.

A hypothesis is CERTIFIED when the resulting profile has exploitability below
1e-12, which makes it an exact Nash equilibrium up to floating point.
"""
import itertools, json, time
import numpy as np
import kuhnGen as Q, cfrGen as CG, certify as C, poletest as PT


def _train(a):
    it, s = a
    return CG.train(Q.Kuhn(3, 4), it, seed=s).tolist()


def enumerate_support(g, p0, cand, iters=25, tol=1e-12, verbose=True):
    found = []
    t = time.time()
    for m, mask in enumerate(itertools.product((0, 1), repeat=len(cand))):
        q = np.array(p0, float)
        S = []
        for c, bit in zip(cand, mask):
            if bit:
                S.append(c)
            else:
                q[c] = 1.0 if p0[c] > 0.5 else 0.0
        r, h = C.newton(g, q, S, iters=iters)
        e = float(np.abs(g.exploitability_bi(r)).max())
        if e < tol:
            found.append(dict(mask=mask, interior=S, expl=e, profile=r.copy()))
        if verbose and (m + 1) % 128 == 0:
            print("      %d/%d hypotheses, %d certified, %.0fs"
                  % (m + 1, 2 ** len(cand), len(found), time.time() - t))
    return found


def in_sgs_family(g, p):
    """Map a (3,4) profile back to kuhn3p order and test Table 3 membership."""
    import kuhn3p as K, family as F
    perm = np.empty(48, int)
    for pl in range(3):
        for j in range(1, 5):
            for h, k in Q.SGS_SIT[pl].items():
                perm[K.NAME_IDX["%s%d%d" % ("abc"[pl], j, k)]] = g.pidx(pl, j, h)
    q = p[perm]                                     # now in kuhn3p ordering
    I = K.NAME_IDX
    free = dict(b11=q[I["b11"]], b21=q[I["b21"]], b23=q[I["b23"]],
                b32=q[I["b32"]], c11=q[I["c11"]], c33=q[I["c33"]],
                c34=q[I["c34"]])
    rebuilt = F.make_profile(**free)
    dev = float(np.abs(rebuilt - q).max())
    return dev, {k: round(float(v), 6) for k, v in free.items()}


def main():
    import multiprocessing as mp
    g = Q.Kuhn(3, 4)
    ITERS = 8000000          # long run: shrinks the ambiguous set
    import os
    cache = "cfr34_%d.json" % ITERS
    if os.path.exists(cache):
        P = [np.array(x) for x in json.load(open(cache))]
        print("   (loaded cached CFR profiles)")
    else:
        with mp.Pool(4) as pool:
            P = [np.array(x) for x in pool.map(_train, [(ITERS, s) for s in range(4)])]
        json.dump([x.tolist() for x in P], open(cache, "w"))
    V = np.array(P)
    # ambiguous = not confidently pure across every seed
    cand = [i for i in range(g.nparam)
            if not (V[:, i].max() < 5e-3 or V[:, i].min() > 1 - 5e-3)]
    MAXC = 13                # 2^13 = 8192 hypotheses is the practical ceiling
    if len(cand) > MAXC:
        # keep the genuinely ambiguous ones; snap those already nearly pure
        dist = {i: min(V[:, i].mean(), 1 - V[:, i].mean()) for i in cand}
        cand = sorted(sorted(cand, key=lambda i: -dist[i])[:MAXC])
        print("   (capped to the %d most ambiguous)" % MAXC)
    print("(3,4): %d ambiguous coordinates -> %d support hypotheses"
          % (len(cand), 2 ** len(cand)))
    print("   %s\n" % ", ".join(g.name(i) for i in cand))
    p0 = np.array(min(P, key=lambda q: np.abs(g.exploitability_bi(q)).max()))
    for i in range(g.nparam):
        if i not in cand:
            p0[i] = 1.0 if p0[i] > 0.5 else 0.0
    found = enumerate_support(g, p0, cand)
    print("\n   CERTIFIED: %d of %d hypotheses reach exploitability < 1e-12"
          % (len(found), 2 ** len(cand)))
    seen = []
    for f in found:
        dev, free = in_sgs_family(g, f["profile"])
        nint = len(f["interior"])
        noff = len(PT.offpath(g, f["profile"]))
        seen.append(dict(nint=nint, noff=noff, expl=f["expl"], dev=dev, free=free,
                         profile=f["profile"].tolist()))
    seen.sort(key=lambda d: (-d["nint"], d["dev"]))
    print("\n   interior  off-path  exploitability   dist to SGS family   free params")
    for d in seen[:14]:
        tag = "IN FAMILY" if d["dev"] < 1e-9 else "dev %.2e" % d["dev"]
        print("   %-9d %-9d %-16.2e %-20s %s" % (d["nint"], d["noff"], d["expl"], tag, d["free"]))
    json.dump([{k: v for k, v in d.items()} for d in seen], open("supports_34.json", "w"))
    infam = sum(1 for d in seen if d["dev"] < 1e-9)
    print("\n   %d/%d certified equilibria lie in the SGS Table 3 family; %d do NOT"
          % (infam, len(seen), len(seen) - infam))


if __name__ == "__main__":
    main()
