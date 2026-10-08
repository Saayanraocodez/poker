# 2026-10-07 20:10: (3,5) open questions, partly answered (MASTER_DATA §16.11.2–3)

- **How many betting equilibria:** continua, with different payoffs. All three are certified with
  `k35/cert35seg.py` and `k35/cert35gen.py`; the latter takes `name=p/q` for off-path fixes and
  `name:=p/q` for free parameters, and `k35/degen35.py` finds the degeneracies.
  - I: segment c11 in [0, 29/50].
  - III: a branch, certified at b11 = 27/200.
  - II: isolated, only card 1 bluffs; P2's payoff is +0.0016 versus −0.0013 on I.
  - II's mirror is NOT an equilibrium.
  - Inputs: `q2_polish35.py` → `q2_polish35.json`; `q2_polish35_plus.json` adds the mirror.
- **P1-silent:** none found. `silent35.py` (restricted MCCFR) + `silent35b.py` (check-subgame
  polish + deterrence via `silent35_deter.py`): 7 check-subgame equilibria, deterrence impossible
  with margin +0.0263. This is evidence only.
- **RUNNING:** `k35/enumc7.py` on the silent cell `a11:0,...,a51:0` (22 workers, tag `k5c7_silentN`,
  log `k35/log_enumc7_k5c7_silentN.txt`), started from a tool call, so it dies if the app closes.
  It is resumable: rerun the same command. If it closes with 0 leaves, port the 5-card checker
  (`checkcert` / `certleaf` / `xcheck` / `checkenum2` at 60 coordinates, plus an INDEPENDENT check of
  `D_all5.pkl`). That would prove no P1-silent equilibrium.

# 2026-10-07: (3,5) HAS an exact equilibrium with P1 BETTING (certified)

`polish35.py`: MCCFR at 20 seeds x 10^7, then Newton + support repair. 7 seeds reach one
equilibrium with P1 opening cards 1,2 at 0.1615, card 3 at 0.0404, card 5 at 0.8478. The (c11, c21)
split is free.

- `k35/hiprec35.py` + the 400-digit runs: `b11 = (11 + √13)/72`, `c32 = 4 − √13`; the rest is
  degree > 8.
- `k35/cert35.py`: exact Krawczyk on a 14x14 reduction justified by polynomial identities, plus
  the D-conditions on all 60 coordinates. CERTIFIED.
- `k35/cert35check.py`: independent, no sympy. CONFIRMED.
- Negative controls (shifted box, flipped `a42`) are rejected.
- `k35/xeq35.py`: exact Nash verifier, positive and negative controls on the 4-card witness.
- Equilibrium: `k35/cert35_equilibrium.txt`. MASTER_DATA §16.11.1; PAPER_KIT contribution 14 and
  open problem 3.
- Not done: whether (3,5) also has P1-silent equilibria, and how many betting equilibria it has.
  Nothing is committed since 84dbfcf.

# 2026-10-06 21:00: (3,5) with exact propagation: faithful, but out of reach exhaustively

The `k35/` ports (`xprop.py`, `enumc7.py`, `test_xprop_port.py`) pass:
- regression at 4 cards, bit for bit;
- the structure checks at 5 cards;
- 60/60 float kills reproduced.

The 49 timed-out cells are still out of reach. The 90-min A/B of layer ladders (`ab_k5.py`, logs
`log_enumc7_k5ab_*`) left every arm open with a growing frontier. Extrapolated, that is ~3.6M
nodes and about two months for the probed cell (MASTER_DATA §16.11). The checker port
(`checkcert`/`certleaf`/`xcheck`/`checkenum2` at 60 coordinates, plus an INDEPENDENT check of
`D_all5.pkl`; `makeD.py` used the `checkD` recursion itself) was NOT done; only do it if
something closes cells.

Proposed next step (not started): regenerate the (3,5) MCCFR runs (`cfrGen.py`; Part 9 has P1
opening up to 0.83) and try to polish them into EXACT rational equilibria with P1 betting. One
success would settle open problem 3 for (3,5) positively.

# 2026-10-05 22:30: ALL 77 BETTING BRANCHES VERIFIED END TO END, no float arithmetic anywhere

`enumc7` + `checkenum2` closed the six branches the grind could not: 26,223 nodes, 461 support
leaves all `EMPTY_BOX`, 0 failed, 0 missing, 2.3 h enum + 10 min check. Per-branch table in
MASTER_DATA §16.9.1; `enumc7_summary_nash.txt`.

- `enumc_summary_nash.txt` now has 77 OK lines; the six are tagged `[enumc7]`, and the replaced
  PARTIAL lines are in the history.
- PAPER_KIT updated: contribution 2, the Theorem 4 proof note, and "what the proof trusts"
  (item (ii) removed for every branch).
- **Cross-check DONE (10-06 00:00):** `enumc7` + `checkenum2` on all 77 betting branches gives
  77/77 OK, 33,104 nodes, 462 leaves all `EMPTY_BOX`, 0 failed. Every betting branch is closed
  by two independent certified methods (MASTER_DATA §16.9.1). Nothing is running except
  keep-awake, which can be stopped with `schtasks /end /tn PokerKeepAwake`.
- **The `enumc6` grind is retired** (`PokerRetryPartial` would find nothing to do). Its outputs
  `enumc_c_*N.jsonl.gz` (~6.5 GB) are superseded partial trees, kept unless the user wants them
  deleted.

# 2026-10-05 20:00: OPTION 2 built and controlled; the six branches running under `enumc7`

