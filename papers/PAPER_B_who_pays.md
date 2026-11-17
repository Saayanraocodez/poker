# Who Pays When a Player Deviates? The Incidence Ratio in Three-Player Kuhn Poker

**Saayan Rao** — split draft, built by `papers/build_split.py` from `PAPER_DRAFT.md` Part I.

> One of three papers cut from the single working draft. Theorem, lemma and table numbers are shared
> across the three. The research record (`MASTER_DATA.md`), the code map and the reproduction commands
> are in `PAPER_DRAFT.md` Parts II–III. Claim tags: **[P]** proved, **[E]** exact computation,
> **[G]** grid or sampling evidence, **[F]** float exploration, **[F\*]** float carried to machine
> precision, **[?]** not established. The five-card game and the Hold'em line are not in this paper.

## Abstract

In a two-player zero-sum game a deviation's whole loss lands on the single opponent. With three players
the loss is split between two opponents, and Nash equilibrium does not determine the split. We study
this in three-player Kuhn poker, whose equilibrium set is known exactly (companion paper: every
equilibrium has the first player silent and follows the Szafron–Gibson–Sturtevant family on path).

We define an incidence ratio ρ, the share of a deviator's loss borne by a given opponent. On the
equilibrium family ρ is undefined on 19 of 48 coordinate directions, changes sign, and is unbounded. Its
singularities are exactly the boundary of the equilibrium region: ρ has simple poles where a deterrence
inequality becomes tight, with residue equal to the costless transfer available there (Theorems 1–2),
and the width of the indeterminate window equals the family's own payoff-transfer parameter
(Proposition 5), so it cannot be shrunk away. The parameters that locate the poles are never reached in
play and have no effect on payoffs.

What closes the question is not Nash equilibrium. Sequential rationality fixes ρ's sign; perfection and
quasi-perfection leave the same interval; every normal-form proper equilibrium has the off-path call
frequency at one interior point, `c33 = lo + w/3`, where ρ is finite and rational (Theorem 3). Two
noise models make this concrete and disagree with each other: trembles of one order drive the
equilibrium to an END of the window, a pole of ρ, and to the largest payoff transfer `β = 1/4`; logit
noise drives it to `lo + w/3` and to `β* ≈ 0.1616`, the root of an explicit equation.

## Contributions

1. **The incidence ratio and its structural facts** (Propositions 1–5).
2. **Poles on the boundary of the equilibrium set**: a three-part criterion (Theorem 1), an exact
   Möbius form with residue `R = t/D′` (Theorem 2), a hard floor (Proposition 5).
3. **Off-path determination**: who pays is decided by behaviour that never occurs.
4. **Normal-form properness forces `c33 = lo + w/3`** (Theorem 3, with a complete necessity proof).
5. **Selections**: generic trembles go to a pole and to `β = 1/4`; logit noise to `lo + w/3` and `β*`.
6. **A two-player control**: the phenomenon needs three players for two independent reasons.

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

## 3. The equilibrium set (from the companion paper)

The companion paper proves the following; they are used here as given.

- **Theorem 4.** Every Nash equilibrium is realisation-equivalent to a member of the SGS family: P1
  never bets, and Table 3 holds on every reached information set.
- **Theorem 5.** The complete Nash set is the union of twelve explicit sets; Table 4 gives the certified
  range of every coordinate. Off path, the responses to P1's bet are constrained only by P1's
  deterrence inequalities.
- **Theorem 6.** In every sequential equilibrium `b32 = b22 = c13 = c34 = 0`, `c43 = 1` and
  `c33 ∈ [1/2, 15/16]`; perfection, agent-normal-form properness and quasi-perfection leave `c33` an
  interval (Corollaries 6.1–6.2).

---

## 4. Who pays when a player deviates: the incidence ratio

### 4.1 Definitions

- **Definition 1.** At `p`, a direction `d` on player A's coordinates is *feasible* if `d_i ≥ 0` where
  `p_i = 0` and `d_i ≤ 0` where `p_i = 1`.
