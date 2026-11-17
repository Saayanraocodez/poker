# The Complete Equilibrium Set of Three-Player Kuhn Poker: Certificates, Refinements, Correlation and the Ante

**Saayan Rao** — split draft, built by `papers/build_split.py` from `PAPER_DRAFT.md` Part I.

> One of three papers cut from the single working draft. Theorem, lemma and table numbers are shared
> across the three. The research record (`MASTER_DATA.md`), the code map and the reproduction commands
> are in `PAPER_DRAFT.md` Parts II–III. Claim tags: **[P]** proved, **[E]** exact computation,
> **[G]** grid or sampling evidence, **[F]** float exploration, **[F\*]** float carried to machine
> precision, **[?]** not established. The five-card game and the Hold'em line are not in this paper.

## Abstract

Three-player Kuhn poker has a published family of equilibria (Szafron, Gibson and Sturtevant 2013) whose
completeness was left open. We settle the equilibrium set exactly. In every Nash equilibrium the first
player checks with every card and play follows the family wherever it is reached (Theorem 4); off the
path the Nash set is strictly larger, and we give all of it as the union of twelve semi-algebraic sets
with certified coordinate ranges (Theorem 5). The proof of Theorem 4 is one replayable object: 81
exact-propagation certificate trees, one per cell of the first player's opening labels, about 38,000
nodes, checked by an independent rational checker with no solver in it. Two older certified routes
(66,699 support-leaf certificates; 4.4 million label-box nodes) agree with it.

On this set we decide the refinements exactly (Theorem 6). Sequential rationality pins every off-path
coordinate except two; perfection, agent-normal-form properness and quasi-perfection leave the third
player's call frequency `c33` an interval. As SELECTIONS the picture is sharper: every tremble shape we
solved (38 of 38) picks the same on-path equilibrium, the corner with the largest payoff transfer, and
puts `c33` at an end of its interval.

Two results explain why the first player's silence is delicate. It needs independent randomisation:
there is an exact normal-form correlated equilibrium in which the first player bets (Theorem 9), so no
correlated-equilibrium certificate could replace the enumeration. And it is a band-of-antes
phenomenon: with the ante as a parameter a closed-form silent family exists up to
`A2 = 1/2 + √23/6 ≈ 1.2993` and not beyond, and the standard game sits exactly where the second player
starts betting.

## Contributions

1. **The equilibrium set, exactly** (Theorems 4 and 5), with P2's payoff `−1/48` in every equilibrium.
2. **A proof a reader can replay**: 81 certificate trees, an independent checker, a coverage driver;
   six of the 80 betting cells also by a four-line hand argument (Lemma 6).
3. **Refinements decided exactly** (Theorem 6, Corollaries 6.1–6.2).
4. **What a fixed tremble shape selects**: one on-path point and an end of the `c33` window.
5. **Silence needs independence** (Theorem 9): an exact normal-form correlated equilibrium with P1
   betting.
6. **The ante as a parameter**: a closed-form silent family and its exact end.
7. **An independent exact reproduction of SGS**, with two errata.

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
  present results are exact, and §8.2 uses its parameter (the pot) at N = 4. **[?] Only the abstract
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

## 3. Reproduction of SGS, and two errata

### 3.1 Validation **[E]**

| check | result |
|---|---|
| Table 3 utilities, 600 random family points | max error 5.0e-16 |
| exact rational check at `b11 = 1/8, b21 = 1/4` | `u = (−1/32, −1/48, 5/96)` exactly |
| SGS §1's worked leaf (`a13` in deal 124) | factors `(1−a11)·b21·(1−c42)·a13`, payoff `(−2, 3, −1)` |
| Appendix eq. (3), (4), (5): u3 / u2 / u1 with one player free, 400 points each | max error 6.0e-16 / 2.2e-16 / 8.9e-16 |
| Table 4's mismatched profile; P2's gain κβ | reproduced exactly (0.0104167 = κ/4) |
| exact best-response gap, 450 family points | < 5e-16 for all three players |

Matching eqs. (3)–(5) pins down both the tree and the Table 3 transcription at once.

### 3.2 Erratum 1 (material): `b33` in SGS §4's prose **[E]**