The user reopened option 2 on condition of exact arithmetic and credibility. The method:

- **Prover (`xprop.py` + `enumc7.py`):** the float enumeration's propagation (`bnb6` +
  `treesize6`), but EXACT (Fractions; chord endpoints rounded outward to 2^-60). It records a
  certificate for every narrowing or kill. Every node record carries its labels, exact box and
  that certificate. Layer kills are `certbox` certificates from the exact box.
- **Independent checker (`xcheck.py` + `checkenum2.py`):** imports only `tree.py`; nothing from
  ivl/bnb6/treesize6/xprop. It replays each node from its parent's record, in parallel.
- **Soundness lemmas and controls:** MASTER_DATA §16.9.1. Agreement 417/417; oracle-confirmed
  tampering 2,463/2,463 rejected; 64/64 certified equilibria survive the exact tree; the silent
  branch reproduces the R ledger's 12 FAMILY leaves identically (4,723 nodes, OK).
- **The six branches:** `PokerEnumc7` task = `run_enumc7.py 20 branches_enumc7.txt`, ledger
  `enumc7_summary_nash.txt`. Each output is checked by `checkenum2` as it finishes.
  `a11:0,a21:MIX,a31:MIX,a41:1`: 97 nodes, 126 s, **OK**. The grind on that branch had made
  156k kills per 8 h slice without finishing.
- **The `enumc6` grind is PAUSED, not deleted.** It resumes with `schtasks /run /tn
  PokerRetryPartial`. Retire it once all six are verified under `enumc7`.

# 2026-10-05: round 1 complete, none finished; user decision: keep grinding, no float trust

Round 1 slice results (the last slice of each):

| branch | kills | float-unsure | queue at end | trend |
|---|---|---|---|---|
| `M_M_0_M` | 1.32M | 350k | 32.5k | growing |
| `0_M_0_M` | 781k | 349k | 14.5k | growing ~1,800/h (fresh, corrected policy) |
| `M_0_0_M` | 585k | 251k | 19k | growing |
| `0_0_M_0` | 402k | 187k | 3.9k | growing slowly |
| `M_M_0_1` | 483k | 218k | 4.4k | flat |
| `0_M_M_1` | 156k | 40k | 2.1k | flat |

The uncertifiable regime dominates the cost: on `0_M_0_M`, 478k s went to `fdeadu` checks against
91k s for layer checks.

**Decision (user):** keep all six rotating under `enumc6`. No step may trust float arithmetic, so
the checker will NOT replay the float propagation. Speed-ups must come from exact means only.
Round 2 started 10-05 12:20 with `M_M_0_M`.

# 2026-10-04 20:20: restarted after 2.9 days asleep

Task Scheduler's default 72 h `ExecutionTimeLimit` killed `PokerKeepAwake` at 10/01 20:40. The box
idle-slept at 23:30 and stayed asleep until the user woke it at 10/04 20:18. Nothing on disk was
lost (all outputs checkpointed). Both tasks are now `PT0S` and were restarted.

Round 1 so far, one `enumc6` slice each, none finished:

| branch | kills | float-unsure | queue at end |
|---|---|---|---|
| `M_M_0_M` | 1,316k | 350k | 32.5k |
| `M_M_0_1` | 483k | 218k | ~4.4k (flat for the last 3 h) |
| `0_M_M_1` | 156k | 40k | ~2.1k (flat) |
| `M_0_0_M` | 585k | 251k | 19k |

`M_0_0_M`'s slice was cut off by the restart, so it has no ledger line; it is checkpointed and
retried as "missing". Now running `0_0_M_0`, migrated from the 9/29 `enumc3` leftovers: 22,997
records, 95 ancestors matched, 80 unfinished nodes. Then `0_M_0_M` (fresh), then round 2.
Order: `retry_order.txt`.

# 2026-09-30 13:30: the six PARTIAL branches grind under `enumc6` (resumable), round-robin 8 h slices

The user picked "keep grinding, made resumable" (option 1) over replaying the float tree in the
checker. At 8 h both `enumc5` branches still had growing queues (~+1,700 jobs/h, linear): `0_M_0_M`
reached kill 688k, float-unsure 293k (its output was DELETED by the cap at 04:52, since the old
retry deleted capped output). `M_M_0_M` reached 590k kills; it was detached from its cap at 12:32
and salvaged.

- **`enumc6.py`** = `enumc5` workers plus a durable driver. The output is a chain of complete gzip
  members. Every `KUHN_CKPT` s the member is sealed and fsynced, and only then is the offset written
  atomically to `enumc_<tag>.ckpt`. RESUME replays the float propagation down the ancestors of the
  unfinished nodes (children of splits with no record), checking each against its stored split
  record, with work-shared pool replay. A file without a `.ckpt` is migrated (complete records
  rewritten; original kept as `.premigrate`).
