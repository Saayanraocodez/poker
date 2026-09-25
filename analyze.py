"""
Directional-derivative / utility-transfer analysis of the Szafron-Gibson-
Sturtevant equilibrium family for three-player Kuhn poker.

  * central finite differences of (u1,u2,u3) along every feasible unilateral
    perturbation direction of each player,
  * the zero-sum identity  du_A + du_B + du_C = 0,
  * rho = -(du_C/d eps) / (du_A/d eps)  over a fine grid of the free parameters.
"""
import json
import sys

import numpy as np

import kuhn3p as K
import family as F
import grids as G

TOL = 1e-12                      # exact-gradient zero threshold
H = 1e-5                         # central-difference step
CYC = {0: (1, 2), 1: (2, 0), 2: (0, 1)}          # A -> (B, C)
PN = ("P1", "P2", "P3")
OUT = {}


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


# ===========================================================================
hdr("0.  Grid over the family's free parameters")
P, M = G.full_grid()
N = P.shape[0]
for code, nm in ((0, "A  c11=0    "), (1, "B  0<c11<1/2"), (2, "C  c11=1/2  ")):
    k = int((M["sub"] == code).sum())
    print("   sub-family %s : %5d grid points" % (nm, k))
print("   TOTAL                : %5d grid points"
      "   (requirement was >= 100)" % N)
print("   beta range spanned   : [%.4f, %.4f]" % (M["beta"].min(),
                                                  M["beta"].max()))
print("   free params varied   : b11, b21, b23, b32, c11, c33, c34")

U = K.utilities_batch(P)
pred = np.stack([-K.KAPPA * (0.5 + M["beta"]),
                 -K.KAPPA * 0.5 * np.ones(N),
                 K.KAPPA * (1.0 + M["beta"])], axis=1)
print("   max |u_grid - Table 3 closed form| = %.3e"
      % np.abs(U - pred).max())

# ===========================================================================
hdr("1.  Is there ANY strictly improving direction?  (exact best responses)")
sub = np.linspace(0, N - 1, 400).astype(int)
expl = np.array([K.exploitability(P[i]) for i in sub])
print("   exact best-response gap  max_i (BR_i - u_i) over %d sampled points:"
      % len(sub))
print("      P1 %.3e   P2 %.3e   P3 %.3e" % tuple(expl.max(axis=0)))
print("   Every profile is an exact Nash equilibrium, so by definition NO")
print("   perturbation of any single player can strictly increase that")
print("   player's utility:  du_A/d eps <= 0 for every feasible direction.")
OUT["max_exploitability"] = expl.max(axis=0).tolist()

# ===========================================================================
hdr("2.  Central finite differences vs exact multilinear derivatives")
GE = K.gradients_batch(P, h=None)          # exact  (N,48,3)
GF = K.gradients_batch(P, h=H)             # central difference
err = np.abs(GE - GF)
print("   central difference step h = %g" % H)
print("   max |central_diff - exact| over %d points x 48 coords x 3 players"
      " = %.3e" % (N, err.max()))
print("   (u_i is multilinear, hence AFFINE along a single coordinate, so the")
print("    central difference is exact up to floating-point round-off.)")
OUT["max_fd_error"] = float(err.max())

# ===========================================================================
hdr("3.  Zero-sum identity   du_A/d eps + du_B/d eps + du_C/d eps = 0")
zs_fd = np.abs(GF.sum(axis=2))
zs_ex = np.abs(GE.sum(axis=2))
print("   max |sum_i du_i| (central difference) = %.3e" % zs_fd.max())
print("   max |sum_i du_i| (exact)              = %.3e" % zs_ex.max())
bad = int((zs_fd > 1e-9).sum())
print("   points/directions flagged as violating zero-sum (> 1e-9): %d" % bad)
print("   This can never fail: every leaf of the tree pays out exactly the")
print("   chips put in, so sum_i u_i(p) = 0 identically on ALL of [0,1]^48,")
print("   not just on the equilibrium family.  It is a property of the game,")
print("   not a property of the equilibrium.")
OUT["max_zero_sum_violation"] = float(zs_fd.max())

# ===========================================================================
hdr("4.  Sign of du_A along every FEASIBLE direction  (equilibrium check)")
own = np.zeros((3, K.NPARAM), dtype=bool)
for A in range(3):
    own[A, A * 16:(A + 1) * 16] = True

