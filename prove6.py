"""Parallel, checkpointed driver for bnb6:  is  {a_coord >= delta}  free of Nash equilibria?

    python prove6.py <coord> <delta> <workers> <maxnodes> <tag> [chunk] [rule] [mode]

mode = "nash" (strong rules only; the claim is about every Nash equilibrium) or
       "seq"  (bnb5's weak rules added; the claim is about every SEQUENTIAL
               equilibrium -- see bnb6.propagate).

Round-based work distribution.  A pool of open boxes lives in the driver; each
round every box is handed to a worker as a job, the worker runs bnb6.search on
it for at most `chunk` nodes and returns either PROVED (its subtree is empty),
SURVIVOR (a box of width < 1e-9 passed every rule -- a candidate equilibrium,
reported and the run stops), or OPEN (its unfinished stack, which goes back
into the pool).  The pool is checkpointed to ck6_<tag>.npz after every round
with a signature of the problem, so a killed run resumes where it was and a
checkpoint from a different problem is refused.

Verdicts:
    PROVED        pool empty: no point of the region satisfies the first-order
                  Nash conditions in box semantics => no Nash equilibrium there.
    NOT PROVED    a survivor box; its centre is re-checked with eqtools.expl.
    INCONCLUSIVE  node cap reached; the pool is on disk.
"""
import numpy as np, sys, time, os
from multiprocessing import Pool
import bnb6, kuhn3p as K

I = K.NAME_IDX


def _job(a):
    LO, HI, chunk, rule, weak = a
    v, n, rest = bnb6.search(LO, HI, maxnodes=chunk, rule=rule, weak=weak)
    if v is True:
        return ("proved", n, None)
    if v is False:
        return ("survivor", n, rest)
    L = np.concatenate([s[0] for s in rest]); H = np.concatenate([s[1] for s in rest])
    return ("open", n, (L, H))


def _sig(coord, delta, rule, weak):
    return np.array([I[coord], delta, {"slope": 0, "width": 1}[rule], int(weak)], float)


def save(ck, L, H, nodes, rounds, elapsed, sig):
    tmp = ck + ".tmp.npz"
    np.savez(tmp, L=L, H=H, nodes=nodes, rounds=rounds, elapsed=elapsed, sig=sig)
    for k in range(8):
        try:
            os.replace(tmp, ck + ".npz"); return
        except PermissionError:
            time.sleep(0.5)
    raise


if __name__ == "__main__":
    coord, delta, nw, maxnodes, tag = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    chunk = int(sys.argv[6]) if len(sys.argv) > 6 else 4000
    rule = sys.argv[7] if len(sys.argv) > 7 else "slope"
    mode = sys.argv[8] if len(sys.argv) > 8 else "nash"
    weak = {"nash": False, "seq": True}[mode]
    KIND = "sequential" if weak else "Nash"
    ck = "ck6_%s" % tag
    sig = _sig(coord, delta, rule, weak)
    nodes = 0; rounds = 0; elapsed0 = 0.0
    if os.path.exists(ck + ".npz"):
        with np.load(ck + ".npz") as z:
            if not np.array_equal(z["sig"], sig):
                raise SystemExit("checkpoint %s belongs to a different problem; delete it or change the tag" % ck)
            L, H = z["L"], z["H"]; nodes = int(z["nodes"]); rounds = int(z["rounds"]); elapsed0 = float(z["elapsed"])
        print("resumed %s: %d boxes, %d nodes, %d rounds, %.0fs" % (ck, len(L), nodes, rounds, elapsed0), flush=True)
    else:
        LO = np.zeros((1, 48)); HI = np.ones((1, 48)); LO[0, I[coord]] = delta
        # breadth-first warm-up in the driver so every worker has something to do
        L, H = LO, HI
        while 0 < len(L) < 4 * nw:
            nL, nH, al, DLO, DHI, SL, SK = bnb6.propagate(L, H, weak=weak)
            nL, nH, SL, SK = nL[al], nH[al], SL[al], SK[al]
            nodes += len(L)
            if len(nL) == 0:
                L, H = nL, nH; break
            j = bnb6.choose_split(nL, nH, SL, SK, rule)
            mid = 0.5 * (nL[np.arange(len(nL)), j] + nH[np.arange(len(nL)), j])
            L = np.repeat(nL, 2, axis=0); H = np.repeat(nH, 2, axis=0)
            r = np.arange(len(nL))
            H[2 * r, j] = mid; L[2 * r + 1, j] = mid
        print("warm-up: %d boxes from %d nodes" % (len(L), nodes), flush=True)
    print("claim: no %s equilibrium with %s >= %g   workers %d  chunk %d  rule %s  cap %d" % (KIND, coord, delta, nw, chunk, rule, maxnodes), flush=True)
    t0 = time.time() - elapsed0
    verdict = None
    with Pool(nw) as pool:
        while len(L) > 0:
            rounds += 1
            # group rows into jobs of up to 16 boxes (search handles a batch as one stack entry)
            jobs = [(L[s:s+16], H[s:s+16], chunk, rule, weak) for s in range(0, len(L), 16)]
            newL = []; newH = []; surv = None; rn = 0
            for kind, n, rest in pool.imap_unordered(_job, jobs):
                rn += n
                if kind == "survivor" and surv is None:
                    surv = rest
                elif kind == "open":
                    newL.append(rest[0]); newH.append(rest[1])
            nodes += rn
            L = np.concatenate(newL) if newL else np.zeros((0, 48)); H = np.concatenate(newH) if newH else np.zeros((0, 48))
            el = time.time() - t0
            print("round %d  nodes %d (+%d)  open boxes %d  %.0fs  %.1f nodes/s" % (rounds, nodes, rn, len(L), el, nodes / max(el, 1e-9)), flush=True)
            save(ck, L, H, nodes, rounds, el, sig)
            if surv is not None:
                lo, hi = surv
                x = 0.5 * (lo + hi)
                import eqtools as E
                print("\nNOT PROVED: a box of width < 1e-9 survives every rule.  centre:", flush=True)
                print("   " + ", ".join("%s=%.6f" % (K.PARAM_NAME[i], x[i]) for i in range(48)), flush=True)
                print("   exploitability at the centre: %.3e" % np.abs(E.expl(x)).max(), flush=True)
                np.save("survivor6_%s.npy" % tag, x)
                verdict = False; break
            if nodes > maxnodes:
                print("\nINCONCLUSIVE at %d nodes: %d boxes open (checkpointed)" % (nodes, len(L)), flush=True)
                verdict = None; break
        else:
            verdict = True
            print("\nPROVED: no %s equilibrium has %s >= %g.   %d nodes, %d rounds, %.0fs" % (KIND, coord, delta, nodes, rounds, time.time() - t0), flush=True)
