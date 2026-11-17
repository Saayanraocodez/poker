"""Build the three split papers from PAPER_DRAFT.md Part I, so they stay in sync with it.

    python papers/build_split.py        ->  papers/PAPER_A_equilibrium_set.md
                                            papers/PAPER_B_who_pays.md
                                            papers/PAPER_C_learning.md

Each paper = hand-written front matter (below) + sections of Part I, renumbered.  A reference "§N.M" to a
section of this paper is renumbered; one to a section that lives elsewhere becomes "§N.M of the full draft".
Theorem, lemma and table numbers are shared across the three papers and are not changed.
The five-card game (Part I §10) and the Hold'em line (§17) are parked: not in any of the three.
"""
import re, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
src = open(os.path.join(ROOT, 'PAPER_DRAFT.md'), encoding='utf-8').read()
part1 = src[src.index("# PART I — THE PAPER"):src.index("# PART II — APPENDICES")]


def section(n):
    m = re.search(r"^## %d\. .*$" % n, part1, re.M)
    nxt = re.search(r"^## ", part1[m.end():], re.M)
    body = part1[m.start():m.end() + (nxt.start() if nxt else len(part1) - m.end())]
    return re.sub(r"\n---\s*$", "\n", body.rstrip()) + "\n"


def subsection(n, k):
    sec = section(n)
    m = re.search(r"^### %d\.%d .*$" % (n, k), sec, re.M)
    nxt = re.search(r"^### ", sec[m.end():], re.M)
    return sec[m.start():m.end() + (nxt.start() if nxt else len(sec) - m.end())].rstrip() + "\n"


REFS = part1[part1.index("## References"):].rstrip()
REFS = re.sub(r"\n---\s*$", "", REFS) + "\n"


def assemble(title, front, items, tail):
    """items: list of ('sec', n) | ('sub', n, [k...], new title) | ('text', title, body)"""
    out = [front.rstrip() + "\n"]; mapping = {}; num = 0; bodies = []; partial = set()
    for it in items:
        num += 1
        if it[0] == 'sec':
            n = it[1]; body = section(n)
            mapping[str(n)] = str(num)
            body = re.sub(r"^## %d\. " % n, "## %d. " % num, body, count=1, flags=re.M)
            body = re.sub(r"^### %d\.(\d+) " % n, lambda m: "### %d.%s " % (num, m.group(1)), body, flags=re.M)
            body = re.sub(r" \(new(, preliminary)?(, 20\d\d-\d\d-\d\d)?\)$", "", body.split("\n", 1)[0]) + "\n" + body.split("\n", 1)[1]
        elif it[0] == 'sub':
            n, ks, newtitle = it[1], it[2], it[3]
            parts = ["## %d. %s\n" % (num, newtitle)]; mapping[str(n)] = str(num); partial.add(str(n))
            for j, k in enumerate(ks, 1):
                sub = subsection(n, k)
                mapping["%d.%d" % (n, k)] = "%d.%d" % (num, j)
                parts.append(re.sub(r"^### %d\.%d " % (n, k), "### %d.%d " % (num, j), sub, count=1, flags=re.M))
            body = "\n".join(parts)
        else:
            body = "## %d. %s\n\n%s\n" % (num, it[1], it[2].strip())
        bodies.append(body)

    def fix(m):
        full = m.group(1) + (m.group(2) or "")
        if full in mapping: return "§" + mapping[full]
        if m.group(1) in mapping and m.group(2) and m.group(1) not in partial: return "§" + mapping[m.group(1)] + m.group(2)
        if m.group(2): return "§%s of the full draft" % full
        if m.group(1) in mapping: return "§" + mapping[m.group(1)]
        return "§%s of the full draft" % full
    text = "\n---\n\n".join(bodies)
    text = re.sub(r"§(\d+)(\.\d+)?(?! of the full draft)", fix, text)
    text = text.replace("of the full draft of the full draft", "of the full draft")
    return "# " + title + "\n\n" + out[0] + "\n---\n\n" + text + "\n---\n\n" + tail.strip() + "\n\n---\n\n" + REFS


COMMON = """**Saayan Rao** — split draft, built by `papers/build_split.py` from `PAPER_DRAFT.md` Part I.

> One of three papers cut from the single working draft. Theorem, lemma and table numbers are shared
> across the three. The research record (`MASTER_DATA.md`), the code map and the reproduction commands
> are in `PAPER_DRAFT.md` Parts II–III. Claim tags: **[P]** proved, **[E]** exact computation,
> **[G]** grid or sampling evidence, **[F]** float exploration, **[F\\*]** float carried to machine
> precision, **[?]** not established. The five-card game and the Hold'em line are not in this paper.
"""

