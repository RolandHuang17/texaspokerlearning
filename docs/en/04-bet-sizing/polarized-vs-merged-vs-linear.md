# Polarized, merged and linear: three range shapes, three sizing logics

<!-- hands: 2 -->
<!-- terms: polarized, merged, linear, value-range, bluff-range, range-approach, overbet, capacity, capped-range, bet-size -->

## 本节目标 / Objectives

- Use one inequality -- the `regime` column of `table.04-05.bet-break-even-equity` -- to show that the one-street break-even surface can only produce a top band or the whole range, never "top plus bottom with the middle empty".
- Use each size's bluff share together with the supply of value and bluff combos in hand to compute the largest block of combos that size can carry, and read the shape (merged or polarized) off that number.
- Say which half of a shape judgement is computable here (quota, capacity, nut advantage, capped test) and which half is not (the calling range at a given size, and the middling band's expectation), and mark the latter UNVERIFIED.

## 前置知识 / Prerequisites

- `04-04` the per-size quota equation and the two-size crossover equity `ē`.
- `03-01` equity advantage decides who bets often, nut advantage who bets big; `03-02` capped ranges.
- `02-04` bluff share `B/(P+2B)` and ratio `(P+B)/B`; `02-03` the combos each size forces the defender to keep.

## 核心原理 / The principle

The three shapes are not three levels of nerve. They are **three answers to where the three segments of one strength axis land**:

| Shape | Definition (strength sorted strong to weak) | Sizing logic |
|---|---|---|
| polarized | top segment bets, bottom segment bets, middle empty | only big sizes / overbets can carry it |
| merged | top and bottom adjacent, one contiguous block bets | a single small-to-medium size |
| linear | size rises monotonically with strength | the ladder itself is the strategy |

The core claim of this lesson is one auditable sentence: **`pokergto.ev`'s break-even surface gives, per size, a single first-degree inequality in equity `e`, and one inequality can cut out a top band or a bottom band -- never a union of the two.** Polarization needs a second constraint to appear, and that constraint is the per-size bluff quota plus range capacity. This is `derived`, argued below and checked by a sweep of 1592 `(size, fold frequency)` pairs, in which no row was `regime = below` with `e* ≤ 1`.

## 推导 / Derivation

`break_even_equity_to_bet(P, B, f)` solves `EV(bet) = EV(check)`:

```
e* = ( (1 − f)·B − f·P ) / ( 2B(1 − f) − f·P ),   denominator D, numerator N
```

The sign of `D` picks the regime -- the rule stated in `BreakEven`'s own docstring and re-checked branch by branch in `tests/test_ev.py`:

- `D > 0` → `above`: bet iff `e ≥ e*`, a **top band**.
- `D < 0` → `below`: the inequality flips, bet iff `e ≤ e*`.
- `D = 0` → `all / none / indifferent`: size and fold rate decide alone, `e` never enters.

**Point one: the flip does not create a "bluff only" band.** `D = 0` solves to `f = 2B/(P + 2B)`, while `N = 0` solves to `f = B/(P + B)`, and

```
B/(P+B) < 2B/(P+2B)   ⟺   P + 2B < 2P + 2B   ⟺   0 < P
```

So by the time `f` crosses the `D = 0` line -- i.e. enters `below` -- `N` is already negative: negative over negative is positive, so `e* > 0`. Solving `e* = 1` gives `N = D`, which reduces to `(1 − f)·B = 0`, i.e. only `f = 1`. Hence `e* > 1` throughout the `below` region: **it is true that weaker hands want to bet more, but no hand is excluded.** `below` means "bet the whole range", not "bet air". That is not a promise made by algebra alone: across 8 sizes × 1592 fold frequencies the count of `below` rows with `e* ≤ 1` is `0`.

**Point two: capacity picks the shape.** The largest block of combos a size can carry is

```
stall(B) = min( bluff supply A / s(B),  value supply V / (1 − s(B)) ),   s(B) = B/(P + 2B)
```

`V` and `A` come from the board (that is what `capacity` means), `s(B)` from the size. With `A, V` fixed, small sizes are value-constrained (the `V/(1−s)` bound binds first) and big sizes are bluff-constrained (the `A/s` bound binds first). **Being bluff-constrained means a block of made hands has to stay in the checking range**, so the betting range collapses into "top + bottom" with a hole in the middle. That is where polarization comes from: it is a division, not a decision.

**Point three: whether folds rise with size decides if size is monotone in strength.** Differentiating `ev_bet` in `B` with `f` held constant:

```
∂EV(bet)/∂B = (1 − f)·( 2e − 1 )
```

If `f` does not move, this says strong hands want big sizes and weak hands want small ones -- linear. At `e = 1/2` it is exactly 0, so the size is irrelevant. Polarization needs `f` to climb with `B`, and `f(B)` is an input from an opponent model, not something this repository computes.

## 直觉 / Intuition

Think of a size as the size of a stall. The bigger the stall, the fewer value hands each bluff has to bring with it (1/4 pot needs 5 : 1, 2 × pot needs only 1.5 : 1). That sounds generous, but it moves the demand to the other side: **a big stall needs more bluffs to fill its ratio, and air is finite.** When air runs out you have to leave value hands behind -- the medium made hands go to the check line -- and the betting range becomes two-ended all by itself.

Small sizes do the opposite: the ratio is strict (5 value per bluff), so you refuse to leave any value out, and the betting block runs from the nuts down through very thin value with almost no gap. That is merged.

Linear is the third case: you have enough air *and* enough nuts, and the ladder itself becomes the signal you leak. That requires the opponent's fold rate to genuinely differ by size, which is precisely the input this repository cannot verify.

## 算例 / Worked examples

**Example 1 -- where the regime flips (`P = 1`).** `f_all = 2B/(P + 2B)`:

| Size | `f_all` | just below | exactly at | just above |
|---|---|---|---|---|
| 1/3 pot | 40.00% | `above` | `all` | `below` |
| 1/2 pot | 50.00% | `above` | `all` | `below` |
| 3/4 pot | 60.00% | `above` | `all` | `below` |
| pot | 66.67% | `above` | `all` | `below` |
| 2 × pot | 80.00% | `above` | `all` | `below` |

Reproduce: `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; B=F(1,2); fa=2*B/(1+2*B); print([ev.break_even_equity_to_bet(1,B,x).regime for x in (fa-F(1,100),fa,fa+F(1,100))])"` → `['above', 'all', 'below']`. `table.04-05.bet-break-even-equity` agrees row by row: `1/2 pot` at `f = 0.5` is `all`, `1/3 pot` at `f = 0.4` is `all`.

**Example 2 -- the ladder at a constant fold rate (`P = 1, f = 0.30`).**

| `e` | 1/3 pot | 1/2 pot | 3/4 pot | pot | 2 × pot | Shape reading |
|---|---|---|---|---|---|---|
| 1.00 | 1.233333 | 1.350000 | 1.525000 | 1.700000 | 2.400000 | monotone up → linear |
| 0.50 | 0.650000 | 0.650000 | 0.650000 | 0.650000 | 0.650000 | exactly flat → size irrelevant |
| 0.00 | 0.066667 | −0.050000 | −0.225000 | −0.400000 | −1.100000 | monotone down → air wants small, not big |

The flat middle row is not luck: it is `∂EV/∂B = (1 − f)(2e − 1) = 0`. **And note what is absent: with `f` fixed, polarization never appears** -- air prefers the smallest size. Reproduce: `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print([float(ev.ev_bet(1,B,F(3,10),F(1,2))) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))])"`.

**Example 3 -- the bar rises with size at the same `f = 0.30`.** `e*` is `−0.400000 / 0.125000 / 0.300000 / 0.363636 / 0.440000` for 1/3 pot through 2 × pot. That is: **when he does not fold more, the bigger bet asks for a stronger hand.** It is the opposite of "big size means aggression", and it is one of the contradictions this lesson exists to write down.

**Example 4 -- capacity picks the shape (supply `V = 40` value + `A = 15` bluff combos, `P = 1`).**

| Size | bluff share `s(B)` | largest block | value / bluffs | leftovers |
|---|---|---|---|---|
| 1/4 pot | 16.67% | 48.0000 | 40.0 / 8.0 | 7.0 air left |
| 1/3 pot | 20.00% | 50.0000 | 40.0 / 10.0 | 5.0 air left |
| 1/2 pot | 25.00% | 53.3333 | 40.0 / 13.3333 | 1.6667 air left |
| 3/4 pot | 30.00% | 50.0000 | 35.0 / 15.0 | 5.0 value left |
| pot | 33.33% | 45.0000 | 30.0 / 15.0 | 10.0 value left |
| 2 × pot | 40.00% | 37.5000 | 22.5 / 15.0 | 17.5 value left |

Up to 1/2 pot the binding side is value: all 40 value combos bet, the block is contiguous = merged. From 3/4 pot up the binding side is air: to use 2 × pot you must keep 17.5 made hands out of the betting range, leaving "22.5 top + 15 air" = polarized, and the polarization was produced by division. Reproduce: `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds; V,A=F(40),F(15); [print(float(B), float(odds.bluff_fraction_at_indifference(1,B,exact=True)), float(min(A/odds.bluff_fraction_at_indifference(1,B,exact=True), V/(1-odds.bluff_fraction_at_indifference(1,B,exact=True))))) for B in (F(1,4),F(1,3),F(1,2),F(3,4),F(1),F(3,2),F(2))]"`.

## 生成表 / Generated tables

This lesson's foundation is that table: the break-even equity and regime for every size and fold frequency, solved in closed form by `break_even_equity_to_bet` and re-substituted row by row with `ev_bet` / `ev_check` (hence the zero `residual` column):

<!-- BEGIN AUTO:table.04-05.bet-break-even-equity -->
|    Size | Fold frequency f | MDF at this size | Break-even equity e* | Regime | Residual |
|---:|---:|---:|---:|---:|---:|
| 1/3 pot |           25.00% |         75.0000% |              0.0000% |  above |        0 |
| 1/3 pot |           40.00% |         75.0000% |                    - |    all |        - |
| 1/3 pot |           50.00% |         75.0000% |            200.0000% |  below |        0 |
| 1/3 pot |           60.00% |         75.0000% |            140.0000% |  below |        0 |
| 1/3 pot |           75.00% |         75.0000% |            114.2857% |  below |        0 |
| 1/2 pot |           25.00% |         66.6667% |             25.0000% |  above |        0 |
| 1/2 pot |           40.00% |         66.6667% |            -50.0000% |  above |        0 |
| 1/2 pot |           50.00% |         66.6667% |                    - |    all |        - |
| 1/2 pot |           60.00% |         66.6667% |            200.0000% |  below |        0 |
| 1/2 pot |           75.00% |         66.6667% |            125.0000% |  below |        0 |
| 3/4 pot |           25.00% |         57.1429% |             35.7143% |  above |        0 |
| 3/4 pot |           40.00% |         57.1429% |             10.0000% |  above |        0 |
| 3/4 pot |           50.00% |         57.1429% |            -50.0000% |  above |        0 |
| 3/4 pot |           60.00% |         57.1429% |                    - |    all |        - |
| 3/4 pot |           75.00% |         57.1429% |            150.0000% |  below |        0 |
|     pot |           25.00% |         50.0000% |             40.0000% |  above |        0 |
|     pot |           40.00% |         50.0000% |             25.0000% |  above |        0 |
|     pot |           50.00% |         50.0000% |              0.0000% |  above |        0 |
|     pot |           60.00% |         50.0000% |           -100.0000% |  above |        0 |
|     pot |           75.00% |         50.0000% |            200.0000% |  below |        0 |
|   2 pot |           25.00% |         33.3333% |             45.4545% |  above |        0 |
|   2 pot |           40.00% |         33.3333% |             40.0000% |  above |        0 |
|   2 pot |           50.00% |         33.3333% |             33.3333% |  above |        0 |
|   2 pot |           60.00% |         33.3333% |             20.0000% |  above |        0 |
|   2 pot |           75.00% |         33.3333% |           -100.0000% |  above |        0 |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.ev#break_even_equity_to_bet`

<!-- generated by: tools/gen_tables.py from pokergto.ev::break_even_equity_to_bet -->
<!-- END AUTO:table.04-05.bet-break-even-equity -->

Read the `regime = below` rows as "the direction flipped", but notice every one of them carries `break_even_equity` above 1 (`2.0`, `1.4`, `1.142857`, …): by point one they exclude no hand at all. It is the `regime = all` rows where size alone decides.

The next table is where `s(B)` in Example 4 comes from -- the quota each size demands:

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

Shape is not only about your own cards: it is about who owns the nut side. `can_bet_big` and `can_bet_often` are computed separately below, and on two of the four boards they disagree:

<!-- BEGIN AUTO:table.03-01.equity-vs-nut-advantage -->
|    Board |                       Hero range |                           Villain range |             Hero |          Villain | Hero equity | Equity edge | Hero nut share |  Nut edge | Who bets often | Who bets big |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
|   Kh7s3d |    AKs,AQs,ATs,KQs,AKo,AQo,99,77 | KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s |        CO opener |        BB caller |    71.5272% |    43.0545% |        6.8182% |   6.8182% |      hero      |     hero     |
|   9h6d3c | AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs |   87s,76s,65s,54s,T8s,T9s,98o,97o,66,55 |       BTN opener |        BB caller |    36.8154% |   -26.3691% |        4.7619% |   4.7619% |    villain     |     hero     |
|   As9s5d |     AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT |           KQs,QJs,KJs,JTs,98s,76s,99,55 |        CO opener |        BB caller |    61.0233% |    22.0466% |        0.0000% | -10.3448% |      hero      |   villain    |
| Kh7s3d4c |         AKo,AQo,ATs,KQs,99,77,44 |         KJs,QJs,JTs,T9s,98s,A5s,KQo,AJo | CO opener (turn) | BB caller (turn) |    76.9775% |    53.9550% |        7.5000% |   7.5000% |      hero      |     hero     |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.theory.range_advantage#advantage`

<!-- generated by: tools/gen_tables.py from pokergto.theory.range_advantage::advantage -->
<!-- END AUTO:table.03-01.equity-vs-nut-advantage -->

Whether a top segment exists at all is a machine test, not a debate -- `is_capped` supplies it:

<!-- BEGIN AUTO:table.03-02.capped-range-check -->
|  Board |    Role |      Combos |         Best in range |         Board ceiling | Capped? |
|---:|---:|---:|---:|---:|---:|
| Kh7s3d |    hero | 44.0 combos | three of a kind 7 K 3 | three of a kind K 7 3 |     yes |
| Kh7s3d | villain | 58.0 combos |      one pair K Q 7 3 | three of a kind K 7 3 |     yes |
| AsKsQh |    hero | 65.0 combos |            straight A |            straight A |      no |
| AsKsQh | villain | 80.0 combos |      one pair K A Q 9 |            straight A |     yes |
| 9h6d3c |    hero | 63.0 combos | three of a kind 9 6 3 | three of a kind 9 6 3 |      no |
| 9h6d3c | villain | 48.0 combos | three of a kind 6 9 3 | three of a kind 9 6 3 |     yes |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.theory.range_advantage#is_capped`

<!-- generated by: tools/gen_tables.py from pokergto.theory.range_advantage::is_capped -->
<!-- END AUTO:table.03-02.capped-range-check -->

Finally, the quota is not backed by algebra only. Five one-street toys, solved independently at five different sizes, reproduce the closed forms to within these gaps:

<!-- BEGIN AUTO:table.08-04.solver-vs-algebra -->
|        Size | Solved defence | Algebraic MDF | Solved bluff share | Algebraic bluff share | Exploitability (chips/hand) |
|---:|---:|---:|---:|---:|---:|
| 0.5000x pot |         66.67% |        66.67% |             25.00% |                25.00% |              0.000001 chips |
| 0.3333x pot |         75.01% |        75.00% |             20.00% |                20.00% |              0.000014 chips |
| 1.0000x pot |         50.01% |        50.00% |             33.34% |                33.33% |              0.000043 chips |
| 0.7500x pot |         57.16% |        57.14% |             30.02% |                30.00% |              0.000098 chips |
| 2.0000x pot |         33.33% |        33.33% |             40.00% |                40.00% |              0.000008 chips |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `src/pokergto/solver/proofs.py#PUBLISHED_PROOFS`

<!-- generated by: tools/gen_tables.py from pokergto.solver.cfr::solve -->
<!-- END AUTO:table.08-04.solver-vs-algebra -->

## 实战牌局 / Live hands

**Hand 1 (`hand.04-05-polarized-river`) -- river `Kh7s3d8c6d`, pot 100 bb, hero raised from CO and owns the nut advantage, supply 40 value combos + 15 air combos, size set {1/3 pot, 2 × pot}.**

- Capacity: a 2 × pot bet demands `s = 40.00%` bluffs, so `stall(2x) = min(15/0.4, 40/0.6) = 37.5` combos, i.e. 22.5 value + 15 air. The remaining 17.5 value combos **must not be in it**.
- Decision: bet 2 × pot with the top 22.5 plus all 15 air. Filling the stall to 50 combos would need 20 bluffs and there are only 15, so the missing 5 get patched with middling made hands -- at which point the shape is no longer polarized, it is "the middle bets 2 × pot".
- Cost (computed): a middling hand with `e = 0.35` against `f = 0.30` scores `EV(2 × pot) = 12.5000`, `EV(check) = 35.0000`, `EV(1/3 pot) = 47.5000` at `P = 100`; `ev.compare` ranks them and `ev.regret` reports 35.0000 chips lost relative to the best.
- The shape here is counted, not chosen: the `Kh7s3d` row of `table.03-01.equity-vs-nut-advantage` gives `can_bet_big = hero` (`nut_edge = 0.115385`), and the 2 × pot row of `table.04-05.bet-break-even-equity` at `f = 0.25` gives `e* = 0.454545`, i.e. a high bar only the top clears.

**Hand 2 (`hand.04-05-merged-flop`) -- flop `9h6d3c`, pot 20 bb, same supply of 40 value + 15 air, opponent folding at the theoretical rate for a 1/3-pot bet (`f = 25%`).**

- Capacity: `stall(1/3 pot) = min(15/0.2, 40/0.8) = 50` combos = 40 value + 10 bluffs, with 5 air left for the check line. Every value hand including the thinnest is inside the betting block, contiguous = merged.
- Threshold check: at `f = 0.25` the 1/3-pot row gives `e* = 0` (first row of `table.04-05.bet-break-even-equity`). **That is both a licence and a warning**: `e* = 0` says no bet is worse than checking, and it also says the threshold selected nothing about shape -- the shape came from the capacity division one line above.
- Decision: use one size, 1/3 pot, rather than {1/3 pot, 2 × pot}: 2 × pot is bluff-constrained here (capped at 37.5 combos) while 1/3 pot holds 50, so moving value into the size that cannot carry it takes money out of the betting range.
- Cost of the mistake: the `e = 0.35` middle scores `47.5000` at 1/3 pot and `12.5000` at 2 × pot (same command as Hand 1), a gap of `35.0000` chips. That is not a difference of taste about size, it is the expectation of one hand under one stated fold rate.

## 范围图 / Range chart

How hard a big size squeezes the defender's range is one reason polarization looks reasonable -- he only has to keep a third of everything:

<!-- BEGIN AUTO:range.04-02.mdf-floor-vs-two-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. |
| 7 | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 6 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 5 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 4 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 3 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 2 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |

442.0 combos = 33.33% of all 1,326

Legend: `··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%; the diagonal is pairs, the upper triangle suited, the lower offsuit.

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.04-02.mdf-floor-vs-two-pot -->

Those 442 combos (33.33%) are a floor, not a solution: `pokergto.odds` constrains the total frequency only, and the chart fills it strongest-first (its own `assumptions` say so). So the chart proves "a big size narrows defence"; it cannot prove "my betting range should be two-ended". The second claim needs the calling range at each size, which this repository does not have -- see the next section and the provenance table.

## 为何成立、何时失效 / Why it works, when it breaks

**Premises**: the strength axis can be sorted by one scalar `e`; each size's bluff share obeys the indifference condition `s(B) = B/(P+2B)`; the supplies `V, A` are given; and `f` and `e` do not move with size within an example (point three uses exactly that as its limiting case).

**Where it breaks**:

1. **`e` is "equity when called", and the calling range changes with size.** Polarization is defined by "the middle dies at this size against a stronger calling range", which demands **a calling range per size**. This repository cannot produce one: `02-07` treats `q` as an input and `04-01`'s range logic treats range structure as an input. So "this band gets worse at this size" is **`reference` + UNVERIFIED**; the path to verifying it is per-size calling ranges in `data/src/spots/*.yaml`, counted with `poker range` plus `pokergto.cards.remove_cards` and evaluated with `poker equity`.
2. **A one-street model cannot deliver multi-street pressure.** Merged shapes are often propped up by "I still get to bet the next street". Leduc does have that second street and is solved (`data/gen/solver/leduc.json`), so the structure exists in this repository now -- but it is a six-card game with one size per street and no board development, which is not the later street whose equity this lesson's turn card creates. Every closed form used below is still one-street only.
3. **The relation between `f` and `B` is an input.** Example 2's flat row, and the absence of polarization, both rest on holding `f` fixed. Real opponents fold more facing 2 × pot; `f(B)` increasing is common sense but is not verified here.
4. **`regime = below` is widely misread.** Point one proves `e* > 1` throughout, so "below means bet air" is false; it means bet everything. Any "proof of polarization" built on that reading is void.
5. **Multiway pots**: both `s(B)` and `f` change with player count (`pokergto.theory.multiway`), so the shape discussion has to be reopened.

## 陷阱 / Common mistakes

1. **Reading `regime = below` as "bluff here".** In that region `e* > 1` (point one; 0 exceptions in a 1592-row sweep), so nothing is excluded: the correct reading is "bet the whole range".
   *Cost*: replacing value betting with air whenever the opponent folds a lot, while Example 3 shows the same fold rate demands `e* = 0.44` at the big size.
2. **Classifying shapes with adjectives instead of the capacity division.** "This hand suits an overbet" carries no content; `stall(B) = min(A/s, V/(1−s))` does.
   *Cost*: Hand 1 -- filling 50 combos at 2 × pot needs 20 bluffs when 15 exist, and patching 5 with middling hands costs 35.0000 chips per hand (`EV(2 × pot) = 12.5` against `EV(1/3 pot) = 47.5`).
3. **Assuming nut-richness alone licenses polarization.** Having a top end is necessary, not sufficient: two rows of `table.03-02.capped-range-check` show `is_capped = true`, i.e. that line has no top at all, and an overbet loses its basis.
   *Cost*: betting big with a capped range means you cannot answer with a raise; `range.04-02.mdf-floor-vs-two-pot` only owes 442 continuing combos, and all of them are hands you cannot beat.
4. **Treating shape as a by-product once sizes are chosen.** Example 2 shows size and shape are two solutions of the same constraint system: with `f` fixed the ladder is linear, and polarization only enters once `f` climbs with `B` -- and `f(B)` is an input.
   *Cost*: defining "polarized = bet big" yields, against an MDF-defending opponent, the vacuous result that air scores exactly 0 at every size, which teaches nothing.

## 练习 / Drills

- Reproduce point one's sweep (answer: `1592 0` -- 1592 rows scanned, 0 of them `below` with `e* ≤ 1`): `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; sizes=[F(1,4),F(1,3),F(1,2),F(2,3),F(3,4),F(1),F(3,2),F(2)]; pairs=[(B,2*B/(1+2*B)+F(k,1000)) for B in sizes for k in range(1,200) if 2*B/(1+2*B)+F(k,1000)<1]; print(len(pairs), sum(1 for B,f in pairs if (be:=ev.break_even_equity_to_bet(1,B,f)).regime=='below' and be.threshold is not None and be.threshold<=1))"`.
- With `P = 1, V = 40, A = 15`, compute `stall` at 3/2 pot yourself and say which side binds (answer: `s = 37.50%`, `stall = 40.0000`, bluff-constrained, 15 bluffs and 25 value).
- Write `∂EV/∂B` for the three equities in Example 2, explain why the `e = 1/2` row must be exactly flat (all five sizes at `0.65`), and confirm `EV(check)` is `0.5`.
- From `table.08-04.solver-vs-algebra`, read the 2 × pot row: solved bluff share `0.399993` against the closed form `0.4`, solved defence `0.333323` against `0.333333`; then explain why this toy cannot settle shape questions (one size and three hand types per game).

## 自测清单 / Self-check

- [ ] I can write the closed form for `e*` and state the order of the `D = 0` and `N = 0` lines.
- [ ] I can prove `e* > 1` whenever the regime is `below`, and say in one sentence why that is not "bet air".
- [ ] I can decide whether a size is value- or bluff-constrained with `stall(B) = min(A/s, V/(1−s))` and read the shape off the leftovers.
- [ ] I can name the non-computable quantity hidden in the definition of polarization (the per-size calling range) and give the concrete path to making it checkable.
- [ ] I can separate `can_bet_often` from `can_bet_big` and say which one to trust when they disagree.

## 来源与置信度 / Provenance and confidence

Every regime, threshold, expectation and capacity division here is computed in this repository. `V = 40`, `A = 15`, `f = 0.30` and `f = 0.25` are authored model inputs. No commercial solver range or strategy table is used; the solver data cited is produced and validated in this repository.

| Content | Source type | Location / reproduce with |
|---|---|---|
| `e*` closed form, regime branches, `residual = 0` | `derived` | `data/gen/tables/table.04-05.bet-break-even-equity.json`; `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(ev.break_even_equity_to_bet(1,F(1,2),F(1,2)))"`; branch-by-branch substitution in `tests/test_ev.py` |
| Example 1's five `f_all` rows and the three-state sequence | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; [print(float(B), float(2*B/(1+2*B)), [ev.break_even_equity_to_bet(1,B,x).regime for x in (2*B/(1+2*B)-F(1,100), 2*B/(1+2*B), 2*B/(1+2*B)+F(1,100))]) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))]"` |
| Example 2's flat row and both monotone ladders | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print([[round(float(ev.ev_bet(1,B,F(3,10),F(e))),6) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))] for e in (F(1),F(1,2),0)])"` |
| Example 3's `e*` rising from −0.4 to 0.44 | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print([None if ev.break_even_equity_to_bet(1,B,F(3,10)).threshold is None else round(float(ev.break_even_equity_to_bet(1,B,F(3,10)).threshold),6) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))])"` |
| Example 4's six `stall` rows and leftovers | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds; V,A=F(40),F(15); [print(float(B), float(odds.bluff_fraction_at_indifference(1,B,exact=True)), float(min(A/odds.bluff_fraction_at_indifference(1,B,exact=True), V/(1-odds.bluff_fraction_at_indifference(1,B,exact=True))))) for B in (F(1,4),F(1,3),F(1,2),F(3,4),F(1),F(3,2),F(2))]"` |
| Hand 1 / 2's `12.5`, `35.0`, `47.5` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; rows=ev.compare(100,[('check',0),('1/3 pot',100/3),('2x pot',200)],fold_frequencies={'check':0,'1/3 pot':F(3,10),'2x pot':F(3,10)},equities_when_called={'check':F(35,100),'1/3 pot':F(35,100),'2x pot':F(35,100)}); print([(r.action, round(r.ev,4)) for r in rows], ev.regret(rows))"` |
| Point one's "1592 rows, 0 exceptions" sweep | `derived` | the command in the first drill, written out in plain `python -c` rather than taken from an artifact |
| `V = 40 / A = 15`, `f = 0.30 / 0.25`, and how the supply distributes on a board | `reference` + **UNVERIFIED** | authored model inputs, no card-removal correction; verification path as in `04-04` |
| "The middle dies at this size against a stronger calling range" (the definitional term of polarization) | no artifact → **UNVERIFIED** | needs per-size calling ranges: `data/src/spots/*.yaml` + `poker equity`; nothing in this repository computes a calling range from a size |
| Multi-street pressure supporting a merged shape | no artifact → **UNVERIFIED** | no two-street game solved here (`docs/development/solver-proof-policy.md`) |
| Solved frequencies against the closed forms at five sizes | `derived` | `data/gen/tables/table.08-04.solver-vs-algebra.json`, artifacts `data/gen/solver/toy_1street_*.json`, registry `src/pokergto/solver/proofs.py` |

## 术语 / Terms

<!-- terms: polarized, merged, linear, value-range, bluff-range, range-approach, overbet, capacity, capped-range, bet-size -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 极化 | polarized | top plus bottom bet, middle empty; produced by a bluff-constrained capacity |
| — | 合并 | merged | value and bluff segments contiguous; the value-constrained small size |
| — | 线性 | linear | size monotone in strength; the limiting shape when `f` does not move |
| — | 价值范围 | value range | supply `V`, taken as 40 combos here |
| — | 诈唬范围 | bluff range | supply `A`, taken as 15 combos here; `s(B)` decides whether it fills a size |
| — | 范围法 | range-based sizing logic | the route where range shape and capacity set the size; this lesson is its arithmetic |
| — | 超池下注 | overbet | `B > P`; here first of all a quota demand (40% bluffs) |
| — | 牌型容量 | capacity | how many strong hands and how much air a range can hold, i.e. `V` and `A` |
| — | 封顶范围 | capped range | a range with no top end; `is_capped` is the machine test |
| — | 下注尺度 | bet size | `B`; `s(B)`, `e*` and `stall(B)` are all functions of it |
