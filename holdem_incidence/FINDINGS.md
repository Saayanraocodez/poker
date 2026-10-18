# Findings: does off-path behaviour decide who pays, beyond Kuhn poker?

**Question.** In a three-player game a unilateral deviation's payoff effect is split between the
other two players. In three-player Kuhn poker that split is decided by behaviour at information
sets nobody reaches, and it has simple poles at the edges of the equilibrium set. Does this survive
in Hold'em river games with real cards, and if so, under what conditions?

**Answer, in one paragraph.** Yes, but only under a precise condition, which is now both proved
and observed. The mechanism needs an action that some player **never takes with any hand** (an
"opponent-silent" action), so that the responses to it are genuinely off path.
- **Pot 1.5 (24-hand JJ–AA river game):** P1 never opens, and the mechanism is present.
  - Rationalising the CFR profile gives an **exact** Nash equilibrium.
  - Its off-path responses carry **exact simple poles**. At each pole the deviation costs the
    deviator exactly nothing and moves a nonzero amount between the other two players.
  - The equilibrium condition holds exactly up to the pole.
- **Every other configuration:**
  - The 24-hand game at pots 3 and 6, four boards with a broader 36-hand support, and two
    asymmetric weightings.
  - In all of them P1 opens with some hands, so no response set is opponent-silent, and the scan
    found **0 witnesses in all 33 profiles**.
  - Theorem 8 (THEORY.md) predicts this. The only near-unreached sets are a player's continuations
    after an action they essentially never take, and those provably carry no cross effect.
- **Imposing silence at pot 3** brings the exact poles back. But the deterrence windows of the
  bluff and the value bet do not overlap, so no equilibrium carries them.
- **The pot threshold (§3).** P1's silence, and with it the exact poles, lasts from pot 1.5 up
  to **pot 759/256 ≈ 2.965**, certified by exact Nash equilibria. At **pot 381/128 ≈ 2.977**
  every DCFR seed opens. The switch sits in a window 1/256 wide in the prior contribution, just
  below Kuhn's pot of 3.
  - The certified silent branch ends **exactly at pot 3c\* ≈ 2.970210**, with c\* an algebraic number
    of degree 10 (§3.1). This is the end of that branch, not a proof that no other silent
    equilibrium exists above it.
  - **For every pot in [4, 6] no P1-silent Nash equilibrium exists at all** (with a suit-symmetric
    check part, and whatever the responses to P1's bet). This is proved by exact correlated-equilibrium
    certificates valid on whole intervals of the pot, each replayed by an independent checker
    (§3.2, THEORY.md Theorem 12). Pots in (2.970, 4) remain open.

These are statements about the **specified conditional river games**, not about unrestricted
Hold'em.

Theory: [`THEORY.md`](THEORY.md). Code and commands: [`README.md`](README.md). Every number below
comes from a file under `results/`.

---

## 1. Verified exactly (rational arithmetic, independent oracles)

**The bridge is an exact correspondence** (`results/bridge/bridge_checks.json`,
`tests/test_bridge.py`).
- The game: board 2c 4d 6h 8s Tc; each seat's possible hands JsJh, QsQh, KsKh, AsAh; pot 3 bb;
  stacks 1 bb; min bet 1 bb; no open fold.
- 24 ordered deals, each of probability exactly 1/24, onto Kuhn's 24 deals.
- 13 terminal histories per deal and 312 leaves.
- 48 binary information sets, in bijection with Kuhn's (player, card, situation) coordinates,
  with the same legal actions.
- All **312/312 terminal payoff triples equal Kuhn's**, checked against an independent Kuhn rule
  and against kuhn3's own terminal function. All sum to 0.
- **Expected utilities equal kuhn3's exactly** at 10 profiles:
  - six SGS family points, including both β-corners;
  - the off-path witness of MASTER_DATA;
  - three random rational profiles.
- **All 48 derivative vectors U(x=1) − U(x=0) equal kuhn3's exactly** at each (480/480).
- The float engine agrees with the repository's `kuhn3p` to < 1e-14.

Scope: an exact correspondence between these two specified continuation games. It does not show
that these ranges arise at an equilibrium of unrestricted Hold'em, nor that the continuation
equilibrium extends to the start of a hand.

**The full best response is validated** (`tests/test_bestresponse.py`, `tests/test_extension.py`).
- It equals brute-force enumeration of all 2^16 pure strategies per player, at random profiles
  and at an SGS point (exact).
- It gives r = (0, 0, 0) exactly at every family point.
- At the witness's Table-2 projection (b12 := 0) it gives **r1 = 1/300 exactly**, the known value.
- **Coordinated case.** P1 bets the A and would fold after checking. The coordinate-gradient search
  of kuhn3 reports *no* profitable direction. The full best response finds **r1 = 1/4 exactly**, by
  checking and then calling, and brute force confirms it.
- On a multi-action tree (stacks 2, bet 1 bb or all-in, one raise), it matches a per-hand brute
  force.

**Kuhn's off-path pole is reproduced exactly** (`results/positive_control/`, plot
`kuhn_c33_pole.png`). At sub-family B with b11 = b21 = 3/20, b32 = 2/5, c11 = 1/4:
- P1's a11 bet has an exact root c33* = **1/10 = 1/2 − b32**, cross effect (−1/6, 0, 1/6), and
  numerator (0, +11/480, −11/480).
- P1's a41 bet has its root at **29/80**.
- P1's exact residual is **0 on [1/10, 29/80]** and positive outside: Table 3's window.
- The same preregistered scan, run blind on 7 exact SGS profiles, returns these poles among 6–16
  validated witnesses per profile, all with exact rational roots. On 3 DCFR profiles of the bridge
  it returns 14–16 each.

**The 24-hand expansion** (JJ, QQ, KK, AA, all six combos each).
- 6,480 legal ordered deals, 84,240 leaves, and 1,296 deals with at least two equal-strength
  hands, matching the audit.
