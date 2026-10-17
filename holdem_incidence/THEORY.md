# Theory: the off-path incidence mechanism beyond Kuhn poker

This note states and proves the structural results behind the experiments. They hold in **every
finite n-player, constant-sum extensive-form game with perfect recall**, which includes Kuhn
poker, every river game in this framework, and any poker game with chance moves.

Three-player Kuhn poker is then a special case: its "pole at the edge of the c33 window" and
its residue identity R = t/D′ (PAPER_DRAFT Theorems 1–2) are Theorems 5–7 below. The results
also say exactly where the mechanism can survive in richer games (Theorem 8), and that one off-path
parameter can only move incidence along a line (Theorem 10). They show as well that equilibrium
accuracy cannot control incidence near a pole (Proposition 11).

Every result has a computational check: `scripts/theory_checks.py` writes
`results/theory/theory_checks.json`, mostly in exact rational arithmetic. Labels: **[P]** proof
below; **[E]** exact computational check; **[N]** float check.

---

## Setting and notation

- Γ: a finite extensive-form game with players 1..n, chance, and perfect recall.
- **Constant sum:** Σ_i u_i(z) = κ at every terminal history z. The river games use κ = 0.
- σ: a behavioural profile.
- **Reach:** π^σ(h) = π_0(h) Π_i π_i^σ(h), where π_i^σ(h) is the product of player i's own action
  probabilities on the path to h. By perfect recall π_i^σ(h) is the same at every h in one of i's
  information sets J, written π_i^σ(J). Also π^σ(J) = Σ_{h∈J} π^σ(h).
- V_i^σ(h): player i's continuation value from h.
- σ^{I→a}: σ with information set I forced to action a.
- **The derivative vector of a mass transfer b → a at I** (owner A):
  D_i = d/dε U_i(σ_I + ε(e_a − e_b), σ_{−I}) at ε = 0.
- **The incidence ratio:** ρ_{A→Y} = −D_Y / D_A. For n players the share vector is
  s = (−D_k/D_A)_{k≠A}.
- **An off-path parameter:** θ = σ_J(a′) at an information set J of a player X ≠ A, with the mass
  1 − θ on a″. σ(θ) is σ with that one probability set to θ, everything else unchanged.

---

## Lemma 1 (affinity). [P, E]

For any information set I and fixed σ_{−I}, the map σ_I ↦ U_i(σ) is affine on the simplex over
I's actions:

  U_i(σ) = Σ_a σ_I(a) U_i(σ^{I→a}).

Hence the derivative of the transfer b → a is **exactly** D_i = U_i(σ^{I→a}) − U_i(σ^{I→b}), with
no finite-difference error. A direction that moves several information sets of the same player
has, to first order, the sum of the per-set derivatives.

*Proof.* Under perfect recall no history passes through I twice: if h ⊏ h′ were both in I, the
owner would remember at h′ the action taken at h. So every terminal history z either avoids I, and
then π^σ(z) does not involve σ_I, or passes through exactly one h ∈ I and contains exactly one
factor σ_I(a_z). Grouping the terminals of U_i = Σ_z π^σ(z) u_i(z) by the action taken at I gives
the identity. The multi-set statement follows from the product rule, because each set enters each
path's reach through at most one factor. ∎

*Check:* `tests/test_extension.py::test_mass_transfer_derivative_is_exact` verifies, exactly on a
multi-action tree, that moving mass δ changes U by exactly δ·D. `tests/test_bridge.py` verifies
all 48 Kuhn coordinates against kuhn3.

---

## Proposition 2 (constant-sum shares; two players have no mechanism). [P, E]

Σ_i D_i = 0 for every direction.
- **n = 3:** ρ_{A→B} + ρ_{A→C} = 1 wherever D_A ≠ 0. These are signed shares; they can be
  negative or exceed 1.
- **General n:** Σ_{k≠A} s_k = 1.
- **n = 2:** D_B = −D_A identically. So ρ ≡ 1, a direction that costs the deviator nothing moves
  nobody, and no incidence ratio has a pole.

*Proof.* Differentiate Σ_i U_i ≡ κ. ∎

*Check:* the two-player control (`results/control/`) gives ρ = 1 for every defined direction, and
0 costless transfers.

---

## Theorem 3 (off-path parameters: no direct effect, affine cross effect). [P, E]