For the `c11 = 1/2` sub-family, SGS §4 states `b33 = (1 + b11 + 2b21)/2`. Table 3 gives
`(1 + 2b11 + b21)/2 − b23(1 − b21)` there. The prose transposes b11 and b21 and drops the b23 term.
Where the two differ, the prose value is not an equilibrium:

| b11 | b21 | b23 | b33 (Table 3) | b33 (prose) | exploitability (Table 3) | exploitability (prose) |
|---|---|---|---|---|---|---|
| 0.20 | 0.05 | 0 | 0.72500 | 0.65000 | 2.2e-16 | **6.25e-03** |
| 0.15 | 0.10 | 0.02 | 0.68200 | 0.67500 | 7.3e-17 | **5.83e-04** |
| 0.20 | 0.05 | 0.079 | 0.65000 | 0.65000 | 2.2e-16 | 2.2e-16 |
| 0.10 | 0.10 | 0 | 0.65000 | 0.65000 | 7.6e-17 | 7.6e-17 |

`du_i/db33 = (0, 0, 0)` for all three players, yet a wrong `b33` destroys the equilibrium. It is a
pure deterrence parameter, the paper's main mechanism in miniature.

### 3.3 Erratum 2 (cosmetic): a sign in Lemma 4 **[E]**

SGS display `∂u2/∂b23 = 2κ(1−b21)(1−2c11)`. Their own eq. (4) gives `2κ(1−b21)(2c11−1)`. The next
line of their proof uses the corrected sign, so the proof is unaffected.



---

## 4. Method

### 4.1 Exact engine and multilinearity

- **Full enumeration.** All 24 deals × 13 histories are materialised once as a leaf table:
  `u_i(p) = κ Σ_leaves (Π factors) · payoff_i`. No sampling, no iteration.
- **Multilinearity.** Each `u_i` is multilinear in the 48 coordinates, hence affine along any single
  coordinate:
  - `∂u/∂x_i = u(x_i = 1) − u(x_i = 0)`, exactly;
  - any `∂u/∂x` is affine in every other single coordinate, so its zeros are solved in closed form
    rather than searched.
- **Exact best responses.** `u_i` decomposes over the card player i holds. A best response is 4
  independent 4-decision problems, 4 × 2^4 = 64 evaluations, so exploitability is exact.
- **Rational arithmetic** (`fractions.Fraction`) for every headline claim.

### 4.2 The Nash condition that is actually right: the own-reach-stripped gradient

For information set `i` of player `k`, the reach of any node factorises:
`R(n) = R_k(i) · R_{−k}(n)`, where `R_k(i)` is the product of k's own coordinates on the path (the
same for every node of i).

**Definition 4.** The own-reach-stripped gradient is
`D_i(p) = (1/24) Σ_{n ∈ i} R_{−k}(n) · (V_k(agg child of n) − V_k(pass child of n))`,
so that `∂u_k/∂x_i = R_k(i) · D_i` exactly.

**Definition 5 (D-condition).** `x_i D_i ≥ 0` and `(1 − x_i) D_i ≤ 0`. That is: interior ⇒ `D = 0`,
`x = 0` ⇒ `D ≤ 0`, `x = 1` ⇒ `D ≥ 0`.

**Lemma 1.**
- (a) Every Nash equilibrium satisfies the D-condition at every own-reachable set, and can be
  re-chosen at own-unreached sets (changing no payoff and no reached play) to satisfy it everywhere.
- (b) A profile satisfying the D-condition everywhere is Nash.

*Proof:* the one-shot deviation principle, by backward induction over each player's own tree
(PAPER_KIT §6.1). **[P]**

**Why not `∂u_k/∂x_i = 0`.** The plain gradient vanishes at every own-unreached set whatever the
continuation. So the reach-weighted first-order system admits non-equilibria: a dominated off-path
continuation can "support" an earlier choice. Five "open" leaves of the first pass were exactly such
points. With D they die at the root.

### 4.3 Support enumeration as a label tree

Each coordinate gets one of these labels:
- `0` or `1`;
- `MIX` (open interval (0,1));
- `DC` (its set provably unreached on the cell, or the coordinate occurs in no other constraint; it
  carries the D-condition pair instead of a label, which loses nothing by Lemma 2);
