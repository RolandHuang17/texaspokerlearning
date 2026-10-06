# Tracing CFR iterations by hand on the Kuhn game

<!-- hands: 2 -->
<!-- terms: kuhn, cfr, regret-matching, information-set, strategy-profile, indifference, mixed-strategy, bluff-to-value-ratio, minimum-defense-frequency, exploitability -->

## 本节目标 / Objectives

- Carry one Kuhn information set's ledger from iteration 1 to iteration 8 and say how the frequencies follow it.
- Read the committed artifact (`data/gen/solver/kuhn.json`) -- all 12 rows -- and state plainly what this run converged to.
- Explain why "the king opens only about 64% of the time" is not a bug: give the indifference condition that licenses it and show the run satisfies it.
- Explain why `solver/proofs.py` asserts dominance relations and the family bound but never an opening frequency, and what that teaches about reading any solver output.

## 前置知识 / Prerequisites

- `08-01` nodes, information sets, strategy profiles: rows are cut by my own card.
- `08-02` regret matching and counterfactual weighting: every ledger number here comes from it.
- `02-04` bluff-to-value ratio: Kuhn's family sits exactly on chapter 02's half-pot row.

## 核心原理 / The principle

Kuhn is the one game in this chapter where every step can be checked by hand: cards `J < Q < K`, one street, bet size 1, no raises, 6 deals, 9 nodes, 12 information sets (`src/pokergto/solver/games.py#kuhn`). It is also the only bluffing game here with a complete analytic solution: game value `-1/18`, and its equilibria form a **one-parameter family**.

So this lesson is not about how to run CFR. It is about two harder habits:

1. trace one iteration by hand and watch the ledger push the frequencies;
2. understand that **the frequencies you converged to are not the same object as the theory's frequencies**. Every point on the family has exploitability zero; which one a run lands on is a property of the implementation. Treating that point as a theorem is the real lesson of this chapter.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Family and dominance assertions: `src/pokergto/solver/proofs.py#KUHN`. Artifact: `data/gen/solver/kuhn.json` (CFR+, 20,000 iterations).
>     The family verification and the hybrid exploitability below are computed on the spot with the commands shown.

## 推导 / Derivation

Let `alpha` be P0's frequency of opening with `J`, `kappa` P0's frequency with `K`; `beta` P1's queen-call frequency facing an opening bet; `g` P1's frequency of betting `J` after P0 checks; `c` P0's queen-call frequency facing a bet. Five quantities, four relations, all from indifference.

**Relation 1: `beta = 1/3`.** P0 with `J`: checking always loses the ante (`J` never wins a showdown), value `-1`. Opening meets `Q` half the time and `K` half: `0.5*[(1-beta)(+1) + beta(-2)] + 0.5*(-2) = -0.5 - 1.5*beta`. Equalise -> `beta = 1/3`.
Meaning: **P1's queen must call exactly one third of the time before `alpha` gets any freedom at all.** `alpha` itself is never pinned -- that is what the family is.

**Relation 2: `kappa = 3*alpha`.** For P1's queen to mix strictly inside `(0, 1)` it must be indifferent. The counterfactual ratio of jack to king in P0's opening range is `alpha : kappa`, so
`2*alpha/(alpha+kappa) - 2*kappa/(alpha+kappa) = -1` -> `kappa = 3*alpha`.
Since `kappa <= 1`, the bound **`alpha <= 1/3`** drops out immediately: it is the physical constraint "the king can be bet at most always". The interval textbooks quote is a consequence of `kappa = 3*alpha`; and **"always bet the king" is exactly the corner of that line at `alpha = 1/3`, not a premise.**