- **Controls:**
  - `control_resume.py` (kills in the top expansion and mid-pool, junk past the checkpoint,
    forced migration, a kill between the migration's renames): resumed trees replay OK in
    `checkenum`, with no duplicate ids.
  - `control_replay.py`: serial and parallel replay give bit-identical states.
  - Real run: branch 2's 1.25 GB `enumc5` file migrated to 900,911 records, and 19,429 ancestors
    were replayed and matched.
- **`checkenum.py`** now checks certificates in bounded batches while reading
  (`KUHN_CHECK_BATCH`, default 20,000). Holding every certificate would need tens of GB for these
  trees. Regression: a verified branch re-checks to its ledger numbers exactly, and swapped
  certificates in a middle batch are still caught.
- **`retry_partial.py`** for `enumc6`:
  - round-robin until every branch is verified; a capped slice keeps its output;
  - one current ledger line per branch;
  - finished means rc 0 AND a `.ckpt` that says complete, anything else is an ERROR line (never a
    check of a partial file);
  - order from `retry_order.txt`; `run_retry.env` is re-read per slice (from the next driver start).
- **A/B of the layer test (`ab_layer.py`):** `enumc5`'s cheap layer test was WRONG. It was run
  on the verified branch `a11:MIX,a21:MIX,a31:MIX,a41:1` with 4 workers per arm:
  - full ladder: done in 1,440 s, 30,983 nodes, 0 float-unsure, `checkenum` OK. All 9,439 layer
    tests killed their node.
  - rung 0 only: not done at 7,200 s, 53k+ nodes, 1,303 float-unsure. The 1,373 layer nodes it
    failed to kill are where the uncertifiable subtrees start.

  2026-10-01: the layer test below an uncertifiable node is now SKIPPED (`KUHN_RUNGS_LAYERU=none`;
  use the token, because an empty env value can be dropped on Windows). It made 0 kills in 90,956
  calls on M_M_0_M and M_M_0_1 and wasted 68,493 s in one slice. Effective from the 07:44 slice.
  M_M_0_1 under the corrected policy:
  - at 2,311 s: 2,543/2,524 top subtrees done, 48,754 kills;
  - then still into the uncertifiable regime: 23,458 float-unsure at 7,014 s, seeded by 51
    float-dead children that the full ladder could not certify;
  - its full-ladder layer failures cost ~152 s each (37,000 s in 2 h).

  Policy since 15:44 (`run_retry.env`): layer test and float-dead children use the full ladder.
  Below an uncertifiable node, a new `layeru` context plus `fdeadu`, both rung 0 (the full ladder
  essentially never succeeds there). Branch 2 resumed under it: 1,015,120 records, 20,079
  unfinished nodes, 23,110 ancestors replayed and matched in 392 s.
- On a power loss: `schtasks /run /tn PokerKeepAwake`, then `schtasks /run /tn PokerRetryPartial`.
  It resumes; nothing is lost past the last checkpoint.

# 2026-09-29 20:52: the six PARTIAL branches now run under `enumc5`

`enumc3` (inherited certified boxes) and `enumc4` were dead ends on these branches. `enumc3` made
30-60x fewer kills per hour than `enumc2`. `enumc4` had 16,092 float-unsure nodes after 23.5 h with
a growing queue. Both were stopped. The 3 `enumc3` PARTIAL lines are in `enumc_partial_history.txt`,
and the retry log says where `0_0_M_0` was when it was stopped.

**Where enumc2's time actually goes** (`probe_knuth.py`: Knuth-weighted random walks that follow
`enumc2.subtree` exactly, including descent into uncertifiable children; `probe_knuth_sum.py`).
Across the six branches:

| context | est. ladder time | in failures | saved by rung 0 only | kills lost |
|---|---|---|---|---|
| layer test (depth % 4) | 5,323 s | 5,008 s | 5,006 s | 2 |
| layer test below an uncertifiable node | 26,064 s | 26,064 s | 25,800 s | 0 |
| float-dead child | 1,110 s | 984 s | 1,049 s | 20 |
| float-dead child below an uncertifiable node | 127,720 s | 89,405 s | 126,190 s | 1,465 |

The layer test ran the full ladder (1 LP, 1 chord, 20 LP, 40 chord nodes) on nodes that are
alive: 61-129 s per failure, and nearly all its kills come at rung 0. Below an uncertifiable node,
the float declares every child dead, so every child paid about 35 s. That is the straggler
regime: the first `enumc2` runs finished ~99 % of their subtrees in an hour, then sat on 10-40
jobs until the cap.

**`enumc5.py`** = `enumc2` with per-context rungs (`KUHN_RUNGS_LAYER=0`, `KUHN_RUNGS_FDEAD=0,1,2,3`,
`KUHN_RUNGS_FDEADU=0`) and time-based hand-back (`KUHN_JOBSECS=300`). The progress lines carry
per-context ladder stats. The output format is unchanged. Test on `a11:MIX,a21:1,a31:MIX,a41:0`:
the same 3,188-node tree as `enumc2`, `checkenum` OK, 192 s vs 290 s.

**Running:** task `PokerRetryPartial` = `retry_partial.py 1 26 28800 enumc5.py`, settings in
`run_retry.env`. It retries all six in order `0_M_0_M`, `M_M_0_M`, `M_0_0_M`, `0_0_M_0`,
`M_M_0_1`, `0_M_M_1`, 8 h cap each. It now retries every branch that is PARTIAL by another script
or absent from the ledger, and keeps a PARTIAL line tagged with its own script (so a restart after
a power loss resumes correctly). Ledger lines are tagged `[enumc5]`. On a power loss, just
`schtasks /run /tn PokerKeepAwake` and `schtasks /run /tn PokerRetryPartial`.

# RESTARTED 2026-09-28 20:40 after a power loss (2026-09-26 ~21:00)

Both runs died with the box; neither resumes mid-branch, so each restarts its current branch.
- **`PokerRetryPartial`** (`retry_partial.py 1 20 28800 enumc3.py 2`): branch 1
  `a11:0,a21:MIX,a31:0,a41:MIX` had finished before the outage (PARTIAL, 790 float-unsure, in the
  ledger). The dead run had already moved the other five PARTIAL lines to the history, so a plain
  relaunch would have retried only branch 1. `retry_partial.py` now retries the branches ABSENT
  from the ledger when there are any (the 5), in the old order: `M_M_0_M`, `M_0_0_M`, `0_0_M_0`,
  `M_M_0_1`, `0_M_M_1`. That's 8 h cap each, so ~40 h.
