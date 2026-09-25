"""Controls for the bnb5 PARTITION pruning rules, as used by allbranch5.py.

control3.py validates `bnb`'s label propagation.  bnb5 is a different code
path -- its own f1/f0 rules over ivl.bounds, applied to arbitrary boxes rather
than label-induced ones -- so it needs its own control, and allbranch5 leans on
it in a configuration nothing has exercised before: *slab* boxes on the four
opening coordinates.

The invariant: a box containing a real equilibrium must never be killed, and
must never be narrowed so far that it stops containing it.  If a partition cell
holding a known family point ever comes back "EMPTY (proven)", every emptiness
verdict from the driver is worthless.

usage:  python control5.py [locut] [hicut] [maxnodes]
"""
import sys, numpy as np, bnb5, allbranch5 as AB, family as F, eqtools as E, kuhn3p as K

locut = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02
hicut = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
maxnodes = int(sys.argv[3]) if len(sys.argv) > 3 else 300000
edges = [0.0, locut, hicut, 1.0]

# Known family equilibria, including off-path free parameters set away from 0.5
# (freezing off-path coordinates was the bug that made every family control
# fail -- they are variables, and they still shape other players' incentives).
tests = [
    ("A(1/8,1/4)",        F.profile_A(0.125, 0.25)[0]),
    ("A(0,0)",            F.profile_A(0.0, 0.0)[0]),
    ("A(1/4,1/4)",        F.profile_A(0.25, 0.25)[0]),
    ("A(1/8,1/4)+off",    F.profile_A(0.125, 0.25, t_b32=0.3, t_c33=0.7, c34=0.2)[0]),
    ("B(1/8,0.2)",        F.profile_B(0.125, 0.2)[0]),
    # NB: profile_B(b11, c11) sets b21 = b11, so at c11 = 1/2 the point lands in
    # sub-family C, whose constraint b21 <= min{b11, 1/2 - 2 b11} then reduces to
    # b11 <= 1/6.  profile_B(0.2, 1/2) is therefore NOT an equilibrium (expl
    # 4.2e-03), and using it as a control makes bnb5 look unsound when it is
    # behaving correctly -- but profile_B(b11, 1/2) for b11 <= 1/6 IS one
    # (measured ~1e-16 at b11 = 0, 0.05, 0.125, 1/6; 1.25e-05 just past it).
    # Membership is decided by family.violations, not by the constructor used.
    ("B(1/8,0.3)+off",    F.profile_B(0.125, 0.3, t_b32=0.9, t_c33=0.1, c34=0.8)[0]),
    ("B(0.2,0.3)",        F.profile_B(0.2, 0.3)[0]),
    ("C(0.2,0.05)",       F.profile_C(0.2, 0.05)[0]),
    ("C(1/4,0)",          F.profile_C(0.25, 0.0)[0]),
    ("C(0.2,0.05)+off",   F.profile_C(0.2, 0.05, t_b23=0.4, t_b32=0.6, t_c33=0.3, c34=0.7)[0]),
]


def cell_of(p):
    """The partition cell code whose slab contains p on each opener."""
    code = []
    for v in AB.OPEN:
        j = int(np.searchsorted(edges, p[v], side='right')) - 1
        code.append(min(max(j, 0), len(edges) - 2))
    return tuple(code)


def contains(LO, HI, p, tol=1e-9):
    return bool((LO <= p + tol).all() and (HI >= p - tol).all())


print("edges %s   maxnodes %d\n" % (edges, maxnodes))

# ---- 0. every control point must actually BE an equilibrium ---------------
# A control that is not an equilibrium proves nothing when it dies, and makes a
# correct prune look unsound.  Refuse to run on a bad control set.
bad = [(nm, float(np.abs(E.expl(p)).max())) for nm, p in tests
       if np.abs(E.expl(p)).max() >= 1e-12]
