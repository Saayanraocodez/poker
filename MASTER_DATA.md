# COMPLETE DATA RECORD
## Three-player Kuhn poker: deviation incidence on the Szafron–Gibson–Sturtevant family

Every number, table, derivation, dead end and open question this project produced. Nothing is
summarised away. Written to be mined for a paper, not read straight through.

**Evidence tags used throughout**

| tag | meaning |
|---|---|
| **[P]** | proved — closed form or structural argument, holds on the continuum |
| **[E]** | exact computation — rational arithmetic or machine precision at enumerated points |
| **[G]** | grid / multi-seed evidence — holds at every tested point, not a proof |
| **[X]** | tested and REFUTED, or a method that failed |
| **[?]** | plausible, NOT established here — do not assert |

---

# PART 0 — SOURCE AND SCOPE

**Source paper.** Duane Szafron, Richard Gibson, Nathan Sturtevant, *"A Parameterized Family of
Equilibrium Profiles for Three-Player Kuhn Poker"*, AAMAS 2013, pp. 247–254.
<https://www.ifaamas.org/Proceedings/aamas2013/docs/p247.pdf>

**Taken from it.** The game definition, Table 1 (parameter naming), Table 2 (21 necessary
values), Table 3 (the family and three sub-families), Table 4 (a deliberately mismatched
profile), Appendix equations (3), (4), (5). All transcribed verbatim.

**Added here.** The incidence ratio ρ and its complete analysis; a pole criterion; a residue
theorem; a refinement ladder; the N = n+1 law across n = 3…6; two errata; and a catalogue of
failed hypotheses.

**The scope caveat that governs everything.** SGS leave open whether their family contains ALL
equilibria. Every claim about the four-card game is conditional on being inside it. Part 10
records four separate attempts to settle this, all inconclusive.

---

# PART 1 — CODE INVENTORY AND VALIDATION CHAIN

Python 3.13, numpy only (matplotlib for figures). No randomness in any headline result; random
draws sample validation points under fixed seeds.

| file | role |
|---|---|
| `kuhn3p.py` | 4-card 3-player engine: 312-leaf tree, exact utilities, gradients, best response, reach, rational utilities |
| `family.py` | SGS Tables 2 and 3 transcribed; constraint checker `violations()`; sub-family constructors |
| `grids.py` | the 9,072-point family grid and dense 1-D sweeps |
| `kuhn2p.py` | independent 2-player engine (30-leaf tree), α-family |
| `kuhnNp.py` | 3-player, N-card engine |
| `kuhnGen.py` | **n-player, N-card** engine — the general one |
| `cfr3p.py`, `cfrNp.py`, `cfrGen.py` | external-sampling MCCFR for each engine |
| `poletest.py` | the local pole criterion, engine-agnostic |
| `properness.py` | the d_free vs d_cond dimension test |
| `certify.py` | Newton on the indifference system + greedy support repair |
| `decompose.py`, `causal.py`, `counterfactual.py` | the mechanism analyses |
| `dominance.py`, `iterdom.py`, `enum_full.py` | dominance scan and pruned support enumeration |
| `dynamics.py` | replicator flow, exact Jacobian, spectrum (Part 14) |
| `chaos.py` | Lyapunov exponent measurement and its two-player calibration |
| `verify_paper.py` | validation against the published paper |
| `handcheck.py` | the hand-reproducible worked example |
| `analyze.py`, `followup*.py`, `sweep*.py`, `hunt.py`, `certify45.py`, `enumerate_support.py` | study scripts |
| `plots.py`, `plots2.py` | figures 1–4 |

## 1.1 Cross-validation between independent implementations [E]

Each engine is validated by requiring it to reproduce its predecessor.

| engine | scope | validated against | discrepancy |
|---|---|---|---|
| `kuhn3p` | 3 players, 4 cards, 312 leaves | the SGS paper (Part 3) | ≤ 8.9e-16 |
| `cfr3p` | independent tree for MCCFR | `kuhn3p`, 200 random profiles | **1.1e-16** |
| `kuhnNp` | 3 players, N cards | `kuhn3p` at N=4 | **0.0 exactly** (reach 2.5e-16) |
| `kuhnGen` | n players, N cards | `kuhnNp` at n=3, N=4,5,6 | 8.9e-16 / 1.4e-15 / 1.9e-15 |
| `kuhn2p` | 2 players, 3 cards, 30 leaves | known value u₁ = −1/18 | exact rational |

Component checks: `gradient()` vs `dcoord()` → 3.9e-16 to 1.75e-15; `best_response_bi()` vs
brute force → 4.4e-16 to 5.6e-16; vectorised `pole_test` vs direct per-pair → root error
4.0e-15, numerator error 1.7e-16.

## 1.2 Structural formulas, confirmed exactly (not fitted) [E]

| quantity | formula | n=3 | n=4 | n=5 | n=6 |
|---|---|---|---|---|---|
| leaves per deal | n·2^(n−1) + 1 | 13 | 33 | 81 | 193 |
| situations per player | 2^(n−1) | 4 | 8 | 16 | 32 |
| parameters | n·N·2^(n−1) | 12N | 32N | 80N | 192N |
| deals | N!/(N−n)! | 24 @N=4 | 120 @N=5 | 720 @N=6 | 5,040 @N=7 |

Sizes built: (5,7) = 2,520 deals / 204,120 leaves / 560 params, builds in **1.35 s**.
(6,8) = 20,160 deals / 3,890,880 leaves / 1,536 params.

## 1.3 Performance work required to reach n = 6 [E]

| problem | cause | fix | before | after |
|---|---|---|---|---|
| memory | per-(player,card) slice cached one full leaf-table copy **per player** | build lazily | (6,8) ~6 GB | **266 MB** |
| memory | int64 indices, float64 payoffs | int32 / int8 | (6,7) ~1.5 GB | **69 MB** |
| gradient | O(maxf²) product recomputation | prefix/suffix + `bincount` | — | 1.0 s @(6,7) |
| best response | brute force 2^16 per card at n=5 | backward induction | infeasible | 2.1 s @(5,6) |
| utilities | (nleaf × nplayer) temporary | matvec `w @ PAY` | — | — |

---

# PART 2 — THE GAME AND NOTATION

## 2.1 Rules

Deck {1,2,3,4}; three players; one card each; one card undealt. 24 deals, each of probability
**κ = 1/24 ≈ 0.0416667**. Everyone antes 1. One betting round, order P1 → P2 → P3.

- No bet outstanding: the actor **checks (K)** or **bets (B)** one chip.
- Once anyone bets: every other player, *including those who already checked*, answers
  **fold (F)** or **call (C)**, in order, wrapping around.
- No raises. Highest unfolded card takes the pot.

13 terminal histories per deal → **312 leaves**:
`BFF BFC BCF BCC KBFF KBFC KBCF KBCC KKK KKBFF KKBFC KKBCF KKBCC`

## 2.2 Parameterization (SGS Table 1)

`a_jk` / `b_jk` / `c_jk` = probability that P1 / P2 / P3 takes the **aggressive** action
(B with no bet out, C facing a bet) holding card *j* in situation *k*.

| k | P1 history | P2 history | P3 history |
|---|---|---|---|
| 1 | (root) | K | KK |
| 2 | KKB | B | KB |
| 3 | KBF | KKBF | BF |
| 4 | KBC | KKBC | BC |

A profile is the 48-vector `[a₁₁..a₄₄, b₁₁..b₄₄, c₁₁..c₄₄]`;
index = `player·16 + (card−1)·4 + (situation−1)`.
Call k=1 a **round-1 (opening)** decision and k=2,3,4 **round-2 (call/fold)** decisions.

## 2.3 The general n-player betting rule

Verified to reproduce SGS's tree exactly at n=3:

```
bettor = index of first 'B' in history, else None
if bettor is None:  terminal if len(hist) == n, else actor = len(hist)
else:               nresp = len(hist) - bettor - 1
                    terminal if nresp == n-1, else actor = (bettor + 1 + nresp) mod n
```

---

# PART 3 — THE PUBLISHED FAMILY AND ITS VALIDATION

## 3.1 Table 2 — 21 necessary values

`a₁₂=a₁₃=a₁₄=a₂₄=0`, `a₄₂=a₄₃=a₄₄=1`, and the same pattern for b and c.
**Independently confirmed by dominance computation: 21 / 21.** See §10.1. [E]

## 3.2 Table 3 — the family

With **β = max{b₁₁, b₂₁}**:

- **P1 has no free parameters:** `a₁₁=a₂₁=a₂₂=a₂₃=a₃₁=a₃₂=a₃₄=a₄₁=0`, `a₃₃=1/2`.
- **P2 free:** `b₁₁, b₂₁, b₂₃, b₃₂`; `b₂₂=b₃₁=b₃₄=0`;
  `b₃₃ = ½ + (b₁₁+b₂₁)/2 + β/2 − b₂₃(1−b₂₁)`; `b₄₁ = 2b₁₁ + 2b₂₁`.
- **P3 free:** `c₁₁, c₃₃, c₃₄`; `c₂₁ = ½ − c₁₁`; `c₂₂=c₂₃=c₃₁=c₃₂=0`; `c₄₁=1`.

**Constraints:**
```
b₂₃ ≤ max{0, (b₁₁−b₂₁)/(2(1−b₂₁))}
c₁₁ ≤ min{½, (2−b₁₁)/(3+2b₁₁+2b₂₁)}
b₃₂ ≤ ½ + ¾(b₁₁+b₂₁) + β/4
½ − b₃₂ ≤ c₃₃ ≤ ½ − b₃₂ + ¾(b₁₁+b₂₁) + β/4
0 ≤ c₃₄ ≤ 1
```

**Three sub-families:**

| | condition | β |
|---|---|---|
| A | `c₁₁ = 0`, `b₁₁ ≤ b₂₁ ≤ ¼`, `b₂₃ = 0` | b₂₁ |
| B | `0 < c₁₁ < ½`, `b₂₁ = b₁₁ ≤ ¼`, `b₂₃ = 0` | b₁₁ |
| C | `c₁₁ = ½`, `b₁₁ ≤ ¼`, `b₂₁ ≤ min{b₁₁, ½−2b₁₁}` | b₁₁ |

**Utilities:** `u₁ = −κ(½+β)`, `u₂ = −κ/2`, `u₃ = κ(1+β)`, β ∈ [0, ¼].

## 3.3 Reachability — the fact everything depends on

Because `a_j1 = 0` for every j, **P1 never bets anywhere in the family.** Therefore P2 never
answers a bet and P3 never reaches the post-bet subtrees. The coordinates
`b₁₂, b₂₂, b₃₂, b₄₂` and `c₁₃, c₂₃, c₃₃, c₄₃, c₁₄, c₂₄, c₃₄, c₄₄` have **reach probability zero
family-wide** — not at a corner, everywhere. This includes two of the family's own free
parameters, `b₃₂` and `c₃₃`.

## 3.4 Validation against the paper [E]

| check | sample | max error |
|---|---|---|
| Table 3 utilities | 600 random family points | **5.0e-16** |
| exact rational at b₁₁=1/8, b₂₁=1/4 | 1 point | u = (−1/32, −1/48, 5/96) exactly |
| worked leaf a₁₃ in deal 124 | 1 leaf | factors (1−a₁₁)·b₂₁·(1−c₄₂)·a₁₃, payoff (−2,3,−1) — matches |
| Appendix eq. (3), u₃ with P3 free | 400 random points | **6.0e-16** |
| Appendix eq. (4), u₂ with P2 free | 400 random points | **2.2e-16** |
| Appendix eq. (5), u₁ with P1 free | 400 random points | **8.9e-16** |
| Table 4 mismatched profile, P2 gains κβ | 1 profile | 0.0104167 exactly |
| best-response gap on family points | 450 random points | **< 5e-16** |

Matching eq. (3)/(4)/(5) is the strong test — those polynomials pin down the tree and the
transcription simultaneously.

---

# PART 4 — ERRATA IN THE PUBLISHED PAPER

## 4.1 Erratum 1 — MATERIAL. The `b₃₃` formula in the Section 5 prose [E]

For the `c₁₁ = ½` sub-family, SGS Section 5 states `b₃₃ = (1 + b₁₁ + 2b₂₁)/2`. Table 3's general
formula gives `½ + (b₁₁+b₂₁)/2 + β/2 − b₂₃(1−b₂₁)`, i.e. with β = b₁₁,
`(1 + 2b₁₁ + b₂₁)/2 − b₂₃(1−b₂₁)`. The prose version transposes b₁₁ and b₂₁ and drops the b₂₃
term. They agree only when `b₁₁ = b₂₁` and `b₂₃ = 0`, or at `b₂₃ = b₂₃^max`.

Where they differ the prose value is **not an equilibrium**:

| b₁₁ | b₂₁ | b₂₃ | b₃₃ Table 3 | b₃₃ prose | exploitability (T3) | exploitability (prose) |
|---|---|---|---|---|---|---|
| 0.20 | 0.05 | 0 | 0.72500 | 0.65000 | 2.2e-16 | **6.25e-03** |
| 0.15 | 0.10 | 0.02 | 0.68200 | 0.67500 | 7.3e-17 | **5.83e-04** |
| 0.20 | 0.05 | 0.079 | 0.65000 | 0.65000 | 2.2e-16 | 2.2e-16 |
| 0.10 | 0.10 | 0 | 0.65000 | 0.65000 | 7.6e-17 | 7.6e-17 |

Table 3's formula is correct and is what the Appendix proof uses.

**A detail worth its own sentence:** `du_i/db₃₃ = (0, 0, 0)` — b₃₃ affects nobody's payoff at
all, yet setting it wrong destroys the equilibrium. It is a pure deterrence parameter, and it
foreshadows the paper's entire mechanism.

## 4.2 Erratum 2 — cosmetic. A sign in Lemma 4 [E]

Lemma 4 displays `∂u₂/∂b₂₃ = 2κ(1−b₂₁)(1−2c₁₁)`. Differentiating the paper's own eq. (4) gives
`2κ(1−b₂₁)(2c₁₁−1)`. The paper's immediately following usage ("If c₁₁ = 0, then
∂u₂/∂b₂₃ = −2κ(1−b₂₁) ≤ 0") matches the corrected sign, so no theorem is affected. Our engine
matches eq. (4) to 2.2e-16, confirming the correction.

---

# PART 5 — FORMAL RESULTS

Stated for a finite n-player constant-sum extensive game with binary information sets,
parameterized by p ∈ [0,1]^M.

## Definition 1 — feasible direction
At p, a direction d supported on player A's coordinates is *feasible* if `d_i ≥ 0` wherever
`p_i = 0` and `d_i ≤ 0` wherever `p_i = 1`. The feasible set is a polyhedral cone whose extreme
rays are exactly the feasible ±e_i.

## Definition 2 — incidence ratio
For feasible d with `du_A/dε ≠ 0`: **ρ_{A→X}(d) = −(du_X/dε)/(du_A/dε)**.

## Definition 3 — costless vs equilibrium-preserving
d is *costless* for A if `du_A/dε = 0`. It is *equilibrium-preserving* if `p + εd` remains a
Nash equilibrium for small ε > 0. **These are different**, and the distinction matters (§7.4).

## Proposition 1 — constant sum is structural [P]
`Σᵢ uᵢ(p) = 0` on **all** of [0,1]^M, not merely on the equilibrium set.
*Proof:* every leaf pays out exactly the chips paid in, so the payoffs sum to zero at each of the
312 leaves; expectation inherits it. ∎
*Corollaries:* `Σᵢ duᵢ = 0` for every direction, on and off equilibrium; hence
**ρ_{A→B} + ρ_{A→C} = 1** — ρ is a *share*.
*Numerics:* max |Σdu| = **3.5e-16** exact, 2.8e-11 by central difference at h=1e-5 (pure
round-off from dividing by 2h); 1.1e-15 → 2.1e-14 across all (n,N). **Zero points flagged.**

## Proposition 2 — orientation invariance [P]
`ρ(d) = ρ(−d)`; numerator and denominator both flip sign. ρ depends only on *which* coordinate
is perturbed, not the sign of the step.

## Proposition 3 — no improving direction [P,G]
At every point of the family, `du_A/dε ≤ 0` for every feasible d, for every A.
*Proof:* `du_A(d) = Σᵢ dᵢ ∂u_A/∂xᵢ` is linear in d; the feasible cone is generated by the
feasible ±eᵢ; each generator has du_A ≤ 0 or the profile is not an equilibrium; a nonnegative
combination of nonpositive numbers is nonpositive. ∎

| player | feasible pairs | improving | strictly costly | neutral (du_A = 0) |
|---|---|---|---|---|
| P1 | 154,224 | **0** | 111,456 | 42,768 |
| P2 | 186,618 | **0** | 52,038 | 134,580 |
| P3 | 161,784 | **0** | 57,072 | 104,712 |
| **total** | **502,626** | **0** | 220,566 | 282,060 |

Plus 4,000 random feasible **multi-coordinate** directions: max du_A = **−1.44e-02**, none
positive.

## Proposition 4 — two-player collapse [P]
With n=2, `du_B = −du_A` identically. Hence (a) no costless transfer exists — `du_A = 0` forces
`du_B = 0`; (b) ρ ≡ 1 wherever defined; (c) no pole is possible, since numerator and denominator
are the same number up to sign and vanish together. ∎

## Proposition 5 — hard floor [P,E]
`w = hi − lo = ¾(b₁₁+b₂₁) + β/4`, **independent of b₃₂**.
*Proof:* `lo = ½ − b₃₂`, `hi = ½ + ¾(b₁₁+b₂₁) + β/4 − b₃₂`; subtract. ∎
Every term is non-negative, so **w = 0 ⟺ b₁₁ = b₂₁ = 0 ⟺ β = 0 ⟺ κβ = 0.**

| point | b₁₁ | b₂₁ | b₃₂ | w measured | w formula | κβ |
|---|---|---|---|---|---|---|
| B, b₃₂=2/5 | 3/20 | 3/20 | 2/5 | **21/80** | 21/80 | 1/160 |
| B, refined face | 3/20 | 3/20 | 0 | **21/80** | 21/80 | 1/160 |
| A, refined face | 1/10 | 1/5 | 0 | **11/40** | 11/40 | 1/120 |
| A, corner β=¼ | 1/4 | 1/4 | 0 | **7/16** | 7/16 | 1/96 |
| C, refined face | 1/5 | 1/20 | 0 | **19/80** | 19/80 | 1/120 |
| C, b₂₃ at max | 1/4 | 0 | 0 | **1/4** | 1/4 | 1/96 |

*Consequence:* deterrence slack and the SGS transfer are the same currency. The window cannot be
closed without destroying the transfer that motivates the study.

**The collapse is asymmetric.** At b₁₁ = b₂₁ = 0 the window degenerates to {½}:

| dev | D′/κ | t = du₂ at c₃₃* | du₃ | du₁ | verdict |
|---|---|---|---|---|---|
| a₁₁ | −4 | **−1/48** | +1/48 | 0 | **still a POLE** |
| a₄₁ | +2 | 0 | 0 | 0 | 0/0, clause (iii) fails |

a₄₁'s numerator vanishes with the window so its pole dies; a₁₁'s does not — the singular point
becomes the *only admissible* value of c₃₃. Shrinking the window is doubly futile.

## Proposition 6 — incidence is an (n−2)-simplex [P,E]
Shares `s_k = (∂u_k/∂y)/(−∂u_A/∂y)` satisfy `Σ_{k≠A} s_k = 1`.
- **n=2:** the simplex is a point, s = 1 forced. There is no incidence question.
- **n=3:** one dimension — a single scalar ρ. *The only case where "the split" is a number.*
- **n≥4:** (n−2) dimensions — ρ becomes a vector.

*Verified:* max |Σs − 1| = **2.8e-13 → 8.7e-12**. Affine rank of the achievable share set:

| n | N | costly directions | affine rank | n−2 |
|---|---|---|---|---|
| 3 | 4, 5, 6 | 48, 60, 72 | **1** | 1 |
| 4 | 5, 6 | 160, 192 | **2** | 2 |
| 5 | 6 | 480 | **3** | 3 |
| 6 | 7, 8 | 1344, 1536 | **4** | 4 |

Rank = n−2 in **all 122 solver runs**.

## Theorem 1 — the pole criterion [E,G]
ρ has a pole along e_y **iff** all three hold:
- **(i)** `du_A/dy = 0` has a root in some free coordinate x;
- **(ii)** that root is attainable inside the family's constraints;
- **(iii)** the numerator `du_C/dy` does not vanish there.

A witness for each failure mode is in §7.5.

## Theorem 2 — exact global form for ρ [P,E]
Fix every free parameter but c₃₃. Then `D(c₃₃) = du₁/da_{j1}` and `N(c₃₃) = −du₃/da_{j1}` are
both affine in c₃₃, and moreover **N′ = D′**. Hence ρ is a Möbius function with a pole of order
exactly 1, and

> **ρ(c₃₃) = 1 + R/(c₃₃ − c₃₃*)** — exactly, not asymptotically — with **R = N(c₃₃*)/D′**.

`D′ = ∂²u₁/(∂a_{j1}∂c₃₃)` equals **−4κ** for a₁₁ and a₂₁, **+2κ** for a₄₁, and **0** for a₃₁ —
which is precisely why a₃₁ can never have a pole.

At c₃₃* the denominator vanishes, so the deviation is costless for P1 and Proposition 1 forces
`du₂ = −du₃ = t`. Hence `N(c₃₃*) = t` and **R = t/D′**: the residue *is* the magnitude of the
costless transfer available at that boundary, divided by the mixed second derivative.

*Verified:* N′/D′ = 1 exactly and residual error **0.0e+00** in exact rational arithmetic at six
family points × three deviations. Second differences of N and D in c₃₃ < 2.2e-16. This supersedes
the weaker `ρ = R/(c₃₃−c₃₃*) + O(1)` — the O(1) term is exactly 1.

## Theorem 3 — properness selection [P,E]
Under Myerson properness on the normal form, an interior c₃₃ requires
`cost(a₁₁) = cost(a₄₁)`, which holds uniquely at **c₃₃ = lo + w/3** (= ½ + w/3 once b₃₂ = 0 is
forced). Both corners are eliminated, and ρ is finite and exactly rational everywhere.

*Proof sketch:* `cost(a₁₁) = cost(a₂₁) = 4κ(c₃₃ − lo)` and `cost(a₄₁) = 2κ(hi − c₃₃)`.
Properness sends the probability of a strictly costlier action to a lower order, so any cost
inequality drives `r₄/(r₁+r₂)` to 0 or ∞; via the belief `q = (r₁+r₂)/(r₁+r₂+2r₄)` and P3's
threshold q = 1/5 that pushes c₃₃ to 1 or 0, both outside the window. Cost equality gives
`4(c₃₃−lo) = 2(hi−c₃₃)`. There properness constrains nothing between the equal-cost actions, so
the knife-edge ratio `r₄ = 2(r₁+r₂)` is admissible and P3 is exactly indifferent. The corners
have one cost exactly 0 and the other strictly positive, so the same argument contradicts them. ∎

**Scope caveat.** Properness on the **normal** form, where whole pure strategies are ordered by
expected cost and the behavioural rates r_j inherit that ordering. *Agent*-normal-form properness
compares only actions within one information set and would **not** order a₁₁ against a₄₁ — P1
holding the 1 and P1 holding the 4 are different information sets. [?] whether extensive-form
proper or quasi-perfect selects the same point.

**And it is specific to the minimal game** — see §9.6.

---

# PART 6 — METHOD

1. **Full enumeration.** All 24 deals × 13 histories materialized once as a leaf table of
   (parameter-index list, payoff triple). `u_i(p) = κ Σ_leaves (Π factors) × payoff_i`.
   No sampling, no CFR, no iteration for any exact result.

2. **Multilinearity.** Each u_i is multilinear in the 48 coordinates, hence *affine* along any
   single coordinate. Consequences:
   - `∂u/∂x_i = u(x_i=1) − u(x_i=0)` — exact from two evaluations.
   - central differences are exact to round-off: max |central − exact| = **2.4e-11** at h=1e-5
     over 9,072 × 48 × 3.
   - any `∂u/∂x` is itself affine in every *other* coordinate, so its zeros are **solved for**,
     not searched. This converts "ρ grows near the boundary" into "the pole is *at* the boundary".
   - a ratio of two affine functions is Möbius → poles are simple.

3. **Exact best responses.** u_i decomposes over the card i holds, so BR splits into 4
   independent 4-decision problems: 4 × 2⁴ = 64 exact evaluations. For n ≥ 5, backward induction
   over information sets (linear in tree size).

4. **Grid.** 9,072 valid family points — sub-family A 2,268, B 2,268, C 4,536 — sweeping
   b₁₁, b₂₁, b₂₃, b₃₂, c₁₁, c₃₃, c₃₄ across their full valid ranges, β spanning [0, ¼]. Dense
   1-D sweeps use 201 points. Every point checked against `violations()`.

5. **Rational arithmetic** (`fractions.Fraction`) for all headline claims.

---

# PART 7 — RESULTS ON THE FOUR-CARD FAMILY

## 7.1 The premise correction [G]

At an equilibrium no strictly improving deviation exists, so "exploitation direction" is the
wrong frame. Feasible directions split into **costly** (du_A < 0; ρ well defined) and
**costless** (du_A = 0; ρ has a zero denominator). See Proposition 3 for the full count.

## 7.2 ρ is neither well-defined nor sign-stable [G]

- **19 of 48** coordinates have `du_A ≡ 0` at *every* grid point:
  `a₃₃, a₄₄, b₁₁, b₁₂, b₂₁, b₂₂, b₃₂, b₃₃, b₄₁, b₄₂, b₄₄, c₁₃, c₁₄, c₂₃, c₂₄, c₃₃, c₃₄, c₄₃, c₄₄`