- **`PokerEnumc4Test`** (enumc4, 8 workers, `run_c4test_0_M_0_MN.env`): restarted from zero.
  Pre-outage log kept as `log_enumc3_c4test_0_M_0_MN_preoutage.txt`. At 1431 s it had
  kill 665, split 603, **float-unsure 339**, so it was not curing float-unsure at that point.
  Compare against enumc3 on the same branch (`log_enumc_c_0_M_0_MN.txt`: 76 unsure at 3 h,
  790 at 8 h).
- `PokerKeepAwake` relaunched.

# Where things stand — 2026-09-24 19:00

## DONE — the paper's results are all written up; no placeholders left in MASTER_DATA
- **Directed rounding + full re-derivation (suffix R)**: nash 77/77 (45,276 supports, all
  empty), seq 32/32 (20,755, all empty), silent 668 → 12 FAMILY. `python summarize6.py R`.
- **Certificates for every leaf**: 66,699 / 66,699 verified by `checkcert.py`, 0 failed.
- **Theorem 4** (on-path completeness) and **Theorem 5** (the complete Nash set, Table 4):
  PAPER_KIT §7.1–7.2, MASTER_DATA §16.7–16.10.
- **Theorem 6 — refinements decided exactly** (PAPER_KIT §7.3, MASTER_DATA §16.13):
  - every information set is binary ⟹ extensive-form proper = perfect (Lemma R1);
  - 18 coordinates fall to exact dominance (`D_v = c·R_v`, c = −1, +4 or +5 — an earlier count of 8
    used a coefficient-sign test that misses mixed-sign reaches); 13 have a nontrivial Nash window;
  - the belief system in closed form: `lim D_v/R_v = A_v/B_v`, seven linear forms **identical at
    all twelve leaves** (each verified symbolically against the tree);
  - forced in every sequential equilibrium: `b32 = b22 = c13 = c34 = 0`, `c43 = 1`, `c33 ≥ 1/2`
    and `c33` interior; only `c23` keeps freedom, and only with trembles of different orders;
  - enumeration **complete**: every pattern decided; **637 kill records + 3,554 box certificates + 21 witnesses, all replayed by the independent `checkseqcert.py` (12/12 leaves, 0 failed)**; 21 sequential
    witnesses (21/21 verified by the independent `checkseq.py`), 0 undecided**; exactly three
    patterns survive (two at the generic leaves, one at the corners, where refinement pins
    `a33 = c33 = 1/2`);
  - perfection certified in 3 patterns; **open problem 2 answered**: extensive-form properness
    leaves `c33` an interval (width 7/32 at `b11 = b21 = 1/8`, `c11 = 1/4`) where normal-form
    properness picks `55/96`. Over the whole set `c33 ∈ [1/2, 15/16]` — the upper half of its
    Nash window.
- **(3,5) feasibility settled** (§16.11): 171 of 240 cells decided inside 15 min (mean 186 s,
  no supports); Knuth node estimates put the P1-betting cells at 2.5e6–1.2e7 nodes against the
  4-card silent branch's 1.6e4 — 150× to 760×, so days per cell. The cap, not the method, is
  what leaves 35 undecided. `estcells.py` reports both leaf and node estimates.

## RUNNING (2026-09-24 18:54) — windowless via Task Scheduler
- **Third pass: 71 / 77 betting branches verified end to end** (4,394,323 certified nodes,
  1,877 support leaves all EMPTY_BOX, 0 failed; 22.1 h enum + 2.4 h check, finished
  2026-09-23 20:10). MASTER_DATA §16.9 and PAPER_KIT §7.1 carry it.
- **Retry of the 6 PARTIAL branches**: task `PokerRetryPartial` runs `retry_partial.py 3 9`
  (3 branches at a time, 9 workers each, 12 h cap) → appends to `enumc_summary_nash.txt`,
  log `log_retry_partial.txt`; the replaced PARTIAL lines are in `enumc_partial_history.txt`.
  When it ends: refresh §16.9's table (branches, nodes, kills, splits) and the two PAPER_KIT
  mentions (§7.1 proof note and "what the proof trusts").
- `PokerKeepAwake` holds idle sleep; `schtasks /end /tn PokerKeepAwake` when done.
  Start/stop anything with `schtasks /run|/end /tn <name>`. Never wrap a run in `cmd /c ... > log`:
  that opens a console window, and closing it kills the run (`^C` at the end of a log).

(3,5) sweep: DONE 2026-09-22 — 190 of 239 cells decided, none with P1 betting; §16.11.

## TRAPS
- **Anything launched from a tool call dies with the app's process tree.** 2026-09-22 02:26:
  keepawake and both drivers vanished together, no traceback; the box idle-slept at 02:31
  (`Kernel-Power` 42) and 11 h of enumeration was lost. Launch detached instead — the process
  then belongs to `WmiPrvSE`:
  ```
  Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = 'cmd /c "<python>" -u driver.py args > log.txt 2>&1'
    CurrentDirectory = '<project dir>' }
  ```
- **Kill trees, not drivers** (`taskkill /F /T /PID`): a bare kill orphans the pool workers,
  which keep computing and holding GB. Sweep for orphans (a `-c` worker whose parent is not a
  live python pid) after any killed run.
