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

## 3. Theory (THEORY.md)

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
  exception.
- **One off-path parameter moves incidence along a straight line** in share space, for every n
  (Theorem 10). Exact in a 4-player river game.
- **Exact equilibria can be 10⁻⁶ apart and differ in ρ by 68,750** (Proposition 11): equilibrium
  accuracy cannot control incidence near a pole.

---

## 4. Limitations

1. **Conditional river games** with *specified* product priors, chosen ranges and an all-in-only
   action set. The all-in-only set is forced by the rules here (stack = min bet), so there is no
   bet-size abstraction in these experiments. Nothing here concerns equilibria of unrestricted
   Hold'em or whether these ranges arise upstream.
2. **Equilibrium accuracy.** Only the pot-1.5 profiles are certified exact, by rationalisation plus
   exact best responses. All others are approximate equilibria with the measured residuals above.
   "No witness" is relative to the declared tolerances (reach ≤ 1e-6 for candidates, etc.,
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

## 5. Unresolved, and the most informative next experiment

- **The pot threshold** (most informative next): P1 is silent at pot 1.5 and bets at pot 3. Sweep
  the prior contribution between 1/2 and 1 on the 24-hand game, and certify each point exactly.
  This locates the switch at which the off-path mechanism appears. It would be the river-game
  analogue of Kuhn's N = n + 1 law, in pot-to-stack ratio instead of deck size.
- **Prove** (or refute) "no P1-silent equilibrium at pot 3", with the correlated-equilibrium
  certificate method that settled (3,5)-Kuhn.
- **Refinement of the pot-1.5 witnesses:** which survive sequential rationality?
- **The blocker route:** design polarised, card-overlapping ranges in which a public action is
  taken only by combos that block an opponent's hand.
- **Action abstraction:** run the implemented multi-size tree (`configs/extension_stack6_sizes.json`,
  tested) and compare against the all-in game.

## 6. Reproduce

```
python -m unittest discover -s tests -v
python scripts/bridge_checks.py
python scripts/smoke_budget.py
python scripts/run_training.py pilot 12 ; python scripts/run_training.py panel 14 ; python scripts/run_training.py control 2
python scripts/positive_control.py write ; python scripts/positive_control.py train ; python scripts/positive_control.py sweep
python scripts/silent_p1.py train ; python scripts/silent_p1.py analyse
python scripts/analyze_profiles.py pilot ; python scripts/analyze_profiles.py panel ; python scripts/analyze_profiles.py control ; python scripts/analyze_profiles.py positive_control
python scripts/pilot_contrast.py ; python scripts/witness_sweeps.py panel ; python scripts/verify_pot15.py ; python scripts/theory_checks.py ; python scripts/make_plots.py
```
Extend: add a config (pot, stacks, sizes, raise cap, ranges, weights) under `configs/` and point
`hinc/plan.py` at it. Re-running any training command resumes from checkpoints.
