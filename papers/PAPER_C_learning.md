# What CFR Computes in Three-Player Kuhn Poker: Certified Distances, Non-Convexity and Noise

**Saayan Rao** — split draft, built by `papers/build_split.py` from `PAPER_DRAFT.md` Part I.

> One of three papers cut from the single working draft. Theorem, lemma and table numbers are shared
> across the three. The research record (`MASTER_DATA.md`), the code map and the reproduction commands
> are in `PAPER_DRAFT.md` Parts II–III. Claim tags: **[P]** proved, **[E]** exact computation,
> **[G]** grid or sampling evidence, **[F]** float exploration, **[F\*]** float carried to machine
> precision, **[?]** not established. The five-card game and the Hold'em line are not in this paper.

## Abstract

Counterfactual regret minimisation has no convergence guarantee beyond two players, and three-player
Kuhn poker is the standard small test. Its complete Nash set is now known exactly (companion paper),
so "what does CFR compute here?" can be answered with certified distances instead of exploitability.

All 150 outputs of external-sampling MCCFR at 10⁶ iterations lie a certified distance of at least
0.0067 from the Nash set (median 0.044), and the bound is attained by an exact witness in every case;
the error is on the path of play. The reason is geometric: CFR averages in sequence form and the Nash
set is not convex — the midpoint of two exact equilibria with equal payoffs has exploitability exactly
1/320. At 10⁸ iterations MCCFR still wanders among sub-families. Full-width alternating variants (CFR+,
DCFR) do converge onto the Nash set, to certified distance about 5·10⁻⁶, yet select no refinement, and
every variant tested favours the third seat (`β ≈ 0.12–0.17`). Exploitability understates the distance
to equilibrium by a median factor of 29.

Adding noise does select, but the answer depends on the noise. On the game with a floor on every
action, CFR+ stops converging; solved exactly, that game has an isolated equilibrium which tends to the
family's corner `β = 1/4`. The logit quantal response equilibrium tends to `β* ≈ 0.1616`, the root of
an explicit equation, and to the off-path call frequency normal-form properness requires. On path the
equilibrium being played is identifiable from observed play; whether it is an equilibrium is not.

## Contributions

1. **Certified distances from CFR outputs to the complete Nash set**, with exact witnesses.
2. **Non-convexity as the mechanism**: an exact two-point demonstration (Proposition 8).
3. **Which variants converge**: alternating full-width CFR+ and DCFR do; MCCFR, CFR and Linear CFR do
   not within the budgets tried. None selects a refinement; all carry a seat bias.
4. **Noise selects, differently**: floors (trembles) against logit.
5. **Identifiability**: on-path parameters are locally identifiable; equilibrium-ness is not.

---

## 1. Related work

**Kuhn poker and small-game analysis.**
- Kuhn (1950) solved the two-player game and gave its one-parameter equilibrium family.
- Abou Risk & Szafron (2010) introduced the three-player variant used here; SGS (2013) found the
  family under study.
- Hoehn et al. (2005) built exploitive agents from the analytic two-player solutions.
- Billingham (arXiv:1802.04670) computes equilibria of three-player Kuhn poker with N > 3 cards
  numerically (regularised equations, Newton and arc-length continuation) as a function of the pot
  size. Its abstract reports that the standard N = 4 game is qualitatively different from N > 4, and
  a new kind of midrange bet for N > 5. This is the closest neighbour: it is numerical where the
  present results are exact, and §18.3 of the full draft uses its parameter (the pot) at N = 4. **[?] Only the abstract
  was read; read the paper before submission.** arXiv:1704.08124 and arXiv:1707.01392 (simplified
  three-player Kuhn variants) are still to be checked.

**Multiplayer equilibrium computation.**
- CFR (Zinkevich et al. 2008), MCCFR (Lanctot et al. 2009), CFR+ (Tammelin 2014), and Linear and
  Discounted CFR (Brown & Sandholm 2019).
