"""Plots of rho = -(du_C/d eps)/(du_A/d eps) over the family's free parameters."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import kuhn3p as K
import family as F
import grids as G

CYC = {0: (1, 2), 1: (2, 0), 2: (0, 1)}          # A -> (B, C)
PN = ("P1", "P2", "P3")
TOL = 1e-12
H = 1e-5
plt.rcParams.update({"figure.dpi": 130, "font.size": 8.5,
                     "axes.grid": True, "grid.alpha": .3,
                     "axes.titlesize": 9, "legend.fontsize": 7.2})


def rho_along(P, param, A, C, h=H):
    """rho and the three derivatives along +e_param, for a stack of profiles."""
    i = K.NAME_IDX[param]
    d = np.zeros(K.NPARAM)
    d[i] = 1.0
    du = (K.utilities_batch(P + h * d) - K.utilities_batch(P - h * d)) / (2 * h)
    dA = du[:, A]
    r = np.where(np.abs(dA) > 1e-10, -du[:, C] / np.where(dA == 0, 1, dA),
                 np.nan)
    return r, du


# ===========================================================================
# FIGURE 1 -- the same deviation for all three players:
#             "bet the 3 in the opening round when the family says check"
# ===========================================================================
fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.5), constrained_layout=True)
LINES = [("A: c11=0, b11=b21=beta", lambda n: G.line_A_beta(n, .5, .5, 0., 1.),
          "-", 3.4, "tab:blue"),
         ("A: c11=0, b11=0", lambda n: G.line_A_beta(n, .5, .5, 0., 0.),
          "--", 2.4, "tab:cyan"),
         ("B: 0<c11<1/2 (c11 = 0.6 c11max)",
          lambda n: (np.linspace(0, .25, n),
                     np.array([F.profile_B(
                         b, .6 * F.c11_max(b, b), .5, .5, 0.)[0]
                         for b in np.linspace(0, .25, n)])),
          "-.", 1.8, "tab:orange"),
         ("C: c11=1/2, b21=0", lambda n: (np.linspace(0, .25, n),
                                          np.array([F.profile_C(
                                              b, 0., 0., .5, .5, 0.)[0]
                                              for b in np.linspace(0, .25, n)])),
          ":", 2.2, "tab:green")]

for A, param in enumerate(("a31", "b31", "c31")):
    ax = axes[A]
    B, C = CYC[A]
    for lbl, mk, ls, lw, col in LINES:
        x, P = mk(201)
        r, du = rho_along(P, param, A, C)
        ax.plot(x, r, ls, color=col, lw=lw, label=lbl)
    ax.axhline(0, color="k", lw=.8)
    ax.axhline(1, color="k", lw=.5, ls=":")
    ax.set_title("A = %s, d = +e_{%s}   (C = %s)\n%s bluff-bets the 3 in round 1"
                 % (PN[A], param, PN[C], PN[A]))
    ax.set_xlabel(r"$\beta$   (201 points, full valid range)")
    ax.set_ylabel(r"$\rho = -\,(du_%s/d\epsilon)\,/\,(du_%s/d\epsilon)$"
                  % (C + 1, A + 1))
    ax.set_ylim(-.2, 1.2)
    ax.legend(loc="best")
fig.suptitle(r"$\rho$ for the one directly comparable deviation across all "
             r"three players  (each panel: 201 grid points x 4 slices)",
             fontsize=10)
fig.savefig("fig1_rho_parallel_direction.png", bbox_inches="tight")
print("wrote fig1_rho_parallel_direction.png")

# ===========================================================================
# FIGURE 2 -- where rho is ill-defined / where its sign flips  (A = P1)
# ===========================================================================
fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.5), constrained_layout=True)
b11, b21 = .10, .20

ts, P = G.line_A_tc33(401, b11, b21, t_b32=.5)
r, du = rho_along(P, "a11", 0, 2)
ax = axes[0]
for k, (lbl, col) in enumerate((("$du_1/d\\epsilon$  (A)", "tab:red"),
                                ("$du_2/d\\epsilon$  (B)", "tab:blue"),
                                ("$du_3/d\\epsilon$  (C)", "tab:green"))):
    ax.plot(ts, du[:, k], color=col, lw=1.6, label=lbl)
ax.axhline(0, color="k", lw=.8)
ax.set_title("A = P1, d = +e_{a11}  (P1 bluff-bets the 1)\n"
             r"$b_{11}=0.1,\ b_{21}=0.2,\ b_{32}=$ mid")
ax.set_xlabel(r"$t$:  $c_{33}$ swept across its valid interval")
ax.set_ylabel("directional derivative")
ax.legend(loc="best")

ax = axes[1]
ax.plot(ts, r, color="tab:purple", lw=1.8)
ax.axhline(0, color="k", lw=.8)
ax.axvline(0, color="tab:red", lw=1.0, ls="--")
ax.text(.02, .93, r"pole: $du_1/d\epsilon = 0$ at $c_{33}=\frac{1}{2}-b_{32}$",
        transform=ax.transAxes, color="tab:red", fontsize=7.5)
ax.set_ylim(-25, 25)
ax.set_title(r"$\rho$ diverges and changes sign along the SAME direction")
ax.set_xlabel(r"$t$:  $c_{33}$ swept across its valid interval")
ax.set_ylabel(r"$\rho=-(du_3/d\epsilon)/(du_1/d\epsilon)$")

# 2-D sign map over (beta, t_c33)
ax = axes[2]
nb, nt = 121, 121
bs, tsg = np.linspace(1e-3, .25, nb), np.linspace(0, 1, nt)
Z = np.empty((nt, nb))
for a, t in enumerate(tsg):
    P = np.array([F.profile_A(.5 * b, b, .5, t, 0.)[0] for b in bs])
    rr, _ = rho_along(P, "a11", 0, 2)
    Z[a] = rr
im = ax.pcolormesh(bs, tsg, np.clip(Z, -3, 3), cmap="coolwarm",
                   vmin=-3, vmax=3, shading="auto")
ax.contour(bs, tsg, Z, levels=[0.0], colors="k", linewidths=1.4)
fig.colorbar(im, ax=ax, label=r"$\rho$ (clipped to $\pm3$)")
ax.set_title(r"sign map of $\rho$ over the free parameters"
             "\n(black = sign flip, bottom edge = undefined)")
ax.set_xlabel(r"$\beta=b_{21}$   ($b_{11}=\beta/2$)")
ax.set_ylabel(r"$t$:  position of $c_{33}$ in its interval")
ax.grid(False)
fig.suptitle(r"$\rho$ is neither well-defined everywhere nor constant in sign "
             r"— A = P1, direction $+e_{a_{11}}$", fontsize=10)
fig.savefig("fig2_rho_illdefined_and_signflip.png", bbox_inches="tight")
print("wrote fig2_rho_illdefined_and_signflip.png")

# ===========================================================================
# FIGURE 3 -- the costless transfer directions: du_A == 0, denominator == 0
# ===========================================================================
fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.3), constrained_layout=True)
COLS = ("tab:red", "tab:blue", "tab:green")

# (a) the paper's along-family transfer d/d beta  (multi-coordinate)
bs = np.linspace(1e-3, .25 - 1e-3, 201)
DU = np.array([(K.utilities(F.profile_A(b + H, b + H, .5, .5, 0.)[0])
                - K.utilities(F.profile_A(b - H, b - H, .5, .5, 0.)[0]))
               / (2 * H) for b in bs])
ax = axes[0]
for k in range(3):
    ax.plot(bs, DU[:, k], color=COLS[k], lw=1.7, label="$du_%d/d\\beta$" % (k + 1))
ax.axhline(0, color="k", lw=.8)
ax.axhline(K.KAPPA, color="grey", lw=.6, ls=":")
ax.axhline(-K.KAPPA, color="grey", lw=.6, ls=":")
ax.set_title("P2 moves ALONG the family\n"
             r"(paper's transfer: $b_{11},b_{21},b_{33},b_{41}$ move together)")
ax.set_xlabel(r"$\beta$")
ax.set_ylabel(r"$du_i/d\beta$")
ax.legend(loc="center right")
ax.text(.03, .1, r"$du_2/d\beta\equiv 0\ \Rightarrow\ \rho$ undefined",
        transform=ax.transAxes, fontsize=8)

# (b,c,d) single-coordinate costless transfers, one per player
CASES = [(0, "a11", lambda n: G.line_A_beta(n, .5, 0.0, 0., .5),
          r"$\beta$", "A = P1, $d=+e_{a_{11}}$ at $c_{33}=\\frac{1}{2}-b_{32}$"),
         (1, "b11", lambda n: G.line_A_beta(n, .5, .5, 0., .5),
          r"$\beta$", "A = P2, $d=+e_{b_{11}}$ (everywhere)"),
         (2, "c21", lambda n: G.line_A_beta(n, .5, .5, 0., .5),
          r"$\beta$", "A = P3, $d=+e_{c_{21}}$ (everywhere)")]
for ax, (A, param, mk, xlab, ttl) in zip(axes[1:], CASES):
    x, P = mk(201)
    _, du = rho_along(P, param, A, CYC[A][1])
    for k in range(3):
        ax.plot(x, du[:, k], color=COLS[k], lw=1.7,
                label="$du_%d/d\\epsilon$" % (k + 1))
    ax.axhline(0, color="k", lw=.8)
    ax.set_title(ttl + "\n" + r"$du_A/d\epsilon \equiv 0$: costless transfer")
    ax.set_xlabel(xlab)
    ax.set_ylabel(r"$du_i/d\epsilon$")
    ax.legend(loc="best")
fig.suptitle("Every player has a direction that costs them nothing and moves "
             "utility between the other two — there the denominator of "
             r"$\rho$ is exactly 0", fontsize=10)
fig.savefig("fig3_costless_transfers.png", bbox_inches="tight")
print("wrote fig3_costless_transfers.png")