- `U` (not yet assigned).

A node's system substitutes the 0/1 labels into every D and imposes the sign conditions. Every leaf
implies its ancestors' systems (Lemma 3), and the labels partition the cube (Lemma 4). So a node
proved infeasible contains no equilibrium, and the surviving leaves cover every equilibrium.

### 4.4 How a node or leaf is proved empty: the certificate types

| certificate | what it proves | checker step |
|---|---|---|
| rational interval contraction (HC4) | a box shrinks; a coordinate is forced; the box empties | replay each step in Fractions |
| LP relaxation with McCormick rows, rational duals | the relaxation is infeasible (weak duality) | rebuild each row from named origins, check `y·A ≥ 0`, `y·b < 0` |
| Nullstellensatz / Rabinowitsch cofactors | `1 ∈ ⟨E, 1 − t v⟩` (an equality system forbids `v ≠ 0`) | multiply out the cofactors in Fractions |
| Gröbner normal forms of inequalities | e.g. `b41 ≥ 0` reduces to the constant −1/96 | cofactor proof of the reduction |
| interval tree recursion with the chord contractor | the tree-structured bound excludes a box | exact tree bounds |
| exact propagation record (enumc7) | a forced value, a chord narrowing justified by convexity, or a contradiction, on the exact propagated box | `checkenum2` replays every node from its parent's record |
| FAMILY claim | every point of the leaf satisfies Table 3 on non-DC coordinates | identities and ranges as separate certificates |

Three facts made it work. Each was learned the hard way (Appendix B):
- interval reasoning alone can never kill a family-adjacent leaf, because its closure contains
  equilibria;
- the exact test pays off at depth, not at the root, so it runs every four levels of the label DFS;
- in a betting branch, assigning the responses to P1's bet first (`KUHN_ORDER=bet`) turns hours into
  minutes.

### 4.5 Outward rounding and the third pass

`ivl.py` rounds every floating-point operation outward with `nextafter`, so float prunes are rigorous
under IEEE-754. The third pass removed even that dependence: every betting branch was re-derived as a
certificate tree in which every float kill is replaced by an exact certificate, or the node is split.
- 71 branches: `enumc2` + `checkenum`;
- the 6 that resisted: `enumc7` + `checkenum2`, exact propagation;
- `enumc7` on **all** 77 gives 33,104 nodes and 462 leaves, all `EMPTY_BOX`; on the silent cell,
  4,723 nodes and the same 12 FAMILY leaves; on the three root-dead cells, one node each.

So the exact-propagation trees alone cover all 81 cells. They are the proof of Theorem 4 (§5), and
the other routes are independent cross-checks.



---

## 5. Theorem 4: every equilibrium plays the SGS family on path

**Theorem 4 (on-path completeness).** *Every Nash equilibrium of three-player four-card Kuhn poker is
realisation-equivalent to a member of the SGS family. P1 never bets, and on every reached
information set play satisfies Table 3's identities and parameter ranges. As profiles, the
equilibrium set is strictly larger than the family (exact witness with `b12 = 9/100` off path).*
**[P,E]**

*Proof.*
1. By Lemma 1, it suffices to enumerate profiles satisfying the D-condition everywhere.
2. P1's four opening coordinates give 81 label cells, which partition the profile space (Lemma 4).
3. **Every cell is closed by one exact certificate tree.** `enumc7.py` derives, for a cell, a tree in
   which every node carries its exact propagated box and a certificate for every narrowing, kill and
   leaf. `checkenum2.py`, written independently of the prover, replays each tree starting from the
   cell's four opening labels (it rejects a tree whose root is anything else), and `check81.py` checks
   that the 81 cells are all covered and that no support survives outside the silent cell.
   - **The 80 betting cells contain no support.** 77 trees with 33,104 nodes and 462 support leaves,
     every leaf certified empty; the other three cells (`a11 = a21 = 0`, `a41 = 1`) die at the root.
   - **The silent cell:** 4,723 nodes and 79 leaves: 67 certified empty and 12 FAMILY leaves. These are
     sub-families A (4 leaves), B (3) and C (5), with every corner.