- **Tremble ratios normalise per information set, never globally** — each leading coefficient
  is homogeneous within one set. Under a global simplex 28 patterns were undecidable; per set
  the same patterns die instantly with certificates.

---

# Previously — 2026-09-19

## DONE: the on-path completeness theorem, both halves

**Every Nash equilibrium of three-player Kuhn poker has P1 silent and plays the
SGS family (Table 3 identities AND parameter ranges) at every reached
information set.** MASTER_DATA.md Part 16 is the record; §16.5 states the
theorem and its one quantified float caveat; §16.4.1 is the 77-branch table.

```
silent branch   5,754 supports -> 5,742 empty + 12 FAMILY (A/B/C, all corners)
betting side    77 branches, 1,337,533 supports, every one empty; 0 family, 0 open
controls        24,565 certified equilibria (744 family, 23,820 hunt, witness)
                all land in FAMILY leaves, in every enumeration variant
```

What made the last 40 hours possible (all in memory `exact-leaf-stage`):
`enuml.py` (exact test every 4 levels of the label DFS, dynamic work sharing,
`KUHN_ENUM=layered`) and `KUHN_ORDER=bet` (assign the responses to P1's bet
first). A branch that took 23 h under `enum6` takes minutes; the all-MIX
branch (Knuth estimate 2.7e6 patterns) took 205 s and has 0 supports.

**Nothing running.** The seq-mode ledger is also complete (32/32 branches,
230,975 supports, all empty) and the cross-check `xcheck2_MMM1` re-derived the
736,987-support branch with the final method: 2,406 supports, all empty, 484 s.
`python summarize6.py` prints both ledgers. `keepawake.py` can be killed.

**Left for the paper:** state the theorem as in §16.5; the float caveat is
quantified (rounding ~1e-13 against margins 1e-11), directed rounding in
`ivl` would remove it entirely. PAPER_KIT.md open problem 1 and the claim
table are updated.

---

# Previously (2026-09-10/11)


## 2026-09-11 — the undecided 13,779 were searched hard; 869 carry FAMILY equilibria

`lmdeep.py`: 48 random LM starts x 40 iterations per pattern (pipe2 used one
start, from the box centre, 14 iterations), every survivor polished and
certified by `eqtools.expl`:

```
TOTAL scanned 13779   LM-feasible 881   CERTIFIED Nash 869   OUTSIDE family: 0
certified 869 = 869 distinct patterns, 148 distinct leaf-distributions
family gap max 5.93e-13 ; P1 opening max 0.00e+00 ; u2 spread 3.8e-15
```

So the branch's accounting is now:

```
proven infeasible                          3,031,464   99.544 %
carry a certified FAMILY equilibrium           984      (115 + 869 patterns)
undecided                                   12,910    0.4239 %   -> pats_undecided2.npy
```

## ALSO 2026-09-11 — an algebraic attack on a11 (P1 bluffing its worst card)

With only Table 2 substituted, every one of the 27 first-order conditions is a
small multilinear polynomial (461 monomials in total, max 37 terms, degree <= 4;
`symbet.py`, `symbet2.py`, `symbet3.py`, all verified against `bgrad` to 1e-16).
The ones that matter for a11 are tiny:

```
du1/da11 = [ 2(1-c33)(1-b22) + 2(1-c23)(1-b32) - 3 ] / 12      (4 variables of 48)
du2/db32 = (3 a11 + 3 a21 - 2 a41) / 24                          (linear, 3 variables)
du2/db22 = -(5 a11 c34 - 3 a11 + 2 a31 + 2 a41) / 24
du3/dc23 = -(4 a11 b32 - 4 a11 + a31 - a41 b32 + 2 a41) / 24
du3/dc33 = -(4 a11 b22 - 4 a11 - 4 a21 - a41 b22 + 2 a41) / 24
```

Chained: a11 > 0 => c33,b22,c23,b32 < 1/2 => du2/db32 <= 0 => **2 a41 >= 3(a11+a21)**
=> a41 > 0. P1 can only bluff card 1 if it also value-bets card 4 (the family has
a41 = 0), and then needs du1/da41 >= 0. On 4,461 sampled points satisfying the
chain, du1/da41 <= -0.021 -- but the origin face (a11 = e, a41 = 2e, all else 0)
satisfies all six with equality, so six conditions are NOT enough (`provea11.py`
v1 found exactly that survivor). Version 2 uses all 27 conditions with box
semantics and a dependency-directed split; `propagate` passed a soundness control
(280 boxes containing certified equilibria, 0 killed). Running at delta = 0.02,
single-threaded, 20M-node cap: `log_provea11_d02.txt`.

## DONE — the silent branch is 99.544 % PROVEN (was 80.3 %)

Nothing is running; the machine is idle and the sleep hold is released.

| depth | proven of its input | **cumulative** | residual |
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
3,031,464 of 3,045,358 proven infeasible (99.544 %)
residual 13,894 = 115 distinct patterns that CARRY the certified equilibria
                + 13,779 undecided (0.4525 % of the branch)
