# Paper kit — everything you need to write this up

Working material for a paper built on the exact analysis in `REPORT.md`. Every number below
was produced by the code in this directory; provenance is given for each. Claims are tagged:

- **[P]** proved (closed form / structural argument, holds on the continuum)
- **[E]** exact computation (rational or machine-precision float, at enumerated points)
- **[G]** grid evidence (holds at every point of a finite grid; not a proof over the continuum)
- **[?]** plausible but **not** established here — check before asserting

---

## 1. Title, abstract, keywords

### Candidate titles

1. *From Undetermined to Determinate: A Refinement Ladder for Deviation Incidence in Three-Player Kuhn Poker*
2. *Who Pays When a Player Deviates? Properness Pins the Split in Three-Player Kuhn Poker*
3. *Pinning the Split: Off-Path Play, Refinement, and Properness on a Three-Player Kuhn Equilibrium Family*

4. *The Complete Equilibrium Set of Three-Player Kuhn Poker, and Who Pays When a Player Deviates*

Title 4 matches the paper as it now stands (Theorems 4–6 are its spine); title 2 overclaims
unless "properness" is read as normal-form properness, which Corollary 6.1 makes necessary.

### Abstract (draft, ~270 words; revised 2026-09-24 for Theorems 4–6)

> In two-player zero-sum games a deviation's whole loss lands on the single opponent. With three
> players the loss is split, and Nash equilibrium does not determine the split. We study this in
> three-player Kuhn poker, starting from the equilibrium family of Szafron, Gibson and Sturtevant
> (AAMAS 2013). We first settle the equilibrium set exactly. In every Nash equilibrium the first
> player checks with every card and play follows the family wherever it is reached; off the
> path the Nash set is strictly larger, and we give all of it as the union of twelve explicit
> semi-algebraic sets with certified coordinate ranges. The proofs are exact: 66,699 support
> leaves and over four million enumeration nodes carry stored certificates — Nullstellensatz
> cofactors, rational LP duals, interval steps under outward rounding — replayed by a
> solver-free rational checker. We then decide the equilibrium refinements exactly on this set,
> writing Kreps–Wilson beliefs in closed form as leading coefficients along a tremble.
> Sequential rationality pins every off-path coordinate but two — eighteen of them by exact
> dominance — and halves the window of the third player's call frequency `c₃₃` to `[½, 15/16]`.
> Every information set is binary, so extensive-form properness coincides with perfection, and
> it still leaves `c₃₃` an interval; only normal-form properness selects a point. We define an
> incidence ratio ρ, the share of a deviator's loss borne by a given opponent, and show it has
> simple poles exactly on the boundary of the equilibrium region, with residue equal to the
> costless transfer available there. The surviving interval of `c₃₃` carries both poles, so the
> split is determinate only under normal-form properness — which the algorithm that discovered
> the family, MCCFR, does not select.

