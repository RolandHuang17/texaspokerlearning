# Who governs the size: frequency logic against range logic

<!-- hands: 2 -->
<!-- terms: frequency-approach,range-approach,betting-frequency,checking-frequency,bet-size,minimum-defense-frequency,fold-frequency,indifference,value-bet,bluff,combos,nut-advantage,capped-range -->

## 本节目标 / Objectives

- Write down and verify by hand the closed form `EV(bet) − EV(check) = f·p·(1−e) + (1−f)·b·(2e−1)`, and say which term belongs to frequency logic and which to range logic.
- Given any (size, opponent fold frequency) pair, state which `break_even_equity_to_bet` regime (`above` / `below` / `all` / `none`) you are in and what slice of the range that says should bet.
- Point at three conclusions in the generated tables that follow from frequency alone, and two that require range composition, and explain why they are not the same kind of statement.

## 前置知识 / Prerequisites

- `02-03` minimum defense frequency (MDF): `MDF = p/(p+b)`, and the fact that it is the complement of the fold frequency a bluff needs, not a hand threshold.
- `02-04` indifference: the value-to-bluff mix is set by the size, computed in `table.02-04.bluff-value-ratio`.
- `03-02` capped range: `is_capped` answers only "does this line contain the nuts". It governs the credibility of a threat, not the arithmetic of a size.

## 核心原理 / The principle

Between the two actions available on one street (bet / check), the size is decided by two independent questions: **frequency decides whether a size is usable at all, and hand strength decides which slice of the range is entitled to use it.** Written as one equation, the expected-value gap between betting and checking is `f·p·(1−e) + (1−f)·b·(2e−1)`: the first term contains only size and fold frequency, the second only size and equity. This is a `derived` claim: it follows from four definitions in `pokergto.ev` and depends on no solver, no chart, no authority.

<!-- provenance: kind=derived verified=true -->
> Derived at: `src/pokergto/ev.py#ev_bet` and `src/pokergto/ev.py#break_even_equity_to_bet`; every branch of the closed form is re-checked by bisection in `tests/test_ev.py`.

## 推导 / Derivation

Every symbol is defined before it is used: `p` is the money in the middle **before** the actor adds anything, `b` is what the actor adds, `f` is the probability that **every** opponent folds (a declared input -- see the provenance section), `e` is hero's equity when the money goes in. Folding is the reference point, so money already in the pot cancels out of every difference.

### Step one: what each action is worth

```
EV(bet)   = f·p + (1−f)·( e·(p + 2b) − b )
EV(check) = e·p
```

### Step two: take the difference and split it in half

```
EV(bet) − EV(check) = f·p − f·e·p + (1−f)·b·(2e − 1)
                    = f·p·(1−e)  +  (1−f)·b·(2e−1)
                      └ frequency ┘   └ range ┘
```

The frequency term `f·p·(1−e)` is "what I collect when they fold"; it moves with size and fold rate only. The range term `(1−f)·b·(2e−1)` is "what happens when I get called", and its **sign depends only on whether `e` is above or below `1/2`**. That is the hinge of the whole sizing theory: with `e > 1/2` it is positive and bigger is better, with `e < 1/2` it is negative and smaller is better, and at `e = 1/2` the size carries no information at all. Measured in the engine: at `p=6, b=2, f=1/4`, a hand with `e = 1/2` gains exactly `+0.75bb` at all three sizes 2bb, 6bb and 12bb.

### Step three: solve for the threshold, and ask the sign before dividing

Setting the difference to zero gives `e·D = N` with

```
D = 2b(1−f) − f·p        N = (1−f)b − f·p        e* = N / D
```

**This is the step that can fail: dividing by `D` requires asking its sign first.** When `D > 0`, "betting is better" reads `e ≥ e*` (the value region); when `D < 0` the whole inequality flips and reads `e ≤ e*` (the bluff region). `break_even_equity_to_bet` returns the sign as the `regime` field precisely so that no lesson can bury it in a footnote. Two boundaries you can compute by hand:

```
f = b/(p+b)   (the opponent defends exactly MDF)  ->  N = 0  ->  e* = 0        air is indifferent
f = 2b/(p+2b)                                     ->  D = 0  ->  regime all/none   size alone decides
```

The second boundary is reachable: at `p = 1, b = 1, f = 2/3` we get `D = 0` and `f·p − (1−f)·b = +1/3 > 0`, so the answer is `all` (`tests/test_ev.py::test_when_the_fold_frequency_is_extreme_enough_equity_stops_mattering`).

## 直觉 / Intuition

Read the equation as two sentences:

- **The frequency term is "may I bet at all".** Every size is an entry ticket and the price is the fold frequency it needs: 1/3 pot asks 25%, 2x pot asks 66.67% (`python -m pokergto odds --pot 1`). If the spot cannot supply that many folds, the size does not exist here.
- **The range term is "who bets it".** At a given size, whether `e` sits above or below `1/2` puts the hand in the "bigger is better" half or the "smaller is better" half. This is why "we have a range advantage so I bet small" is a bad inference: a range advantage does not pick a size, it picks how many hands with `e > 1/2` you own, and *those* pick the size.

Mental model: frequency logic is the **ceiling**, range logic is the **resident list**. The ceiling says how many floors the building may have; the list says who lives on each. Confusing them produces the two-sentences-that-are-each-true-but-combine-falsely genre of advice.

## 算例 / Worked examples

Every line below comes from `python -c` against `pokergto.ev`, with `f` declared.

**Example 1 -- frequency short: `p = 6bb, b = 2bb, f = 1/4`.** `break_even_equity_to_bet` returns `regime=above, e* = 0`. Gains: `e=3/4` → `+1.125bb`; `e=1/2` → `+0.75bb`; air → `0.0bb`. The size is playable by the whole range at this fold rate, yet the strong hand's gain is a multiple of the weak one's: all the size information sits in the range term.

**Example 2 -- the row where size alone decides: `p = 6bb, b = 2bb, f = 0.4`.** This is exactly the `D = 0` boundary for a 1/3-pot bet (`2·2·0.6 = 0.4·6`), the `regime=all` row of `table.04-05.bet-break-even-equity`. Measured, the gain is `+1.2bb` at `e = 0, 1/2, 3/4, 1` -- **equity does not participate at all**. Asking "should I bet my strong or my weak hands here" is meaningless; the answer is "bet everything".

**Example 3 -- the sign flips: `p = 6bb, b = 2bb, f = 0.6`.** `D = 2·2·0.4 − 0.6·6 = −2 < 0`, so `regime=below, e* = 1.4` (the table prints it as `140.0000%`). `1.4 > 1` is not an error; it means every hand satisfies `e ≤ 1.4`, i.e. bet the whole range, and the ordering is inverted: air `+2.8bb`, `e=1/2` `+1.8bb`, `e=3/4` `+1.3bb`. Weaker bets more eagerly. The bluff region is produced by the denominator changing sign.

**Example 4 -- one strong hand walking the whole ladder: `e = 3/4, p = 6bb`, each size faced with its own MDF-consistent fold rate.** Gains in bb/hand: 1/4 pot `0.9` · 1/3 pot `1.125` · 1/2 pot `1.5` · 2/3 pot `1.8` · 3/4 pot `1.928571` · pot `2.25` · 1.5x `2.7` · 2x pot `3.0` (with `EV(check) = 4.5` as the baseline). Strictly increasing -- this one-street model cannot produce "small is clever", which is the most important negation in this lesson and the reason `04-02` exists.

## 生成表 / Generated tables

The first table is the spine: each row solves `e* = ((1−f)b − f·p) / (2b(1−f) − f·p)` and re-substitutes into `ev_bet − ev_check`; the residual column is what that substitution leaves behind.

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

The second shows frequency logic eating size and nothing else: at `p = 1` the eight MDF / required-fold / call-equity figures contain no `e`.

<!-- BEGIN AUTO:table.02-03.mdf-vs-sizing -->
|    Size |    MDF | Fold freq a bluff needs | Equity to call |
|---:|---:|---:|---:|
| 1/4 pot | 80.00% |                  20.00% |         16.67% |
| 1/3 pot | 75.00% |                  25.00% |         20.00% |
| 1/2 pot | 66.67% |                  33.33% |         25.00% |
| 2/3 pot | 60.00% |                  40.00% |         28.57% |
| 3/4 pot | 57.14% |                  42.86% |         30.00% |
|  1x pot | 50.00% |                  50.00% |         33.33% |
| 3/2 pot | 40.00% |                  60.00% |         37.50% |
|  2x pot | 33.33% |                  66.67% |         40.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_tables.py from pokergto.odds::sizing_table -->
<!-- END AUTO:table.02-03.mdf-vs-sizing -->

The third is the other half of the division of labour: on the same ladder, "who can bet often" and "who can bet big" come apart -- the `As9s5d` row shows an equity edge of `+0.220466` for hero against a nut share of `0.0`. The ranges are authored illustrative inputs here, not solved strategies (recorded in `provenance.assumptions`).

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

## 实战牌局 / Live hands

**Hand 1 (`hand.04-01-strong-hand-bigger-size`) -- 6-max cash, 100bb. BTN opens 3bb, BB calls, pot 6bb. Flop `Kh7s3d`, BB checks, hero holds `AdKc`.**