```

**Both controls passed.** Depth 8 returns 2,445,582 — bit-for-bit `pipe2`'s
published number. And all 115 distinct patterns carrying certified equilibria are
still in the final residual: the chain never proved a pattern that has a solution.

**The gap that mattered is 43x smaller.** §15.9 had to report 19.7 % resting on
"LM failed to find a point"; it is now 0.45 %. Written up as §15.10 in
`MASTER_DATA.md`.

**Why it stopped at depth 36:** per-stage yield decays (52.8 → 42.6 → 41.3 →
31.6 → 15.3 %) while cost roughly doubles per level. Further progress needs a
different bound, not a bigger depth argument.

## The bug that nearly hid all of this — ERRATUM 7

`bisbatch.bisect` shares ONE `keepcap` across a whole block, so **block size, not
the depth argument, decides how much refinement each pattern gets**. The first
chain ran at the inherited `CH = 1024` and plateaued at ~93 %, looking exactly
like the bound had been exhausted:

```
depth  block  keepcap   proven      boxes
   16   1024    60000   1.61 %     129,355
   20   1024    60000   1.61 %     129,355   <- identical
   24   1024    60000   1.61 %     129,355   <- identical
   16    128    60000  31.79 %     272,421
   20    128    60000  67.19 %     309,345
   24     32    60000  81.98 %     301,894