# ------------------------------------------------------------------------------------------------ A
FRONT_A = COMMON + """
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
"""
TAIL_A = """## Limitations and open problems

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
"""
ITEMS_A = [('sec', 2), ('sec', 3), ('sec', 4), ('sec', 5), ('sec', 6), ('sec', 7), ('sec', 8),
           ('sub', 18, [1, 3, 4], "Selection, correlation and the ante")]

# ------------------------------------------------------------------------------------------------ B
FRONT_B = COMMON + """
## Abstract

In a two-player zero-sum game a deviation's whole loss lands on the single opponent. With three players
the loss is split between two opponents, and Nash equilibrium does not determine the split. We study
this in three-player Kuhn poker, whose equilibrium set is known exactly (companion paper: every
equilibrium has the first player silent and follows the Szafron–Gibson–Sturtevant family on path).

We define an incidence ratio ρ, the share of a deviator's loss borne by a given opponent. On the
equilibrium family ρ is undefined on 19 of 48 coordinate directions, changes sign, and is unbounded. Its
singularities are exactly the boundary of the equilibrium region: ρ has simple poles where a deterrence
inequality becomes tight, with residue equal to the costless transfer available there (Theorems 1–2),
and the width of the indeterminate window equals the family's own payoff-transfer parameter
(Proposition 5), so it cannot be shrunk away. The parameters that locate the poles are never reached in
play and have no effect on payoffs.

What closes the question is not Nash equilibrium. Sequential rationality fixes ρ's sign; perfection and
quasi-perfection leave the same interval; every normal-form proper equilibrium has the off-path call
frequency at one interior point, `c33 = lo + w/3`, where ρ is finite and rational (Theorem 3). Two
noise models make this concrete and disagree with each other: trembles of one order drive the
equilibrium to an END of the window, a pole of ρ, and to the largest payoff transfer `β = 1/4`; logit
noise drives it to `lo + w/3` and to `β* ≈ 0.1616`, the root of an explicit equation.

## Contributions

1. **The incidence ratio and its structural facts** (Propositions 1–5).
2. **Poles on the boundary of the equilibrium set**: a three-part criterion (Theorem 1), an exact
   Möbius form with residue `R = t/D′` (Theorem 2), a hard floor (Proposition 5).
3. **Off-path determination**: who pays is decided by behaviour that never occurs.
4. **Normal-form properness forces `c33 = lo + w/3`** (Theorem 3, with a complete necessity proof).
5. **Selections**: generic trembles go to a pole and to `β = 1/4`; logit noise to `lo + w/3` and `β*`.
6. **A two-player control**: the phenomenon needs three players for two independent reasons.
"""
SUMMARY = """The companion paper proves the following; they are used here as given.

- **Theorem 4.** Every Nash equilibrium is realisation-equivalent to a member of the SGS family: P1
  never bets, and Table 3 holds on every reached information set.
- **Theorem 5.** The complete Nash set is the union of twelve explicit sets; Table 4 gives the certified
  range of every coordinate. Off path, the responses to P1's bet are constrained only by P1's
  deterrence inequalities.
- **Theorem 6.** In every sequential equilibrium `b32 = b22 = c13 = c34 = 0`, `c43 = 1` and
  `c33 ∈ [1/2, 15/16]`; perfection, agent-normal-form properness and quasi-perfection leave `c33` an
  interval (Corollaries 6.1–6.2).
"""
TAIL_B = """## Limitations and open problems

1. **Coordinate directions.** ρ is a ratio, not a convex combination of coordinate ρ's; per-direction
   values do not extend automatically. Census counts and sign ranges are grid statistics.
2. **Theorem 3 is a necessity statement.** Which `β` the normal-form proper set allows, and whether
   every such `β` carries a proper equilibrium at `c33 = lo + w/3`, are open.
3. **The two selections are machine-precision float results.** Open: prove the tremble selection for
   every shape of one order; determine `c11` in the logit limit (the first-order condition leaves it
   free; the branch gives 0.250).
4. **A vector residue identity** for four or more players, where incidence lives on a simplex.
5. **A general theorem:** in n-player constant-sum extensive games, does an equilibrium component with
   an attainable deterrence boundary always carry an unbounded incidence ratio there? (First results
   for Hold'em river games are in the full draft.)
"""
ITEMS_B = [('sec', 2), ('sec', 3), ('text', "The equilibrium set (from the companion paper)", SUMMARY), ('sec', 9),
           ('sub', 18, [1, 2], "What a noise model selects")]