- **21 more** vanish on part of the grid — boundary sub-manifolds.
- Smallest nonzero denominator: **1.0e-4** against κ = 0.0417 — within 0.25 % of zero.
- Observed ρ range: **−50 to +391**.
- **Along-family direction:** `du/dβ = (−κ, 0, +κ)` identically in all three sub-families. With
  A = P2 the denominator is exactly zero while the numerator is κ ≠ 0 — **the paper's headline
  phenomenon is precisely where ρ blows up.**

**Sign behaviour:**

| behaviour | coordinates | detail |
|---|---|---|
| sign **flips** | a₁₁, a₂₁, a₄₁ | ρ(a₁₁) ∈ **[−48.75, +22.0]**; 4,844 pts negative, 906 in (0,1], 1,200 above 1 |
| reaches 0 without flipping | a₃₂, c₃₁ | |
| strictly positive where defined | all P2/P3 costly directions | b₃₁ ≡ 0.600; b₁₄,b₂₄,b₃₄ ≡ 1.0; c₄₁ ≡ 1.0; c₄₂ ≡ 0.75; c₃₁ ∈ [0, 0.5]; c₁₁,c₂₁ ∈ [2, 391] |

## 7.3 Exact closed forms for ρ [E]

| direction | closed form | notes |
|---|---|---|
| `+e_{b₃₁}` | **ρ ≡ 3/5 exactly** | on the *entire* family; hand-derivable (Part 8) |
| `+e_{c₃₁}` | `(2−4s)/(4−5s)`, s = b₁₁+b₂₁ | depends on b₁₁,b₂₁ only via their sum; hits 0 at s = ½ |
| `+e_{a₃₁}` | ∈ [3/11, 2/5] | independent of c₁₁, b₃₂, c₃₃ |

## 7.4 Costless directions exist for everyone — only P2's preserve equilibrium [E,G]

| player | costless coordinates | fraction of grid |
|---|---|---|
| P2 | b₁₁, b₂₁, b₄₁ | 9,072 / 9,072 |
| P3 | c₁₁, c₂₁ | 9,072 / 9,072 |
| P1 | a₁₁, a₂₁, a₂₂, a₃₂, a₄₁ | 7,484 / 9,072 (boundary sub-manifolds only) |

**None of the single-coordinate costless directions preserves equilibrium:**

| direction | du | exploitability after ε=0.01 | after ε=0.05 |
|---|---|---|---|
| P2 `+e_{b₁₁}` | (+1/12, 0, −1/12) | 8.33e-04 | 4.17e-03 |
| P2 `+e_{b₂₁}` | (+1/24, 0, −1/24) | 8.33e-04 | 4.17e-03 |
| P2 `+e_{b₄₁}` | (−1/24, 0, +1/24) | 4.17e-04 | 2.08e-03 |
| P3 `+e_{c₂₁}` | (−0.0333, +0.0333, 0) | 9.17e-04 | 4.58e-03 |
| P3 `+e_{c₁₁}` | (−0.025, +0.0333, −0.0083) | 9.17e-04 | 4.58e-03 |
| P1 `+e_{a₁₁}` at boundary | (0, +0.0255, −0.0255) | 2.71e-03 | 1.35e-02 |
| P1 `+e_{a₂₁}` at boundary | (0, +0.0422, −0.0422) | 1.60e-03 | 8.02e-03 |
| **P2 along-family β** | (−κ, 0, +κ) | **< 5e-16 — stays exactly Nash** | |

*This is the precise sense in which the SGS transfer result is special:* costless directions are
common; costless directions that stay inside the equilibrium set belong to P2 alone.

## 7.5 The pole census, with a witness for every failure mode [E,G]

| deviation | root of du_owner/dx = 0 sits at | max error | round | verdict |
|---|---|---|---|---|
| `+e_{a₁₁}` | `lo = ½ − b₃₂` — Table 3's **lower** bound on c₃₃ | **6.7e-16** | 1 | POLE |
| `+e_{a₂₁}` | the same `lo` (Lemma 5 gives du₁/da₂₁ = du₁/da₁₁ once a₂₂=a₂₃=0) | **6.7e-16** | 1 | POLE |
| `+e_{a₄₁}` | `hi = lo + ¾(b₁₁+b₂₁) + β/4` — Table 3's **upper** bound | **1.2e-15** | 1 | POLE |
| `+e_{a₂₂}` | `c₁₁^max = (2−b₁₁)/(3+2b₁₁+2b₂₁)` | **7.8e-16** | **2** | POLE |
| `+e_{a₃₂}` | `b₂₁ = (1 − 8c₁₁b₁₁)/(4 − 8c₁₁)`; in sub-family A, b₂₁ = ¼ | **2.7e-15** | **2** | POLE |
| `+e_{a₃₁}` | **no root** — no c₃₃ dependence at all, 48/48 cases | — | 1 | fails (i) |
| `b₃₄` | root at b₃₁ = 1, but Table 3 pins b₃₁ = 0 | — | 2 | **fails (ii)** |
| `c₂₂` | root at b₁₁ = b₂₁ = 0 **is** attainable | ρ ≡ 0.800 | 2 | **fails (iii)** |
| `a₁₁, a₂₁` when b₃₂ > ½ | `c₃₃* = ½ − b₃₂ < 0`, outside [0,1] | — | 1 | **fails (ii)** |

**The a₂₂ root verification:**

| b₁₁ | b₂₁ | b₂₃ | root(c₁₁) | c₁₁^max | \|diff\| |
|---|---|---|---|---|---|
| 0.00 | 0.00 | 0 | 0.66666667 | 0.66666667 | 0.0e+00 |
| 0.10 | 0.20 | 0 | 0.52777778 | 0.52777778 | 5.6e-16 |
| 0.25 | 0.25 | 0 | 0.43750000 | 0.43750000 | 5.6e-17 |
| 0.15 | 0.15 | 0 | 0.51388889 | 0.51388889 | 3.3e-16 |
| 0.20 | 0.05 | 0.09 | 0.51428571 | 0.51428571 | 7.8e-16 |
| 0.25 | 0.00 | 0.125 | 0.50000000 | 0.50000000 | 1.1e-16 |

**Full census over all 48 parameters:**

| | round-1 poles | round-2 poles |
|---|---|---|
| **P1** | a₁₁, a₂₁, a₄₁ | a₂₂, a₃₂ |
| **P2** | none | none |
| **P3** | c₁₁, c₂₁ | none |

Neither specific to opening bets, nor to P1. What *is* specific to P1: only P1's pole locations
are set by **off-path** parameters. P3's sit at boundaries in on-path parameters. P2 has no poles
at all — every P2 direction either has du₂ ≡ 0 or a bounded, constant ρ.

## 7.6 The divergence, and the residue [E]

At b₁₁ = b₂₁ = 0.15, b₃₂ = 0.40, c₁₁ = 0.25, c₃₄ = 0.5; c₃₃ interval [0.1000, 0.3625]:

| c₃₃ position | du₁/da₁₁ | ρ(a₁₁) | du₁/da₄₁ | ρ(a₄₁) |
|---|---|---|---|---|
| lo (endpoint) | +0.0000000 | **undefined** | −0.0218750 | +1.38 |
| lo + 1e-4 | −0.0000044 | **−9999.00** | −0.0218728 | +1.38 |
| lo + 1% | −0.0004375 | −99.00 | −0.0216562 | +1.38 |
| midpoint | −0.0218750 | −1.00 | −0.0109375 | +1.76 |
| hi − 1% | −0.0433125 | −0.01 | −0.0002187 | +39.10 |
| hi − 1e-4 | −0.0437456 | −0.00 | −0.0000022 | **+3810.52** |
| hi (endpoint) | −0.0437500 | +0.00 | +0.0000000 | **undefined** |

Each direction is well behaved at the *other's* pole. The pole is not isolated:
`du₁/da₁₁ = du₁/da₂₁ = 0` identically along the whole line `c₃₃ = ½ − b₃₂` (checked at
b₃₂ = 0, 0.15, 0.30, 0.45; exploitability 7.3e-17 throughout) — a codimension-1 surface.

**Exact residues, R = t/D′:**

| dev | D′/κ | c₃₃* | transfer t | R = t/D′ |
|---|---|---|---|---|
| a₁₁ | −4 | +0.1000 | +0.04375000 | **−21/80** |
| a₂₁ | −4 | +0.1000 | +0.04375000 | **−21/80** |
| a₄₁ | +2 | +0.3625 | −0.00833333 | **−1/10** |
| a₁₁ | −4 | +0.5000 | −0.03645833 | **+7/32** |
| a₂₁ | −4 | +0.5000 | −0.01562500 | **+3/32** |
| a₄₁ | +2 | +0.7375 | +0.02083333 | **+1/4** |
| a₁₁ | −4 | +0.2000 | +0.06875000 | **−33/80** |
| a₂₁ | −4 | +0.2000 | +0.04270833 | **−41/160** |
| a₄₁ | +2 | +0.4500 | −0.00416667 | **−1/20** |
| a₄₁ | +2 | +0.0500 | −0.03750000 | **−9/20** |

**Rate confirmation** — ρ·(c₃₃ − c₃₃*) → R, one decade of relative error per decade of offset:

| offset | a₁₁: ρ·Δc | rel. err | a₄₁: ρ·Δc | rel. err |
|---|---|---|---|---|
| 1e-2 | −0.2525000000 | 3.81e-02 | −0.1100000000 | 1.00e-01 |
| 1e-3 | −0.2615000000 | 3.81e-03 | −0.1010000000 | 1.00e-02 |
| 1e-4 | −0.2624000000 | 3.81e-04 | −0.1001000000 | 1.00e-03 |
| 1e-5 | −0.2624900000 | 3.81e-05 | −0.1000100000 | 1.00e-04 |
| 1e-6 | −0.2624990000 | 3.81e-06 | −0.1000010001 | 1.00e-05 |
| 1e-7 | −0.2624999004 | 3.79e-07 | −0.1000001014 | 1.01e-06 |
| 1e-8 | −0.2624999916 | 3.19e-08 | −0.1000000183 | 1.83e-07 |
| 1e-9 | −0.2624999771 | 8.71e-08 | −0.1000001620 | 1.62e-06 |

(The floor near 1e-8 is float cancellation, not a departure from the model.)

## 7.7 Off-path parameters: unconstrained is NOT inert [E]

`b₃₂, c₃₃, c₃₄, c₄₄` have **exactly zero** first derivatives for all three players at all 9,072
points (max |du_i/dx| = **0.000e+00**), and `c₃₄, c₄₄` have exploitability 7.3e-17 for *every*
value in [0,1] — nobody's incentive constrains them.

But the **mixed second derivatives** are not zero:

| x | ∂²u/(∂a₁₁∂x) | ∂²u/(∂a₂₁∂x) | via a₃₁ | via a₄₁ |
|---|---|---|---|---|
| `c₃₄` | (0, +κ, −κ) | (0, +κ, −κ) | 0 | 0 |
| `c₄₄` | (0, −2κ, +2κ) | (0, −2κ, +2κ) | 0 | 0 |
| `c₃₃` | (−4κ, 0, +4κ) | (−4κ, 0, +4κ) | 0 | (+2κ, 0, −2κ) |
| `b₃₂` | (−4κ, +3κ, +κ) | (−4κ, +3κ, +κ) | 0 | (+2κ, −2κ, 0) |

`c₄₄` requires b₃₂ > 0 to be reachable at all:

| b₃₂ | reach(c₄₄) after a₁₁ = 0.5 | ∂²u₃/(∂a₁₁∂c₄₄) |
|---|---|---|
| 0.00 | 0 | 0 |
| 0.10 | 0.00208333 | +0.020833 |
| 0.40 | 0.00833333 | +0.083333 |

Reach after a single P1 deviation (a_j1 = 0.5), at b₃₂ = 0.40:

| P1 opens with | reach(c₃₄) | reach(c₄₄) |
|---|---|---|
| card 1 | 0.020833 | 0.008333 |
| card 2 | 0.020833 | 0.008333 |
| card 3 | 0 | 0 |
| card 4 | 0 | 0 |

**Two independent sources of indeterminacy in ρ:**
- **denominator** ← b₃₂, c₃₃ — constrained, but by an *inequality* whose boundary is attainable
  → a **pole** on the edge of the equilibrium set.
- **numerator** ← c₃₄, c₄₄ — constrained by nobody at all → ρ's *value* is undetermined even
  where the denominator is safely away from zero.

## 7.8 The refinement ladder [E]

| rung | pins | evidence | what survives |
|---|---|---|---|
| **Nash** | nothing off-path | first derivatives exactly 0.00e+00 | ρ undefined or unbounded, sign ambiguous |
| **Dominance** | c₃₄ = 0, c₄₄ = 1 | advantage **−1.000000** / **+5.000000** under *every* tremble ratio tested | numerator still partly free |
| **Sequential rationality** | b₃₂ = 0 at the knife-edge | b₃₂ advantage **−0.1667**; off it, c₃₃ → 1 gives exploitability **5.3e-02** | sign fixed: ρ(a₁₁) ∈ [1.395, 45.42], **no flip** |
| **Properness** | **c₃₃ = lo + w/3** | costs equal in exact rationals | ρ finite and exactly rational |

**The belief computation.** At P3's BF/card-3 set the pot is 4; folding costs 1, calling risks 2
to win 3. Calling beats folding iff `3q − 2(1−q) > −1`, i.e. **q > 1/5**, where
`q = P(P1 holds 1 or 2 | P1 bet, P2 folded, P3 holds the 3)`. From the tree,
`q = (r₁+r₂)/(r₁+r₂+2r₄)`. Indifference iff **r₄ = 2(r₁+r₂)**.

| r₄ | q | c₃₃ advantage | b₃₂ advantage | c₃₃ admissible? | b₃₂ admissible? |
|---|---|---|---|---|---|
| 0.5 | 0.66667 | +2.333333 | +1.000000 | no | no (→1, outside) |
| 1 (uniform) | 0.50000 | +1.500000 | +0.666667 | no | no (→1, outside) |
| 2 | 0.33333 | +0.666667 | +0.250000 | no | no (→1, outside) |
| 3 | 0.25000 | +0.250000 | −0.000000 | no | yes (mix) |
| **4** | **0.20000** | **+0.000000** | **−0.166667** | **yes (mix)** | **yes (→0)** |
| 5 | 0.16667 | −0.166667 | −0.285714 | no | yes (→0) |
| 8 | 0.11111 | −0.444444 | −0.500000 | no | yes (→0) |
| 12 | 0.07692 | −0.615385 | −0.642857 | no | yes (→0) |
| 20 | 0.04762 | −0.761905 | −0.772727 | no | yes (→0) |

Exactly one ratio works, and there b₃₂ = 0 is forced. The knife-edge holds across the family
(5 points spanning all three sub-families, all indifferent to ≤ 1.8e-13).

**Properness cost equality at c₃₃ = lo + w/3, exact rationals:**

| point | c₃₃* | cost a₁₁ | cost a₂₁ | cost a₄₁ | equal? | cost a₃₁ | a₃₁ costliest? |
|---|---|---|---|---|---|---|---|
| B, b₃₂=2/5 | 3/16 | 7/480 | 7/480 | 7/480 | ✓ | 73/960 | ✓ |
| B, refined face | 47/80 | 7/480 | 7/480 | 7/480 | ✓ | 73/960 | ✓ |
| A, refined face | 71/120 | 11/720 | 11/720 | 11/720 | ✓ | 7/96 | ✓ |
| A, corner β=¼ | 31/48 | 7/288 | 7/288 | 7/288 | ✓ | 11/192 | ✓ |
| C, refined face | 139/240 | 19/1440 | 19/1440 | 19/1440 | ✓ | 73/960 | ✓ |
| C, b₂₃ at max | 7/12 | 1/72 | 1/72 | 1/72 | ✓ | 7/96 | ✓ |

**Corner exclusion:**

| point | at c₃₃ = lo | at c₃₃ = hi |
|---|---|---|
| B, b₃₂=2/5 | cost a₁₁ = 0, cost a₄₁ = 7/320 → a₄₁ strictly worse | 7/160 vs 0 → a₁₁ strictly worse |
| A, refined face | 0 vs 11/480 | 11/240 vs 0 |
| A, corner β=¼ | 0 vs 7/192 | 7/96 vs 0 |

**The selected ρ — every value finite and exactly rational:**

| point | w | ρ(a₁₁) | ρ(a₂₁) | ρ(a₄₁) |
|---|---|---|---|---|
| B, b₃₂=2/5 | 21/80 | **−4/7** | −4/7 | **11/7** |
| B, refined face | 21/80 | **20/7** | 20/7 | **−5/7** |
| A, refined face | 11/40 | **73/22** | 49/22 | **−7/11** |
| A, corner β=¼ | 7/16 | **5/2** | 29/14 | **−5/7** |
| C, refined face | 19/80 | **83/38** | 143/38 | **−11/19** |
| C, b₂₃ at max | 1/4 | **7/4** | 29/8 | **−1/2** |

**Refined face (b₃₂ = 0, c₃₄ = 0):** the c₃₃ window becomes [½, b₃₂max]; both poles survive.

| b₁₁ | b₂₁ | refined c₃₃ interval | width | a₁₁ lower edge | a₄₁ upper edge |
|---|---|---|---|---|---|
| 0.15 | 0.15 | [0.5000, 0.7625] | 0.2625 | **POLE** | **POLE** |
| 0.10 | 0.20 | [0.5000, 0.7750] | 0.2750 | **POLE** | **POLE** |
| 0.25 | 0.25 | [0.5000, 0.9375] | 0.4375 | **POLE** | **POLE** |
| 0.20 | 0.05 | [0.5000, 0.7375] | 0.2375 | **POLE** | **POLE** |
| 0.00 | 0.00 | [0.5000, 0.5000] | 0 (degenerate) | POLE | none |

Refined face stays exactly Nash (max exploitability 2.2e-16). With b₃₂ = 0, reach(c₄₄) = 0 even
after a P1 deviation — **c₄₄ becomes genuinely inert**. On the refined face
ρ(a₁₁) ∈ [1.395, 45.42] over 250 sampled points, strictly positive, **no sign flip**.

## 7.9 Two-player control [E,G]

Independent 30-leaf engine (3 cards, 6 deals), standard one-parameter family α ∈ [0, 1/3].

**Family verified first:** max exploitability **1.9e-16** over 201 α; `u₁ = −1/18` exactly
(rational check at α = 1/6 gives (−1/18, +1/18)); α = −0.02 → exploitability 0.020 and
α = ⅓+0.02 → 0.010, so the interval is exactly right.

**Reason 1 — no third party.** Over 201 α × every feasible coordinate direction:

```
strictly costly (du_A < 0)         : 1403
du_A = 0 AND opponent moves        :    0   <- costless transfers
du_A = 0 and nothing moves (null)  : 2011
max |du_1 + du_2|                  : 0.000e+00
```

Every free-parameter direction is exactly (0, 0):

| α | x₁₁ | x₃₁ | x₂₂ |
|---|---|---|---|
| 0.0000 | (+0.00000, +0.00000) | (−0.00000, +0.00000) | (+0.00000, +0.00000) |
| 0.1667 | (+0.00000, +0.00000) | (−0.00000, +0.00000) | (−0.00000, +0.00000) |
| 0.3333 | (+0.00000, +0.00000) | (−0.00000, +0.00000) | (+0.00000, +0.00000) |

against three-player `du/db₁₁ = (+1/12, 0, −1/12)`, `du/db₂₁ = (+1/24, 0, −1/24)`,
`du/db₄₁ = (−1/24, 0, +1/24)`. ρ is **identically 1** over all 1,403 defined pairs — range
[1.000000000000000, 1.000000000000000] — even with |du_A| down to 8.3e-4.

**Reason 2 — no slack either.** Off-path region exists only at the single endpoint α = 0, and
those coordinates are pinned to a **point**:

| parameter | zero-exploitability set | width |
|---|---|---|
| 2p `y₁₂` (family value 0) | [0.000000, 0.000000] | **0 — no slack** |
| 2p `y₂₂` (family value 1/3) | [0.333333, 0.333333] | **0 — no slack** |
| 2p `y₃₂` (family value 1) | [1.000000, 1.000000] | **0 — no slack** |
| 3p `c₃₃` at b₁₁=b₂₁=0.15, b₃₂=0.40 | [0.1000, 0.3625] | **0.2625 — slack** |

Reach across the 2-player family:

| param | reach @α=0 | reach @α=1/3 |
|---|---|---|
| x₁₁ | 0.333333 | 0.333333 |
| x₁₂ | 0.166667 | 0.111111 |
| x₃₂ | 0.055556 | 0.000000 |
| y₁₂ | **0.000000** | 0.166667 |
| y₂₂ | **0.000000** | 0.222222 |
| y₃₂ | **0.000000** | 0.055556 |

**Interchangeability contrast:** 2-player u₁ = −1/18 for every α, spread **2.4e-16**.
3-player u₁ ∈ [−0.03125, −0.02083] and u₃ ∈ [0.04167, 0.05208], spread **κ/4 each**, while
u₂ is pinned at −κ/2 (spread 2.8e-16).

## 7.10 The one genuinely improving direction — SGS Table 4 [E]

Table 4 deliberately mixes sub-families (P2 from c₁₁=½, P3 from c₁₁=0) and is not an
equilibrium. P2's exact exploitability there is **0.0104167 = κβ**, matching the paper.

Improving direction `−e_{b₂₃}`:
```
du₁/dε = 0    du₂/dε = +0.083333 = 2κ    du₃/dε = −0.083333
ρ_{P2→P1} = 0.0000    ρ_{P2→P3} = 1.0000
```
P2's entire gain comes out of P3; P1 is untouched. Magnitudes tie out: 2κ × (1/8) = κ/4 = κβ.

## 7.11 Seat asymmetry on the four-card family

| β | u₁ | u₂ | u₃ |
|---|---|---|---|
| 0 | −0.0208 | −0.0208 | +0.0417 |
| ¼ | **−0.0313** | −0.0208 | **+0.0521** |

P1's positional penalty ranges over **[κ/2, 3κ/4]** = [0.0208, 0.0313] — and which value obtains
is set by β, a choice **P2** makes that costs P2 exactly nothing. Seat 1's handicap is 50 %
larger or smaller depending on a free decision by a player who is unaffected either way.

---

# PART 8 — THE HAND-REPRODUCIBLE WORKED EXAMPLE

**Grid point.** Sub-family A, b₁₁ = b₂₁ = 0 (β = 0), b₂₃ = 0, b₃₂ = 0, c₃₃ = ½, c₃₄ = 0.
P1 and P2 never bet; P3 bets the 4 always and the 2 half the time after two checks. Facing P3's
bet, P1 calls only with the 4 (a₄₂ = 1); if P1 folds, P2 calls with the 4 always and the 3 half
the time (b₃₃ = ½). Utilities **(−1/48, −1/48, +1/24)** = (−κ(½+0), −κ/2, κ(1+0)).

**Deviation.** A = P2, `d = +e_{b₃₁}`: P2 starts betting the 3 after P1 checks. Only the **6
deals where P2 holds the 3** are affected.

| deal (P1,P2,P3) | P2 **bets** | P2 **checks** | difference |
|---|---|---|---|
| (1,3,2) | (−1, 2, −1) | (−1, 3/2, −1/2) | (0, +1/2, −1/2) |
| (1,3,4) | (−1, −2, 3) | (−1, −3/2, 5/2) | (0, −1/2, +1/2) |
| (2,3,1) | (−1, 2, −1) | (−1, 2, −1) | (0, 0, 0) |
| (2,3,4) | (−1, −2, 3) | (−1, −3/2, 5/2) | (0, −1/2, +1/2) |
| (4,3,1) | (+3, −2, −1) | (+2, −1, −1) | (+1, −1, 0) |
| (4,3,2) | (+3, −2, −1) | (+5/2, −1, −3/2) | (+1/2, −1, +1/2) |
| **sum** | | | **(+3/2, −5/2, +1)** |

Multiply by κ = 1/24: `du = (+1/16, −5/48, +1/24)`. Constant-sum check:
`3/48 − 5/48 + 2/48 = 0` ✓. With A = P2 and C = P1:

> **ρ = −(1/16)/(−5/48) = 3/5**, complement 2/5.

Engine agrees to **2.7e-12** by both central difference and exact derivative.

**Why it is 3/5 everywhere.** Carrying the same six deals with b₃₃, c₁₁, c₂₁ symbolic:
```
du₁ = (1/24) [ (1 − c₁₁) + (1 − c₂₁) ]  = (1/24)(2 − (c₁₁+c₂₁))
du₂ = (1/24) [ (c₁₁+c₂₁)(3 − 4b₃₃) + 2b₃₃ − 4 ]
```
Table 3 sets `c₂₁ = ½ − c₁₁`, so `c₁₁ + c₂₁ = ½` identically and both collapse to
`du₁ = (3/2)/24`, `du₂ = (−5/2)/24` — **independent of b₁₁, b₂₁, b₂₃, b₃₃, c₁₁, b₃₂, c₃₃, c₃₄**.
Hence ρ ≡ 3/5 on the whole family. Verified with b₃₃ over [0.5, 0.875] and c₁₁ over [0, 0.5];
breaking `c₁₁ + c₂₁ = ½` (e.g. c₁₁=0.20, c₂₁=0.10) gives du₁ = +0.0708, du₂ = −0.1050 and
destroys the constancy.

**Contrast at the same point.** `+e_{b₁₁}` gives (+1/12, 0, −1/12): P2 pays nothing, P1 gains
1/12, P3 loses 1/12, and ρ = −(1/12)/0 is undefined. Same grid point, same player, one direction
with a clean rational share and one with no share at all.

---

# PART 9 — GENERALIZATION: n PLAYERS, N CARDS

## 9.1 The complete (n,N) grid — 122 MCCFR runs [G]