- Strength: `python -m pokergto equity "AdKc" "KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s" --board "Kh7s3d"` → `0.912269` (exact enumeration). `2e−1 = 0.824538 > 0`, the range term is positive.
- Does the size exist: `python -m pokergto spr --stack 97 --pot 6` → SPR `16.167`; a 2x-pot bet is 12bb and 97bb are still behind, so 12bb is a **size**, not an all-in.
- With the declared `f = 1/4`, gains: 1/3 pot `+1.368403bb` · pot `+3.842017bb` · 2x pot `+7.552439bb` (`EV(check) = 5.473614`).
- Decision: bet big. Not because "BTN has a range advantage" -- `table.03-01`'s `Kh7s3d` row does show hero's equity edge `+0.430545` -- but because **this hand's** `e` is far above `1/2`, and the range term therefore wants `b` as large as the stacks allow.

**Hand 2 (`hand.04-01-fold-supply-flips-the-answer`) -- same table, same flop, hero now holds `QdJd`, pot 6bb.**

- Strength: the same command with `QdJd` → `0.347828`. `2e−1 = −0.304344 < 0`, the range term is negative.
- Case A, `f = 1/4`: gains are 1/3 pot `+0.521742bb` · 1/2 pot `+0.293484bb` · pot `−0.391290bb` · 2x pot `−1.760838bb`. Decision: 1/3 pot, and delete the pot-sized option; moving from 1/3 pot to pot costs `0.913` bb per hand.
- Case B, `f = 0.6` (the opponent folds far more, same size): `regime=below, e* = 1.4`; all four sizes gain, and the best is the smallest: 1/3 pot `+2.104344bb` · pot `+1.617394bb` · 2x pot `+0.886968bb`.
- The decision is still "small", but **the governing reason changed**. In A it was "my equity is below 1/2"; in B it is "the fold rate is high enough to flip the sign of the whole inequality". Same hand, same size, two different owners of the answer -- that is exactly the question in this lesson's title.

## 范围图 / Range chart

<!-- BEGIN AUTO:range.04-02.mdf-floor-vs-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | :: | .. | .. | .. |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 7 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 6 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 5 | @@ | @@ | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 4 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 3 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 2 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |

663.0 combos = 50.00% of all 1,326