Let θ be an off-path parameter at J (owner X), and let D(θ) be the derivative vector of a transfer
b → a at an information set I ≠ J of a player A ≠ X, under σ(θ). Write
Δ_i^τ(h) = V_i^τ(h a′) − V_i^τ(h a″).

1. U_i(σ(θ)) is affine in θ with slope Σ_{h∈J} π^σ(h) Δ_i^σ(h). In particular, **if π^σ(J) = 0
   every player's utility is independent of θ.**
2. D(θ) is affine in θ: D(θ) = D(θ₀) + (θ − θ₀)·C, with the **cross effect**
   C_i = Σ_{h∈J} [ π^{σ^{I→a}}(h) Δ_i^{σ^{I→a}}(h) − π^{σ^{I→b}}(h) Δ_i^{σ^{I→b}}(h) ].
3. Σ_i C_i = 0.
4. **Own-unreached sets carry no cross effect.** If π_X^σ(J) = 0, then C = 0: D does not depend
   on θ, for every deviation of every other player.

*Proof.*
- (1) is Lemma 1 at J.
- (2) Forcing I does not touch θ, because I ≠ J. So U_i(σ^{I→a}(θ)) and U_i(σ^{I→b}(θ)) are
  each affine in θ by Lemma 1 at J, with the slopes given by (1) for those profiles. Their
  difference is D_i(θ).
- (3) Σ_i Δ_i^τ(h) = κ − κ = 0 at every h.
- (4) For h ∈ J, the reach π^{τ}(h) contains the factor π_X^τ(J). This equals π_X^σ(J) = 0
  whenever τ agrees with σ on X's information sets, which σ^{I→a} and σ^{I→b} do, since A ≠ X. ∎

*Checks:*
- (1): along the OP2 sweeps (θ unreached) the utilities vary by at most the float floor.
- (3): |Σ_i C_i| over every scanned pair.
- (4), exactly: in a rationalised 24-hand pilot profile with P2's AA opening forced to 1, every one
  of the own-unreached sets × all upstream sets of P1 and P3 has C = 0 exactly.

---

## Corollary 4 (Möbius form; at most one simple pole). [P]

For Y ≠ A,

  ρ_{A→Y}(θ) = −(D_Y(θ₀) + (θ − θ₀) C_Y) / (D_A(θ₀) + (θ − θ₀) C_A).

This is a fractional-linear function of θ:
- If C_A ≠ 0 it has exactly one candidate pole, θ* = θ₀ − D_A(θ₀)/C_A, which is simple unless
  D_Y(θ*) = 0. Its residue is −D_Y(θ*)/C_A.
- If C_A = 0 there is no pole along θ.

So a large incidence ratio along an off-path parameter is never a higher-order singularity, and θ*
is an exact rational number whenever the profile is rational. ∎

---

## Theorem 5 (the residue identity, n = 3). [P, E]

Let n = 3 and let B be the third player (B ∉ {A, X}), and suppose C_B = 0. A sufficient condition
is that B's payoff does not depend on the action at J at any history of J reachable under σ^{I→a}
or σ^{I→b}: for example, **B has already folded** at every history of J. If C_A ≠ 0, then for
θ ≠ θ*

  ρ_{A→X}(θ) = 1 + t / (C_A (θ − θ*)),     ρ_{A→B}(θ) = −t / (C_A (θ − θ*)),

where t = D_B(θ*) is the **costless transfer** at the pole. At θ* the deviation costs A nothing and
moves exactly t from X to B. So the constant term is exactly 1 and the residue is R = t/C_A.

*Proof.*
1. C_X = −C_A − C_B = −C_A, by Theorem 3(3).
2. So D_A(θ) = C_A(θ − θ*) and D_X(θ) = D_X(θ*) − C_A(θ − θ*).
3. D_B(θ) = D_B(θ*) = t, because C_B = 0.
4. Proposition 2 at θ* gives D_X(θ*) = −t.
5. Substituting, ρ_{A→X} = (t + C_A(θ − θ*)) / (C_A(θ − θ*)). ∎

*Kuhn as a special case:* θ = c33 is P3's call after P1 bets and **P2 folds**, so C_P2 = 0. Then
C_A = D′, and PAPER_DRAFT Theorem 2's "N′ = D′, constant term 1, R = t/D′" is exactly this theorem.