- CFR carries no convergence guarantee to Nash beyond two players.
- Three-player equilibrium computation is PPAD-hard (Daskalakis & Papadimitriou 2005).
- Ganzfried & Sandholm (2010) incorporate qualitative models; Ganzfried (2018, Games 9(2):33) built
  a three-player Kuhn agent.

**Equilibrium selection and refinement.**
- Selten (1975) trembling-hand perfection; Kreps & Wilson (1982) sequential equilibrium; Myerson
  (1978) proper equilibrium; van Damme (1984) quasi-perfection; van Damme (1991), the monograph.
- Harsanyi & Selten (1988) on selection.
- In two-player zero-sum games equilibria are interchangeable with a unique value. With three
  players they are not, and the SGS family is an explicit witness.

**Three-player poker specifically.**
- Nash & Shapley (1950) solved a three-person poker game analytically (with replacement and returned
  antes).
- Chen & Ankenman (2006, Example 29.2) construct an endgame with a utility transfer between two other
  players.

**Exact certification in game theory.** **[?]** Interval-Newton (Krawczyk) existence proofs, LP-dual
certificates and Nullstellensatz certificates are standard in verified numerics and polynomial
optimisation. Their combination into a replayable proof of an equilibrium-set characterisation
appears to be new for poker. Survey before claiming.

The full bibliography with verification status is in Appendix H.



---

## 2. The game and notation

### 2.1 Rules

- **Deal.** Deck {1,2,3,4}; one card each to P1, P2, P3. That makes **24 deals, each of probability
  κ = 1/24**. Everyone antes 1.
- **Betting.** One betting round; a bet or call is exactly 1 chip; no raises. Acting order P1, P2,
  P3. With no bet outstanding the actor checks (K) or bets (B); facing a bet, the actor folds (F) or
  calls (C).
- **Sequences.**
  - P1 bets → P2 answers → P3 answers → end.
  - P1 checks, P2 bets → P3 answers → P1 answers → end.
  - P1 checks, P2 checks, P3 bets → P1 answers → P2 answers → end.
  - All check → three-way showdown.
- **Showdown.** The highest unfolded card takes the pot.

There are 13 terminal histories per deal, 312 leaves in all.

### 2.2 Parameterisation (SGS Table 1)

`a_jk`, `b_jk`, `c_jk` is the probability that P1 / P2 / P3 takes the **aggressive** action (B with
no bet out, C facing a bet) holding card *j* in situation *k*:

| k | P1 history | P2 history | P3 history |
|---|---|---|---|
| 1 | (root) | K | KK |
| 2 | KKB | B | KB |
| 3 | KBF | KKBF | BF |
| 4 | KBC | KKBC | BC |

A profile is the 48-vector `[a11..a44, b11..b44, c11..c44]`. Situation k = 1 is the opening decision
(round 1); k = 2, 3, 4 are call/fold decisions (round 2). Every information set is (own card, public
history), and **every information set has exactly two actions**.

### 2.3 The SGS family (Tables 2 and 3)

**Table 2** (21 values SGS call necessary): `x12 = x13 = x14 = x24 = 0` and `x42 = x43 = x44 = 1` for
each player `x ∈ {a, b, c}`.

**Table 3**, with `β = max{b11, b21}`:
- **P1 has no free parameters:** `a11 = a21 = a22 = a23 = a31 = a32 = a34 = a41 = 0`, `a33 = 1/2`.
- **P2:**
  - free: `b11, b21, b23, b32`;
  - fixed: `b22 = b31 = b34 = 0`;
  - identities: `b33 = 1/2 + (b11+b21)/2 + β/2 − b23(1−b21)` and `b41 = 2b11 + 2b21`.
- **P3:**
  - free: `c11, c33, c34`;
  - identity: `c21 = 1/2 − c11`;
  - fixed: `c22 = c23 = c31 = c32 = 0`, `c41 = 1`.
