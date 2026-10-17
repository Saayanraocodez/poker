# holdem_incidence — deviation incidence in three-player Hold'em river games

A small, inspectable framework that carries the three-player Kuhn incidence question —
*does off-path behaviour change how a unilateral deviation's payoff effect is split between the
other two players?* — into conditional Hold'em river continuation games with real cards.

Findings: [`FINDINGS.md`](FINDINGS.md). Theory, with proofs: [`THEORY.md`](THEORY.md). Everything below
reproduces them.

## Setup

Python ≥ 3.10 with `numpy`; `matplotlib` for plots; `psutil` for the budget measurement. No other
dependencies. The two oracle implementations used by the tests are read-only and located through
`tests/_paths.py`, which can be redirected with the environment variables `KUHN3_DIR`,
`AUDIT_PATH` and `POKER_REPO`:
- `kuhn3.py` (the earlier exact Kuhn implementation);
- `holdem_bridge_audit.py` (the independent best-of-21 evaluator).

```
pip install numpy matplotlib psutil
```

## Layout

| path | what |
|---|---|
| `hinc/cards.py` | cards, best-five-of-seven evaluator (direct, from rank/suit counts), hand classes |
| `hinc/ranges.py` | seat ranges with exact weights; the **specified** product prior conditioned on card compatibility; a container for a **derived** joint table |
| `hinc/betting.py` | public betting tree from explicit rules (stacks, min bet, bet sizes, raise sizes, raise cap; no open fold) |
| `hinc/game.py` | `RiverGame`: deals, prior, strengths, split-pot payoffs, information sets `(player, own hand, public history)` with stable ids, validation |
| `hinc/strategy.py` | profiles (float or exact `Fraction`), save/load with the information-set table and game fingerprint |
| `hinc/evaluate.py` | full-enumeration reach, values, utilities, information-set reach (float and exact) |
| `hinc/bestresponse.py` | **full** unilateral best responses (information-set backward induction, coordinated earlier/later changes), residuals r_i and NashConv, brute-force validators |
| `hinc/cfr.py` | CFR, CFR+, DCFR with full traversal, seeds, declared averaging, zero-weight records, restrictions, checkpoints |
| `hinc/incidence.py` | exact derivative vectors (U(I→a) − U(I→b)), ρ, classification with declared tolerances |
| `hinc/offpath.py` | θ-sweeps, exact affine roots θ*, cross effects |
| `hinc/kuhn_bridge.py` | the map to Kuhn coordinates and Kuhn payoffs |
| `hinc/surd.py` | exact arithmetic in a real quadratic field Q(√d), so profiles with quadratic-surd probabilities are evaluated exactly by the same engine |
| `hinc/plan.py` | the declared analysis plan (thresholds, selection rule, budgets) |
| `configs/` | versioned game configurations (bridge, expanded24, control_2p, extension, `panel/`) |
| `scripts/` | experiment drivers (below) |
| `tests/` | correctness checks (unittest) |
| `results/` | everything the experiments produced (policies, checkpoints, histories, CSV/JSON records, plots) |

## Reproduce

All commands run from this directory. Seeds are fixed in `hinc/plan.py`. Re-running a training
command resumes every run from its checkpoint.

```
python -m unittest discover -s tests -v          # full checks (~15 min; HINC_FAST=1 skips the brute-force ones)
python scripts/bridge_checks.py                   # exact bridge reproduction + 24-hand counts + lifted Kuhn  -> results/bridge/
python scripts/smoke_budget.py                    # timing / memory -> results/smoke/budget.json
python scripts/preregister.py                     # freeze configs + plan (refuses to overwrite; --amend "why")
python scripts/run_training.py pilot 12           # 24-hand game: CFR+ and DCFR x 6 seeds x 30,000 iterations
python scripts/run_training.py panel 14           # sensitivity panel: DCFR x 3 seeds x 12,000 iterations
python scripts/run_training.py control 2          # two-player constant-sum control
python scripts/positive_control.py write          # exact SGS family profiles of the bridge as policies
python scripts/positive_control.py train          # DCFR on the bridge (3 seeds)
python scripts/positive_control.py sweep          # exact Kuhn c33 window sweep
python scripts/silent_p1.py train                 # OP2: restricted game, P1's opening forced to check
python scripts/silent_p1.py analyse               # OP2: deterrence search + theta sweep
python scripts/analyze_profiles.py pilot          # per-run analysis.json, infosets.csv, incidence.csv, offpath_pairs_*.csv
python scripts/analyze_profiles.py panel
python scripts/analyze_profiles.py control
python scripts/analyze_profiles.py positive_control
python scripts/pilot_contrast.py                  # the Kuhn-analogue parameter on path in the pilot
python scripts/witness_sweeps.py panel             # sweeps along every validated witness
python scripts/verify_pot15.py                    # independent exact re-check of a pot-1.5 witness
python scripts/theory_checks.py                   # computational checks of THEORY.md
python scripts/make_plots.py                      # results/plots/*.png
python scripts/run_training.py potsweep 21        # pot sweep: 24-hand game at prior contribution c in (1/2, 1)
python scripts/potsweep.py train 48000 potsweep_48k <grid config names>   # declared continuation
python scripts/analyze_profiles.py potsweep ; python scripts/analyze_profiles.py potsweep_48k ; python scripts/theory_checks.py t8
python scripts/potsweep.py certify                # 10^6 rationalisation + exact re-check of float-scan witnesses
python scripts/potsweep.py polish potsweep        # class-symmetric exact polish (Q or Q(sqrt d)) + exact scan
python scripts/potsweep.py polish potsweep_48k
python scripts/potsweep.py polish_silent 61/64    # P1-silent variant with the deterrence search
python scripts/potsweep.py summary ; python scripts/potsweep.py table ; python scripts/potsweep.py plot
python scripts/verify_potsweep.py                 # independent re-check of every stored certificate
```

Scratch runs: set `HINC_RESULTS=<dir>` to keep them out of `results/` (the project's scratch
folder is `../../work/`).

## Conventions every record states

- **Root:** a conditional river game. The board, ranges and prior are declared, and values are
  conditional on reaching this root. The prior is either *specified* (a product of seat weights
  conditioned on compatibility) or *derived* (a joint table). Only specified priors are used in
  the experiments here.
- **Payoffs:** net chips (bb) relative to the start of the hand (the Kuhn convention):
  −(prior + river contribution) + pot share. Zero-sum at every leaf; split pots shared equally.
- **Policies** see only their own hand and the public history. The evaluator sees the deal.
  Information sets are never merged by equity.
- **Equilibrium quality** is the measured r_i = max_τ U_i(τ, σ_−i) − U_i(σ) from exact full best
  responses (float64 enumeration; exact rationals where stated). CFR convergence is not assumed
  in three-player games.
- **Derivatives** are exact mass transfers U(I→a) − U(I→b), in bb per unit probability.
  ρ(A→X) = −D_X/D_A only for resolved, nonzero D_A. Raw D is always stored.

## Extending

- **Deeper stacks, bet sizes, a bounded raise tree:** set `stacks`, `bet_sizes`
  (`"<x>pot"`, `"<x>bb"`, `"allin"`), `raise_sizes` and `max_raises` in a config.
  `configs/extension_stack6_sizes.json` is an example, and `tests/test_extension.py` runs CFR,
  best responses (checked by brute force) and mass-transfer derivatives on it unchanged.
- **Not implemented:**
  - side pots, so stacks must be equal;
  - short all-in raises (only full raises are offered);
  - the turn (a public chance transition with card removal);
  - derived (upstream) priors from a solved earlier street (only the container exists).