rows = []
for A in range(3):
    dA = GE[:, :, A]                                  # (N,48)
    mine = own[A][None, :]
    can_up = (P < 1.0 - 1e-12) & mine                 # +e_i feasible
    can_dn = (P > 1.0e-12) & mine                     # -e_i feasible
    # feasible directional derivative of u_A
    up_improves = can_up & (dA > TOL)
    dn_improves = can_dn & (-dA > TOL)
    n_improve = int(up_improves.sum() + dn_improves.sum())
    n_feas = int(can_up.sum() + can_dn.sum())
    n_zero = int((can_up & (np.abs(dA) <= TOL)).sum()
                 + (can_dn & (np.abs(dA) <= TOL)).sum())
    rows.append((PN[A], n_feas, n_improve, n_feas - n_improve - n_zero, n_zero))
    print("   A = %s : %7d feasible (point,direction) pairs | strictly"
          " IMPROVING %d | strictly COSTLY %7d | NEUTRAL (du_A = 0) %7d"
          % (PN[A], n_feas, n_improve, n_feas - n_improve - n_zero, n_zero))
OUT["improving_directions"] = sum(r[2] for r in rows)
print("\n   => the requested d_A ('a perturbation that strictly increases u_A')")
print("      DOES NOT EXIST at any point of this family, for any player.")

# ===========================================================================
hdr("5.  Costless transfer directions:  du_A = 0 but du_B = -du_C != 0")
for A in range(3):
    B, C = CYC[A]
    dA, dB, dC = GE[:, :, A], GE[:, :, B], GE[:, :, C]
    mine = own[A][None, :]
    neutral = mine & (np.abs(dA) <= TOL) & (np.abs(dB) > TOL)
    cols = np.where(neutral.any(axis=0))[0]
    per_pt = neutral.sum(axis=1)
    print("   A = %s : %d of %d grid points have >=1 costless transfer"
          " direction   (params: %s)"
          % (PN[A], int((per_pt > 0).sum()), N,
             ", ".join(K.PARAM_NAME[i] for i in cols)))
OUT["transfer_dirs"] = True

# ===========================================================================
hdr("6.  rho = -(du_C/d eps) / (du_A/d eps)  over the grid")
print("   Convention (cyclic):  A=P1 -> B=P2, C=P3 ;  A=P2 -> B=P3, C=P1 ;")
print("                         A=P3 -> B=P1, C=P2.")
print("   rho is invariant under d -> -d (both numerator and denominator")
print("   flip sign), so rho depends only on WHICH parameter is perturbed.")
print("   Identity: rho_{A->B} + rho_{A->C} = 1, since du_B + du_C = -du_A.\n")

rho_tab = {}
for A in range(3):
    B, C = CYC[A]
    print("   ---- A = %s  (B = %s, C = %s) "
          "------------------------------------------------" % (PN[A], PN[B],
                                                                 PN[C]))
    print("     param  kind        undef/9072   min|du_A|      rho range"
          "               sign of rho")
    for i in range(A * 16, (A + 1) * 16):
        dA, dB, dC = GE[:, i, A], GE[:, i, B], GE[:, i, C]
        nz = np.abs(dA) > TOL
        ndeg = int((~nz).sum())
        # a costless TRANSFER needs du_A = 0 AND the others moving *there*
        moves = (~nz) & (np.abs(dB) > TOL)
        if nz.sum() == 0:
            kind = "TRANSFER" if moves.any() else "null"
            note = ("costless transfer" if moves.any()
                    else "no effect on anyone")
            print("     %-6s %-11s %6d/9072   ---           UNDEFINED"
                  " everywhere   (%s)" % (K.PARAM_NAME[i], kind, ndeg, note))
            rho_tab[K.PARAM_NAME[i]] = dict(kind=kind, undefined=ndeg,
                                            sign="undefined")
            continue
        r = -dC[nz] / dA[nz]
        pos = int((r > 1e-9).sum())
        neg = int((r < -1e-9).sum())
        zer = int((np.abs(r) <= 1e-9).sum())
        if pos and neg:
            sign = "*** FLIPS + <-> - ***"
        elif pos and zer:
            sign = "+ , touches 0"
        elif neg and zer:
            sign = "- , touches 0"
        elif pos:
            sign = "+ everywhere"
        elif neg:
            sign = "- everywhere"
        else:
            sign = "identically 0"
        kind = ("TRANSFER" if moves.any()
                else ("unreached" if ndeg else "costly"))
        print("     %-6s %-11s %6d/9072   %.3e   [%+9.4f, %+9.4f]   %s"
              % (K.PARAM_NAME[i], kind, ndeg, np.abs(dA[nz]).min(),
                 r.min(), r.max(), sign))
        rho_tab[K.PARAM_NAME[i]] = dict(
            kind=kind, lo=float(r.min()), hi=float(r.max()), pos=pos, neg=neg,
            zero=zer, undefined=ndeg, sign=sign,
            min_abs_dA=float(np.abs(dA[nz]).min()))
    print()