**Relation 3: `c = 1/3 + alpha`.** P1 bets `J` after a check, and the two reachable deals must be weighted by **opponent reach**: P0 checks with `Q` at frequency 1 and with `K` at `1 - kappa`. The jack's bet-minus-check difference is `2 - 3c` against the queen and `-1` against the king, so
`1*(2 - 3c) + (1 - kappa)*(-1) = 0` -> `c = (1 + kappa)/3 = 1/3 + alpha`.
**The weights are counterfactual, not "the opponent is equally likely to hold Q or K".** The naive prior gives `c = 1/3`, which is 0.2133 away from the artifact's `0.5467` -- an error a reader actually makes (example 5 and trap 2 below).

**Relation 4: `g = 1/3`.** P0's queen must be indifferent facing a bet: calling wins 2 or loses 2, folding costs 1, so `P(J | bet) = 1/4` is required -> `g/(g+1) = 1/4` -> `g = 1/3` (P1 never bets the queen after a check, and always bets the king).

**Verify the family.** Parameterise a profile from the four relations and feed it to `exploitability`:

```bash
PYTHONPATH=src python -c "
import numpy as np
from pokergto.solver.games import kuhn
from pokergto.solver.exploitability import exploitability, expected_value
t=kuhn(1.0); idx={l:i for i,l in enumerate(t.infoset_labels)}
def fam(a):
    k=3*a; c=(1+k)/3
    d={'0:0:J':(1-a,a),'0:0:Q':(1.0,0.0),'0:0:K':(1-k,k),
       '1:1:J':(2/3,1/3),'1:1:Q':(1.0,0.0),'1:1:K':(0.0,1.0),
       '2:0:J':(1.0,0.0),'2:0:Q':(1-c,c),'2:0:K':(0.0,1.0),
       '3:1:J':(1.0,0.0),'3:1:Q':(2/3,1/3),'3:1:K':(0.0,1.0)}
    m=np.zeros((t.n_infosets,2))
    for l,i in idx.items(): m[i]=d[l]
    return m
for a in (0.0,0.1,0.213282,1/3): print(a, exploitability(t,fam(a)), expected_value(t,fam(a)))"
# exploitability is at the 1e-17 level for every alpha; game value -0.055555556 = -1/18
```