if bad:
    for nm, e in bad:
        print("  *** control point %s is NOT an equilibrium (expl %.2e)" % (nm, e))
    sys.exit("control set invalid -- fix the profiles before trusting any verdict")
print("--- 0. all %d control points verified Nash (max expl %.1e)"
      % (len(tests), max(float(np.abs(E.expl(p)).max()) for _, p in tests)))

fail = 0

# ---- 1. tight box around each equilibrium survives propagation -------------
print("--- 1. tight box (p +/- 1e-6) survives bnb5.propagate")
for nm, p in tests:
    e = np.abs(E.expl(p)).max()
    LO = np.clip(p - 1e-6, 0.0, 1.0)[None, :]
    HI = np.clip(p + 1e-6, 0.0, 1.0)[None, :]
    nLO, nHI, al = bnb5.propagate(LO.copy(), HI.copy())
    ok = bool(al[0]) and contains(nLO[0], nHI[0], p)
    fail += not ok
    print("  %-18s expl %.1e  alive %-5s contains %-5s  %s"
          % (nm, e, bool(al[0]), contains(nLO[0], nHI[0], p), "ok" if ok else "*** FAIL"))

# ---- 2. the containing partition cell survives propagation ----------------
print("\n--- 2. containing partition cell survives bnb5.propagate")
for nm, p in tests:
    code = cell_of(p)
    LO, HI = AB.cell_box(code, edges)
    assert contains(LO, HI, p), "cell_of/cell_box disagree for %s" % nm
    nLO, nHI, al = bnb5.propagate(LO[None, :].copy(), HI[None, :].copy())
    ok = bool(al[0]) and contains(nLO[0], nHI[0], p)
    fail += not ok
    print("  %-18s cell %-12s alive %-5s contains %-5s  %s"
          % (nm, str(code), bool(al[0]), contains(nLO[0], nHI[0], p),
             "ok" if ok else "*** FAIL"))

# ---- 3. end to end: the cell must not be declared EMPTY --------------------
print("\n--- 3. end-to-end bnb5.search on a LOCAL box around each equilibrium")
print("       must terminate, return boxes, and still cover the equilibrium")
# Deliberately NOT the whole partition cell.  Every known equilibrium is
# P1-silent, so all of them sit in the all-low cell [0,locut]^4, which also
# contains every small-frequency profile and does not terminate at any sane
# node count (300k nodes -> 103,465 boxes, still ABORT).  A search that aborts
# proves nothing either way, so gating on it would be gating on noise.
# A local box exercises the identical propagate/split/emit path and actually
# reaches a verdict.
inconc = 0
for w in (0.05, 0.15):
    print("  half-width %.2f" % w)
    for nm, p in tests:
        LO = np.clip(p - w, 0.0, 1.0)
        HI = np.clip(p + w, 0.0, 1.0)
        st, boxes = bnb5.search(LO0=LO, HI0=HI, wtol=AB.WTOL, maxdepth=AB.MAXDEPTH,
                                cap=4096, maxnodes=maxnodes)
        ab = st.get('ABORT', False)
        held = any(contains(b[0][i], b[1][i], p)
                   for b in boxes for i in range(b[0].shape[0]))
        if st['boxes'] == 0 and not ab:
            verdict = "*** FAIL: declared EMPTY around a known equilibrium"; fail += 1
        elif ab:
            verdict = "INCONCLUSIVE (node cap)"; inconc += 1
        elif not held:
            verdict = "*** FAIL: %d boxes but none contains the equilibrium" % st['boxes']
            fail += 1
        else:
            verdict = "PASS: %d boxes, equilibrium covered" % st['boxes']
        print("    %-18s nodes=%-8d boxes=%-7d %s" % (nm, st['nodes'], st['boxes'], verdict))

ok = (fail == 0 and inconc == 0)
print("\n%s  (%d failures, %d inconclusive)"
      % ("ALL CONTROLS PASSED" if ok else "*** CONTROLS NOT PASSED", fail, inconc))
sys.exit(0 if ok else 1)