4. Lemma 5: a FAMILY leaf's points agree with a family member on every reached coordinate. ∎

**Lemma 6 (six cells by hand).** *No equilibrium has `a11 = a21 = 0 < a41`.* If P1 bets only cards 3
and 4, and bets the 4 with positive probability, then every set "facing P1's bet with card 1, 2 or 3"
is reached, and calling there loses for sure. So every such call has probability 0, and a bet with
card 1 is called at most by a 4: it is worth at least `(1/3)(+2) + (2/3)(−2) = −2/3`. Checking card 1
is worth at most −1. So `a11 = 0` is not a best reply. ∎ This covers the three cells the root
propagation kills and three more (`a41` interior), with no computation at all.

**Independent cross-checks (not part of the proof above).** The same verdicts were reached earlier by
two other certified routes, each with its own checker:
- the R ledger: layered enumeration under outward-rounded interval arithmetic, with a stored
  certificate for every support leaf, 66,699 of 66,699 replayed by `checkcert.py` (668 silent, 45,276
  Nash-mode betting, 20,755 seq-mode betting);
- label-box certificate trees for 71 betting cells: 4,394,323 nodes replayed by `checkenum.py`.

**Counts are not invariants.** Node and leaf counts depend on the number of workers and on the LP
solver build; only the verdicts are fixed. A re-derivation on another machine (3 workers) gives the
silent cell 610 supports instead of 668, with the same 12 FAMILY leaves label for label, and one
betting tree closes in 445 nodes instead of 484 (`independent_check/`).

**Corollary 4.1.** In every Nash equilibrium P1 checks with every card.

**Corollary 4.2.** The equilibrium payoff set is the segment
`{(−κ(1/2 + β), −κ/2, κ(1 + β)) : β ∈ [0, 1/4]}`. In particular **P2's payoff is −1/48 in every
equilibrium**, and `u1 + u3 = −1/48`.

**The off-path witness** (why "as profiles" fails). Take the sub-family-C corner:
- on path: `b11 = 1/4`, `b21 = b23 = 0`, `c11 = 1/2`;
- off path: `b32 = 23/100`, `c33 = 1/4`, `c34 = 9/10`, `b12 = 9/100`, `b22 = 1/40`, `c23 = 1/25`.

Its exploitability is exactly (0, 0, 0). Setting `b12 := 0`, P1 gains exactly 1/300 by betting card
2. With Table 3's pins on top, P1 gains 1/150. So Table 2 is necessary only at reached information
sets, and a dominated off-path action can be *essential*: 169 of 23,820 hunt equilibria stop being
Nash when projected onto Table 2.

**Ledger.** The proof (`check81.py`; node counts are those of the 2026-10-05 run; a re-derivation on
another machine is in `proof34/`, 77 of the 81 cells on 2026-11-17, the silent cell at 4,720 nodes and 80
leaves with the same 12 FAMILY leaves):

| part | cells | nodes | support leaves | verdict |
|---|---|---|---|---|
| betting cells, exact-propagation trees | 77 | 33,104 | 462 | all empty |
| betting cells dead at the root | 3 | 3 | 0 | closed by exact propagation (and by Lemma 6) |
| silent cell | 1 | 4,723 | 79 | 67 empty + 12 FAMILY |

The cross-checks (the run of 2026-09-20/21 under outward-rounded interval arithmetic, suffix R, and
the third pass):

| part | supports | verdict |
|---|---|---|
| Nash-mode betting, 77 branches | 45,276 | all empty (47 branches have no support) |
| seq-mode betting, 32 branches | 20,755 | all empty |
| silent cell | 668 | 656 empty + 12 FAMILY |
| leaf certificates replayed | 66,699 / 66,699 | 0 failed |
| node certificates replayed (71 betting branches, label-box trees) | 4,394,323 | 0 failed |



---

## 6. Theorem 5: the complete Nash set, off path included