The `alpha = 1/3` run is the textbook profile (king always bets, P0's queen calls 2/3); `alpha = 0.213282` is the member this repository's run landed on. Both pass the exploitability gate and both pass the `-1/18` gate -- **which is precisely why the registry asserts relations and not rows.**

## 直觉 / Intuition

Picture the equilibrium as a line, not a point:

- Sliding `alpha` leaves P0's jack indifferent and P1's queen indifferent. Nothing pushes a run toward one particular `alpha`; where it stops depends on flooring, weighting and traversal order, not on theory.
- The existence of the line is itself the information: P0's bluff frequency is not identifiable, so **"did the code get this 64% wrong?" is a question no single row can answer**. Relations can: `3*alpha = 0.639846` against the king's opening `0.639918` (gap 7.2e-5) and `1/3 + alpha = 0.546615` against the queen's call `0.5467` (gap 8.5e-5). Both gaps sit at the 1e-4 level, the same size as that run's residual exploitability `1.08e-05` -- not a coincidence, the same "not fully converged" remainder.
- The transferable habit: **move from "what should this hand do" to "what constrains the frequencies on this row".** Most real-poker arguments (should the nuts always bet, should one size always be used) are equilibrium-selection questions dressed as theory questions.

## 算例 / Worked examples

**Example 1 -- a real ledger, Kuhn under CFR+, iterations 1 to 8.** Column order: nodes 0 and 1 are `(check, bet)`, nodes 2 and 3 are `(fold, call)`.

| Iter | Information set | Cumulative regret `R` | Current strategy | Average strategy |
|---|---|---|---|---|
| 1 | `0:0:J` | `[0.0, 0.125]` | `(0, 1)` | `(0.5, 0.5)` |
| 2 | `0:0:J` | `[0.1667, 0.125]` | `(0.571, 0.429)` | `(0.167, 0.833)` |
| 4 | `0:0:J` | `[0.2537, 0.0]` | `(1, 0)` | `(0.6, 0.4)` |
| 8 | `0:0:J` | `[0.2431, 0.1124]` | `(0.684, 0.316)` | `(0.738, 0.262)` |
| 1 | `0:0:K` | `[0.0, 0.125]` | `(0, 1)` | `(0.5, 0.5)` |
| 3 | `0:0:K` | `[0.0, 0.162]` | `(0, 1)` | `(0.237, 0.763)` |
| 8 | `0:0:K` | `[0.0601, 0.1674]` | `(0.264, 0.736)` | `(0.281, 0.719)` |
| 1 | `3:1:Q` | `[0.0833, 0.1667]` | `(0.333, 0.667)` | `(0.5, 0.5)` |
| 8 | `3:1:Q` | `[0.2181, 0.1589]` | `(0.579, 0.421)` | `(0.634, 0.366)` |

Three observations: `0:0:J`'s *current* strategy swings `(0,1) -> (0.571,0.429) -> (1,0) -> (0.684,0.316)` while its average glides smoothly toward `0.738`; `0:0:K`'s check entry gets floored back to 0 on iteration 3 (the CFR+ property); `3:1:Q`'s average is already near `1/3` at iteration 8 (`0.366`) because relation 1 pins it. The command to reproduce the table is in the Drills.

One implementation detail must be stated or the hand arithmetic will not match: the floor in `cfr.py` is applied **after every `(node, deal)` update**, not once per iteration (`np.maximum(regret_row, 0.0, out=regret_row)` sits inside the recursion). That is why `3:1:Q` reads `[0.0833, 0.1667]` after iteration 1 instead of `[0, 0.1667]`: deal 0 leaves `[0, 0.25]` after flooring, then deal 5 adds `+0.0833 / -0.0833` and the negative entry is not re-floored. Deal order is fixed by `permutations`, so the output stays deterministic (the artifact records `determinism_verified: true`, `seed: 0`) -- but a learner following the textbook "sum the iteration, then floor" recipe will not reproduce this intermediate ledger.

**Example 2 -- the answer at 20,000 iterations (`data/gen/solver/kuhn.json`).**

| Information set | Average strategy (verbatim from the artifact) | Against the family relations |
|---|---|---|
| `0:0:J` | check 0.786718 / bet 0.213282 | `alpha = 0.213282` |
| `0:0:K` | check 0.360082 / bet 0.639918 | `3*alpha = 0.639846`, gap 7.2e-5 |
| `0:0:Q` | check 1.0 / bet 0.0 | never opens the queen |
| `1:1:J` | bet 0.333346 | `g = 1/3` |
| `1:1:Q` | bet 0.0 | |
| `1:1:K` | bet 1.0 | |
| `2:0:J` | call 0.0 | strictly dominated, excluded |
| `2:0:Q` | call 0.5467 | `1/3 + alpha = 0.546615`, gap 8.5e-5 |
| `2:0:K` | call 1.0 | strictly dominant |
| `3:1:J` | call 0.0 | |
| `3:1:Q` | call 0.333365 | `beta = 1/3` |
| `3:1:K` | call 1.0 | |

Game value `-0.0555555567` (gate `|delta| <= 1e-4` against `-1/18 = -0.0555555556`), exploitability `1.08333e-05` (gate `5e-05`), `determinism_verified: true`, `seed: 0`, `timing_seconds: null`.

**Example 3 -- splicing two members together.** Take the artifact's `alpha = 0.213282`, keep the other 11 rows untouched, and change only `0:0:K` to "open always" (the textbook line). That hybrid:

```
exploitability = 0.030002 chips per hand   (about 2,800x the artifact's residual)
game value     = -0.055554 chips per hand  (still passes the -1/18 gate!)
```

**This is the single most important number in the lesson**: pairing the corner's `kappa = 1` with the interior's `alpha = 0.2133` produces a strategy that is not an equilibrium, yet its game value is still right. The `-1/18` anchor cannot catch it; only the exploitability gate can. That is why ADR-0002 demands both mechanisms.

**Example 4 -- Kuhn's opening range lands on chapter 02's half-pot row.** Kuhn's bet is 1 into a pot of 2, i.e. half pot, so every interior member gives

```
bluff share of the opening range = alpha/(alpha+kappa) = alpha/(4*alpha) = 1/4 = 25.00%
value : bluff                    = 3 : 1
```

From the artifact: `0.213282/(0.213282+0.639918) = 0.24998` and `0.639918/0.213282 = 3.0003`. The generated table below puts the algebra for `1/2 pot` (0.25 and 3.0) next to it: same fact, one side iterated, one side derived.

**Example 5 -- measuring MDF on the right range.** Kuhn's bet is 1 into a pot of 2, so `minimum defense frequency = pot/(pot+bet) = 2/3`. Using the artifact's rows, two different "defense frequencies" can be computed:

| What is being measured | Who | Value | Versus MDF |
|---|---|---|---|
| Whole reaching range, dominated `J` included | P0 at node 2 | 0.422388 | looks far below 2/3 |
| Whole reaching range, dominated `J` included | P1 at node 3 | 0.291672 | looks far below 2/3 |
| The sub-range that actually faces a bluff | P0 (`Q` and `K`, reach-weighted) | 0.666711 | equals 2/3 (gap 4.4e-5) |
| The sub-range that actually faces a bluff | P1 (`Q` and `K`, equal weights) | 0.666683 | equals 2/3 (gap 1.6e-5) |

The formula does not fail; the object was wrong. **Card removal**: when I bluff the jack, the opponent cannot also hold the jack, so that cell is not in the range facing the bluff at all. Drop the dominated cells from the denominator and MDF holds exactly -- the fold frequencies actually facing a bluff are 0.333289 and 0.333317, against the `bet/(pot+bet) = 1/3` a bluff needs.

```bash
PYTHONPATH=src python -c "
import json
rep=json.load(open('data/gen/solver/kuhn.json',encoding='utf-8'))['average_strategy']
a=rep['0:0:J']['bet']; k=rep['0:0:K']['bet']; c=rep['2:0:Q']['call']; b=rep['3:1:Q']['call']
print('P0 bluff-facing defence', (c+(1-k))/(1+(1-k)), 'P1 bluff-facing defence', (b+1)/2)
print('P0 aggregate defence', (c+(1-k))/((1-a)+1+(1-k)), 'P1 aggregate defence', ((a+k)*b+a)/(k+(a+k)+a))"
```

This is the seam between this lesson and chapter 02: `02-03` says MDF is a floor on a *total* frequency; Kuhn adds "say which range the total is weighted over first". The same trap exists in real postflop charts, and nobody asks the question before copying the number.

## 生成表 / Generated tables

Kuhn's family pins the bluff-to-value mix at 1 : 3, which is exactly the size relation:

<!-- BEGIN AUTO:table.02-04.bluff-value-ratio -->
|    Size | Bluff share of betting range | Value : bluff |
|---:|---:|:---:|
| 1/4 pot |                       16.67% |     5 : 1     |
| 1/3 pot |                       20.00% |     4 : 1     |
| 1/2 pot |                       25.00% |     3 : 1     |
| 2/3 pot |                       28.57% |    2.5 : 1    |
| 3/4 pot |                       30.00% |   2.33 : 1    |
|  1x pot |                       33.33% |     2 : 1     |
| 3/2 pot |                       37.50% |   1.67 : 1    |
|  2x pot |                       40.00% |    1.5 : 1    |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#bluff_fraction_at_indifference`

<!-- generated by: tools/gen_tables.py from pokergto.odds::sizing_table -->
<!-- END AUTO:table.02-04.bluff-value-ratio -->

How to read it: the `1/2 pot` row *is* Kuhn's structure -- bluffs are 25% of the opening range, value to bluff 3 : 1. Sliding `alpha` changes the two frequencies individually and never this ratio. So the correct use of "I read 0.2133 and 0.6399" is to form the ratio first (about 3.0), compare it against this table, and only then decide whether the row is even testable.

## 实战牌局 / Live hands

Two hands: the first plays one Kuhn deal to the terminal, frequencies taken from the artifact; the second carries the "relations, not rows" discipline into a real river spot.

**Hand 1 (`hand.08-03-kuhn-king-versus-queen`) -- deal 5: P0 holds `K`, P1 holds `Q`.**

| Step | Node | Information set | Frequencies (`kuhn.json`) | Note |
|---|---|---|---|---|
| 1 | 0 | `0:0:K` | bet 0.639918 / check 0.360082 | the king checks 36% of the time |
| 2a | 3 | `3:1:Q` | fold 0.666635 / call 0.333365 | if P0 opens, `beta = 1/3` |
| 2b | 1 | `1:1:Q` | check 1.0 | if P0 checks, P1's queen checks back to showdown |

- Opening and getting called ends at node 8 with payoff `+2` (`terminal_p1_calls = winner*2`); opening and being folded to ends at node 7 with `+1`; check-check ends at node 4 with `+1`.
- Looked at one deal at a time, opening is better here: `0.333365*2 + 0.666635*1 = 1.333365` versus `1.000000`. The other deal in the same row (deal 4, where P1 holds `J`) runs the opposite way: checking gives `0.666654*1 + 0.333346*2 = 1.333346` versus opening's `1.000000`.
- **Averaged over the two deals -- which is what the row `0:0:K` is -- they cancel**: opening `1.166683`, checking `1.166673`, difference `1.0e-05`, the same magnitude as that run's residual exploitability `1.08333e-05`. Reproduce it:

```bash
PYTHONPATH=src python -c "
import numpy as np, json
from pokergto.solver.games import kuhn
from pokergto.solver.tree import TerminalNode
t=kuhn(1.0); rep=json.load(open('data/gen/solver/kuhn.json',encoding='utf-8'))['average_strategy']
row=[None]*t.n_infosets
for l,i in {l:i for i,l in enumerate(t.infoset_labels)}.items():
    acts=[n.actions for n in t.nodes if getattr(n,'infosets',None) is not None and i in set(int(x) for x in np.unique(n.infosets))][0]
    row[i]=[rep[l][a] for a in acts]
def u(node,deal,p=0):
    n=t.nodes[node]
    if isinstance(n,TerminalNode): return float(n.payoff[deal]) if p==0 else -float(n.payoff[deal])
    s=row[int(n.infosets[deal])]; return sum(s[a]*u(c,deal,p) for a,c in enumerate(n.children))
print('bet', (u(3,4)+u(3,5))/2, 'check', (u(1,4)+u(1,5))/2)"
# bet 1.1666825 check 1.166673
```

- That is the direct proof that "the king bets only 64%" is legitimate: **indifference lives at the information set, not inside one deal.** On one deal opening is clearly better by 0.333; on the other it is clearly worse by 0.333; the row nets zero. Anyone claiming a solver "says the king should always bet" should first explain the sign flip between those two deals.

**Hand 2 (`hand.08-03-real-river-value-frequency`) -- heads up, river `Kh9d6s4h2c`, pot 24. You hold either the nut flush or air; the opponent holds one bluff-catcher.**

Scenario (`reference`: an example built by the author, not output from any solver): you bet 12 (half pot) on the river.

- The textbook question -- "should the nuts bet 100%?" -- gets a Kuhn answer: **not necessarily, and this is a balance question rather than a principle.** In Kuhn the king's opening frequency `kappa` is dragged below 1 by `kappa = 3*alpha`, because the opponent's queen needs only one third of a call to make our bluff indifferent. Change the size or the bluff frequency and the value frequency moves with it.
- Two hard statements do transfer: (a) once balanced, the value-to-bluff mix is set by the size -- the `1/2 pot` row of `table.02-04.bluff-value-ratio` says 3 : 1; (b) facing a bet, calling with the strongest hand is strictly dominant and calling with the weakest is strictly dominated (Kuhn: `2:0:K` = 1.0, `2:0:J` = 0; the artifact satisfies both inside a 1e-3 tolerance).
- What does not transfer: here the opponent reacts on later streets, has several sizes, and card abstraction merges information sets (08-06), so a closed relation like `kappa = 3*alpha` simply does not exist. A commercial tool reporting "shove the nuts 62%" may equally be reporting an equilibrium selection or an unfinished run -- the checklist that tells them apart is in 08-04; this lesson only states the problem.

## 范围图 / Range chart

Nothing is embedded here: `data/gen/ranges/` contains only chapter 02's MDF floor chart, and Kuhn's "range chart" is a three-row table anyway -- `J` opens 0.213282, `Q` opens 0.0, `K` opens 0.639918 (`data/gen/solver/kuhn.json`). Painting that as colour adds no information and invites the reader to see a strength shape that does not exist.

The habit to train is a different reading order: **shape first, then numbers, and always ask what fixes each one.** In this lesson the shape entries are assertable -- `0:0:Q = 0`, `2:0:J = 0`, `2:0:K = 1`, `3:1:J = 0`, `3:1:K = 1` -- because dominance locks them. The numbers (`0.2133`, `0.6399`, `0.5467`) are neither: they are one point on a line.

## 为何成立、何时失效 / Why it works, when it breaks

**Why 64% is a legitimate answer.** Three things hold at once: (1) it satisfies `kappa = 3*alpha` to within 7.2e-5, the same order as the residual exploitability; (2) on that profile the king's two actions differ by 1e-05 in counterfactual value, i.e. it really is indifferent (hand 1's command); (3) the whole profile scores exploitability `1.08e-05` under the gate `5e-05`, and game value `-0.055556` against `-1/18` -- all five entries of `checks` in `data/gen/solver/kuhn.json` read `pass: true`.

