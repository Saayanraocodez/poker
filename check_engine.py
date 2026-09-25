"""Structural sanity checks on the game engine (no equilibrium theory yet)."""
import collections

import numpy as np

import kuhn3p as K

print("leaves          :", K.NLEAF, "=", K.NLEAF // 24, "per deal x 24 deals")
print("deals           :", len(K.DEALS))
print("leaf zero-sum   :", bool(np.all(np.abs(K.PAY.sum(axis=1)) < 1e-12)))

rng = np.random.default_rng(0)
sums = [float(K.utilities(rng.random(48)).sum()) for _ in range(5)]
print("sum u_i (random):", ["%.3e" % s for s in sums])

# every deal's leaf probabilities must sum to 1
q = np.empty(49)
q[:48] = rng.random(48)
q[48] = 1.0
w = np.where(K.AGG, q[K.IDX], 1 - q[K.IDX]).prod(axis=1)
s = collections.defaultdict(float)
for r in range(K.NLEAF):
    s[tuple(K.HOLDER[r])] += w[r]
print("per-deal prob=1 :", all(abs(v - 1) < 1e-12 for v in s.values()),
      " (", len(s), "deals )")

# --- reproduce the two worked examples printed in the paper -------------------
# Section 2: leaf "a13" in deal 124 contributes -2*kappa*(1-a11)*b21*(1-c42)*a13
# to u1.  Find that leaf in our table and check its factors and payoff.
want = {"deal": (1, 2, 4)}
for d, factors, pay in K.ROWS:
    if d != want["deal"]:
        continue
    names = [(K.PARAM_NAME[i], agg) for i, agg in factors]
    if names == [("a11", False), ("b21", True), ("c42", False), ("a13", True)]:
        print("paper leaf a13  : factors", names, "payoff", pay,
              " expected (-2, 3, -1)")
print("engine checks done")
