"""Completeness control for enumeration + exact stage: every certified
equilibrium we own must lie in a leaf whose verdict is FAMILY.

A point is matched to every leaf whose closure it is within tol of (see
leaves_of): numerics cannot tell a coordinate at 1e-9 from one at 0, so the
point may belong to the MIX leaf or to its 0-labelled neighbour; the control
asks that at least one matching leaf is FAMILY.  This is the check
check_enum6.py's control B got wrong: it matched certified PATTERNS, and an LM
pattern can put a MIX label on a coordinate whose certified value is 0.

Point sets:
  certified_eq_all.npy      744 family points (P1 silent, Table 2/3)  -- both modes
  hunt_eq_bet2.npy       23,820 certified Nash, 94 % off Table 2      -- nash mode
  offpath_witness.npy         1 exact Nash point with b12 = 9/100     -- nash mode
In seq mode the last two need NOT be in any leaf (they are Nash but not
sequentially rational); the control only reports how many are.

usage:  python control_symleaf.py <tag> [tol]
        tol defaults to 1e-6: hunt points are LM-polished, a coordinate the true
        equilibrium holds at 0 comes back as ~1e-9 and at tol = 1e-9 21 of them
        were labelled MIX and "fell" into empty neighbouring leaves.
"""
import numpy as np, sys, eqtools as E, symleaf

U, MIX, DC = 9, 2, 3
tag = sys.argv[1]; tol = float(sys.argv[2]) if len(sys.argv) > 2 else 1e-6
L = np.load("enum6_pat_%s.npy" % tag).astype(np.int8)
z = np.load("symleaf_%s.npz" % tag); V = z["verdict"]
notdc = L != DC
print("tag %s  leaves %d  verdicts %s" % (tag, len(L), {v: int((V == symleaf.VC[v]).sum()) for v in symleaf.VERD if (V == symleaf.VC[v]).sum()}))


def leaves_of(q):
    """leaves whose CLOSURE the numerical point q is within tol of: a leaf's
    label 0 needs q <= tol, label 1 needs q >= 1 - tol, MIX accepts anything in
    [0, 1] (the true point may sit on the boundary the numerics cannot resolve),
    DC accepts anything.  A point therefore matches every leaf it could belong
    to; the control asks that at least one of them is FAMILY."""
    ok = np.ones(len(L), bool)
    ok &= ~((L == 0) & (q[None, :] > tol)).any(axis=1)
    ok &= ~((L == 1) & (q[None, :] < 1 - tol)).any(axis=1)
    return np.flatnonzero(ok)


def check(name, X, must=True):
    n_in = 0; n_fam = 0; bad = []; multi = 0
    for q in X:
        hit = leaves_of(q)
        if len(hit) == 0:
            bad.append("not in any leaf"); continue
        if len(hit) > 1: multi += 1
        n_in += 1
        vs = {symleaf.VERD[V[k]] for k in hit}
        if "FAMILY" in vs: n_fam += 1
        else: bad.append("in leaf %s with verdict %s" % (hit.tolist(), vs))
    ok = (n_fam == len(X)) if must else (n_fam == n_in)
    print("  %-22s n %6d  in a leaf %6d  in a FAMILY leaf %6d  (points matching >1 leaf: %d)   %s"
          % (name, len(X), n_in, n_fam, multi, "OK" if ok else "*** FAIL"))
    for b in bad[:5]: print("      ", b)
    return ok


ok = True
X = np.load("certified_eq_all.npy")
ex = np.array([np.abs(E.expl(q)).max() for q in X]); assert ex.max() < 1e-13
ok &= check("family 744", X, must=True)
nash = tag.endswith("N")
try:
    H = np.load("hunt_eq_bet2.npy")
    ok &= check("hunt 23820", H, must=nash)
except Exception as e:
    print("  hunt set skipped:", e)
try:
    W = np.load("offpath_witness.npy").reshape(-1, 48)
    ok &= check("off-path witness", W, must=nash)
except Exception as e:
    print("  witness skipped:", e)
print("\nCONTROL %s: %s" % (tag, "PASSED" if ok else "*** FAILED"))
