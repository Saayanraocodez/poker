# Does the pole/incidence phenomenon generalize? — ISEF continuation, first results

**Headline.** It does **not** generalize by adding cards. It **does** generalize by adding
players. And the reason is exactly clause (ii) of the pole criterion — attainability — which
turns out to hinge on whether the first player goes silent.

Evidence tags: **[P]** proved, **[E]** exact computation, **[G]** grid/seed evidence,
**[1]** single-seed (§5 has since been upgraded to 108 multi-seed runs).

---

## 1. What was built, and how it was validated

| file | what | validation |
|---|---|---|
| `kuhnNp.py` | 3-player Kuhn on an N-card deck | reproduces `kuhn3p` at N=4 with **0.0** discrepancy on utilities, gradients, exploitability (reach 2.5e-16) **[E]** |
| `kuhnGen.py` | **n-player**, N-card Kuhn | reproduces `kuhnNp` for n=3 at N=4,5,6 with **0.0** on utilities, exploitability *and* reach **[E]** |
| `cfrNp.py`, `cfrGen.py` | external-sampling MCCFR for both | — |
| `poletest.py` | the local pole test, engine-agnostic | — |
| `theorem.py` | verification of the general theorem | — |
| `sweepNn.py`, `sweep6.py` | the (n,N) pole sweeps | — |
| `mechanism.py` | §5b: why P1 goes silent | — |
| `decompose.py` | §5c: exact per-opponent decomposition | identity exact to 1e-17 **[E]** |
| `properness.py` | §5d: the d_free vs d_cond dimension test | control reproduces (3,4) **[E]** |
| `certify.py` | §5e: Newton on the indifference system | recovers 1.8e-16 from 3e-2 noise **[E]** |

The betting rule generalizes cleanly: players act in order; once anyone bets, every other
player answers fold/call in order, wrapping. That gives

> leaves per deal = **n·2ⁿ⁻¹ + 1** (13, 33, 81 for n = 3, 4, 5) — confirmed exactly
> situations per player = **2ⁿ⁻¹** (4, 8, 16) — confirmed exactly
> parameters = n·N·2ⁿ⁻¹

Enumeration is never the bottleneck: (n,N) = (5,7) is 2,520 deals / 204,120 leaves / 560
parameters and builds in **1.35 s**.

---

## 2. The general theorem

Let G be a finite n-player constant-sum extensive game with binary information sets,
parameterized by p ∈ [0,1]^M (one coordinate per set = probability of the aggressive action).

**P1 (multilinearity).** Each `u_i` is affine in every single coordinate.
*Verified:* max second difference **1.1e-15 → 1.1e-14** across (n,N) = (3,4)…(5,6). **[E]**

**P2 (constant sum).** `Σᵢ uᵢ` is constant on all of [0,1]^M, so `Σᵢ ∂uᵢ/∂y = 0` for every
coordinate — on and off equilibrium. *Verified:* max |Σ du| **1.1e-15 → 2.1e-14**. **[E]**

**P3 (incidence is an (n−2)-simplex).** For a deviation `y` of player A with `∂u_A/∂y ≠ 0`,
define the shares `s_k = (∂u_k/∂y)/(−∂u_A/∂y)` for `k ≠ A`. Then **`Σ_{k≠A} s_k = 1`**.
*Verified:* max |Σs − 1| **2.8e-13 → 8.7e-12**. **[P,E]**

> **n = 2:** the simplex is a point — `s = 1` forced. There is no incidence question.
> **n = 3:** one dimension — a single number ρ. *This is the only case where "the split" is a scalar.*
> **n ≥ 4:** (n−2) dimensions — ρ becomes a vector.

And the achievable set **saturates** that dimension:

| n | N | costly directions | affine rank of the share set | n−2 |
|---|---|---|---|---|
| 3 | 4, 5, 6 | 48, 60, 72 | **1** | 1 |
| 4 | 5, 6 | 160, 192 | **2** | 2 |
| 5 | 6 | 480 | **3** | 3 |

**[E]** — exact in every case tested, and confirmed in 24/24 independent n=4 seeds.

**T1 (Möbius).** For any other coordinate x, both `∂u_A/∂y` and `∂u_k/∂y` are affine in x, so
each share is a Möbius transform of x with a pole of order ≤ 1:

> **`s_k(x) = N′_k/D′ + R_k/(x − x*)`**, `x* = −D⁰/D′`, `R_k = N_k(x*)/D′`.

*Verified:* fit from three values of x, predict two more — max error **3.3e-15 → 8.5e-12**
across all six (n,N). **[P,E]** (The N=4 3-player special case had `N′/D′ = 1` exactly; that
happens iff the third player's mixed second derivative vanishes, and is **not** general.)

**T2 (poles sit on the equilibrium boundary).** If x is at a zero-reach information set then
`∂uᵢ/∂x = 0` for all i, so x is unconstrained by payoffs. The only equilibrium conditions on x
are the incentive constraints `∂u_A/∂y ≤ 0`, each affine in x; their intersection is a closed
interval. Hence every pole lies on the boundary of the admissible interval.
*Verified:* first derivatives at off-path coordinates are **exactly 0.00e+00** in all six
(n,N). **[P,E]**

But the *mixed second* derivatives are not — and only for the deviation that re-opens the set:

| n, N | off-path coords | max \|du/dx\| | targeted `∂²u/(∂y∂x)` | random y |
|---|---|---|---|---|
| 3,4 | 3 | 0.00e+00 | **0.4129** | 0.1781 |
| 3,5 | 3 | 0.00e+00 | **0.3003** | 0 |
| 4,5 | 7 | 0.00e+00 | **0.2461** | 0.2461 |
| 5,6 | 15 | 0.00e+00 | **0.1182** | 0 |

**T3 (residue).** At `x*`, `∂u_A/∂y = 0`, so by P2 the deviation is costless for A and purely
redistributive among the others: **R is the costless-transfer vector divided by D′.** For n=3
that collapses to the scalar `t/D′` proved earlier. **[P]**

**The three hypotheses are game-specific**, and testing them is the empirical work:
(i) `D′ ≠ 0`, (ii) `x*` attainable, (iii) `N_k(x*) ≠ 0`.

---

## 3. Adding cards kills it

MCCFR, **50 seeds** at N=5 (1.5M iterations each), plus 10 control seeds at N=4.

| | N = 4 (10 seeds) | N = 5 (50 seeds) |
|---|---|---|
| median exploitability | 0.00105 | 0.00342 |
| off-path sets | vary by seed | **`b5_3, b5_4` in 50/50** |
| (x,y) pairs where x moves an incentive | 111 | 100 |
| root attainable in [0,1] | 86 | **0** |
| genuine poles | **86** | **0** |
| root range | median 0.78 | **1.216 – 2.966** |

At N=5 the closest any root comes to the admissible interval is **0.216 outside**. Clause (ii)
fails, uniformly, in every one of 50 independent approximate equilibria. **[G]**

**Why.** At N=4, P1 never bets, which sends P2's and P3's bet-response sets off-path
family-wide. From N=5 on, **P1 value-bets the top card ~80%** (0.825, 0.799 at N=5, 6), so
those sets are reached (reach 5.8e-2, 4.7e-2, 1.1e-2 at N=5). The only surviving off-path
sets are `b_N_3, b_N_4` — P2 self-excluding by always betting the top card — and P2 strictly
prefers that bet at *every* admissible value (`du₂/db5_1` runs +0.154 → +0.033, floor ≈ 2κ).

---

## 4. Adding players restores it

MCCFR, **24 seeds** at (n,N) = (4,5), 400k iterations each, 212 s.

| | value |
|---|---|
| median exploitability | 0.00257 (max 0.00367) |
| off-path sets per seed | median **39** |
| (x,y) pairs where x moves an incentive | 978 |
| root attainable in [0,1] | **619** |
| genuine poles | **619** |
| seeds with ≥1 pole | **24 / 24** |
| pole roots | 0.036 – 0.9997, **median 0.639** |
| numerators | min 1.7e-4, median 0.0207 |
| affine rank of share set | **2 in 24/24 seeds** |

Roots sit deep inside [0,1], not marginally — unlikely to be artifacts of 2.6e-3 exploitability.
The most common pole pairs are `x = b5[B]` and `x = c5[BF]` (opponents' responses to a bet by
P1) driving `y = a1[-] … a4[-]` (P1's own opening) — **structurally identical to the N=4,
n=3 mechanism.** **[G]**

---

## 5. The unifying variable: P1's silence, and N = n+1

**122 MCCFR runs across all eight (n, N) configurations, n = 3–6 — the 2×4 grid is complete.** This was the weakest claim in the first
pass (single-seed); it is now the strongest. **[G]**

| n | N | N = n+1 | seeds | median expl | **P1 max opening** | off-path | rank | pairs | attainable | **POLES** | seeds w/ pole |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 4 | **YES** | 20 | 0.00157 | **0.011** | 6 | 1 | 251 | 175 | **175** | 18/20 |
| 3 | 5 | no | 20 | 0.00348 | 0.828 | 2 | 1 | 40 | 0 | **0** | 0/20 |
| 4 | 5 | **YES** | 20 | 0.00264 | **0.010** | 34 | 2 | 756 | 468 | **468** | 20/20 |
| 4 | 6 | no | 20 | 0.00284 | 0.850 | 14 | 2 | 288 | 22 | 22 | 15/20 |
| 5 | 6 | **YES** | 20 | 0.00313 | **0.024** | 94 | 3 | 393 | 213 | **213** | 15/20 |
| 5 | 7 | no | 8 | 0.00448 | 0.826 | 52 | 3 | 350 | 2 | 2 | 2/8 |
| 6 | 7 | **YES** | 8 | 0.00365 | **0.014** | 420 | 4 | 103 | 44 | **44** | 7/8 |
| 6 | 8 | no | 6 | 0.00457 | 0.764 | 130 | 4 | 107 | 1 | 1 | 1/6 |

**The separation on P1's opening probability is total and has no overlap:**

> **0.010 – 0.024 when N = n+1**, versus **0.764 – 0.850 when N > n+1.**

Four values of n, and n = 6 lands at **0.014** — squarely in the silent band.

Give the deck a single card more than the minimum and P1 switches from silence to value-betting
the top card ~83% of the time. Nothing in between, across three values of n.

**And attainability tracks it just as cleanly** — the fraction of roots landing inside [0,1]:

| | n=3 | n=4 | n=5 | n=6 |
|---|---|---|---|---|
| **N = n+1** | **70 %** | **62 %** | **54 %** | **43 %** |
| N > n+1 | **0 %** | 8 % | 1 % | **1 %** |

The attainable fraction declines steadily with n (70 → 62 → 54 → 43 %) while staying an order
of magnitude above the N > n+1 controls — the mechanism weakens as players are added but does
not switch off.

**Correction to the first pass.** The single-seed scan reported (5,6) with 0 poles and (4,6)
with 2, which looked like counterexamples. Both were under-convergence: at 20 seeds, (5,6)
gives **213 poles in 15/20 seeds** and (4,6) gives only 22 with **8 %** of roots attainable.
The hypothesis stands.

**One honest nuance:** N > n+1 does not give *exactly* zero. (3,5) is a clean 0/20, but (4,6)
and (5,7) leak a few poles (8 % and 1 % of roots attainable). So the claim is a sharp
quantitative separation, not an absolute dichotomy.

**Affine rank = n−2 confirmed at scale:** rank 1 in all 40 n=3 seeds, rank 2 in all 40 n=4
seeds, rank 3 in all 28 n=5 seeds, **rank 4 in all 8 n=6 seeds**. **[G]**

**Seat asymmetry across all six configurations** (mean over seeds) — the first player is worst
and the last is best in every single one:

| n, N | seat utilities |
|---|---|
| 3, 4 | P1 −0.02832, P2 −0.02021, **P3 +0.04853** |
| 3, 5 | P1 −0.03509, P2 −0.00145, **P3 +0.03653** |
| 4, 5 | P1 −0.01406, P2 −0.01397, P3 −0.00840, **P4 +0.03643** |
| 4, 6 | P1 −0.03184, P2 −0.01022, P3 +0.00769, **P4 +0.03437** |
| 5, 6 | P1 −0.00908, P2 −0.00907, P3 −0.00770, P4 −0.00388, **P5 +0.02973** |
| 5, 7 | P1 −0.02954, P2 −0.01483, P3 −0.00095, P4 +0.01254, **P5 +0.03278** |
| 6, 7 | P1 −0.00604, P2 −0.00619, P3 −0.00619, P4 −0.00494, P5 −0.00181, **P6 +0.02517** |
| 6, 8 | P1 −0.02681, P2 −0.01579, P3 −0.00658, P4 +0.00343, P5 +0.01480, **P6 +0.03096** |

Note the minimal deck *compresses* the spread (n=5, N=6: −0.009 → +0.030) while an extra card
widens it (n=5, N=7: −0.030 → +0.033) — P1's silence is worth roughly 0.02 chips to P1.


---

## 5b. Why does P1 go silent? The incentive flips sign — but not for the reason I guessed

36 MCCFR runs, 6 seeds per configuration. **[G]**

| n | N | N = n+1 | P1 opens the TOP card | P(someone bets \| P1 checks) | **du₁/d(open top)** |
|---|---|---|---|---|---|
| 3 | 4 | **YES** | **0.0154** | 0.5114 | **−0.00902** |
| 3 | 5 | no | 0.8306 | 0.5841 | **+0.00099** |
| 4 | 5 | **YES** | **0.0169** | 0.4514 | **−0.01022** |
| 4 | 6 | no | 0.8390 | 0.6531 | **+0.00120** |
| 5 | 6 | **YES** | **0.0237** | 0.4424 | **−0.00711** |
| 5 | 7 | no | 0.8308 | 0.7009 | **+0.00208** |

**The result: P1's incentive to bet the best card flips sign exactly at the threshold.**
Strictly negative (−0.007 to −0.010) when N = n+1, strictly positive (+0.001 to +0.002) with
one extra card. Not a correlate — this is the derivative that directly governs the behaviour,
and its sign change *is* why the off-path region appears and disappears.

**The hypothesis I set out to test was wrong, in the informative direction.** I predicted
slow-playing: P1 checks the nuts because somebody else is likely to bet behind. That predicts
`P(someone bets)` should be **higher** at N = n+1. It is **lower** — 0.44–0.51 versus
0.58–0.70 — and the correlation with P1's opening frequency is **+0.91** across configurations
(+0.88 across all 36 individual seeds), i.e. P1 bets the top card *more* when others are
*more* likely to bet behind. That is the opposite of the slow-play story.

The likely reading is that `P(someone bets | P1 checks)` is **downstream, not causal**: when
P1 bets the top card 83 % of the time, a check from P1 signals weakness, so the others correctly
respond by betting more often behind. The correlation is an equilibrium consequence of P1's
strategy rather than a cause of it. **[?]** — this reading is not itself tested.

**So the mechanism chain is established at its last link and open at the first:**

> N = n+1 → **[open]** → `du₁/d(open top) < 0` → P1 silent → opponents' bet-response sets go
> off-path family-wide → deterrence windows with attainable boundaries → poles.

Everything from the sign of the derivative rightward is measured. Why the *deck size* controls
that sign is the next question, and the natural test is to decompose `du₁/d(open top)` into its
fold-equity and showdown components and see which one crosses zero.


---

## 5c. Where the sign flip lives: an exact decomposition

**An exact identity.** Holding the best card, P1 never loses a showdown and never folds, so on
those deals P1's payoff is the pot minus P1's own stake — that is, **exactly the sum of the
opponents' contributions**. Every opponent puts in the ante plus at most one more chip, so

> **du₁/d(open top) = Σ_{j≠1} Δ_j**,  where
> **Δ_j = P(j puts in a 2nd chip | P1 bets) − P(j puts in a 2nd chip | P1 checks)**

`Δ_j > 0` means betting extracts more from opponent j; `Δ_j < 0` means checking extracts more
(slow-play works on that opponent). **[P]**

*Verified:* forcing P1 to never fold the best card makes the identity exact —
**2.6e-17 / 4.0e-18 / 7.5e-17** at (3,4) / (4,5) / (5,6). On raw CFR output it holds to
5.6e-05, the gap being entirely CFR's residual folding probability at a barely-reached set.
**[E]**

**The discriminator is the *later* opponents' term.** 36 runs, 6 seeds per configuration:

| n | N | N = n+1 | next player (P2) | **all later players** | total |
|---|---|---|---|---|---|
| 3 | 4 | **YES** | −0.01008 | **+0.00106** | −0.00902 |
| 4 | 5 | **YES** | +0.00068 | **−0.01090** | −0.01022 |
| 5 | 6 | **YES** | +0.00233 | **−0.00944** | −0.00712 |
| 3 | 5 | no | −0.01135 | **+0.01234** | +0.00099 |
| 4 | 6 | no | −0.01489 | **+0.01608** | +0.00120 |
| 5 | 7 | no | −0.00942 | **+0.01149** | +0.00208 |

**The later-players term separates with no overlap:** `[−0.0109, +0.0011]` when N = n+1 versus
`[+0.0115, +0.0161]` when N > n+1. It is also the term that carries the total. The immediate
next player's term separates too but in the *opposite* direction (more negative when N > n+1)
and is outweighed.

So with a spare card in the deck the later opponents call P1's bet often enough to add ≈ +0.013;
with a minimal deck they do not — they fold, and P1 would have made more by checking and letting
them bet into the nuts.

**The chain is now open at one narrower link:**

> N = n+1 → **[open: why do later opponents call a bet less often when the deck is minimal?]**
> → later-players term < 0 → `du₁/d(open top) < 0` → P1 silent → opponents' bet-response sets
> go off-path family-wide → attainable deterrence boundaries → poles.

This is an exact *accounting* of where the sign flip sits, not yet a causal account of why the
later opponents behave differently. That is the remaining question.


---

## 5d. Properness beyond n=3, and why it cannot yet be settled

**The dimension test.** At (3,4) properness pinned the last free off-path parameter because a
fixed number of equal-cost conditions matched the number of free parameters. Generalise that
to a dimension count:

- **d_free** = off-path parameters that still have a non-degenerate deterrence window, after
  discarding those pinned by belief-free dominance and those that are *inert* (unreachable even
  under trembles).
- **d_cond** = rank of the Jacobian of the deviating player's cost-*differences* with respect
  to those parameters — how many independent equal-cost conditions properness supplies.

`d_cond = d_free` → at most one point; `d_cond < d_free` → a face survives; `d_cond > d_free`
→ no proper equilibrium in the component.

**Control passes.** On *exact* SGS family profiles the test returns **d_free = 2, d_cond = 2 →
at most one point** at three different family points, spanning both sub-families and both
`b₃₂` values — reproducing the known (3,4) result. **[E]**

**Indicative extension.** On CFR profiles, wherever the structure is detected at all,
`d_cond = d_free` — including **4 = 4 at (4,5)**. But it is detected in only **3 of 10 seeds**:

| (n,N) | d_free per seed |
|---|---|
| 3,4 | 0, **2** (= d_cond), 0 |
| 4,5 | 0, **4** (= d_cond), **4** (= d_cond), 0 |
| 5,6 | 0, 0, 0 |

At exploitability ≈ 3e-3 the incentive constraints are violated by about as much as the
windows are wide, so the windows collapse; the off-path count swings 2 / 13 / 7 across seeds
where the exact profile gives a stable 14. **The properness question cannot be settled without
exact equilibria.** **[?]**

## 5e. Attempting exact certification — the solver works, support identification does not

At an equilibrium every strictly interior coordinate leaves its owner indifferent,
`F_i(p) = du_owner/dp_i = 0`, a square multilinear system whose Jacobian
`d²u_owner/(dp_i dp_j)` is exact from two gradient evaluations per column.

**The formulation is right.** On the exact SGS profile, `max|F| = 2.8e-17`. **[E]**

**The solver is right.** Perturb the true profile and run damped pseudo-inverse Newton:

| noise | exploitability | max\|F\| |
|---|---|---|
| 1e-3 | 1.6e-04 → **1.9e-16** | 2.8e-04 → 4.2e-17 |
| 1e-2 | 4.7e-03 → **1.9e-16** | 4.2e-03 → 1.4e-17 |
| 3e-2 | 1.5e-02 → **1.8e-16** | 7.4e-03 → 4.2e-17 |

(Coordinate error stays at noise level: it converges to a *different* point of the same
positive-dimensional component, which is still an exact equilibrium.) **[E]**

**Support identification is the blocker.** The true (3,4) support is **14 off-path / 7
interior**. CFR-derived guesses give **2 / 13** at a 5e-3 snap threshold and **13 / 9** at
4e-2; being wrong by two coordinates makes the indifference system unsatisfiable and Newton
stalls. A greedy repair — drop the worst-violated coordinate to the pure value its derivative
points at — diverges monotonically (2.1e-3 → 2.1e-1 over nine repairs).

**UPDATE — closed at (3,4).** An 8M-iteration MCCFR run shrinks the ambiguous set from 16 to
12 coordinates, and Newton over all 2^12 = 4,096 support hypotheses certifies **40 exact
equilibria** (exploitability to 3.5e-17) in 98 s. **All 40 lie in the SGS family.** 13 deviate from Table 3 in
some coordinate, but every one of those deviations is in `c23` alone — off-path, reach 1e-29 to
exactly 0 — and **zero** deviate in an on-path coordinate. All 40 match the family's closed-form
utilities to **2.43e-16**.

An earlier pass flagged one case as deviating in on-path `b41` (reach 0.25). **That was a bug in
the checker**: it rounded the free parameters to six decimals before rebuilding, so
`b41 = 2(b11+b21)` came out ~4e-6 off and tripped a 1e-6 threshold. Unrounded it matches Table 3
to 1.11e-16. This is *corroborating* evidence for the family at (3,4), not a completeness proof —
the search only covers support hypotheses reachable from one CFR profile. **[E]**

> **What would have closed it (superseded):** a real support-identification procedure, not a better solver.
> Exhaustive enumeration over a reduced candidate set is feasible at (3,4) (2⁹ = 512 Newton
> runs at ~0.1 s each) and a linear-complementarity formulation would scale further. Until
> then, **every claim outside N = 4 rests on approximate equilibria at ~3e-3**, and §5d in
> particular is indicative only.

---

## 5f. B answered on certified equilibria: properness is specific to (3,4)

**Certification ported to (4,5).** The ambiguous set there is 43 coordinates — 2^43 hypotheses —
so exhaustive enumeration is impossible. Visiting hypotheses in order of **Hamming distance from
the CFR reading** instead certifies **29 exact equilibria** (best exploitability **1.86e-16**),
all within distance 1–2, in 782 s. **[E]**

**The dimension test on certified equilibria, all 12 examined:**

| off-path | with slack | inert | dominance-pinned | **d_free** | d_cond |
|---|---|---|---|---|---|
| 113 | 53 | 36 | 17 | **0** | 0 |

Every slack off-path parameter is either inert or pinned by belief-free dominance — 36 + 17 = 53
exactly — leaving **nothing for properness to pin**. Verified against **40 random tremble ratios
spanning three orders of magnitude**, not just the 4 hand-picked ones. **[E]**

> **Theorem 3 describes the special case, not the general one.** At (3,4) properness is needed
> because `c33` has slack that dominance does not reach. At (4,5) a weaker refinement already
> suffices, and the question does not arise.

This **corrects** the indicative reading in §5d (`d_free = d_cond = 4` at (4,5)), which was an
artifact of running the test on approximate equilibria where the deterrence windows collapse.

---

## 5g. An attempt on the last link that did NOT close it

**Hypothesis.** At N = n+1 the "facing P1's bet" sets carry ~zero reach, so their calling
frequencies are set by *deterrence* rather than by best response; deterring a P1 who holds the
best card requires calling *less*. At N > n+1 those sets are on-path and the frequencies are set
by the opponents' own best response, which calls more.

| n | N | N=n+1 | reach of bet-response sets | equilibrium call rate | myopic BR | gap |
|---|---|---|---|---|---|---|
| 3 | 4 | **YES** | **0.0108** | 0.1046 | 0.0020 | +0.1026 |
| 4 | 5 | **YES** | **0.0161** | 0.0607 | 0.0024 | +0.0583 |
| 5 | 6 | **YES** | **0.0235** | 0.0487 | 0.0023 | +0.0465 |
| 3 | 5 | no | **0.4716** | 0.2413 | 0.0646 | +0.1767 |
| 4 | 6 | no | **0.6057** | 0.1770 | 0.0543 | +0.1228 |
| 5 | 7 | no | **0.6998** | 0.1427 | 0.0471 | +0.0956 |

**Prediction 1 (reach separation) confirmed 30-40x** — 1-2% at N = n+1 against 47-70% otherwise.
**But it is close to tautological:** the reach of the bet-response sets is essentially P(P1 bets),
which is the quantity being explained. It restates the regime rather than deriving it.

**Prediction 2 (calling below best response) refuted, and the test was mis-designed.** The gap is
positive everywhere and *larger* at N > n+1 — the opposite of the prediction. The cause is the
counterfactual: forcing `a_top = 1` makes P1's betting range artificially all-nuts, so the best
response to it is fold-everything, and the comparison measures nothing useful.

> **Superseded by 5h.** What 5g established negatively: the effect is entirely in opponents' calling rate
> against a bet (§5c), it is not slow-play (§5b), it is not information sharpness (§5b), and it
> is not captured by a best-response comparison against a forced-nuts range (§5g). A correct test
> needs a counterfactual that holds P1's *equilibrium* betting range fixed while varying only the
> deck size — which is not straightforward, since that range is itself what changes.

---

## 5h. The link resolved: it is a fixed point, not a one-way cause

**A controlled counterfactual.** The confound in every earlier attempt was that P1's equilibrium
betting range differs between regimes. Remove it by defining every strategy by **card rank**
rather than card index, so the *identical* strategy instantiates at any deck size. Hold P1's
range fixed and polarised -- bet the best card always, bluff the worst at a fixed rate -- and ask
one question: facing an identical range, does an opponent's best response call more as N grows?

| n | N = n+1 | n+2 | n+3 | n+4 | n+5 |
|---|---|---|---|---|---|
| 3 | 0.2500 | 0.2000 | 0.1667 | 0.2857 | 0.2500 |
| 4 | 0.2000 | 0.1667 | 0.2857 | 0.2500 | 0.2222 |

**Flat.** No trend, and no separation at N = n+1. Robust across 9 reference settings (bluff rate
0.15/0.33/0.60 x call breadth 0.3/0.5/0.7): slopes in N run **-0.031 to +0.071**, mixed sign.
Against an *equilibrium* call rate that jumps 2-3x with a sharp boundary (0.049-0.105 at N = n+1
versus 0.143-0.241 otherwise). **[E]**

> **So deck size does not drive calling directly. The equilibrium difference is a selection
> effect** -- and that reframes the whole question.

**The resolution.** There is no one-way causal chain to find. P1 is silent *because* opponents
call little; opponents call little *because* their bet-response sets are off-path (P1 is silent)
and therefore constrained only by deterrence. The two conditions are simultaneous, and the deck
size selects which self-consistent pair exists -- it does not shift any single best-response
function. That is why three separate attempts to find "the cause" failed: they were looking for
a one-way mechanism inside a simultaneity.

The chain in section 5b should therefore be read as a **fixed-point condition**, not an arrow:

```
   N = n+1  selects the equilibrium in which
        P1 silent  <-->  bet-response sets off-path  <-->  calling constrained only by deterrence
   which yields  du1/d(open top) < 0,  consistent with P1's silence.
```

---

## 5i. Looking for equilibria outside the family

SGS leave open whether their family contains every equilibrium. Four attacks, in increasing
order of what they establish.

**1. Broad random-restart Newton — failed, and proves nothing.** 50,400 restarts from random
0/1/interior support patterns (half of them forcing P1's opening to be interior) found **zero**
exact equilibria — including zero *family* members, which is the tell. Diagnosis: with the
correct support and random starting values Newton recovers an equilibrium **5 times in 20**;
with random supports it hits **0 in 2,000**. The obstacle is the support space, not the solver:
a random pattern over 48 coordinates essentially never matches a real equilibrium support.
**This search is uninformative, not negative.** **[X]**

**2. Is P1's bet dominated? No.** Maximising `du1/da_j1` over *all* opponent strategies by
coordinate ascent with 400 restarts:

| P1 bets card | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| max gain | **+1.000** | **+1.166** | **+1.206** | **+1.250** |

Against sufficiently loose opponents P1 gains up to **+1.25** by betting — thirty times κ.
So nothing structural forbids an equilibrium in which P1 bets, and the family's `a_j1 = 0` is
not forced by dominance. **[E]**

**3. CFR from a pro-betting start still collapses to silence.** Initialising P1's opening
regrets at +5000 so the solver begins by betting constantly:

| iterations | P1 max opening | exploitability |
|---|---|---|
| 400 k | 0.576 | 0.0406 |
| 2 M | 0.148 | 0.0079 |
| 8 M | **0.039** | **0.0020** |

The early rows are under-convergence, not a discovery — an exploitability of 0.04 is about κ.
Given enough iterations the profile returns to P1-silent from even an adversarial start. **[G]**

**4. Support enumeration near a solver profile** certified 40 exact equilibria, **all in the
family** (§5e).

> **Verdict: no counterexample found, and no proof of completeness.** The evidence corroborates
> SGS — 40 certified equilibria all inside, and CFR returning to the family from a hostile
> start — but the systematic search was local and P1's bet is not dominated, so an equilibrium
> with P1 betting is not ruled out. Settling it needs a complementarity or pruned-enumeration
> method over supports, which is beyond what is built here.

---

## 6. Honest limits

1. **Everything is approximate.** Exploitability medians 1.1e-3 (N=4), 3.4e-3 (N=5), 2.6e-3
   (n=4). No exact certification of any N≥5 or n≥4 equilibrium was achieved. The N=5 negative
   result is robust because the roots miss by 0.216–1.97, far outside the error; the n=4
   positive result is robust because roots sit at median 0.639.
2. **No closed-form family for N > 4 or n > 3.** All results are local tests at sampled
   equilibria, not statements about the whole equilibrium component.
3. **§5 is now 108 runs, but N > n+1 is not exactly pole-free.** (3,5) gives a clean 0/20;
   (4,6) and (5,7) leak a few (8 % and 1 % of roots attainable versus 54–70 % at N = n+1).
   The claim is a sharp quantitative separation, not an absolute dichotomy. (5,7) has only
   8 seeds.
4. **Snapping.** The local test rounds near-pure probabilities to exactly 0/1 to expose
   off-path structure. Exploitability barely moves (0.00105 → 0.00107 at N=4; 0.00342 →
   0.00323 at N=5), but it is a step that deserves a sensitivity check.
5. The n=4 "39 off-path sets per seed" is post-snapping; some are likely snapping artifacts.

---

## 7. What this gives the ISEF project

The original framing — "does it generalize to bigger games?" — would have produced a yes/no.
What actually emerged is better:

> **The mechanism is generic given attainability (proved from multilinearity and constant-sum
> alone, for all n and N). Attainability is not a formality: it fails uniformly at N=5 for
> n=3, and holds in 24/24 seeds at n=4. What decides it is whether the first player is silent,
> which tracks how close the deck is to minimal.**

That is a theorem plus a sharp, falsifiable empirical hypothesis — considerably stronger than
running the same code on a bigger game. Two further results fall out for free:

- **ρ is a scalar only at n = 3.** For n ≥ 4 incidence is a vector on an (n−2)-simplex, and
  the achievable set has full dimension (rank 1, 2, 3 at n = 3, 4, 5). This reframes the whole
  question — the original paper's ρ is the lowest non-trivial case of a general object.
- **Positional advantage persists and sharpens.** At n=4, N=5 the seat utilities are
  P1 −0.01412, P2 −0.01396, P3 −0.00847, **P4 +0.03656** (± ≤ 0.0018 over 24 seeds). Acting
  last is worth roughly 0.05 chips/hand over acting first, as at n=3.

### Next steps, in order of value

1. ~~Multi-seed (5,6)/(4,6)~~, ~~(6,7)~~, ~~(6,8)~~ — **all done**; the 2x4 grid is complete
   and the separation holds at every one of the four values of n.
2. **Push exploitability down** (CFR+ or a vectorized full-tree CFR) so the local tests run at
   1e-6 rather than 1e-3.
3. **Certify one equilibrium exactly** at (4,5) — the case where poles are abundant — via
   support-guess + exact rational solve.
4. **Look for the n≥4 residue structure**: with a vector residue, is there an analogue of
   `R = t/D′`? T3 says yes in principle; it has not been computed.