*Check, exact (bridge):* for a11, a21 and a41 against c33, C_P2 = 0 and the identity holds exactly
at 40 rational points:
- a11, a21: C = (−1/6, 0, 1/6), θ* = 1/10, t = 11/480, R = −11/80;
- a41: C = (1/12, 0, −1/12), θ* = 29/80, R = −1/10.

On the 24-hand OP2 sweeps (P2 folded before θ), C_P2 = 0 and the residue form holds to float
precision.

---

## Theorem 6 (the window theorem). [P, E]

Let σ be a Nash equilibrium and θ an off-path parameter at an unreached set J (π^σ(J) = 0). Then

  W = { θ ∈ [0, 1] : σ(θ) is a Nash equilibrium }

is a **closed interval** containing θ₀. Explicitly, W = { θ : G(θ) ≤ 0 }, where

  G(θ) = max_{i ≠ X} max_{τ_i pure} [ U_i(τ_i, σ_{−i}(θ)) − U_i(σ) ]

is convex and piecewise linear. Every endpoint of W inside (0, 1) is a zero of the gain of some
pure deviation of some player i ≠ X, whose gain is affine in θ with a nonzero slope.

*Proof.*
1. By Theorem 3(1), U_j(σ(θ)) = U_j(σ) for every j and θ.
2. X's own deviations replace σ_X, θ included, so X's best-response value does not depend on θ,
   and X's condition holds for every θ.
3. For i ≠ X and each pure τ_i, U_i(τ_i, σ_{−i}(θ)) is affine in θ (Lemma 1 at J for the profile
   (τ_i, σ_{−i})).
4. σ(θ) is Nash iff no pure deviation pays, i.e. iff G(θ) ≤ 0. G is a maximum of finitely many
   affine functions, hence convex and piecewise linear.
5. A sublevel set of a continuous convex function on [0, 1] is a closed interval, and θ₀ ∈ W.
6. At an interior endpoint, G = 0 and G > 0 just outside, so the active affine piece vanishes
   there with a nonzero slope. ∎

Nash places no condition on X's behaviour at J itself; sequential rationality would, which is why
the refinements of PAPER_DRAFT Theorem 6 can shrink W.

*Check, exact (bridge):* on a 1/160 grid, the profiles σ(c33) with exactly zero residuals form the
contiguous block [1/10, 29/80], which is Table 3's window. On the OP2 sweeps r₁(θ) has nonnegative
second differences (convexity).

---

## Theorem 7 (attainable poles sit on the window's boundary). [P, E]

Same setting. Let I be an information set of A ≠ X, and D(θ) the derivative of the transfer b → a
at I.
- (a) If σ_I(a) = 0 (A never plays a at I), then D_A(θ) ≤ 0 on W.
- (b) If moreover C_A ≠ 0 and θ* ∈ W, then θ* is an **endpoint** of W. On the far side of θ* the
  transfer b → a strictly pays, so the family leaves the Nash set exactly at the pole. As θ → θ*
  inside W, |ρ_{A→Y}| → ∞ for every Y with D_Y(θ*) ≠ 0.
- (c) If σ_I is interior and π_A^σ(I) > 0, then D_A ≡ 0 on W. So if W has nonempty interior,
  C_A = 0: **a mixed coordinate never carries an attainable pole along an off-path parameter.**

*Proof.*
- (a) By Lemma 1, U_A(σ(θ)) = U_A(σ^{I→b}(θ)) when σ_I(b) = 1 (binary case; the multi-action
  case is the same with the support of σ_I). The Nash condition U_A(σ^{I→a}(θ)) ≤ U_A(σ(θ)) is
  D_A(θ) ≤ 0.
- (b) An affine function that is ≤ 0 on an interval and has a nonzero slope cannot vanish inside
  it. If θ* ∈ W it is an endpoint, and beyond it D_A > 0, so σ(θ) is not Nash there.
- (c) Interior play at an own-reachable set means indifference, D_A(θ) = 0 for θ ∈ W. An affine
  function vanishing on an interval has zero slope. ∎

This is the general form of the Kuhn observation that "Table 3's c33 interval *is* P1's deterrence
window, and each end is a pole for a different deviation".