**Why the registry asserts no opening frequency.** Kuhn's four assertions are: game value `-1/18`; calling the king facing a bet = 1; calling the jack facing a bet = 0; jack opening frequency inside `[0, 1/3]` (kind `frequency_bounds`, a membership test, not a value test). `assert_jack_bluff_in_family` says it outright: demanding one member would test the implementation's trajectory rather than game theory. It also explains the discrepancy between `games.py`'s docstring and the artifact -- the docstring's "player 0 bets the king always" is the `alpha = 1/3` corner, whereas this run sits at `0.639918`, and `proofs.py#KUHN` records that in its `notes` instead of hiding it. The same docstring hands "calls the queen at frequency `alpha + 1/3`" to player 1; in the artifact that row is **P0's** `2:0:Q` (0.5467 = 1/3 + alpha), while P1's `3:1:Q` reads 0.333365. Nothing in `checks` asserts `alpha + 1/3` at all -- when a docstring and a generated artifact disagree, the artifact plus the registered assertions are what this chapter teaches you to read.

**Where these conclusions stop:**

1. **Games that are not a family.** Change sizes, streets or player count and the equilibrium may collapse to a point (then copying frequencies is legitimate) or stay a line (then copying is wrong). The test is not somebody's chart: it is whether you can write an indifference condition that pins that row.
2. **After abstraction.** Card abstraction merges information sets, so `alpha` and `kappa` get coarser meanings; 08-06 discusses the direction of the bias.
3. **Scale.** 6 deals, 12 rows and 20,000 iterations solve exactly; a real postflop tree does not, and this project cut the 6-max postflop solver outright (`adr/0002`, Rule B). Leduc is the middle case and it is here now: 360 deals and 3,780 rows, where this file's per-deal recursion needs about 0.23 s per iteration and the public-tree form needs 0.003 s. Read `08-04` for what gates it, because there is no `-1/18` to compare it against.
4. **Transfers:** indifference sets frequencies; single rows can be unidentifiable while relations are; a profile can carry the right game value and still be exploitable. **Does not transfer:** Kuhn's digits, and "the jack's bluff frequency is always free", a symmetry that exists only with three cards.

