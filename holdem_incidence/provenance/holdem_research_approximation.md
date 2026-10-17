# A Hold’em approximation for the deviation incidence project

Prepared 16 October 2026. Recommendation: study three-player river continuation games with explicit private-hand ranges, beginning with an exact embedding of the existing Kuhn model. Enlarge the ranges, then the betting tree, then the number of streets. This preserves the three separate payoff derivatives that define the research question and gives a known answer against which to validate the implementation.

The immediate research question is: **Does off-path response freedom still change the allocation of a unilateral deviation’s payoff effects in richer Hold’em continuation games, after controlling for equilibrium error?** A successful poker-playing agent is not sufficient evidence for that claim.

## Project context used

I read both August 29 copies of *Off-Path Play Decides On-Path Incidence: Deviation Transfers in Three-Player Kuhn Poker* and the Google document last modified October 3 that summarizes the later completeness and refinement work. The later notes supersede the older drafts’ statement that completeness remains open. I treated their theorem and certificate claims as project context, not as results independently reverified in this task.

- [August 29 draft with the MCCFR and properness analysis](https://drive.google.com/file/d/1fhneqHN5aRsWZMjK7BwnkLNot1lTJB8U/view?usp=drivesdk)
- [Earlier August 29 draft](https://drive.google.com/file/d/11rmcBatTuGYBc9Ka435b9MvPrDJDVVyi/view?usp=drivesdk)
- [October 3 project summary, titled Untitled document](https://docs.google.com/document/d/1NYot7Lx1acjIqybJ5krLGvmALAnU93fnsO38tWmNcZk/edit?usp=drivesdk)

The local three-player Kuhn implementation provides a useful starting point. The separate eight-handed strategy prototype reduces postflop play to a heads-up hand-strength game; that reduction cannot test this project’s three-party incidence mechanism.

## An exact starting point with real Hold’em cards

Use a river continuation game with these public conditions:

| Component | Specification |
|---|---|
| Players | Three, acting P1 then P2 then P3 |
| Board | 2♣ 4♦ 6♥ 8♠ T♣ |
| Each player’s possible private hands | J♠J♥, Q♠Q♥, K♠K♥, A♠A♥ |
| Joint prior | Uniform over all ordered, card-compatible assignments of those hands |
| Pot | 3 big blinds; account for 1 big blind previously contributed by each seat |
| Remaining stack | 1 big blind per player |
| Minimum opening bet | 1 big blind |
| Action convention | Check or bet with nothing to call; fold or call facing a bet |
| Utility | Net chips, no rake |

The four hand types are strictly ordered JJ < QQ < KK < AA. Each is a distinct two-card combination, so two players cannot receive the same type. There are 4 × 3 × 2 = 24 equally likely ordered deals. Relabel these four types as Kuhn’s J, Q, K and A.

With one big blind left and a one-big-blind minimum opening bet, the only positive bet is all-in. Other players may fold or call; nobody has enough chips to raise. The betting tree therefore has exactly the same 13 terminal histories as three-player Kuhn. Each player has four decision situations per private type, giving the same 48 binary behavioral coordinates. Public histories, private information, chance probabilities and terminal payoffs all correspond.

**Verification performed:** the accompanying dependency-free audit computes best-five-of-seven Hold’em ranks, generates the betting histories and checks all 24 × 13 = 312 terminal payoff triples against their Kuhn counterparts. All match exactly; all sum to zero. This establishes the game mapping, so any correctly established Kuhn result transfers to this specified continuation game, including its off-path strategies and deviation derivatives.

**Scope:** this is a deliberately restricted conditional hand distribution under the stated action convention, excluding an open-fold option when checking is available. It does not establish that those ranges arise at an equilibrium of unrestricted Hold’em, or that the continuation equilibrium extends to an equilibrium from the start of a hand. The starting model is a calibration case, not evidence that the phenomenon is typical of Hold’em.

## A practical expansion sequence

| Stage | Change | What it tests |
|---|---|---|
| 0 | Exact four-type embedding above | Reproduction of known payoffs, off-path effects and incidence calculations |
| 1 | All six combinations of each of JJ, QQ, KK and AA, giving 24 private hands per seat | Additional card compatibility constraints and ties |
| 2 | Broader 24–48-hand supports containing value hands, marginal hands and bluffs; varied boards and asymmetric range weights | Whether the effect depends on the specially constructed pocket-pair prior |
| 3 | Deeper equal stacks and several legal bet sizes, with an initially bounded raise tree | Sensitivity to the action abstraction |
| 4 | Add the turn and a real river chance transition | Sensitivity to future public information |

Stage 1 has **6,480 legal ordered deals and 84,240 terminal leaves**, as counted by the audit. Of those deals, 1,296 contain at least two equal-strength hands; this counts equal strengths whether or not those players reach showdown. There are at most 288 binary behavioral coordinates before removing impossible information sets. No equilibrium has been computed for this expanded model in this task.

For comparison, a fixed five-card board with unrestricted three-player hole cards has C(47,2) C(45,2) C(43,2) = **966,381,570** ordered private-hand assignments. Restricting the ranges first makes exact evaluation feasible without replacing cards by independent strength scores. These are state counts, not runtime benchmarks.

For Stage 2, preregister a small board panel: disconnected rainbow, paired, three-flush and connected boards. Use both symmetric ranges and asymmetric ranges. Select ranges independently of whether they produce the desired phenomenon; retain negative findings. Keep the same support when comparing nearby range weights so that disappearing types do not masquerade as an equilibrium boundary.

For Stage 3, possible opening sizes are half-pot, pot and all-in, filtered by minimum-bet and stack rules. Define raise-to amounts explicitly and initially permit at most one raise. This is an action abstraction. Compare it with a larger action set and allow best-response searches to use omitted sizes when assessing abstraction sensitivity. Keep minimum raises, all-in rules and terminal chip accounting correct. Restricting stacks and raises should be stated in every result.

## Preserve the actual private-information structure

For independently specified per-seat range weights w_i, define the joint distribution by

q(h1,h2,h3 | board) = Z^(-1) × w1(h1) w2(h2) w3(h3) × 1[all cards are compatible].

Normalize after rejecting overlapping cards. This is a chosen prior model, not an assumption that any observed continuation distribution necessarily has this form. If ranges come from a pre-river policy, derive the joint distribution from its reach probabilities and retain any additional dependence.

A policy observes only its own hole cards, public board, public betting history and public stacks. It must never see the other private hands used by the evaluator. Use full hand combinations initially; preserve public action history and perfect recall. If later bucketing becomes necessary, validate incidence against finer hand representations, including blocker distinctions. Similar showdown equity alone does not establish equivalent effects on two different opponents.

Each river experiment is a conditional continuation game with a declared prior. Its values and derivatives are conditional on that root. Converting them to per-hand effects requires the probability of reaching the root, and potentially the effects of upstream strategy changes.

## Compute candidates and verify equilibrium separately

Use tabular CFR or CFR+ as a candidate generator on the first expanded games, with multiple initializations. Use MCCFR if complete traversals become too costly. Neither convergence of a curve nor low self-play regret certifies Nash equilibrium in a three-player game. Brown and Sandholm explicitly state this limitation for their multiplayer method; the original MCCFR equilibrium guarantees concern two-player zero-sum games. [Pluribus paper](https://noambrown.github.io/papers/19-Science-Superhuman.pdf), [MCCFR paper](https://www.cs.cmu.edu/~kwaugh/publications/nips09b.pdf).

For every retained profile σ, compute each player’s **full unilateral best-response improvement**:

r_i = max over τ_i of U_i(τ_i, σ_-i) − U_i(σ),

and report r1, r2, r3, max_i r_i and NashConv = r1 + r2 + r3. Full best responses must respect information sets and allow coordinated changes to a player’s earlier and later decisions. A coordinate-gradient check alone is insufficient, especially at information sets made unreachable by that player’s own earlier actions.

Exact best responses on a finite abstraction establish its Nash residual, up to numerical arithmetic error. An approximate best-response search ordinarily supplies a lower bound on the true residual; failure to find an improvement does not certify a small residual. Rational reconstruction followed by exact payoff and best-response checks can validate selected small-game witnesses.

OpenSpiel’s `nash_conv` reports the sum and per-player improvements; its separate `exploitability` interface is limited to two-player constant-sum games. Its Universal Poker environment is a candidate for later stages, subject to verification of the chosen game configuration and build. Reusing the project’s existing exact tree and adding a card evaluator is the smaller first step. [NashConv implementation](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/python/algorithms/exploitability.py), [Universal Poker implementation](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/games/universal_poker/universal_poker.cc).

## Measure the quantity the paper is about

For each feasible unilateral direction d of player A, retain the whole derivative vector:

D_i = dU_i(σ_A + εd, σ_-A)/dε at ε = 0,

ρ_(A→X) = −D_X / D_A, when D_A ≠ 0.

Check D1 + D2 + D3 = 0 before interpreting the ratios. The two opponent shares sum to one but can be negative or exceed one; they are signed shares, not probabilities. At an exact Nash equilibrium, feasible deviations cannot give the deviator a positive first-order gain, although another player may gain.

For a single binary information-set probability x, perfect recall makes each payoff affine in x with all other probabilities fixed. Compute its derivative as U_i(x=1) − U_i(x=0), avoiding small finite-difference subtraction. If increasing x is infeasible at the baseline, use the feasible direction with the appropriate sign. For larger action sets, move probability mass between actions while maintaining the simplex constraint.

Record baseline reach, reach after the tested deviation, raw derivatives, residuals and ρ. Distinguish genuinely zero-reach information sets from low-reach ones. Exploration during training does not establish an equilibrium refinement, and positive action floors make every legally reachable information set on-path in the perturbed policy.

Do not declare a pole from a large numerical ratio. To support a simple pole along a parameterized feasible family σ(t), establish a point t* with D_A(t*) = 0, D_X(t*) ≠ 0 and a nonzero derivative of D_A with respect to t, while verifying the equilibrium or stated approximate-equilibrium condition along that family. Changing an off-path action can leave baseline payoffs unchanged while breaking another player’s deterrence condition.

When sampling, use paired evaluations, common random deals and separate training and evaluation samples. Estimate numerator and denominator jointly; if the denominator’s uncertainty includes zero, report the ratio as unresolved or use an appropriate ratio confidence set. Smaller best-response residuals alone do not bound incidence-ratio error near a zero denominator. Exact roots in a small game are stronger evidence than very large sampled ratios.

Compare unrefined candidates with explicit tremble or regularization experiments, but do not label entropy regularization or a uniform action floor “normal-form properness.” Any claim about proper equilibrium needs the relevant definition and a verified limiting argument. The binary-action equivalences discussed in the project notes also cannot simply be carried over after adding multiple bet sizes.

## The first research deliverable

Implement Stage 1 on the existing three-player tree, verify full best responses, and sweep a preregistered collection of supports and priors. Save one record per profile and deviation containing board, ranges, stack and pot rules, seed, all three utilities, all three best-response improvements, information-set reach, all three derivatives and ratio status.

The first substantive result should be either a validated witness of the mechanism beyond the four-type embedding, or a documented disappearance under particular changes. Then expand one modeling choice at a time. A defensible claim is “the mechanism survives in these specified three-player Hold’em river continuation games.” Full-game prevalence, full-game equilibria and equilibrium completeness require additional evidence.

The exact bridge is already verified. Whether the incidence effect survives the richer games remains an experiment to run.