- 288 binary information sets; chips are conserved at every leaf.
- **The Kuhn equilibria do not lift.** Every combo playing its rank's SGS strategy has exact
  NashConv **0.222–0.269 bb** at all six family points tested. Card removal and ties change the
  game.

**Exact pole witnesses beyond the four-type embedding** (`results/panel/pot_pot1.5_JJAA24/`,
`results/witness_sweeps/`, plots `witness_sweeps_*.png` and `witness_incidence_*.png`). The game:
the 24-hand JJ–AA game with prior contribution 1/2 each (pot 1.5), stack 1 = min bet, so all-in is
the only bet, by the rules.
- Three DCFR seeds end at NashConv 1.26e-8 to 1.44e-8 bb.
- **Rationalising** each profile (limit_denominator 10⁶, rows renormalised exactly) gives an
  **exact Nash equilibrium**: exact residuals (0, 0, 0) and exact utilities (0, 0, 0).
- The equilibrium:
  - P1 and P2 never bet;
  - P3 bets AA always and bluffs JJ ≈ 29 %;
  - P1 and P2 call only with AA.
  - So every response to a P1 or P2 bet is exactly unreached (opponent-silent).
- In the lowest-NashConv seed, **all 10 class-level witnesses** found by the scan are exact. For
  each, with θ the off-path response and the deviation P1's or P2's bet:
  - the root θ* is an exact rational number;
  - D_A(θ*) = 0 exactly, with a nonzero numerator;
  - the residuals at θ* are exactly (0, 0, 0).
- Example: **θ = P2's call with KK facing P1's bet** (baseline 0.055), deviation = P1's AA value
  bet, θ* ≈ 0.2339.
  - Below θ* the family stays an exact equilibrium.
  - At θ* the AA bet costs P1 exactly nothing and moves 0.0180 bb (per unit of probability) from
    P2 to P3.
  - Beyond θ* the AA bet pays: r1 grows linearly.
  - ρ(P1→P3) has a simple pole at θ* (plot `witness_incidence_pot_pot1.5_JJAA24.png`).
- Independent re-check (`scripts/verify_pot15.py`, log in `results/witness_sweeps/`), for the JJ-call witness: exact residuals 0 at θ*
  and at θ* − 1/1000, and r1 = 8.36e-5 > 0 at θ* + 1/1000. So θ* is exactly the window's endpoint,
  as Theorem 7 says.

---

## 2. Measured evidence (float64 full enumeration; residuals reported, not assumed)

All profiles are complete three-player profiles from one run each (never assembled across runs).
Selection was by the declared residual rule only: NashConv(average) ≤ 10⁻³ × pot. All 41 trained
profiles passed, and all were analysed.

**Pilot: 24-hand game, pot 3, 6 seeds × {CFR+, DCFR} × 30,000 full-traversal iterations.**
- **Residuals.** Average-strategy NashConv:
  - DCFR 1.8e-4 to 3.0e-4 bb;
  - CFR+ 2.7e-4 to 3.8e-4 bb.
  - The current strategies do not converge (NashConv 1.7e-3 to 1.0e-2).
  - No information set had zero averaging weight.
- **Play.** P1 opens AA 53–58 % (value) and JJ 22–24 % (bluff), and QQ/KK essentially never. P3
  has the positional advantage: utilities ≈ (−0.047, +0.003, +0.044).
- **Directions** (declared tolerances: |D_A| ≤ 10·max r_i ⇒ unresolved):
  - 80–112 costly;
  - 124–158 unresolved (indifferent within error);
  - 42–50 "profitable". These are only the leftover mass at nearly pure dominant actions:
    (1−x)·D_A ≤ 1.2e-6 bb, far below r_A.
  - Every direction satisfies |ΣD| ≤ 1.8e-14 (max over all 48 analysed profiles).
- **Off-path scan:** 12 rare sets per profile, **all own-rare** (P2's continuations after checking
  AA, which P2 always bets). 432 combo-level and 12 class-level pairs per profile: **0 witnesses**
  in 12/12 profiles.