## 陷阱 / Common mistakes

1. **Treating a converged row as a theorem.** "The solver says bet the king 64%", copied into notes -- or into the opposite mistake, "the solver must be broken, everyone knows you always bet the king".
   *Cost*, computed on the spot: splice the corner's `kappa = 1` onto the interior's `alpha = 0.213282` and the profile scores exploitability **0.030002 chips per hand** while its game value stays `-0.055554`. Copy the wrong member and the value check never fires; only the exploitability check does. At 0.030 chips per hand, 100 hands is 3.0 chips.
2. **Solving balance with priors instead of counterfactual weights.** Using "after P0 checks, the opponent is equally likely to hold Q or K" gives `c = 1/3`; reach-weighting (`Q` checks at 1, `K` checks at `1 - kappa`) gives `c = 1/3 + alpha = 0.5466`.
   *Cost*: substitute `c = 1/3` into relation 3's left side and P1's jack bluff gains `+0.639918` per unit frequency over checking (that is `+0.1067` once the 1/6 deal weight is applied) -- exactly `kappa`. So P0's 0.2133 shortfall in defense turns the opponent's air into a machine. Chapter 02's "defend below MDF and you print money" is an arithmetic statement, and here it is measurable.
3. **Checking only the shape, ignoring what fixes each cell.** `0:0:Q = 0` follows from dominance; `3:1:Q = 1/3` follows from indifference; `0:0:K = 0.64` follows from neither.
   *Cost*: three different confidence levels read as one, and money gets placed on the least reliable cell. The registry writes its assertions along exactly those three boundaries so that a reader can keep them apart.
