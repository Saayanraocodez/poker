"""Controls on enum6's silent-branch leaf set against the old enumeration.

  A. SOUNDNESS DIRECTION (new pruning is a superset of old pruning):
     every new leaf must match an old pattern of pats_0000.npy on all of the
     new leaf's non-DC coordinates.  A new leaf with no old match would mean
     the new tree branched where the old did not -- impossible if the code is
     what it claims to be.
  B. COMPLETENESS (nothing feasible was lost):
     every pattern known to carry a certified equilibrium -- surv_pat_samp,
     surv_pat_rest, and the 869 certified in lmdeep -- must match a new leaf
     (agreeing on the new leaf's non-DC coordinates).
  C. WHAT IS LEFT: new leaves matching no certified pattern, and how they
     relate to the 12,910 patterns the depth-36 chain left undecided.
"""
import numpy as np, sys
import kuhn3p as K, eqtools as E

U, MIX, DC = 9, 2, 3
tag = sys.argv[1] if len(sys.argv) > 1 else "silent"
L = np.load("enum6_pat_%s.npy" % tag).astype(np.int8)
print("new leaves: %d   label histogram %s" % (len(L), dict(zip(*[x.tolist() for x in np.unique(L, return_counts=True)]))))
old = np.load("pats_0000.npy", mmap_mode="r")
print("old patterns: %d" % old.shape[0])


def matches(P, Q):
    """for each row p of P: does some row q of Q agree with p on p's non-DC coordinates?"""
    out = np.zeros(len(P), bool)
    Q = np.asarray(Q)
    for k, p in enumerate(P):
        m = p != DC
        out[k] = bool((Q[:, m] == p[m]).all(axis=1).any())
    return out


# A
ok = np.zeros(len(L), bool)
step = 500000
for k, p in enumerate(L):
    m = p != DC
    hit = False
    for s in range(0, old.shape[0], step):
        blk = np.asarray(old[s:s+step])
        if (blk[:, m] == p[m]).all(axis=1).any(): hit = True; break
    ok[k] = hit
print("A. every new leaf matches an old pattern: %d of %d   %s" % (ok.sum(), len(L), "OK" if ok.all() else "*** FAIL"))

# B
cert = [np.load("surv_pat_samp.npy"), np.load("surv_pat_rest.npy")]
X = np.load("lmdeep_x_und.npy"); Pu = np.load("lmdeep_pat_und.npy")
ex = np.array([np.abs(E.expl(q)).max() for q in X])
cert.append(Pu[ex < 1e-13])
C = np.unique(np.concatenate(cert).astype(np.int8), axis=0)
# a certified pattern c matches a new leaf l if they agree on l's non-DC coords
okB = np.zeros(len(C), bool)
for k, c in enumerate(C):
    m = (L != DC)
    okB[k] = bool(((L == c[None, :]) | ~m).all(axis=1).any())
print("B. every certified-equilibrium pattern (%d distinct) is a new leaf: %d   %s" % (len(C), okB.sum(), "OK" if okB.all() else "*** FAIL"))
if not okB.all():
    print("   missing:", np.flatnonzero(~okB)[:10])

# C
covered = np.zeros(len(L), bool)
for k, l in enumerate(L):
    m = l != DC
    covered[k] = bool((C[:, m] == l[m]).all(axis=1).any())
rest = L[~covered]
np.save("enum6_restidx_%s.npy" % tag, np.flatnonzero(~covered))
print("C. new leaves carrying a certified equilibrium: %d ; remaining (undecided) leaves: %d" % (covered.sum(), len(rest)))
und = np.load("pats_undecided2.npy").astype(np.int8)
if len(rest):
    inund = matches(rest, und)
    print("   of the remaining, matching one of the 12,910 previously undecided: %d" % inund.sum())
    np.save("enum6_rest_%s.npy" % tag, rest)
# how many of the 12,910 undecided survive as new leaves at all
surv = np.zeros(len(und), bool)
for k, u in enumerate(und):
    m = (L != DC)
    surv[k] = bool(((L == u[None, :]) | ~m).all(axis=1).any())
print("   of the 12,910 previously undecided patterns, still present as new leaves: %d  (the other %d are now PROVEN infeasible by propagation)" % (surv.sum(), len(und) - surv.sum()))