Legend: `··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%; the diagonal is pairs, the upper triangle suited, the lower offsuit.

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.04-02.mdf-floor-vs-pot -->

This is the MDF floor for a pot-sized bet: combos filled in strength order until they cover `MDF = 50%` of the 1,326 starting combos, i.e. 663 combos (the `total_combos` field of `range.04-02.mdf-floor-vs-pot.json`). It is a **quota, not a list**: it says 663 combos must continue and says nothing about which. Frequency logic owns the height of that line; filling it is range logic's job, and `04-07` is about exactly that.

## 为何成立、何时失效 / Why it works, when it breaks

**Assumptions that make it hold:** one street only; showdown immediately when called; `f` and `e` given as scalars; folding valued at 0 as the reference point. All four are stated in `pokergto.ev`'s module docstring.

Where it stops being the answer:

1. **`f` is not independent of `b`.** The difference above treats `f` as an input. In a real hand `f` moves with `b`, and this engine **cannot** supply that mapping: it needs an opponent model or a solve. So Example 4's monotonicity is a conclusion "under MDF-consistent fold rates", not advice to always bet big.
2. **There are streets after the call.** In `ev_bet` a call means showdown; one street of algebra collapses every later decision into a single `e`. The multi-street version belongs to `04-04`, `04-05` and chapter 06.
3. **The defender can raise.** MDF is derived for call/fold. With raises available the total defense floor is unchanged but the *calling* frequency can sit lower (`02-03`'s break list, item 2). Read this lesson's `f` as "the probability of not facing aggression".
4. **Multiway pots.** `f` is the probability that **everyone** folds. `python -m pokergto mdf --pot 10 --bet 5 --opponents 2` → 42.27% each, 66.67% jointly. The `p` in the frequency term is still the whole pot, but winning it now costs a product of independent folds.
5. **Range composition is not in the equation, but the source of `e` is.** `e` comes from range versus range, and whether a range can even *hold* the nuts comes from `is_capped`: `table.03-02`'s `AsKsQh` pair of rows -- hero 82 combos uncapped, villain 92 combos capped -- is the kind of verdict frequency logic cannot produce.

## 陷阱 / Common mistakes

1. **"They defend MDF, so the size does not matter."** At each size's own MDF fold rate, an `e = 3/4` hand gains `0.9bb` at 1/4 pot and `3.0bb` at 2x pot (`p = 6bb`, Example 4). *Cost*: `1.875bb/hand` (1.125 at 1/3 pot against 3.0 at 2x pot). Recompute with one `python -c` call to `ev_bet`/`ev_check`.
2. **Translating "range advantage" straight into "small size".** The direction comes from `sign(2e−1)` per hand, not from the range average. At `p=6, f=1/4`: an `e=0.35` hand loses `2.25bb/hand` by using 2x pot instead of 1/3 pot; an `e=0.75` hand loses `3.75bb/hand` the other way. *Cost*: 2.25-3.75bb per hand for one wrong size, printed directly by `compare` plus `regret`.
3. **Still sorting by strength on a `regime=all` row.** 1/3 pot with `f = 0.4` is the `D = 0` line: the gain is `+1.2bb` at every equity tested. "Bet the strong ones, check the weak ones" buys exactly nothing there. *Cost*: 0bb -- but you will believe you differentiated. This row exists to force reading `table.04-05`'s `regime` column before talking about hand strength.

## 练习 / Drills

- By hand, compute `D` and `N` for `p = 1, b = 1/3`, find the `f` that makes `D = 0`, then confirm with `python -m pokergto odds --pot 1` that a 1/3-pot bet's **required fold rate is 25%** -- do not merge it with the 20% in the same row (equity needed to call, the same closed form as the bluff share but a different question).
- Sweep `f = 0.1 … 0.75` at `p=6, b=2` with `python -c`, write down the two critical points where `regime` goes `above → all → below`, and compare with `table.04-05.bet-break-even-equity`.
- Explain the difference between `e* = 200%` and `regime=all`: both mean "bet the whole range", but one is a flipped denominator and one is equity-independent. Why does the table keep them in separate columns?
- Combo check: `python -m pokergto range "22+,ATs+" --json` → 114 combos, `8.5973%`. Why must an MDF quota be combo-weighted rather than averaged over 169 classes?

## 自测清单 / Self-check

- [ ] I can write `EV(bet) − EV(check) = f·p·(1−e) + (1−f)·b·(2e−1)` from memory and say what each term governs.
- [ ] I know to ask the sign of `D` before dividing, and can state the boundary `f = 2b/(p+2b)`.
- [ ] I can explain why `e* = 1.4` does not mean "140% equity required" but "every hand qualifies".
- [ ] I can name three conclusions here that come from frequency and two that come from range composition, with their table names.
- [ ] I can list what this one-street model cannot justify, and which assumption would have to be added first.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number in this lesson is computed in this repository. No commercial solver output, no third-party range chart, no screenshot appears anywhere in it.

| Content | Source type | Location |
|---|---|---|
| Closed form and regime signs | `derived` | `src/pokergto/ev.py#break_even_equity_to_bet`; re-substitution and direction assertions in `tests/test_ev.py` |
| Size → MDF / folds needed / call equity | `derived` | `data/gen/tables/table.02-03.mdf-vs-sizing.json` |
| Size → break-even equity and regime | `derived` | `data/gen/tables/table.04-05.bet-break-even-equity.json` |
| Equity edge vs nut edge rows | `derived` | `data/gen/tables/table.03-01.equity-vs-nut-advantage.json` (ranges are illustrative inputs) |
| MDF floor quota chart | `derived` | `data/gen/ranges/range.04-02.mdf-floor-vs-pot.json` |
| Every `f` value used | declared input | **UNVERIFIED**: `table.04-05`'s own `provenance.assumptions` states that fold frequencies are declared, not measured. Everything here is a conditional answer for a stated `f`. |
| How `f` moves with `b` | **UNVERIFIED** | Nothing in this repository solves that mapping; it is chapter 08 work. |
| Enumerated ranges are not thinned by board cards | measured limitation | **UNVERIFIED**: `parse("77")` still contains `7s` combos on a `Kh7s3d` board, and both `range_equity` and `nut_advantage` count the full range (measured: `77` vs `AKo` returns `0.983838`, not `1.0`). The combo counts and nut shares in `table.03-01` are therefore upper-biased; this lesson uses their signs and comparisons, never them as exact quotas. |

## 术语 / Terms

| Abbreviation | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 频率法 | frequency-approach | the half of the equation containing only size and fold rate |
| — | 范围法 | range-approach | the half governed by `sign(2e−1)` and range composition |
| MDF | 最低防守频率 | minimum-defense-frequency | `p/(p+b)`, the `mdf_of_size` column of `table.04-05` |
| — | 弃牌频率 | fold-frequency | `f`, a declared input: everyone folds at once |
| — | 无差别 | indifference | `EV(bet) = EV(check)`, i.e. `e·D = N` |
| — | 区间 | regime | `above` / `below` / `all` / `none`, set by the sign of `D` |
| — | 组合数 | combos | the weighting unit: `AKo` 12, `AKs` 4, `AA` 6 |
| — | 封顶范围 | capped-range | the verdict of `is_capped`: a sizing input, not a hand statement |