*(The earlier abstract, built around ρ alone, is superseded: the completeness and exact
refinement results are now the paper's spine, and ρ is the question they answer.)*

### Keywords

Nash equilibrium; equilibrium refinement; proper equilibrium; extensive-form games;
multiplayer games; Kuhn poker; imperfect information; off-path behaviour; counterfactual
regret minimization.

### ACM/AAMAS-style categories

Computing methodologies → Multi-agent systems; Theory of computation → Solution concepts in
game theory; Applied computing → Computer games.

---

## 2. Contributions (numbered, for the intro)

1. **The equilibrium set, exactly.** *Theorem 4*: in every Nash equilibrium P1 checks with every
   card, and play follows the SGS family — Table 3's identities *and* ranges — at every reached
   information set; P2's payoff is `−1/48` in every equilibrium. *Theorem 5*: the complete Nash
   set, off path included, is the union of twelve explicit semi-algebraic sets, with every
   coordinate's range certified (Table 4). **[P,E]**

2. **Proofs a reader can replay.** Every verdict is a stored certificate checked by an
   independent ~450-line Fraction checker with no solver in it: 66,699 / 66,699 support leaves,
   and the enumeration's node kills for **all 77** betting branches, with 0 failures. 71 are
   label-box certificate trees (4,394,323 nodes). The last 6 are exact-propagation certificate
   trees (26,223 nodes), replayed by a second, independently written exact checker. No float
   arithmetic remains in any proof. **[E]**

3. **Refinements decided exactly, and the properness question answered.** *Theorem 6*: beliefs in
   closed form as leading coefficients along a tremble; eighteen coordinates settled by exact
   dominance; in every sequential equilibrium every off-path coordinate is pinned except `c₂₃`
   and `c₃₃` (all of them at the corner sub-families), and `c₃₃ ∈ [½, 15/16]`; all 398 off-path
   support patterns decided, every exclusion and every witness replayed by an independent
   Fraction checker (637 kill records, 3,554 box certificates, 21 witnesses on concrete tremble
   curves; 12 / 12 leaves, 0 failed).
   Because every information set is binary, extensive-form properness equals perfection, and it
   leaves `c₃₃` an interval — so the selection below is a property of the normal form
   (*Corollary 6.1*). **[P,E]**

4. **Normal-form properness makes the split determinate.** Requiring trembles to be ordered by
   cost *across pure strategies* forces the surviving free off-path parameter to a unique
   interior value `c₃₃ = lo + w/3`, at which ρ is finite and exactly rational at every point of
   the family. Both corner solutions are eliminated. Contribution 3 shows no weaker refinement
   does this. **[P,E]**

5. **A three-stage ladder, with each stage doing something different.** Nash leaves ρ undefined
   or unbounded; sequential rationality (and extensive-form properness) fixes its *sign* but
   not its *magnitude*; normal-form properness fixes both. The two sources of indeterminacy — a vanishing denominator and an
   unconstrained numerator — come apart cleanly across the stages. **[E]**

6. **A hard floor.** The width of the indeterminate window is
   `w = ¾(b₁₁+b₂₁) + β/4`, and `w = 0 ⟺ β = 0 ⟺ κβ = 0`. Deterrence slack and the SGS utility
   transfer are the same currency: the window cannot be closed without destroying the
   phenomenon that motivates the paper. Worse, at `w = 0` one pole survives as the *only*
   admissible point. **[P,E]**

7. **An exact global form for ρ.** `ρ(c₃₃) = 1 + R/(c₃₃ − c₃₃*)` exactly — not asymptotically —
   with `R = t/D′`, the costless transfer magnitude over the mixed second derivative. The
   constant term is exactly 1, verified in exact rational arithmetic at every test point.
   **[P,E]**

8. **A three-part criterion for poles**, with a witness for each way it can fail, and a census
   over all 48 parameters showing poles at round-1 *and* round-2 decisions and for two of the
   three players. **[E,G]**

9. **Off-path determination.** The parameters fixing both the location and the value of P1's
   poles are never reached and have exactly zero effect on equilibrium payoffs. "Who pays" is
   decided by behaviour that never occurs. **[E]**

10. **MCCFR does not select the proper equilibrium.** Over 150 seeds at 10⁶ iterations, `c₃₃` is
   dispersed across the window (sd ≈ 0.24 of window width, correlation with everything ≈ 0);
   99/150 outputs lie in none of the three sub-families; and β clusters at ≈ 0.17, never near
   0, a systematic per-seat bias worth ≈ 0.007 chips. CFR reproduces the refinement
   predictions that follow from *dominance* (`c₃₄ → 0` in 139/150) and not those requiring a
   tremble structure (`b₃₂ → 0` in only 41/150). **[E,G]**

11. **An independent exact reproduction** of the SGS family, validated against every
   independently checkable statement in the paper — Table 3 utilities, Table 4, the worked
   leaf, and Appendix eq. (3), (4), (5) — all to ≤ 8.9 × 10⁻¹⁶. **[E]**

12. **Two errata**, one material: a `b₃₃` formula in the Section 5 prose that yields
   non-equilibrium profiles (exploitability 6.25 × 10⁻³), and a sign slip in Lemma 4. **[E]**

13. **A two-player control** showing the phenomenon requires three players for two logically
    independent reasons — no third party to receive a transfer, and no deterrence slack in the
    first place. **[E,G]**

14. **P1's silence is a minimal-deck phenomenon, now at the level of theorems.** In (3, 4)
    every equilibrium has P1 silent (Theorem 4). In (3, 5) there is an exact equilibrium in which
    P1 bets cards 1, 2, 3 and 5. It was found by polishing MCCFR and proved by an exact-arithmetic
    Krawczyk existence test, re-checked independently (MASTER_DATA §16.11.1). **[E]**
    **And in (3, 5) P1 bets in EVERY equilibrium** (MASTER_DATA §16.11.4–5). The proof has three steps:
    - **Reduction:** a P1-silent equilibrium would need P1's value with the top card, when checking,
      to be ≥ 19/8. Otherwise "open 5, bluff 1 at rate 3/8" beats every response (an exact vertex
      certificate over all 2¹⁵ responses).
    - **Certificate:** a correlated-equilibrium (Lagrangian) certificate shows that no equilibrium of
      the restricted game reaches 19/8. Twenty-four "no profitable deviation" inequalities bound that
      value by 28071283/12000000 ≈ 2.3393.
    - **Check:** the bound is verified exactly over all 2⁴⁰ pure profiles by two independent
      checkers.

    So the deck size flips the answer: silent always at N = 4, never at N = 5. **[E]**

---

## 3. Positioning and related work

### The gap you are filling

SGS (2013) establish that P2 can transfer κβ from P1 to P3 while remaining in equilibrium.
They do not ask what happens to the *other* two players when a player deviates, nor whether
the split of that deviation is determined. That is the question here. The framing — a
directional-derivative incidence ratio — appears to be new for this game. **[?]** (verify no
prior work; see the arXiv items below).

### Threads to cite

**Kuhn poker and small-game analysis.** Kuhn (1950) for the two-player game and its
one-parameter equilibrium family; Abou Risk & Szafron (2010) for the three-player variant
used here; SGS (2013) for the family under study. Hoehn et al. (2005) used the two-player
analytic solutions to build exploitive agents — a direct precedent for "analytic solution →
downstream algorithm".

**Multiplayer equilibrium computation.** Zinkevich et al. (2008) for CFR; Lanctot et al.
(2009) for the MCCFR variant SGS used to discover the family; Daskalakis & Papadimitriou
(2005) for PPAD-hardness of three-player equilibria; Ganzfried & Sandholm (2010) on
exploiting qualitative structure. Note that CFR carries no convergence guarantee beyond two
players — this is the standard motivation for wanting analytic solutions in this regime.

**Equilibrium selection and non-interchangeability.** This is the natural home for the
result. In two-player zero-sum games equilibria are interchangeable with a unique value
(von Neumann); with three players they are not, and SGS's family is an explicit witness.
Harsanyi & Selten (1988) for equilibrium selection generally.

**Equilibrium refinement — the most important connection, and now tested (R11).**
Our indeterminacy is driven by parameters at *unreached* information sets. Refinement
concepts exist precisely to discipline off-path behaviour: Selten (1975) trembling-hand
perfection, Kreps & Wilson (1982) sequential equilibrium, Myerson (1978) proper equilibrium,
van Damme's monograph. We test this directly (R11): a refinement **does** collapse part of the indeterminacy —
`c34`, `c44` and `b32` are pinned, and ρ's sign becomes determinate — but the `c33`
interval survives and both poles remain. Position this as the paper's bridge to the
refinement literature rather than as a caveat.

**Three-player poker specifically.** Nash & Shapley (1950) solved a three-person poker game
analytically, but with replacement and returned antes. Chen & Ankenman (2006, Example 29.2)
construct an endgame where one player transfers utility between two others — SGS note their
result shows this arises naturally rather than by construction.

### Bibliography

Verified (read or used directly in this work):

- **[V]** D. Szafron, R. Gibson, N. Sturtevant. *A Parameterized Family of Equilibrium
  Profiles for Three-Player Kuhn Poker.* AAMAS 2013, pp. 247–254.
  <https://www.ifaamas.org/Proceedings/aamas2013/docs/p247.pdf>

From that paper's reference list (standard, safe to cite; re-verify page numbers):

- **[S]** H. W. Kuhn. *Simplified two-person poker.* In Contributions to the Theory of Games,
  vol. 1, pp. 97–103. Princeton University Press, 1950.
- **[S]** N. Abou Risk, D. Szafron. *Using counterfactual regret minimization to create
  competitive multiplayer poker agents.* AAMAS 2010, pp. 159–166.
- **[S]** M. Zinkevich, M. Johanson, M. Bowling, C. Piccione. *Regret minimization in games
  with incomplete information.* NIPS-20, pp. 905–912, 2008.
- **[S]** M. Lanctot, K. Waugh, M. Zinkevich, M. Bowling. *Monte Carlo sampling for regret
  minimization in extensive games.* NIPS-22, pp. 1078–1086, 2009.
- **[S]** C. Daskalakis, C. H. Papadimitriou. *Three-player games are hard.* ECCC TR05-139,
  2005.
- **[S]** J. Nash. *Equilibrium points in n-person games.* PNAS 36:48–49, 1950.
- **[S]** J. Nash, L. Shapley. *A simple three-person poker game.* In Contributions to the
  Theory of Games, vol. 1, pp. 105–116. Princeton University Press, 1950.
- **[S]** B. Hoehn, F. Southey, R. Holte, V. Bulitko. *Effective short-term opponent
  exploitation in simplified poker.* AAAI 2005, pp. 783–788.
- **[S]** S. Ganzfried, T. Sandholm. *Computing equilibria by incorporating qualitative
  models.* AAMAS 2010, pp. 183–190.
- **[S]** D. Koller, A. Pfeffer. *Representations and solutions for game-theoretic problems.*
  Artificial Intelligence 94(1):167–215, 1997.
- **[S]** B. Chen, J. Ankenman. *The Mathematics of Poker.* ConJelCo, 2006.
- **[S]** F. Southey et al. *Bayes' bluff: opponent modelling in poker.* UAI 2005, pp. 550–558.

Pointers found by search but **not read** — verify before citing:

- **[P]** J. Billingham et al. *Equilibrium solutions of three player Kuhn poker with N > 3
  cards: a new numerical method using regularization and arc-length continuation.*
  arXiv:1802.04670 (2018). Likely the closest neighbour; check whether it already reports
  anything about transfer directions or ρ-like quantities.
- **[P]** *Simplified three player Kuhn poker.* arXiv:1704.08124.
- **[P]** *Full street simplified three player Kuhn poker.* arXiv:1707.01392.
- **[P]** S. Ganzfried. *Successful Nash equilibrium agent for a three-player
  imperfect-information game.* Games 9(2):33, 2018; arXiv:1804.04789.

Refinement literature to add (**[S]**, standard):

- R. Selten. *Reexamination of the perfectness concept for equilibrium points in extensive
  games.* Int. J. Game Theory 4:25–55, 1975.
- D. Kreps, R. Wilson. *Sequential equilibria.* Econometrica 50(4):863–894, 1982.
- R. Myerson. *Refinements of the Nash equilibrium concept.* Int. J. Game Theory 7:73–80, 1978.
- J. Harsanyi, R. Selten. *A General Theory of Equilibrium Selection in Games.* MIT Press, 1988.
- E. van Damme. *Stability and Perfection of Nash Equilibria.* Springer, 1991.

---

## 4. Preliminaries and notation

### The game

Three-player Kuhn poker (Abou Risk & Szafron 2010; SGS Section 2). Deck {1,2,3,4}, one card
each to P1, P2, P3 — **24 deals, each of probability κ = 1/24**. Everyone antes 1. One
betting round; a bet or call is exactly 1 chip; no raises. Acting order P1, P2, P3. With no
bet outstanding the actor checks (K) or bets (B); facing a bet the actor folds (F) or
calls (C).

- P1 bets → P2 answers → P3 answers → end.
- P1 checks, P2 bets → P3 answers → **P1 answers** → end.
- P1 checks, P2 checks, P3 bets → P1 answers → **P2 answers** → end.
- All check → three-way showdown.

Highest unfolded card takes the pot. The tree has **13 terminal histories per deal, 312
leaves total**.

### Parameterization (SGS Table 1)

`a_jk`, `b_jk`, `c_jk` = probability that P1 / P2 / P3 takes the **aggressive** action (B with
no bet out, C facing a bet) holding card *j* in situation *k*. The passive action has
probability 1 − x. A profile is the 48-vector `[a₁₁..a₄₄, b₁₁..b₄₄, c₁₁..c₄₄]`.

| k | P1 history | P2 history | P3 history |
|---|---|---|---|
| 1 | (root) | K | KK |
| 2 | KKB | B | KB |
| 3 | KBF | KKBF | BF |
| 4 | KBC | KKBC | BC |

Call k = 1 a **round-1 (opening)** decision and k = 2,3,4 **round-2 (call/fold)** decisions.
Each player has exactly 16 parameters and acts at 4 information sets per card.

### The family (SGS Tables 2 and 3)

**Table 2 (21 necessary values).** `a₁₂=a₁₃=a₁₄=a₂₄=0`, `a₄₂=a₄₃=a₄₄=1`, and the same
pattern for b and c.

**Table 3**, with β = max{b₁₁, b₂₁}:

- **P1 has no free parameters**: `a₁₁=a₂₁=a₂₂=a₂₃=a₃₁=a₃₂=a₃₄=a₄₁=0`, `a₃₃=1/2`.
- **P2**: free `b₁₁, b₂₁, b₂₃, b₃₂`; `b₂₂=b₃₁=b₃₄=0`;
  `b₃₃ = ½ + (b₁₁+b₂₁)/2 + β/2 − b₂₃(1−b₂₁)`; `b₄₁ = 2b₁₁ + 2b₂₁`.
- **P3**: free `c₁₁, c₃₃, c₃₄`; `c₂₁ = ½ − c₁₁`; `c₂₂=c₂₃=c₃₁=c₃₂=0`; `c₄₁=1`.
- Constraints: `b₂₃ ≤ max{0, (b₁₁−b₂₁)/(2(1−b₂₁))}`;
  `c₁₁ ≤ min{½, (2−b₁₁)/(3+2b₁₁+2b₂₁)}`; `b₃₂ ≤ ½ + ¾(b₁₁+b₂₁) + β/4`;
  `½ − b₃₂ ≤ c₃₃ ≤ ½ − b₃₂ + ¾(b₁₁+b₂₁) + β/4`; `0 ≤ c₃₄ ≤ 1`.

Three sub-families: **A** (`c₁₁=0`, `b₁₁ ≤ b₂₁ ≤ ¼`, `b₂₃=0`, β=b₂₁); **B**
(`0 < c₁₁ < ½`, `b₂₁=b₁₁ ≤ ¼`, `b₂₃=0`, β=b₁₁); **C** (`c₁₁=½`, `b₁₁ ≤ ¼`,
`b₂₁ ≤ min{b₁₁, ½−2b₁₁}`, β=b₁₁).

**Utilities:** `u₁ = −κ(½+β)`, `u₂ = −κ/2`, `u₃ = κ(1+β)`.

### Reachability (important, and easy to state early)

Because `a_j1 = 0` for every j, **P1 never bets anywhere in the family**. Consequently P2
never faces a bet and P3 never reaches BF or BC. The parameters `b₁₂, b₂₂, b₃₂, b₄₂` and
`c₁₃, c₂₃, c₃₃, c₄₃, c₁₄, c₂₄, c₃₄, c₄₄` sit at information sets of reach probability zero.
The off-path region is **family-wide**, not an artifact of a corner. Note this includes two of
the family's own free parameters, `b₃₂` and `c₃₃`.

---

## 5. Reproduction and errata (Section for the paper — this buys you credibility cheaply)

### Validation table

| check | result |
|---|---|
| Table 3 utilities `u₁=−κ(½+β)`, `u₂=−κ/2`, `u₃=κ(1+β)`, 600 random family points | max err **5.0e-16** |
| exact rational check at `b₁₁=1/8, b₂₁=1/4` | `u = (−1/32, −1/48, 5/96)` — exact |
| SGS Section 2's worked leaf `a₁₃` in deal 124 | factors `(1−a₁₁)·b₂₁·(1−c₄₂)·a₁₃`, payoff `(−2,3,−1)` — matches |
| Appendix **eq. (3)** (u₃ with P3 free), 400 random points | max err **6.0e-16** |
| Appendix **eq. (4)** (u₂ with P2 free), 400 random points | max err **2.2e-16** |
| Appendix **eq. (5)** (u₁ with P1 free), 400 random points | max err **8.9e-16** |
| Table 4 mismatched profile and P2's stated gain of κβ | reproduced exactly (0.0104167 = κ/4) |
| exact best-response gap, 450 random family points | **< 5e-16** for all three players |

Matching eq. (3)–(5) is the strong test: those polynomials pin down both the tree and the
Table 3 transcription simultaneously.

### Erratum 1 (material) — `b33` in the Section 5 prose

For the `c₁₁ = ½` sub-family, SGS Section 5 states `b₃₃ = (1 + b₁₁ + 2b₂₁)/2`. Table 3's
general formula gives `b₃₃ = ½ + (b₁₁+b₂₁)/2 + β/2 − b₂₃(1−b₂₁)`, i.e. with β = b₁₁,
`(1 + 2b₁₁ + b₂₁)/2 − b₂₃(1−b₂₁)`. The prose version has b₁₁ and b₂₁ transposed and drops
the b₂₃ term; the two agree only when `b₁₁ = b₂₁` and `b₂₃ = 0`, or at `b₂₃ = b₂₃^max`.

Where they differ, the prose value is **not an equilibrium**: **[E]**

| b₁₁ | b₂₁ | b₂₃ | b₃₃ (Table 3) | b₃₃ (prose) | exploitability (T3) | exploitability (prose) |
|---|---|---|---|---|---|---|
| 0.20 | 0.05 | 0 | 0.72500 | 0.65000 | 2.2e-16 | **6.25e-03** |
| 0.15 | 0.10 | 0.02 | 0.68200 | 0.67500 | 7.3e-17 | **5.83e-04** |
| 0.20 | 0.05 | 0.079 | 0.65000 | 0.65000 | 2.2e-16 | 2.2e-16 |
| 0.10 | 0.10 | 0 | 0.65000 | 0.65000 | 7.6e-17 | 7.6e-17 |

Table 3's formula is the correct one, and the Appendix proof uses it. **A nice detail worth a
sentence:** `du_i/db₃₃ = (0,0,0)` for all three players — b₃₃ affects nobody's payoff — yet
setting it wrong destroys the equilibrium. It is a pure deterrence parameter. This is the
same phenomenon as `c₃₃`, and it foreshadows the paper's main mechanism.

### Erratum 2 (cosmetic) — sign in Lemma 4

Lemma 4 displays `∂u₂/∂b₂₃ = 2κ(1−b₂₁)(1−2c₁₁)`. Differentiating the paper's own eq. (4)
gives `2κ(1−b₂₁)(2c₁₁−1)`. The paper's immediately following usage ("If c₁₁ = 0, then
∂u₂/∂b₂₃ = −2κ(1−b₂₁) ≤ 0") is consistent with the corrected sign, so the proof is
unaffected. Our engine matches eq. (4) to 2.2e-16, confirming the corrected sign. **[E]**

---

## 6. Method

State these plainly; they are what make the results exact rather than approximate.

1. **Full enumeration.** All 24 deals × 13 terminal histories are materialized once as a leaf
   table of (parameter-index list, payoff triple). `u_i(p) = κ Σ_leaves (Π factors) × payoff_i`.
   No sampling, no CFR, no iteration.

2. **Multilinearity.** Each `u_i` is multilinear in the 48 parameters, hence **affine along
   any single coordinate**. Three consequences used throughout:
   - `∂u/∂x_i = u(x_i=1) − u(x_i=0)` — an *exact* derivative from two evaluations.
   - central differences are exact to round-off for coordinate directions
     (max |central − exact| = **2.4e-11** at h = 1e-5 over 9,072 × 48 × 3). **[E]**
   - any expression of the form `∂u/∂x` is affine in every *other* single parameter, so its
     zeros can be solved for in **closed form** rather than searched. This is what turns
     "we observed a pole near the boundary" into "the pole is at the boundary".

3. **Exact best responses.** `u_i` decomposes over the card player i holds, and i's
   parameters for card j appear only in deals where i holds j. So the best response splits
   into 4 independent 4-decision problems: 4 × 2⁴ = 64 exact evaluations. Exploitability is
   `BR_i − u_i`.

4. **Grid.** 9,072 valid family points — sub-family A 2,268, B 2,268, C 4,536 — sweeping
   `b₁₁, b₂₁, b₂₃, b₃₂, c₁₁, c₃₃, c₃₄` across their full valid ranges, β spanning [0, ¼].
   Dense 1-D sweeps use 201 points. Every point is checked against `violations()`, a direct
   transcription of the Table 3 constraints.

5. **Rational arithmetic** (`fractions.Fraction`) at selected points, to rule out
   floating-point artifacts in headline claims.

---

## 7. Formal statements

Give these as numbered propositions; most have one-line proofs.

**Definition 1 (feasible direction).** At `p ∈ [0,1]⁴⁸`, a direction `d` supported on player
A's 16 coordinates is *feasible* if `d_i ≥ 0` wherever `p_i = 0` and `d_i ≤ 0` wherever
`p_i = 1`. The feasible set is a polyhedral cone whose extreme rays are exactly the feasible
`±e_i`.

**Definition 2 (incidence ratio).** For feasible `d` with `du_A/dε ≠ 0`,
`ρ_{A→X}(d) = −(du_X/dε)/(du_A/dε)`.

**Definition 3.** `d` is *costless* for A if `du_A/dε = 0`. It is *equilibrium-preserving* if
`p + εd` remains a Nash equilibrium for small ε > 0.

**Proposition 1 (constant-sum, structural).** `Σ_i u_i(p) = 0` for **all** `p ∈ [0,1]⁴⁸`.
*Proof:* the three payoffs sum to zero at each of the 312 leaves, since chips paid in equal
chips paid out. ∎ **[P]**
*Corollaries:* `Σ_i du_i/dε = 0` for every direction, on and off the family; and
`ρ_{A→B} + ρ_{A→C} = 1` whenever defined. **ρ is a share.**
*Numerics:* max |Σ du_i| = **3.5e-16** exact, **2.8e-11** by central difference at h = 1e-5;
zero points flagged. The zero-sum identity is a property of the *game*, not of the
equilibrium — it cannot fail, and a paper should say so rather than presenting it as a test
that passed.

**Proposition 2 (orientation invariance).** `ρ(d) = ρ(−d)`, since numerator and denominator
both flip sign. Hence ρ depends only on *which* parameter is perturbed, not the sign of the
step. **[P]**

**Proposition 3 (no improving direction).** At every point of the family, `du_A/dε ≤ 0` for
every feasible `d`, for every A.
*Proof:* `du_A(d) = Σ_i d_i ∂u_A/∂x_i` is linear in `d`; the feasible cone is generated by
the feasible `±e_i`; each generator has `du_A ≤ 0` (else the profile is not an equilibrium);
a nonnegative combination of nonpositive numbers is nonpositive. ∎ **[P]**
*Numerics:* over **502,626** feasible (point, coordinate-direction) pairs, **0** improving.
Also 4,000 random feasible multi-coordinate directions: max `du_A` = **−1.44e-02**, none
positive. **[G]**

| player | feasible pairs | improving | strictly costly | neutral (du_A = 0) |
|---|---|---|---|---|
| P1 | 154,224 | **0** | 111,456 | 42,768 |
| P2 | 186,618 | **0** | 52,038 | 134,580 |
| P3 | 161,784 | **0** | 57,072 | 104,712 |

**Theorem 1 (pole criterion).** ρ has a pole along `e_x` iff all three hold:
(i) `du_owner/dx = 0` has a root in some free parameter; (ii) that root is attainable inside
the Table 3 constraints; (iii) the numerator `du_C/dx` does not vanish there.
Witnesses that each is necessary are in §8, R7. **[E,G]**

**Theorem 2 (exact global form for ρ).** Fix every free parameter but `c₃₃`. Then
`D(c₃₃) = du₁/da_{j1}` and `N(c₃₃) = −du₃/da_{j1}` are both affine in `c₃₃`, and moreover
**`N′ = D′`**. Hence ρ is a Möbius function of `c₃₃` with a pole of order exactly 1, and

> **ρ(c₃₃) = 1 + R/(c₃₃ − c₃₃*)**,  exactly — not asymptotically — with `R = N(c₃₃*)/D′`.

`D′ = ∂²u₁/(∂a_{j1}∂c₃₃)` equals `−4κ` for `a₁₁` and `a₂₁`, `+2κ` for `a₄₁`, and `0` for `a₃₁`
— which is precisely why `a₃₁` can never have a pole. At `c₃₃*` the denominator vanishes, so
the deviation is costless for P1 and Proposition 1 forces `du₂ = −du₃ = t`; hence
`N(c₃₃*) = t` and **`R = t/D′`**: the residue *is* the magnitude of the costless transfer
available at that boundary, divided by the mixed second derivative. **[P,E]**
*Numerics:* `N′/D′ = 1` exactly and residual error **0.0e+00** in exact rational arithmetic, at
six family points × three deviations. This supersedes the weaker asymptotic statement
`ρ = R/(c₃₃−c₃₃*) + O(1)`: the `O(1)` term is exactly 1.

**Proposition 5 (hard floor).** The width of the indeterminate window is
`w = hi − lo = ¾(b₁₁+b₂₁) + β/4`, independent of `b₃₂`. Every term is non-negative, so
`w = 0 ⟺ b₁₁ = b₂₁ = 0 ⟺ β = 0 ⟺ κβ = 0`.
*Proof:* `lo = ½ − b₃₂` and `hi = b₃₂max − b₃₂ = ½ + ¾(b₁₁+b₂₁) + β/4 − b₃₂`; subtract. ∎
*Consequence:* deterrence slack and the SGS utility transfer are the same currency. The
window cannot be closed without destroying the transfer. And at `w = 0` the `a₄₁` pole dies
(its numerator vanishes) while the `a₁₁` pole survives as the **only admissible** value of
`c₃₃`. **[P,E]**

**Theorem 3 (properness selection).** Under Myerson properness applied to the normal form,
an interior `c₃₃` requires `cost(a₁₁) = cost(a₄₁)`, which holds uniquely at

> **`c₃₃ = lo + w/3`**  (and `= ½ + w/3` once `b₃₂ = 0` is forced).

Both corners `c₃₃ ∈ {lo, hi}` are excluded. At the selected point ρ is finite and exactly
rational for every deviation, at every point of the family.
*Proof sketch:* `cost(a₁₁) = cost(a₂₁) = 4κ(c₃₃ − lo)` and `cost(a₄₁) = 2κ(hi − c₃₃)`.
Properness sends the probability of a strictly costlier action to a lower order, so any cost
inequality drives `r₄/(r₁+r₂)` to 0 or ∞; by R11's belief `q = (r₁+r₂)/(r₁+r₂+2r₄)` and P3's
threshold `q = 1/5`, that pushes `c₃₃` to 1 or 0, both outside the window. Cost equality gives
`4(c₃₃−lo) = 2(hi−c₃₃)`, i.e. `c₃₃ = lo + w/3`; there properness constrains nothing between
the equal-cost actions, so the knife-edge `r₄ = 2(r₁+r₂)` is admissible and P3 is exactly
indifferent. The corners have one cost exactly 0 and the other strictly positive, so the same
argument applies and contradicts them. ∎ **[P,E]**
*Scope:* this is properness on the **normal form**, where pure strategies are ordered by
expected cost and the behavioural rates `r_j` inherit that ordering. *Agent*-normal-form
properness compares only actions within one information set and would not order `a₁₁` against
`a₄₁`. State the assumption explicitly.

**Proposition 4 (two-player collapse).** In any two-player constant-sum game,
`du_B = −du_A` identically. Hence (a) no costless transfer exists — `du_A = 0` forces
`du_B = 0`; (b) `ρ ≡ 1` wherever defined; (c) no pole is possible, since numerator and
denominator are the same number up to sign and vanish together. ∎ **[P]**

### 7.1 The completeness theorem and its lemmas (2026-09-20)

Notation. A behavioural profile is `p ∈ [0,1]⁴⁸`, `x_i` the probability of the aggressive
action at information set `i` (16 per player). Player `k`'s payoff `u_k(p)` is multilinear.
Every information set of `k` is `(own card, public history)`, so `k`'s own earlier choices on
the path to any node of the set are the same: the set's reach factorises as
`R(n) = R_k(i) · R_{−k}(n)` with `R_k(i)` the product of `k`'s own coordinates on the path
(the same for every node `n` of `i`) and `R_{−k}(n)` the product of the other players' and
chance. Say `i` is **own-reachable** under `p` if `R_k(i) > 0`, and **reached** if some node
of `i` has `R(n) > 0`.

**Definition 4 (own-reach-stripped gradient).**
`D_i(p) = (1/24) Σ_{n ∈ i} R_{−k}(n) · (V_k(agg child of n) − V_k(pass child of n))`, where
`V_k` are `k`'s continuation values under `p`. Then `∂u_k/∂x_i = R_k(i) · D_i` exactly.

**Definition 5 (D-condition at `i`).** `x_i D_i ≥ 0` and `(1 − x_i) D_i ≤ 0`; equivalently
`x_i > 0 ⇒ D_i ≥ 0` and `x_i < 1 ⇒ D_i ≤ 0`, i.e. `x_i` is a best reply at `i` with beliefs
proportional to `R_{−k}(n)` — vacuous when the opponents keep `i` unreached (`D_i ≡ 0`).

**Lemma 1 (Nash ⇔ D-condition everywhere, up to own-unreached re-choice).**
(a) If `p` is a Nash equilibrium, the D-condition holds at every own-reachable information
set, and there is a profile `p′` that agrees with `p` at every own-reachable set of every
player (hence has the same reached play and the same payoffs, and is Nash) and satisfies the
D-condition at **every** information set.
(b) If `p` satisfies the D-condition at every information set, `p` is a Nash equilibrium.
*Proof.* (a) At an own-reachable `i`, `∂u_k/∂x_i = R_k(i) D_i` with `R_k(i) > 0`, so a best
reply in the single coordinate `x_i` forces the D-condition. Build `p′` by backward induction
over `k`'s own decision tree, re-choosing `x_i` at every own-unreached set to satisfy the
D-condition given the (already re-chosen) continuation; these sets have `R_k = 0`, so nothing
on the path of play and no payoff changes, and no `D_j` of another player changes (every term
of `D_j` through such a set carries `k`'s zero coordinate). At an own-reachable `i` the
D-condition survives the re-choice: if `x_i < 1` and `D′_i > 0` (or `x_i > 0` and `D′_i < 0`)
then "deviate at `i` and continue as `p′`" is a strategy of `k` with strictly larger payoff,
contradicting optimality of `p_k`. (b) Backward induction over the own tree: at the deepest
sets the D-condition maximises `Σ_n R_{−k}(n) V_k(n)`; inductively every continuation is
optimal, so `p_k` is optimal against `p_{−k}`. ∎ **[P]**
*Why this and not `∂u_k/∂x_i = 0`:* the plain gradient vanishes at every own-unreached set
whatever the continuation, so the reach-weighted first-order system admits profiles that are
not equilibria (MASTER_DATA §16.2, erratum 8); `D` does not.

**Lemma 2 (the DC pair is the exact local condition).** For `x ∈ [0,1]`,
`x D ≥ 0 ∧ (1 − x) D ≤ 0` ⇔ `(x > 0 ⇒ D ≥ 0) ∧ (x < 1 ⇒ D ≤ 0)` ⇔ (`x = 0 ⇒ D ≤ 0`,
`x = 1 ⇒ D ≥ 0`, `0 < x < 1 ⇒ D = 0`). ∎ **[P]** So a coordinate whose label is not
enumerated (DC: its set has reach upper bound 0 on the cell, or it occurs in no other
constraint) loses nothing when it carries the pair instead of a label.

**Lemma 3 (node systems relax their leaves).** A node of the label tree assigns each
coordinate `0`, `1`, `MIX` (open `(0,1)`), `DC` or `U`; its system substitutes the `0/1`
labels into every `D_i` and imposes `D_i = 0` for `MIX`, `−D_i ≥ 0` for `0`, `D_i ≥ 0` for
`1`, and the pair of Lemma 2 for `DC` and `U`. Each of the three labels of a `U` coordinate
implies its pair, so every leaf's system implies its ancestors'. Hence a node proved
infeasible (rational contraction plus a rationally certified LP relaxation, or the interval
rules of `bnb6` with outward rounding) has no leaf containing a profile that satisfies the
D-condition everywhere. ∎ **[P]**

**Lemma 4 (labels partition).** `x ↦ (0 if x = 0, 1 if x = 1, MIX otherwise)` assigns every
profile exactly one label vector, so the 3⁴⁸ label cells partition `[0,1]⁴⁸`; a leaf with `DC`
coordinates is the union of the cells that agree with it elsewhere. Every prune in the
enumeration is sound for profiles satisfying the D-condition everywhere (Lemma 3; the
`bnb6` strong rules `DLO > 0 ⇒ x = 1`, `DHI < 0 ⇒ x = 0`, and the dominance rule restricted
to certainly-reached sets, are necessary conditions of Nash), so the surviving leaves cover
every such profile — in particular the `p′` of Lemma 1(a) for every Nash `p`. ∎ **[P]**

**Lemma 5 (FAMILY leaf ⇒ realization-equivalent to a family member).** A leaf is FAMILY
when every point of its system has Table 3's pins on its non-DC coordinates (by the labels),
satisfies the identities `a33 = ½`, `b41 = 2(b11 + b21)`, `c21 = ½ − c11`, and `b33`'s
formula split on `b11 ≶ b21`, and satisfies the sub-family's parameter ranges (A: `c11 = 0`;
B: `c11, c21` interior; C: `c11` interior, `c21 = 0`) — each fact an exact certificate. Every
reached coordinate is non-DC, so such a point agrees with a member `q` of the SGS family on
every reached coordinate (take `q`'s off-path coordinates from the family's admissible
off-path set, which is non-empty); `p` and `q` then induce the same distribution over
terminal nodes, hence the same payoffs. ∎ **[P]** (SGS's converse, that every member of the
family is an equilibrium, is their Theorem; the reproduction in §5 confirms it.)

**Theorem 4 (on-path completeness).** *Every Nash equilibrium of three-player four-card
Kuhn poker is realization-equivalent to a member of the SGS family: P1 never bets, and on
every reached information set its play satisfies Table 3's identities and parameter ranges.
As profiles the equilibrium set is strictly larger than the family (exact witness
`b12 = 9/100` off path).*
*Proof.* By Lemma 1 it suffices to enumerate profiles satisfying the D-condition everywhere.
P1's four opening coordinates give 81 label cells; 78 survive the root (`root81`, nash mode).
The 77 cells with some `a_j1 ≠ 0` contain no surviving support: layered exact enumeration
(`enuml`, exact test every four levels, bet-first order) reaches 45,276 supports, every one
certified empty (47 of the 77 cells have no support at all; run of 2026-09-20/21 under
outward-rounded interval arithmetic, 8h35m on 18 workers). The silent cell yields 668
supports: 656 certified empty, 12 FAMILY — sub-families A (4 leaves), B (3), C (5), with
every corner. Every leaf verdict is a stored certificate replayed by an independent
Fraction-only checker (`checkcert.py`: 66,699 of 66,699 leaves — 668 silent, 45,276 nash-mode
betting, 20,755 seq-mode betting — verified, 0 failed; `cert_summary_R.txt`). The *node
kills* above the leaves are certified too, for all 77 betting cells. Each cell is re-derived as a
tree in which every pruned node carries its own exact certificate.
- 71 cells: `checkenum.py` replays all 4,394,323 nodes with 0 failures (MASTER_DATA §16.9).
- The last 6: every node also carries its exact propagated box and a certificate of that box.
  `checkenum2.py` replays all 26,223 nodes with an independent exact implementation, with 0
  failures (§16.9.1).

Lemma 5 finishes. ∎
**[E,P]**

**Corollary 4.1.** In every Nash equilibrium P1 checks with every card (`a_j1 = 0`,
`j = 1..4`). **Corollary 4.2.** The set of Nash equilibrium payoff vectors is the family's,
the segment `{(−κ(½ + β), −κ/2, κ(1 + β)) : β ∈ [0, ¼]}` with `κ = 1/24` and
`β = max{b₁₁, b₂₁}`; in particular P2's payoff is `−1/48` in **every** equilibrium of the
game, and `u₁ + u₃ = −1/48`. **[P]** (realization equivalence plus the family's utilities in
§4, checked on the 744 certified family points to 1e-15).

### 7.2 The complete equilibrium set, off path included (2026-09-21)

In the silent cell almost no information set is own-unreached: P1's later sets all follow a
check (probability 1), P3's sets are first moves, P2's later sets follow P2's own check, which has
positive probability wherever `b_j1 < 1`. The exception is `b41 = 1` (two of the twelve leaves,
70 and 440): P2's `b43`, `b44` are then own-unreached, and Lemma 1's re-choice acts exactly
there. Hence:

**Theorem 5 (the complete Nash set).** *The set of Nash equilibria of three-player four-card
Kuhn poker is the union of the twelve sets `Ŝ_ℓ`, one per FAMILY leaf `ℓ`, where
`S_ℓ = { x ∈ [0,1]⁴⁸ : the leaf's labels (0/1 exact, MIX strictly interior) and the D-condition
at every coordinate }` and `Ŝ_ℓ` frees the own-unreached coordinates (`b43`, `b44` in the two
leaves with `b41 = 1`; nothing elsewhere). Each `S_ℓ` factors as (on-path parameters) ×
(deterrence region) × (free cube): the reached coordinates carry Table 3 (sub-family A, B or C
with its identities and ranges); the off-path coordinates that enter some player's incentive —
P2's and P3's responses to P1's bet (`b_j2`, `c_j3`, `c_j4`), P1's and P3's responses to P2's bet
where P2 never bets (`a_j3`, `a_j4`, `c_j2`), and the raises `a44`, `b44` — are constrained only
by the deterrence inequalities `D_{a_j1} ≤ 0` (P1 gains nothing by betting card `j`),
`D_{b_j1} ≤ 0` where `b_j1 = 0`, and the sign-determined pins they induce (e.g. `a32 = 0` forces
`b44 ≥ 4/5` through `D_{a32} = −(5 b44 − 4)/48`); every remaining coordinate has `D ≡ 0` and is
free in `[0, 1]`.* The twelve systems are written out in `nefull_systems.txt` (Gröbner normal forms of
every inequality) and the projection of the union on each coordinate — the off-path *windows* —
in `nefull_ranges.txt`, every bound an emptiness certificate (`{S_ℓ, x_v > T}` empty, checked by
`checknefull.py`) with an exact rational witness where it is attained. **[E,P]**
*Proof.* Lemma 1(b) makes every point of every `S_ℓ` a Nash equilibrium (the leaf's system is
the D-condition everywhere), and changing an own-unreached coordinate changes no payoff and no
incentive (Lemma 1(a)), so every point of `Ŝ_ℓ` is one too. Conversely Lemma 1(a) and the
enumeration (every other leaf of the silent cell certified empty, every betting cell without
support) put the re-choice `p′` of every Nash `p` in some `S_ℓ`, and `p` differs from `p′` only
on own-unreached coordinates, i.e. `p ∈ Ŝ_ℓ`. The factorisation is read off the systems: the D of
every coordinate outside the listed ones reduces to 0 modulo the leaf's identities
(`nefull_systems.txt`). ∎

**The windows (Table 4).** Projection of the complete Nash set on every coordinate that is a
parameter or a constrained off-path coordinate somewhere (`nefull_ranges.txt`; every bound an
emptiness certificate checked by `checknefull.py`, attained bounds with an exact witness):

| coordinate | role | over all equilibria | A | B | C |
|---|---|---|---|---|---|
| `a13` | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| `a14` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| `a23` | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| `a24` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| `a33` | on path (Table 3) | [0, 1/2] | [0, 1/2] | [0, 1/2] | [0, 1/2] |
| `a34` | off path | [0, 1] | [0, 1] | [0, 1ᶜ] | [0, 1] |
| `a43` | off path | [1, 1] | [1, 1] | [1, 1] | [1, 1] |
| `a44` | off path | [0, 1] | [0, 1] | [0ᶜ, 1] | [0, 1] |
| `b11` | on path (Table 3) | [0, 1/4] | [0, 1/4] | [0, 1/4ᶜ] | [0, 1/4] |
| `b12` | off path | [0, 0.4173ᶜ] | [0, 0.4173⁻] | [0, 0.4169⁻] | [0, 0.2781ᶜ] |
| `b21` | on path (Table 3) | [0, 1/4] | [0, 1/4] | [0, 1/4] | [0, 1/6] |
| `b22` | off path | [0, 0.5841ᶜ] | [0, 0.5841⁻] | [0, 7/12] | [0, 0.3895⁻] |
| `b23` | on path (Table 3) | [0, 1/8] | [0, 0] | [0, 0] | [0, 1/8] |
| `b32` | off path | [0, 15/16] | [0, 15/16] | [0, 15/16ᶜ] | [0, 19/24] |
| `b33` | on path (Table 3) | [1/2, 7/8] | [1/2, 7/8] | [1/2ᶜ, 7/8] | [1/2, 3/4] |
| `b41` | on path (Table 3) | [0, 1] | [0, 1] | [0, 1] | [0, 2/3] |
| `b42` | off path | [31/40ᶜ, 1] | [0.7750ᶜ, 1] | [31/40ᶜ, 1] | [0.7750⁻, 1] |
| `b43` | off path | [0ᶜ, 1] | [0⁻, 1] | [0⁻, 1] | [1, 1] |
| `b44` | off path | [17/32ᶜ, 1] | [0.7797⁻, 1] | [17/32ᶜ, 1] | [4/5, 1] |
| `c11` | on path (Table 3) | [0, 1/2] | [0, 0] | [0⁻, 1/2⁻] | [1/2, 1/2] |
| `c12` | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| `c13` | off path | [0, 0.5269ᶜ] | [0, 0.5269⁻] | [0, 0.5268ᶜ] | [0, 0.3458ᶜ] |
| `c14` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| `c21` | on path (Table 3) | [0, 1/2] | [1/2, 1/2] | [0⁻, 1/2⁻] | [0, 0] |
| `c22` | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| `c23` | off path | [0, 7/12] | [0, 7/12ᶜ] | [0, 7/12] | [0, 0.3894⁻] |
| `c24` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| `c32` | off path | [0, 1/2] | [0, 1/2] | [0, 1/2] | [0, 1/2] |
| `c33` | off path | [0, 15/16] | [0, 15/16ᶜ] | [0, 15/16] | [0, 19/24] |
| `c34` | off path | [0, 1] | [0, 1] | [0, 1ᶜ] | [0, 1] |
| `c42` | off path | [1, 1] | [1, 1] | [1, 1] | [1, 1] |
| `c43` | off path | [0.7750ᶜ, 1] | [0.7752ᶜ, 1] | [0.7750ᶜ, 1] | [0.7750⁻, 1] |
| `c44` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |

Marks: a bare number is attained (exact rational witness in the leaf, verified); ⁻ = certified strict bound (not attained); ᶜ = certified bound, attainment undecided at the search precision (the true extremum lies between the best known equilibrium value and this bound).

Read with §4: `a13`, `c12`, `c22` are 0 and `a43`, `c42` are 1 in *every* equilibrium although they
are off the path — the deterrence inequalities pin them (a fold with the worst card facing a
bet, a call with the best card, are forced by the *other* players' incentives). `b12`, `b22`,
`c13`, `c23` — the responses to P1's bet that Table 2 sets to 0 — are free up to ≈ 0.42, 0.58,
0.53, 7/12 respectively; `b42`, `c43` (calls with the top card) only need ≥ ≈ 0.775; `b32`,
`c33` range over `[0, 15/16]`; `b44 ≥ 17/32` (≥ 4/5 wherever `a32 = 0` binds); `a14`, `a24`, `c14`,
`c24`, `c34`, `c44`, `a44`, `b43` are unconstrained. Sub-family C is the most restricted
(`b41 ≤ 2/3`, `b32`, `c33 ≤ 19/24`). At the three corner leaves (`b11 = b21 = 0`) the responses to P1's bet
are pinned to Table 2 (`b12 = b22 = c13 = c23 = 0`, `b42 = c43 = 1`) while `b32`, `c33 ∈ [0, 1/2]`,
`a33 ∈ [0, 1/2]` and `b44 ≥ 4/5` keep a window: the deterrence of P1's bet has no slack at the
corners, the deterrence of P2's does.


### 7.3 Theorem 6 — the refinements, decided exactly

**Lemma R1 (binary sets).** Every information set of 3-player Kuhn poker has exactly two
actions. For such a game a completely mixed behaviour profile is ε-proper in van Damme's
extensive-form sense iff it is ε′-perfect with ε′ = ε/(1−ε): with two actions "the inferior
action gets at most ε times the better one" and "the inferior action gets at most ε" differ
only by the factor `1 − ε ≤ σ(better) ≤ 1`. Hence **extensive-form proper = extensive-form
perfect = agent-normal-form perfect** here, and only *normal-form* properness — which orders
whole pure strategies across information sets — can select more.

**Definition (the belief system).** For coordinate `v`, `D_v` is the own-reach-stripped
gradient and `R_v` the reach of `v`'s information set with the owner's own choices stripped;
`D_v / R_v` is the value difference at the set under the beliefs the profile induces. Along a
tremble `x_w = ε r_w` (where the profile plays 0) / `1 − ε r_w` (where it plays 1) both vanish
at an unreached set and the limit is `A_v(x, r) / B_v(x, r)`, the ratio of the leading
coefficients: the belief-weighted value difference, with the ratios `r` shared by every set —
Kreps–Wilson consistency in closed form.

**Theorem 6 (sequential = proper set).** Over the complete Nash set of Theorem 5:

1. *(dominance, belief-free)* Eighteen coordinates satisfy `D_v = c·R_v` identically, with
   `c = −1` (calling with the worst cards: `x12, x13, x14, x24` for each player `x`), `+4`
   (`x43`) or `+5` (`x44`) — the same chip difference at **every node** of the set, under every
   belief — so each is pinned in every sequential equilibrium; and `b42 = 1` because
   `D_{b42}/R_{b42} ≥ 4 > 0` everywhere. Thirteen of the eighteen have a nontrivial Nash window
   (Table 4), eight of them all of `[0,1]`: the refinement collapses thirteen dimensions to
   points.
2. *(closure)* Substituting those and recomputing the leading coefficients settles 7–12
   coordinates per leaf, including `b44 = 1` and the "private" `b24 = b14 = 0` that appear in
   no Nash inequality at all.
3. *(leaf-independence and the knife-edges)* After the closure the unreached coordinates'
   leading coefficients are the **same six linear forms at all twelve leaves**; the leaf enters
   only through the reached conditions. They give, in every sequential equilibrium:
   **`b32 = 0`** (interior needs `2 r_{a41} = 3(r_{a11}+r_{a21})`, incompatible with `c33`'s
   knife-edge `(2−b22) r_{a41} = 4(1−b22) r_{a11} + 4 r_{a21}` — R11's `r₄ = 2(r₁+r₂)` at
   `b22 = 0` — and one-signed at every other ordering of P1's four openings; `b32 = 1` is
   outside the Nash window), **`c43 = 1`** (`b22 ≤ 1`), **`c13 = 0`** (`b22 ≤ 0.5841 < 1`),
   **`c34 = 0`** (`c34 = 1` forces `b22 = 0`, which forces `c34 = 0`), and then P1's card-2
   deterrence reads **`c33 ≥ 1/2`** — with `c33 ≤ 15/16` this makes `c33` interior in *every*
   sequential equilibrium, so the belief always sits on the knife-edge. **`b22 = 0`** (interior
   needs `3 r_{a11} = 2(r_{a31}+r_{a41})`, hence `b22 > 2/5` on the knife-edge, and
   `{b22 ≥ 2/5}` is certified empty on the refined system). Only `c23` keeps freedom (and
   `c33`, below): interior forces `r_{a21} = r_{a31} = 0` — trembles of different orders, which
   Kreps–Wilson consistency allows and which exact witnesses realise at all nine generic leaves —
   and such points have no uniform inward direction, so sequentiality and perfection part
   company there.
   *(The ratios must be normalised one information set at a time: each leading coefficient is
   homogeneous within a single set, and under one global simplex a whole set can vanish and the
   case becomes undecidable — 28 patterns that were undecided globally die instantly per set.)*
4. *(what `c33` keeps)* `c33 ≥ 1/2` is exact and unconditional and the Nash upper bound
   `c33 ≤ 1/2 + (3/4)(b11+b21) + β/4` is untouched, so over the sequential set
   `c33 ∈ [1/2, 15/16]` — exactly the **upper half** of its Nash window `[0, 15/16]`, every
   value attained at the parameter corner `b11 = b21 = 1/4`, and collapsing to the single
   point `1/2` at the corner sub-families `b11 = b21 = 0`.
5. *(the surviving interval)* At `b11 = b21 = 1/8`, `c11 = 1/4` the Nash window `c33 ∈ [1/2,
   23/32]` is entirely sequential (explicit positive beliefs `r_{a41} = 4/13`, the rest
   `1/13`) and its interior is perfect: an inward direction with `s* = 3715/28782 > 0`, every
   first-order condition strict but `c44`'s (true on the whole cube), and the indifference
   Jacobian of rank 8 — the implicit function theorem then gives the ε-perfect curve. The two
   endpoints are the two poles of ρ and are undecided at first order.

**The enumeration behind (3).** The 0 / 1 / interior patterns of the unreached coordinates are
enumerated leaf by leaf with no forcing injected, and **every pattern is decided with evidence an
independent checker replays** (`seqcert.py`, `checkseqcert.py`: 637 kill records, 3,554 box
certificates, 21 witnesses — each an exact Nash point with an explicit tremble curve; 12 / 12
leaves, 0 failed, 0 undecided). Exactly three patterns survive, each identical at every leaf of
its kind: at the nine generic leaves `b22 = 0, c23 = 0, c33` interior and `b22 = 0, c23`
interior, `c33` interior (the latter needing trembles of different orders); at the three corner
leaves (`b11 = b21 = 0`) `a34 = c32 = b22 = c23 = 0` with `a33`, `c33` interior. The corners are
the generic structure mirrored — P2's bet is the unreached one there, so P2's opening trembles
carry the beliefs and `c32, a33, a34` play `b32, c33, c34` — and their Nash windows
`a33, c33 ∈ [0, ½]` then collapse under refinement to **`a33 = c33 = ½`**. Two exact tests closed
the last cases: a leading form one-signed in its own ratios settles its coordinate at every
order, and a kill over all 75 orderings of a tremble group in which each class is normalised on
its own with strictly positive ratios. `perfwit.py` certifies a perfect equilibrium in the
`c23 = 0` pattern at three leaves.
*Trust:* Theorem 6 now meets the standard of Theorems 4 and 5 — every exclusion and every
witness is replayed by an independent checker. Its relaxation is sound under two restrictions
the checker enforces: belief rows multi-homogeneous in the sets' ratios, and one-signed kills
only for forms linear in one set's ratios (MASTER_DATA §16.13).

**Corollary 6.1 (open problem 2, for this game).** Extensive-form properness leaves `c33` an
interval of width `7/32`; normal-form properness (Theorem 3) selects the single interior point
`c33 = lo + w/3 = 55/96`. The two notions are therefore **not** equivalent here, and the
selection of Theorem 3 is a property of the normal form, as §12 item 7 suspected. The
machinery that decides this is the same everywhere: exact rational arithmetic, an LP in the
belief ratios with a Farkas certificate when it fails, and an exact witness when it succeeds
(`refine.py`, `seqset.py`, `seqrun.py`; MASTER_DATA §16.13).

---

*What the proof trusts.* (i) The game tree (`tree.py`, printed in words by `checkD.py -v`)
and the 48 gradients `D_i` recomputed from it independently (`checkD.py`); (ii) IEEE-754
round-to-nearest without fused multiply-add in numpy's elementwise ufuncs, for the interval
prunes (`ivl.py` rounds every operation outward); (iii) the checker itself, ~450 lines of
Fraction arithmetic with no solver — which checks that every certificate starts from a box
containing everything the node's labels allow (added 2026-09-26; all 66,699 leaf, 522 range
and 4.4M tree certificates re-verified under it, 0 failed). Nothing depends on sympy or scipy having been right: they
only *found* the certificates.

Item (ii) was the one a reader had to take on the arithmetic's word rather than on a
certificate's, and the third pass has removed it.

- **71 branches (`enumc2.py`).**  A betting branch is re-derived as a *certificate tree* in which
  every node the float propagation kills carries its own `certbox` certificate (or is kept alive
  and split), and `checkenum.py` replays the whole tree in Fractions.  4,394,323 certified nodes,
  1,877 support leaves all certified empty, **0 failed**.
- **The six that resisted (`enumc7.py`).**  Their pruning comes from interval propagation
  contracted along the whole path, which no certificate starting from a label box reproduces.
  `enumc7` carries out that propagation itself in EXACT rational arithmetic and records a
  certificate for every step.  Each certificate is a forced value, a chord narrowing justified
  by the convexity of the interval bound, or a contradiction.  `checkenum2.py`, written
  independently of the prover, replays every node from its parent's record.  26,223 nodes, 461
  support leaves all certified empty, **0 failed** (MASTER_DATA §16.9.1).

Controls for the new method:
- the silent branch reproduces the R ledger's 12 FAMILY leaves label for label;
- 64 certified equilibria survive the exact tree;
- every one of 2,463 tampered certificates is rejected.

So item (ii) is no longer trusted for any branch: **all 77 betting branches are verified end to
end, with no float arithmetic in any proof.**

---

## 8. Results, with every number

### R1 — the premise correction (frame this as a finding, not a caveat)

At an equilibrium there is no strictly improving deviation, so "exploitation direction" is
vacuous. The well-defined object is the *incidence* of a deviation. Feasible directions split
into **costly** (`du_A < 0`; ρ defined, measuring what fraction of A's loss lands on C) and
**costless** (`du_A = 0`; ρ has a zero denominator). See Proposition 3 for numbers.

### R2 — ρ is not well-defined, and not merely on a thin set **[G]**

- **19 of 48** parameters have `du_A ≡ 0` at *every* grid point:
  `a₃₃, a₄₄, b₁₁, b₁₂, b₂₁, b₂₂, b₃₂, b₃₃, b₄₁, b₄₂, b₄₄, c₁₃, c₁₄, c₂₃, c₂₄, c₃₃, c₃₄, c₄₃, c₄₄`.
- **21 more** have `du_A = 0` on part of the grid.
- Where nonzero, the denominator is **not bounded away from zero**: min |du_A| = **1.0e-4**
  against κ = 0.0417, i.e. within 0.25 %. ρ reaches **−50** and **+391** on the grid.
- The single most important case: P2's move **along the family** gives
  `du/dβ = (−κ, 0, +κ)` identically in all three sub-families, so with A = P2 the denominator
  is exactly zero while the numerator is κ ≠ 0. **The paper's headline phenomenon is precisely
  where ρ blows up.**

### R3 — costless vs equilibrium-preserving **[E]**

All three players have costless directions:

| player | costless coordinates | fraction of grid |
|---|---|---|
| P2 | `b₁₁, b₂₁, b₄₁` | 9,072 / 9,072 |
| P3 | `c₁₁, c₂₁` | 9,072 / 9,072 |
| P1 | `a₁₁, a₂₁, a₂₂, a₃₂, a₄₁` | 7,484 / 9,072 (boundary sub-manifolds only) |

**But none of the single-coordinate costless directions preserves equilibrium.** Stepping
ε = 0.01 along each:

| direction | du | exploitability after ε = 0.01 |
|---|---|---|
| P2 `+e_{b₁₁}` | (+1/12, 0, −1/12) | 8.33e-04 |
| P2 `+e_{b₂₁}` | (+1/24, 0, −1/24) | 8.33e-04 |
| P2 `+e_{b₄₁}` | (−1/24, 0, +1/24) | 4.17e-04 |
| P3 `+e_{c₂₁}` | (−0.0333, +0.0333, 0) | 9.17e-04 |
| P1 `+e_{a₁₁}` at boundary | (0, +0.0255, −0.0255) | 2.71e-03 |

By contrast the **along-family β direction** — `b₁₁, b₂₁, b₃₃, b₄₁` moving together — keeps
exploitability below 5e-16 at every point. So: *costless directions are common; costless
directions that stay inside the equilibrium set belong to P2 alone.* This is the precise
sense in which SGS's transfer result is special.

### R4 — sign of ρ **[G]**

- **Flips (+ and − both occur along one fixed direction, purely from moving free
  parameters):** `a₁₁, a₂₁, a₄₁`. For `+e_{a₁₁}`, ρ ranges over **[−48.75, +22.0]** with
  4,844 grid points negative, 906 in (0,1], 1,200 above 1.
- **Reaches 0 without flipping:** `a₃₂`, `c₃₁`.
- **Strictly positive wherever defined:** all of P2's and P3's costly directions.

Interpretation for the reader: ρ ∈ (0,1) means B and C split A's loss; ρ < 0 means C loses
too (B gains more than A loses); ρ > 1 means C gains more than A loses.

### R5 — exact closed forms for ρ (good "concrete anchor" material) **[E]**

- `ρ_{P2→P1}(+e_{b₃₁}) ≡ 3/5` **exactly, on the entire family** — every sub-family, every
  value of every free parameter. Derived by hand in §9.
- `ρ_{P3→P2}(+e_{c₃₁}) = (2 − 4s)/(4 − 5s)` with `s = b₁₁ + b₂₁`; it depends on `b₁₁` and
  `b₂₁` only through their sum, is independent of `c₁₁`, and reaches exactly 0 at `s = ½`,
  the extreme corner `b₁₁ = b₂₁ = ¼` of the family.
- `ρ_{P1→P3}(+e_{a₃₁}) ∈ [3/11, 2/5]`, depending on `b₁₁` and `b₂₁` separately, and
  independent of `c₁₁, b₃₂, c₃₃`.

### R6 — off-path parameters determine both the location and the value of ρ **[E]**

`b₃₂, c₃₃, c₃₄, c₄₄` have **exactly zero** first derivatives for all three players at all
9,072 points (max |du_i/dx| = 0.000e+00), and `c₃₄, c₄₄` have exploitability 7.3e-17 for
*every* value in [0,1] — nobody's incentive constrains them at all. Yet their mixed second
derivatives through P1's openings are nonzero:

| x | ∂²u/(∂a₁₁∂x) | ∂²u/(∂a₂₁∂x) | via a₃₁ | via a₄₁ |
|---|---|---|---|---|
| `c₃₄` | (0, +κ, −κ) | (0, +κ, −κ) | 0 | 0 |
| `c₄₄` | (0, −2κ, +2κ) | (0, −2κ, +2κ) | 0 | 0 |
| `c₃₃` | (−4κ, 0, +4κ) | (−4κ, 0, +4κ) | 0 | (+2κ, 0, −2κ) |
| `b₃₂` | (−4κ, +3κ, +κ) | (−4κ, +3κ, +κ) | 0 | (+2κ, −2κ, 0) |

`c₄₄` requires `b₃₂ > 0` to be reachable at all (to sit at BC holding the 4, P3 needs P2 to
have called with something other than the 4; P2's only other calling card is the 3, with
probability `b₃₂`): reach after `a₁₁ = 0.5` is 0 at `b₃₂ = 0`, 0.00208 at `b₃₂ = 0.10`,
0.00833 at `b₃₂ = 0.40`.

**The clean statement:** *unconstrained is not inert.* And ρ has **two independent sources of
indeterminacy** — the denominator, via `b₃₂` and `c₃₃`, which are constrained but by an
inequality whose boundary is attainable (giving a pole); and the numerator, via `c₃₄` and
`c₄₄`, which are constrained by nobody, so ρ's value is undetermined even far from any pole.

### R7 — the pole census, with witnesses **[E,G]**

Closed-form root solves (recall each `∂u/∂x` is affine in each free parameter):

| deviation | zero of `du_owner/dx` sits at | max error | round |
|---|---|---|---|
| `+e_{a₁₁}` | `lo = ½ − b₃₂`, Table 3's **lower** bound on c₃₃ | 6.7e-16 | 1 |
| `+e_{a₂₁}` | same `lo` (Lemma 5 gives `du₁/da₂₁ = du₁/da₁₁` once `a₂₂=a₂₃=0`) | 6.7e-16 | 1 |
| `+e_{a₄₁}` | `hi = lo + ¾(b₁₁+b₂₁) + β/4`, Table 3's **upper** bound | 1.2e-15 | 1 |
| `+e_{a₃₁}` | **no root** — no `c₃₃` dependence at all, 48/48 cases | — | 1 |
| `+e_{a₂₂}` | `c₁₁^max = (2−b₁₁)/(3+2b₁₁+2b₂₁)`, Table 3's **upper bound on c₁₁** | 7.8e-16 | **2** |
| `+e_{a₃₂}` | `b₂₁ = (1 − 8c₁₁b₁₁)/(4 − 8c₁₁)`; in sub-family A this is `b₂₁ = ¼`, Table 3's cap | 2.7e-15 | **2** |

So **Table 3's `c₃₃` interval is exactly P1's deterrence window**: its lower bound exists to
kill `a₁₁`/`a₂₁`, its upper bound to kill `a₄₁`. Both are attainable, so there is a pole at
each end, for different deviations, approached from opposite sides:

```
 c33 position     du1/da11     rho(a11)     du1/da41     rho(a41)
 lo (endpoint)   +0.0000000   undefined    -0.0218750   +1.38
 lo + 1e-4       -0.0000044   -9999.00     -0.0218728   +1.38
 midpoint        -0.0218750   -1.00        -0.0109375   +1.76
 hi - 1e-4       -0.0437456   -0.00        -0.0000022   +3810.52
 hi (endpoint)   -0.0437500   +0.00        +0.0000000   undefined
```

Each direction is perfectly well behaved at the *other's* pole. The pole is not isolated:
`du₁/da₁₁ = du₁/da₂₁ = 0` identically along the whole line `c₃₃ = ½ − b₃₂` (checked at
`b₃₂ = 0, 0.15, 0.30, 0.45`, exploitability 7.3e-17 throughout) — a codimension-1 surface.

**Three negative controls, one per clause of Theorem 1:**

| control | clause it fails | evidence |
|---|---|---|
| `b₃₄` (round 2) | (ii) not attainable | root at `b₃₁ = 1`, Table 3 pins `b₃₁ = 0`; `du₂/db₃₄ ≡ −0.0208`, ρ ≡ 1 |
| `c₂₂` (round 2) | (iii) numerator vanishes | root at `b₁₁=b₂₁=0` **is** attainable, but ρ ≡ 0.800 exactly as `b₁₁=b₂₁ → 0`, then 0/0 |
| `a₁₁`, `a₂₁` at `b₃₂ > ½` | (ii) not attainable | `c₃₃* = ½ − b₃₂ < 0`, outside [0,1] |

**Census over all 48 parameters:**

| | round-1 poles | round-2 poles |
|---|---|---|
| **P1** | `a₁₁, a₂₁, a₄₁` | `a₂₂, a₃₂` |
| **P2** | none | none |
| **P3** | `c₁₁, c₂₁` | none |

So the mechanism is **neither** specific to opening bets **nor** specific to P1. What is
specific to P1 is *where the boundary lives*: P1's round-1 poles are located by `b₃₂`/`c₃₃`,
which are off-path. P3's poles sit at boundaries in on-path parameters (`b₁₁, b₂₁, b₂₃`).
P2 has no poles at all — every P2 direction either has `du₂ ≡ 0` or a bounded, constant ρ.

### R8 — exact residues **[E]**

| dev | D′/κ | c₃₃* | transfer t | R = t/D′ |
|---|---|---|---|---|
| a₁₁ | −4 | +0.1000 | +0.04375000 | −0.26250000 = **−21/80** |
| a₂₁ | −4 | +0.1000 | +0.04375000 | **−21/80** |
| a₄₁ | +2 | +0.3625 | −0.00833333 | **−1/10** |
| a₁₁ | −4 | +0.5000 | −0.03645833 | **+7/32** |
| a₂₁ | −4 | +0.5000 | −0.01562500 | **+3/32** |
| a₄₁ | +2 | +0.7375 | +0.02083333 | **+1/4** |
| a₁₁ | −4 | +0.2000 | +0.06875000 | **−33/80** |
| a₂₁ | −4 | +0.2000 | +0.04270833 | **−41/160** |
| a₄₁ | +2 | +0.4500 | −0.00416667 | **−1/20** |

Rate confirmed: `ρ·(c₃₃ − c₃₃*)` converges to R at one decade of relative error per decade of
offset (3.81e-02 at 1e-2 → 3.19e-08 at 1e-8; the floor near 1e-8 is float cancellation, not a
departure from the model).

### R9 — two-player control **[E,G]**

Independent from-scratch solver (3 cards, 6 deals, **30 leaves**), standard one-parameter
family α ∈ [0, 1/3]. Verified first: max exploitability **1.9e-16** over 201 α;
`u₁ = −1/18` exactly (rational check at α = 1/6 gives `(−1/18, +1/18)`); α outside [0,⅓] is
genuinely exploitable (0.020 at α = −0.02, 0.010 at α = ⅓+0.02), so the interval is exactly
right.

**Reason 1 — no third party.** Over 201 α × every feasible coordinate direction:

```
strictly costly (du_A < 0)         : 1403
du_A = 0 AND opponent moves        :    0   <- costless transfers
du_A = 0 and nothing moves (null)  : 2011
max |du_1 + du_2|                  : 0.000e+00
```

Every free-parameter direction is exactly `(0,0)`, against the three-player counterparts
`du/db₁₁ = (+1/12, 0, −1/12)`, `du/db₂₁ = (+1/24, 0, −1/24)`, `du/db₄₁ = (−1/24, 0, +1/24)`.
ρ is **identically 1** over all 1,403 defined pairs — range
`[1.000000000000000, 1.000000000000000]` — even with |du_A| down to 8.3e-4.

**Reason 2 — no slack either.** The off-path region exists only at the single endpoint α = 0
(where P1 never bets), not family-wide. And those parameters are pinned to a **point**:

| | zero-exploitability set | width |
|---|---|---|
| 2p `y₁₂` (family value 0) | [0.000000, 0.000000] | **0 — no slack** |
| 2p `y₂₂` (family value 1/3) | [0.333333, 0.333333] | **0 — no slack** |
| 2p `y₃₂` (family value 1) | [1.000000, 1.000000] | **0 — no slack** |
| 3p `c₃₃` at b₁₁=b₂₁=0.15, b₃₂=0.40 | [0.1000, 0.3625] | **0.2625 — slack** |

**Interchangeability contrast.** 2-player: `u₁ = −1/18` for every α, spread **2.4e-16**.
3-player: `u₁ ∈ [−0.03125, −0.02083]` and `u₃ ∈ [0.04167, 0.05208]`, spread **κ/4 each**,
while `u₂` is pinned at −κ/2 (spread 2.8e-16).

### R10 — the one genuinely improving direction **[E]**

SGS's Table 4 deliberately mixes sub-families (P2 from `c₁₁=½`, P3 from `c₁₁=0`) and is not
an equilibrium. P2's exact exploitability there is **0.0104167 = κβ**, matching the paper.
The improving direction is `−e_{b₂₃}`, with

```
du₁/dε = 0    du₂/dε = +0.083333 = 2κ    du₃/dε = −0.083333
ρ_{P2→P1} = 0.0000    ρ_{P2→P3} = 1.0000
```

P2's entire gain comes out of P3; P1 is untouched. The magnitudes tie out:
`2κ × (1/8) = κ/4 = κβ`. This is a useful sanity anchor — the one place in the whole study
where the denominator is positive.

### R11 — does an equilibrium refinement collapse the indeterminacy? **Partly — and it separates the two sources** **[E]**

> **Superseded by Theorem 6 (§7.3).** R11 is a numerical probe on a slice of the family, with
> only P1's openings trembling. Theorem 6 decides the same question exactly on the complete
> Nash set with every coordinate trembling: every finding below survives (`b32 = 0`, `c34 = 0`,
> `c44 = 1`, the knife-edge `r₄ = 2(r₁+r₂)`, the refined `c33 ≥ ½`), and more is pinned —
> every off-path coordinate except `c23` and `c33`.

All of ρ's indeterminacy lives at information sets of reach probability zero, which is
exactly what Selten (1975) and Kreps & Wilson (1982) refinements discipline. We test this
directly: perturb P1's opening with trembles `a_{j1} = ε·r_j`, so every information set has
positive reach; then the owner's optimal action at each off-path set is decided by the sign
of `∂u_owner/∂x`, normalized by the set's reach, and the belief there is an explicit function
of the ratio vector `r`.

**(a) Two parameters are pinned by dominance, belief-free.** The per-unit-reach advantage of
the aggressive action is *identical* under every tremble ratio tested, including wildly
asymmetric ones:

| r | `c34` advantage | `c44` advantage |
|---|---|---|
| (1,1,1,1) | −1.000000 | +5.000000 |
| (1,1,1,4) | −1.000000 | +5.000000 |
| (1,1,1,8) | −1.000000 | +5.000000 |
| (5,1,1,1) | −1.000000 | +5.000000 |
| (1,5,1,0.2) | −1.000000 | +5.000000 |
| (0.1,3,7,1) | −1.000000 | +5.000000 |

Reason for `c34`: at BC holding the 3, P2 has called, and in this family P2 calls only with
the 4 or the 3 (probability `b32`); P3 holds the 3, so P2 holds the 4 and P3 loses for
certain. Folding is dominant, and calling costs exactly one more chip — hence −1 exactly.
**Table 3 leaves `c34` free in [0,1]; any refinement forces `c34 = 0`.** The `c44 = 1` of
Table 2 is independently confirmed (advantage exactly +5).

**(b) `c33` is belief-dependent, and the belief is a knife-edge.** At P3's BF/card-3 set the
pot is 4; folding costs 1, calling risks 2 to win 3. So calling beats folding iff
`3q − 2(1−q) > −1`, i.e. **q > 1/5**, where `q = P(P1 holds 1 or 2 | P1 bet, P2 folded, P3
holds the 3)`. From the tree, `q = (r₁+r₂)/(r₁+r₂+2r₄)` — indifference iff
**`r₄ = 2(r₁+r₂)`**. Confirmed numerically (advantage 8.3e-14 at `r = (1,1,1,4)` and at
`(0.5,0.5,1,2)`):

| r₄ | q | `c33` advantage | P3 wants |
|---|---|---|---|
| 0.5 | 0.66667 | +2.333333 | call |
| 1 (uniform) | 0.50000 | +1.500000 | call |
| 2 | 0.33333 | +0.666667 | call |
| **4** | **0.20000** | **+0.000000** | **indifferent** |
| 8 | 0.11111 | −0.444444 | fold |

Off the knife-edge P3 strictly prefers a corner, and **both corners lie outside Table 3's
deterrence window**: at `c33 = 1` the profile is not even Nash — P1 exploits it by
5.3 × 10⁻². So the SGS family is sequentially rational only on a one-dimensional knife-edge
in tremble-ratio space. Verified that the knife-edge holds across the family (5 points
spanning all three sub-families, all indifferent to ≤ 1.8e-13).

**(c) The consistency check, and what it forces.** The knife-edge must simultaneously satisfy
`b32`. It does, and it bites:

| r₄ | `c33` adv | `b32` adv | `c33` admissible? | `b32` admissible? |
|---|---|---|---|---|
| 1 | +1.500000 | +0.666667 | no | no (→1, outside Table 3) |
| 3 | +0.250000 | −0.000000 | no | yes (mix) |
| **4** | **+0.000000** | **−0.166667** | **yes (mix)** | **yes (→0)** |
| 8 | −0.444444 | −0.500000 | no | yes (→0) |

At the unique admissible ratio, P2 strictly folds at B/card-3, so **`b32 = 0` is forced**.

**(d) The refined face, and the consequence for ρ.** Refinement therefore selects the face
`b32 = 0, c34 = 0` of the equilibrium polytope. With `b32 = 0`, Table 3's `c33` window becomes
`[1/2, b32^max]` — still an interval, still with both endpoints attainable:

| b₁₁ | b₂₁ | refined `c33` interval | width | `a11` lower edge | `a41` upper edge |
|---|---|---|---|---|---|
| 0.15 | 0.15 | [0.5000, 0.7625] | 0.2625 | **POLE** | **POLE** |
| 0.10 | 0.20 | [0.5000, 0.7750] | 0.2750 | **POLE** | **POLE** |
| 0.25 | 0.25 | [0.5000, 0.9375] | 0.4375 | **POLE** | **POLE** |
| 0.20 | 0.05 | [0.5000, 0.7375] | 0.2375 | **POLE** | **POLE** |
| 0.00 | 0.00 | [0.5000, 0.5000] | 0 (degenerate) | POLE | none |

The refined face is a sub-family of Table 3 and remains exactly Nash (max exploitability
2.2e-16). And once `b32 = 0` is forced, `reach(c44) = 0` even after a P1 deviation, so
**`c44` becomes genuinely inert** — the refinement removes it from the numerator too.

**The headline.** Refinement kills the **numerator** source of indeterminacy — `c34`, `c44`
and `b32` are all pinned — and with it ρ's sign ambiguity: on the refined face
`ρ(+e_{a11}) ∈ [1.395, 45.42]` over 250 sampled points, **strictly positive, no sign flip**,
against the unrefined range `[−48.75, +22.00]` which did flip. But the **denominator** source
survives untouched: the `c33` interval is merely relocated, not shrunk, and **both poles
remain at both endpoints**.

> **Refinement makes ρ's sign determinate. It does not make ρ finite.** The two sources of
> indeterminacy identified in R6 come apart cleanly under refinement, which is a stronger
> statement than either "refinement fixes it" or "refinement does nothing".

### R12 — the hard floor: the window and the transfer are the same currency **[P,E]**

`lo = ½ − b₃₂` and `hi = b₃₂max − b₃₂`, so the `b₃₂` terms cancel and the window width is

> **w = hi − lo = ¾(b₁₁ + b₂₁) + β/4**,  independent of `b₃₂`.

Verified in exact rational arithmetic at six family points spanning all three sub-families:

| point | b₁₁ | b₂₁ | b₃₂ | w measured | w formula | κβ |
|---|---|---|---|---|---|---|
| B, b₃₂=2/5 | 3/20 | 3/20 | 2/5 | **21/80** | 21/80 | 1/160 |
| B, refined face | 3/20 | 3/20 | 0 | **21/80** | 21/80 | 1/160 |
| A, refined face | 1/10 | 1/5 | 0 | **11/40** | 11/40 | 1/120 |
| A, corner β=1/4 | 1/4 | 1/4 | 0 | **7/16** | 7/16 | 1/96 |
| C, refined face | 1/5 | 1/20 | 0 | **19/80** | 19/80 | 1/120 |
| C, b₂₃ at max | 1/4 | 0 | 0 | **1/4** | 1/4 | 1/96 |

Every term of `w` is non-negative, so `w = 0 ⟺ b₁₁ = b₂₁ = 0 ⟺ β = 0 ⟺ κβ = 0`.
**Deterrence slack and the SGS utility transfer are the same currency.** One cannot respond to
the indeterminacy by shrinking the window, because the window closes exactly when the transfer
the paper is about vanishes.

**And the collapse is not symmetric.** At `b₁₁ = b₂₁ = 0` the window degenerates to `{½}`:

| dev | `D′/κ` | `t = du₂` at `c₃₃*` | `du₃` | `du₁` | verdict |
|---|---|---|---|---|---|
| `a₁₁` | −4 | **−1/48** | +1/48 | 0 | **still a POLE** |
| `a₄₁` | +2 | 0 | 0 | 0 | 0/0, clause (iii) fails |

`a₄₁`'s numerator vanishes with the window, so its pole dies. `a₁₁`'s does not — the singular
point becomes the *only admissible value* of `c₃₃`. Shrinking the window is doubly futile.

### R13 — properness pins `c₃₃`, and ρ becomes determinate **[P,E]**

**Setup.** Write `cost(a_{j1}) = −du₁/da_{j1} ≥ 0` for what P1 forgoes by opening with card j.
From Lemma 5, `cost(a₁₁) = cost(a₂₁) = 4κ(c₃₃ − lo)` and `cost(a₄₁) = 2κ(hi − c₃₃)`.

**The argument.** Myerson properness orders trembles by cost: if `cost(a) > cost(a′)` then
`σ(a) ≤ ε·σ(a′)`. Combined with R11's belief `q = (r₁+r₂)/(r₁+r₂+2r₄)` and P3's threshold
`q = 1/5`:

- `cost(a₁₁) < cost(a₄₁)` ⟹ `r₄/(r₁+r₂) → 0` ⟹ `q → 1 > 1/5` ⟹ P3 strictly calls ⟹ `c₃₃ = 1`,
  outside the window (`hi ≤ 15/16`). Contradiction.
- `cost(a₁₁) > cost(a₄₁)` ⟹ `q → 0 < 1/5` ⟹ P3 strictly folds ⟹ `c₃₃ = 0`, outside the window
  whenever `b₃₂ < ½`. Contradiction.
- Hence an interior `c₃₃` requires **cost equality**: `4(c₃₃ − lo) = 2(hi − c₃₃)`, i.e.

> **c₃₃ = lo + w/3.**

At that point properness imposes no constraint between the now-equal-cost actions, so the
knife-edge ratio `r₄ = 2(r₁+r₂)` is admissible and P3 is exactly indifferent — a consistent
fixed point.

**Exact verification** (rational arithmetic, six points, all three sub-families):

| point | `c₃₃* = lo + w/3` | cost a₁₁ | cost a₂₁ | cost a₄₁ | equal? | cost a₃₁ | a₃₁ costliest? |
|---|---|---|---|---|---|---|---|
| B, b₃₂=2/5 | 3/16 | 7/480 | 7/480 | 7/480 | ✓ | 73/960 | ✓ |
| B, refined face | 47/80 | 7/480 | 7/480 | 7/480 | ✓ | 73/960 | ✓ |
| A, refined face | 71/120 | 11/720 | 11/720 | 11/720 | ✓ | 7/96 | ✓ |
| A, corner β=1/4 | 31/48 | 7/288 | 7/288 | 7/288 | ✓ | 11/192 | ✓ |
| C, refined face | 139/240 | 19/1440 | 19/1440 | 19/1440 | ✓ | 73/960 | ✓ |
| C, b₂₃ at max | 7/12 | 1/72 | 1/72 | 1/72 | ✓ | 7/96 | ✓ |

`a₃₁` is always the costliest opening, so properness gives it the smallest tremble — and `r₃`
cannot affect the `c₃₃` belief in any case, since P3 holds the 3 at that set so P1 cannot.

**Both corners are excluded** by the same mechanism. At `c₃₃ = lo`, `cost(a₁₁) = 0` while
`cost(a₄₁) = 2κw > 0`, so `a₄₁` is strictly worse, `r₄/(r₁+r₂) → 0`, `q → 1`, and P3 calls —
giving `c₃₃ = 1 ≠ lo`. At `c₃₃ = hi` the mirror argument gives `c₃₃ = 0 ≠ hi`:

| point | at `c₃₃ = lo` | at `c₃₃ = hi` |
|---|---|---|
| B, b₃₂=2/5 | cost a₁₁ = 0, cost a₄₁ = 7/320 → a₄₁ strictly worse | 7/160 vs 0 → a₁₁ strictly worse |
| A, refined face | 0 vs 11/480 | 11/240 vs 0 |
| A, corner β=1/4 | 0 vs 7/192 | 7/96 vs 0 |

**Consistency at the other off-path sets.** At the properness point, `b₃₂` advantage is
−0.1667 (→ `b₃₂ = 0` forced), `c₃₄` advantage is −1.0000 (→ `c₃₄ = 0` forced), and `c₄₄` shows
+5 where `b₃₂ > 0` (→ `c₄₄ = 1`) and `nan` wherever `b₃₂ = 0` because `reach(c₄₄) = 0` even
under trembles — `c₄₄` is inert on the refined face, exactly as R11 found. Every selected
profile is exactly Nash (exploitability ≤ 2.2 × 10⁻¹⁶). With `b₃₂ = 0`, `lo = ½`, so the
selected point is **`c₃₃ = ½ + w/3`**.

**The selected ρ is finite and exactly rational:**

| point | w | ρ(a₁₁) | ρ(a₂₁) | ρ(a₄₁) |
|---|---|---|---|---|
| B, b₃₂=2/5 | 21/80 | **−4/7** | −4/7 | **11/7** |
| B, refined face | 21/80 | **20/7** | 20/7 | **−5/7** |
| A, refined face | 11/40 | **73/22** | 49/22 | **−7/11** |
| A, corner β=1/4 | 7/16 | **5/2** | 29/14 | **−5/7** |
| C, refined face | 19/80 | **83/38** | 143/38 | **−11/19** |
| C, b₂₃ at max | 1/4 | **7/4** | 29/8 | **−1/2** |

Every value finite, every value an exact rational. Properness turns ρ from an unbounded,
sign-ambiguous quantity into a determinate one.

**Scope caveat, stated in the paper.** This is Myerson properness on the **normal form**,
where whole pure strategies are ordered by expected cost and the behavioural tremble rates
`r_j` inherit that ordering. *Agent*-normal-form properness compares only actions within a
single information set, and would not order `a₁₁` against `a₄₁` — P1 holding the 1 and P1
holding the 4 are different information sets. The step from normal-form tremble probabilities
to the behavioural rates `r_j` is where the modelling assumption sits; state it explicitly.

### R14 — does MCCFR select the proper equilibrium? No, and it is biased **[E,G]**

150 seeds of external-sampling MCCFR (Lanctot et al. 2009), 10⁶ iterations each, 660 s wall
clock on 27 workers. The solver is an independent reimplementation of the game; its tree
agrees with the main engine to **1.1 × 10⁻¹⁶** on 200 random profiles.

**Step 0, exploitability first.** Median max-player exploitability **0.001503**, mean 0.001703,
range [0.000467, 0.005465] — i.e. a median of **3.6 % of κ**. These are approximate equilibria,
not exact ones, and every statement below is conditioned on that.

**Step 1, family membership — the outputs are mostly NOT in the family.** The pinned Table 2/3
parameters come out right (`a₁₁, a₂₁, a₃₁ ≈ 0`; `a₃₃ = 0.5054 ± 0.0095`; `c₄₁ = 1.0000` exactly).
But the *sub-family* conditions fail:

| | seeds |
|---|---|
| sub-family A (`c₁₁ ≈ 0`, `b₁₁ ≤ b₂₁`) | 29 / 150 |
| sub-family B (`0 < c₁₁ < ½` **and** `b₂₁ = b₁₁`) | 11 / 150 |
| sub-family C (`c₁₁ ≈ ½`, `b₂₁ ≤ min{b₁₁, ½−2b₁₁}`) | 11 / 150 |
| **in none of the three** | **99 / 150** |

The dominant failure: 109 seeds have intermediate `c₁₁`, which requires sub-family B and hence
`b₂₁ = b₁₁` exactly — but `|b₂₁ − b₁₁|` has median **0.111**. CFR sits *between* sub-families,
on a locus the family does not contain. Max-norm distance to the nearest same-parameter family
profile: median 0.038, max 0.286, dominated by `b₃₃`.

This is suggestive — but not conclusive — evidence bearing on SGS's own open question of
whether other equilibria exist outside the family: the residual distance is far larger than
the exploitability would suggest for a profile converging *into* the family. It could equally
be under-convergence. Report it as suggestive.

**Step 3, β is systematically biased.** β mean **0.1687**, sd 0.0499, range [0.0545, 0.2734] —
never near 0, and 9 seeds above the valid ceiling of 1/4. Since `u₁ = −κ(½+β)` and
`u₃ = κ(1+β)`, this means MCCFR systematically hands P3 about **κ·0.169 ≈ 0.0070 chips** at
P1's expense relative to the β = 0 member. **A per-seat bias produced by the solver, not the
game** — directly relevant to how three-player benchmark numbers are read.

**Step 4, `c₃₃` is not selected.** Its position in `[lo, hi]` as a fraction (0 = lower pole,
1/3 = the properness point, 1 = upper pole):

| | mean | sd | \|frac − 1/3\| | \|frac − 1/2\| |
|---|---|---|---|---|
| all 150 seeds | 0.4845 | 0.2739 | 0.2564 | 0.2408 |
| best-converged quartile (38) | 0.4125 | 0.2350 | **0.1886** | 0.2154 |

Correlation of `frac` with exploitability **+0.076**, with `reach(c₃₃)` **−0.000**, with β
**−0.050**. It is noise. In the best-converged quartile the properness point is the closer
hypothesis, but with sd 0.235 neither fits: **`c₃₃` is dispersed, and MCCFR selects nothing.**
The mechanism is plain from the reach column — the off-path sets are visited with probability
`b₃₂ ≈ 1.4e-3`, `c₃₃ ≈ 1.2e-3`, `c₃₄ ≈ 2.0e-4`, `c₄₄ ≈ 9.5e-6`, so CFR gets almost no training
signal exactly where the indeterminacy lives.

**Step 5, the refined face — a clean split.** `c₃₄ < 0.02` in **139/150** seeds (median 0.0002),
agreeing with the refinement prediction. `b₃₂ < 0.02` in only **41/150** (median 0.072; the
best-converged quartile is *worse*, median 0.133), disagreeing with it.

> **CFR reproduces the refinement predictions that follow from belief-free dominance, and not
> those that require a particular tremble structure.** `c₃₄ = 0` is dominance; `b₃₂ = 0`
> depends on the knife-edge ratio. The algorithm has no reason to respect the latter, and does
> not.

### R15 — does it generalize? Not in N, yes in n **[P,E,G]**

Full detail in `GENERALIZATION.md`. Two new exactly-validated engines: `kuhnNp.py` (3-player,
N cards; reproduces `kuhn3p` with **0.0** discrepancy) and `kuhnGen.py` (**n**-player, N cards;
reproduces `kuhnNp` for n=3 with **0.0** on utilities, exploitability and reach). The betting
rule gives `n·2^(n-1)+1` leaves per deal and `2^(n-1)` situations per player, both confirmed
exactly; (n,N) = (5,7) is 204,120 leaves and builds in 1.35 s.

**The general theorem.** Multilinearity + constant-sum alone give, for every n and N:
`Σ_k s_k = 1` where `s_k = (∂u_k/∂y)/(−∂u_A/∂y)` — so incidence lives on an **(n−2)-simplex**;
each share is an exact **Möbius transform** of any other coordinate, hence a pole of order ≤ 1;
and an off-path coordinate has **exactly zero** first derivatives, so the admissible set for it
is an interval and every pole sits on that interval's boundary. Verified: multilinearity
1.1e-15→1.1e-14, `|Σ du|` 1.1e-15→2.1e-14, `|Σ s − 1|` 2.8e-13→8.7e-12, Möbius prediction error
3.3e-15→8.5e-12, off-path first derivatives **0.00e+00**, across (n,N) = (3,4)…(5,6).

**ρ is a scalar only at n = 3.** The achievable share set has affine rank exactly **n−2** —
1, 2, 3 at n = 3, 4, 5 — saturating the bound, and rank 2 in 24/24 independent n=4 seeds. The
paper's ρ is the lowest non-trivial case of a vector-valued object.

**Adding cards kills the phenomenon.** 50 MCCFR seeds at n=3, N=5: the off-path set is
`b5_3, b5_4` in **50/50** seeds, 100 (x,y) pairs move an incentive, and **0** have an attainable
root — the roots run **1.216 to 2.966**, missing [0,1] by at least 0.216. Clause (ii) fails
uniformly. Cause: at N=4 P1 never bets; from N=5 on P1 value-bets the top card ~80%, so the
off-path region that carries the mechanism is reached.

**Adding players restores it.** 24 seeds at n=4, N=5: **619 genuine poles, 24/24 seeds**, roots
0.036–0.9997 (median 0.639), numerator median 0.021. The dominant pole pairs are `b5[B]` and
`c5[BF]` driving P1's openings — structurally identical to the n=3, N=4 mechanism.

**The unifying variable, confirmed over 108 runs.** P1 goes silent exactly when **N = n+1**, with no overlap: max opening probability **0.011 / 0.010 / 0.024** at (3,4) / (4,5) / (5,6), against **0.828 / 0.850 / 0.826** at (3,5) / (4,6) / (5,7). Attainability tracks it — the fraction of roots inside [0,1] is **70 / 62 / 54 %** when N = n+1 versus **0 / 8 / 1 %** when N > n+1. So the governing variable is how close the deck is to minimal, not deck size or player count alone. Affine rank = n−2 held in all 108 seeds. (N > n+1 is not *exactly* pole-free: (3,5) is 0/20 but (4,6) and (5,7) leak a few.)

**Seat asymmetry persists at n=4:** P1 −0.01412, P2 −0.01396, P3 −0.00847, **P4 +0.03656**
(sd ≤ 0.0018 over 24 seeds).

---

## 9. The hand-checkable worked example (put this in an appendix)

A referee should be able to redo one number without running code.

**Point.** Sub-family A, `b₁₁ = b₂₁ = 0` (so β = 0), `b₂₃ = 0`, `b₃₂ = 0`, `c₃₃ = ½`,
`c₃₄ = 0`. Then P1 and P2 never bet; P3 bets the 4 always and the 2 half the time after two
checks. Facing P3's bet, P1 calls only with the 4 (`a₄₂ = 1`); if P1 folds, P2 calls with the
4 always and the 3 half the time (`b₃₃ = ½`). Utilities `(−1/48, −1/48, +1/24)`, matching
`(−κ(½+0), −κ/2, κ(1+0))`.

**Deviation.** A = P2, `d = +e_{b₃₁}`: P2 starts betting the 3 after P1 checks. Only the
**6 deals where P2 holds the 3** are affected, so the whole derivative is six rows.

| deal (P1,P2,P3) | P2 **bets** | P2 **checks** | difference |
|---|---|---|---|
| (1,3,2) | (−1, 2, −1) | (−1, 3/2, −1/2) | (0, +1/2, −1/2) |
| (1,3,4) | (−1, −2, 3) | (−1, −3/2, 5/2) | (0, −1/2, +1/2) |
| (2,3,1) | (−1, 2, −1) | (−1, 2, −1) | (0, 0, 0) |
| (2,3,4) | (−1, −2, 3) | (−1, −3/2, 5/2) | (0, −1/2, +1/2) |
| (4,3,1) | (+3, −2, −1) | (+2, −1, −1) | (+1, −1, 0) |
| (4,3,2) | (+3, −2, −1) | (+5/2, −1, −3/2) | (+1/2, −1, +1/2) |
| **sum** | | | **(+3/2, −5/2, +1)** |

Multiply by κ = 1/24: `du = (+1/16, −5/48, +1/24)`; zero-sum check
`3/48 − 5/48 + 2/48 = 0`. With A = P2 and C = P1, `ρ = −(1/16)/(−5/48) = 3/5`, complement
2/5. Engine agrees to 2.7e-12 by both central difference and exact derivative.

**Why it is 3/5 everywhere — the general computation.** Carrying the same six deals with
`b₃₃`, `c₁₁`, `c₂₁` symbolic:

```
du₁ = (1/24) [ (1 − c₁₁) + (1 − c₂₁) ]                      = (1/24)(2 − (c₁₁+c₂₁))
du₂ = (1/24) [ (c₁₁+c₂₁)(3 − 4b₃₃) + 2b₃₃ − 4 ]
```

Table 3 sets `c₂₁ = ½ − c₁₁`, so `c₁₁ + c₂₁ = ½` identically, and both collapse:
`du₁ = (3/2)/24` and `du₂ = (−5/2)/24`, **independent of `b₁₁, b₂₁, b₂₃, b₃₃, c₁₁, b₃₂,
c₃₃, c₃₄`**. Hence `ρ ≡ 3/5` on the whole family. Verified against the engine at points with
`b₃₃` ranging over [0.5, 0.875] and `c₁₁` over [0, 0.5]; also verified that breaking
`c₁₁ + c₂₁ = ½` breaks the constancy (e.g. `c₁₁=0.20, c₂₁=0.10` gives
`du₁ = +0.0708, du₂ = −0.1050`). **[E]**

**Contrast at the same point.** `+e_{b₁₁}` gives `(+1/12, 0, −1/12)`: P2 pays nothing, P1
gains 1/12, P3 loses 1/12, and ρ = −(1/12)/0 is undefined. Same grid point, same player, one
direction with a clean rational share and one with no share at all.

---

## 10. Figures and tables

Existing figures (in this directory, regenerate with `plots.py` / `plots2.py`):

| file | caption draft |
|---|---|
| `fig1_rho_parallel_direction.png` | ρ against β for the one deviation that is structurally identical for all three players — "bluff-bet the 3 in the opening round" (`a₃₁`/`b₃₁`/`c₃₁`) — on four slices through the three sub-families, 201 points each. P2's is exactly 3/5 everywhere; P1's and P3's move with the parameters. |
| `fig2_rho_illdefined_and_signflip.png` | Left: the three directional derivatives for `+e_{a₁₁}` as `c₃₃` sweeps its valid interval. Middle: ρ diverging through the pole and crossing zero along the *same* direction. Right: 121×121 sign map of ρ over (β, c₃₃) with the zero contour drawn. |
| `fig3_costless_transfers.png` | The four costless directions — P2's along-family β move plus one single-coordinate direction per player — each showing `du_A/dε ≡ 0` while the other two move equal and opposite. |
| `fig4_offpath_deterrence.png` | Left: Table 3's `c₃₃` interval coincides exactly with P1's deterrence window. Middle: each endpoint is a pole for a *different* deviation — `a₁₁`/`a₂₁` at the lower edge, `a₄₁` at the upper, `a₃₁` never. Right: slack versus no slack — an interval of equilibria against a single point. |

Figures worth adding for a paper:

- **A game-tree figure** with the four situations labelled. Redraw rather than reuse SGS's
  Figure 1; readers need it to follow the notation.
- **A schematic of the three-part pole criterion** — a decision diagram with the three
  witnesses attached. This is the paper's conceptual core and currently exists only as prose.
- **The 2-player/3-player contrast as a single two-panel figure**: utilities across the
  family (flat line vs two diverging lines), and ρ across the family (constant 1 vs a curve
  with poles). This is the closing argument and deserves a picture.

Tables to include: the validation table (§5), the pole census (§7 R7), the residue table
(§8 R8), the two-player slack comparison (§9 R9).

---

## 11. Discussion — the arguments worth making

**1. "Exploitation" is the wrong question at an equilibrium; incidence is the right one.**
The reflex when studying a deviation is to ask who gains. At equilibrium nobody does. The
substantive question is who *pays*, and in a three-player game that question has a
one-dimensional answer space that the equilibrium conditions do not close.

**2. Zero-sum with three players constrains only a sum.** With two players `du_B = −du_A`
pins everything. With three, `du_B + du_C = −du_A` leaves a free coordinate. Every result
here is a consequence of that one extra degree of freedom. This is the sentence to put in
the intro.

**3. The indeterminacy concentrates exactly where the equilibrium set has boundaries.** The
poles are not scattered — they sit on the faces of the polytope of equilibria. Table 3's
`c₃₃` interval *is* P1's deterrence window, and both its endpoints are attainable. The
geometry of the equilibrium region and the singularities of the incidence ratio are the same
object.

**4. Off-path play determines on-path incidence.** `b₃₂`, `c₃₃`, `c₃₄`, `c₄₄` have exactly
zero effect on the equilibrium payoffs and are never reached. They nonetheless fix where P1's
poles are and what value ρ takes. Anything that reports "who pays when a player deviates" is
therefore reporting a fact about behaviour that never occurs. **This is the paper's most
quotable result.**

**5. A refinement ladder, with each rung doing something different.** Nash leaves the split
wholly undetermined. Sequential rationality under trembles pins `c34` and `c44` by belief-free
dominance and `b32` at the unique admissible tremble ratio, which removes ρ's *sign*
ambiguity but leaves every pole. Myerson properness — ordering trembles by cost — forces the
surviving parameter to `c33 = lo + w/3` and makes ρ finite and exactly rational. The two
sources of indeterminacy identified in R6 are dispatched by different rungs: the numerator by
sequential rationality, the denominator by properness.

**5b. And you cannot take the other route.** The obvious alternative — shrink the
indeterminate window instead of selecting within it — is closed off by Proposition 5: the
window's width and the family's utility transfer are the same quantity, `w = 0 ⇔ κβ = 0`.
Worse, at `w = 0` one pole survives as the only admissible point.

**5c. The algorithm that found the family cannot find the selection.** MCCFR disperses `c33`
across the window with no correlation to anything (R14), because the off-path sets carry
reach probability ~10⁻³. It does reproduce the *dominance*-driven predictions. The
indeterminacy is invisible to the solver precisely where it matters.

**6. A practical caution for multiplayer agents.** Two agents both playing "an equilibrium
strategy" from this family can produce a non-equilibrium profile in which one loses κβ
(SGS's Table 4, reproduced here at exploitability 0.0104167). Our results add that even
*within* a single consistent profile, the answer to "who did that cost?" is not determined
by the equilibrium conditions. Benchmarks that report per-seat results in three-player games
are measuring something partly arbitrary.

---

## 12. Limitations and threats to validity (write these; reviewers will find them anyway)

1. **One game, and a tiny one.** 4 cards, 3 players, one betting round. Nothing here shows
   the mechanism generalizes to larger games. The obvious next targets are the N > 3 card
   variants (Billingham et al.) and three-player Leduc.

2. **One family.** SGS state explicitly that it remains open whether other three-player Kuhn
   equilibria exist outside this family. **Every claim here is conditional on being inside
   it.** Do not write "in three-player Kuhn poker" where you mean "in the SGS family".

3. **Grid vs continuum.** Distinguish carefully. The pole *locations* are closed-form root
   solves and hold on the continuum **[P/E]**. The census counts, sign ranges and min-|du_A|
   figures are grid statistics **[G]** — they establish existence and give ranges, but a
   claim like "ρ is positive everywhere for P2" is really "at all 9,072 grid points".

4. **Coordinate directions.** The census uses single-coordinate directions. Proposition 3
   shows the extreme-ray argument extends the *classification* to all feasible directions.
   ρ itself is a ratio and is **not** a convex combination of coordinate ρ's, so per-direction
   ρ values do not automatically extend. Say so.

5. **Numerical floor.** The residue rate check floors near 1e-7–1e-8 from float
   cancellation. Exact rational arithmetic was used for headline values; the rate check was
   not.

6. **The "P1 is uniquely exposed" claim needs care.** P3 also has poles. The correct claim is
   narrower: P1 is the only player whose pole locations are set by *off-path* parameters, and
   the only player whose ρ changes sign. Earlier drafts of this analysis overstated it; do
   not repeat that.

7. **Properness is applied to the normal form.** Theorem 3 orders whole pure strategies by
   expected cost and lets the behavioural tremble rates inherit that ordering. Agent-normal-
   form properness would not order `a11` against `a41` (different information sets), so the
   selection result is scoped to normal-form properness. Whether extensive-form proper or
   quasi-perfect equilibrium gives the same point is open.

8. **The MCCFR study is of approximate equilibria.** Median exploitability 1.5e-3 (3.6% of
   κ). The finding that 99/150 outputs lie in no sub-family is therefore suggestive about
   equilibria outside the family, not conclusive — under-convergence is not excluded. 150
   seeds, one sampling scheme, one iteration count.

9. **The generalization results are local tests at approximate equilibria.** Exploitability
   medians 1.1e-3 (N=4), 3.4e-3 (N=5), 2.6e-3 (n=4); no exact certification for N>4 or n>3,
   and no closed-form family. The N=5 negative is robust (roots miss by ≥ 0.216) and the
   n=4 positive is robust (roots median 0.639), but the N = n+1 hypothesis is single-seed.

10. **The refinement test is sequential rationality, not full THP.** R11 perturbs P1's
   opening and checks each off-path owner's optimality under the induced beliefs. It does
   not verify that the trembles are themselves equilibrium trembles of the perturbed game.
   The perturbed-game exploitability gap scales as Θ(ε) (8.8e-2, 1.05e-2, 1.08e-3,
   1.08e-4, 1.08e-5 at ε = 1e-1 … 1e-5), consistent with being a limit of perturbed
   equilibria but not a proof of it. Also, the tremble sweep uses ratios of the form
   `(1,1,1,r₄)`; the belief at the `c33` set depends only on `(r₁+r₂)` versus `r₄`, so this
   is representative for `c33`, but a full sweep would be safer for the other sets.
   The refined-face ρ range is 250 sampled points, not an exhaustive grid.
   **Largely closed by Theorem 6 (2026-09-22/24):** sequentiality is now decided exactly over
   the complete Nash set, with every coordinate trembling and every ordering of the trembles
   covered, and perfection is certified (inward direction + full-rank indifference Jacobian +
   implicit function theorem) at explicit points, including the whole interior of the `c33`
   window at one parameter point. What remains open is perfection *everywhere* on the
   sequential set — the `c23`-interior pattern has no uniform inward direction, and the
   first-order test cannot decide it — and quasi-perfection.

11. **`c₃₄`/`c₄₄` are unconstrained but not inert.** An earlier draft called `c₄₄` inert; the
   mixed second derivatives disprove it. Keep the distinction sharp: zero first derivative
   and zero exploitability say a parameter is *unconstrained*, not that it has no effect.

---

## 13. Reproducibility

Python 3.13, numpy only (matplotlib for figures). No randomness in any headline result;
random draws are used only to sample validation points, with fixed seeds.

| file | role |
|---|---|
| `kuhn3p.py` | 3-player engine: 312-leaf tree, exact utilities, batch utilities, exact/finite-difference gradients, exact best responses, reach probabilities, rational utilities |
| `family.py` | SGS Tables 2 and 3 transcribed; constraint checker; sub-family constructors |
| `grids.py` | the 9,072-point grid and the dense 1-D sweeps |
| `kuhn2p.py` | independent 2-player engine (30-leaf tree) and the α-family |
| `verify_paper.py` | §5 validation → `log_verify.txt` |
| `analyze.py` | derivatives, zero-sum, ρ census → `log_analyze.txt`, `results.json` |
| `handcheck.py` | the §9 worked example → `log_handcheck.txt` |
| `followup4.py` | pole at all three P1 openings; `c₃₄`/`c₄₄` inertness test |
| `followup5.py` | round-2 census, attainability controls, 48-parameter pole census |
| `followup6.py` | 2-player control analysis |
| `followup8.py` | §8 R11: refinement — off-path owners' optimality under trembles, perturbed-game gap |
| `followup9.py` | §8 R11: tremble-consistency across all off-path sets; the refined face |
| `cfr3p.py` | independent external-sampling MCCFR solver (own tree; agrees with `kuhn3p` to 1.1e-16) |
| `followup10.py` | §8 R14: the 150-seed MCCFR study → `cfr_sweep.json`, `log_cfr.txt` |
| `kuhnNp.py` / `kuhnGen.py` | §8 R15: N-card 3-player and general n-player engines (both exactly validated) |
| `cfrNp.py` / `cfrGen.py` / `poletest.py` | MCCFR for both, and the engine-agnostic local pole test |
| `theorem.py` | §8 R15: verification of the general theorem |
| `sweepNn.py` | §8 R15: the 108-run (n,N) sweep testing N = n+1 |
| `sweepN5.py` / `sweepN4p.py` | §8 R15: the 50-seed N=5 and 24-seed n=4 sweeps |
| `followup11.py` | §8 R12/R13: hard floor, exact global form, properness selection (exact rationals) |
| `refine.py` | §7.3 Theorem 6: the Jacobian of the gradients, the dominance test, the first-order perfection certificate |
| `seqset.py` | §7.3: belief systems in closed form (`A_v/B_v`), the exact sequentiality LP, tremble orderings, exact witnesses |
| `seqrun.py` | §7.3: the per-leaf enumeration of off-path patterns → `seq_<leaf>.json`, `seq_summary.txt` |
| `checkseq.py` | §7.3: independent Fraction-only checker for the sequential witnesses (17/17 verified) |
| `resolve_seq.py`, `perfwit.py` | §7.3: second pass on undecided patterns; search for a perfect witness in each surviving pattern |
| `forcecheck.py` | §7.3: the mechanised part of the forcing chain — coefficient bounds of the leading forms over Table 4's windows, all 12 leaves |
| `seqforms.py` | §7.3: the belief forms rebuilt from the game tree in Fractions (no sympy) — the checker's foundation |
| `seqcert.py`, `checkseqcert.py` | §7.3: Theorem 6's enumeration with stored evidence for every step, and its independent replay (12/12 leaves, 637 kills, 3,554 certificates, 21 witnesses on concrete tremble curves) |
| `resolve_seq2.py`, `witC.py` | §7.3: close the last 28 patterns — one-signed forms on assigned coordinates, the exhaustive 75-ordering kill with strictly positive in-class ratios, and sub-family-C witnesses (small `b23`) |
| `enumc2.py`, `checkenum.py`, `runenumc.py`, `retry_partial.py` | §7.1 / MASTER_DATA §16.9: the betting branches as certificate trees and their Fraction replay; `retry_partial.py` re-runs capped branches at a long clock |
| `k35/runcells.py`, `k35/estcells.py` | MASTER_DATA §16.11: the (3,5) cell sweep, and Knuth leaf **and node** estimates (the node count is what predicts runtime) |
| `start_third_pass.py` | windowless launcher (`pythonw.exe`, Task Scheduler): long runs must not own a console window |
| `followup7.py` | residue identity `R = t/D′`; corrected 2-player slack sweep |
| `plots.py`, `plots2.py` | figures 1–4 |

Run order: `check_engine.py` → `verify_paper.py` → `analyze.py` → `handcheck.py` →
`followup4.py` → `followup5.py` → `followup6.py` → `followup7.py` → `followup8.py` → `followup9.py` → `followup10.py` → `followup11.py` →
`plots.py` → `plots2.py`.

For an artifact submission, state the leaf count (312 / 30) and the grid size (9,072) in the
abstract or Section 1 — they are the two numbers that convince a reader nothing was sampled.

---

## 14. Open problems (good closing section)

1. **Is the SGS family the complete equilibrium set?** Open in the original paper — and now
   answered, in two halves (MASTER_DATA Part 16, 2026-09-16). *As profiles*: no, and an exact
   witness with `b12 = 9/100` off path shows it cannot be. *On path*: for every Nash equilibrium
   in which P1 never bets, the reached coordinates satisfy Table 3's identities **and** its
   parameter ranges — proved by exact rational certificates on every one of the 5,754 support
   leaves of the branch (`symleaf.py`). The P1-betting branches are being decided the same way
   The P1-betting branches are decided the same way: all 77 Nash-mode branches, 1,337,533
   supports, every one certified empty (2026-09-19); re-derived 2026-09-20/21 under outward-rounded
   interval arithmetic with stored certificates and an independent checker (45,276 supports on the
   betting side, all empty; MASTER_DATA §16.7–16.8). "The family is the complete set of on-path
   equilibrium plays" is a theorem with no float caveat (§7.1, Theorem 4).
   Write it as: *every Nash equilibrium plays a member of the SGS family wherever play is
   reached; off the path of play the equilibrium set is strictly larger than the family.*
2. **Is the selection robust to the properness variant?** Theorem 3 uses normal-form
   properness. Does extensive-form proper, or quasi-perfect, select the same `c33 = lo + w/3`?
   **Answered for extensive-form properness (Theorem 6 / Corollary 6.1, 2026-09-22): no.**
   Every information set here is binary, so extensive-form properness coincides with
   extensive-form perfection (Lemma R1), and the perfect set still contains a whole interval
   of `c33` — at `b11 = b21 = 1/8`, `c11 = 1/4` the interval `(1/2, 23/32)`, of width `7/32`,
   with normal-form properness picking `55/96` inside it. Refinement pins every *other*
   off-path coordinate it can (`b32 = c13 = c34 = 0`, `c43 = b42 = b44 = a44 = c44 = 1`,
   `a14 = a24 = c14 = c24 = b12 = 0`, `b24 = b14 = 0`) but not `c33`, which it merely confines
   to `[1/2, ·]` — so the denominator source of ρ's indeterminacy survives every refinement
   short of the normal-form one. What remains open is
   quasi-perfection, and whether the normal-form selection is itself canonical.

2b. **Are there equilibria outside the SGS family?** Answered (Theorem 5, 2026-09-21): the
   complete Nash set is the union of twelve explicit semi-algebraic sets — the family on the path
   of play, with off-path windows (Table 4) that Table 2 does not allow (`b12` up to ≈ 0.42,
   `c33` up to 15/16, …). R14's 99/150 off-family MCCFR outputs should be re-read against
   Table 4: off path they may well be equilibria.

3. **Confirm the N = n+1 hypothesis.** R15 finds P1 silent — and poles present — exactly
   when the deck is minimal, but on single seeds. Multi-seed runs at (5,6) and (4,6) would
   settle it cheaply. The instrument now runs on (3, 5) directly (`k35/`, MASTER_DATA §16.11),
   and the sweep is complete: of P1's 239 betting cells, **190 are decided inside a 15-minute
   cap (mean 223 s) and none of them carries an equilibrium in which P1 bets**; 49 time out.
   A Knuth estimate says why — those cells are 2.5e6 to 1.2e7 nodes against the 4-card silent
   branch's 1.6e4, i.e. 150× to 760×, so they need days each rather than minutes, and in the
   one measured the estimator found no surviving leaf in 200 walks. The exact-propagation method
   that closed the 4-card betting side ports faithfully (60/60 float kills reproduced) but does
   not close these cells. One measured cell extrapolates to ~3.6 million nodes, about two months
   on one desktop (MASTER_DATA §16.11). An exhaustive (3, 5) certification needs a stronger
   per-node bound, not a longer clock.

   **Answered for (3, 5) on the positive side (2026-10-07, MASTER_DATA §16.11.1):** (3, 5)-Kuhn
   HAS an exact Nash equilibrium in which P1 bets:
   - P1 opens cards 1 and 2 with probability ≈ 0.1615 each, card 3 ≈ 0.0404 and card 5 ≈ 0.8478;
   - payoffs ≈ (−0.0350, −0.0013, +0.0363).

   The equilibrium was found by polishing MCCFR (7 of 20 seeds reach it), and proved by an
   exact-arithmetic Krawczyk (interval-Newton) existence test:
   - on a 14-equation reduction justified by polynomial identities;
   - with every one-shot D-condition checked over a box of radius 10⁻³⁰;
   - re-checked by an independent sympy-free implementation;
   - with negative controls rejected.

   Some coordinates are irrational (`b₁₁ = (11 + √13)/72`, `c₃₂ = 4 − √13`), others algebraic of
   degree > 8, so the theorem is an existence statement with a certified enclosure, not a closed
   form. So the N = n+1 separation is a theorem at (3, 4) (P1 silent in every equilibrium) and at
   (3, 5) (P1 bets in some equilibrium, and, by §16.11.5, in every equilibrium).

   **More (MASTER_DATA §16.11.2–3).** The (3, 5) betting equilibria are not a single point, and
   their payoffs differ.  All three components below are certified exactly:

   | component | what P1 does | P2's payoff |
   |---|---|---|
   | I: a whole segment | same play along it; only P3 shifts weight between opening with cards 1 and 2 | −0.0013 |
   | III: a branch leaving I, a one-parameter family | close to I | about −0.0011, varying along the branch |
   | II: isolated | bluffs only with card 1 | **+0.0016** |

   With 4 cards P2 gets −1/48 in every equilibrium, so **equilibrium payoffs are unique at (3, 4)
   and not at (3, 5)**.  **P1-silent equilibria: NONE, proved (MASTER_DATA §16.11.5).**  For all 7
   polished check-subgame equilibria, no choice of responses to a bet deters P1, by a margin of
   +0.026 (calling deters bluffs but feeds value bets).  The proof below covers every equilibrium.  **Exact reduction (MASTER_DATA
   §16.11.4):** a P1-silent equilibrium exists only if the restricted game (P1 forced to check) has
   an equilibrium in which **P1's value with the top card is at least 19/8**, i.e. opponents put in
   at least 3/8 chip on average against P1's nuts; the known restricted family has 0.194.
   Equivalently, P1's deviation "open 5 always, open 1 at rate 3/8" beats every response unless
   V₅ ≥ 19/8 (vertex certificate over all 2¹⁵ responses, exact).  The exhaustive enumeration of
   either the silent cell (2.6e7 nodes) or the restricted game (1.2e8) is out of reach.  **Closed
   by a certificate (§16.11.5):** multipliers on 24 deviation inequalities give
   L = u_1(·|5) + Σ μ_τ (u_a − u_a(τ)) ≤ 28071283/12000000 ≈ 2.3393 < 19/8 over the whole cube.  L is
   multilinear, so a check over the 2⁴⁰ pure profiles suffices.  Two independent exact checkers
   (`k35/ceverify.py`, `k35/ceverify2.py`) give the same maximum.  **Toward "I–III are all"
   (MASTER_DATA §16.11.6):** the same certificates on the FULL game (two independent exact
   checkers, `k35/fullcheck35.py` / `fullcheck35b.py`) prove that in every equilibrium:
   - P1 opens 5 with positive probability;
   - P1 never opens any of 1–4 with certainty;
   - if P1 never bluffs with 1 or 2, it opens 3 sometimes and mixes 5.

   Completeness stays open: the coarse relaxation is too weak in 24 of the 30 opening cells holding
   no known component.  36 MCCFR seeds find only I, II, III.  Still open: whether I–III are all the
   betting equilibria. Related: is there a vector analogue of the residue identity
   `R = t/D′` for n ≥ 4, where the residue becomes a vector on the (n−2)-simplex?
4. **Is there a general theorem?** Conjecture: in any n-player constant-sum extensive game
   with n ≥ 3, an equilibrium component with an attainable deterrence boundary produces an
   unbounded incidence ratio at that boundary. Theorem 1's three clauses are stated in a way
   that should generalize; the residue theorem needs only multilinearity of the utilities.
5. **Does the indeterminacy matter for learning?** CFR and its variants converge to *some*
   point in the family. Which one, and does the choice systematically favour a seat?

---

## 15. Claim calibration — sentences you may and may not write

| ✗ do not write | ✓ write instead |
|---|---|
| "P1 never bets in Kuhn-type 3-player games" | "P1 is silent in every equilibrium at (3, 4) and bets in every equilibrium at (3, 5)" (Theorem 4; MASTER_DATA §16.11.5) |
| "we enumerated every (3, 5) equilibrium" | "no (3, 5) equilibrium has P1 silent, by a deterrence cut plus a correlated-equilibrium certificate checked exactly over all 2⁴⁰ pure profiles of the restricted game; the betting equilibria are not enumerated" |
| "ρ is undefined on a measure-zero set" | "ρ is undefined on 19 of 48 coordinate directions everywhere, and on part of the family for 21 more" |
| "P1 is the only player exposed to this" | "P1 is the only player whose poles are located by off-path parameters, and the only player whose ρ changes sign; P3 also has poles" |
| "we verified the zero-sum identity" | "the zero-sum identity is structural and cannot fail; we confirm it numerically as an implementation check" |
| "central differences approximate the derivative" | "u is affine along any single coordinate, so the central difference is exact to round-off" |
| "in three-player Kuhn poker, ..." | "in the SGS equilibrium family for three-player Kuhn poker, ..." |
| "ρ is not pinned down" | "ρ is not pinned down by Nash; sequential rationality fixes its sign and properness fixes its value" |
| "properness pins ρ" (unqualified) | "normal-form properness pins ρ; extensive-form properness — equal to perfection here, since every information set is binary — provably leaves c₃₃ an interval (Corollary 6.1)" |
| "CFR converges to the family" | "MCCFR reaches median exploitability 3.6% of κ, but 99/150 outputs lie in none of the three sub-families" |
| "a refinement fixes the indeterminacy" | "sequential rationality pins every off-path coordinate except c₂₃ and c₃₃ and removes ρ's sign ambiguity, but leaves c₃₃ ∈ [½, 15/16] and both poles; only normal-form properness picks a point" |
| "we checked the results numerically" | "every verdict is a stored exact certificate replayed by an independent Fraction checker (66,699 leaves; 4.4M enumeration nodes on 71 of 77 betting branches)" |
| "the refinement analysis covers the family" | "the refinement is decided on the complete Nash set of Theorem 5: all off-path support patterns, every exclusion and witness replayed by an independent checker (637 kills, 3,554 certificates) and 21 witnessed" |
| "c₃₄ and c₄₄ are irrelevant" | "c₃₄ and c₄₄ are unconstrained by every player's incentive, but not inert: they set the numerator of P1's ρ" |
| "ρ diverges near the boundary" | "ρ has a simple pole at the boundary with residue R = t/D′" |
| "the family is a continuum of equilibria with the same value" | "the family is a continuum of equilibria whose values differ: u₁ and u₃ each vary by κ/4 across it" |
| "the SGS family is the set of all equilibria" | "every Nash equilibrium plays a member of the SGS family on the path of play; as profiles the equilibrium set is strictly larger (exact witness with b₁₂ = 9/100 off path)" |
| "we proved the silent branch empty outside the family by interval bisection" | "interval bisection cannot decide a family-adjacent support (its closure contains equilibria); the branch is decided by exact certificates — ideal membership, Gröbner normal forms, and a rationally certified LP relaxation" |
| "the first-order conditions characterise Nash" | "the own-reach-stripped first-order system does, up to re-choosing coordinates at own-unreached information sets; the plain reach-weighted system admits non-equilibria" |