```

At block 1024, depths 16/20/24 are **bit-identical** — depth was inert past the
point the block saturated the cap. `proveall` now uses `CH = 32` (most effective
AND fastest). §15.4's 80.3 % is unaffected: at depth 8 the rate is 81.10 % at
every block size from 32 to 1024, because the cap only binds as depth grows.

## Previously running — closing the silent branch's proof gap

`provechain.sh`: iterative deepening, each stage proving only what the previous
one could not. `keepawake.py` is holding (`log_keepawake3.txt`).

```
python -u proveall.py pats_0000.npy        8  14 s08
python -u proveall.py prove_surv_s08.npy  12  14 s12
python -u proveall.py prove_surv_s12.npy  16  14 s16     <- here
python -u proveall.py prove_surv_s16.npy  20  14 s20
python -u proveall.py prove_surv_s20.npy  24  14 s24
python -u proveall.py prove_surv_s24.npy  28  14 s28
```

| depth | proven this stage | **cumulative proven** | residual | time |
|---|---|---|---|---|
| 8 | 2,445,582 of 3,045,358 (80.305 %) | **80.305 %** | 599,776 | 2,556 s |
| 12 | 265,076 of 599,776 (44.196 %) | **89.011 %** | 334,700 | 4,732 s |
| 16 | running | | | |

**The depth-8 stage is the chain's control**: 2,445,582 is bit-for-bit the number
`pipe2` produced (§15.9.1), so `proveall` reproduces the published screen exactly
and every deeper stage builds on a verified baseline.

**The ceiling is 99.929 %, not 100 %.** 2,174 patterns (115 distinct) are
LM-feasible and carry the 2,138 certified equilibria; a sound prover can never
prove a feasible pattern infeasible, and `proveall`'s pre-flight exists to
guarantee it does not try. Reaching that floor would mean: *every pattern in the
P1-silent branch is either proven to carry no equilibrium, or carries one of the
744 certified equilibria — all of which lie in the SGS family.*

**Do not launch a deep pass over the whole file.** Running depth 18 directly at
all 3,045,358 patterns spends depth-18 effort on the 80 % that depth 8 kills
instantly: it managed 376 of 1523 chunks in 14 hours before being replaced by
this chain. Deepen the residual, never the input.

## Headline (2026-09-07)

1. **The P1-silent branch is settled end to end.** Not a 13.1 % sample any more:
   the whole 3,045,358-pattern enumeration has been screened. 744 distinct
   certified equilibria, **0 outside the SGS family**.
2. **Every `feas.py` verdict in the previous handoff was depth-limited, not
   tolerance-limited.** All 43,321,175 emitted boxes hit `maxdepth`; none reached
   `wtol`. That table says much less than it appeared to.
3. **Both exhaustive routes to the P1-betting question are now closed by
   measurement** rather than by guesswork — support enumeration is 10^9–10^10
   patterns per branch, and box refinement grows ~1.5x per level while needing
   ~104 more levels.
4. **One real instrument improvement fell out:** `bnb5`'s split rule is wrong.
   Splitting on gradient looseness instead of width gives 3x fewer boxes.

## 1. The P1-silent branch, whole

`400,000 (samp) + 2,645,358 (rest) = 3,045,358` is exactly the §15.3 enumeration.

| | samp (§15.4) | rest (new) | **whole branch** |
|---|---|---|---|
| patterns screened | 400,000 | 2,645,358 | **3,045,358** |
| proven infeasible by interval bisection | 320,743 (80.2 %) | 2,124,839 (80.3 %) | **2,445,582 (80.3 %)** |
| LM candidates | 262 | 1,912 | 2,174 |
| certified exact Nash (`expl < 1e-13`) | 259 | 1,879 | **2,138** |
| distinct leaf-distributions | 114 | 635 | **744** |
| **outside the SGS family** | 0 | 0 | **0** |

`union_silent.py` merges both halves by leaf-distribution signature and re-checks
everything, writing `certified_eq_all.npy` (744 profiles):

```
family leaf-distribution gap: max 1.288e-13   OUTSIDE family (>1e-9): 0 of 744
b41 = 2(b11+b21)                           max residual 9.70e-14
c21 = 1/2 - c11                            max residual 2.32e-14
b33 = 1/2+(b11+b21)/2+beta/2-b23(1-b21)    max residual 1.29e-13
beta = max{b11,b21} over the branch: [0, 0.25]   (family [0, 0.25])
u1 [-0.031250000000, -0.020833333333]   u2 identically -0.020833333333
u3 [ 0.041666666667,  0.052083333333]   — exactly the family's payoff set
```

Re-running `verify_surv.py` on the old sample reproduces §15.4 exactly (259
certified, 114 distinct, gap 2.301e-14), so these are new coverage, not a moved
goalpost.

**Caveat unchanged.** Only bisection proves, and it settled 80.3 %. The other
19.7 % of patterns are not proved infeasible — LM merely failed to find a point
there. This is an exhaustive *search* over the branch, not a proof of emptiness.

## 2. ERRATUM: every feas.py verdict was depth-limited

`bnb5` emits a box when `W.max < wtol` **OR** `depth >= maxdepth`. All 13 tasks
ran `wtol=0.06, maxdepth=26` with ~26 free coordinates — about one halving per
coordinate, width 0.5. Reaching 0.06 needs ~5 halvings each, i.e. depth ~130.

```
widthscan.py:  TOTAL boxes 43321175   emitted on width tolerance: 0 (0.0000%)
```

Zero, out of 43.3 million. Meanwhile the node cap was 120,000,000 and the biggest
task used 21,156,070 — 18 %. **The runs stopped on the wrong limit**, and
`abort=False` was true while saying nothing about coverage.

**Before any bnb5 run, assert `maxdepth >= nfree * ceil(log2(1/wtol))`.**

## 3. What the boxes still prove

They are coarse but they are a sound *cover*, so `betencl.py` extracts a rigorous
enclosure with no new search. All 8 bet tags agree:

- **Table 2's 21 coordinates are forced across the entire P1-betting region.**
  Table 2 had only ever been established globally; this is it holding separately
  on the betting side, and it doubles as a control on the box set.
- The only other constraint recovered is `a21 in [0, 0.5]` whenever `a11 >= 0.02`.
- Utility enclosures are trivial (±0.8 against a family range of width 0.01),
  which is the honest price of width-0.5 boxes.

## 4. Route A — support enumeration: CLOSED

Knuth unbiased tree-size estimator, 4,000 random root-to-leaf walks
(`treesize.py`). The silent branch is the control; its true value is known:

| branch | estimated patterns | vs silent |
|---|---|---|
| **silent (control, true 3,045,358)** | **3.035e6 ± 1.5e5** | 1x |
| `a11 = 1` | 1.815e9 | 600x |
| `a11` interior | 2.318e10 | 7,600x |
| `a41` interior | 2.957e10 | 9,700x |
| `a31` interior | 3.277e10 | 10,800x |
| `a21` interior | 4.000e10 | 13,100x |

100 % of sampled paths survive pruning — propagation is not biting on these
branches. Cross-checked directly: `betenum.py a11 MIX` emitted 1,778,292 leaves
in 4,018,960 nodes in 1,289 s, i.e. 0.008 % of the estimate, putting a full
enumeration of that one branch at ~194 days *before* any screening. The screen
itself runs at 48.9 patterns/s. §15.3's method does not port to the bet side.

## 5. Route B — box refinement: CLOSED at the current split rule

Depth ladder on `bet_a41_lo` (`tasks_ladder.txt`, `log_ladder.txt`):

| depth | 16 | 18 | 20 | 22 | 24 | 26 |
|---|---|---|---|---|---|---|
| boxes | 12,178 | 45,594 | 138,809 | 337,074 | 651,161 | 1,544,817 |
| growth/level | — | 1.94 | 1.75 | 1.56 | 1.39 | 1.54 |

The rate stops decaying and settles near 1.5. Reaching a real `wtol` needs ~104
further levels; even depth 40 is ~200x the boxes of depth 26 on the *smallest*
task alone, which is hundreds of GB before it is anything else.

## 6. The split rule is wrong — 3x, and it is one line

`bnb5` splits the widest coordinate. `splitrule.py` compares alternatives on
`bet_a41_lo` at maxdepth=22, with `width` included as the control:

```
grad       344,620 nodes   111,627 boxes   324s   x0.331 boxes
reachgrad  344,620 nodes   111,627 boxes   325s   x0.331
width      847,044 nodes   337,074 boxes   369s   x1.000  <- reproduces the ladder exactly
reach      847,044 nodes   337,074 boxes   408s   x1.000
```

`grad` = split on `W * (DHI - DLO)`: width times how loose that coordinate's own
gradient bound is. Masking unreachable coordinates (`reach`) changes **nothing**
on its own, because an unreachable coordinate already has `DHI - DLO = 0` and
`grad` drops it for free — do not spend time on that idea again.

The full `grad` ladder (`gradladder.py`, `log_gradladder.txt`) settles it:

| depth | 18 | 20 | 22 | 24 | 26 |
|---|---|---|---|---|---|
| boxes, `grad` | 24,346 | 53,361 | 111,627 | 230,124 | **475,538** |
| growth/level | — | 1.480 | 1.446 | 1.436 | 1.438 |
| boxes, `width` | 45,594 | 138,809 | 337,074 | 651,161 | **1,544,817** |

3.2x fewer boxes at depth 26 and a lower exponent (**1.44 flat** against ~1.57),
but *flat* is the point: it is not decaying towards 1, so `1.44^104` is still
~10^16 and **the refinement route is closed under the better rule too.** What the
rule does buy is that every future bnb5 run is ~2.5x cheaper, which is worth
taking regardless.

## 7. Two controls that failed, and what they saved

- **`control_boxpats.py` — 0 of 9.** A support pattern derived from a coarse box
  cannot express a family equilibrium. The boundary reading pins coordinates that
  are interior (`a33 = 1/2` sits on a slab edge, gets pinned to 0, and bisection
  then correctly *proves* that pattern infeasible); the interior reading demands
  `du = 0` on coordinates hard against 0 or 1. Every real equilibrium mixes the
  two, and enumerating the mixtures is 2^21 per box. **This killed a planned
  ~6-day screen that would have returned a clean, meaningless "nothing found".**
- **`control_pg.py` — 0 of 9 from box centres.** `pgsolve.py` (LM on the
  projected-gradient residual `x - clip(x + du, 0, 1)`, no support labels) is
  itself correct: `F(p*) = 0` exactly at known equilibria, and it converges from
  perturbations up to ~0.1. It fails from box centres because a width-0.5 slab
  centre is ~0.25 away in every coordinate. So the depth-26 boxes cannot seed a
  search either.

## 8. Route C — multistart: run, and it found nothing outside the family

`pilot_hunt.py`, 2,048 uniform random starts with Table 2 fixed (27 free
coordinates), `pgsolve` then certification by `eqtools.expl`:

```
free           starts 2048  residual<1e-12 19  CERTIFIED 8 (0.39%)  with P1 betting 0
     distinct leaf-distributions 4   family gap max 5.26e-13   OUTSIDE family: 0
