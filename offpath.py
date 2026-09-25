"""The SGS family is NOT complete as a set of PROFILES -- exact witness.

`family_gap` compares LEAF DISTRIBUTIONS, so every audit that reported "0 outside
the family" was a statement about on-path play only.  Off path, Nash permits
anything that keeps every on-path deviation unprofitable, including actions the
paper's Table 2 rules out by dominance: dominance only bites at information sets
that are reached.

This script does three things, all in EXACT rational arithmetic where it matters:

  1. CENSUS of the project's own certified equilibria: how many violate Table 2
     (off path), how many violate Table 3's off-path values (b22 = 0, c23 = 0,
     the b32 / c33 windows), and -- the part that matters -- for how many the
     off-path action is ESSENTIAL: moving it to its Table-2/Table-3 value
     destroys the equilibrium.

  2. WITNESS: a Nash equilibrium q, all 48 coordinates rational, with
     b12 > 0 (P2 calls P1's bet holding the worst card), such that
        exploitability(q) = 0                 exactly, for all three players
        exploitability(q with b12 := 0) > 0   exactly, with P1 the gainer.
     Its leaf distribution is a family member's, so on path it is the family;
     as a profile it is outside Table 2, hence outside Table 3.

  3. The mechanism, read off the exact best response: which P1 bet becomes
     profitable once P2 stops calling with card 1.

usage:  python offpath.py
"""
import numpy as np, itertools
from fractions import Fraction as Fr
import kuhn3p as K, eqtools as E, classify, family as F, symbet

I = K.NAME_IDX; NAME = K.PARAM_NAME
T2 = {n: 0 for n in symbet.T2_ZERO}; T2.update({n: 1 for n in symbet.T2_ONE})


# ------------------------------------------------------------ exact tools --
def util_exact_by_card(p, player):
    """u_player split by the card `player` holds: dict card -> Fraction."""
    q = list(p) + [Fr(1)]
    out = {j: Fr(0) for j in K.CARDS}
    for r in range(K.NLEAF):
        w = Fr(1)
        for k in range(K.IDX.shape[1]):
            i = int(K.IDX[r, k])
            w *= q[i] if K.AGG[r, k] else (1 - q[i])
            if w == 0: break
        if w == 0: continue
        out[int(K.HOLDER[r, player])] += w * int(K.PAY[r, player])
    return {j: K.KAPPA_F * v for j, v in out.items()}


def br_exact(p, player):
    """exact best-response value and the pure best response (per card)."""
    total = Fr(0); arg = {}
    for j in K.CARDS:
        own = [K.pidx(player, j - 1 + 1, k) for k in K.SITUATIONS]
        best = None
        for bits in itertools.product((Fr(0), Fr(1)), repeat=4):
            qq = list(p)
            for i, v in zip(own, bits): qq[i] = v
            val = util_exact_by_card(qq, player)[j]
            if best is None or val > best: best, bb = val, bits
        total += best; arg[j] = tuple(int(b) for b in bb)
    return total, arg


def expl_exact(p):
    u = K.utilities_exact(p)
    return [br_exact(p, i)[0] - u[i] for i in range(3)]


def rat(x, den=1000):
    return Fr(x).limit_denominator(den)


def table3_exact(b11, b21, b23, b32, c11, c33, c34):
    """Table 2 + Table 3 in exact arithmetic (mirrors family.make_profile)."""
    p = [None] * 48
    for n, v in T2.items(): p[I[n]] = Fr(v)
    for n in ("a11", "a21", "a22", "a23", "a31", "a32", "a34", "a41"): p[I[n]] = Fr(0)
    p[I["a33"]] = Fr(1, 2)
    beta = max(b11, b21)
    p[I["b11"]] = b11; p[I["b21"]] = b21; p[I["b22"]] = Fr(0); p[I["b23"]] = b23
    p[I["b31"]] = Fr(0); p[I["b32"]] = b32
    p[I["b33"]] = Fr(1, 2) + (b11 + b21) / 2 + beta / 2 - b23 * (1 - b21)
    p[I["b34"]] = Fr(0); p[I["b41"]] = 2 * b11 + 2 * b21
    p[I["c11"]] = c11; p[I["c21"]] = Fr(1, 2) - c11
    for n in ("c22", "c23", "c31", "c32"): p[I[n]] = Fr(0)
    p[I["c33"]] = c33; p[I["c34"]] = c34; p[I["c41"]] = Fr(1)
    assert all(v is not None for v in p)
    return p


def fmt(p):
    return ", ".join("%s=%s" % (NAME[i], p[i]) for i in range(48) if p[i] != T2.get(NAME[i], None) and not (NAME[i] in T2))


