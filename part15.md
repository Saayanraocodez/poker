
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

**Established.**

1. Table 2's 21 values follow from one rigorous global interval fixed point. `c41 = 1` does not.
2. The P1-silent support space is fully enumerated: 3,045,358 patterns of `3^18`.
3. In a 13.1 % random sample of those, 80.2 % are **proven** to carry no equilibrium, and every
   equilibrium that does exist there — 259 certified, 114 distinct — lies in the family, with all
   of Table 3's identities holding to `1.5e-14` and the payoff set exactly the family's.
4. 39 of the 80 P1-betting branches contain **no equilibrium at all**. Every branch in which P1
   always bets card 1, and every branch in which P1 always bets card 2 with `a41` not free, is
   dead.
5. Table 3's closed forms and its three-sub-family structure are derived algebraically.

**Not established.** The family is still not proved complete.

- 41 P1-betting branches are open, all with P1 bluffing at an interior frequency.
- 86.9 % of the enumerated silent patterns have not yet been screened.
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