**Theorem 5.** *The set of Nash equilibria is the union of twelve sets `Ŝ_ℓ`, one per FAMILY leaf ℓ.
Here `S_ℓ` is {the leaf's labels, and the D-condition at every coordinate}, and `Ŝ_ℓ` frees the
own-unreached coordinates. These are `b43` and `b44` in the two leaves with `b41 = 1`, and nothing
elsewhere.*

*Each `S_ℓ` factors as (on-path parameters) × (deterrence region) × (free cube).*
- *The reached coordinates carry Table 3.*
- *The off-path coordinates that enter some incentive are constrained only by the deterrence
  inequalities `D_{a_j1} ≤ 0`, `D_{b_j1} ≤ 0` where `b_j1 = 0`, and the sign-determined pins these
  induce.*
- *Every remaining coordinate has `D ≡ 0` and is free in [0, 1].* **[E,P]**

The twelve systems are written out in `nefull_systems.txt`. Their coordinate projections, the
*windows*, are in `nefull_ranges.txt`: 522 bound certificates (`{S_ℓ, x_v > T}` empty), checked by
`checknefull.py`, with exact witnesses where a bound is attained.

**Table 4 — the windows.** Marks: bare = attained (exact witness); ⁻ = certified strict bound, not
attained; ᶜ = certified bound with attainment undecided; ‡ = free where `b41 = 1` (note below the table). The ᶜ decimals were sharpened on 2026-11-17 to within 1e-5 of the
best equilibrium value found (`sharpen_ranges.py`).

| coordinate | role | all equilibria | A | B | C |
|---|---|---|---|---|---|
| a13 | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| a14 | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| a23 | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| a24 | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| a33 | on path | [0, 1/2] | [0, 1/2] | [0, 1/2] | [0, 1/2] |
| a34 | off path | [0, 1] | [0, 1] | [0, 1ᶜ] | [0, 1] |
| a43 | off path | [1, 1] | [1, 1] | [1, 1] | [1, 1] |
| a44 | off path | [0, 1] | [0, 1] | [0ᶜ, 1] | [0, 1] |
| b11 | on path | [0, 1/4] | [0, 1/4] | [0, 1/4ᶜ] | [0, 1/4] |
| b12 | off path | [0, 0.41668ᶜ] | [0, 0.41668ᶜ] | [0, 5/12] | [0, 0.27779ᶜ] |
| b21 | on path | [0, 1/4] | [0, 1/4] | [0, 1/4] | [0, 1/6] |
| b22 | off path | [0, 0.58334ᶜ] | [0, 0.58334ᶜ] | [0, 7/12] | [0, 0.38890ᶜ] |
| b23 | on path | [0, 1/8] | [0, 0] | [0, 0] | [0, 1/8] |
| b32 | off path | [0, 15/16] | [0, 15/16] | [0, 15/16ᶜ] | [0, 19/24] |
| b33 | on path | [1/2, 7/8] | [1/2, 7/8] | [1/2ᶜ, 7/8] | [1/2, 3/4] |
| b41 | on path | [0, 1] | [0, 1] | [0, 1] | [0, 2/3] |
| b42 | off path | [31/40ᶜ, 1] | [0.77579ᶜ, 1] | [31/40ᶜ, 1] | [0.77579ᶜ, 1] |
| b43 | off path | [0, 1]‡ | [0, 1]‡ | [0, 1]‡ | [1, 1] |
| b44 | off path | [0, 1]‡ | [0, 1]‡ | [0, 1]‡ | [4/5, 1] |
| c11 | on path | [0, 1/2] | [0, 0] | [0⁻, 1/2⁻] | [1/2, 1/2] |
| c12 | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| c13 | off path | [0, 0.52623ᶜ] | [0, 0.52623ᶜ] | [0, 0.52623ᶜ] | [0, 0.34509ᶜ] |
| c14 | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| c21 | on path | [0, 1/2] | [1/2, 1/2] | [0⁻, 1/2⁻] | [0, 0] |
| c22 | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| c23 | off path | [0, 7/12] | [0, 7/12ᶜ] | [0, 7/12] | [0, 0.38890ᶜ] |
| c24 | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| c32 | off path | [0, 1/2] | [0, 1/2] | [0, 1/2] | [0, 1/2] |
| c33 | off path | [0, 15/16] | [0, 15/16ᶜ] | [0, 15/16] | [0, 19/24] |
| c34 | off path | [0, 1] | [0, 1] | [0, 1ᶜ] | [0, 1] |
| c42 | off path | [1, 1] | [1, 1] | [1, 1] | [1, 1] |
| c43 | off path | [0.77503ᶜ, 1] | [0.77579ᶜ, 1] | [0.77503ᶜ, 1] | [0.77579ᶜ, 1] |
| c44 | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |

‡ `b43` and `b44` are own-unreached where `b41 = 1` (`b11 = b21 = 1/4`), and Theorem 5 frees them there: the
family point `b11 = b21 = 1/4` with `b43 = b44 = 0` is exactly Nash. Where `b41 < 1`, `b43 = 1` and
`b44 ≥ 17/32ᶜ` (A: `≥ 0.7797⁻`, B: `≥ 17/32ᶜ`, C: `≥ 4/5`). *(Corrected 2026-11-16, erratum 12: the earlier rows
left out the leaves in which the coordinate is private or own-unreached.)*

**How to read it:**
- **Pinned although off path.** `a13 = c12 = c22 = 0` and `a43 = c42 = 1` in every equilibrium: the
  other players' deterrence pins them.
- **Free well beyond Table 2.** The responses to P1's bet that Table 2 sets to 0 range up to
  `b12 = 5/12`, `b22 = 7/12`, `c13 ≈ 0.526` and `c23 = 7/12` (the first two up to 1e-5 in sub-family A). The
  top-card calls `b42` and `c43` only need ≥ ≈ 0.775.
- **Wide windows.** `b32` and `c33` range over [0, 15/16]. `b44 ≥ 17/32` wherever `b41 < 1`; at `b41 = 1`
  (`b11 = b21 = 1/4`) P2 never checks the top card, so `b43` and `b44` are free.
- **Sub-family C is the most restricted:** `b41 ≤ 2/3`, and `b32, c33 ≤ 19/24`.
- **The corner leaves** (`b11 = b21 = 0`) pin the responses to P1's bet exactly to Table 2.



---

## 7. Theorem 6: the refinements, decided exactly

### 7.1 Beliefs in closed form

Take a coordinate `v`. `D_v / R_v` is the value difference at its set under the profile's beliefs,
where `R_v` is the set's reach with the owner's own choices stripped. Along a tremble
`x_w = ε r_w` (where the profile plays 0) or `1 − ε r_w` (where it plays 1), both vanish at an
unreached set. Their limit is `A_v(x, r) / B_v(x, r)`, the ratio of leading coefficients. The ratios
`r` are shared by every set: this is Kreps–Wilson consistency in closed form. Sequential rationality
is then a sign condition on `A_v`, linear in r. For a fixed profile it is one exact LP; infeasibility
comes with a Farkas certificate.

**Lemma R1 (binary sets).** With two actions per set, ε-proper ⇔ ε′-perfect with ε′ = ε/(1−ε). So
agent-normal-form proper = extensive-form perfect = agent-normal-form perfect. (Earlier drafts called the
first of these "extensive-form proper"; the lemma is about properness of the agent normal form, where each
information set is its own player.) Only *normal-form*
properness, which orders whole pure strategies across information sets, can select more. **[P]**

### 7.2 Theorem 6

**Theorem 6 (the sequential set).** Over the complete Nash set:
1. **Dominance, belief-free.** Eighteen coordinates satisfy `D_v = c · R_v` identically:
   - `c = −1` for calling with the worst cards (`x12, x13, x14, x24` for each player);
   - `c = +4` for `x43`;
   - `c = +5` for `x44`.

   Each is pinned in every sequential equilibrium. Also `b42 = 1`, since `D_b42 / R_b42 ≥ 4`.
   Thirteen of these have a nontrivial Nash window, and ten of those windows are all of [0, 1].
2. **Closure.** Substituting and recomputing settles 7–12 more coordinates per leaf, including
   `b44 = 1` and the "private" `b24 = b14 = 0`.
3. **The knife-edges.** After the closure, the unreached coordinates' leading coefficients are *the
   same six linear forms at all twelve leaves*. In every sequential equilibrium:
   - **`b32 = 0`**: interior `b32` needs `2 r_a41 = 3(r_a11 + r_a21)`, which is incompatible with
     `c33`'s knife-edge;
   - **`c43 = 1`**, **`c13 = 0`**, **`c34 = 0`** and **`b22 = 0`**;
   - P1's card-2 deterrence then reads **`c33 ≥ 1/2`**.

   Only `c23` keeps some freedom. Its interior forces trembles of different orders, which consistency
   allows and exact witnesses realise.
4. **What `c33` keeps:** `c33 ∈ [1/2, 15/16]`, the upper half of its Nash window. It collapses to the
   point 1/2 at the corner sub-families.
5. **The surviving interval.** At `b11 = b21 = 1/8`, `c11 = 1/4`:
   - the Nash window `c33 ∈ [1/2, 23/32]` is entirely sequential;
   - its interior is **perfect** (inward direction with `s* = 3715/28782`, indifference Jacobian of
     rank 8, implicit function theorem);
   - the endpoints are the two poles of ρ.

   **[P,E]**

**The enumeration behind (3).** All 398 off-path support patterns are decided: 377 killed and 21
witnessed. The independent replay (`seqcert.py` / `checkseqcert.py`) checks 637 kill records, 3,554
box certificates and 21 witnesses on concrete tremble curves `x_w = ε^e ρ`, at 12 of 12 leaves, with
0 failures. Three patterns survive:
- at the nine generic leaves: `b22 = 0, c23 = 0, c33` interior, and `b22 = 0, c23` interior, `c33`
  interior;
- at the three corner leaves: the mirrored structure, where P2's bet is the unreached one. There
  `a33 = c33 = 1/2` is pinned.

**Three traps the decision had to get past** (detail in Appendix B.6):
- **Per-set normalisation.** A leading coefficient is homogeneous within one set, so under a global
  simplex a whole set's ratios can vanish and the case becomes undecidable. 28 patterns that were
  undecided globally die at once per set.
- **Orderings.** Consistency allows different tremble orders; enumerate the ordered partitions (75
  for P1's four openings).
- **Multi-homogeneity.** Per-set normalisation is without loss only for multi-homogeneous forms. The
  checker enforces this.

### 7.3 Corollary 6.1: agent-normal-form properness does not select

**Corollary 6.1.** Agent-normal-form properness leaves `c33` an interval of width 7/32. Normal-form
properness (Theorem 3) selects `c33 = lo + w/3 = 55/96`. The two notions differ here. **[P,E]**

### 7.4 Corollary 6.2 (new): quasi-perfection does not select either

For quasi-perfection (van Damme 1984), each player's own later moves are taken from σ itself; only
the others tremble. In these coordinates the condition is the D-condition with the own-reach-stripped
gradient evaluated at the mixed profile `(σ_k, x_{−k})`. The certificate is `refine.perfect_cert`
with each row's own-player columns removed from the Jacobian, plus a stricter row set: every
interior coordinate whose D is not identically zero.

`qperf.py` sweeps `c33` through the Nash window at the slice of Theorem 6(5):
- **The open interval (1/2, 23/32), symbolically.** Both perfection and quasi-perfection are
  certified for every `c33` in the open interval: the same 8×8 minor (rows
  `a33, b11, b21, b33, b41, c11, c21, c33`; columns `a11, a12, a13, a21, a22, a23, a42, b11`), with
  `det = −95/3439853568 ≠ 0`.
- **Inward directions:** `s* = 3715/28782` for perfection and `s* = 1/14` for quasi-perfection.
- **The endpoints** 1/2 and 23/32 are first-order tight and not sign-definite (at `a21` and `a41`
  respectively). They are undecided at first order.

**Corollary 6.2.** *Quasi-perfection, like agent-normal-form properness, leaves `c33` an interval, at
least the open interval (1/2, 23/32) at this slice. Only normal-form properness selects a point
(55/96).* This closes open problem 2 for the refinements considered. **[E]**



---

## 8. Selection, correlation and the ante

### 8.1 A fixed tremble shape selects a corner and a pole **[F\*]**

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

### 8.2 The first player's silence needs independence **[E]**

The five-card result "no silent equilibrium" (Theorem 8) was proved by a correlated-equilibrium
certificate. Could one such certificate replace the 81 trees of Theorem 4? It would bound P1's betting
probability over all correlated equilibria, so it can exist only if P1 is silent in all of them.

**Theorem 9.** *Three-player Kuhn poker has a normal-form correlated equilibrium in which P1 bets with
probability 3308538/55243663 ≈ 0.0599 (cards 1, 2 and 4 with probabilities 0.050, 0.030, 0.160).*

*Proof.* `continuations/nfce_witness.json` is a distribution on 193 pure profiles. `nfce_verify.py`
checks in integer arithmetic every normal-form incentive constraint: for each player, each strategy
recommended with positive probability, each card and each alternative plan for that card (2,309 rows;
payoffs are additive over a player's cards, so single-card deviations suffice). ∎

In the weaker type-agent sense (each (player, card) sees only its own plan) P1 can bet with probability
0.1136 (`ce_witness.json`, 644 rows, exact). Payoffs leave the Nash set too: P2 gets −0.02027 in the
normal-form equilibrium, not −1/48.

*Consequence.* No Lagrangian or correlated-equilibrium certificate proves Corollary 4.1. The proof has
to use the product structure of independent strategies, as the label enumeration does.

### 8.3 The ante as a parameter **[E]**, **[F\*]**

Let every player ante `A`, with the bet still 1; the standard game is `A = 1`.

| ante | P1 | P2 | payoffs |
|---|---|---|---|
| `A < 2/3` | may bet the 4 | may bet the 4 | zero: nobody bluffs |
| `2/3 < A < 1` | silent | **silent** | unique |
| `A = 1` | silent | the SGS family | a segment (β) |
| `1 < A ≲ 1.09` | silent | bets | several vectors, differing for all three players |
| `1.1 ≲ A ≤ A2` | silent | bets the 4 always | unique |
| `A > A2` | **bets** (the 4 always from `A ≈ 1.42`) | | unique |

(Float sweep with machine-precision polish, except the family below.)

- **The standard game is a transition point.** Below `A = 1` the second player never bets; above it,
  it does. The SGS payoff continuum is the boundary case.
- **A closed-form silent family.** With `q = 3A + 1`: `a32 = (3A−1)/q`, `a33 = (6A−4)/q`,
  `b11 = b21 = c11 = c21 = 1/q`, `b33 = (3A−1)/q`, `b41 = 1`, the top card always calling, and the
  off-path calls with the 3 in P1's deterrence window

  > `(6A − 4)/q ≤ b32 + c33 ≤ (12A + 3)/q²`.

  `pot_exact.py` verifies in exact arithmetic that this is a Nash equilibrium across the window at
  `A = 11/10, 6/5, 5/4, 129/100`, and that P1 gains just outside it.
- **The window closes at `A2 = 1/2 + √23/6 ≈ 1.2993`** (`18A² − 18A − 7 = 0`). The sweep has P1 silent
  at 1.25 and betting at 1.30.

So P1's silence is a band-of-antes phenomenon as well as a small-deck one, and its mechanism is the
same at every ante: Table 3's `c33` interval is the `A = 1` case of a window whose ends cross at `A2`.
*Not proved:* that no other silent equilibrium exists past `A2`, or that every equilibrium is silent
below it.

---

## Limitations and open problems

1. **One game.** Everything here is the four-card game; the five-card game is treated separately.
2. **Perfection on the whole sequential set** is not decided (the `c23`-interior pattern has no uniform
   inward direction), and the endpoints of the `c33` interval are undecided at first order.
3. **The tremble selection is a machine-precision float result**, not a certificate, and 4 of 42 random
   shapes were not solved. Open: prove that every tremble shape of one order selects
   `(b11, b21, b23, c11) = (0, 1/4, 0, 0)`.
4. **The normal-form proper set**: which `β` it allows is open (see the companion paper on incidence).
5. **The ante.** Is P1 silent in every equilibrium for `2/3 < A ≤ A2`, and never beyond? What is the
   structure of the multiplicity window `1 < A ≲ 1.09`? Each needs the 81-cell machinery at that ante.
6. **Certificates.** `proof34/` holds the trees; the older cross-check certificates (about 64 GB) are
   outside git.

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