| n | N | N=n+1 | seeds | median expl | **P1 max opening** | off-path | rank | pairs | attainable | **POLES** | seeds w/pole | % roots in [0,1] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 4 | **YES** | 20 | 0.00157 | **0.011** | 6 | 1 | 251 | 175 | **175** | 18/20 | **70%** |
| 3 | 5 | no | 20 | 0.00348 | 0.828 | 2 | 1 | 40 | 0 | **0** | 0/20 | **0%** |
| 4 | 5 | **YES** | 20 | 0.00264 | **0.010** | 34 | 2 | 756 | 468 | **468** | 20/20 | **62%** |
| 4 | 6 | no | 20 | 0.00284 | 0.850 | 14 | 2 | 288 | 22 | 22 | 15/20 | 8% |
| 5 | 6 | **YES** | 20 | 0.00313 | **0.024** | 94 | 3 | 393 | 213 | **213** | 15/20 | **54%** |
| 5 | 7 | no | 8 | 0.00448 | 0.826 | 52 | 3 | 350 | 2 | 2 | 2/8 | 1% |
| 6 | 7 | **YES** | 8 | 0.00365 | **0.014** | 420 | 4 | 103 | 44 | **44** | 7/8 | **43%** |
| 6 | 8 | no | 6 | 0.00457 | 0.764 | 130 | 4 | 107 | 1 | 1 | 1/6 | 1% |

> **The separation on P1's opening probability has NO overlap:**
> **0.010 – 0.024 when N = n+1**, versus **0.764 – 0.850 when N > n+1**, across four values of n.

**Honest nuance:** N > n+1 is not *exactly* pole-free. (3,5) is a clean 0/20, but (4,6), (5,7)
and (6,8) leak a few. The claim is a sharp quantitative separation, not an absolute dichotomy.

**Root distributions:**

| n,N | roots | min | median | max | % inside [0,1] |
|---|---|---|---|---|---|
| 3,4 | 251 | −11.604 | 0.718 | 55.477 | 70% |
| 3,5 | 40 | 1.218 | 1.572 | 2.778 | 0% |
| 4,5 | 756 | −116.489 | 0.610 | 1409.874 | 62% |
| 4,6 | 288 | −306.199 | 2.126 | 7071.596 | 8% |
| 5,6 | 393 | −116.861 | 0.526 | 29.931 | 54% |
| 5,7 | 350 | −19496.747 | 9.165 | 7027969.173 | 1% |

## 9.2 Seat utilities across all eight configurations [G]

| n, N | seat utilities (mean over seeds) |
|---|---|
| 3, 4 | P1 −0.02832, P2 −0.02021, **P3 +0.04853** |
| 3, 5 | P1 −0.03509, P2 −0.00145, **P3 +0.03653** |
| 4, 5 | P1 −0.01406, P2 −0.01397, P3 −0.00840, **P4 +0.03643** |
| 4, 6 | P1 −0.03184, P2 −0.01022, P3 +0.00769, **P4 +0.03437** |
| 5, 6 | P1 −0.00908, P2 −0.00907, P3 −0.00770, P4 −0.00388, **P5 +0.02973** |
| 5, 7 | P1 −0.02954, P2 −0.01483, P3 −0.00095, P4 +0.01254, **P5 +0.03278** |
| 6, 7 | P1 −0.00604, P2 −0.00619, P3 −0.00619, P4 −0.00494, P5 −0.00181, **P6 +0.02517** |
| 6, 8 | P1 −0.02681, P2 −0.01579, P3 −0.00658, P4 +0.00343, P5 +0.01480, **P6 +0.03096** |

First player worst and last player best in **all eight**. The minimal deck *compresses* the
spread (n=5,N=6: −0.009 → +0.030) while an extra card widens it (n=5,N=7: −0.030 → +0.033).

## 9.3 Adding cards kills it — the 50-seed detail at N=5 [G]

| | N = 4 (10 seeds) | N = 5 (50 seeds) |
|---|---|---|
| median exploitability | 0.00105 | 0.00342 |
| off-path sets | vary by seed | **`b5_3, b5_4` in 50/50** |
| (x,y) pairs where x moves an incentive | 111 | 100 |
| root attainable in [0,1] | 86 | **0** |
| genuine poles | **86** | **0** |
| root range | median 0.78 | **1.216 – 2.966** |

Closest any root comes to the admissible interval at N=5: **0.216 outside**. Clause (ii) fails
uniformly in all 50 independent approximate equilibria.

**Why.** At N=4 P1 never bets, sending P2's and P3's bet-response sets off-path family-wide.
From N=5 on P1 value-bets the top card ~80 % (0.825, 0.799 at N=5, 6), so those sets are reached
(reach 5.8e-2, 4.7e-2, 1.1e-2 at N=5). The only surviving off-path sets are `b_N_3, b_N_4` —
P2 self-excluding by always betting the top card — and P2 strictly prefers that bet at *every*
admissible value: `du₂/db5_1` runs +0.154 → +0.033, floor ≈ 2κ. The root sits at
**b5_3 = 1.270**, outside [0,1]. Mixed second derivative confirming b5_3 does move the incentive:
`∂²u/(∂b5_1 ∂b5_3) = (0, −0.1214, +0.1214)`.

## 9.4 Adding players restores it — the 24-seed detail at (4,5) [G]

| | value |
|---|---|
| median exploitability | 0.00257 (max 0.00367) |
| off-path sets per seed | median **39** |
| (x,y) pairs where x moves an incentive | 978 |
| root attainable in [0,1] | **619** |
| genuine poles | **619** |
| seeds with ≥1 pole | **24 / 24** |
| pole roots | 0.036 – 0.9997, median **0.639** |
| numerators | min 1.7e-4, median 0.0207 |
| affine rank of share set | **2 in 24/24 seeds** |