*Check:* the positive-control scan finds Kuhn's c33 poles exactly at the two window ends:
- a11/a21 at 1/10;
- a41 at 29/80;
- every validated witness passes the family check on one side only.

---

## Theorem 8 (which unreached information sets can carry the mechanism). [P, E]

In a river game with root prior q over compatible deals, an information set is J = (X, h, H): own
hand h, public history H. Perfect recall and the product form of reach give

  π^σ(J) = π_X^σ(H | h) · q(h) · E_q[ Π_{Y≠X} π_Y^σ(H | d_Y) | d_X = h ].

Write Pr_{−X}(H) = Σ_d q(d) Π_{Y≠X} π_Y^σ(H | d_Y) for the probability of the OTHER players'
actions in H. An unreached J is of (at least) one of three kinds:

| kind | condition | can it carry a cross effect? |
|---|---|---|
| **own-unreached** | π_X^σ(H \| h) = 0 | **never** (Theorem 3(4)) |
| **opponent-silent** | Pr_{−X}(H) = 0: some other player never takes an action of H, with any hand | yes, when another player's deviation reaches H |
| **blocker-unreached** | Pr_{−X}(H) > 0 but E[Π_{Y≠X} π_Y(H \| d_Y) \| d_X = h] = 0: the others take the actions in H only with hands that share a card with h | yes, when another player's deviation reaches H with hands h does not block |

Consequences:
1. **The Kuhn mechanism needs a silent action.** In Kuhn's equilibria P1 never bets with any card,
   so every response to a bet is opponent-silent. If at every reached public node every action is
   taken with positive probability by some hand of the actor, no set is opponent-silent. Then the
   only possible carriers are blocker-unreached sets.
2. **Blocker-unreached sets are a card-level route.** Kuhn has total card removal (one card per
   rank); Hold'em has partial removal, where two hands can share one card. Example: if P1 bets
   only combos containing A♠, a responder holding A♠K♠ never faces the bet. A P1 deviation with
   A♥A♦ reaches that response set, and it can then shift the split of P1's deviation.
3. **Rare sets inherit the bound.** The cross effect of Theorem 3(2) is a sum of reaches under the
   forced profiles times payoff differences, and each reach carries X's own factor π_X^σ(H | h).
   So |C_i| ≤ 2M·π_X^σ(H | h), where M bounds |u|: an own-rare set carries an own-rare cross
   effect.

*Proof.* Split the reach of each h′ ∈ J into X's factor, which depends only on h by perfect
recall, chance, and everyone else's. A zero of the product is a zero of one factor. The second
factor vanishes either because the others' actions in H never occur at all (opponent-silent), or
because they occur only with hands incompatible with h (blocker). Own-unreached is Theorem 3(4).
For the other two kinds, the cross effect is nonzero only if forcing the deviation at I gives J
positive reach. The bound in (3) is the reach factorisation with |Δ_i| ≤ 2M. ∎

*Check:* `T8_classification` classes every rare or unreached set of every analysed profile by its
smallest factor (own reach, Pr_{−X}(H), or the blocking ratio). Results, all 48 analysed
profiles:

| profiles | rare / unreached sets | validated off-path witnesses |
|---|---|---|
| pilot (12), pot 6 (3), four boards × R36 (12), two weightings × R36 (6) | **own-rare only** (12–53 per profile) | **0** in all 33 |
| pot 1.5 (3) | **opponent-silent-rare** (144 per profile) | **10–12** each (class level), exact |
| bridge, exact SGS (7) | opponent-silent-unreached 12–24, blocker-unreached 2–3, own-unreached 0–1 | 6–16 each |
| bridge, DCFR (3) | opponent-silent-rare 12, blocker-rare 3 | 14–16 each |
| two-player control (2) | none | — |

The theorem predicts the empirical pattern without exception: a profile has witnesses exactly
when it has opponent-silent sets.

---

## Theorem 9 (zero-sum two-party continuation). [P]

If after the deviation at I every path to J has eliminated every player except A and X, then
C_B = 0 for every other player B. In three players this is the hypothesis of Theorem 5, so the
residue identity holds. This is why incidence along deterrence windows that open after a fold is
always "1 + simple pole".

*Proof.* A folded player's payoff is fixed below the fold, so Δ_B ≡ 0 on J. ∎

---

## Theorem 10 (one off-path parameter moves incidence along a line). [P, E]