- **Constraints:**
  - `b23 ≤ max{0, (b11−b21)/(2(1−b21))}`;
  - `c11 ≤ min{1/2, (2−b11)/(3+2b11+2b21)}`;
  - `b32 ≤ 1/2 + (3/4)(b11+b21) + β/4`;
  - `1/2 − b32 ≤ c33 ≤ 1/2 − b32 + (3/4)(b11+b21) + β/4`;
  - `0 ≤ c34 ≤ 1`.

**Sub-families:**
- **A:** `c11 = 0`, `b11 ≤ b21 ≤ 1/4`, `b23 = 0`, β = b21.
- **B:** `0 < c11 < 1/2`, `b21 = b11 ≤ 1/4`, `b23 = 0`, β = b11.
- **C:** `c11 = 1/2`, `b11 ≤ 1/4`, `b21 ≤ min{b11, 1/2 − 2b11}`, β = b11.

**Utilities:** `u1 = −κ(1/2 + β)`, `u2 = −κ/2`, `u3 = κ(1 + β)`.

### 2.4 Reachability

Because `a_j1 = 0` for every j, **P1 never bets anywhere in the family**. So P2 never faces a bet, and
P3 never reaches BF or BC. The coordinates `b12, b22, b32, b42` and `c13, c23, c33, c43, c14, c24,
c34, c44` sit at information sets of reach probability zero. Two of the family's own free parameters,
`b32` and `c33`, are among them. The off-path region is family-wide, not an artifact of a corner.



---

## 3. The equilibrium set (from the companion papers)

The companion papers prove the following; they are used here as given.

- **Theorem 4.** Every Nash equilibrium is realisation-equivalent to a member of the SGS family: P1
  never bets, and Table 3 holds on every reached information set. P2's payoff is `−1/48` in every
  equilibrium; P1's and P3's vary with `β ∈ [0, 1/4]`.
- **Theorem 5.** The complete Nash set is the union of twelve explicit sets; Table 4 gives the certified
  range of every coordinate. This is what distances are measured to.
- **Theorem 6 and Theorem 3.** Every sequential equilibrium has `b32 = 0`; every normal-form proper
  equilibrium has `c33` at one third of its window.

---

## 4. Learning dynamics: what CFR actually computes

### 4.1 MCCFR does not select, and is biased (R14) **[E,G]**

150 seeds of external-sampling MCCFR, 10^6 iterations each, from an independent tree that agrees with
the engine to 1.1e-16. Median exploitability is 0.0015, which is 3.6 % of κ.
- **Family membership:** sub-family A 29, B 11, C 11, **none 99 of 150**. CFR sits between
  sub-families: 109 seeds have intermediate `c11` but `|b21 − b11|` has median 0.111.
- **β is biased:** mean 0.1687, never near 0. That hands P3 about 0.0070 chips per hand at P1's
  expense. This is a per-seat bias produced by the solver, not the game.
- **`c33` is not selected:** its position in the window has sd 0.27 and correlates with nothing.
  Off-path reach is about 1e-3, so CFR gets almost no training signal there.
- **Dominance predictions are reproduced** (`c34 < 0.02` in 139/150). Tremble-structure predictions
  are not (`b32 < 0.02` in only 41/150).

### 4.2 Re-read against Theorem 5: every MCCFR output is certified off the Nash set (new) **[E]**

`reread14.py` certifies, for each output p, an exact lower bound on its max-norm distance to the
complete Nash set of Theorem 5. It uses a superset per leaf (labels, linear identities, certified
ranges) and weak duality: `|x − p|_∞ ≥ N/|g|_1` with rational multipliers. `reread14b.py` then finds,
for every output, an exact Nash point at that distance (re-verified by exact best responses).

| statistic | value |
|---|---|
| certified distance, min / median / mean / max | 0.0067 / 0.0444 / 0.0519 / 0.2101 |
| outputs certified farther than 0.005 / 0.01 / 0.02 / 0.05 / 0.1 | 150 / 147 / 123 / 67 / 10 (of 150) |
| distance ÷ exploitability, median (min) | 28.7 (4.3) |
| exact witness found, upper bound = lower bound | 150 / 150 (max ub − lb = 1.65e-7; exactly equal in 106) |
| coordinates carrying the certificate | a32 78, b11 41, b21 41, c11 10, a41 7, c21 6, … |
| off-path coordinates outside Table 4's windows (by > 0.02) | 0 |