4. **Equating small exploitability with "every row has converged".** Along a family the rows trade off against each other: `alpha = 0`, `0.1`, `0.213282` and `1/3` all score exploitability at the 1e-17 level (verified with the `fam(a)` command).
   *Cost*: believing that 10x more iterations will reveal the "true" `0.2133`. It will not -- that number is the run's current position on the line. Watch the residuals of the *relations*, not of the frequencies.

## 练习 / Drills

- Reproduce example 1's eight ledgers:
  `PYTHONPATH=src python -c "import numpy as np; from pokergto.solver.games import kuhn; from pokergto.solver.cfr import CFRSolver; t=kuhn(1.0); idx={l:i for i,l in enumerate(t.infoset_labels)}; s=CFRSolver(t, plus=True); [print(it, [ (l, np.round(s.regrets[idx[l]],4), np.round(s.current_strategy()[idx[l]],3)) for l in ('0:0:J','0:0:K','3:1:Q') ]) or (s.step(0), s.step(1)) for it in range(1,9)]"`
- Run the `fam(a)` command from the Derivation with `alpha` in `{0, 0.05, 0.2, 0.3, 1/3}` and confirm every member scores exploitability at numerical zero.
- From the artifact, `c = 0.5467` and `kappa = 0.639918`: compute `2 - 3c` and `1 - kappa`. They should match (0.359900 versus 0.360082, gap 1.8e-4) -- that identity *is* relation 3.
- Recompute the ratio yourself: `0.213282/(0.213282+0.639918)` and `0.639918/0.213282`, then compare with the `1/2 pot` row of `table.02-04.bluff-value-ratio`.