- **Definition 2.** For feasible `d` with `du_A/dε ≠ 0`, the incidence ratio is
  `ρ_{A→X}(d) = −(du_X/dε)/(du_A/dε)`.
- **Definition 3.** `d` is *costless* if `du_A/dε = 0`. It is *equilibrium-preserving* if `p + εd`
  stays Nash.

### 4.2 Structural facts

**Proposition 1 (constant sum is structural).** `Σ u_i = 0` on all of [0,1]^48, because chips are
conserved at each of the 312 leaves. So `ρ_{A→B} + ρ_{A→C} = 1`: ρ is a share. **[P]**

**Proposition 2.** `ρ(d) = ρ(−d)`. **[P]**

**Proposition 3 (no improving direction).** At every family point, `du_A ≤ 0` for every feasible `d`.
The feasible cone is generated by the feasible `±e_i`. **[P]** Grid check: 502,626 feasible
(point, coordinate) pairs with 0 improving, and 4,000 random multi-coordinate directions with max
`du_A = −1.44e-2`. **[G]**

| player | feasible pairs | improving | strictly costly | neutral |
|---|---|---|---|---|
| P1 | 154,224 | 0 | 111,456 | 42,768 |
| P2 | 186,618 | 0 | 52,038 | 134,580 |
| P3 | 161,784 | 0 | 57,072 | 104,712 |

**Proposition 4 (two-player collapse).** With two players `du_B = −du_A`. So no costless transfer
exists, `ρ ≡ 1`, and no pole is possible. **[P]**

### 4.3 ρ is ill-defined, sign-unstable and unbounded on the family **[G]**

- **19 of 48** coordinates have `du_A ≡ 0` at every one of 9,072 grid points:
  `a33, a44, b11, b12, b21, b22, b32, b33, b41, b42, b44, c13, c14, c23, c24, c33, c34, c43, c44`.
  21 more vanish on part of the grid.
- **The denominator is not bounded away from 0:** min `|du_A| = 1.0e-4` against κ = 0.0417. ρ reaches
  −50 and +391.
- **P2's move along the family** has `du/dβ = (−κ, 0, +κ)` identically. The headline phenomenon of
  SGS is exactly where ρ blows up.
- **Sign flips** along `a11`, `a21` and `a41`: for `+e_a11`, ρ ranges over [−48.75, +22.0].

**Costless directions exist for every player, but only P2's along-family move preserves equilibrium**
(ε = 0.01 steps):

| direction | du | exploitability after the step |
|---|---|---|
| P2 `+e_b11` | (+1/12, 0, −1/12) | 8.33e-04 |
| P2 `+e_b21` | (+1/24, 0, −1/24) | 8.33e-04 |
| P2 `+e_b41` | (−1/24, 0, +1/24) | 4.17e-04 |
| P3 `+e_c21` | (−0.0333, +0.0333, 0) | 9.17e-04 |
| P1 `+e_a11` (boundary) | (0, +0.0255, −0.0255) | 2.71e-03 |
| along-family β move | — | < 5e-16 everywhere |

**Exact closed forms** **[E]**:
- `ρ_{P2→P1}(+e_b31) ≡ 3/5` on the entire family (worked by hand in Appendix A);
- `ρ_{P3→P2}(+e_c31) = (2 − 4s − m)/(4 − 5s − m)`, with `s = b11 + b21` and `m = b23(1 − b21)`; this is
  `(2 − 4s)/(4 − 5s)` wherever `b23 = 0` (sub-families A and B);
- `ρ_{P1→P3}(+e_a31) ∈ [3/11, 2/5]`.

### 4.4 Off-path parameters decide on-path incidence **[E]**

`b32`, `c33`, `c34` and `c44` have exactly zero first derivatives for all three players at all 9,072
points. `c34` and `c44` have exploitability 7.3e-17 at every value in [0, 1]. Yet their mixed second
derivatives through P1's openings are nonzero:

| x | ∂²u/(∂a11 ∂x) | ∂²u/(∂a21 ∂x) | via a31 | via a41 |
|---|---|---|---|---|
| c34 | (0, +κ, −κ) | (0, +κ, −κ) | 0 | 0 |
| c44 | (0, −2κ, +2κ) | (0, −2κ, +2κ) | 0 | 0 |
| c33 | (−4κ, 0, +4κ) | (−4κ, 0, +4κ) | 0 | (+2κ, 0, −2κ) |
| b32 | (−4κ, +3κ, +κ) | (−4κ, +3κ, +κ) | 0 | (+2κ, −2κ, 0) |

*Unconstrained is not inert.* ρ has two independent sources of indeterminacy:
- **the denominator**, via `b32` and `c33`: constrained, but by an inequality whose boundary is
  attainable, which gives a pole;
- **the numerator**, via `c34` and `c44`: constrained by nobody.

### 4.5 Theorem 1 (pole criterion) and the census **[E,G]**

**Theorem 1.** ρ has a pole along `e_x` iff three things hold:
- (i) `du_owner/dx = 0` has a root in some free parameter;
- (ii) the root is attainable inside the Table 3 constraints;
- (iii) the numerator does not vanish there.

**Closed-form roots:**

| deviation | zero of `du_owner/dx` | round |
|---|---|---|
| +e_a11, +e_a21 | `lo = 1/2 − b32` (Table 3's lower bound on c33) | 1 |
| +e_a41 | `hi = lo + (3/4)(b11+b21) + β/4` (the upper bound) | 1 |
| +e_a31 | no root (no c33 dependence) | 1 |
| +e_a22 | `c11max = (2 − b11)/(3 + 2b11 + 2b21)` | 2 |
| +e_a32 | `b21 = (1 − 8 c11 b11)/(4 − 8 c11)` (in A: b21 = 1/4) | 2 |

So **Table 3's c33 interval is exactly P1's deterrence window**. Its lower bound exists to kill
a11/a21, its upper bound to kill a41, and both are attainable.

**Negative controls**, one per clause:
- `b34` fails (ii): its root is at `b31 = 1`, which Table 3 pins to 0.
- `c22` fails (iii): `ρ = (b11 + 3 b21)/(b11 + 4 b21)` stays in [3/4, 1] (4/5 on `b11 = b21`), then 0/0 at the corner.
- a11 with `b32 > 1/2` fails (ii): the root is below 0.

**Census over all 48 coordinates:**

| player | round-1 poles | round-2 poles |
|---|---|---|
| P1 | a11, a21, a41 | a22, a32 |
| P2 | none | none |
| P3 | c11, c21 | none |

### 4.6 Theorem 2 (exact global form) and the residues **[P,E]**

**Theorem 2.** Fix every free parameter except `c33`. Then `D(c33) = du1/da_j1` and
`N(c33) = −du3/da_j1` are both affine in `c33`, with `N′ = D′`. Hence

> **ρ(c33) = 1 + R/(c33 − c33\*)** exactly, with **R = t/D′**,

where `t` is the costless transfer at the boundary (at `c33*`, `du2 = −du3 = t` by Proposition 1).
`D′/κ` is −4 for a11 and a21, +2 for a41, and 0 for a31 (which is why a31 never poles).

| dev | D′/κ | c33* | t | R |
|---|---|---|---|---|
| a11 | −4 | 0.1000 | +0.04375 | **−21/80** |
| a21 | −4 | 0.1000 | +0.04375 | **−21/80** |
| a41 | +2 | 0.3625 | −0.00833 | **−1/10** |
| a11 | −4 | 0.5000 | −0.03646 | **+7/32** |
| a21 | −4 | 0.5000 | −0.01563 | **+3/32** |
| a41 | +2 | 0.7375 | +0.02083 | **+1/4** |
| a11 | −4 | 0.2000 | +0.06875 | **−33/80** |
| a21 | −4 | 0.2000 | +0.04271 | **−41/160** |
| a41 | +2 | 0.4500 | −0.00417 | **−1/20** |

### 4.7 Proposition 5: the hard floor **[P,E]**

The window width is **`w = hi − lo = (3/4)(b11 + b21) + β/4`**, independent of `b32`. So
`w = 0 ⟺ β = 0 ⟺ κβ = 0`: **deterrence slack and the SGS transfer are the same currency.** At
`w = 0`, a41's pole dies (its numerator vanishes) but a11's survives, as the only admissible value of
`c33`. Exactly verified at six points across all sub-families (w = 21/80, 11/40, 7/16, 19/80, 1/4).

### 4.8 Theorem 3: normal-form properness forces `c33 = lo + w/3` **[P,E]**

**Theorem 3 (necessity).** *In every normal-form proper equilibrium with `β > 0`, `c33 = 1/2 + w/3`
(that is `lo + w/3`, with `b32 = 0`). A normal-form proper equilibrium exists (Myerson 1978).*

- **Costs:** `cost(a11) = cost(a21) = 4κ(c33 − lo)` and `cost(a41) = 2κ(hi − c33)`.
- **Mechanism:** properness orders trembles by cost. P3's belief at BF holding the 3 is
  `q = (r1 + r2)/(r1 + r2 + 2 r4)`, and P3's call threshold is `q = 1/5`.
  - Any strict cost inequality sends `c33` to 0 or 1, outside the window.
  - So cost equality is needed: **`c33 = lo + w/3`**.
- **Both corners are excluded.**

*Proof.* A normal-form proper equilibrium induces a quasi-perfect, hence sequential, equilibrium (van
Damme 1984), so Theorem 6 applies: `b12 = b22 = b32 = 0`, `b42 = 1`, `c13 = c34 = 0`, `c43 = 1`. P1's
pure strategies are a plan per card, and their costs add over cards. So the cheapest strategy that
bets card `j` costs `cost(a_j1)`, and along an ε-proper sequence the total probability `r_j` of betting
card `j` is at most `Kε·r_j'` whenever `cost(a_j1) > cost(a_j'1)` in the limit.
1. *`c23 = 0`.* If `c23 > 0` then `cost(a11) = 4κ(c33 + c23 − 1/2) > cost(a21) = 4κ(c33 − 1/2)`, so
   `r1 ≪ r2`. An interior `c33` needs `r4 = 2(r1 + r2)(1 + o(1))`, so `r1 ≪ r4`; then P3's belief at BF
   holding the 2, `r1/(r1 + r3 + 2 r4)`, goes to 0 and folding is strictly better: `c23 = 0`, a
   contradiction. (A non-interior `c33` is outside the window, since `0 < 1/2 ≤ c33 ≤ hi < 1`.)
2. *Cost equality.* With `c23 = 0`, `cost(a11) = cost(a21)`. If `cost(a41) > cost(a11)` then
   `r4 ≪ r1 + r2`, `q → 1`, P3 calls and `c33 = 1`; if `cost(a41) < cost(a11)` then `q → 0` and
   `c33 = 0`. Both are outside the window, so `4(c33 − lo) = 2(hi − c33)`.
3. *The corners.* At `c33 = lo` one cost is 0 and the other positive, at `c33 = hi` the reverse; step 2
   applies. (`hi > 0` because `b32 = 0`.) ∎

*What is not proved.* That every on-path family member carries a normal-form proper equilibrium, or
which `β` properness allows. Two selections computed in §5 bear on it: the limiting logit equilibrium
sits exactly at `c33 = lo + w/3` (with `β = β* ≈ 0.1616`), while generic trembles of equal order go to
an end of the window (with `β = 1/4`).

- **ρ is finite and exactly rational** at the selected point:

| point | w | ρ(a11) | ρ(a21) | ρ(a41) |
|---|---|---|---|---|
| B, b32 = 2/5 | 21/80 | −4/7 | −4/7 | 11/7 |
| B, refined face | 21/80 | 20/7 | 20/7 | −5/7 |
| A, refined face | 11/40 | 73/22 | 49/22 | −7/11 |
| A, corner β = 1/4 | 7/16 | 5/2 | 29/14 | −5/7 |
| C, refined face | 19/80 | 83/38 | 143/38 | −11/19 |
| C, b23 at max | 1/4 | 7/4 | 29/8 | −1/2 |

*Scope:* properness on the **normal form**. Agent-normal-form properness would not order a11 against
a41, since they are different information sets.

### 4.9 The ladder **[E]**

| stage | what it does to ρ |
|---|---|
| Nash | undefined or unbounded; sign flips |
| sequential (Theorem 6) | kills the numerator source (`c34`, `c44`, `b32` pinned); ρ's sign becomes determinate, ρ(+e_a11) ∈ [1.395, 45.42] on the refined face; both poles survive |
| perfect = agent-normal-form proper, and quasi-perfect (Corollaries 6.1–6.2, at the slice of Theorem 6(5)) | the same interval of `c33`: nothing more is selected |
| normal-form proper (Theorem 3) | kills the denominator source; ρ finite and rational |

Perfection and quasi-perfection are not nested in general (Mertens 1995); here they are compared only
on the slice where both are certified.

**Sets versus selections (§5).** The rows above are sets of equilibria. A single noise model selects a
point, and where it lands depends on the model: trembles of one order go to an END of the `c33` window,
a pole of ρ (§5.1); logit noise goes to `lo + w/3`, where ρ is finite (§5.2).

### 4.10 Two-player control **[E,G]**

Independent 2-player engine: 3 cards, 30 leaves, α-family on [0, 1/3]. Max exploitability 1.9e-16 on
201 values of α, and `u1 = −1/18` exactly for every α.
- **No third party:** 0 costless transfers in 3,414 (point, direction) pairs, and ρ ≡ 1 on all 1,403
  defined pairs.
- **No slack:** the off-path region exists only at α = 0, and is pinned to a point (width 0), against
  `c33`'s width-0.2625 window in the 3-player game.

### 4.11 The one genuinely improving direction **[E]**

SGS's Table 4 mixes sub-families and is not an equilibrium: P2's exploitability there is exactly
κβ = 0.0104167. The direction is `−e_b23`, with `du = (0, +2κ, −2κ)`. P2's gain comes entirely out
of P3.

### 4.12 The dynamical-systems reading **[P,E,G]**

Learning dynamics in replicator form, one 2-simplex per set: `dx_i/dt = x_i(1−x_i) g_i(x)`.
- **The family is a manifold of fixed points** (max |dx/dt| = 1.9e-17 across the window).
- **ρ's denominator is an eigenvalue of the linearised flow.** For a pure coordinate the Jacobian row
  has only its diagonal entry `(1 − 2x_i) g_i`. Matched to 0.0e+00 in the spectrum.
- **A pole is a loss of hyperbolicity.** At `lo` the zero-eigenvalue count rises by two (a11, a21);
  at `hi` it rises by one (a41).
- **The flow does not converge** from interior starts: |dx/dt| is still about 2e-2 after 3,000 RK4
  steps. Only time averages converge.
- **Chaos: unresolved.** The two-player control's Lyapunov estimate (+0.0053, true value 0) shows a
  measurement bias larger than the three-player signal.



---

## 5. What a noise model selects

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

## Limitations and open problems

1. **Coordinate directions.** ρ is a ratio, not a convex combination of coordinate ρ's; per-direction
   values do not extend automatically. Census counts and sign ranges are grid statistics.
2. **Theorem 3 is a necessity statement.** Which `β` the normal-form proper set allows, and whether
   every such `β` carries a proper equilibrium at `c33 = lo + w/3`, are open.
3. **The two selections are machine-precision float results.** Open: prove the tremble selection for
   every shape of one order; determine `c11` in the logit limit (the first-order condition leaves it
   free; the branch gives 0.250).
4. **A vector residue identity** for four or more players, where incidence lives on a simplex.
5. **A general theorem:** in n-player constant-sum extensive games, does an equilibrium component with
   an attainable deterrence boundary always carry an unbounded incidence ratio there? (First results
   for Hold'em river games are in the full draft.)

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