Most common pole pairs: `x = b5[B]` and `x = c5[BF]` (opponents' responses to a bet by P1)
driving `y = a1[-] … a4[-]` (P1's own opening) — **structurally identical to the (3,4)
mechanism.**

## 9.5 The mechanism chain

### 9.5.1 The incentive flips sign at the threshold [G]

| n, N | N=n+1 | P1 opens TOP card | P(someone bets \| P1 checks) | **du₁/d(open top)** |
|---|---|---|---|---|
| 3, 4 | **YES** | 0.0154 | 0.5114 | **−0.00902** |
| 3, 5 | no | 0.8306 | 0.5841 | **+0.00099** |
| 4, 5 | **YES** | 0.0169 | 0.4514 | **−0.01022** |
| 4, 6 | no | 0.8390 | 0.6531 | **+0.00120** |
| 5, 6 | **YES** | 0.0237 | 0.4424 | **−0.00711** |
| 5, 7 | no | 0.8308 | 0.7009 | **+0.00208** |

### 9.5.2 The exact decomposition [P,E]

Holding the best card P1 never loses a showdown and never folds, so P1's payoff on those deals
is exactly the sum of the **opponents'** contributions. Hence

> **du₁/d(open top) = Σⱼ Δⱼ**, where
> **Δⱼ = P(j puts in a 2nd chip | P1 bets) − P(j puts in a 2nd chip | P1 checks)**

*Verified exact* to **2.6e-17 / 4.0e-18 / 7.5e-17** at (3,4)/(4,5)/(5,6) once P1 is forced never
to fold the nuts. On raw CFR output it holds to 5.6e-05, the gap being CFR's residual folding at
a barely-reached set.

**Per-opponent:**

| n, N | N=n+1 | Δ P2 | Δ P3 | Δ P4 | Δ P5 |
|---|---|---|---|---|---|
| 3, 4 | YES | −0.01008 | +0.00106 | | |
| 3, 5 | no | −0.01135 | +0.01234 | | |
| 4, 5 | YES | +0.00068 | +0.00126 | −0.01217 | |
| 4, 6 | no | −0.01489 | +0.00931 | +0.00677 | |
| 5, 6 | YES | +0.00233 | +0.00901 | −0.00461 | −0.01385 |
| 5, 7 | no | −0.00942 | −0.00317 | +0.01113 | +0.00353 |

**By role, and split into halves:**

| n,N | N=n+1 | next player Δ | **all later Δ** | later: if P1 BETS | later: if P1 CHECKS |
|---|---|---|---|---|---|
| 3,4 | YES | −0.01008 | **+0.00106** | **0.04162** | 0.04055 |
| 4,5 | YES | +0.00068 | **−0.01090** | **0.03322** | 0.04412 |
| 5,6 | YES | +0.00233 | **−0.00944** | **0.02816** | 0.03760 |
| 3,5 | no | −0.01135 | **+0.01234** | **0.06178** | 0.04944 |
| 4,6 | no | −0.01489 | **+0.01608** | **0.06590** | 0.04982 |
| 5,7 | no | −0.00942 | **+0.01149** | **0.05846** | 0.04697 |

**The later-players term separates with no overlap** — [−0.0109, +0.0011] at N = n+1 versus
[+0.0115, +0.0161] otherwise — and it carries the total. The **check** column is flat across all
six (0.038–0.049) while the **bet** column nearly doubles. So the whole effect is opponents'
**calling rate against a bet**, not their betting into a check.

### 9.5.3 The resolution: a fixed point, not a one-way cause [E]

Defining every strategy by card **rank** so the identical strategy instantiates at any deck
size, and holding P1's range fixed and polarised, an opponent's best-response call fraction is:

| n | N=n+1 | n+2 | n+3 | n+4 | n+5 |
|---|---|---|---|---|---|
| 3 | 0.2500 | 0.2000 | 0.1667 | 0.2857 | 0.2500 |
| 4 | 0.2000 | 0.1667 | 0.2857 | 0.2500 | 0.2222 |

**Flat** — no trend, no separation at N = n+1. Robust across 9 reference settings (bluff rate
0.15/0.33/0.60 × call breadth 0.3/0.5/0.7): slopes in N run **−0.031 to +0.071**, mixed sign,
spreads 0.107–0.607. Against an *equilibrium* call rate that jumps 2–3× at exactly that boundary
(0.049–0.105 at N=n+1 versus 0.143–0.241 otherwise).

Reach of the bet-response sets (near-tautological but recorded):

| n,N | N=n+1 | reach of bet-response sets | equilibrium call rate | myopic BR | gap |
|---|---|---|---|---|---|
| 3,4 | YES | **0.0108** | 0.1046 | 0.0020 | +0.1026 |
| 4,5 | YES | **0.0161** | 0.0607 | 0.0024 | +0.0583 |
| 5,6 | YES | **0.0235** | 0.0487 | 0.0023 | +0.0465 |
| 3,5 | no | **0.4716** | 0.2413 | 0.0646 | +0.1767 |
| 4,6 | no | **0.6057** | 0.1770 | 0.0543 | +0.1228 |
| 5,7 | no | **0.6998** | 0.1427 | 0.0471 | +0.0956 |

> **Conclusion.** Deck size does not shift any single best-response function; it selects which
> pair of behaviours is simultaneously consistent:
> **P1 silent ↔ bet-response sets off-path ↔ calling constrained only by deterrence.**
> Each half holds because the other does. Three attempts to find a one-way cause failed because
> the structure is a simultaneity.

## 9.6 Properness is specific to the minimal game [E]

Dimension test: **d_free** = off-path coordinates with a non-degenerate deterrence window, after
discarding dominance-pinned and inert ones; **d_cond** = rank of the Jacobian of the deviating
player's cost-differences with respect to those coordinates.

**Control on exact SGS profiles** (three family points, both sub-families, both b₃₂ values):
**d_free = 2, d_cond = 2 → at most one point.** Reproduces the known (3,4) result.

**At (4,5), on 12 CERTIFIED exact equilibria:**

| off-path | with slack | inert | dominance-pinned | **d_free** | d_cond |
|---|---|---|---|---|---|
| 113 | 53 | 36 | 17 | **0** | 0 |

36 + 17 = 53 exactly — every slack off-path coordinate is either inert or pinned by belief-free
dominance, leaving **nothing for properness to pin**. Survives **40 random tremble ratios
spanning three orders of magnitude**.

> **Theorem 3 describes the special case, not the general one.** At (3,4) properness is needed
> because c₃₃ has slack that dominance does not reach. At (4,5) a weaker refinement suffices.

This **corrects** an earlier indicative reading (d_free = d_cond = 4 at (4,5)), which was an
artifact of running the test on approximate equilibria where the windows collapse.

## 9.7 MCCFR does not select the proper equilibrium [E,G]

150 seeds × 10⁶ iterations, 660 s on 27 workers.

| question | answer |
|---|---|
| exploitability reached | median **0.001503**, mean 0.001703, range [0.000467, 0.005465] — 3.6 % of κ |
| per player (mean) | P1 0.000827, P2 0.001077, P3 0.001428 |
| outputs in sub-family A / B / C | 29 / 11 / 11 — **99 of 150 in NONE** |
| dominant failure | 109 seeds have intermediate c₁₁, which requires b₂₁ = b₁₁ exactly; median \|b₂₁−b₁₁\| = **0.111** |
| max-norm distance to nearest family profile | median 0.038, max 0.286 |
| β distribution | mean **0.1687**, sd 0.0499, range [0.0545, 0.2734] — **never near 0**; 9 seeds above the valid ceiling |
| implied per-seat bias | hands P3 ≈ **0.0070 chips** at P1's expense vs the β=0 member |
| c₃₃ position in window (1/3 = properness point) | mean 0.4845, sd 0.2739; best quartile 0.4125, sd 0.2350 |
| correlation of that position with exploitability / reach / β | **+0.076 / −0.000 / −0.050** — it is noise |
| reproduces dominance prediction c₃₄ → 0 | **139 / 150** (median 0.0002) |
| reproduces tremble prediction b₃₂ → 0 | **41 / 150** (median 0.072) |
| reach of off-path sets in CFR output (median) | b₃₂ 1.4e-3, c₃₃ 1.2e-3, c₃₄ 2.0e-4, c₄₄ 9.5e-6 |

Pinned parameters do come out right: c₄₁ = 1.0000 exactly, a₃₃ = 0.5054 ± 0.0095,
a₁₁/a₂₁/a₃₁ ≈ 0 (max dev 0.0108), a₄₁ 0.0109 ± 0.0076.

> **MCCFR reproduces the refinement predictions that follow from belief-free dominance, and not
> those requiring a particular tremble structure.** The off-path sets carry reach ~10⁻³, so the
> solver gets almost no training signal exactly where the indeterminacy lives.

---

# PART 10 — EXACT CERTIFICATION AND THE COMPLETENESS QUESTION

## 10.1 Independent dominance verification [E]

Conditional dominance measured as the per-unit-reach advantage `du_owner/dx ÷ reach(x)`, with
other coordinates confined to [ε, 1−ε] so every set stays reached. (Without the reach
normalisation, unreachable sets give du/dx = 0 exactly and **nothing** ever appears dominated —
a first attempt returned 0/48 for exactly this reason.)

| verdict | count | coordinates |
|---|---|---|
| always worse → fix 0 | 12 | a₁₂ a₁₃ a₁₄ a₂₄ b₁₂ b₁₃ b₁₄ b₂₄ c₁₂ c₁₃ c₁₄ c₂₄ |
| always better → fix 1 | 10 | a₄₂ a₄₃ a₄₄ b₄₂ b₄₃ b₄₄ **c₄₁** c₄₂ c₄₃ c₄₄ |
| genuinely free | 26 | a₁₁ a₂₁ a₂₂ a₂₃ a₃₁ a₃₂ a₃₃ a₃₄ a₄₁ b₁₁ b₂₁ b₂₂ b₂₃ b₃₁ b₃₂ b₃₃ b₃₄ b₄₁ c₁₁ c₂₁ c₂₂ c₂₃ c₃₁ c₃₂ c₃₃ c₃₄ |

> **All 21 of Table 2's values are confirmed: 21 / 21.** Independent verification of the paper.
> **And one more:** `c₄₁ = 1` is also dominance-forced, though the paper places it in Table 3
> (the family) rather than Table 2 (necessary conditions). A small strengthening.

**Iterated dominance adds nothing** — a fixed point is reached in one round. Space:
3⁴⁸ = 7.98e22 → **3²⁶ = 2.54e12**.

## 10.2 Newton on the indifference system [E]

At an equilibrium every strictly interior coordinate leaves its owner indifferent:
`F_i(p) = du_owner/dp_i = 0`. Multilinearity makes the Jacobian
`J_ij = ∂²u_owner/(∂p_i ∂p_j)` exact from two gradient evaluations per column. Damped
pseudo-inverse Newton (rcond 1e-6, strict-improvement line search).

**The formulation is right:** on the exact SGS profile, **max|F| = 2.8e-17**.

**The solver is right:**

| noise added to the true profile | exploitability | max\|F\| |
|---|---|---|
| 1e-3 | 1.6e-04 → **1.9e-16** | 2.8e-04 → 4.2e-17 |
| 1e-2 | 4.7e-03 → **1.9e-16** | 4.2e-03 → 1.4e-17 |
| 3e-2 | 1.5e-02 → **1.8e-16** | 7.4e-03 → 4.2e-17 |

(Coordinate error stays at noise level: it converges to a *different* point of the same
positive-dimensional component, still an exact equilibrium.)

## 10.3 Support enumeration at (3,4) — 40 exact equilibria [E]

An 8-million-iteration MCCFR run shrinks the ambiguous coordinate set from 16 to **12**; Newton
over all 2¹² = 4,096 support hypotheses certifies **40 exact equilibria** (exploitability to
**3.5e-17**) in 98 s.

| certified | in SGS family | deviating in any coordinate | deviating in an **on-path** coordinate |
|---|---|---|---|
| **40 / 4096** | **40** | 13 | **0** |

Every deviation is in `c₂₃` alone — off-path, reach 1e-29 to exactly 0, where Table 2 assigns a
value that cannot matter. All 40 match the family's closed-form utilities to **2.43e-16**.

**A retracted claim.** An earlier pass flagged one case as deviating in on-path `b₄₁`
(reach 0.25). That was a bug in the checker: it rounded the free parameters to six decimals
before rebuilding, so `b₄₁ = 2(b₁₁+b₂₁)` came out ~4e-6 off and tripped a 1e-6 threshold.
Unrounded it matches Table 3 to **1.11e-16**.

## 10.4 Certification ported to (4,5) [E]

43 ambiguous coordinates — 2⁴³ hypotheses — so exhaustive enumeration is impossible. Visiting
hypotheses in order of **Hamming distance from the CFR reading** certifies **29 exact
equilibria** (best **1.86e-16**), all within distance 1–2, in 782 s. CFR at 4M iterations reached
exploitability [0.00087, 0.00059, 0.00087, 0.00172].

## 10.5 Four attempts on "are there equilibria outside the family?" — ALL INCONCLUSIVE

**Note on method.** Lemke–Howson / LCP does **not** apply here: it is specific to two-player
games. With n ≥ 3 the complementarity conditions are polynomial rather than linear, so pruned
support enumeration is the appropriate tool.

### Attempt 1 — broad random-restart Newton. FAILED, uninformative. [X]
50,400 restarts from random 0/1/interior support patterns (half forcing P1's opening interior)
found **zero** exact equilibria — including **zero family members**, which is the tell.
Diagnosis: with the correct support and random starting values Newton recovers an equilibrium
**5 times in 20**; with random supports it hits **0 in 2,000**. The support space is the
obstacle, not the solver.

### Attempt 2 — is P1's bet dominated? No. [E]
Maximising `du₁/da_j1` over *all* opponent strategies (coordinate ascent, 400 restarts):

| P1 bets card | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| max gain | **+0.99989** | **+1.16611** | **+1.20565** | **+1.24959** |

Against loose enough opponents P1 gains up to **30× κ** by betting. The family's `a_j1 = 0` is
**not** forced by dominance, so an equilibrium with P1 betting is not ruled out.

### Attempt 3 — CFR from a pro-betting start. Returns to silence. [G]
Initialising P1's opening regrets at +5000:

| iterations | P1 max opening | exploitability |
|---|---|---|
| 400 k | 0.576 | 0.0406 |
| 2 M | 0.148 | 0.0079 |
| 8 M | **0.039** | **0.0020** |

The early rows are under-convergence, not a discovery — exploitability 0.04 is about κ. Given
enough iterations the profile returns to P1-silent even from an adversarial start.

### Attempt 4 — pruned support enumeration. Coverage far too low. [X]
Pruning applied: iterated dominance (48 → 26 free), branch on P1's opening pattern (81
branches), reachability inside each branch. Surviving space **1.089e12**.

| P1 pattern | reachable free coords | 3^k |
|---|---|---|
| (0,0,0,0) — silent | 17 | 1.291e+08 |
| (1,1,1,1) | 5 | 2.430e+02 |
| (0,0,0,½) — worst | 22 | 3.138e+10 |

Result: **320,243 hypotheses tested = 2.94e-07 of the space; 0 equilibria found** — including 0
in the P1-silent branch where 40 are known to exist. Random sampling of support patterns cannot
work at this scale.

> **VERDICT.** No equilibrium outside the family found; **no proof of completeness.** The
> evidence corroborates SGS — 40 certified equilibria all inside, CFR returning to the family
> from a hostile start — but the systematic search was local and P1's bet is not dominated.
> **What is actually needed: branch-and-bound with partial-feasibility pruning**, cutting
> infeasible subtrees without testing every leaf. That is a different algorithm from anything
> built here.
>
> **It was subsequently built — see PART 15.** Everything in this Part 10.5 stands as written;
> Part 15 supersedes its verdict.

---

# PART 11 — HYPOTHESES TESTED AND REFUTED

Eight claims that looked right and were not. Each was caught by a control.

| # | claim | why it looked right | what killed it |
|---|---|---|---|
| 1 | **P1 slow-plays the nuts** because someone is likely to bet behind | explains silence at N=n+1 intuitively | Predicts P(someone bets) *higher* at N=n+1. It is *lower* — 0.44–0.51 vs 0.58–0.70 — and correlates **+0.91 the wrong way** |
| 2 | **Information sharpness** explains the calling difference | minimal deck → your card pins your rank | Sharpness is **identical (0.1667)** at (3,4) and (3,5), which have opposite Δ. Fails on the first pair |
| 3 | **c₄₄ is inert** | zero first derivative for everyone, everywhere | Nonzero mixed second derivative (0, −2κ, +2κ). Unconstrained ≠ inert |
| 4 | **P1 is the only player exposed** to off-path indeterminacy | P1 is the only one with zero free parameters | P3 has poles too (c₁₁, c₂₁). Correct claim is narrower: only P1's pole *locations* are set by off-path parameters |
| 5 | **Greedy support repair** will find the exact equilibrium | drop the worst-violated coordinate to its pure value | Diverges monotonically: exploitability 2.1e-03 → 2.1e-01 over nine repairs |
| 6 | **Calling rates at N=n+1 sit below best response** because those sets are deterrence-driven | bet-response sets really do carry only 1–2 % reach at N=n+1 vs 47–70 % | Gap is positive everywhere and *larger* at N>n+1. Test mis-designed: forcing a_top=1 makes P1's range artificially all-nuts, so BR is fold-everything |
| 7 | **A certified equilibrium sits outside the SGS family** | one of 40 deviated in on-path b₄₁, reach 0.25 | Checker bug: free parameters rounded to 6 decimals before rebuilding. Unrounded it matches Table 3 to 1.11e-16 |
| 8 | **Random-restart search will find equilibria outside the family** | the solver certifies reliably once the support is right | 50,400 restarts found *zero* — including zero family members. Support space is the obstacle |

## 11.1 Bugs caught by controls, not by inspection

| bug | how it surfaced |
|---|---|
| Properness test miscounted **inert** parameters as free | control on the exact SGS profile returned "face of dim 2" instead of the known unique point |
| Newton `rcond` = 1e-10 → huge steps along near-null directions | exploitability got **58× worse** at (4,5) |
| Line search accepted non-improving steps | same |
| Residue `D′` computed as a first rather than mixed second derivative | printed 0 for every deviation |
| Test point outside the family (b₁₁≠b₂₁ with 0<c₁₁<½) | a single MISMATCH row in an otherwise clean identity check |
| Dominance scan measured unnormalised `du/dx` | returned 0/48 dominated; unreachable sets give exactly 0, so no sign is ever uniform |
| `_sub` cached one full leaf-table copy per player | (6,8) needed ~6 GB |
| Empty-support hypothesis → zero-size array reduction | crash at the all-pure branch of enumeration |
| Buffered stdout on a long background run | log file empty for 25 minutes |
| `nohup ... &` inside an already-backgrounded shell | job silently killed, 0-byte log |


---

# PART 14 — THE DYNAMICAL-SYSTEMS READING

Learning dynamics on an extensive-form game with binary information sets take the replicator
form, one 2-simplex per set, driven by counterfactual value:

```
dx_i/dt = x_i (1 - x_i) g_i(x),     g_i(x) = du_owner(i) / dx_i
```

## 14.1 The family is a MANIFOLD of fixed points [E]

Every SGS family point is a fixed point: interior coordinates have `g_i = 0` (indifference) and
pure coordinates have `x_i(1-x_i) = 0`. Verified across the c₃₃ window:
**max |dx/dt| = 1.9e-17.**

This is not an isolated equilibrium but a continuum of them — which is what makes the incidence
question well posed in the first place.

## 14.2 ρ's denominator IS an eigenvalue of the linearised flow [P,E]

Linearising, and using that u is multilinear so `d²u/dx_i² = 0`:

```
J_ij = delta_ij (1 - 2 x_i) g_i  +  x_i (1 - x_i) * d2u_owner/(dx_i dx_j)
```

For a **pure** coordinate, `x_i(1-x_i) = 0`, so row i of J has *only* its diagonal entry.
Therefore `(1 - 2x_i) g_i` is **exactly an eigenvalue**. Verified — match to `0.0e+00`:

| coordinate | x_i | g_i | predicted eigenvalue | in spectrum? |
|---|---|---|---|---|
| a₁₁ | 0.00 | −0.02187500 | −0.02187500 | **yes (0.0e+00)** |
| a₂₁ | 0.00 | −0.02187500 | −0.02187500 | **yes (0.0e+00)** |
| a₃₁ | 0.00 | −0.07604167 | −0.07604167 | **yes (0.0e+00)** |
| a₄₁ | 0.00 | −0.01093750 | −0.01093750 | **yes (0.0e+00)** |
| c₄₁ | 1.00 | +0.06041667 | −0.06041667 | **yes (0.0e+00)** |
| a₃₃ | 0.50 | 0.00000000 | 0.00000000 | **yes (0.0e+00)** |

And `du₁/da₁₁ = −0.02187500` is exactly ρ's denominator for `+e_{a₁₁}`.

> **ρ = −(du_C/dy)/(du_A/dy) has an eigenvalue of the linearised learning dynamics in its
> denominator.**

## 14.3 The pole IS the loss of hyperbolicity [E]

Since the equilibrium conditions are `g_i <= 0` for a pure-0 coordinate and `g_i >= 0` for a
pure-1 one, every pure coordinate is **stable**, and becomes **neutral exactly when g_i = 0** —
which is the deterrence boundary, which is where ρ's denominator vanishes.

Spectrum across the c₃₃ window at b₁₁=b₂₁=0.15, b₃₂=0.40:

| c₃₃ position | zero eigenvalues | stable | g(a₁₁) | ρ(a₁₁) |
|---|---|---|---|---|
| **lo (POLE)** | **17** | 26 | +0.000000 | **undefined** |
| lo + 2% | 15 | 28 | −0.000875 | −49.00 |
| quarter | 15 | 28 | −0.010937 | −3.00 |
| midpoint | 15 | 28 | −0.021875 | −1.00 |
| hi − 2% | 15 | 28 | −0.042875 | −0.02 |
| **hi (POLE)** | **16** | 27 | −0.043750 | **+0.00** |

**The multiplicity matches which deviations pole there.** At `lo` the count rises by **two**,
because a₁₁ and a₂₁ share that root (§7.5); at `hi` it rises by **one**, for a₄₁ alone.

> **A pole of the incidence ratio and a bifurcation of the learning dynamics are the same
> event.** The published parameter interval is simultaneously the deterrence window and the
> hyperbolicity region of the flow, and its endpoints are where an eigenvalue crosses zero.

(A single eigenvalue reads +2.5e-10 at every point — one real value inside the zero cluster,
numerical noise rather than an instability.)

## 14.4 A bifurcation-theoretic reading of the hard floor [E]

Proposition 5 says the window width is `w = ¾(b₁₁+b₂₁) + β/4`, and `w = 0 ⟺ β = 0`. In
dynamical terms: as β → 0 the two boundaries **collide**, and with them the two poles. The
collision is asymmetric — a₄₁'s numerator vanishes with the window so its pole dies, while
a₁₁'s survives (t = −1/48) and the singular point becomes the *only admissible* value of c₃₃.

The N = n+1 law (Part 9) is the same phenomenon at the level of the game rather than the
parameter: crossing the deck-size threshold changes the qualitative structure of the fixed-point
set. Because N is discrete this is not a smooth bifurcation, and §9.5.3 shows the switch is a
**fixed-point selection** rather than a change in any single best-response function.

## 14.5 The flow does not converge [G]

Integrating from random interior starts (RK4, 3,000 steps):

| run | dx/dt at end | max distance from nearest pure |
|---|---|---|
| 0 | 1.64e-02 | 0.4878 |
| 1 | 1.64e-02 | 0.4824 |
| 2 | 1.98e-02 | 0.4813 |
| 3 | 1.95e-02 | 0.4815 |
| 4 | 1.47e-02 | 0.4939 |

The state is still moving at ~2e-2 after thousands of steps and stays deep in the interior. The
flow **cycles or wanders; it does not settle onto the family.** This matches the standard picture
for no-regret dynamics — only the *time-average* converges — and it explains §9.7 directly: the
off-path coordinates receive essentially no training signal because the current iterate never
settles anywhere near them.

## 14.6 Is it chaotic? UNRESOLVED — the measurement is not precise enough [X]

Largest Lyapunov exponent by the Benettin tangent-space method with the exact Jacobian:

| | runs | lambda range | mean |
|---|---|---|---|
| three-player (48 coords) | 5 | −0.0066 … +0.0025 | **−0.0023** |
| **two-player control** (12 coords) | 4 | +0.0003 … +0.0096 | **+0.0053** |

**The control settles it, and settles it negatively.** Two-player zero-sum replicator dynamics
are volume-preserving, so the control's true exponent is **exactly 0**. Measuring +0.0053 means
the method carries a bias larger than the entire three-player signal. Upgrading the tangent step
from Euler to RK4 moved the control only from +0.0059 to +0.0053, so the residual bias is
elsewhere — most likely the clipping that keeps trajectories inside the box (which breaks
conservativity) and the finite-difference Jacobian used in the two-player case.

**Resolution ~ ±0.01; signal ~ 1e-3.** No claim either way about chaos is supportable from this
measurement. What *would* settle it: an unclipped formulation on the interior (e.g. logit
coordinates), an exact Jacobian for the two-player engine, and far longer runs after verifying
the trajectory has equilibrated.

## 14.7 What the dynamical view adds, honestly

**Real:** the family is a manifold of fixed points; ρ's denominator is exactly an eigenvalue;
the pole is exactly a loss of hyperbolicity, with multiplicity matching the deviations involved;
the flow provably does not converge, which explains why CFR cannot resolve the off-path
coordinates.

**Not established:** chaos. And the N = n+1 threshold is a discrete switch, so calling it a
bifurcation is an analogy rather than a theorem.

**Literature this connects to** (verify before citing — not read here): Sato, Akiyama & Farmer,
*Chaos in learning a simple two-person game*, PNAS 2002; Palaiopanos, Panageas & Piliouras on
multiplicative weights and chaos; Piliouras & Shamma on cycling in game dynamics.

---

# PART 12 — OPEN PROBLEMS

1. **Is the SGS family complete?** Open in the original paper. **Substantially advanced in
   Part 15** — the branch-and-bound was built; the P1-silent support space is now exhaustively
   enumerated and 39 of 80 P1-betting branches are proven empty. Still open: 41 P1-betting
   branches in which P1 bluffs at an interior frequency (§15.5, §15.7).
2. **Extensive-form vs normal-form properness.** Theorem 3 is scoped to the normal form. Does
   quasi-perfect or extensive-form proper select the same point? [?]
3. **Why does deck size select the fixed point?** §9.5.3 shows it is a simultaneity, not a
   one-way cause, but not *why* N = n+1 is the switching value.
4. **Does the mechanism reach larger games?** Everything here is tiny by design.
5. **A general theorem.** Conjecture: in any n-player constant-sum extensive game with n ≥ 3, an
   equilibrium component with an attainable deterrence boundary produces an unbounded incidence
   ratio there. Theorem 1's three clauses are stated to generalize; the residue theorem needs
   only multilinearity. [?]
6. **Does the indeterminacy matter for learning?** CFR converges to *some* family point (§9.7
   shows a systematic β bias). Which one, and does the choice favour a seat?
7. **Is the learning flow chaotic?** §14.6 could not resolve it — the two-player control, whose
   true exponent is 0, reads +0.005. Needs an unclipped (logit) formulation, an exact two-player
   Jacobian, and equilibrated long runs.
8. **Does the eigenvalue identity generalise?** §14.2 shows ρ's denominator is an eigenvalue for
   *pure* coordinates because their Jacobian row is diagonal. Whether an analogous statement
   holds for interior coordinates is untested. [?]

---

# PART 13 — REPRODUCTION

```
python check_engine.py      # engine sanity
python verify_paper.py      # Part 3 validation      -> log_verify.txt
python analyze.py           # Part 7 core results    -> log_analyze.txt, results.json
python handcheck.py         # Part 8 worked example  -> log_handcheck.txt
python followup4.py         # poles at all P1 openings; c34/c44 inertness
python followup5.py         # round-2 census, attainability controls
python followup6.py         # 2-player control
python followup7.py         # residue identity R = t/D'
python followup8.py         # refinement: off-path owners under trembles
python followup9.py         # tremble consistency; the refined face
python followup10.py        # 150-seed MCCFR study    -> cfr_sweep.json
python followup11.py        # hard floor, exact form, properness
python sweepNn.py           # the (n,N) pole sweep    -> sweep_Nn.json
python sweep6.py            # n=6 branches
python mechanism.py         # why P1 goes silent
python decompose.py         # exact per-opponent decomposition
python causal.py            # which half of Delta moves
python counterfactual.py    # rank-defined control
python dominance.py         # conditional dominance scan  -> dominance.json
python iterdom.py           # iterated dominance          -> iterdom.json
python enumerate_support.py # (3,4) certification         -> supports_34.json
python certify45.py         # (4,5) certification         -> certified_45.json
python enum_full.py         # pruned enumeration
python hunt.py              # random-restart equilibrium hunt
python dynamics.py          # replicator spectrum (imported by chaos.py)
python chaos.py             # Lyapunov exponents + 2-player calibration
python plots.py; python plots2.py   # figures 1-4
```

**Two numbers that convince a reader nothing was sampled:** **312** leaves in the base game and
**9,072** grid points, both enumerated exhaustively. Put them in the abstract.

---

# PART 15 — THE COMPLETENESS QUESTION, RE-OPENED AND LARGELY SETTLED

Part 10.5 left four inconclusive attempts and a verdict: *"What is actually needed:
branch-and-bound with partial-feasibility pruning."* That algorithm was built. This part records
it and what it found.

## 15.1 The instrument [E]

Three new engines, each validated against the existing ones before use.

| file | role | validation |
|---|---|---|
| `tree.py` | explicit 25-position game tree, one shape shared by all 24 deals | utilities vs `kuhn3p` **1.0e-15**; gradients **8.9e-16** |
| `bgrad.py` | batched exact `du_owner/dx` for a stack of profiles, 29 µs/row | vs `tree.tree_grad` **2.2e-16**; reach vs `kuhn3p.reach` **1.9e-16** |
| `ivl.py` | **interval propagation** over the tree: outer bounds on every `du/dx`, on reach, and on `(u1,u2,u3)`, for a *box* of profiles | collapses onto the exact gradient at a point (**5.6e-17**); containment verified on 300 random points inside random boxes; `util_box` containment on 400 points |

The bound is tree-structured, not term-by-term. At a node with coordinate `x` in `[lo,hi]` the
value interval is `[min_q (q·Vagg_lo + (1−q)·Vpass_lo), max_q (…)]` over `q` in `[lo,hi]` — tight
in `q`, because value is a *convex combination* in `q`. Term-by-term interval arithmetic on the
312-leaf sum loses the constraint `x + (1−x) = 1` and is far weaker.

### Search formulations, in the order they were tried

1. `bnb.py` — enumerate **support labels** `{0, 1, interior}` per coordinate, prune with the
   interval bound, collapse provably-unreachable coordinates.
2. `bnb2.py` / `bnb3.py` — the same, plus **value bisection** of the interior boxes.
3. `bnb5.py` — **no labels at all.** A box `[lo,hi]` per coordinate *implies* its own condition:
   `lo > 0` forces `du/dx ≥ 0`; `hi < 1` forces `du/dx ≤ 0`; both force `du/dx = 0`. Splitting
   `[0,1]` at `m` gives `[0,m]` (needs `du ≤ 0`) and `[m,1]` (needs `du ≥ 0`) — **both children
   carry a condition immediately, and the halves do not overlap.**

Formulation 3 removes a real defect of 1 and 2: the label "interior" has to be carried as the box
`[0,1]`, which *contains* the two pure labels, so the branch `a_j1 = interior` re-does the entire
problem. That redundancy is why the label search on the P1-betting branches would not terminate.

**Soundness.** Every pruning rule is a necessary condition of Nash, so no equilibrium is ever
discarded — with one qualification. Two "weak" rules fire when the value difference `Δ` at a
coordinate's node is bounded away from zero with a constant sign on the whole box: then
`du = Σ_n R_n Δ_n` vanishes only if every reach `R_n` is zero, i.e. only if the information set is
unreachable, in which case the coordinate cannot affect any leaf. Those rules move such a
coordinate to its dominant pure value. **They are sound modulo leaf-distribution equivalence**,
which is the right equivalence here: two profiles with the same 312-leaf distribution are the same
strategic object.

## 15.2 Table 2 re-derived rigorously, and one project claim corrected [E]

A single fixed point of interval propagation on the **full cube** `[0,1]^48` — no sampling, no
interiority assumption — forces **exactly 21 coordinates**:

```
-> 0 :  a12 a13 a14 a24   b12 b13 b14 b24   c12 c13 c14 c24     (12)
-> 1 :  a42 a43 a44       b42 b43 b44       c42 c43 c44          (9)
```

That is Table 2, entry for entry, from a rigorous global bound rather than the reach-normalised
scan of §10.1. **27 coordinates remain free**, not 26.

> **ERRATUM 3 — to this project, not to the paper.** §10.1 claimed `c41 = 1` is also
> dominance-forced, "a small strengthening" of Table 2. **It is not.** Witness: set
> `a22 = a32 = b23 = b33 = 0` (with the 21 Table-2 values). Then `du3/dc41 = 0.0` **exactly**
> while `reach(c41) = 0.25` — P3 holding card 4 wins the same 2 chips whether it bets and everyone
> folds, or checks and wins the showdown. The §10.1 scan confined the other coordinates to
> `[ε, 1−ε]`, which excludes precisely this profile; an interiority-restricted scan cannot
> establish dominance. `c41 = 1` belongs in Table 3, exactly where SGS put it.

## 15.3 The P1-silent branch: a complete support enumeration [E]

Branch: `a11 = a21 = a31 = a41 = 0`. After Table 2 and reachability collapsing, **18** coordinates
are live, so `3^18 = 387,420,489` support hypotheses. Depth-first search with interval propagation
and unit propagation at every node:

| | |
|---|---|
| search nodes | **5,267,496** |
| surviving support patterns | **3,045,358** (0.79 % of `3^18`) |
| wall clock | 525 s, one core |

This is the first exhaustive support enumeration of the branch. For comparison, §10.3's
certification searched `2^12 = 4,096` hypotheses, and §10.5's Attempt 4 sampled `3.2e5` of a
`1.089e12` space — coverage `2.9e-7`.

**Only 223 of the 3,045,358 patterns are compatible with Table 3's label structure.** The other
3,045,135 would, if realisable, be equilibria outside the family. They are the whole question.

## 15.4 Feasibility of the enumerated patterns [E,G]

Two-stage test on a **400,000-pattern uniform random sample** (13.1 % of the enumeration):

1. **Sound stage** — batched value bisection (8 levels) of each pattern's box. A pattern dies only
   when propagation *proves* no point in its box satisfies the first-order conditions.
2. **Search stage** — Levenberg–Marquardt on the active set (indifference equations for interior
   coordinates, plus any violated pure-coordinate sign condition pushed to its boundary), started
   from each surviving sub-box centre. Off-path coordinates are **variables, not constants** — an
   unreachable information set contributes nothing to utilities but its value still shapes other
   players' incentives (§7.7), and freezing it at 0.5 was an early bug that made every family
   control fail.

| | |
|---|---|
| patterns tested | 400,000 |
| **proven infeasible** by interval bisection | **320,743 (80.2 %)** |
| sub-boxes examined | 1,507,713 |
| LM-feasible candidates | 262 |
| **certified exact Nash** (max exploitability `< 1e-13`) | **259** |
| distinct leaf distributions among them | **114** |
| **outside the SGS family** | **0** |
| max leaf-distribution distance to the matching Table-3 profile | **2.30e-14** |

Coordinate ranges over the 114, restricted to coordinates that are actually **reached**:

```
a11 a21 a31 a41 = 0     a22 a32 = 0     a33 = 1/2  (reached in 112/114; free in the other 2)
b31 = b34 = 0           c31 = c22 = c32 = 0        c41 = 1
b11 in [0, 1/4]         b21 in [0, 0.1661]         b23 in [0, 1/8]
b33 in [1/2, 3/4]       b41 in [0, 0.6661]         c11, c21 in [0, 1/2]
```

Every Table-3 identity holds to machine precision across all 114:

| identity | max residual |
|---|---|
| `b41 = 2(b11 + b21)` | **4.2e-15** |
| `b33 = 1/2 + (b11+b21)/2 + β/2 − b23(1−b21)` | **1.5e-14** |
| `c21 = 1/2 − c11` | **8.1e-16** |
| `a33 = 1/2` (where reached) | **0** |
| `u1 = −κ(1/2 + β)` | **3.1e-16** |
| `u2 = −κ/2` | **1.0e-16** |
| `u3 = κ(1 + β)` | **2.3e-16** |

`β = max{b11,b21}` attains both endpoints of `[0, 1/4]`. The certified payoff set is exactly the
family's: `u1` in `[−3κ/4, −κ/2]`, `u2 = −κ/2` identically, `u3` in `[κ, 5κ/4]`.

## 15.5 P1 betting: 39 of 80 branches proven empty [E]

Branch on the label of P1's four opening coordinates: `3^4 = 81`, one of which is the silent
branch. **34 die on the first fixed point of interval propagation, in milliseconds.** The pattern
is structural:

| condition | branches dead at the root |
|---|---|
| `a11 = 1` (P1 always bets the worst card) | **22 / 27** |
| `a21 = 1` | 18 / 27 |
| `a11 = 1` together with `a21` in `{1, interior}` | **all** |

Five more were then **proven empty** by the full search — `(0,1,1,0)`, `(0,1,1,1)`, `(0,1,2,0)`,
`(0,1,0,0)`, `(0,1,1,2)` — every one a branch where P1 always bets card 2. Formulation 3 does this
in **231 to 1,777 nodes**; the label-only enumeration needed **43,218** nodes on `(0,1,1,2)` alone
and produced 25,738 patterns that then had to be tested one by one.

**41 branches remain open**, all with at least one opening coordinate strictly interior — P1
bluffing at a frequency strictly between 0 and 1. Attempt 2 of §10.5 remains the reason this
cannot be waved away: P1's bet is *not* dominated, gaining up to `+1.2499` against loose enough
opponents.

## 15.6 Table 3 derived algebraically, and where β comes from [P]

`symderive.py` fixes the support structure the enumeration says is the only one carrying P1-silent
equilibria, builds the eight indifference equations symbolically over the 24-deal tree in exact
rational arithmetic, and solves them. The equations are startlingly small:

```
du1/da33 = (2 b11 + 2 b21 − b41)/12            du2/db33 = (2 c11 + 2 c21 − 1)/12
du2/db11 = −(2 a33 − 1)/12                     du2/db41 = (a33 − c11 − c21)/12
du2/db21 = −(2 a33 + 2 b23 c11 − b23 − 1)/12   du3/dc21 = −(b11 + 2 b33 − b41 − 1)/12
du2/db23 = −(b21 − 1)(2 c11 − 1)/12
du3/dc11 = (2 b21 b23 − b21 − 2 b23 − 2 b33 + b41 + 1)/12
```

Reading them off:

- `du2/db11 = 0` gives **`a33 = 1/2`** immediately — P1's call frequency at KBF is pinned by P2's
  willingness to bet card 1, nothing else.
- `du1/da33 = 0` gives **`b41 = 2(b11 + b21)`**.
- `du2/db33 = 0` gives **`c21 = 1/2 − c11`**.
- `du2/db21 = 0` with `a33 = 1/2` collapses to **`b23 (2 c11 − 1) = 0`** — so *either* `b23 = 0`
  *or* `c11 = 1/2`. **That single factorisation is the origin of SGS's sub-family split.**

Solving each case:

| case | interior / boundary pattern | solution | utilities |
|---|---|---|---|
| **A** | `c11 = 0`, `c21` interior, `b23 = 0` | `a33=1/2`, `c21=1/2`, `b41=2(b11+b21)`, `b33=1/2+b11/2+b21` | `(−(2b21+1)/48, −1/48, (b21+1)/24)` |
| **B** | `c11` and `c21` both interior | adds **`b21 = b11`**; `b23=0`, `b33=1/2+3b11/2`, `b41=4b11` | `(−(2b11+1)/48, −1/48, (b11+1)/24)` |
| **C** | `c11 = 1/2`, `c21 = 0`, `b23` interior | `b33 = 1/2 + b11 + b21/2 − b23(1−b21)`, `b41=2(b11+b21)` | `(−(2b11+1)/48, −1/48, (b11+1)/24)` |

Each `b33` equals Table 3's `1/2 + (b11+b21)/2 + β/2 − b23(1−b21)` **exactly** (symbolic residual
0) once `β` is read as `b21` in case A and `b11` in cases B and C.

> **`β = max{b11, b21}` is not a formula — it is two cases glued.** Sub-family A carries
> `b11 ≤ b21` and produces `β = b21`; sub-family C carries `b21 ≤ b11` and produces `β = b11`; B
> has `b11 = b21` and the two agree. The `max` in Table 3 is the single expression covering all
> three, and nothing in the algebra ever computes a maximum.

Conditional on the support structure, this **is** a proof of Table 3.

## 15.7 What is now established, and what is not

> **Superseded in part by §15.9 (2026-09-07/09).** Item 3's "13.1 % random sample" is now the
> whole branch, and the second "not established" bullet is discharged. The rest stands. §15.9 also
> carries an erratum to §15.5's `feas.py` verdicts.

**Established.**

1. Table 2's 21 values follow from one rigorous global interval fixed point. `c41 = 1` does not.
2. The P1-silent support space is fully enumerated: 3,045,358 patterns of `3^18`.
3. In a 13.1 % random sample of those, 80.2 % are **proven** to carry no equilibrium, and every
   equilibrium that does exist there — 259 certified, 114 distinct — lies in the family, with all
   of Table 3's identities holding to `1.5e-14` and the payoff set exactly the family's.
   *(§15.9: now the entire branch — 80.3 % proven, 744 distinct certified, 0 outside the family.)*
4. 39 of the 80 P1-betting branches contain **no equilibrium at all**. Every branch in which P1
   always bets card 1, and every branch in which P1 always bets card 2 with `a41` not free, is
   dead.
5. Table 3's closed forms and its three-sub-family structure are derived algebraically.

**Not established.** The family is still not proved complete.

- 41 P1-betting branches are open, all with P1 bluffing at an interior frequency.
- ~~86.9 % of the enumerated silent patterns have not yet been screened.~~ **Discharged §15.9:**
  the branch is screened end to end.
- The LM stage is a *search*, not a decision procedure: a pattern it fails on is not thereby proved
  infeasible. Only the interval-bisection stage produces proofs, and it settled 80.2 %.

The honest statement is stronger than §10.5's, but the same in kind: **no equilibrium outside the
SGS family exists anywhere the search has looked — and the search has now looked exhaustively at
the support level.**

## 15.8 Reproduction

```
python control3.py                          # controls: known family equilibria survive every prune
python runsilent.py                         # complete P1-silent enumeration -> pats_0000.npy
python probe81.py                           # the 81 P1-opening branches     -> log_probe81.txt
python allbranch3.py 30000000 20            # integrated interval B&B on the surviving branches
python pipe.py pats_sample.npy 20 8 samp    # bisection + LM feasibility
python verify_surv.py surv_pat_samp.npy surv_x_samp.npy   # certify and classify
python symderive.py                         # symbolic derivation of Table 3
python feas.py "<task list>" 8              # targeted "can this coordinate deviate?" searches
```

# PART 15.9 — THE SILENT BRANCH COMPLETED, AND BOTH EXHAUSTIVE ROUTES TO THE BET BRANCH CLOSED

Work of 2026-09-07/09. Three things happened: the P1-silent branch was finished end to end, the two
exhaustive routes to the P1-betting branch were closed **by measurement** rather than by running out
of patience, and three errata were found — two of them in this project's own instrument.

## 15.9.1 The P1-silent branch, whole [E]

`pipe2.py` finished `pats_rest.npy`. Since `400,000 (samp) + 2,645,358 (rest) = 3,045,358`, that is
exactly the §15.3 enumeration: the branch is no longer a 13.1 % sample.

| | samp (§15.4) | rest | **whole branch** |
|---|---|---|---|
| patterns screened | 400,000 | 2,645,358 | **3,045,358** |
| **proven infeasible** by interval bisection | 320,743 (80.2 %) | 2,124,839 (80.3 %) | **2,445,582 (80.3 %)** |
| LM candidates | 262 | 1,912 | 2,174 |
| **certified exact Nash** (`expl < 1e-13`) | 259 | 1,879 | **2,138** |
| distinct leaf-distributions | 114 | 635 | **744** |
| **outside the SGS family** | 0 | 0 | **0** |

`union_silent.py` merges both certified sets by leaf-distribution signature into
`certified_eq_all.npy` and re-checks everything:

```
family leaf-distribution gap: max 1.288e-13   OUTSIDE family (>1e-9): 0 of 744
b41 = 2(b11+b21)                           max residual 9.70e-14
c21 = 1/2 - c11                            max residual 2.32e-14
b33 = 1/2+(b11+b21)/2+beta/2-b23(1-b21)    max residual 1.29e-13
beta = max{b11,b21}: [0, 0.25]  — the full family range, both endpoints attained
u1 [-0.031250000000, -0.020833333333]   u2 identically -0.020833333333
u3 [ 0.041666666667,  0.052083333333]   — exactly the family's payoff set
```

Re-running `verify_surv.py` on the old sample reproduces §15.4 to the digit (259 certified, 114
distinct, gap 2.301e-14), so the pipeline is unchanged and these numbers are new coverage.

## 15.9.2 ERRATUM 4 — every `feas.py` verdict was depth-limited [X]

`bnb5` emits a box when `W.max < wtol` **OR** `depth >= maxdepth`. All 13 feasibility tasks ran
`wtol=0.06, maxdepth=26`. After Table 2 there are ~26 free coordinates, so 26 splits is about *one
halving per coordinate* — width 0.5. Reaching 0.06 needs ~5 halvings each, i.e. depth ~130.

`widthscan.py` checked every emitted box:

```
TOTAL boxes 43321175   emitted on width tolerance: 0 (0.0000%)
```

Not one box in 43.3 million reached the tolerance. Meanwhile the node cap was `120,000,000` and the
largest task used `21,156,070` — 18 %. **The runs stopped on the wrong limit**, and `abort=False`
was true while saying nothing about coverage. Read those verdicts as "at one bisection per
coordinate, propagation could not empty this region", which is far weaker than it looked.

**Rule:** before any `bnb5` run, assert `maxdepth >= nfree * ceil(log2(1/wtol))`.

## 15.9.3 What the coarse boxes still prove: Table 2 on the betting side [E]

Coarse is not unsound — the surviving boxes are a rigorous *cover*, so `betencl.py` extracts an
enclosure with no new search. All 8 bet tags agree:

- **Table 2's 21 coordinates are forced across the entire P1-betting region.** Table 2 had only ever
  been established globally (§15.2); this is it holding separately where P1 bets, and it doubles as
  a control on the box set.
- The only other constraint recovered is `a21 in [0, 0.5]` whenever `a11 >= 0.02`.
- Utility enclosures are trivial (±0.8 against a family range of width 0.01) — the honest price of
  width-0.5 boxes.

## 15.9.4 Route A — support enumeration of a betting branch: CLOSED [E]

`treesize.py` implements Knuth's unbiased tree-size estimator: walk one random root-to-leaf path,
multiply the surviving-children counts, average over walks. 4,000 walks per branch. **The silent
branch is the control — its true size is known.**

| branch | estimated support patterns | vs silent |
|---|---|---|
| **silent (control, true 3,045,358)** | **3.035e6 ± 1.5e5** — 0.3 % error | 1x |
| `a11 = 1` | 1.815e9 | 600x |
| `a11` interior | 2.318e10 | 7,600x |
| `a41` interior | 2.957e10 | 9,700x |
| `a31` interior | 3.277e10 | 10,800x |
| `a21` interior | 4.000e10 | 13,100x |

**100 % of sampled paths survive pruning** on every betting branch — propagation is not biting at
all once P1 bets. Cross-checked by direct enumeration: `betenum.py a11 MIX` emitted 1,778,292 leaves
in 4,018,960 nodes in 1,289 s, i.e. 0.008 % of the estimate, putting one branch at ~194 days *before*
any screening; the screen itself runs at 48.9 patterns/s. §15.3's method does not port.

## 15.9.5 Route B — box refinement: CLOSED, under both split rules [E]

Depth ladder on `bet_a41_lo`:

| depth | 16 | 18 | 20 | 22 | 24 | 26 |
|---|---|---|---|---|---|---|
| boxes (`width` rule) | 12,178 | 45,594 | 138,809 | 337,074 | 651,161 | 1,544,817 |
| boxes (`grad` rule) | — | 24,346 | 53,361 | 111,627 | 230,124 | 475,538 |
| growth/level (`grad`) | — | — | 1.480 | 1.446 | 1.436 | **1.438** |

The `grad` growth rate is **flat at ~1.44**, not decaying toward 1. Reaching a real `wtol` needs ~104
further levels, and `1.44^104` is ~10^16. Even depth 40 is ~200x the boxes of depth 26 on the
*smallest* task alone — hundreds of GB before it is anything else.

## 15.9.6 The split rule was wrong, and it is one line [E]

`bnb5` splits the widest coordinate. `splitrule.py` compares alternatives on `bet_a41_lo` at
maxdepth=22, with `width` included as the control:

```
grad       344,620 nodes   111,627 boxes   324s   x0.331 boxes
reachgrad  344,620 nodes   111,627 boxes   325s   x0.331
width      847,044 nodes   337,074 boxes   369s   x1.000  <- reproduces the ladder exactly
reach      847,044 nodes   337,074 boxes   408s   x1.000
```

`grad` splits on `W * (DHI - DLO)` — width times how loose that coordinate's own gradient bound is.
Masking unreachable coordinates (`reach`) changes **nothing** on its own: an unreachable coordinate
already has `DHI - DLO = 0`, so `grad` drops it for free. 3.2x fewer boxes at depth 26 and a lower
exponent (1.44 against ~1.57). It does not reopen the completeness route, but every future `bnb5`
run is ~2.5x cheaper.

## 15.9.7 Route C — a 20,000,000-start multistart hunt [G]

With both exhaustive routes closed, `bethunt.py` searches: random starts with Table 2's 21
coordinates fixed (so 27 free), LM on the **projected-gradient residual** `x - clip(x + du, 0, 1)`
(`pgsolve.py`, no support hypothesis at all), then certification by `eqtools.expl`. About 75 % of
starts draw an opening coordinate from `[0.02, 1]` — they *begin* with P1 betting.

```
TOTAL starts 20,000,000  residual-converged 181,463  CERTIFIED 75,201  distinct 23,820
certified equilibria with P1 betting: 0

max exploitability       9.999e-14   (all < 1e-13)
family gap               max 5.822e-12     OUTSIDE family: 0 of 23,820
max P1 opening frequency 2.204e-12         — P1 silent in every one
u2 spread 1.25e-13 about -0.020833333;  beta spans the full [0, 0.25]
```

Every certified equilibrium reached from a betting start came back with P1 silent — the same
behaviour §10.5 Attempt 3 saw from CFR, now at 10^7 scale with exact certification instead of
convergence. **This is a search and cannot show the family is complete.**

Note that `181,463` points reached residual `< 1e-12` but only `75,201` are equilibria: the projected
gradient is a *first-order* condition, and off-path information sets make it insufficient (§7.7).
Certification is by `expl`, never by the residual.

## 15.9.8 ERRATA 5 and 6 — two bugs in this project's own verification [X]

> **ERRATUM 5.** `classify.family_gap` returns **1.0 as a sentinel** meaning "could not construct the
> Table-3 image", not as a measured distance, and its guard rejected any image coordinate above
> `1 + 1e-12`. The 20M hunt therefore finished by reporting `OUTSIDE family (>1e-9): 2 of 23820`.
> Both were the family's **own corner** `b11 = b21 = 1/4`, where Table 3 gives `b41 = 2(b11+b21) = 1`
> exactly and floating point lands at `1 + 1.0e-12`. Their real leaf-distribution gap, after the clip
> the function performs anyway, is **2.2e-16** — family members exactly. The false positive lands
> precisely at the extreme point a counterexample hunt would most want to believe.
> Fixed: `OOR_TOL = 1e-9` in `classify.py`, and `TOL` on the `[0,1]` checks in `family.violations`
> (which every other check in that function already had). `control_famgap.py` controls both
> directions: corners give gap 0, a genuine non-profile image is still rejected, and a 1e-6
> perturbation off the family is still detected with gap equal to the perturbation.

> **ERRATUM 6.** An earlier session recorded that `family.profile_B(b11, 1/2)` is *never* an
> equilibrium, citing exploitability 4.2e-03. That figure is real, but it is the value at `b11 = 0.2`
> only. `profile_B(b11, c11)` sets `b21 = b11`, so at `c11 = 1/2` the point lands in sub-family **C**,
> whose constraint `b21 <= min{b11, 1/2 - 2 b11}` reduces to `b11 <= 1/6`. Measured: `b11 = 0, 0.05,
> 0.125, 1/6` give `expl ~1e-16` (genuine equilibria); `1/6 + 1e-4` gives `1.25e-05`; `0.18, 0.2,
> 0.25` give `1.7e-03, 4.2e-03, 1.0e-02`. As recorded the note discards a whole family of valid
> control points and names the wrong mechanism.

## 15.9.9 Where the completeness question now stands

**Established.** Everything in §15.7, plus:

6. The P1-silent branch is screened **end to end** — 3,045,358 patterns, 80.3 % proven infeasible,
   744 distinct certified equilibria, **0 outside the family**, every Table-3 identity to ~1e-13,
   `beta` attaining both endpoints of `[0, 1/4]`.
7. Table 2's 21 coordinates are forced across the entire P1-**betting** region, not only globally.
8. A 20,000,000-start multistart search, three quarters of it started with P1 betting, produces
   75,201 certified equilibria and **not one** in which P1 bets.

**Not established.** The family is still not proved complete — but now with the reasons quantified:

- The P1-betting branch is not settled, and neither exhaustive route can settle it with this
  instrument: support enumeration is 10^9–10^10 patterns per branch (§15.9.4), and box refinement
  grows 1.44x per level while needing ~104 more of them (§15.9.5). These are measurements, not
  impressions.
- ~~19.7 % of the silent branch's patterns are not *proven* infeasible~~ **— closed to 0.45 % by
  §15.10.** 99.544 % of the branch is now proven infeasible; the remainder is 115 distinct patterns
  that carry the certified equilibria plus 13,779 undecided ones.

**The diagnostic that matters for any future attempt on the bet branch** is §15.9.4's: 100 % of
sampled paths survive pruning there. The obstruction is the *bound*, not the branching and not the
budget. Changing the split rule bought 3x; nothing will be won by branching harder against a bound
that never fires.

## 15.9.10 Reproduction

```
python widthscan.py bet_a11_hi ... sil_c41_lt1   # ERRATUM 4: 0 of 43.3M boxes hit wtol
python betencl.py 8 bet_a11_hi ...               # rigorous enclosure -> Table 2 on the bet side
python treesize.py 4000 6 silent a11:MIX a21:MIX a11:1 a31:MIX a41:MIX
python splitrule.py 22 4 width reach grad reachgrad
python gradladder.py 5 18 20 22 24 26
python union_silent.py                           # whole-branch certified set
python bethunt.py 625000 32 24 bet2              # the 20M-start hunt (~26 h)
python control_famgap.py                         # ERRATUM 5 control, both directions
python depthproof.py 4000 8 10 12 14 16          # proof rate vs bisection depth
python proveall.py pats_0000.npy 18 14 d18       # close the 19.7 % gap
```

# PART 15.10 — THE P1-SILENT BRANCH DRIVEN FROM 80.3 % TO 99.5 % PROVEN

Work of 2026-09-10/11. §15.9.9 named the one remaining gap that more compute
could close: 19.7 % of the silent branch's patterns were not *proven* infeasible,
resting only on LM failing to find a point there. That gap is now 0.45 %.

## 15.10.1 Result [E]

`proveall.py` re-runs the proving stage — `bisbatch.bisect`, the only stage that
produces proofs — at increasing depth, each stage taking as input only the
residual the previous one could not settle (`provechain*.sh`).

| depth | proven of its input | **cumulative proven** | residual |
|---|---|---|---|
| 8 | 2,445,582 of 3,045,358 (80.305 %) | **80.305 %** | 599,776 |
| 12 | 272,589 of 599,776 (45.448 %) | **89.256 %** | 327,187 |
| 16 | 176,677 of 327,187 (53.999 %) | **95.058 %** | 150,510 |
| 20 | 79,413 of 150,510 (52.763 %) | **97.665 %** | 71,097 |
| 24 | 30,286 of 71,097 (42.598 %) | **98.660 %** | 40,811 |
| 28 | 16,845 of 40,811 (41.276 %) | **99.213 %** | 23,966 |
| 32 | 7,569 of 23,966 (31.582 %) | **99.462 %** | 16,397 |
| 36 | 2,503 of 16,397 (15.265 %) | **99.544 %** | **13,894** |

```
FINAL: 3,031,464 of 3,045,358 proven infeasible (99.544 %)
       residual 13,894, of which 115 distinct patterns are KNOWN to carry
       equilibria (the 2,174 LM-feasible rows behind the 744 certified profiles)
       genuinely undecided: 13,779  (0.4525 % of the branch)
```

**Two controls.** The depth-8 stage returns 2,445,582 — bit-for-bit `pipe2`'s
number from §15.9.1, so `proveall` reproduces the published screen exactly. And
every one of the 115 distinct patterns that carries a certified equilibrium is
still present in the final residual: the chain never proved a pattern that has a
solution. `proveall.preflight` enforces this before each stage and refuses to run
on failure.

## 15.10.2 ERRATUM 7 — a batching constant was worth 20x in proving power [X]

> `bisbatch.bisect` shares **one `keepcap` across a whole block**, so the block
> size, not the depth argument, decides how much refinement each pattern actually
> receives. The first version of this chain ran at the inherited `CH = 1024` and
> plateaued at ~93 %, looking exactly as though the interval bound had been
> exhausted. It had not been. Measured on the depth-16 residual, identical depth
> and identical patterns:
>
> ```
> depth  block  keepcap   proven          boxes
>    16   1024    60000   1.61 %         129,355
>    20   1024    60000   1.61 %         129,355   <- identical
>    24   1024    60000   1.61 %         129,355   <- identical
>    16    128    60000  31.79 %         272,421
>    20    128    60000  67.19 %         309,345
>    24     32    60000  81.98 %         301,894
> ```
>
> At block 1024 the results for depths 16, 20 and 24 are **bit-identical** — the
> block saturates the cap at the same place every time, so every level past ~14
> is inert. Raising `keepcap` to 400,000 changes nothing; what matters is the
> per-pattern allowance `keepcap / block`. `proveall` now uses `CH = 32`, which is
> both the most effective and the fastest setting measured.
>
> **§15.4's published 80.3 % is unaffected** — verified directly: at depth 8 the
> proof rate is 81.10 % at every block size from 32 to 1024, because the cap only
> binds once boxes-per-pattern grows with depth.

## 15.10.3 Where this method stops [E]

The per-stage yield holds near 50 % through depth 20 and then decays —
42.6, 41.3, 31.6, 15.3 % at depths 24/28/32/36 — while cost roughly doubles per
level (depth 8 is 0.05 core-s per pattern; depth 28 is 3.5). Depth 36 is where
the trade stops paying. Going further would need a different bound, not a larger
depth argument.

## 15.10.4 What the branch now says

**Every pattern in the P1-silent support enumeration is now one of:**

- **proven to carry no equilibrium** — 3,031,464 of 3,045,358 (**99.544 %**), by
  sound interval bisection;
- **known to carry one of the 744 certified equilibria**, all of which lie in the
  SGS family (115 distinct patterns);
- **undecided** — 13,779 patterns (**0.4525 %**) where bisection could not prove
  emptiness and LM found no point.

That last class is the honest remainder. It is 43x smaller than the 19.7 % §15.9
had to report, and no equilibrium has ever been found in it.

## 15.10.5 Reproduction

```
python proveall.py pats_0000.npy        8  14 s08    # control: reproduces 80.305 %
python proveall.py prove_surv_s08.npy  12  14 t12
python proveall.py prove_surv_t12.npy  16  14 t16
python proveall.py prove_surv_t16.npy  20  14 t20
python proveall.py prove_surv_t20.npy  24  14 t24
python proveall.py prove_surv_t24.npy  28  14 t28
python proveall.py prove_surv_t28.npy  32  14 t32
python proveall.py prove_surv_t32.npy  36  14 t36
```

Total ~24 h on 14 workers. Deepen the residual, never the input: running depth 18
directly at all 3,045,358 patterns managed 376 of 1523 chunks in 14 hours before
being abandoned for this chain.

# PART 16 — THE COMPLETENESS QUESTION, DECIDED BY EXACT CERTIFICATES

Work of 2026-09-15/16. Part 15 ended with the silent branch 99.5 % *proven* and both exhaustive
routes to the betting branches closed by measurement. Both conclusions were about the instrument,
not the game. Two things changed:

1. `offpath.py` (2026-09-15) showed the family is **not complete as a set of profiles** — an exact
   Nash equilibrium with `b12 = 9/100` off path — so the only completeness that can be true is
   **on path**: every equilibrium plays like a family member wherever play is reached. It also
   showed every previous pruning rule that moved an unreached coordinate to its dominant value
   (bnb2/bnb5 "weak rules", the Table-2 slice) was sound for *sequentially rational* equilibria
   only. `bnb6.py` is the Nash-sound propagation (strong rules, a chord contractor, a
   slope-directed split); `enum6.py` is the support enumeration driven by it, with a
   contracted box per leaf. Its silent-branch tree has **4,616 leaves** where §15.3's had
   3,045,358 patterns.
2. Every residual leaf of every earlier chain turned out to be undecidable by interval
   reasoning *at any budget*, for one of three structural reasons (§16.2). An exact per-leaf
   decision procedure (§16.1) decides all of them in seconds.

## 16.1 The exact leaf stage: `symleaf.py`, `exactbox.py`, `exlp.py` [E]

An `enum6` leaf is a label pattern (0 / 1 / MIX / DC per coordinate) plus a box. With the 0/1
coordinates substituted, each own-gradient is a small multilinear polynomial over **Q** in the MIX
and DC coordinates. `symleaf.decide` returns one of

| verdict | certificate |
|---|---|
| `EMPTY_GB` | `1 ∈ ⟨E⟩`: the indifference equalities have no complex solution |
| `EMPTY_MIX` | Rabinowitsch: `1 ∈ ⟨E, 1 − t·v⟩`, so the MIX coordinate `v` is 0 (or 1) on every solution — contradicting "strictly interior" |
| `EMPTY_CONST` | an inequality reduces modulo the Gröbner basis of `E` to a constant of the wrong sign |
| `EMPTY_BOX` | `exactbox.prove_empty`: rational interval branch-and-bound with **open** endpoints on MIX coordinates, HC4 contraction, and an LP relaxation at every node |
| `FAMILY` | the leaf may be non-empty and every equilibrium in it satisfies Table 3 on its reached coordinates — pins by the labels, the identities (`a33 = ½`, `b41 = 2(b11+b21)`, `c21 = ½ − c11`, the `b33` formula split on `b11 ≶ b21`) by radical membership or by proving `{h > 0}` and `{h < 0}` empty — **and** SGS's parameter ranges for its sub-family, each proved by showing `{feasible, h > 0}` empty |
| `OPEN` | none of the above within the budget (a second pass at 10× the budget follows automatically) |

Every arithmetic step is `fractions.Fraction`. The LP relaxation (`exlp.py`) is proposed by HiGHS in
floating point and **certified in rationals**: the float duals are clipped and repaired, and the
weak-duality bound `b·y + U·w ≤ target` is checked exactly; only an infeasibility verdict is ever
used. Three ingredients of the relaxation each decided a class of leaves nothing else could:
recursive McCormick envelopes on every product link; **monotone elimination** rows (a constraint
affine in a variable whose coefficient has a sign determined *factor by factor* is weakest at one
end of that variable's range — the coefficient `10(1−b41)(1−2c21)` expands to an interval
straddling 0); and Gröbner normal forms of every inequality and identity, so the LP sees the
substituted system.

Controls: `control_symleaf.py` — every certified equilibrium we own lies in a FAMILY leaf (§16.3).

## 16.2 Three errata about the instrument, and one about the theory [X]

**ERRATUM 8 — the first-order system is not the Nash condition.** `du_i/dx_i = Σ_n R_n Δ_n`
vanishes identically at an information set the player keeps unreached by their *own* earlier
choice (P2 always betting card 4 ⇒ P2's call/fold sets after checking). A dominated off-path
continuation there can "support" the earlier choice, and the first pass returned five OPEN silent
leaves (`a32` MIX, `b21 ≈ 0.338`) that are first-order points and not equilibria. The correct
system uses the **own-reach-stripped** gradient `D_i` (`symbet.build_D`: opponents' reach only,
own factors set to 1): `D_i = 0` for MIX, `≤ 0` / `≥ 0` for 0 / 1, and for a DC coordinate `x`
the pair `x·D_i ≥ 0`, `(1−x)·D_i ≤ 0`. By the one-deviation principle over each player's own
decision tree this is exactly the Nash condition, up to re-choosing coordinates at own-unreached
sets — which never changes on-path play. With `D`, those five leaves die at the root.

**ERRATUM 9 — "984 leaves carry certified equilibria" was 12.** `check_enum6.py`'s control B
matched certified *patterns*; an LM pattern can label a coordinate MIX while its certified value is
`0.0`. The point sits on the leaf's boundary, i.e. in the neighbouring leaf. The exact stage
returns `EMPTY_MIX` for such a leaf and is right.

**ERRATUM 10 — interval reasoning cannot decide a family-adjacent leaf, ever.** The three
patterns: (i) a coordinate the family holds at 0 labelled MIX — the closure contains solutions,
so a closed box survives every refinement (`EMPTY_MIX` decides it); (ii) two linear conditions
jointly infeasible, `b21 − b11 > 0` with `b11 − b21 ≥ 0` — bisection converges to the diagonal
forever (the LP decides it in one pivot); (iii) a nonlinear chain, `a32 = a33 = ½, c11 = c21 = ¼`
turning the `b41 = 1` condition into `−1/96` (`EMPTY_CONST`). §15.10's 0.45 % residual and
`prove6pat`'s 26 % at 3,000 nodes were entirely these.

**Theory: Table 3's ranges survive Nash.** In Nash mode P1's fold condition at KKB with card 2
carries P2's off-path `b44` with coefficient `10(1−b41)(1−2c21) ≥ 0`, so it is weakest at
`b44 = 1`, where it is exactly SGS's `c11 ≤ (2−b11)/(3+2b11+2b21)`. Off-path freedom can only
*tighten* P1's deterrence conditions here; the on-path parameter set is SGS's.

## 16.3 The P1-silent branch: decided in both readings [E]

| mode | rules | leaves | empty | FAMILY | control |
|---|---|---|---|---|---|
| seq (`bnb6` weak rules: sequentially rational equilibria) | `enum6 silent` | 4,616 | **4,604** (GB 1,280 · box 2,862 · const 462) | **12** | 744 family points all in FAMILY leaves |
| nash (`KUHN_MODE=nash`: strong rules + dominance at certainly-reached sets) | `enum6 silent` | 5,754 | **5,742** (GB 1,980 · box 3,149 · const 613) | **12** | 744 + the 23,820 hunt points + the off-path witness all in FAMILY leaves |
| nash, re-enumerated under the value-margin contractor (`silentN2`, 2026-09-16 18:51) | `enum6 silent` | 5,754 | **5,742** (same split) | **12** | same control, PASSED |

167 s and 308 s on 8 workers. The 12 FAMILY leaves are, in both modes, exactly the SGS
structure: sub-family A (4 leaves: generic, `b11 = 0`, `b11 = b21 = 0`, `b41 = 1`), B (3: generic,
`b11 = 0`, `b41 = 1`), C (5: generic, `b23 = 0`, `b21 = 0`, both, `b11 = b21 = 0`). Every identity
and every parameter range is proved on every one of them.

**Established.** Every Nash equilibrium of three-player Kuhn poker in which P1 never bets has
on-path play in the SGS family — Table 3's identities *and* its parameter ranges — with the
equilibrium's off-path coordinates otherwise free (§offpath). This is the strongest reading under
which "the family is complete" is true, and it is now a theorem modulo §16.5's caveat.

## 16.4 The P1-betting branches [E]

`runbet6.py` (exact stage on every leaf; the interval stage `prove6pat` was retired after it
proved 20–35 % of the last branches in hours and `symleaf` decided the rest in seconds). Seq mode:
33 branches alive at the root (`root81.py`), the silent one above, 32 betting. Nash mode: 78
alive, 77 betting, queued behind the seq run (`chain_nash.ps1`). The ledger is
`runbet6_summary.txt` / `runbet6_summary_nash.txt`; every finished branch so far is **empty**.
`python summarize6.py` regenerates the table from the ledgers.

**Exact frontier filter (2026-09-17).** `enum6` now runs the exact root test on every subtree of
its top expansion before the float DFS (`enumx.node_test`: the label pattern with unassigned
coordinates carrying the best-response pair `x·D ≥ 0`, `(1−x)·D ≤ 0` — a sound relaxation of every
leaf below). On the finished Nash branch `a11:MIX,a21:MIX,a31:0,a41:1` it killed 93.6 % of the 962
frontier subtrees; on `a11:MIX,a21:MIX,a31:MIX,a41:1` 640 of 729. Control: the Nash silent branch
with the filter gives 5,658 leaves → 5,646 empty + 12 FAMILY, `control_symleaf` PASSED (`silentX`).
A pure exact DFS from the root is *not* the win: with ~40 unassigned coordinates the test costs
~5 s and prunes almost nothing at the top of the tree (3 → 9 → 27 → 78 alive at levels 1–4).

**Layered exact enumeration (2026-09-19, `enuml.py`).** The frontier filter was not enough: the
surviving 12 % of subtrees held 99 % of the leaves (`a11:MIX,a21:MIX,a31:MIX,a41:1`: 736,987
leaves, 17 h of float enumeration + 6 h of exact decision, all empty). `enuml` applies the same
exact test every 4 levels of the label DFS. It kills 84–94 % of the nodes it sees at every layer,
and on betting branches it reaches **zero leaves**: `a11:0,a21:MIX,a31:0,a41:0` (enum6: 9,987
leaves, 940 s) → 96 leaves in 268 s; the test branch `a11:MIX,a21:MIX,a31:0,a41:1` (enum6: 125,993
leaves, 6,001 s) → 4,087 exact tests, 0 leaves in its first 20 of 38 subtrees. Control: the Nash
silent branch → **84 leaves → 72 empty + 12 FAMILY**, `control_symleaf` PASSED (`silentL`, all
24,565 certified points found). The driver runs it with `KUHN_ENUM=layered`; a branch line with
`leaves 0` means no support survived the exact test at any layer. Soundness is that of the frontier
filter (§16.1, `enumx.py`): the node system is a relaxation of every leaf below it.

Also 2026-09-17: 20 first-pass timeouts in five Nash branches were all empty at the root once
`exactbox` rounded contracted bounds outward to the dyadic grid 2⁻⁴⁸ — without it the
denominators grew 3 → 5 → 12 → 39 → 203 → 1,075 bits in six contraction rounds and the
contractor stalled — and the root LP was moved ahead of any Gröbner computation.

### 16.4.1 Result: every P1-betting branch is empty [E]

Nash mode, all 77 branches alive at the root (`root81.py`), decided 2026-09-16 → 2026-09-19.
"supports" = leaves of the enumeration that reached the exact stage (0 when the exact test killed
every subtree before the bottom); every one of them is certified empty; `family` and `open` are 0
everywhere. 1,337,533 supports in all; the layered runs performed 421,304 exact node tests.

| branch (a11,a21,a31,a41) | supports | family | open |
|---|---:|---:|---:|
| `0,M,0,1` | 9987 | 0 | 0 |
| `0,M,1,1` | 10677 | 0 | 0 |
| `0,M,M,1` | 210788 | 0 | 0 |
| `M,0,0,1` | 4981 | 0 | 0 |
| `M,0,M,1` | 115610 | 0 | 0 |
| `M,M,0,1` | 125993 | 0 | 0 |
| `M,0,1,1` | 7112 | 0 | 0 |
| `0,0,1,0` | 886 | 0 | 0 |
| `M,0,1,M` | 4427 | 0 | 0 |
| `M,M,1,1` | 41300 | 0 | 0 |
| `0,0,1,M` | 1913 | 0 | 0 |
| `M,M,1,M` | 6970 | 0 | 0 |
| `0,M,1,M` | 5914 | 0 | 0 |
| `0,M,1,0` | 6570 | 0 | 0 |
| `M,0,1,0` | 7164 | 0 | 0 |
| `M,M,1,0` | 7479 | 0 | 0 |
| `M,M,M,1` | 736987 | 0 | 0 |
| `0,M,0,0` | 96 | 0 | 0 |
| `0,0,0,M` | 2735 | 0 | 0 |
| `0,0,M,0` | 1589 | 0 | 0 |
| `M,0,0,0` | 0 | 0 | 0 |
| `M,M,0,0` | 0 | 0 | 0 |
| `M,M,0,M` | 13441 | 0 | 0 |
| `0,0,M,M` | 4 | 0 | 0 |
| `M,0,0,M` | 3055 | 0 | 0 |
| `0,M,0,M` | 8273 | 0 | 0 |
| `0,M,M,0` | 0 | 0 | 0 |
| `M,0,M,0` | 0 | 0 | 0 |
| `M,M,M,0` | 0 | 0 | 0 |
| `0,M,M,M` | 0 | 0 | 0 |
| `M,0,M,M` | 0 | 0 | 0 |
| `M,M,M,M` | 0 | 0 | 0 |
| `0,1,0,0` | 96 | 0 | 0 |
| `0,1,0,1` | 56 | 0 | 0 |
| `0,1,0,M` | 0 | 0 | 0 |
| `0,1,1,0` | 96 | 0 | 0 |
| `0,1,1,1` | 224 | 0 | 0 |
| `0,1,1,M` | 0 | 0 | 0 |
| `0,1,M,0` | 288 | 0 | 0 |
| `0,1,M,1` | 0 | 0 | 0 |
| `0,1,M,M` | 0 | 0 | 0 |
| `1,0,0,0` | 192 | 0 | 0 |
| `1,0,0,1` | 530 | 0 | 0 |
| `1,0,0,M` | 0 | 0 | 0 |
| `1,0,1,0` | 256 | 0 | 0 |
| `1,0,1,1` | 377 | 0 | 0 |
| `1,0,1,M` | 24 | 0 | 0 |
| `1,0,M,0` | 993 | 0 | 0 |
| `1,0,M,1` | 0 | 0 | 0 |
| `1,0,M,M` | 0 | 0 | 0 |
| `1,1,0,0` | 0 | 0 | 0 |
| `1,1,0,1` | 29 | 0 | 0 |
| `1,1,0,M` | 24 | 0 | 0 |
| `1,1,1,0` | 0 | 0 | 0 |
| `1,1,1,1` | 1 | 0 | 0 |
| `1,1,1,M` | 217 | 0 | 0 |
| `1,1,M,0` | 0 | 0 | 0 |
| `1,1,M,1` | 0 | 0 | 0 |
| `1,1,M,M` | 0 | 0 | 0 |
| `1,M,0,0` | 0 | 0 | 0 |
| `1,M,0,1` | 0 | 0 | 0 |
| `1,M,0,M` | 0 | 0 | 0 |
| `1,M,1,0` | 0 | 0 | 0 |
| `1,M,1,1` | 179 | 0 | 0 |
| `1,M,1,M` | 0 | 0 | 0 |
| `1,M,M,0` | 0 | 0 | 0 |
| `1,M,M,1` | 0 | 0 | 0 |
| `1,M,M,M` | 0 | 0 | 0 |
| `M,1,0,0` | 0 | 0 | 0 |
| `M,1,0,1` | 0 | 0 | 0 |
| `M,1,0,M` | 0 | 0 | 0 |
| `M,1,1,0` | 0 | 0 | 0 |
| `M,1,1,1` | 0 | 0 | 0 |
| `M,1,1,M` | 0 | 0 | 0 |
| `M,1,M,0` | 0 | 0 | 0 |
| `M,1,M,1` | 0 | 0 | 0 |
| `M,1,M,M` | 0 | 0 | 0 |
| **77 branches** | **1337533** | **0** | **0** |

The 16 largest counts (up to 736,987) are the branches decided before the layered enumeration and
the bet-first label order existed; under the final method the same class of branch gives 0–13,441
supports and takes minutes (the all-MIX branch, Knuth estimate 2.7 × 10⁶ patterns: 0 supports,
205 s). Cross-check of the two methods on one branch: `a11:MIX,a21:MIX,a31:MIX,a41:1` — `enum6`
736,987 supports, all certified empty (23 h); `enuml` with the bet-first order 2,406 supports, all
certified empty (484 s on 4 workers, `xcheck2_MMM1`). Consistent, as they must be: the layered
method only removes supports that the exact test certifies empty at an ancestor.

The seq-mode run was stopped after 17 of 32 branches on 2026-09-16 (every sequentially rational
equilibrium is a Nash equilibrium, so the Nash-mode run subsumes it) and completed with the layered
method on 2026-09-19: **32 of 32 branches, 230,975 supports, all empty** (`runbet6_summary.txt`).

## 16.5 What is established, and the one caveat

**THEOREM (on-path completeness).** *Every Nash equilibrium of three-player four-card Kuhn poker
has P1 never betting, and its play at every reached information set is that of a member of the
SGS family: Table 3's identities and its parameter ranges hold on the reached coordinates. Off the
path of play the equilibrium set is strictly larger than the family (the `b12 = 9/100` witness).*

Proof structure, every step an exact certificate except the one caveat below: the 81 label cells
of P1's four opening coordinates cover the profile space; 78 survive the root (§root81); the
silent cell's 5,754 supports are 5,742 certified empty + 12 FAMILY with identities and ranges
proved (§16.3, three independent enumerations, control on 24,565 certified equilibria); the 77
betting cells contain no support at all (§16.4.1). Sequential-rationality reading: implied.

- **Caveat, quantified.** The *leaf set* is produced by `enum6` / `enuml`, whose float
  propagation is `ivl`'s interval arithmetic without directed rounding. Every prune carries a margin
  `TOL = 1e-11` in *value* space (`DHI < −tol`, `DLO > tol`, `DMIN > tol`), and `ivl.bounds` is
  four levels of convex combinations of payoffs `|V| ≤ 3`, four-factor products of numbers in
  `[0, 1]` and a six-term sum scaled by 1/24 — an accumulated rounding error of order `1e-13`, two
  orders below the margin. The one place the margin was in the wrong space was the chord
  contractor (`bnb6.propagate`): `t_c − tol` is a margin in the pinned coordinate, which is not a
  value margin when the chord is nearly flat (a value error `e` becomes `e/slope` in `t`). Fixed
  2026-09-16 18:20: the excluded range is now where the computed chord is below `−tol` in value,
  then a further `tol` in `t`; an excluded point has true chord `< −tol + 3e < 0`. The silent
  branches and the seq-mode betting branches finished before that time were enumerated with the
  `t`-margin contractor (the unsound case needs a chord slope below `3e/tol ≈ 0.03` *and* an
  equilibrium within `3e` of the kill line — not something a rational game produces, but not a
  proof); the Nash-mode silent branch is re-enumerated under the fixed contractor (`silentN2`) and
  every Nash-mode betting branch uses it. `control_symleaf.py` (24,565 certified equilibria, all
  in FAMILY leaves) is the empirical check on the whole chain.

- **Two small checks, 2026-09-20.** (i) The 3 opening cells `root81` kills (`a11:0,a21:0,a31:{0,1,MIX},a41:1`)
  were killed by *float* propagation only; `enumx.node_test` from the full box `[0,1]^48` (no float
  box) certifies each empty exactly in 0.2-0.3 s, so no cell of the 81 rests on `ivl` alone.
  (ii) In all 12 FAMILY leaves (`silentN2`, `silentLB`) every DC coordinate has reach bound exactly 0
  (a 0/1 label on every path to it), so "reached ⇒ non-DC ⇒ checked by the FAMILY test" holds with
  no float in it. Note also that the layered exact tests *start from* the float-contracted box
  (`enumx.node_test(lab, LO, HI)`, widened 1e-9): the caveat covers the box handed to the exact
  stage, not only the leaf set.

## 16.6 Reproduction

```
python control6.py                                  # bnb6 soundness controls (2026-09-15)
python enum6.py silent 8 silent3                    # seq-mode silent leaves      (179 s)
KUHN_MODE=nash python enum6.py silent 8 silentN     # nash-mode silent leaves     (1826 s)
python symleaf.py silent3 8 - 0 300 600             # 4604 empty + 12 FAMILY      (167 s)
python symleaf.py silentN 8 - 0 300 600             # 5742 empty + 12 FAMILY      (308 s)
python control_symleaf.py silent3 ; python control_symleaf.py silentN
python root81.py ; KUHN_MODE=nash python root81.py  # 33 / 78 branches alive at the root
KUHN_MODE=nash KUHN_ENUM=layered KUHN_ORDER=bet python runbet6.py 16 300   # all 77 nash branches (hours)
KUHN_MODE=seq  KUHN_ENUM=layered KUHN_ORDER=bet python runbet6.py 16 300   # the seq-mode ledger
KUHN_MODE=nash KUHN_ORDER=bet python enuml.py silent 4 silentLB 4          # layered control: 12 FAMILY
python control_symleaf.py silentLB                                          # PASSED
python summarize6.py                                # both ledgers as tables
```
`restart.ps1` relaunches the whole thing after a reboot (keepawake + the nash driver with the
three environment variables); `runbet6` skips ledgered branches and `symleaf` resumes from its
checkpoint.

Re-derivation of 2026-09-20/21 (directed rounding, suffix R, certificates) — the record of
§16.7–16.8:
```
python test_ivl_directed.py                          # outward rounding vs the recursion in Fractions
python control6.py                                   # ALL CONTROLS PASSED (log_control6_R.txt)
python checkD.py                                     # the 48 gradients recomputed from the tree: 48/48
KUHN_SUFFIX=R python root81.py ; KUHN_MODE=nash KUHN_SUFFIX=R python root81.py    # 33 / 78, identical lists
KUHN_MODE=nash KUHN_ORDER=bet python enuml.py silent 8 silentR 4                   # 668 supports, 12 FAMILY
python control_symleaf.py silentR                                                  # PASSED
powershell -File rerunR.ps1                          # nash (18 workers) + seq (8) drivers, KUHN_SUFFIX=R
KUHN_MODE=nash python resolve_left.py R 16 ; KUHN_MODE=seq python resolve_left.py R 8   # interval fallback
python summarize6.py R                               # both ledgers (ledger_tables_R.txt)
python certall.py R 24                               # certificates + independent check, cert_summary_R.txt
python checkcert.py cert_silentR.json.gz             # replay any one leaf set by hand
```

## 16.7 Directed rounding: the caveat removed (2026-09-20)

**What changed.** `ivl.py` now rounds every floating-point operation outward. IEEE-754 round-to-
nearest gives, for a real `r` that rounds to the double `f`, `pred(f) <= r <= succ(f)` (a
neighbour of `f` nearer to `r` would contradict `f` being the nearest), so `nextafter(f, -inf)`
is a true lower bound and `nextafter(f, +inf)` a true upper bound after every `+ - * /`. The
value recursion is evaluated as `V = P + x (A - P)` (lower bound of `A - P` first, `x >= 0`),
the reach products round outward, the six-node sums are sequential rounded adds instead of a
BLAS matmul, and the `1/24` scale is a rounded division by the exact integer 24. Exact zeros are
preserved (a sum that rounds to 0 is 0; a product that rounds to 0 with two nonzero factors
would be an underflow, which raises instead of rounding — impossible at the box sizes the
enumeration produces, but the check makes the claim unconditional), which is what the reach-
upper-bound test `RH == 0 -> don't-care` needs. `bnb6.propagate`'s chord contractor computes the
crossing `t_c` in the safe direction (numerator down, denominator up, quotient down for `tlo`,
the mirror for `thi`) and the kept range `[lo + w tlo, lo + w thi]` rounded outward; the extra
`tol` margins in value and in `t` are kept as pure slack. Nothing else in the chain touched a
float verdict (the exact stage `symleaf` / `exactbox` / `exlp` uses floats only to *propose*
LP duals and branching choices, every verdict is certified in `Fractions`). `KUHN_ROUND=nearest`
restores the old arithmetic for comparison. Cost: `ivl.bounds` is 2.1x slower on a 512-row
batch (3.4x on tiny ones — `enuml`'s top expansion is now batched for that reason).

**Verification of the rounding itself** (`test_ivl_directed.py`): the same
recursion evaluated in exact rationals on 60 boxes (random, with exact 0/1 endpoints, points,
and pinned coordinates): every directed bound encloses the exact one (0 violations over
5 x 48 x 60 numbers), the directed bounds enclose the old nearest ones (max gap 3e-15), the
worst distance from the exact recursion is 1.3e-14, and the reach upper bound is zero exactly
where the exact one is. `control6.py` (convexity of the pinned bounds, 1,344 certified
equilibria never killed or contracted past, dependency graph, search controls): see
`log_control6_R.txt`.

**Re-derivation (suffix R, nothing from the 2026-09-19 run reused).**
- `root81.py`: 78 / 81 nash, 33 / 81 seq branches alive at the root — identical lists.
- Silent branch, nash mode, layered, bet order (`enuml.py silent 8 silentR 4`): 668 supports
  (1,901 top subtrees, 351 after the exact filter, 2,835 exact tests), **656 certified empty +
  the same 12 FAMILY leaves** (label vectors identical to `silentLB` and `silentN2`), 1,491 s.
  `control_symleaf.py silentR`: 744 family + 23,820 hunt equilibria + the off-path witness all
  in FAMILY leaves — PASSED.
- Betting side: `rerunR.ps1` = `KUHN_SUFFIX=R KUHN_ENUM=layered KUHN_ORDER=bet runbet6.py`, nash
  (18 workers) and seq (8 workers) side by side; ledgers `runbet6_summary_nashR.txt` /
  `runbet6_summaryR.txt`, `python summarize6.py R`. **RESULT (09-21 04:18): nash mode 77 / 77
  branches, 45,276 supports, every one certified empty** (45,267 by the exact stage, 9 leaves of
  `a11:0,a21:MIX,a31:0,a41:1` by the interval fallback in 6,047 nodes); 47 of the 77 branches
  have no support at all; 46,783 exact node tests (34,123 kills), 210,508 top-expansion subtrees
  of which 1,187 survived the exact filter; 8.3 h of enumeration summed over branches (8h35m
  wall, 18 workers, sharing the box with the seq driver). **Seq mode 32 / 32 branches, 20,755
  supports, all empty** (34 leaves by the interval fallback: 8 + 26, 25,536 nodes), 4.4 h summed.
  `ledger_nashR_table.txt` / `ledger_seqR_table.txt` hold the per-branch tables (supports,
  top-expansion subtrees, survivors, exact tests, kills, seconds, fallback leaves).

**THEOREM, restated without the caveat.** *Every Nash equilibrium of three-player four-card
Kuhn poker is realization-equivalent to a member of the SGS family: P1 never bets, and on every
reached information set its play satisfies Table 3's identities and parameter ranges. As
profiles the equilibrium set is strictly larger (the `b12 = 9/100` witness).* Proof: 81 label
cells of P1's opening; 78 survive the root; the 77 betting cells contain no support (above); the
silent cell's 668 supports are 656 empty + 12 FAMILY with identities and ranges proved (this
section, control PASSED). Every prune is now either an exact certificate or an IEEE-754
interval argument with outward rounding — no tolerance carries any rounding. PAPER_KIT §7.1
has the lemmas (Nash ⇔ D-condition up to own-unreached re-choice; the DC pair; node systems
relax leaves; labels partition; FAMILY ⇒ realization-equivalent) and the corollaries (P1 never
bets; the equilibrium payoff set is the family's segment, P2's payoff `−1/48` in every
equilibrium).

## 16.8 Stored certificates and an independent checker (2026-09-20)

**Why.** Until now the prover was the checker: a leaf's verdict was one `int8` in
`symleaf_<tag>.npz`, and `EMPTY_GB` / `EMPTY_MIX` / `EMPTY_CONST` and every FAMILY identity
rested on `sympy.groebner` returning `[1]` or a normal form, with no cofactor produced or
checked. The computer-assisted-proof norm (four-colour, Kepler) is stored certificates replayed
by a small independent checker. That now exists.

**Certificates** (`certleaf.py <tag> <workers> [maxnodes]` → `cert_<tag>.json.gz`, one record per
leaf; the decision procedure is symleaf's, stage by stage):
- `EMPTY_BOX` — `certbox.prove_empty_cert`: the B&B tree. Each node: its start box (root bounds,
  or the parent's contracted box cut at the split point), the contraction trace
  (`('lo'|'hi', j, value, strict, constraint)`, or `('kill', constraint)` / `('empty', j)`),
  and, when the LP relaxation closes it, only the rows with a nonzero dual multiplier (named
  by provenance: a system row, a monotone-elimination row with the coefficient's sign
  certificate, an open endpoint, a McCormick envelope row of a product link) plus the column
  multipliers `w`. Weak duality with `b·y + U·w ≤ 1` bounds `eps' = eps + 1` on the relaxation:
  no point of the system in the box. Rows are named by origin (`D`/`0`/`1`/`DCx`/`DC1` of a
  coordinate, a derived row, a hypothesis), not carried as polynomials: ~2.7 KB per leaf.
- `EMPTY_GB` — cofactors `1 = Σ q_k e_k` (`nullcert.lift`: Macaulay system at the smallest
  degree that works, modular pre-solve then exact re-solve, identity re-expanded before it is
  returned). `EMPTY_MIX` — `1 = Σ q_k e_k + q_0 (1 − t x)` (or `1 − x`). `EMPTY_CONST` —
  `p − r = Σ q_k e_k` with the constant `r` of the wrong sign. K1b's reduced system — every
  basis element `g = Σ q_k e_k` and every normal form `p − NF(p) = Σ q_k e_k` as derived rows.
- `FAMILY` — pins by the labels; each identity either `1 ∈ ⟨E, 1 − t h⟩` with cofactors or two
  box certificates (`h > 0`, `h < 0` added as a strict hypothesis row, with the `b11 ≶ b21`
  hypothesis where the identity is split); each range a box certificate for `h > 0` or a
  cofactor reduction to a constant `≤ 0`. Reductions of `h` modulo the basis carry their own
  cofactors.

**Checker** (`checkcert.py cert_<tag>.json.gz`): Fractions on dict-polynomials, no sympy, no
scipy, no LP. It rebuilds the leaf's system from the labels and `D_all.pkl` (itself recomputed
from the game tree by `checkD.py`: 48/48 agree), constructs every named row itself, re-derives
every contraction step from the named constraint and the current box (a claimed bound may be no
stronger than the derived one), verifies each LP node by weak duality on the named rows, checks
the tree's split structure, and verifies every cofactor identity by expansion. Negative tests:
a flipped dual sign, a contraction step strengthened by one grid step, another leaf's labels, a
dropped child, a changed McCormick row type and a changed cofactor are all rejected with the
reason named.

**Results.** `silentR` (668 leaves): certificates for 668/668 in 87 s on 6 workers
(`EMPTY_BOX` 654, `EMPTY_GB` 2, `FAMILY` 12; verdict classes identical to symleaf's), verified
668/668 in 3 s. **Betting branches (09-21): every leaf set of both R ledgers certified and verified —
66,699 of 66,699 leaves (668 silent + 45,276 nash + 20,755 seq; 66,682 EMPTY_BOX, 3 EMPTY_GB,
2 EMPTY_CONST, 12 FAMILY), 0 failed, `cert_summary_R.txt`** (`certall.py R 24`; generation
~4 h on 24 workers, checking ~1 h). Two leaves needed a second look: leaf 1791 of
`a11:MIX,a21:MIX,a31:0,a41:MIX` exposed erratum 11 (below) and verifies after the fix; leaf 1793
of the same set hit the 900 s per-leaf watchdog in the Gröbner cofactor lifts and is certified by
a 5-node base-system B&B (`K0b`, now the stage before any Gröbner work).

**Two provers are better than one (2026-09-21).** Eight leaves of the seq branch
`a11:0,a21:MIX,a31:0,a41:1` (and nine of the nash one) time out in the exact LP B&B — one of
them is still open after 20,000 nodes — while `bnb6`'s interval B&B kills them in ~50 nodes
each (420 for all eight, nash-mode strong rules included). The LP relaxation sums monomial
ranges and forgets the game tree; the interval recursion keeps the shared path prefixes and
its enclosure of `D_i` is far tighter there. Conversely, at internal enumeration nodes with
many free coordinates the LP kills 39 of 40 float survivors and the tree bound none. So
`treebound.py` puts the tree recursion into the certificate prover in exact arithmetic:
`d_bounds` (the own-reach-stripped `ivl` recursion in Fractions, checked against the `D`
polynomials at sample points and exact at point boxes), `tree_rules` (the D-condition of the
labels as kill / pin rules) and `chord_contract` (bnb6's chord argument: the maximum of `D_i`
over the box with `x_v` pinned is convex in the pinned value, so it lies below the chord of
the two pinned tree bounds; excluded ranges are exact rationals, dyadically rounded outward).
`certbox` runs contraction + HiGHS LP first and the tree/chord rules only where that fails;
all eight hard leaves then die at the root in ~6 s each, certificates verified. The checker
re-derives every tree bound and every chord crossing itself (`check_tree_step`,
`check_chord_step`, ~80 lines). A second gap surfaced on a FAMILY leaf at the corner
`b11 = 1/4`: HiGHS's float duals cannot be rounded to a bound `<= 1` (they are off by ~1e-13
and the true optimum is exactly 1), so `certbox` now solves the dual LP exactly with `exlp`'s
simplex as the last resort (0.2 s there) — the same reason `exactbox.lp_infeasible` falls back
to the exact primal. Order of attempts per node: contraction, LP (HiGHS duals), tree rules,
chord contraction, LP (HiGHS), LP (exact dual), split. `symleaf.decide` now runs the same
search (`exactbox.prove_empty(..., lab, gidx)` delegates to `certbox`), so future ledgers
decide these leaves at the root instead of handing them to the interval fallback; the R
ledgers above were produced by the earlier stage and stand as recorded.

**ERRATUM 11 (2026-09-21, found by the checker).** `exactbox.lp_infeasible` built the four
McCormick rows of a product link `m = p · x_j` with a dict literal `{k: ±1, kj: ·, kp: ·}`;
for a *squared* monomial the prefix is the variable itself (`kj == kp`) and the second
coefficient silently overwrote the first, so the row `(x_h − x)(x − y_l) ≥ 0` lost its
`x_h · x` term and became unsound. The `D` polynomials are multilinear, so squares occur only
in Gröbner-reduced systems (K1b/K3a/K3b on the reduced rows, and the FAMILY identity/range
proofs after reduction) — never in the enumeration's node tests (`enumx.node_test` uses the
multilinear node system) and never at K0. The checker rejected the certificate of leaf 1791 of
`a11:MIX,a21:MIX,a31:0,a41:MIX` ("dual infeasible at a monomial column"), the only failure in
the first 34 leaf sets (≈35,000 leaves). Fixed in `exactbox` and `certbox` (`_acc`); the leaf
is EMPTY_BOX by the B&B (K3b) and verifies. Consequence for the record: a symleaf verdict of the
R ledgers is trusted only through its verified certificate; every leaf whose certificate failed
is re-derived with the fixed prover (`certall` re-run), and the certificate totals below are
the numbers the paper cites.

**What remains outside the certificates.** (i) The enumeration's internal-node exact kills
(`enumx.node_test` at every fourth level of `enuml`) are the same contraction + LP proofs but
are not recorded — recording them means re-running the enumeration with `certbox` in the
worker (~3 KB per killed node, hundreds of thousands of nodes per mode). (ii) The float prunes
(`bnb6` rules under `ivl`'s outward rounding) are rigorous IEEE-754 arguments, not
certificates; an exact replay in Fractions of every float-killed node is possible with the
recursion in `test_ivl_directed.py` but was not run. (iii) `tree.py` is the game.

### 16.8.1 A gap in the checker, closed, and everything re-verified (2026-09-26)

`check_box_cert` replayed a certificate from the starting box the certificate *declared* and
never compared that box with the node's labels.  A certificate proves that its system has no
point INSIDE its box, so a box tighter than the labels allow could "prove" a false kill by
simply excluding the solutions, and the independent checker would have accepted it.  The
prover always passed the labels' box, so this was a gap in the checking, not (as it turned
out) an error in any result -- but an independent checker must not take the box on trust.
It now requires the starting box to contain everything the labels allow (or, for the
inherited-box enumeration of §16.9, everything the node's *replayed* certified box allows);
a certificate with a tampered box is rejected.  Every stored certificate was re-verified under
the new rule (`recheck_all.py`, `recheck_summary.txt`):

| certificates | verified | failed |
|---|---|---|
| support leaves (Theorem 4) | 66,699 | 0 |
| ranges of the complete Nash set (Theorem 5) + witnesses | 522 + 322 | 0 |
| certificate trees of the third pass | 71 branches, 4,394,323 nodes | 0 |

## 16.9 Third pass: the betting side as one replayable certificate tree (2026-09-21)

**What it is.** Leaf certificates (§16.8) cover the silent branch and every leaf-bearing
branch, but 47 of the 77 nash-mode betting branches have no support at all: their proof *is*
the enumeration's node kills, exact and float. `enumc2.py` re-enumerates a branch as a
**certified label tree**: every node is (a) *killed* with a `certbox` certificate on its
D-system (the node's labels with U as the DC pair, private coordinates dropped), (b) *split*
into its three children on the first unassigned coordinate of the bet-first order, or (c) a
*leaf* with a `certleaf` certificate. The float propagation (`treesize6.propagate` under
outward rounding) is used only to decide *which* nodes to try to kill and which coordinates to
mark don't-care — a float verdict is never trusted: a float-killed node or an excluded child
label gets a certificate (contraction, LP, tree rules, chord, LP; budgets 1 then 60) or is kept
alive and split ("float-unsure"); a DC mark needs no justification (Lemma 2). `checkenum.py`
replays the tree with Fractions only: root labels = the branch spec, each split on a U
coordinate with exactly three children, each kill's system a relaxation of the node's cell
(`check_box_cert` with rows rebuilt from the labels), each leaf through `check_leaf`, every
child seen exactly once. A pure exact enumeration (`enumc.py`, no float guidance) was tried
first and grows too fast — the float contractor's *narrowing* is what keeps the tree small; the
certified version only has to reproduce its kills.

**Test.** `a11:0,a21:0,a31:1,a41:0`: 13,412 nodes (8,941 kills, 4,470 splits, 0 leaves — the
float run had 886 leaves, all of which the tree now kills earlier), 2 float-unsure nodes,
1,624 s on 8 workers; `checkenum`: **OK** in 376 s.

**Run** (2026-09-22 → 23).  `KUHN_MODE=nash KUHN_ORDER=bet KUHN_CAP=7200 python runenumc.py 20`
over the 77 branches of `branches_alive_nashR.txt`, ledger `enumc_summary_nash.txt`.  A branch
that exceeds the cap is abandoned with a PARTIAL line and its truncated output removed, so one
hard branch cannot eat the pass; a PARTIAL branch keeps the directed-rounding interval
enumeration (§16.7) as its proof, which is sound -- outward rounding makes every prune a
rigorous interval statement -- but not replayable by the checker.

**Result.**

| | branches | certified nodes | kills | splits | support leaves |
|---|---|---|---|---|---|
| verified end to end (`checkenum`: OK) | **71 / 77** | **4,394,323** | 2,927,648 | 1,464,727 | 1,877, all `EMPTY_BOX` |
| PARTIAL at the cap | 6 / 77 | -- | -- | -- | -- |

Every one of the 71 is verified by `checkenum.py` with **0 failed and 0 children never seen**:
every kill's certificate replayed in Fractions against the node's own labels, every split's
three children accounted for, every support leaf through `check_leaf`.  22.1 h of enumeration,
2.4 h of checking, on one desktop.  So for 71 of the 77 betting branches the statement "no Nash
equilibrium has P1 betting in this branch" no longer rests on floating-point arithmetic at
all, directed rounding included: it is a finite tree of exact certificates that a 450-line
Fraction checker replays.

The six PARTIAL branches, with their state at the cap:

    a11:0,a21:MIX,a31:MIX,a41:1      4 h: 53,622 kills  26,113 splits  228 float-unsure
    a11:MIX,a21:MIX,a31:0,a41:1      2 h: 29,484 kills  14,205 splits   62 float-unsure
    a11:0,a21:0,a31:MIX,a41:0        2 h: 47,660 kills  23,070 splits   33 float-unsure
    a11:MIX,a21:MIX,a31:0,a41:MIX    2 h: 109,631 kills 53,855 splits    0 float-unsure
    a11:MIX,a21:0,a31:0,a41:MIX      2 h: 52,596 kills  25,750 splits    3 float-unsure
    a11:0,a21:MIX,a31:0,a41:MIX      2 h: 123,506 kills 60,591 splits   22 float-unsure

Five are simply large (the verified branches run up to 148k nodes, and these were still
producing kills at the cap); only the first is pathological -- 228 nodes that the float
propagation kills but no certificate in the ladder reproduces, each forcing a split and a
subtree.  The cap wants choosing with care: a 1 h cap threw away a branch that needed 4,283 s
with its queue already empty.

**A retry that went backwards (2026-09-24/25).**  Retrying the six at a 12 h cap, three at a time
with 9 workers each, finished none of them -- and with far MORE float-unsure nodes than the
first attempt (234 to 1,073, against 0 to 62 in 2 h with 20 workers), and fewer kills in 12 h
than the first run made in 2.  The float-unsure count is not a property of the branch alone:
it depends on how the tree is cut into jobs (the top expansion stops at `KUHN_FRONTIER x nw`
subtrees, so fewer workers means shallower subtree roots and longer float-propagated paths below
them).  Splitting the machine across branches is therefore the wrong trade for `enumc2`: the
six are now run one at a time with 26 workers each at an 8 h cap, nearest-to-done first and the
pathological branch last (`retry_partial.py 1 26 28800`; replaced lines are kept in
`enumc_partial_history.txt`).

**Inherited certified boxes (`enumc3.py`, 2026-09-26).**  The cause of float-unsure nodes is
structural: the float propagation kills a node using a box contracted along the whole path
from the root, while every `enumc2` certificate starts again from the node's bare LABEL box.
`enumc3` certifies the contraction itself: at every split it runs `certbox.contract_traced` on
the node's own system from the node's certified box and records the steps; the children start
from the contracted box (the split coordinate set by the child's label) and every kill
certificate starts from the node's certified box.  `checkenum.py` replays each split's
contraction from the box it has itself computed for that node and requires every kill to start
from a box containing it -- sound because a child's feasible set lies inside its parent's (the
parent's DC pair is the union of the three labels) and contraction only removes infeasible
points.  Files without contraction records check exactly as before.

On a verified branch (`a11:MIX,a21:0,a31:MIX,a41:1`) the tree shrank from 43,433 nodes
(`enumc2`, 521 s) to **356 nodes (30 s)**, replayed OK.  On the six hard branches it is mixed:
on `a11:MIX,a21:MIX,a31:0,a41:MIX` 76 of 80 subtrees closed within two minutes with 574 kills
(where `enumc2` passed 113,000 kills without finishing), but on `a11:0,a21:MIX,a31:0,a41:MIX`
it went PARTIAL at 8 h with 790 float-unsure nodes -- there the float kills use more than
interval contraction (tree-structured bounds on `D`, the chord contractor), which the inherited
box does not yet carry.  The retry of the six is still running; the ledger records its outcome.

**What the six PARTIAL branches rest on.**  Their support leaves are not in question: all
25,636 of them (581 + 613 + 8,681 + 4,433 + 3,055 + 8,273) are among the 66,699 leaf
certificates replayed by `checkcert.py`.  Only the pruning *above* the leaves -- which nodes the
enumeration discarded before reaching a support -- rests, for these six branches, on the
directed-rounding interval arithmetic of §16.7, which is sound (every operation rounded
outward) but not replayed by a checker.

### 16.9.1 Exact propagation certificates: the six branches closed (2026-10-05)

**Why the certified enumeration stalled.**  Every `enumc2`–`enumc6` certificate starts from the
node's LABEL box, while the float enumeration (the R ledger) killed nodes with
`treesize6.propagate`, whose chord contractor narrows the box along the whole path from the root.
On the six branches that path contraction does the pruning.  Without it, the certified trees
reached 0.15–1.3 million kills per 8 h slice with growing queues (§16.9, RESUME), and no amount
of grinding closed them.

**The method (`xprop.py`, `enumc7.py`).**  The same propagation, in EXACT rational arithmetic
(Fractions, no float anywhere), and certified.  A node's box is derived from its parent's box with
the split coordinate set by the node's label.  Every step that narrows or closes it is recorded:

- forced values `["F", ...]`;
- chord narrowings `["C", v, [side, condition, new bound]]`;
- the closing contradiction `["K", ...]`.

Every node record carries its labels, its exact box and that certificate.  Children that
propagation closes are `pkill` records.  Every four levels a `certbox` certificate from the
node's exact box (the full ladder) may kill the node.  Leaves get `certleaf` certificates.  The
only arithmetic shortcut is that a chord's new endpoint is rounded OUTWARD to the grid 2^-60, a
weaker bound that keeps the rationals small.

**Soundness.**  Each step is a necessary condition for every Nash equilibrium in the box whose
support labels are the node's.  So no equilibrium is ever discarded.

1. *Enclosure.*  The tree recursion with exact interval arithmetic encloses V for every player at
   every node.  It also encloses the reach of every node, and `du_i` (x24) over the box.
2. *Box semantics.*  x_i > 0 forces du_i >= 0 at a Nash equilibrium (utility is linear in a
   player's own x_i).  So lo_i > 0 or label MIX requires du_i >= 0, and symmetrically for hi_i < 1.
   A violated requirement closes the box.
3. *Strong rules.*  du_i > 0 on the whole box forces x_i = 1, and du_i < 0 forces x_i = 0.
4. *Weak rules, only where the labels prove the set reached.*  Some node of the set has a path
   whose aggressive edges are labelled 1/MIX and passive edges 0/MIX, so its reach is positive.
   If the per-node value difference is > 0 at all 6 nodes, then du_i > 0, hence x_i = 1.  Sound
   for every Nash equilibrium.
5. *Chord (convexity lemma).*  Pin x_v = lo_v + w t, t in [0, 1], and let U_i(t) be the
   recursion's upper bound on du_i.  Then U_i is convex in t.  In one deal a coordinate occurs at
   most once on a root-to-leaf path (each player meets each situation once).  So:
   - at x_v's own node, the value bound is affine in t;
   - above it, each value bound is a nonnegative combination of the children's bounds, maximised
     over the other coordinate's endpoints.  Upper bounds stay convex and lower bounds concave;
   - Dh = Ahi − Plo is therefore convex;
   - a reach bound below x_v's node is affine and nonnegative in t;
   - each node's term is f(Dh), with f(D) = rh·D for D >= 0 and rl·D for D < 0 (rh >= rl >= 0).
     Above x_v's node, f is convex and nondecreasing and Dh is convex, so the term is convex.
     Below it, the term is affine.  A sum of convex terms is convex.

   So U_i lies below its chord on [0, 1].  Where the chord through (0, U_i(0)) and (1, U_i(1)) is
   negative, du_i >= 0 is impossible.  If both ends are negative, it is impossible on the whole
   box.  Symmetrically, the lower bound is concave, which handles du_i <= 0.
6. *Labels.*  lo_i >= 1 implies label 1, and hi_i <= 0 implies label 0.  A coordinate whose reach
   bound is 0 at all six nodes is marked DC (Lemma 2).  A MIX coordinate whose box has no
   interior is a contradiction.

*Propagation and D-certificates together.*  Propagation uses the reach-weighted Nash conditions,
and box certificates the own-reach-stripped D-system.  Take any Nash equilibrium p.  Re-choosing p
optimally at the information sets its owner never reaches gives a p' with the same on-path play.
p' is still Nash, so propagation keeps it.  p' satisfies the D-system everywhere, so no
certificate excludes it.  The labels' tree covers p''s labels.  Hence p' lies in a leaf, and the
on-path conclusions (Theorem 4) hold for p.

**The independent checker (`xcheck.py`, `checkenum2.py`).**  It is written separately from the
prover.  It imports only the game definition (`tree.py`) and Fractions: not `ivl`, `bnb6`,
`treesize6` or `xprop`.  Its interval recursion runs over an explicit per-deal game tree.  Every
node is checked from its parent's record alone, so the checks run in parallel:

- the propagation certificate must replay from the parent's box, as the node's label sets it, to
  a box CONTAINED in the recorded one (or close it, for `pkill`);
- the node's labels must be exactly those the box implies, plus its DC marks;
- a kill's `certbox` certificate must start from a box CONTAINING the node's box;
- coverage: every child of every split must be seen exactly once.

By induction down the tree, every recorded box is sound.

**Controls.**

| control | result |
|---|---|
| prover and checker on 417 children along random walks of three hard branches | identical verdict and box for **417 / 417** |
| exact against float propagation along random paths | every float kill reproduced (**178 / 178**); exact box always inside the float box; exact stronger at 83 further children |
| tampered certificates, each confirmed invalid by the PROVER's engine as oracle: a chord bound pushed one grid step, a chord or kill attributed to another condition, a flipped force, an invented force | **2,463 / 2,463 rejected** |
| 64 certified equilibria (`certified_eq_all.npy`) followed down the exact tree | none discarded; every box contains its point; no layer certificate kills its node: **PASS** |
| the P1-silent branch, `enumc7` + `checkenum2` | 4,723 nodes, **OK**; 79 leaves = 67 EMPTY_BOX + **12 FAMILY**: the R ledger's 12 FAMILY leaves, **identical label patterns, one to one** |
| small branch `a11:MIX,a21:1,a31:MIX,a41:0` | 40 nodes (enumc2: 3,188), **OK** |

**The six branches** (`run_enumc7.py 20 branches_enumc7.txt`, ledger `enumc7_summary_nash.txt`):

| branch | nodes | split | pkill | kill | support leaves | checker | enum | check |
|---|---|---|---|---|---|---|---|---|
| `a11:0,a21:MIX,a31:MIX,a41:1` | 97 | 32 | 8 | 57 | 0 | **OK** | 126 s | 1 s |
| `a11:MIX,a21:MIX,a31:0,a41:1` | 2,722 | 907 | 1,186 | 629 | 0 | **OK** | 1,039 s | 53 s |
| `a11:0,a21:0,a31:MIX,a41:0` | 2,167 | 722 | 614 | 831 | 0 | **OK** | 703 s | 39 s |
| `a11:MIX,a21:0,a31:0,a41:MIX` | 9,205 | 3,068 | 3,369 | 2,676 | 92, all `EMPTY_BOX` | **OK** | 2,256 s | 175 s |
| `a11:MIX,a21:MIX,a31:0,a41:MIX` | 5,362 | 1,787 | 1,806 | 1,656 | 113, all `EMPTY_BOX` | **OK** | 1,599 s | 109 s |
| `a11:0,a21:MIX,a31:0,a41:MIX` | 6,670 | 2,223 | 2,051 | 2,140 | 256, all `EMPTY_BOX` | **OK** | 2,435 s | 214 s |
| **total** | **26,223** | 8,739 | 9,034 | 7,989 | 461, all empty | **6 / 6 OK** | 2.3 h | 10 min |

Every node is verified, with 0 failed and 0 children never seen.  The `enumc2`–`enumc6` label-box
enumerations had reached up to 1.3 million kills on single branches without finishing.  The exact
propagated box is what closes them.  The failure of 2026-09-24 to 10-05 was the starting box, not
the size of the problem.

**The betting side is now closed with no float arithmetic anywhere.**  71 of the 77 nash-mode
branches are verified by `enumc2` + `checkenum` (§16.9) and the remaining 6 by `enumc7` +
`checkenum2`.  Every claim in every tree is an exact certificate replayed by a Fraction-only
checker.  The paragraph above on "what the six PARTIAL branches rest on" is superseded: they no
longer rest on directed-rounding interval arithmetic.

**Cross-check: all 77 by the second method too (2026-10-05/06).**  `run_enumc7.py 26
branches_enumc7_all.txt` re-derived the 71 `enumc2`-verified branches with `enumc7` + `checkenum2`.
Over all 77 betting branches (`enumc7_summary_nash.txt`):

| | branches | nodes | support leaves | failed | missing | enum | check |
|---|---|---|---|---|---|---|---|
| `enumc7` + `checkenum2` | **77 / 77 OK** | 33,104 | 462, all `EMPTY_BOX` | 0 | 0 | 3.7 h | 0.2 h |

The 71 took 6,881 nodes, against `enumc2`'s 4,394,323 for the same branches.  So every betting
branch is now closed by **two independent certified methods**, each with its own checker:
label-box certificate trees (`checkenum`, 71 branches) and exact propagation certificate trees
(`checkenum2`, all 77).  Both say the same thing: no Nash equilibrium has P1 betting.

## 16.10 The complete Nash set, off path included (2026-09-21)

The 12 FAMILY leaves' D-systems are the whole Nash set (PAPER_KIT Theorem 5): `S_ℓ` = the leaf's
labels + the D-condition everywhere, with P2's own-unreached `b43`, `b44` freed in the two leaves
with `b41 = 1`. `nefull.py` writes the systems in reduced form (`nefull_systems.txt`) and the
exact range of every MIX / constrained-DC coordinate over every leaf (`nefull_ranges.txt`),
each bound an emptiness certificate `{S_ℓ, x_v > T}` (or `< T`) checked by `checknefull.py`
and, where attained, an exact rational witness point of the leaf verified by exact evaluation.
What the systems show:

- every constrained off-path coordinate (`a44`, `b12`, `b22`, `b32`, `b42`, `b44`, `c13`,
  `c14`, `c23`, `c24`, `c33`, `c34`, `c43`, `c44`, and in the three corner leaves also `a13`,
  `a14`, `a23`, `a24`, `a33`, `a34`, `a43`, `c12`, `c22`, `c32`, `c42`) has `D ≡ 0` on the leaf —
  its own incentive is vacuous; it is constrained **only through other players' deterrence
  inequalities**: P1's four `D_{a_j1} ≤ 0` (never in P1's interest to bet card `j`), and where
  `b_j1 = 0`, P2's `D_{b_j1} ≤ 0`, plus a few sign-determined pins such as
  `D_{a32} = −(5 b44 − 4)/48 ≤ 0 ⟹ b44 ≥ 4/5`;
- every private coordinate (`b24`, `a24`, `b44`, `b14`, `a14` depending on the leaf) has
  `D ≡ 0` and appears in no inequality: free in `[0, 1]`;
- the deterrence inequalities are bilinear in (P2's, P3's) off-path coordinates — the same
  polynomials in every leaf, with the leaf's parameters substituted.

Ranges: PAPER_KIT §7.2 Table 4 (generated by `ranges_table.py` from `nefull_ranges.txt`;
522 range certificates verified, 322 with attained witnesses after the refinement pass
`nefull_refine.py`, which tightened 110 of the 133 undecided bounds; `checknefull.py`: 522 / 522
certificates and 322 / 322 witnesses verified).

## 16.11 (3, 5)-Kuhn: the instrument on the next game (2026-09-21)

`k35/` is the instrument with the card count as a parameter (`KUHN_CARDS`, 60 coordinates,
60 deals, 12 nodes per coordinate; `kuhn3p`, `tree`, `ivl`, `bnb6`, `treesize6`, `symbet`,
`enumx`, `enuml`, `symleaf`, `certbox`, `treebound` copied and generalised; with
`KUHN_CARDS=4` the copy reproduces the original bit for bit — identical `ivl` bounds, identical
78 / 81 root cells, identical `D_all`). `makeD.py` computes the 60 gradients exactly from the
tree (2,807 terms); `rootcells.py`: **240 of 243** P1-opening cells survive the root in nash
mode (105 s); `runcells.py` runs the layered enumeration on every cell with a wall-clock cap.

**The sweep, complete.**  `KUHN_CARDS=5 KUHN_MODE=nash KUHN_ORDER=bet python runcells.py 8 1 900`
over the 239 P1-betting cells (the 240th is the silent cell, which the driver excludes),
ledger `cells_summary_5.txt`: **190 decided inside the 15-minute cap** (mean 223 s) and
**49 timed out**.  189 of the 190 have **no support at all**; the one that does --
`a11:1,a21:1,a31:1,a41:1,a51:1`, P1 betting every card -- has a single leaf that the exact
stage kills (`EMPTY_BOX`).  So **no cell the sweep decided carries an equilibrium in which P1
bets**, which is the (3, 5) analogue of the result this paper proves for four cards, on 79 % of
the cells.

**How big the rest are** (`estcells.py`, Knuth's unbiased estimator on the same label DFS,
reporting both the leaf count and -- summing the running product along the path -- the NODE
count, which is what predicts runtime):

| cell | leaves ~ | nodes ~ | vs the 4-card control |
|---|---|---|---|
| 4-card silent branch (control; true: 668 leaves, 2,835 exact tests, 1,462 s) | 1.65e3 ± 1.1e3 | **1.59e4 ± 4.2e3** | 1x |
| `a11:0,a21:0,a31:0,a41:1,a51:0` (P1 bets only the best card) | 2.60e4 ± 2.2e4 | **2.46e6 ± 2.3e6** | ~150x |
| `a11:MIX,a21:0,a31:0,a41:0,a51:1` (P1 bluffs card 1) | 0 (0 of 200 walks reach a leaf) | **1.21e7 ± 3.3e6** | ~760x |

**Verdict.**  The instrument ports to (3, 5) unchanged and decides 79 % of the cells in minutes,
but the cells where P1 actually bets -- the ones Part 9's MCCFR points at -- are 150x to 760x
the 4-card silent branch in nodes, so each needs days rather than the 15 minutes it was given,
and the second cell above suggests they are *empty* (no walk of 200 reached a leaf) rather than
rich.  (3, 5) is reachable cell by cell with this code and a longer clock; an exhaustive sweep
needs a faster per-node step (the propagation is 60 coordinates over 60 deals) or a cluster.
The 15-minute cap, not the method, is what leaves the 49 cells undecided.

**The exact-propagation method on (3, 5) (2026-10-06).**  The method that closed the 4-card
betting side (§16.9.1) ports to `k35/` (`xprop.py`, `enumc7.py`; NP = 60 coordinates):

- with `KUHN_CARDS=4`, it reproduces the 4-card `xprop` bit for bit, certificates included (87
  children);
- with 5 cards, the dependency and certainly-reached sets match `bnb6` / `treesize6`;
- exact propagation reproduces every float kill (60 / 60) with every exact box inside the float
  box, at 1.8 s per child.

It does NOT bring the 49 cells into reach.  On `a11:MIX,a21:0,a31:0,a41:0,a51:1` (the cell
above, Knuth 1.21e7 nodes), three layer-test policies ran side by side for 90 min on 9 workers
each (`ab_k5.py`):

| layer ladder | nodes | open jobs at 90 min | failed layer tests |
|---|---|---|---|
| full | 1,190 | 327, growing ~200/h | 61, ~500 s each |
| rung 0 | 5,038 | 1,705, growing faster | 350 |
| rungs 0, 2 | 3,711 | 1,514, growing faster | 269 |

None finished, and no support leaf was reached in any of them.  On 4 cards `enumc7` needed about
0.3x the Knuth node estimate (4,723 against 1.59e4 on the silent branch).  That puts this cell at
roughly 3.6 million nodes, which at the full arm's rate (~2,350 nodes/h on 26 workers) is about
two months, and the other 48 cells at weeks each.  The 5-card propagation is as faithful as the
4-card one but much less decisive: interval bounds over 60 deals are looser, and a failed
full-ladder layer test costs ~500 s with 60 coordinates.  **An exhaustive (3, 5) certification
needs a stronger per-node bound, not more time on one desktop.**

### 16.11.1 (3, 5) HAS an exact Nash equilibrium in which P1 bets (2026-10-07)

**Search (evidence only).**  `polish35.py` regenerated Part 9's MCCFR (`cfrGen` on
`kuhnGen.Kuhn(3, 5)`, 20 seeds × 10^7 iterations, 1,317 s; P1 opening up to 0.85).  It then
polished each seed: Newton on the interior support with greedy support repair.  **7 of the 20
seeds** (0, 3, 6, 8, 12, 13, 14) reach the SAME equilibrium at float exploitability ~1e-16:

- 17 interior coordinates, the other 43 exactly 0 or 1;
- **P1 opens cards 1 and 2 at 0.1615, card 3 at 0.0404, card 5 at 0.8478, and never card 4.**

The other 13 seeds lost their support in the crude greedy repair.  At 420 digits (`hiprec35.py`)
the Jacobian has exactly one null direction, (c11, c21) ∝ (1, −1): P3's card-1 and card-2 openings
matter only through their sum.  With c11 = 3/10 the rest is determined:

- `b11 = b21 = (11 + √13)/72` and `c32 = 4 − √13`;
- the other 12 coordinates are algebraic of degree > 8 (no minimal polynomial of degree ≤ 8 with
  coefficients ≤ 10^45, none in ℚ(√13) with coefficients ≤ 10^120).

So there is no closed form, and the proof is an existence proof.

**The certificate (`k35/cert35.py`), exact rational arithmetic throughout.**

1. Every condition is built from k35's tree as an exact polynomial over the 17 interior
   coordinates, with the 43 pure coordinates at 0/1.
2. Checked as polynomial identities: on the subspace a21 = a11, b21 = b11, every condition depends
   on c11, c21 only through s = c11 + c21, and the conditions of a11/a21, b11/b21 and c11/c21
   coincide.  So the 17 conditions are exactly 14 equations G(y) = 0 in the 14 unknowns
   y = (A = a11 = a21, B = b11 = b21, s, a31, a32, a43, a44, a51, b33, b42, b44, c32, c33, c41).
   The game's card-1/card-2 symmetry holds here because nobody calls with card 1 or 2, so the two
   never meet at showdown.
3. **Krawczyk** on the box Y = m ± 10^-30 (m = the 73-digit solution, rational), with an exact
   interval enclosure of the Jacobian over Y: **K(Y) ⊂ int(Y)** (contraction ratio 3.5e-29).  So G
   has exactly one zero y* in Y.
4. **Nash.**  For all 60 coordinates the one-shot D-condition holds at y*.  The 17 interior ones
   satisfy du_i = 0 (the equations) with own reach > 0 on Y, hence D_i = 0.  All 43 pure ones have
   D_i < 0 (at 0) or > 0 (at 1) on the whole of Y, by exact interval evaluation, with 0 violations.
   D-conditions at every information set imply Nash (one-shot deviation principle in each
   player's own tree).
5. **P1 bets:** a11 = a21, a31 and a51 are bounded away from 0 on Y.

**Re-checked independently** by `k35/cert35check.py`, with no sympy.  It uses its own Fraction
dict-polynomials built from the tree, its own substitution, differentiation and interval
evaluation.  The identities, Krawczyk, 0 D-violations and P1 > 0 all agree.  **Negative
controls:** the box centre moved by 10^-25, and a pure coordinate flipped (a42: 1 → 0), are both
REJECTED by Krawczyk.  **Positive control** of the exact Nash verifier `xeq35.py`: the 4-card
off-path witness gives exploitability exactly (0, 0, 0), and its `b12 := 0` variant exactly
(1/300, 0, 0).  The kuhnGen → k35 coordinate mapping is checked to 1e-15 on random profiles.

**The equilibrium** (`k35/cert35_equilibrium.txt`):

- payoffs u = (−0.0350070, −0.0013126, +0.0363196);
- P1: bluffs cards 1–2 at 0.1615, card 3 at 0.0404, value-bets card 5 at 0.8478, never bets 4;
- P2: bets cards 1 and 2 after a check at 0.2029;
- P3: opens card 1 at 3/10 and card 2 at 0.3295 (only their sum is pinned), and always with card 5.

It lies in the cell `a11:MIX,a21:MIX,a31:MIX,a41:0,a51:MIX`, one of the 49 the exhaustive sweep
left undecided.

**What this settles.**  Open problem 3 (the N = n + 1 law), for (3, 5).  With a non-minimal deck,
P1 DOES bet in equilibrium, as Part 9's MCCFR separation (P1 opening 0.76–0.85 when N > n + 1)
suggested, now as an exact theorem.

### 16.11.2 (3, 5): the betting equilibria form continua, with DIFFERENT payoffs (2026-10-07)

`q2_polish35.py` re-polished all 20 MCCFR seeds: Newton on the certified support, else a
distance-ordered support search around the seed's own reading.  15 of 20 float-certify, showing
three P1 behaviours.  Each was then certified EXACTLY:

- `k35/cert35gen.py`: general Krawczyk.  Conditions that are identical polynomials, or identically
  0, are dropped and re-derived.  Off-path coordinates are fixed by their D-sign (`name=p/q`).
  Free directions are fixed as parameters whose conditions stay equations (`name:=p/q`).
- `k35/degen35.py` finds the degeneracies (null rows and columns) that tell which to use.

| component | P1 opens (cards 1–5) | payoffs (u1, u2, u3) | exact status |
|---|---|---|---|
| **I** | 0.1615, 0.1615, 0.0404, 0, 0.8478 | (−0.03501, −0.00131, +0.03632) | **a segment**: c11 ∈ [0, 29/50] with c21 = s* − c11, s* ≈ 0.6295, all certified (`cert35seg.py`).  P1 and P2 play identically along it.  The control c11 ≤ 3/5 FAILS on a22 as predicted (the end is at c11 ≈ 0.5838) |
| **III** | 0.1592, 0.1592, 0.0390, 0, 0.8341 | (−0.03629, −0.00108, +0.03737) | a branch leaving I at c11 = 0, on which b11 ≠ b21.  A one-parameter family: free direction b11 − b21, and P1's card-1 and card-2 conditions are identical polynomials.  Certified at b11 = 27/200 |
| **II** | **0.3227, 0, 0.0365, 0, 0.8381** (only card 1 bluffs) | (−0.03921, **+0.00160**, +0.03762) | isolated (up to P2's off-path b53, b54, set to 1 by D-sign).  Certified; D_a21 ≡ D_a11 as polynomials, so a21 = 0 is exactly indifferent |

Two observations:

- **The equilibrium payoffs of (3, 5) are not unique.**  P2 gets −0.00131 on I, −0.00108 at the
  certified point of III, and +0.00160 at II, and they vary continuously along III.  With 4 cards
  every equilibrium pays P2 exactly −1/48.
- **The betting set is not symmetric under swapping cards 1 and 2.**  II's mirror image (only
  card 2 bluffs) is NOT an equilibrium: exploitability 9.2e-4 and 6.5e-3 after polishing.  Card 2
  beats card 1 at showdown.

Not settled:
- whether these are ALL the betting equilibria.  Five seeds stayed at exploitability ~1e-3, two
  of them near II's mirror, and an exhaustive answer needs the 49 cells (§16.11);
- where III's branch ends.

### 16.11.3 (3, 5): no P1-silent equilibrium found -- deterrence fails by a fixed margin (2026-10-07)

MCCFR on the RESTRICTED game (P1's openings fixed at 0; `silent35.py`, 20 seeds × 10^7), then
Newton on the check-subgame (`silent35b.py`).  This replaces a first attempt whose support repair
judged the full-game exploitability, which was dominated by P1's undeterred opening, and so
destroyed every support.  Results:

- **7 of 20 seeds reach a check-subgame equilibrium** to float precision: P1's exploitability among
  never-opening plans, and P2's and P3's, all ~1e-16.
- **For every one of them, no responses to a bet deter P1.**  In a P1-silent profile the 15
  responses to a bet are off-path, so Nash leaves them free to be chosen to deter.  Minimising P1's
  best opening gain over them (multistart SLSQP) leaves **+0.02631**, the same from every seed and
  start.  At the optimum P1's gains with cards 1, 2 and 5 are balanced at +0.0263: calling deters
  bluffs and feeds the value bet, and folding does the reverse.
- Sanity check: the same gain function gives exactly 0 on the opened cards of the certified
  betting equilibrium, and −0.0207 on its closed card 4.

**Status: evidence, not proof.**  A proof that (3, 5) has NO P1-silent equilibrium must cover
every check-subgame equilibrium.  The exact label enumeration of the silent cell does exactly that,
because P1's opening D-condition with the off-path responses as variables is part of its system.
It is running (`k35/enumc7.py` on `a11:0,a21:0,a31:0,a41:0,a51:0`) and needs the 5-card checker
port to be a certificate.  For a GIVEN check-subgame equilibrium, infeasibility of deterrence has a
finite exact certificate: the gains are multilinear in the 15 responses, so a weighted sum is
minimised at one of the 2^15 vertices of the cube.

**The exhaustive route is out of reach (2026-10-07 night).**  The silent cell ran under `enumc7` for
12,707 s on 22 workers (task `PokerK35Silent`, resumable from `k35/enumc_k5c7_silentN.ckpt`): 12,853
nodes (5,208 splits, 3,626 propagation kills, 4,019 certificate kills) and **0 support leaves**,
but the queue was still growing (2,729 jobs).  A Knuth estimate on the float label DFS (`estcells.py`,
300 walks) puts the cell at **2.6e7 ± 1.7e7 nodes**, larger than the betting cell probed in §16.11
(1.2e7).  At `enumc7`'s ~0.3 of the float tree and ~3,600 nodes/h that is about three months, so the
run was stopped.

So "(3, 5) has no P1-silent equilibrium" stays a well-supported CONJECTURE:
- every one of 20 restricted MCCFR runs (7 polished to float precision) leaves P1 a deterrence gap
  of ~+0.026;
- the exhaustive enumeration met no support leaf in its first 12,853 nodes.

Proving it needs either a much stronger per-node bound, or an analytic reduction of the
check-subgame equilibria (as Table 2/3 did for 4 cards) followed by the finite vertex certificate
of deterrence infeasibility.

## 16.12 Refinements — what the machinery decides and what it does not

The seq-mode ledger (weak rules: an action strictly better at every node of its information
set for every profile in the box must be played — sound for sequential, hence perfect and
proper, equilibria) is complete: 32 / 32 betting branches empty, and the seq-mode silent
enumerations reach the same 12 FAMILY leaves. So every sequential equilibrium lies in the 12
systems of §16.10. Deciding *which* points of those systems are sequential (consistent beliefs),
perfect (limits of trembling-hand equilibria) or proper is not a support question and the
enumeration does not do it; PAPER_KIT R11–R13 decide properness on the family by hand
(Theorem 3), and open problem 2 (normal-form vs extensive-form properness) stands. The natural
next step with this machinery is to write each refinement as a semi-algebraic condition on the
12 systems (for perfection: the deterrence inequalities holding for a sequence of fully mixed
perturbations) and decide it with the same certificates.

## 16.13 Refinements decided exactly: the sequential set, and open problem 2 (2026-09-22)

§16.12 said the enumeration does not decide which points of the 12 systems are sequential,
perfect or proper, and that the next step was to write each refinement as a semi-algebraic
condition and decide it with the same certificates.  That is done (`refine.py`, `seqset.py`,
`seqrun.py`).  The instrument is the same one the whole paper uses -- exact rational arithmetic,
emptiness certificates, verified witnesses -- applied to the belief system instead of the
profile.

**The bridge.**  `symbet.build_D` already gives, per coordinate `v`, the own-reach-stripped
gradient `D_v` = sum over the nodes of `v`'s information set of (other players' reach) x (value
difference).  Divide by the reach `R_v` of the same nodes and `D_v / R_v` is exactly the value
difference under the beliefs the profile induces.  At a REACHED set that is the Nash condition.
At an UNREACHED set both vanish, and along a tremble

    x_w = eps * r_w   where the profile plays 0,     x_w = 1 - eps * r_w   where it plays 1,

both are polynomials in eps whose leading coefficients `A_v(x, r)`, `B_v(x, r)` give

    lim_{eps -> 0}  D_v / R_v  =  A_v / B_v ,

the belief-weighted value difference -- and the ratios `r` are shared by every information set
at once, which is precisely Kreps-Wilson consistency.  Sequential rationality is then a SIGN
CONDITION ON `A_v`, polynomial in the profile and linear in `r`.  So:

  * for a fixed profile, "is this point sequential?" is one exact LP in `r` (`is_sequential`):
    `max m` s.t. the sign conditions, `r >= m`, and `sum r = 1` **within each information
    set's trembles** (every leading coefficient is homogeneous in one set's ratios, so the sets
    scale separately -- see the normalisation note below).  `m > 0` gives an explicit
    consistent belief system; infeasible is a Farkas certificate that no consistent belief
    supports the point;
  * trembles of different orders are the boundary `r_w = 0`, and they are covered completely by
    enumerating the ordered partitions of the trembling coordinates (`seq_orderings`): in a
    linear leading form only the lowest class survives, so 75 orderings of P1's four openings
    exhaust the belief freedom that matters here;
  * because every information set of this game is BINARY, van Damme's extensive-form
    properness, Selten's extensive-form perfection and agent-normal-form perfection coincide
    (PAPER_KIT Lemma R1), so one computation decides all three, and only NORMAL-form properness
    (Theorem 3) can select more.

**Belief-free forcing (dominance).**  *Corrected 2026-09-26: an earlier version said eight.*
EIGHTEEN coordinates are settled with no tremble analysis at all, by exact dominance --
`D_v = c * R_v` identically as polynomials, i.e. the same value difference at every node of the
set, under every belief and against every profile.  The first version of this section tested
for one-signed coefficients of `D_v`, which misses every case where the reach `R_v` itself has
mixed-sign coefficients (its `1 - x` factors); testing the identity directly (`seqcert.dominance`,
`checkseqcert` re-derives it from the tree) finds the full set.  It is the same six decisions for
each player:

| coordinates | `D_v / R_v` | forced | Nash window (Table 4) |
|---|---|---|---|
| `a12`, `a13`, `b13`, `c12` | `-1` | `= 0` | already pinned to 0 by Nash |
| `a14`, `a24`, `c14`, `c24` | `-1` | `= 0` | `[0, 1]` each |
| `b14`, `b24` | `-1` | `= 0` | `[0, 1]` (private: in no Nash inequality) |
| `b12`, `c13` | `-1` | `= 0` | `[0, 0.4173]`, `[0, 0.5269]` |
| `a43` | `+4` | `= 1` | already pinned to 1 by Nash |
| `b43`, `c43` | `+4` | `= 1` | `[0, 1]`, `[0.7750, 1]` |
| `a44`, `c44` | `+5` | `= 1` | `[0, 1]` each |
| `b44` | `+5` | `= 1` | `[17/32, 1]` |

Thirteen of the eighteen have a nontrivial Nash window and eight of them the WHOLE of `[0,1]`:
sequential rationality alone -- any refinement at all -- collapses thirteen dimensions of the
equilibrium set to points.  (`b42 = 1` is not exact dominance but follows the same way:
`D_{b42} / R_{b42} >= 4` everywhere, a robustly one-signed leading form.)

**Per-leaf closure** (`refine.closure`: substitute what is forced, recompute the leading
coefficients, repeat).  7 to 12 coordinates per leaf, including `b44 = 1` everywhere,
`b24 = 0`, `b14 = 0` (the coordinates §16.10 found free in `[0,1]` because they appear in no
Nash inequality at all) and `b43 = 1` in leaves 70 and 440.

**The off-path conditions are the same at all twelve leaves.**  After the dominance closure the
leading coefficients of the unreached coordinates are leaf-independent -- the leaf only enters
through the reached (order-0) conditions:

    A_b32 = (3 r_a11 + 3 r_a21 - 2 r_a41) / 24
    A_c34 = (r_a11 (5 b22 - 1) - b22 r_a41 - r_a21) / 24
    A_b22 = (r_a11 (3 - 5 c34) - 2 r_a31 - 2 r_a41) / 24
    A_c33 = (4 (1 - b22) r_a11 + 4 r_a21 - (2 - b22) r_a41) / 24
    A_c43 = (2 (r_a11 + r_a21 + r_a31) - b22 (r_a11 + r_a31) - b32 (r_a11 + r_a21)) / 6
    A_c13 = (b22 (r_a31 + r_a41) + b32 (r_a21 + r_a41) - r_a21 - r_a31 - 2 r_a41) / 24
    A_c23 = (4 (1 - b32) r_a11 + b32 r_a41 - r_a31 - 2 r_a41) / 24

Seven linear forms, identical at all twelve leaves (`c43`, `c13`, `c23` are quoted below with
`b32 = 0` already substituted, which the first bullet proves).  Only the terms of the LOWEST
tremble class survive in each, so these forms plus the Nash windows of Table 4 decide the
off-path structure:

  * **`b32 = 0`.**  `b32` interior needs `2 r_a41 = 3(r_a11 + r_a21)` and `c33` interior needs
    `(2 - b22) r_a41 = 4(1 - b22) r_a11 + 4 r_a21` -- R11's knife-edge `r_a41 = 2(r_a11+r_a21)`
    at `b22 = 0`.  At `b22 = 0` the two are incompatible, and at any ordering in which one of
    `{a11, a21}`, `{a41}` is strictly larger the surviving form of `A_b32` is one-signed, so
    `b32` is never interior; `b32 = 1` is outside the Nash window (`b32 <= 15/16`).  Checked
    exhaustively over all 75 orderings of P1's four openings (`seq_orderings`).
  * **`c43 = 1`, `c13 = 0`** -- exact dominance (`D = 4R`, `D = -R`); no belief argument is
    needed.  (An earlier version derived them from coefficient bounds of the leading forms over
    Table 4's windows, `forcecheck.py`; that is correct but unnecessary.)
  * **`c34 = 0`.**  If `c34 = 1` then `A_b22 = -(2 r_a11 + 2 r_a31 + 2 r_a41)/24 < 0`, forcing
    `b22 = 0`, and then `A_c34 = -(r_a11 + r_a21)/24 < 0`, contradicting `c34 = 1`.
  * **`c33 >= 1/2`, always.**  With those four settled, P1's deterrence at card 2 reads
    `A_a21 = -(2 c33 - 1)/12 <= 0`.  Since `c33 <= 15/16 < 1`, `c33` is interior in every
    sequential equilibrium, so the belief always sits on the knife-edge
    `(2 - b22) r_a41 = 4(1 - b22) r_a11 + 4 r_a21`; P1's card-1 deterrence
    `2 c33 (1 - b22) + 2 b22 + 2 c23 >= 1` then follows from `c33 >= 1/2`.

What is **not** collapsed: only `c23` and `c33`.  `b22` interior needs
`3 r_a11 = 2(r_a31 + r_a41)`, which with the knife-edge forces `b22 > 2/5`, and the refined
system certifies `{b22 >= 2/5}` empty -- so **`b22 = 0`** as well; `seqrun` kills both
`b22 = mix` patterns outright at every leaf.  `c23` interior needs `4 r_a11 = r_a31 + 2 r_a41`,
which with the knife-edge forces `r_a21 = r_a31 = 0`: P1's card-2 and card-3 trembles
infinitely smaller than the others, which Kreps-Wilson consistency allows and an exact witness
realises (`c23 = 1/32` at `b11 = 0`, `b21 = 3/16`, `c11 = 1/2`, ordering `a11, a41 >> a21 >> a31`).
Those points have no uniform inward direction, so they are the candidates for "sequential but
not perfect".

**The normalisation that decides it.**  Each leading coefficient is homogeneous in the trembles
of ONE information set, so the ratios must be normalised set by set (`sum r = 1` per set), not
globally.  With a single global simplex a whole set's ratios may go to zero, the leading forms
that see only that set become `0 = 0`, and the case is undecidable at this order: under the
global normalisation 28 of the 12 leaves' patterns came back undecided, under the per-set one
the same patterns die instantly with certificates.

**What `c33` is left with.**  `c33 >= 1/2` is exact and unconditional, and the Nash upper
bound `c33 <= 1/2 + (3/4)(b11 + b21) + beta/4` (Table 3, `beta = max{b11,b21}`) is untouched by
the refinement, so over the whole sequential set

    c33 in [1/2, 15/16]   -- exactly the upper half of the Nash window [0, 15/16],

attained: at the parameter corner `b11 = b21 = 1/4` (leaf 70, `b41 = 1`) every value from
`1/2` to `15/16` is sequential, and at the corner sub-families `b11 = b21 = 0` (leaves 18, 211)
the window collapses to the single point `c33 = 1/2` -- R11's last table row, now exact.
So the refinement halves the one window it cannot close.

**Open problem 2, answered for this game.**  At `b11 = b21 = 1/8`, `c11 = 1/4` (leaf 469) the
Nash window is `c33 in [1/2, 23/32]`; every point of it is sequential (explicit positive beliefs,
e.g. `r_a11 = r_a21 = r_a31 = r_a12 = r_a22 = r_a32 = r_c12 = r_c22 = r_c32 = 1/13`,
`r_a41 = 4/13`), and every interior point is PERFECT: `refine.perfect_cert` exhibits an inward
direction with `s* = 3715/28782 > 0`, every first-order condition strict except `c44`'s, which
holds on the whole cube, and the indifference Jacobian of full rank 8, so the implicit function
theorem turns the direction into a curve of completely mixed profiles against which the profile
is a best reply.  The two endpoints are exactly the two poles (`a21`'s and `a41`'s deterrence
going tight) and are undecided at first order.  So extensive-form properness leaves `c33` an
interval of width `7/32`, while normal-form properness (Theorem 3) picks the single point
`c33 = lo + w/3 = 55/96` inside it: **the two notions differ here, and the gap is computed, not
conjectured.**

**Run.** `seqrun.py 6` enumerates, per leaf, the 0 / 1 / interior patterns of the unreached
coordinates, kills a pattern with a `certbox` emptiness certificate or witnesses it with an
exact profile plus an exact positive belief vector (`seq_<leaf>.json`, `seq_summary.txt`):

| | patterns (first run) | excluded | sequential (exact witness) | undecided |
|---|---|---|---|---|
| 9 generic leaves (`b22`, `c23`, `c33` decided) | 99 | 81 | 18 | 0 |
| 3 corner leaves (10 coordinates decided) | 299 | 296 | 3 | 0 |
| **total** | **398** | **377** | **21** | **0** |

**Every pattern is decided.**  Exactly three survive, and each is the same at every leaf of its
kind:

    generic leaves:  b22 = 0,  c23 = 0,         c33 interior              (all 9 leaves)
                     b22 = 0,  c23 interior,    c33 interior              (all 9 leaves; needs
                                                                           trembles of different orders)
    corner leaves:   a33 interior, a34 = 0, c32 = 0, b22 = 0, c23 = 0, c33 interior   (all 3)

Every witness is a profile in exact rationals together with an exact belief vector and, where it
needs them, the relative tremble orders; `checkseq.py` -- an independent checker that rebuilds
the leading coefficients from the tree and re-tests every condition in Fractions -- verifies
**21 / 21, 0 failed**.

**Independently replayed** (2026-09-26, `seqcert.py` + `checkseqcert.py`).  An earlier version
of this section said "killed with certificates" when the exclusions were in fact prover-only:
their certificates had never been stored, and only the witnesses were replayed.  The enumeration
was therefore re-run so that every step leaves evidence, **with no forcing injected**, and an
independent checker replays all of it -- no sympy, no prover code: the belief forms are rebuilt
from the game tree in Fractions (`seqforms.py`, which agrees with the sympy route on all 48
gradients and every leading form tested) and box certificates by `checkcert.check_box_cert`.

| evidence | count | what the checker does |
|---|---|---|
| closure: exact dominance | 18 coordinates (per leaf, those left free) | re-derives `D_v - c R_v = 0` from the tree |
| closure: robust one-signed form | the rest of 140 closure steps | rebuilds the form, checks it is linear in one set's ratios, one-signed, and nonvanishing at every ordering |
| kill: one-signed contradiction | 191 | the same test against the assigned value |
| kill: certificate | 404 | rebuilds every named row from its origin and replays the branch and bound |
| kill: all 75 orderings of a tremble group | 42 (3,150 certificates) | enumerates the orderings itself and replays one certificate per ordering |
| witness | 21 | an exact Nash point, and along an explicit tremble curve `x_w = eps^e rho` the sign of `lim D_v / R_v` for every coordinate |

Coverage is checked too: every 0 / 1 / interior assignment of the decided coordinates extends a
killed record or is witnessed.  **12 / 12 leaves replay, 0 failed; 637 kill records and 3,554
box certificates.**  The surviving patterns are exactly the three above -- and `b32 = c34 = 0`
now come out of the enumeration with replayed evidence, not from an injected argument.

Two restrictions keep the relaxation sound, and both prover and checker enforce them: a belief
row is used only if it is MULTI-HOMOGENEOUS in the information sets' ratios (then scaling each
set separately is harmless, and a form evaluated at the per-set lowest-class ratios is either 0
or the true leading term); and a one-signed form settles a coordinate only if it is linear in
ONE set's ratios with every ratio appearing in a term whose profile factors are interior (so it
cannot vanish under any tremble ordering).  An earlier draft asserted per-set normalisation was
WLOG in general; it is not for forms that mix sets or degrees.  Witnesses are checked as concrete
curves, which also covers the case the earlier LP check skipped: a leading form that collapses,
where the next order decides.

**How the last 28 were closed** (`resolve_seq2.py`, `witC.py`, 2026-09-24).  The corner leaves
are the generic structure *mirrored*: with `b11 = b21 = 0` it is P2's bet that is unreached,
so P2's opening trembles carry the beliefs that P1's did, and `c32, a33, a34` play the parts of
`b32, c33, c34`:

    A_c32 = (3 r_b11 + 3 r_b21 - 2 r_b41) / 24      (mirror of A_b32)
    A_a33 = (2 r_b11 + 2 r_b21 -   r_b41) / 12      (mirror of A_c33)
    A_a34 = -(r_b11 + r_b21) / 24                   (mirror of A_c34)

They had stayed undecided for the reason §16.13's normalisation note describes, one level down:
a relaxation lets the ratios a form depends on vanish while a sibling in the same set absorbs
the normalisation, and the form then reads `0 = 0`.  Two exact tests close that gap:

  * a leading form that is ONE-SIGNED in its own ratios settles its coordinate at every order,
    so an assigned interior or opposite value is impossible (`one_signed_conflict`) --
    `A_a34 < 0` kills 18 patterns: **`a34 = 0`**;
  * an exhaustive kill over the 75 orderings of a tremble group (`kill_by_orderings`): under
    each ordering every form keeps only its own lowest class, each class is normalised on its
    own, and a ratio inside a class is STRICTLY positive (being 0 would put it in a higher class,
    which is another ordering) -- 6 patterns are empty under all 75 orderings of P2's openings:
    **`c32 = 0`**, the mirror of `b32 = 0`.

The last four (the sub-family-C leaves 97, 196, 198) were not hard, only mis-sampled: their
region needs a small positive `b23 <= (b11 - b21)/(2(1 - b21))`, below anything the generic grid
tried; at `b11 = 1/8`, `b21 = 1/32`, `b23 = 1/64`, `c11 = 1/2` all four have exact witnesses.

**At the corners the off-path values collapse to a point.**  The Nash windows there are
`a33, c33 in [0, 1/2]` (Table 4); the reached conditions read `2 a33 + 2 c32 >= 1` and
`2 c33 >= 1`, so with `c32 = 0` the refinement forces **`a33 = c33 = 1/2`** -- `a33` takes, off
the path, exactly the value Table 3 gives it on the path at every other leaf.

**Perfection census.**  `perfwit.py` looks for a *generic* point of each surviving pattern
(the enumeration returns whatever point its search hits first, usually a corner where some
deterrence is tight and the first-order test is inconclusive) and applies `refine.perfect_cert`:
3 of the 21 surviving patterns carry a certified perfect equilibrium (leaves 77, 440, 469 --
sub-families A and B -- with `s* = 4/27`, `6/25`, `3365/25484` and the indifference Jacobian of
full rank), all of them the `c23 = 0` pattern.  The search is a grid, so "no perfect witness
found" in the other 18 is not a proof of imperfection; but the `c23` interior patterns have no
uniform inward direction at any point tried, and at the corners `a33 = c33 = 1/2` sits on both
poles at once, where the first-order test is inconclusive by construction.