forced to bet  starts 2048  residual<1e-12 13  CERTIFIED 9 (0.44%)  with P1 betting 0
     distinct leaf-distributions 6   family gap max 7.26e-14   OUTSIDE family: 0
```

Two things to read here. First, 19 points reach residual < 1e-12 but only 8 are
equilibria — the projected gradient is a *first-order* condition and off-path
information sets make it insufficient (§7.7), so **certification is by `expl`,
never by the residual**. Second, in the "forced to bet" arm every start had an
opening coordinate drawn from [0.02, 1], and *every* certified equilibrium still
came back with P1 silent — the same behaviour §10.5 Attempt 3 saw from CFR.

### COMPLETE — 20,000,000 starts, 0 with P1 betting

```
python -u bethunt.py 625000 32 24 bet2      # 26h 38m, no interruptions
TOTAL starts 20000000  residual-converged 181463  CERTIFIED 75201  distinct 23820
certified equilibria with P1 betting: 0
```

Audit of all 23,820 distinct certified equilibria (`hunt_eq_bet2.npy`):

```
max exploitability      9.999e-14   (all < 1e-13)
family gap              max 5.822e-12
OUTSIDE family (>1e-9)  0 of 23820
max P1 opening freq     2.204e-12       — P1 silent in every one
u1 [-0.031250000, -0.020833333]   u2 spread 1.25e-13 about -0.020833333
u3 [ 0.041666667,  0.052083333]   beta spans the full [0, 0.25]
```

About 15M of the 20M starts began with an opening coordinate drawn from
[0.02, 1]; every one that converged to a certified equilibrium came back with P1
silent. That is the same behaviour §10.5 Attempt 3 saw from CFR, now at 10^7
scale and with exact certification rather than convergence.

**This is a search, not a proof.** It cannot show the family is complete. It is
the strongest evidence available once both exhaustive routes are closed.

### The run first reported "OUTSIDE family: 2" — it was a tolerance bug

Worth reading before trusting any future out-of-family report. `family_gap`
returns **1.0 as a sentinel** meaning "could not construct the Table-3 image",
not as a measured distance, and its guard rejected anything above `1 + 1e-12`.
Both flagged points were the family's own corner `b11 = b21 = 1/4`, where
`b41 = 2(b11+b21) = 1` exactly and floating point lands at `1 + 1.0e-12`. Their
real leaf-distribution gap, after the clip the function performs anyway, is
**2.2e-16** — family members exactly.

Fixed in `classify.py` (`OOR_TOL = 1e-9`) and `family.py` (`TOL` on the `[0,1]`
checks, which every other check in `violations` already had).
`control_famgap.py` controls both directions: corners give gap 0, a non-profile
image (`b11 = b21 = 0.4` → `b41 = 1.6`) is still rejected, and a 1e-6
perturbation off the family is still detected with gap equal to the
perturbation. Re-auditing the silent branch's 744 with the fix leaves it
unchanged at 0 outside.

### Size the batch before starting anything like this again

The first launch used 20 workers x 2048 and got **21 starts/s**. The same work at
24 x 32 gets **230**. An 11x difference from batch size alone:

```
20 x 2048   21      24 x 128   108     24 x 32   230
12 x  512   59      28 x 128   106     28 x 32   233
20 x  256   80      24 x  64   157     28 x 16   256   <- best
                    28 x  64   165     24 x  8   177   <- dispatch overhead
```

It is not BLAS oversubscription: one process alone does 19 starts/s and
`OMP_NUM_THREADS=1` changes nothing (53.1 vs 52.0 ms/start). It is cache — the
per-batch Jacobian is `(B,48,48)` float64, 590 kB at B=32 against 37.7 MB at
B=2048, and 24 workers streaming 37.7 MB each saturate memory bandwidth while the
CPU still reads 89 % busy. Worker count barely matters above ~24; batch size is
the whole story.

## Environment traps (unchanged)

- Processes are **`python3.13`**; `Get-Process python` returns nothing. Use
  `tasklist` or `status.ps1`.
- `np.load` on an `.npz` holds the file open; a later `os.replace` fails with
  `PermissionError [WinError 5]`. Always `with np.load(...) as z:`.
- An empty `feas.py` log means "no task finished yet", not "not running".
- The box idle-sleeps after 60 min on AC and it looks exactly like a hang.
  `keepawake.py` is running (`log_keepawake2.txt`).