## 自测清单 / Self-check

- [ ] I can write Kuhn's four family relations and show that `alpha <= 1/3` comes from `kappa <= 1`.
- [ ] I can defend "the king opens about 64%" with two numeric pieces of evidence.
- [ ] I can say why the artifact's `checks` contain no opening-frequency assertion, only a membership test.
- [ ] I can quote the corner-plus-interior hybrid: exploitability 0.030002 chips per hand, game value still `-1/18`.
- [ ] Reading solver output, I separate shape from numbers and test relations instead of copying rows.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Frequencies are taken verbatim from the artifact; the family, the hybrid exploitability and the iteration-1 to 8 ledgers were computed for this lesson (commands inline).

| Content | Source type | Location |
|---|---|---|
| Kuhn's 12 average-strategy rows, value and exploitability | `derived` | `data/gen/solver/kuhn.json` (CFR+, 20,000 iterations, `seed: 0`, `timing_seconds: null`) |
| Assertions on the family and dominance; the reason no opening frequency is asserted | `derived` | `src/pokergto/solver/proofs.py#KUHN` (with `notes`) and `assert_jack_bluff_in_family` |
| Two frequency attributions in `games.py`'s docstring | **UNVERIFIED** | inconsistent with `data/gen/solver/kuhn.json`: "bets the king always" holds only at the `alpha = 1/3` corner, and the `alpha + 1/3` cell is P0's `2:0:Q` in the artifact while P1's `3:1:Q` is 1/3. `checks` asserts neither |
| `kappa = 3*alpha`, `c = 1/3 + alpha`, `beta = 1/3`, `g = 1/3` | `derived` | Derivation above, verified by its command |
| Family members at exploitability about 1e-17, value -0.055555556 | `derived` | the `fam(a)` command above |
| Hybrid (interior alpha, corner kappa) exploitability 0.030002 | `derived` | computed on the spot: set `0:0:K` to `(check 0, bet 1)` in the artifact rows, then call `exploitability` |
| Ledgers and current/average rows for iterations 1-8 | `derived` | `src/pokergto/solver/cfr.py#CFRSolver`; drill 1 |
| Half-pot bluff share 25% and 3 : 1 | `derived` | `data/gen/tables/table.02-04.bluff-value-ratio.json` |
| MDF 2/3 versus measured 0.666711 / 0.666683 | `derived` | `pokergto.odds#minimum_defense_frequency` plus the example 5 command on artifact rows |
| `-1/18` as a published result | `external` (mathematics, public-domain) | Kuhn (1953): the game value and the shape of the family. Only values are taken, never an expression. Note: `data/src/licensing_manifest.yaml` does not exist yet, so this lesson cites the value through `derived` recomputation in `proofs.py` rather than as a manifest-backed external artifact |
| The real river scenario in hand 2 | `reference` + **UNVERIFIED** | author-built illustration; its only checkable quantities (3 : 1, 25%) come from the `derived` table above |

## 术语 / Terms

<!-- terms: kuhn, cfr, regret-matching, information-set, strategy-profile, indifference, mixed-strategy, bluff-to-value-ratio, minimum-defense-frequency, exploitability -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | Kuhn 博弈 | Kuhn poker | the name stays Latin; this chapter's acceptance test |
| CFR | 反事实遗憾最小化 | counterfactual regret minimization | the algorithm that produced the 12 rows |
| — | 遗憾匹配 | regret matching | the ledger -> frequency step |
| — | 信息集 | information set | one of the 12 rows |
| — | 策略组合 | strategy profile | all 12 rows; splice a corner in and it is no longer an equilibrium |
| — | 混合策略 | mixed strategy | the frequencies inside a row |
| — | 无差别 | indifference | the mechanism that creates the family |
| — | 诈唬与价值比 | bluff-to-value ratio | the family invariant: 3 : 1 |
| MDF | 最低防守频率 | minimum defense frequency | in Kuhn measure it on the range that actually faces the bluffs |
| — | 可剥削度 | exploitability | the only gate that catches a copied member |