So R14's "99/150 outside the family" is **not** evidence of equilibria outside the family. All 150
outputs are off the complete Nash set. The error is **on path** (P1's call `a32`, P2's bluffs
`b11`/`b21`), while their off-path play sits inside the Nash windows. Exploitability badly
understates the distance to the Nash set: by a factor of 29 at the median.

### 4.3 Why: the Nash set is not convex, and CFR averages in sequence form **[E]**

`mixdemo.py` uses two exact equilibria:
- x_A (sub-family A): `b11 = 1/20, b21 = 1/5, c11 = 0, c21 = 1/2`;
- x_C (sub-family C): `b11 = 1/5, b21 = 1/20, c11 = 1/2, c21 = 0`;
- both have `b33 = 29/40`, `b41 = 1/2`, and **identical payoffs** u = (−7/240, −1/48, 1/20).

Their sequence-form mixture is what an average over iterations computes:

| λ | b11 | b21 | c11 | exact exploitability | certified distance to the Nash set |
|---|---|---|---|---|---|
| 0 | 0.0500 | 0.2000 | 0.0000 | 0 | 0 |
| 1/10 | 0.0650 | 0.1850 | 0.0500 | 9/8000 | 0.0500 |
| 1/4 | 0.0875 | 0.1625 | 0.1250 | 3/1280 | 0.0375 |
| 1/2 | 0.1250 | 0.1250 | 0.2500 | **1/320** | 0.0273 |
| 3/4 | 0.1625 | 0.0875 | 0.3750 | 3/1280 | 0.0375 |
| 9/10 | 0.1850 | 0.0650 | 0.4500 | 9/8000 | 0.0500 |
| 1 | 0.2000 | 0.0500 | 0.5000 | 0 | 0 |

**Proposition 8.** *The Nash set of three-player Kuhn poker is not convex in sequence form. The
average of two equilibria with identical payoffs from different sub-families has exploitability
1/320, a small exploitability, at a certified distance 0.0273 from every equilibrium.* That is
exactly the signature of the R14 outputs. **[E]**

### 4.4 MCCFR at 10^8 iterations does not converge onto the set (new) **[G]**

`cfrlong.py` + `cfrlong_an.py`: 24 seeds × 10^8 iterations of ES-MCCFR (about 5,958 s per seed),
checkpointed. At each checkpoint the analysis measures the running average and the play of each
window alone.

| t | exploitability (median) | certified distance (median) | distance (max) | sub-families A/B/C | β (mean) |
|---|---|---|---|---|---|
| 1e4 | 1.39e-2 | 0.3895 | 0.6705 | 20/2/2 | 0.2362 |
| 1e5 | 4.04e-3 | 0.1219 | 0.3080 | 10/9/5 | 0.1658 |
| 1e6 | 1.45e-3 | 0.0452 | 0.1268 | 11/11/2 | 0.1749 |
| 1e7 | 4.99e-4 | 0.0142 | 0.0715 | 8/11/5 | 0.1631 |
| 1e8 | 6.16e-4 | 0.0193 | 0.1061 | 10/13/1 | 0.1716 |

- From 10^6 to 10^8 the median distance shrinks by a factor of 0.44; a 1/√t rate would give 0.1.
- Between 10^7 and 10^8, exploitability and distance get *worse*.
- **The window averages keep switching sub-family** in 18 of 24 seeds over the last two decades
  (β's sd across one seed's windows: median 0.072).
- MCCFR wanders among the sub-families, and its average sits between them.

### 4.5 Full-width CFR+ and DCFR do converge, but select nothing (new) **[E,G]**

`cfrfull.py` (vectorised full-width CFR variants) + `cfrfull_run.py`, 24 starts each (seed
perturbations of the initial regrets):