For any n, and any profile (no equilibrium assumption), the share vector s(θ) = (−D_k(θ)/D_A(θ))_{k≠A}
lies on a straight line in the hyperplane Σ s_k = 1. Explicitly, when C_A ≠ 0,

  s(θ) = λ(θ) s(θ₀) + (1 − λ(θ)) s_∞,   λ(θ) = D_A(θ₀) / D_A(θ),   s_∞ = −C_{−A}/C_A.

When C_A = 0, s(θ) = s(θ₀) − (θ − θ₀) C_{−A}/D_A(θ₀).

So for n ≥ 4, where shares live in an (n−2)-dimensional set, a single off-path parameter can only
move incidence in one direction. The full-dimensional achievable share sets measured at n = 4, 5
(GENERALIZATION.md: affine rank n − 2) need at least n − 2 independent sources of variation.

*Proof.* Substitute D(θ) = D(θ₀) + (θ − θ₀)C, and write (θ − θ₀) = (D_A(θ) − D_A(θ₀))/C_A. ∎

*Check, exact:* a four-player river game (one combo each of 99 JJ QQ KK AA; 120 deals; 3,960
leaves) at a random rational profile. With θ = P4's KK call after B-F-F and P1's JJ bet as the
deviation, all eleven share vectors are exactly collinear (every 2×2 minor vanishes) and each sums
to exactly 1.

---

## Proposition 11 (equilibrium accuracy does not control incidence). [P, E]

There are exact Nash equilibria σ, σ′ of the bridge game (equivalently, three-player Kuhn poker)
with ‖σ − σ′‖_∞ = ε and |ρ(σ) − ρ(σ′)| = 11/(160 ε), for every ε ∈ (0, 1/10]. Hence no bound of the
form |ρ(σ) − ρ(σ_true)| ≤ f(NashConv(σ)) can hold near a pole, even when both NashConvs are exactly
0. A small residual says nothing about the accuracy of an incidence ratio near a zero denominator.

*Proof.* Take σ(θ) on the c33 window [1/10, 29/80] of the sub-family-B point, with θ = 1/10 + ε and
θ = 1/10 + 2ε. Both are inside W, hence exact equilibria (Theorem 6, verified). By Theorem 5 with
R = −11/80, ρ_{P1→P3} = 1 + R/(θ − 1/10), so the difference is |R|/(2ε) = 11/(160 ε). ∎

*Check, exact:* ε = 10⁻², 10⁻⁴, 10⁻⁶ give exact residuals (0, 0, 0) at both points and ρ
differences 6.875, 687.5 and 68,750.

---

## What the theory predicts, and what the experiments found

- **Where P1 opens, the Kuhn route is closed.** In the 24-hand game at pot 3 and pot 6, and in
  every 36-hand panel game, P1 opens with some hands (AA for value, JJ or suited connectors as
  bluffs). No response set is then opponent-silent. All rare sets are own-rare (a player's
  continuation after an action they essentially never take), which Theorems 3(4) and 8(3) say
  carry no cross effect. The scan found 0 witnesses in all 33 such profiles.
- **Where an action is silent, the mechanism reappears.** In the 24-hand game with pot 1.5, P1
  never opens: every response to a bet is opponent-silent. The scan finds 10–12 class-level
  witnesses per seed. After rationalisation the profile is an **exact** Nash equilibrium, and
  every witness is exact (Theorems 5–7):
  - an exact rational root θ*;
  - D_A(θ*) = 0 exactly, with a nonzero numerator;
  - exact residuals 0 on the kept side up to θ*.
- **Imposing silence (OP2, pot 3) reopens the structure but not the equilibrium.** With P1's
  opening forced to check, the poles are back, at θ* = 27/32 for the JJ bluff and ≈ 0.829 for
  the AA value bet. C_P2 = 0, so the residue form of Theorem 5 holds. But the two deterrence
  windows {θ ≥ 27/32} and {θ ≤ 0.829} do not meet, so W is empty along this parameter and no
  equilibrium carries either pole. The best deterrence found over all 72 responses leaves P1
  ≈ 1.0e-3 bb.
- **Still open: the blocker route.** Blocker-unreached sets occur in the bridge's exact family.
  No expanded-game profile here had one, so whether a blocker set can carry an equilibrium pole
  in a real-card game is untested.