OUT["rho_table"] = rho_tab

hdr("6b. Summary answers")
und = [n for n, v in rho_tab.items() if v["sign"] == "undefined"]
flip = [n for n, v in rho_tab.items() if "FLIPS" in v["sign"]]
touch = [n for n, v in rho_tab.items() if "touches" in v["sign"]]
pure = [n for n, v in rho_tab.items() if v["sign"] == "+ everywhere"]
partial = [n for n, v in rho_tab.items()
           if v["sign"] != "undefined" and v["undefined"] > 0]
print("   (1) WELL-DEFINED?  No.")
print("       %d of 48 parameters have du_A == 0 at EVERY grid point:" % len(und))
print("           %s" % ", ".join(und))
print("       a further %d have du_A == 0 on part of the grid:" % len(partial))
print("           %s" % ", ".join(partial))
print("       and where it is nonzero the denominator gets as small as")
print("       %.1e vs kappa = %.4f, so rho is unbounded, not merely undefined"
      % (min(v["min_abs_dA"] for v in rho_tab.values()
             if "min_abs_dA" in v), K.KAPPA))
print()
print("   (2) SIGN?  Not constant.")
print("       sign flips (+ and - both occur): %s"
      % (", ".join(flip) if flip else "none"))
print("       reaches 0 but does not flip     : %s" % ", ".join(touch))
print("       strictly positive everywhere    : %s" % ", ".join(pure))

# ===========================================================================
hdr("7.  The paper's utility transfer:  moving ALONG the family (d/d beta)")
print("   This is a MULTI-coordinate direction: b11, b21, b33 and b41 all move")
print("   together so the profile stays inside the family.  Central difference")
print("   in beta with step %g:\n" % H)
for lbl, mk in (("A  c11=0   (beta = b21, b11 = b21)",
                 lambda b: F.profile_A(b, b, 0.5, 0.5, 0.0)[0]),
                ("B  0<c11<1/2 (beta = b11 = b21, c11 = 0.3)",
                 lambda b: F.profile_B(b, 0.3 * F.c11_max(b, b), .5, .5, 0.)[0]),
                ("C  c11=1/2 (beta = b11, b21 = 0)",
                 lambda b: F.profile_C(b, 0.0, 0.0, 0.5, 0.5, 0.0)[0])):
    b0 = 0.12
    d = (K.utilities(mk(b0 + H)) - K.utilities(mk(b0 - H))) / (2 * H)
    print("     %-42s  du/dbeta = [%+.6f %+.6f %+.6f]   (kappa = %+.6f)"
          % (lbl, d[0], d[1], d[2], K.KAPPA))
print("\n   du_2/d beta == 0 exactly:  P2 moves kappa*d(beta) of utility from")
print("   P1 to P3 at zero cost to itself.  With A = P2 the denominator of rho")
print("   is exactly zero along this direction -> rho = -kappa/0 is UNDEFINED.")

# ===========================================================================
hdr("8.  A genuinely IMPROVING direction: the paper's Table 4 profile")
p4 = F.make_profile(b11=.25, b21=0., b23=.125, b32=0., c11=0., c33=.25, c34=0.)
p4[K.NAME_IDX["b33"]] = 5. / 8.
p4[K.NAME_IDX["b41"]] = .5
g4 = K.gradients_batch(p4[None, :], h=H)[0]
i23 = K.NAME_IDX["b23"]
d = -g4[i23]                                     # direction: decrease b23
print("   Table 4 mixes sub-families (P2 from c11=1/2, P3 from c11=0) and is")
print("   NOT an equilibrium.  P2's exploitability there = %.6f = kappa*beta."
      % K.exploitability(p4)[1])
print("   Improving direction d_A = -e_{b23} (P2 stops calling P3's bet with")
print("   the 2 after folding P1 out).  Central differences:")
print("      du_1/d eps = %+.6f    du_2/d eps = %+.6f    du_3/d eps = %+.6f"
      % tuple(d))
print("      sum = %+.3e" % d.sum())
print("      rho_{P2->P1} = %+.4f      rho_{P2->P3} = %+.4f   (sum = %.4f)"
      % (-d[0] / d[1], -d[2] / d[1], (-d[0] - d[2]) / d[1]))
print("   P2's whole gain comes out of P3; P1 is untouched.")
OUT["table4_rho_P2_to_P1"] = float(-d[0] / d[1])
OUT["table4_rho_P2_to_P3"] = float(-d[2] / d[1])

with open("results.json", "w") as f:
    json.dump(OUT, f, indent=1, default=str)
print("\n[results.json written]")