| variant | updates | iterations | exploitability (median) | certified distance (median / max) | sub-families | β (median) | b32 (median) | c33 position (median) |
|---|---|---|---|---|---|---|---|---|
| CFR | simultaneous, uniform average | 10^6 | 1.60e-4 | 2.97e-3 / 3.34e-2 | A 17, B 7 | 0.157 | 0.0045 | 0.356 |
| Linear CFR | simultaneous, linear | 10^6 | 1.38e-3 | 1.80e-2 / 4.28e-2 | **B 24** | 0.137 | 0.094 | 0.626 |
| CFR+ | alternating, RM+, linear avg | 2·10^4 | 3.68e-7 | **4.95e-6** / 1.74e-5 | A 12, C 12 | 0.121 | 0.120 | 0.174 |
| DCFR(1.5, 0, 2) | alternating | 2·10^4 | 2.54e-7 | **5.62e-6** / 6.92e-5 | A 19, B 2, C 3 | 0.128 | 0.155 | 0.153 |

**Distance over time** (median):
- CFR+: 4.2e-2 (100) → 7.5e-4 (10^3) → 1.3e-5 (10^4) → 5.0e-6 (2·10^4);
- Linear CFR stalls at about 1.6–1.9e-2 from 10^5 on;
- vanilla CFR reaches 3.0e-3 at 10^6.

All variants give `u2 = −1/48` to within 1e-6 (CFR+ range 7.2e-7), as Corollary 4.2 requires.

**Findings:**
1. **Alternating-update full-width variants converge onto the Nash set; the others do not, within
   these budgets.** "CFR does not converge in three-player games" is a statement about specific
   variants and averages, not a law.
2. **Even converged, CFR selects no refinement.**
   - Sequential equilibrium needs `b32 = 0`; CFR+ has median 0.12 and DCFR 0.155.
   - Normal-form properness needs `c33` at 1/3 of its window; CFR+ lands at 0.17 (sd 0.20).
   - The dominance prediction `c34 → 0` holds, and so does Table 3's on-path pin `a32 → 0`.
3. **The seat bias survives convergence:** β ≈ 0.12–0.13 in every variant, never near 0. Every CFR
   variant tested systematically favours P3 over P1.
4. **The sub-family a variant lands in depends on the variant:** Linear CFR lands in B in all 24
   starts; CFR+ splits A/C 12–12.



---

## 5. Noise selects, and the answer depends on the noise

### 5.1 A fixed tremble shape selects a corner and a pole **[F\*]**

Theorem 6 treats perfection as a set, and `c33` keeps an interval because the trembles may sit on the
knife-edge `r_a41 = 2(r_a11 + r_a21)`. A noisy player does not tremble on a knife-edge. So fix a
*shape* `m` and perturb the game: at every information set `i` both actions have probability at least
`ε·m_i`. With floors every set is own-reachable, so the D-condition is the exact equilibrium condition,
and an active-set Newton method solves it to machine precision. The equilibrium is followed down to
`ε = 3.9·10⁻⁶`.

| shape | solved | limit on path `(b11, b21, b23, c11)` | `c33` |
|---|---|---|---|
| uniform | yes | `(0, 1/4, 0, 0)` | `hi = 3/4` |
| 12 random, multipliers in `[1/3, 3]` | 11 | `(0, 1/4, 0, 0)` in all | `hi` in all 11 |
| 30 random, multipliers in `[1/10, 10]` | 27 | `(0, 1/4, 0, 0)` in all | `hi` in 20, `lo = 1/2` in 7 |

- **The perturbed equilibrium is isolated** in every solved case (the indifference Jacobian is
  nonsingular, smallest singular value about 1.2e-2). The continuum of the unperturbed game is gone.
- **On path every shape selects the same extreme point:** `β = 1/4`, with P2 and P3 bluffing only the
  2 (`b11 = c11 = 0`, `b21 = 1/4`, `c21 = 1/2`). Payoffs `(−1/32, −1/48, 5/96)`: the largest transfer
  from P1 to P3 in the family.