if __name__ == "__main__":
    # ---------------------------------------------------------- 1. census --
    print("=== 1. CENSUS: off-path content of the certified equilibria ===")
    for fn in ("certified_eq_all.npy", "lmdeep_x_und.npy", "hunt_eq_bet2.npy"):
        EQ = np.load(fn)
        Z = [I[n] for n in symbet.T2_ZERO]; O = [I[n] for n in symbet.T2_ONE]
        t2 = np.maximum(np.abs(EQ[:, Z]).max(1), np.abs(1 - EQ[:, O]).max(1))
        off2 = t2 > 1e-9
        b22 = np.abs(EQ[:, I["b22"]]) > 1e-9; c23 = np.abs(EQ[:, I["c23"]]) > 1e-9
        # essential?  project Table 2, then also Table 3's off-path pins, re-certify
        P2 = EQ.copy()
        for n, v in T2.items(): P2[:, I[n]] = v
        P3 = P2.copy(); P3[:, I["b22"]] = 0.0; P3[:, I["c23"]] = 0.0
        ex2 = np.array([np.abs(E.expl(q)).max() for q in P2])
        ex3 = np.array([np.abs(E.expl(q)).max() for q in P3])
        print("%-22s n=%6d  off Table 2: %6d (%5.1f%%)  ESSENTIAL (T2 projection not Nash): %5d"
              % (fn, len(EQ), off2.sum(), 100 * off2.mean(), (ex2 > 1e-12).sum()))
        print("%-22s          b22>0: %6d  c23>0: %6d   ESSENTIAL (T2+T3 projection not Nash): %5d"
              % ("", b22.sum(), c23.sum(), (ex3 > 1e-12).sum()))
        gap = np.array([classify.family_gap(q) for q in EQ[:2000]])
        print("%-22s          leaf-distribution gap to family, first %d: max %.1e" % ("", len(gap), gap.max()))

    # --------------------------------------------------------- 2. witness --
    # Constructed, not fitted: on path the family's sub-family-C corner
    # (b11 = 1/4, b21 = b23 = 0, c11 = 1/2); off path -- the 12 coordinates
    # behind P1's bet -- a configuration found by a random search of the cube
    # for maximal slack, then rationalised.  The point is that b32 + c33 < 1/2
    # (OUTSIDE Table 3's c33 window, so with Table 3's pins P1 would bluff), and
    # P1 is deterred instead by b12 > 0 (P2 calls with card 1), b22 > 0 and
    # c23 > 0 -- all three pinned to 0 by Table 2 / Table 3.
    print("\n=== 2. EXACT WITNESS ===")
    p = table3_exact(Fr(1, 4), Fr(0), Fr(0), Fr(23, 100), Fr(1, 2), Fr(1, 4), Fr(9, 10))
    p[I["b12"]] = Fr(9, 100); p[I["b22"]] = Fr(1, 40); p[I["c23"]] = Fr(1, 25)
    e = expl_exact(p)
    p0 = list(p); p0[I["b12"]] = Fr(0)
    e0 = expl_exact(p0)
    k = "constructed"
    print("on path: sub-family C corner b11 = 1/4, b21 = b23 = 0, c11 = 1/2 ; off path: b32 = 23/100, c33 = 1/4, c34 = 9/10")
    print("off-path coordinates outside Table 2 / Table 3:")
    for n in ("b12", "b22", "c23"):
        print("   %s = %s   (Table %s: 0)   reach %.1e" % (n, p[I[n]], "2" if n == "b12" else "3", K.reach(np.array([float(v) for v in p]))[I[n]]))
    print("   and b32 + c33 = %s < 1/2, i.e. c33 is BELOW Table 3's window [1/2 - b32, 3/4 - b32]" % (p[I["b32"]] + p[I["c33"]]))
    u = K.utilities_exact(p)
    print("utilities        u = (%s, %s, %s)   = the family's (-k(1/2+beta), -k/2, k(1+beta)) at beta = 1/4" % u)
    print("exploitability   at q            : (%s, %s, %s)   <- exactly zero: q IS a Nash equilibrium" % tuple(e))
    print("exploitability   at q, b12 := 0  : (%s, %s, %s)   <- P1 gains %s = %.5f" % (tuple(e0) + (e0[0], float(e0[0]))))
    pT = list(p)
    for n in ("b12", "b22", "c23"): pT[I[n]] = Fr(0)
    eT = expl_exact(pT)
    print("exploitability   at Table-3 pins : (%s, %s, %s)   <- P1 gains %.5f" % (tuple(eT) + (float(eT[0]),)))
    assert all(x == 0 for x in e) and e0[0] > 0 and eT[0] > 0
    gap = classify.family_gap(np.array([float(v) for v in p]))
    print("leaf-distribution gap of q to the family: %.1e   (on path, q IS the family)" % gap)
    # ------------------------------------------------------- 3. mechanism --
    print("\n=== 3. MECHANISM ===")
    v1, arg1 = br_exact(p0, 0)
    print("P1's exact best response once b12 = 0 (per card: bet-at-root, then situations 2,3,4):")
    for j in K.CARDS: print("   card %d: %s" % (j, arg1[j]))
    bets = [j for j in K.CARDS if arg1[j][0] == 1]
    print("=> P1 wants to BET card(s) %s.  With b12 > 0, P2 calls that bet holding card 1, which puts P3 in"
          " situation 4 (facing bet + call); the bet then loses enough to P3's calls to be unprofitable." % bets)
    np.save("offpath_witness.npy", np.array([float(v) for v in p]))
    with open("offpath_witness.txt", "w") as f:
        f.write("exact Nash equilibrium with b12 > 0 (P2 calls P1's bet with card 1), outside Table 2/3 as a profile\n")
        for i in range(48): f.write("%s = %s\n" % (NAME[i], p[i]))
    print("\nwritten offpath_witness.npy / offpath_witness.txt")