- **Contrast sweep** of the Kuhn analogue (P3's KK call after B:1-F), `pilot/contrast_*.csv`.
  - It is **on path** here (reach ≈ 0.05, baseline ≈ 0.76).
  - P1's JJ bluff is near-costless at the baseline and moves ≈ 0.061 bb from P2 to P3: the on-path
    "costless transfer" phenomenon of Kuhn survives.
  - The equilibrium window in θ is a single point: r1 rises to 0.27 at θ = 0 and 0.017 at θ = 1.
    This is Theorem 7(c), a mixed coordinate.

**Sensitivity panel (fixed and hashed before any panel result; DCFR, 3 seeds × 12,000 iterations).**

| game | NashConv (bb) | P1's opening | rare sets (kind) | witnesses (class level) |
|---|---|---|---|---|
| 24-hand, **pot 1.5** | 1.3e-8 – 1.4e-8 (exact after rationalisation) | **never** | 144 opponent-silent | **10–12 per seed, exact** |
| 24-hand, pot 3 (pilot) | 1.8e-4 – 3.8e-4 | AA 0.53–0.58, JJ 0.22–0.24 | 12 own | 0 |
| 24-hand, pot 6 | 9.8e-6 – 4.9e-5 | AA 0.97–0.99, JJ 0.27–0.28 | 12–14 own | 0 |
| R36, dry board | 2.3e-5 – 3.9e-5 | AA 0.29, KK 1, AKs 1, JTs 0.03 | 47–49 own | 0 |
| R36, paired board | 1.9e-5 – 4.0e-5 | AA 0.43, JTs 0.48, 76s 1 | 18 own | 0 |
| R36, three-flush board | 6.9e-6 – 1.4e-5 | KK 1, 99 0.67, JTs 0.56, KQs 0.50, 98s 0.31 | 31 own | 0 |
| R36, connected board | 8.4e-6 – 2.3e-5 | 76s 1, 54s 1, JTs 0.76, 98s 0.31 | 16–18 own | 0 |
| R36, P1 value ×2 | 1.6e-5 – 4.6e-5 | AKs 1, KQs 1, KK 0.96, AA 0.40, 76s 0.24 | 48 own | 0 |
| R36, P3 bluffs ×2 | 2.0e-5 – 3.0e-5 | AKs 1, KK 1, AA 0.28, JTs 0.07 | 49–53 own | 0 |

R36 = pairs AA KK 99 55 plus the spade and heart combos of AKs KQs JTs 98s 76s 54s, minus board
cards. The "kind" column comes from the classification of THEORY.md Theorem 8. Retained negative
findings: the eight non-silent configurations.

**OP2 — imposed P1 silence, 24-hand game, pot 3** (`results/op2_silent/`, plot `op2_sweep.png`;
exploratory, preregistered as amendment 1).
- **The restricted game converges:** P1's opening is forced to check, and the restricted
  NashConv is 7.0e-6 to 9.3e-6.
- **The deterrence search.** The 72 unreached responses to a P1 bet are chosen by exact coordinate
  minimisation from 5 declared starts. The best leaves P1 a full-game gain of **1.04e-3 to
  1.10e-3 bb** in all three seeds.
  - JJ bluffs are exactly deterred (margin ≤ 6e-11).
  - QQ and KK are deterred by 0.0027 and 0.0049–0.0075.
  - **AA value bets still pay**, about +1.8e-4 per combo.
- **The θ sweep** (P3's KK call after B:1-F; P2 has folded):
  - The utilities are exactly constant (θ is unreached).
  - Theorem 5's form holds with **C_P2 = 0**.
  - The JJ-bluff root is **θ* = 27/32 exactly** in every seed, with cross effect ≈ (−0.1778, 0,
    +0.1778).
  - The AA value-bet root is ≈ 0.829, with cross effect ≈ (+0.0722, 0, −0.0722).
- **The windows {θ ≥ 27/32} (bluff deterred) and {θ ≤ 0.829} (value bet deterred) do not meet.**
  The window is empty and no equilibrium carries either pole. It is the same "calling deters
  bluffs but feeds value bets" obstruction found in (3,5)-Kuhn.

**Two-player constant-sum control** (`results/control/`): CFR+, 2 seeds, NashConv 4.4e-4 and
9.8e-4. For every defined direction the opponent's share is ρ = 1 (to 12 digits), there are 0
costless transfers, and max |D_1 + D_2| = 0. Proposition 2 is confirmed.

**Training notes.** Full traversal throughout; sampling was not needed at these sizes (10–42
ms/iteration single-process, < 200 MB; `results/smoke/budget.json`). DCFR beat CFR+ on the 24-hand
game. Every run checkpoints and resumes bit-identically (`tests/test_cfr_ranges.py`).

---

## 3. The pot threshold: where P1's silence, and the exact poles, end

Files: `results/potsweep/` (`threshold.json`, `certification.json`, `verify.json`), `results/potsweep_48k/`
and the plot `potsweep_threshold.png`. Preregistered as amendments 2–6; every amendment says what had
already been seen when it was written.

**Setup.**
- The game is the 24-hand JJ–AA game of §1–2: board 2c 4d 6h 8s Tc, stack 1 = bet, all-in only.
- The prior contribution is c per seat, so the pot is 3c. There are 20 values of c in (1/2, 1):
  - a grid in sixteenths;
  - then two preregistered rounds of quarter-point refinement around each switch.
- DCFR ran 3 seeds × 12,000 iterations per point, plus the declared continuation of the seven grid
  points to 48,000 iterations.
- Reused end points: pot 1.5 (§1), pot 3 (the pilot) and pot 6 (the panel).

**Result.**
- **P1 never opens, certified by exact Nash equilibria, at 16 of the 20 contributions.** These run from
  pot 1.5 up to **pot 759/256 ≈ 2.965** (c = 253/256).
- **At pot 381/128 ≈ 2.977 (c = 127/128) every DCFR seed opens:** AA 0.60–0.62 and JJ 0.25. This
  matches pot 3 (AA 0.53–0.57) and pot 6 (AA 0.97–0.99).
- **The switch therefore lies in (759/256, 381/128].** That window is 1/256 wide in c, where the
  preregistered refinement stops, and it sits just below Kuhn's pot of 3.
- **In DCFR the switch is a jump.** At c = 253/256 P1 opens AA with float probability at most
  2.4e-3. One step later the probability is about 0.6.
- **P2's silence ends first,** between pot 285/128 ≈ 2.227 and pot 9/4.
  - Exact equilibria with both P1 and P2 silent are certified up to c = 95/128.
  - At c = 3/4 every DCFR seed has P2 betting AA after P1 checks, with probability 0.17–0.26.
  - Once P2 bets, only the 72 responses to P1's bet stay opponent-silent (Theorem 8: 144 → 72).
    The exact witnesses per certificate fall from 17–28 to 12–15.
  - They stay at 12–15 all the way to c = 253/256. **The mechanism is present wherever P1 is
    silent.**
- **The 2.4e-3 is not evidence of opening.** It is P1's float opening at a certified point, and it
  lies within DCFR's accuracy: every certified point (up to 2.4e-3 at 253/256) also has an exact
  equilibrium in which P1 never opens.

| c | pot | P1 opens (DCFR, max class) | P2 bets AA after check (DCFR) | NashConv (bb) | rare sets (T8) | float-scan witnesses | exact P1-silent certificate (seeds; field) | exact witnesses |
|---|---|---|---|---|---|---|---|---|
| 1/2 † | 3/2 | 3.6e-8 – 5.0e-8 | 7.9e-8 – 9.4e-8 | 1.3e-8 – 1.4e-8 | 144 opp.-silent | 10–12 | 3/3 (Q, 10⁶ rationalisation) | 10–12 † |
| 9/16 | 27/16 | 3.7e-8 – 4.2e-8 | 1.1e-7 – 1.2e-7 | 2.3e-6 – 5.4e-6 | 144 opp.-silent | 5–7 | 3/3; 48k 3/3 (Q) | 17–19 |
| 5/8 | 15/8 | 3.6e-8 – 4.2e-8 | 1.6e-7 – 1.7e-7 | 2.8e-6 – 3.6e-6 | 144 opp.-silent | 9–16 | 3/3; 48k 3/3 (Q) | 20 |
| 11/16 | 33/16 | 3.7e-8 – 5.1e-8 | 3.4e-7 – 3.8e-7 | 1.2e-6 – 3.9e-6 | 144 opp.-silent | 10–21 | 3/3; 48k 3/3 (Q) | 23–25 |
| 45/64 | 135/64 | 4.1e-8 – 5.4e-8 | 4.7e-7 – 5.4e-7 | 1.3e-7 – 7.5e-6 | 144 opp.-silent | 16–19 | 3/3 (Q) | 24 |
| 23/32 | 69/32 | 5.1e-8 – 6.1e-8 | 7.3e-7 – 9.3e-7 | 4.1e-7 – 2.6e-6 | 144 opp.-silent | 12–15 | 3/3 (Q) | 24–28 |
| 47/64 | 141/64 | 7.3e-8 – 5.5e-6 | 1.6e-6 – 2.7e-6 | 2.5e-7 – 4.4e-7 | 144 opp.-silent | 2–10 | 3/3 (Q) | 28 |
| 189/256 | 567/256 | 2.6e-6 – 1.1e-5 | 2.7e-6 – 7.3e-6 | 1.7e-7 – 5.5e-7 | 144 opp.-silent | 0–6 | 2/3 (Q) | 28 |
| 95/128 | 285/128 | 1.3e-5 – 4.4e-5 | 8.7e-6 – 3.7e-5 | 1.9e-7 – 6.3e-7 | 144 opp.-silent | 0–2 | 2/3 (Q) | 28 |
| 191/256 | 573/256 | 9.7e-5 – 3.7e-4 | 1.3e-4 – 5.0e-4 | 8.9e-7 – 3.2e-6 | 23–66 opp.-silent | 0 | none (polish: too many mixed rows, or unfinished) | – |
| 3/4 | 9/4 | 4.2e-8 – 6.4e-8 | 0.17 – 0.26 | 4.3e-7 – 6.8e-7 | 72 opp.-silent | 1–4 | 3/3; 48k 3/3 (Q) | 12–13 |
| 13/16 | 39/16 | 9.7e-7 – 5.3e-6 | 0.53 – 0.54 | 1.3e-3 – 1.9e-3 | 72 opp.-silent | 0 | none (DCFR does not converge) | – |
| 7/8 | 21/8 | 7.7e-8 – 1.2e-7 | 0.75 | 2.7e-6 – 5.6e-6 | 72 opp.-silent | 0–2 | 3/3; 48k 3/3 (Q(√286839393)) | 14–15 |
| 15/16 | 45/16 | 1.8e-7 – 6.6e-7 | 1 | 5.3e-6 – 7.8e-6 | 72 opp.-silent, 12 own | 3–11 | 3/3; 48k 3/3 (Q(√5814557254)) | 13 |
| 61/64 | 183/64 | 7.2e-7 – 1.5e-6 | 1 | 3.4e-6 – 5.6e-6 | 72 opp.-silent, 12 own | 1–2 | 3/3 (Q(√36429626521)) | 13–15 |
| 31/32 | 93/32 | 2.7e-6 – 5.5e-6 | 1 | 3.4e-6 – 5.0e-6 | 72 opp.-silent, 12 own | 0 | 3/3 (Q(√397698368041)) ‡ | 12–14 |
| 125/128 | 375/128 | 6.9e-6 – 1.5e-5 | 1 | 2.4e-6 – 3.8e-6 | 72 opp.-silent, 12 own | 0 | 3/3 (Q(√103487875626361)) | 13 |
| 63/64 | 189/64 | 4.5e-5 – 1.1e-4 | 1 | 2.8e-6 – 4.8e-6 | 32–72 opp.-silent, 12 own | 0 | 3/3 (Q(√6573839017921)) | 13 |
| **253/256** | **759/256** | 2.5e-4 – 2.4e-3 | 1 | 3.4e-6 – 5.5e-5 | 6–24 opp.-silent, 12 own | 0 | **3/3 (Q(√1696550223293641)) ‡** | 12 |
| **127/128** | **381/128** | **0.60 – 0.62** | 1 | 3.1e-5 – 3.4e-5 | 12–14 own | 0 | none ‡ | – |
| 255/256 | 765/256 | 0.57 – 0.58 | 1 | 9.6e-5 – 1.2e-4 | 12 own | 0 | none ‡ | – |
| 1 § | 3 | 0.53 – 0.57 | 1 | 1.8e-4 – 3.0e-4 | 12 own | 0 | none | – |
| 2 § | 6 | 0.97 – 0.99 | 1 | 9.8e-6 – 4.9e-5 | 12–14 own | 0 | none | – |

Notes to the table:
- Columns 3–7 are the 12,000-iteration DCFR profiles. The table is printed by
  `python scripts/potsweep.py table`.
- "exact witnesses" counts the class-level poles found by the scan repeated in exact arithmetic on
  the certified profile (one certificate per profile).
- † At pot 1.5 the count is different: it is the float-scan witnesses, each re-checked exactly (§1).
- ‡ The P1-silent variant with the deterrence search; see below.
- § Reused: the pilot (DCFR, 6 × 30,000) and the panel.

**How the silent points were certified.** The declared 10⁶ rationalisation certified **none** of the
81 new profiles (60 at 12,000 iterations, 21 at 48,000). The largest exact residual per profile
after rounding was 3.8e-8 to 6.3e-5 (about 1e-3 at c = 13/16), because the DCFR averages lie on
continua of equilibria. Three steps did the work. Each was declared in an amendment before its main
run (amendment 4 records one test run made before it):
- **Class-symmetric polish** (amendments 3–4).
  - The game is invariant under the 24 suit permutations, so a profile in which every combo of a
    hand class plays alike is a 4-type profile.
  - From each DCFR profile: average within hand classes, snap near-pure on-path rows, solve the
    indifference conditions of the remaining mixed rows exactly, and round the off-path rows.
- **Quadratic fields** (amendment 4).
  - Up to c = 3/4 the solutions are rational.
  - From c = 7/8 they are quadratic surds. P1's QQ call and P2's KK call enter two bilinear
    indifference conditions, and eliminating between them leaves a quadratic.
  - Those profiles are evaluated exactly in Q(√d) by the unchanged engine, with an exact number
    type (`hinc/surd.py`, checked against the Fraction and float engines by `tests/test_surd.py`).
- **Deterrence search** (amendments 5–6).
  - At c = 31/32 seed 1 and at c = 253/256, DCFR's responses to P1's bet do not deter P1.
  - There the 12 responses are chosen by a declared deterrence search with P1's opening fixed at
    exactly 0, then rounded.
- **Only the exact full best-response check certifies.** There are 64 certificates, and all 64 pass
  an independent re-check (`scripts/verify_potsweep.py`, log in `results/potsweep/`). It parses each
  stored exact profile and confirms:
  - exact residuals (0, 0, 0);
  - P1's opening exactly 0;
  - one witness, re-derived per combo.

**Two exact regularities.**
- **The bluff frequency.** On the silent branch the JJ bluff frequency is exactly
  **13/(24c + 8) = (13/8)/(3c + 1)** at every certified point of the sweep (9/16 ≤ c ≤ 253/256),
  except c = 7/8.
  - This is the bluff that leaves the bluff-catcher's KK indifferent, in pot-odds form.
  - At pot 1.5 it does not hold. P3's bluff there is not pinned: 0.29, 0.38 and 0.42 in the three
    certificates of §1.
  - For c ≤ 3/4 it is P3's bluff after two checks: 26/43, 13/23, 26/49, …, 1/2 at c = 3/4.
  - For c ≥ 15/16, where P2 bets AA always, it is P2's bluff after P1 checks: 26/61, 8/19, 52/125,
    …, 104/253.
  - At c = 7/8, where P2 still mixes with AA (≈ 0.752, a quadratic surd), neither bluff has this
    form.
- **The deterring responses.** Near the top they have one shape: P2 calls only with AA, and after P2
  folds P3 calls with AA and with KK at θ ≈ 0.82–0.84 (OP2's coordinate).
  - The best float margins the search finds (seed 1 at 31/32; identical in all three seeds at the
    other three points):

    | c | 31/32 | 253/256 | 127/128 | 255/256 |
    |---|---|---|---|---|
    | best margin (bb) | +1.8e-3 | +1.5e-4 | −1.8e-4 | −5.1e-4 |

  - The margins fall almost linearly and cross zero at c ≈ 0.990 (pot ≈ 2.970), inside the bracket.
  - At 127/128 and 255/256 the on-path part still solves exactly (r2 = r3 = 0), but P1 keeps
    r1 = 3.6e-4 and 1.0e-3 respectively.

**What is not shown** (declared and retained):
- **The upper end of the bracket is not a non-existence proof.** It rests on DCFR selection. §3.1
  proves exactly that the certified silent branch ends at c\* ≈ 0.990070, but it does not show that
  no P1-silent equilibrium exists at c ≥ 127/128. By upper hemicontinuity, silent equilibria at c
  arbitrarily close to 1 would force one at pot 3, and OP2's local search did not find one there.
- **Two points are not certified.**
  - At c = 13/16 DCFR never converged: NashConv 1.3e-3 to 2.2e-3, even at 48,000 iterations. The
    polish of the 48,000-iteration profiles found more than 12 mixed rows. The polish of the
    12,000-iteration profiles (at most 12 unknowns, so up to 4,096 exact vertex evaluations each)
    was stopped unfinished.
  - At c = 191/256, where P2 starts to bet, two seeds had more than 12 mixed rows and the third was
    stopped unfinished.
  - Two further profiles (seed 1 at 189/256 and at 95/128) were not certified.
  - `results/potsweep_polish_log.txt` lists every polish outcome.
- **The certificates are class-symmetric equilibria,** and the equilibrium sets are continua. For
  example, P2's AA frequency ranges over 0.18–0.27 across the five distinct certificates at c = 3/4.
  The exact witness counts are therefore counts at one certificate each.
- **The float-scan counts are unreliable near the switches.** They drop wherever DCFR leaves a
  residual P1 opening of 1e-5 to 1e-4, which lifts the response sets above the 1e-6 reach cutoff.
  The exact counts do not drop.
- **The N = n + 1 analogue.** In this game, P1's silence, and with it the off-path mechanism, holds
  only while the pot-to-bet ratio is below a threshold in (2.965, 2.977]. For the certified branch
  that threshold is exactly 3c\* ≈ 2.970210 (§3.1). That plays the role of Kuhn's deck-size law, in
  pot-to-bet ratio instead of deck size.

### 3.1 The exact end of the silent branch

Files: `results/threshold/` (`derivation.json`, `certificates.json`, `c_lo/policy_exact.json`,
`silent_threshold_log.txt`), the configs in `configs/threshold/`, and the script
`scripts/silent_threshold.py`. Preregistered as amendments 7–8.

"The branch" means the following profiles:
- class-symmetric profiles in which P1 never opens;
- the on-path support of every certificate from 15/16 to 253/256. That support has 7 mixed class
  rows:
  - P2's JJ bluff;
  - P3's JJ and QQ bets after two checks;
  - P1's QQ call after K-K-B:1;
  - P2's KK call after K-K-B:1-F;
  - P1's QQ and KK calls after K-B:1-F.
- Every other on-path row is as in those certificates.

**Result.**
- **The branch stops being a Nash equilibrium at c\* = 0.99006984393951064639…** That is pot
  3c\* = **2.97020953181853193918…**.
  - c\* is the unique root in (1038163/2²⁰, 1038164/2²⁰) of an irreducible polynomial of degree 10:
    ```
    59243308056576 c^10 + 27305557622784 c^9 - 347454200540160 c^8 - 103553951433984 c^7
      + 216450292773024 c^6 + 137358663110244 c^5 + 14929141080267 c^4 - 7740717415038 c^3
      - 2404935493182 c^2 - 230841755667 c - 6393808520
    ```
  - It lies inside the sweep's bracket (759/256, 381/128]. It is where the float deterrence margins
    above crossed zero (≈ 0.990).
- **The branch is an exact Nash equilibrium for every c in [c_s, c\*], and for no c in (c\*, 2].**
  - c_s = 0.90631245784857080… (pot 2.7189…) is a root of an irreducible polynomial of degree 8.
  - Just below c_s, P2 prefers to check and call with AA, so the support changes. At c = 7/8 the
    certificates have P2 mixing AA.
  - The on-path part alone stays an equilibrium up to c_u = 1.10021699619527157… (pot 3.3007…),
    where P2 starts to bet QQ. So between c\* and c_u only the deterrence of P1's opening fails.

**How.** Everything is exact; the only floats are printed decimals.
- **An independent class-level model.** It is written from the rules, not from `hinc/`:
  - four hand classes per seat;
  - class-triple weights out of 6480: 216 for three ranks, 36 when two seats share a rank, 0 when
    all three do;
  - the 13 terminal histories, with payoffs affine in c.

  Checks against the engine:
  - It equals the engine's exact utilities at all 64 stored certificates and at 6 random profiles.
  - Its 7 indifference equations equal the engine's at all 23 polish records with this support.
  - The game is invariant under the 24 suit permutations, so checking a class-symmetric profile at
    class level checks it in the 24-hand game. One combo's deviation gains 1/6 of its class's.
- **Closed form in c.**
  - The JJ bluff is x₀ = 13/(8(3c+1)).
  - P1's QQ and KK calls after K-B:1-F enter only through their sum, 27(2c−1)/(8(3c+1)). The split
    is free.
  - P1's QQ call against P3's bet is the smaller root of
    6(48c²+106c+17)x² − (1584c²+8139c+574)x + 7(288c²+57c−260) = 0. The other root exceeds 1.
  - Its discriminant is Δ₀(c) = 186624c⁴ + 20196000c³ + 68320809c² + 13810860c + 1072036, which is
    irreducible.
  - P2's KK call and P3's two bets are rational in c and that root. So the whole branch lies in
    Q(c, √Δ₀(c)).
  - The closed form reproduces all 16 stored 7-row certificates exactly. For example, the field
    Q(√1696550223293641) at 253/256 is Q(√Δ₀(253/256)).
- **Support over c.** There are 80 conditions:
  - the mixed rows lie in [0, 1];
  - no pure plan of any class of any player does better on path.

  Each condition is an exact element of Q(c, √Δ₀). Its sign on an interval is decided by isolating
  the real roots of its norm and its denominators, then evaluating exactly between them.
- **Deterrence.** P1's class gains from opening are bilinear in the 12 class responses to the
  all-in. Take the shape the float search found: P2 calls only with AA; P3 folds after B:1-C; after
  B:1-F, P3 calls with AA and calls with KK with probability θ. Then:
  - the JJ bluff is deterred iff θ ≥ θ_J(c) = **27(2c−1)/(8(3c+1))**. This is rational, and at
    pot 3 it is 27/32, OP2's root.
  - the AA value bet is deterred iff θ ≤ θ_A(c) = (180/13)(V_AA(c) − 9c/20). Here V_AA ∈ Q(c, √Δ₀) is
    P1's AA value from checking.
  - QQ and KK stay deterred throughout the window.
  - θ_J < θ_A below c\* and θ_J > θ_A above it. There is a single crossing on (7/8, 2), and c\* is
    that crossing.
- **No other responses help.**
  - The weights λ_JJ = 13/180 and λ_AA = 2(3c+1)/45 cancel θ.
  - At each of the 4096 vertices of the response box, λ_JJ·gain_JJ + λ_AA·gain_AA is at least its
    value at the shape, for every c in (7/8, 2). There are 1407 distinct polynomial differences, and
    each is checked exactly.
  - A multilinear function attains its minimum over a box at a vertex. So for c > c\*, every
    class-symmetric response profile leaves the JJ bluff or the AA value bet profitable.

**Exact certificates on both sides.** Both come from the engine, not the model.
- **c_lo = 1038163/2²⁰** (pot ≈ 2.9702082): an exact P1-silent Nash equilibrium.
  - Its residuals are (0, 0, 0) in Q(√479301108037189029117221334121).
  - It uses θ = 1029/1235 ∈ [θ_J, θ_A] = [0.8331977, 0.8331985].
  - It is re-checked after re-parsing the stored text (`c_lo/policy_exact.json`).
- **c_hi = 1038164/2²⁰ = 259541/262144** (pot ≈ 2.9702110): no class-symmetric responses deter P1.
  - From the engine's own payoff tables and values, λ_JJ·gain_JJ + λ_AA·gain_AA ≥ +1.04e-8 at all
    4096 vertices. This is exact, in Q(√11078542211508872272280161).
  - The on-path part alone is still an exact equilibrium: residuals (0, 0, 0) with P1's opening
    fixed to check.
  - With θ = 1029/1235, P1's full residual is 9.6e-8.

**Scope.** c\* is the threshold of **this branch**: this on-path support, class-symmetric profiles,
and Nash equilibrium only. It does not show that no P1-silent equilibrium exists above c\*. Three
things are not excluded:
- other on-path supports, for example P2 mixing AA as at 7/8;
- combo-asymmetric responses. P1's gains are bilinear, so averaging the responses over suit
  permutations does not preserve deterrence.
- correlated devices.

### 3.2 No P1-silent equilibrium at any pot in [4, 6] (certified)

Files: `results/silent_ce/` (one JSON per certificate or failed attempt, its log, and `check.json`),
`scripts/silent_ce.py` (prover), `scripts/check_silent_ce.py` (independent checker).

**The question.** §3.1 shows where one branch of P1-silent equilibria ends. Does *any* P1-silent
Nash equilibrium exist at larger pots?

**The method** (THEORY.md Theorem 12). A profile in which P1 never opens is Nash iff two things hold:
- its check part is a Nash equilibrium of the restricted game G_c (P1 forced to check);
- the 72 combo-level responses y to P1's all-in deter every P1 combo.

**The certificate.** It uses weights λ over P1's four classes and correlated-equilibrium multipliers
μ over the 12 class agents' (plan, deviation) pairs.
- **B_s** = the maximum over class-level pure profiles of G_c of
  L = Σ λ_k V_k + Σ μ (u_a(ρ) − u_a(τ)) on the plan ρ the agent plays.
  - At any suit-symmetric Nash equilibrium of G_c every bracket is ≥ 0, so Σ λ_k V_k ≤ B_s.
  - The check is exhaustive: 160,000 P2 × P3 class plans, after which P1's classes separate.
- **B_y** = the minimum of Σ λ_k Ebet_k(y) over **all** 2⁷² combo-level response vertices.
  - The function is multilinear, so the minimum is at a vertex.
  - The check enumerates P2's 2²⁴ choices; P3's responses separate given them.
- **If B_s < B_y**, deterrence would need Σ λ_k Ebet_k(y) ≤ Σ λ_k V_k ≤ B_s < B_y. That is
  impossible, so no such equilibrium exists.

The proposer is a float LP (HiGHS) with cutting planes, and it decides nothing.

**Point results**:

| c | pot | coarse (CCE) relaxation | correlated (CE) relaxation |
|---|---|---|---|
| 1 | 3 | margin −0.0275 | margin −0.0120 |
| 11/10 | 3.3 | −0.0219 | −0.0078 |
| 5/4 | 3.75 | −0.0135 | −0.0024 |
| 13/10 | 3.9 | — | −0.00038 (no certificate) |
| 4/3 | 4 | — | **certified**, gap 9.5e-4 |
| 27/20 | 4.05 | — | **certified** |
| 11/8 | 4.125 | −0.0065 | — |
| 7/5 | 4.2 | −0.0051 | **certified** |
| 29/20 | 4.35 | −0.0024 | **certified** |
| 3/2 | 4.5 | **certified**, gap 2.0e-4 | — |
| 2 | 6 | **certified**, gap 0.017 | — |

**Whole intervals** (THEORY.md Proposition 13). With the multipliers fixed, every payoff is affine in
c. So B_s is convex in c and B_y is concave in c, and one rational (λ, μ) that separates at both
ends of an interval separates on all of it. Each interval below is certified exactly at both ends
with one set of multipliers:

| interval of c | pot | margins at the ends |
|---|---|---|
| [4/3, 27/20] | [4, 4.05] | 5.0e-4, 5.0e-4 |
| [27/20, 7/5] | [4.05, 4.2] | 5.3e-4, 5.3e-4 |
| [7/5, 29/20] | [4.2, 4.35] | 3.0e-3, 3.0e-3 |
| [29/20, 3/2] | [4.35, 4.5] | 5.4e-3, 5.4e-3 |
| [3/2, 2] | [4.5, 6] | 5.2e-5, 5.1e-5 |

Their union is **c ∈ [4/3, 2]**: no P1-silent Nash equilibrium with a suit-symmetric check part, for
any responses to P1's bet, at any pot from 4 to 6. One set of multipliers does not stretch over
[4/3, 3/2] or [4/3, 2]; that is why the range is split.

**Checks.**
- **Independent re-check:** all 11 certificates (17 interval ends) pass (`results/silent_ce/check.json`).
  - B_s is recomputed from the engine's class table with the opposite decoupling: P1 × P3
    enumerated, P2 separating.
  - B_y is recomputed from a rule-based combo enumeration, with no engine.
  - Both equal the stored values exactly, and B_s < B_y every time.
- **Table cross-check:** at every c used, the class model and the engine agree on all 9,600
  restricted-game payoff entries.
- **Negative control:** at c_lo = 1038163/2²⁰, where an exact P1-silent equilibrium is certified
  (§3.1), the search finds no certificate (margin −0.0126), as it must.
- The proposer's weights reproduce the threshold proof's: at pot 3 it settles on λ ∝ (13/180 for
  JJ, 8/45 for AA).

**Scope.**
- Nash equilibrium only.
- The check part is suit-symmetric; that is how a 24-hand profile reduces to the class game. The
  responses to P1's bet are fully arbitrary.
- Suit-asymmetric check parts are not excluded.

**Why pots in (2.970, 4) stay open.** At c* an actual P1-silent equilibrium exists, so every valid
certificate must fail there. Relaxation margins must therefore shrink to zero as c falls toward
c*: the CE margin goes from −3.8e-4 at pot 3.9 to −0.012 at pot 3. Closing the gap needs an exact
method rather than a stronger relaxation: an exhaustive support enumeration of the class-symmetric
equilibria of G_c (32 class coordinates), followed by the deterrence check on each support.

---

## 4. Theory (THEORY.md)

Proved for every finite constant-sum n-player game with perfect recall, each with a computational
check (`results/theory/theory_checks.json`):
- **Exact affinity** of payoffs in any information set's row (Lemma 1).
- **Off-path parameters** have zero direct effect and an affine cross effect on every other
  player's deviation, summing to zero (Theorem 3).
  - **Own-unreached sets carry none:** checked exactly, 0 of 576 pairs nonzero.
- **ρ is Möbius in θ** with at most one simple pole (Corollary 4).
- **The residue identity** ρ = 1 + t/(C_A(θ − θ*)) holds whenever the third player is out of the
  pot (Theorems 5 and 9). This generalises Kuhn's R = t/D′. It holds exactly on the bridge and to
  ~1e-11 on OP2.
- **The window theorem:** along an off-path parameter the Nash set is a closed interval
  (Theorem 6).
- **Attainable poles sit at its endpoints;** mixed coordinates cannot carry them (Theorem 7).
- **The classification** of unreached sets into own / opponent-silent / blocker, with only the
  last two able to carry the mechanism (Theorem 8). It predicts all 48 analysed profiles without
  exception. It is also consistent with the 81 pot-sweep profiles of §3: witnesses appear only where
  opponent-silent sets exist.
- **One off-path parameter moves incidence along a straight line** in share space, for every n
  (Theorem 10). Exact in a 4-player river game.
- **Exact equilibria can be 10⁻⁶ apart and differ in ρ by 68,750** (Proposition 11): equilibrium
  accuracy cannot control incidence near a pole.
- **Silence decomposition and certificates** (Theorem 12): a first player's silence is a Nash
  equilibrium iff the check part is one and the off-path responses deter. Lagrangian certificates
  exclude it.
- **Certificates extend from two endpoints to a whole parameter interval** (Proposition 13). Used
  for every pot in [4, 6].

---

## 5. Limitations

1. **Conditional river games** with *specified* product priors, chosen ranges and an all-in-only
   action set. The all-in-only set is forced by the rules here (stack = min bet), so there is no
   bet-size abstraction in these experiments. Nothing here concerns equilibria of unrestricted
   Hold'em or whether these ranges arise upstream.
2. **Equilibrium accuracy.**
   - Certified exact: the pot-1.5 profiles (rationalisation plus exact best responses) and the 64
     pot-sweep certificates of §3 (class-symmetric exact equilibria, some in quadratic fields).
   - All other profiles are approximate equilibria with the measured residuals above.
   - "No witness" is relative to the declared tolerances (reach ≤ 1e-6 for candidates, etc.,
     `hinc/plan.py`).
3. **Scan coverage.** One θ (a combo, or a hand class moved together) against one upstream
   combo/class whose action leads into θ's history. Joint multi-parameter families are not
   scanned.
4. **OP2's deterrence search is local** (5 starts). It bounds the best achievable deterrence from
   above. It does not prove that no P1-silent equilibrium exists at pot 3.
5. **Refinements were not analysed** on the expanded games. Several pot-1.5 witnesses vary
   responses that are plausibly pinned by dominance (calling with AA, folding JJ), which
   sequential rationality would fix. The KK and QQ responses are belief-dependent analogues of
   Kuhn's c33. Their refinement status is open.
6. Seeds: 6 per pilot variant, 3 per panel game. The turn, side pots, short all-in raises and
   derived (upstream) priors are not implemented.

## 6. Unresolved, and the most informative next experiment

- **Close the gap (c\*, 4/3), i.e. pots (2.970, 4)** (most informative next).
  - §3.1: the certified silent branch ends exactly at c\*.
  - §3.2: no P1-silent equilibrium with a suit-symmetric check part exists for c ∈ [4/3, 2]. The
    responses to P1's bet may be arbitrary.
  - In between, relaxations must fail as c → c\*. The exact route is a support enumeration of the
    class-symmetric equilibria of the restricted game, with the deterrence check per support. Pot 3
    lies in this gap.
- **Suit-asymmetric check parts:** the certificates of §3.2 assume the check part is suit-symmetric.
- **Refinement of the pot-1.5 witnesses:** which survive sequential rationality?
- **The blocker route:** design polarised, card-overlapping ranges in which a public action is
  taken only by combos that block an opponent's hand.
- **Action abstraction:** run the implemented multi-size tree (`configs/extension_stack6_sizes.json`,
  tested) and compare against the all-in game.

## 7. Reproduce

```
python -m unittest discover -s tests -v
python scripts/bridge_checks.py
python scripts/smoke_budget.py
python scripts/run_training.py pilot 12 ; python scripts/run_training.py panel 14 ; python scripts/run_training.py control 2
python scripts/positive_control.py write ; python scripts/positive_control.py train ; python scripts/positive_control.py sweep
python scripts/silent_p1.py train ; python scripts/silent_p1.py analyse
python scripts/analyze_profiles.py pilot ; python scripts/analyze_profiles.py panel ; python scripts/analyze_profiles.py control ; python scripts/analyze_profiles.py positive_control
python scripts/pilot_contrast.py ; python scripts/witness_sweeps.py panel ; python scripts/verify_pot15.py ; python scripts/theory_checks.py ; python scripts/make_plots.py
# pot sweep (§3)
python scripts/run_training.py potsweep 21
python scripts/potsweep.py train 48000 potsweep_48k potsweep_c9-16_JJAA24 potsweep_c5-8_JJAA24 potsweep_c11-16_JJAA24 potsweep_c3-4_JJAA24 potsweep_c13-16_JJAA24 potsweep_c7-8_JJAA24 potsweep_c15-16_JJAA24
python scripts/analyze_profiles.py potsweep ; python scripts/analyze_profiles.py potsweep_48k ; python scripts/theory_checks.py t8
python scripts/potsweep.py certify ; python scripts/potsweep.py polish potsweep ; python scripts/potsweep.py polish potsweep_48k ; python scripts/potsweep.py polish_silent 61/64
python scripts/potsweep.py summary ; python scripts/potsweep.py table ; python scripts/potsweep.py plot ; python scripts/verify_potsweep.py
# the exact end of the silent branch (§3.1; ~1 min)
python scripts/silent_threshold.py all
# no P1-silent equilibrium at pots [4, 6] (FINDINGS 3.2)
python scripts/silent_ce.py run 4/3 c4-3_ce          # one point (HINC_CE_MODE=cce for the coarse relaxation)
python scripts/silent_ce.py interval 3/2 2 iv_c3-2_c2  # one certificate for a whole interval of c
python scripts/check_silent_ce.py                       # independent re-check of every stored certificate
```
Extend: add a config (pot, stacks, sizes, raise cap, ranges, weights) under `configs/` and point
`hinc/plan.py` at it. Re-running any training command resumes from checkpoints.