- **Off path `c33` goes to a pole of ρ.** If `m_a41 < 2(m_a11 + m_a21)`, P3 would call with the 3, so
  P1's value bet `a41` rises above its floor until P3 is indifferent, and that needs P1 indifferent on
  `a41`: `c33 → hi`. With the opposite inequality the bluffs rise instead and `c33 → lo`. All 38 solved
  shapes obey this rule.

*Why this corner* (sketch). An accidental call by a 1 lets a bluff with the 2 win a showdown that a
bluff with the 1 always loses, so the bluffs with the 1 fall to their floors. Accidental calls also
make betting the 4 strictly better than checking it, so `b41` and the bluffs behind it rise until the
next indifference binds: P1's call `a32`, at `b21 = 1/4`.

*Consequence for the incidence ratio.* Under generic trembles of one order the split of a deviator's
loss is not just undetermined: the selected equilibrium sits exactly where ρ has a pole.

CFR+ run on the perturbed game does not converge (exploitability stalls near 6e-5), which is why the
equilibria are solved by Newton's method.

### 5.2 Logit noise selects `β*` and `c33 = lo + w/3` **[F\*]**, **[P]**

The logit agent quantal response equilibrium (McKelvey & Palfrey 1998) plays the aggressive action at
set `i` with probability `1/(1 + exp(−λ·D_i/R_i))`. Its principal branch, followed from `λ = 0` by
pseudo-arclength continuation, has no turning point and reaches `λ ≈ 1700`:

| λ | b11 = b21 | c11 | b32 | position of `c33` in its window | cost(a11) | cost(a41) |
|---|---|---|---|---|---|---|
| 48 | 0.1678 | 0.2570 | 4.7e-4 | 0.448 | 0.0877 | 0.0583 |
| 184 | 0.1613 | 0.2519 | 6.7e-14 | 0.364 | 0.0685 | 0.0610 |
| 876 | 0.1615 | 0.2504 | 5.3e-64 | 0.340 | 0.0640 | 0.0624 |
| 1711 | 0.1615 | 0.2502 | 2.0e-124 | 0.337 | 0.0634 | 0.0626 |

- The branch enters **sub-family B** and the sequential set (`b32, b22, c23, c34 → 0`).
- **`c33 → lo + w/3`**, the point of Theorem 3: a tremble at set `j` has probability
  `~ exp(−λ·cost_j)`, so P3's knife-edge forces `cost(a41) = cost(a11)` in the limit.
- **`β` is pinned by an explicit equation.** Along the branch a mixed coordinate has
  `D_i = R_i·logit(x_i)/λ`. The family's indifference system is singular, so this perturbation must be
  orthogonal to the left null space of its Jacobian. In sub-family B that space is spanned by
  `e_b11 − e_b21` and `½e_b11 + ½e_b33 + e_b41`, which gives `b11 = b21 = β` and

  > **`12·logit(β) + 5·logit(1/2 + 3β/2) + 24·logit(4β) = 0`**,

  with the unique root **`β* = 0.1615744435`** in `(0, 1/4)`. The branch agrees to four digits.
- The limit: `c33 = 1/2 + 7β*/12 = 0.59425`, payoffs `(−0.027566, −1/48, 0.048399)`.

So the two standard noise models disagree about who pays: trembles put the transfer at its maximum
`β = 1/4`, logit at `β* ≈ 0.1616`. Neither is a property of the game alone.

---

## 6. Identifiability: can a player tell which equilibrium is being played?

Payoffs vary across the family (P1's and P3's by κ/4), so a player would want to know which member
the others play. In Kuhn poker, cards are seen only at showdown. `ident_probe.py` computes, in exact
arithmetic (sympy rationals), the distribution over what an observer sees: the public action history,
plus the cards of players still in at a showdown, plus the observer's own card for a seated observer.

**On path, the family is identifiable** **[E]**. The Jacobian of the observation distribution with
respect to each sub-family's free on-path parameters has full rank at an interior rational point:

| sub-family | free on-path parameters | rank (P1 / P2 / P3 / spectator) |
|---|---|---|
| A | b11, b21 | 2 / 2 / 2 / 2 |
| B | b11 (= b21), c11 | 2 / 2 / 2 / 2 |
| C | b11, b21, b23 | 3 / 3 / 3 / 3 |

There are 204 observation classes for a seated observer and 171 for a spectator.

**Equal-payoff equilibria are far apart in what they show** **[E].** x_A and x_C of §4.3 have total
variation 41/192 (P1), 159/640 (P2), 113/480 (P3) and 397/1920 (spectator). Some observations are
possible under one and impossible under the other.

**How fast** **[F]**. At x_A, the per-hand Fisher information for β is about 5.7–6.1 for every
observer, so about 6,600 hands pin β to ±0.01 (95 %). Knowing one's own card barely helps. This is a
float number at one point, for orientation only.

**The point that matters: equilibrium-ness is not identifiable.** The responses to P1's bet are never
observed, because P1 never bets. Yet they decide whether the profile is an equilibrium and whether a
bet would pay (Table 4's windows; the `b12 := 0` witness of §6 of the full draft). So an observer can learn what the
opponents do, but not whether it is an equilibrium, except by paying to bet and see. **[P]**
*Proposed follow-up:* the price of learning the off-path responses. This links to the
exploit-vs-safety trade-off.



---

## Limitations and open problems

1. **Specific variants, budgets and averaging schemes.** The distances are certified; the conclusions
   about convergence are empirical.
2. **Why do alternating full-width variants converge here, and simultaneous ones not?**
3. **What drives the seat bias** `β ≈ 0.12–0.17`? Neither noise model lands there (`1/4` and `0.1616`).
4. **Is there a regret-minimising dynamic that converges on the perturbed game**, and so selects the
   tremble limit? CFR+ does not.
5. **Identifiability** is a probe at single rational points, with float Fisher information. Open: the
   price of learning the off-path responses, which decide whether a profile is an equilibrium.

---

## References

See Appendix H for the full list with verification status. Core:

- D. Szafron, R. Gibson, N. Sturtevant. *A Parameterized Family of Equilibrium Profiles for
  Three-Player Kuhn Poker.* AAMAS 2013, 247–254.
- H. W. Kuhn. *Simplified two-person poker.* Contributions to the Theory of Games I, 1950, 97–103.
- N. Abou Risk, D. Szafron. *Using counterfactual regret minimization to create competitive
  multiplayer poker agents.* AAMAS 2010, 159–166.
- M. Zinkevich, M. Johanson, M. Bowling, C. Piccione. *Regret minimization in games with incomplete
  information.* NIPS 2007 (proceedings 2008).
- M. Lanctot, K. Waugh, M. Zinkevich, M. Bowling. *Monte Carlo sampling for regret minimization in
  extensive games.* NIPS 2009.
- O. Tammelin. *Solving large imperfect information games using CFR+.* arXiv:1407.5042, 2014.
- N. Brown, T. Sandholm. *Solving imperfect-information games via discounted regret minimization.*
  AAAI 2019.
- R. Selten (1975); D. Kreps, R. Wilson (1982); R. Myerson (1978); E. van Damme (1984, 1991);
  J. Harsanyi, R. Selten (1988).
- C. Daskalakis, C. Papadimitriou. *Three-player games are hard.* ECCC TR05-139, 2005.
- J. Nash, L. Shapley. *A simple three-person poker game.* 1950.
- B. Chen, J. Ankenman. *The Mathematics of Poker.* 2006.
- R. McKelvey, T. Palfrey. *Quantal response equilibria for extensive form games.* Experimental
  Economics 1:9–41, 1998.
- R. Aumann. *Subjectivity and correlation in randomized strategies.* J. Math. Econ. 1:67–96, 1974.
- J.-F. Mertens. *Two examples of strategic equilibrium.* Games Econ. Behav. 8:378–388, 1995.
- J. Billingham. *Equilibrium solutions of three player Kuhn poker with N > 3 cards: a new numerical
  method using regularization and arc-length continuation.* arXiv:1802.04670, 2018. (abstract only read)

