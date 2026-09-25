"""Quick single-process probes of bnb6 on P1-betting claims.
usage: python probe6.py <coord> <delta> <maxnodes> [rule] [contract] [weak]"""
import numpy as np, sys, time, bnb6, kuhn3p as K
I = K.NAME_IDX
coord, delta, maxnodes = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
rule = sys.argv[4] if len(sys.argv) > 4 else "slope"
contract = (sys.argv[5] != "0") if len(sys.argv) > 5 else True
weak = (sys.argv[6] != "0") if len(sys.argv) > 6 else False
LO = np.zeros(48); HI = np.ones(48); LO[I[coord]] = delta
t0 = time.time()
v, n, rest = bnb6.search(LO, HI, maxnodes=maxnodes, rule=rule, contract=contract, log=2000, weak=weak)
dt = time.time() - t0
if v is True:
    print("PROVED: no %s equilibrium has %s >= %g   (%d nodes, %.0fs, rule=%s contract=%s weak=%s)" % ("SEQUENTIAL" if weak else "Nash", coord, delta, n, dt, rule, contract, weak))
elif v is False:
    lo, hi = rest
    print("NOT PROVED: a width<1e-9 box survived after %d nodes (%.0fs):" % (n, dt))
    print("   " + ", ".join("%s=%.6f" % (K.PARAM_NAME[i], 0.5 * (lo[i] + hi[i])) for i in range(48)))
else:
    left = sum(s[0].shape[0] for s in rest)
    print("INCONCLUSIVE at %d nodes, %d boxes left (%.0fs, %.1f ms/node, rule=%s contract=%s weak=%s)" % (n, left, dt, 1000 * dt / n, rule, contract, weak))