# ------------------------------------------------------------------------------------------------ C
FRONT_C = COMMON + """
## Abstract

Counterfactual regret minimisation has no convergence guarantee beyond two players, and three-player
Kuhn poker is the standard small test. Its complete Nash set is now known exactly (companion paper),
so "what does CFR compute here?" can be answered with certified distances instead of exploitability.

All 150 outputs of external-sampling MCCFR at 10⁶ iterations lie a certified distance of at least
0.0067 from the Nash set (median 0.044), and the bound is attained by an exact witness in every case;
the error is on the path of play. The reason is geometric: CFR averages in sequence form and the Nash
set is not convex — the midpoint of two exact equilibria with equal payoffs has exploitability exactly
1/320. At 10⁸ iterations MCCFR still wanders among sub-families. Full-width alternating variants (CFR+,
DCFR) do converge onto the Nash set, to certified distance about 5·10⁻⁶, yet select no refinement, and
every variant tested favours the third seat (`β ≈ 0.12–0.17`). Exploitability understates the distance
to equilibrium by a median factor of 29.

Adding noise does select, but the answer depends on the noise. On the game with a floor on every
action, CFR+ stops converging; solved exactly, that game has an isolated equilibrium which tends to the
family's corner `β = 1/4`. The logit quantal response equilibrium tends to `β* ≈ 0.1616`, the root of
an explicit equation, and to the off-path call frequency normal-form properness requires. On path the
equilibrium being played is identifiable from observed play; whether it is an equilibrium is not.

## Contributions

1. **Certified distances from CFR outputs to the complete Nash set**, with exact witnesses.
2. **Non-convexity as the mechanism**: an exact two-point demonstration (Proposition 8).
3. **Which variants converge**: alternating full-width CFR+ and DCFR do; MCCFR, CFR and Linear CFR do
   not within the budgets tried. None selects a refinement; all carry a seat bias.
4. **Noise selects, differently**: floors (trembles) against logit.
5. **Identifiability**: on-path parameters are locally identifiable; equilibrium-ness is not.
"""
SUMMARY_C = """The companion papers prove the following; they are used here as given.

- **Theorem 4.** Every Nash equilibrium is realisation-equivalent to a member of the SGS family: P1
  never bets, and Table 3 holds on every reached information set. P2's payoff is `−1/48` in every
  equilibrium; P1's and P3's vary with `β ∈ [0, 1/4]`.
- **Theorem 5.** The complete Nash set is the union of twelve explicit sets; Table 4 gives the certified
  range of every coordinate. This is what distances are measured to.
- **Theorem 6 and Theorem 3.** Every sequential equilibrium has `b32 = 0`; every normal-form proper
  equilibrium has `c33` at one third of its window.
"""
TAIL_C = """## Limitations and open problems

1. **Specific variants, budgets and averaging schemes.** The distances are certified; the conclusions
   about convergence are empirical.
2. **Why do alternating full-width variants converge here, and simultaneous ones not?**
3. **What drives the seat bias** `β ≈ 0.12–0.17`? Neither noise model lands there (`1/4` and `0.1616`).
4. **Is there a regret-minimising dynamic that converges on the perturbed game**, and so selects the
   tremble limit? CFR+ does not.
5. **Identifiability** is a probe at single rational points, with float Fisher information. Open: the
   price of learning the off-path responses, which decide whether a profile is an equilibrium.
"""
ITEMS_C = [('sec', 2), ('sec', 3), ('text', "The equilibrium set (from the companion papers)", SUMMARY_C), ('sec', 11),
           ('sub', 18, [1, 2], "Noise selects, and the answer depends on the noise"), ('sec', 12)]

PAPERS = [("PAPER_A_equilibrium_set.md", "The Complete Equilibrium Set of Three-Player Kuhn Poker: Certificates, Refinements, Correlation and the Ante", FRONT_A, ITEMS_A, TAIL_A),
          ("PAPER_B_who_pays.md", "Who Pays When a Player Deviates? The Incidence Ratio in Three-Player Kuhn Poker", FRONT_B, ITEMS_B, TAIL_B),
          ("PAPER_C_learning.md", "What CFR Computes in Three-Player Kuhn Poker: Certified Distances, Non-Convexity and Noise", FRONT_C, ITEMS_C, TAIL_C)]
for fn, title, front, items, tail in PAPERS:
    text = assemble(title, front, items, tail)
    open(os.path.join(HERE, fn), 'w', encoding='utf-8').write(text)
    print("%-32s %5d lines, %6d words" % (fn, text.count("\n"), len(text.split())))
