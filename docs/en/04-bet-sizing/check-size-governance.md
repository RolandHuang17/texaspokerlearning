# Governing the checking range: what a check line must still carry

<!-- hands: 2 -->
<!-- terms: checking-range, checking-frequency, minimum-defense-frequency, defend, fold-frequency, required-equity, capped-range, combos, bet-size, indifference -->

## 本节目标 / Objectives

- Use `minimum_defense_frequency` and `equity_needed_to_call` to state a checking range's required continuing combos and required folding combos, and convert both onto the 1326-combo grid.
- Use one counting test -- whether the combos below the equity threshold are numerous enough to pay the fold tax -- to decide if a check line is missing its bottom class, and price the shortfall in chips.
- Use `is_capped` to decide whether the line is missing its top class, and state what the opponent's air then collects per hand at any size.
- State that the governance function itself ("what size should the check line tolerate") does not exist in this repository (`src/pokergto/theory/__init__.py` records why it was deleted), so this lesson governs necessary conditions only.

## 前置知识 / Prerequisites

- `02-03` the MDF derivation and its complement `f = B/(P + B)`.
- `02-02` required equity `B/(P + 2B)`; `03-02` capped ranges and lines.
- `04-01` the division of labour between frequency logic and range logic; `04-05` a top segment is a precondition of shape.

## 核心原理 / The principle

A check line -- the part of your range you continue by checking -- must satisfy two things at once, and they are not the same thing:

1. **Total continuation share ≥ MDF** (`pokergto.odds.minimum_defense_frequency`). This is `derived`, and it reads the total only: `theory/frequencies.py` states in its own docstring that "defense frequency" is the share of combos that continue, while call frequency is one action's share inside it, and `defense_indifference_gap` takes a single aggregate argument.
2. **With which hands that share is filled.** MDF is completely silent about that -- the range charts say so in their `assumptions`. So a check line can pass the number and still be strategically dead.

This lesson supplies two computable tests, and they are exactly the two hand classes a check line must carry:

- **Bottom class**: combos below the threshold equity `B/(P + 2B)`, and there must be at least `(1 − MDF)·N` of them. When there are fewer, every forced fold abandons a hand whose `EV(call) > 0`, and that cost is a multiplication away.
- **Top class**: `is_capped` must be false. When it is true, the opponent's pure air takes the whole pot every time (`EV(bluff) = 1·P − 0·B = P`, independent of the size).

**The governance function "what size belongs to the check line" is not implemented here**: `src/pokergto/theory/__init__.py` lists bet-size governance among the four deliberately absent modules. Everything below is a necessary condition and a price tag, not a prescription.

## 推导 / Derivation

Let the check line hold `N` combos and face size `B` into pot `P`.

**Step one: the two thresholds.**

```
must fold:   (1 − MDF)·N = [B/(P + B)]·N
must keep:   MDF·N = [P/(P + B)]·N
fold one combo when:  EV(call) = e(P + 2B) − B < 0   ⟺   e < B/(P + 2B)
```

At `P = 1` the threshold equities are 20.00% (1/3 pot), 25.00% (half), 30.00% (3/4), 33.33% (pot) and 40.00% (2 × pot) -- the same column in `table.02-02.equity-needed-to-call` and `table.02-03.mdf-vs-sizing`.

**Step two: the price of a missing bottom.** Call `C` the number of "cheap folds", i.e. combos under the threshold. If `C ≥ (1 − MDF)·N`, the fold tax is paid entirely by air and costs `0`. If `C` is short by `n = (1 − MDF)·N − C`, those `n` folds must come from hands with `e ≥` threshold, each abandoning `e(P + 2B) − B`.

Worked: `N = 100`, `B = 1/3` pot, every hand at `e = 0.30` (no bottom at all). `C = 0`, `n = 25`, each fold gives up `0.30 × (1 + 2/3) − 1/3 = 0.166667` → `25 × 0.166667 = 4.166667` chips per 100 hands, i.e. `0.041667` per hand.

**Step three: what happens if you refuse to pay.** The opponent is not obliged to keep betting small -- he changes size. At `e = 0.30`, facing a pot-sized bet `EV(call) = 0.30 × 3 − 1 = −0.10`, facing 2 × pot `= 0.30 × 5 − 2 = −0.50`: now every hand folds, `f = 1`, and his air scores `EV(bluff) = 1 × P − 0 × B = 1.000000` -- identical at 1/3 pot, pot and 2 × pot, because with `f = 1` the size never enters the ledger. **That is precisely what the opponent collects when the bottom class is missing: one pot per attempt, size-independent.**

**Step four: a missing top class is the same sentence's other half.** `is_capped` true means the line contains no hand that can raise and none that can call the largest legal size; the opponent again reaches `f = 1` and step three's `EV(bluff) = P` applies. The difference: a missing bottom lets him **size you into folding**; a missing top lets him **collect at any size**. The test itself is `derived` -- `pokergto.theory.range_advantage.is_capped` compares the best hand in the range against the best hand *any* two cards could make on that board, flagging the range when it sits more than `tolerance` steps below.

**Step five: MDF sees only the aggregate.** `defense_indifference_gap(P, B, d)` takes one total; `balance_bluff_and_value`'s `exploitable_side` reads that total and the bluff share. So "raise 25% + call 41.67%" and "call 66.67%, never raise" are the same number to MDF. **That is how a missing top class hides behind a compliant floor.**

## 直觉 / Intuition

A check line is not a leftover basket; it is a claim: against 1/3 pot I keep 75%, against 2 × pot I keep 33.33%. **Those 75% must include hands that cannot win** -- because among all 1326 combos there simply are not 994.5 that beat a third-pot bet. The bottom class is not there to win, it is there to pay the fold tax so the good hands stay in the calling part.

The top class is there to make the raise threat real. MDF cannot see it, but the opponent can: once he knows your longest card is second pair, he pushes the size above your threshold, makes folding correct, and prints money with air.

## 算例 / Worked examples

**Example 1 -- continuing and folding combos per size (`P = 1`, scaled to 1326 combos).**

| Size | MDF | combos to keep | combos to fold | threshold equity |
|---|---|---|---|---|
| 1/3 pot | 75.00% | 994.5 | 331.5 | 20.00% |
| 1/2 pot | 66.67% | 884.0 | 442.0 | 25.00% |
| 3/4 pot | 57.14% | 757.71428 | 568.28571 | 30.00% |
| pot | 50.00% | 663.0 | 663.0 | 33.33% |
| 2 × pot | 33.33% | 442.0 | 884.0 | 40.00% |

Reproduce: `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds; [print(float(B), float(odds.minimum_defense_frequency(1,B,exact=True)*1326), float((1-odds.minimum_defense_frequency(1,B,exact=True))*1326), float(odds.equity_needed_to_call(1,B))) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))]"`. The first row's 994.5 is the same number the chart `range.04-02.mdf-floor-vs-third-pot` prints in its footer.

**Example 2 -- a check line that carries its bottom: 100 combos = 75 at `e = 0.30` + 25 at `e = 0.05`, facing 1/3 pot.** Threshold 20.00%: exactly the 25 air combos sit under it, and the tax owed is `[1/3 ÷ (1 + 1/3)] × 100 = 25` folds. `C = 25 = required`, tax costs `0`, and air scores `EV(bluff) = 0.25 × 1 − 0.75 × 1/3 = 0.000000` (`odds.indifference_check(1, 1/3, 1/4)` → `True`). **That is the bottom class's job: it drives the opponent's air to exactly zero without abandoning a single profitable call.**

**Example 3 -- the same line, opponent changes size: the 75 combos at `e = 0.30` face a pot-sized bet.** Threshold 33.33% > 30%, so `EV(call) = −0.100000` on all of them; fold the 25 air too → `f = 1` → air scores `1.000000` (any size). The same hand calls at 1/3 pot (`+0.166667`) and folds at pot (`−0.100000`): **the threshold is a function of size, the strength is not** -- the meeting point of `02-02` and `04-02` inside this lesson.

**Example 4 -- pricing the missing bottom: 100 combos, all at `e = 0.30`, facing 1/3 pot.** `C = 0`, shortfall `n = 25`: `25 × 0.166667 = 4.166667` chips per 100 hands. Make the line stronger (all at `e = 0.45`) and each fold abandons `0.45 × (5/3) − 1/3 = 0.416667`, so the bill rises to `10.416667` per 100 hands -- **the stronger the line, the more a missing bottom costs**, because the folds throw away more. Reproduce: `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(float(25*ev.ev_call(1,F(1,3),F(3,10))), float(25*ev.ev_call(1,F(1,3),F(45,100))))"`.

**Example 5 -- which size the opponent should punish with (a line folding 50% at every size).** `EV(bluff)`: 1/4 pot `0.375000`, 1/3 pot `0.333333`, 1/2 pot `0.250000`, 3/4 pot `0.125000`, pot `0.000000`, 2 × pot `−0.500000`. **His best punishment size is the smallest one**, not the biggest: you punish over-folding at the size where his fold rate first exceeds the threshold. Reproduce: `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; [print(float(B), float(ev.ev_pure_bluff(1,B,F(1,2)))) for B in (F(1,4),F(1,3),F(1,2),F(3,4),F(1),F(2))]"`.

## 生成表 / Generated tables

MDF, threshold equity and required fold rate -- the three columns that govern the floor all come from one table:

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

The same threshold written from the defender's single-hand side -- which combos of a check line may call:

<!-- BEGIN AUTO:table.02-02.equity-needed-to-call -->
|   Bet (x pot) | Equity needed |
|---:|---:|
|     0.25x pot |        16.67% |
| 0.333333x pot |        20.00% |
|      0.5x pot |        25.00% |
| 0.666667x pot |        28.57% |
|     0.75x pot |        30.00% |
|        1x pot |        33.33% |
|      1.5x pot |        37.50% |
|        2x pot |        40.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#equity_needed_to_call`

<!-- generated by: tools/gen_tables.py from pokergto.odds::equity_needed_to_call -->
<!-- END AUTO:table.02-02.equity-needed-to-call -->

Whether a top class exists is a machine test, not a debate; `is_capped` measures against the best hand any two cards could make on the board:

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

## 实战牌局 / Live hands

**Hand 1 (`hand.04-07-checkline-no-air`) -- flop `Kh7s3d`, hero defends the big blind, pot 12 bb, faces 1/3 pot. Model input: the check line holds 100 combos, all top pair weak kicker and middle pair, uniform equity `e = 0.30`, and not one combo under the 20.00% threshold.**

- Ledger: 1/3 pot owes 75% continuation, i.e. 25 folds, and `C = 0` → shortfall `n = 25`, cost `25 × 0.166667 = 4.166667` chips per 100 hands at `P = 1`, which is `50.0` bb per 100 hands scaled to `P = 12`.
- Decision: this line must not be played as "fold 25". Either call all 100 -- which turns his bluff into `−1/3` per attempt, after which he changes size rather than keep losing -- or the line was built wrong. The lesson's conclusion sits in the build phase: **create `C ≥ 25` first, then decide how to play the hand.**
- What the opponent collects immediately: push to a pot-sized bet and `EV(call) = −0.100000 × 12 = −1.2` bb per hand, so everything folds, `f = 1`, and his air wins `1.000000` pots = `12` bb per attempt. `ev.compare` returns `1.000000` for bluffs at 1/3 pot, pot and 2 × pot, all tied as best, while checking scores `0`: **at `f = 1` the size is irrelevant because `B` never enters the ledger.**
- The repair is computable: put 25 combos of `e = 0.05` air into the line (Example 2's shape) and the fold tax becomes `0` while his air's expectation becomes `0.000000`.

**Hand 2 (`hand.04-07-checkline-capped`) -- turn `Kh7s3d4c`, hero checked first from CO and faces a 2 × pot bet on the river, pot 40 bb. Model input: the strongest hand in the line is `KQ`, top pair two overcards, and `is_capped` returns true.**

- The test comes from `table.03-02.capped-range-check`: on `Kh7s3d` the two rows show `range_best` ("three of a kind 7 K 3" and "one pair K Q 7 3") sitting below `ceiling` ("three of a kind K 7 3"), both with `is_capped = true`. After the `4c` the ceiling still sits above what this line holds.
- What the opponent collects: 2 × pot requires 33.33% continuation (442 combos), and calling it needs `e ≥ 40.00%` (`table.02-02.equity-needed-to-call`). A capped line supplies `0` combos above that bar → `f = 1` → air scores `1.000000` of the pot = `40` bb per hand.
- Decision: the fix is to stop reaching this line at all -- `KQ`-class hands belong in a betting or raising line earlier -- because a check line is governed by how it is **constructed**, not by deciding in the moment not to fold.
- Keep the two failures apart: a missing bottom lets him **size you into folding**; a missing top lets him **collect at any size**, and he needs no over-folding to do it, since `EV(bluff) = P` does not depend on `B`. That is the only size-independent result in this lesson.

## 范围图 / Range chart

The 1/3-pot floor demands 994.5 continuing combos, and that number is itself the proof that a bottom class must exist:

<!-- BEGIN AUTO:range.04-02.mdf-floor-vs-third-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | :: | .. |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 7 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 6 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 5 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 4 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 3 | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 2 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |

994.5 combos = 75.00% of all 1,326

Legend: `··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%; the diagonal is pairs, the upper triangle suited, the lower offsuit.

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.04-02.mdf-floor-vs-third-pot -->

75.00% of all 1326 combos cannot possibly be hands that beat a third-pot bet; the chart fills strongest-first (its `assumptions` say so), so **its own lower edge is air and bluff-catchers**. Read it as "the minimum quantity of bottom class you must own", never as "which hands to fold". It cannot tell you how to split raise against call (step five: MDF is blind to the split), nor whether the line is capped (`is_capped` is that test).

## 为何成立、何时失效 / Why it works, when it breaks

**Premises**: `P` and `B` fixed; `f` means total continuation share; threshold equity uses all-in equity, ignoring realization differences on later streets; one street, no raise branch modelled.

**Where it breaks**:

1. **Threshold equity is not real value.** `e` is equity if the money goes in; how much of it a line actually realizes belongs to equity realization (`01-06`), and this repository **implements no EqR** (`src/pokergto/theory/__init__.py`). Every `C` and `n` here is therefore an all-in-basis bound, not a measured cost.
2. **The governance function is absent.** Judgements like "what size should the check line tolerate" or "which segment raises" need range-level answers; `src/pokergto/theory/__init__.py` lists bet-size governance among four deliberately unimplemented ideas. This lesson gives necessary conditions and prices, not a strategy table.
3. **The raise branch is not modelled.** Step five says MDF ignores the split, but a bluff facing a raise must call or fold, which changes its expectation. Pricing that needs a two-street solve, which does not exist here (`docs/development/solver-proof-policy.md`). **Any "the check line should raise X%" figure is UNVERIFIED.**
4. **Multiway pots**: `f` becomes "everyone folds" and the aggregate thins per player (`pokergto.odds.defense_frequency_multiway`).
5. **`e` is set by the opponent's range, which is an input.** The `0.30`, `0.05` and `0.45` used in Examples 2-4 are authored values.
6. **Tournaments**: replace `P` by its ICM value and the threshold stops being `B/(P+2B)` (chapter 12).

## 陷阱 / Common mistakes

1. **"I fold a little more than MDF, but only weak hands."** If the line has no weak hands, each extra fold abandons a profitable call.
   *Cost*: Example 4's `4.166667` chips per 100 hands at `P = 1`, and `10.416667` when the line is stronger (`e = 0.45`).
2. **Treating an MDF number as a health check.** `defense_indifference_gap` reads only the aggregate, and `balance_bluff_and_value`'s `exploitable_side` reads the aggregate plus the bluff share.
   *Cost*: a line of 66.67% continuation made only of bluff-catchers still reaches `f = 1` facing pot size (Example 3), handing air `1.000000` pots.
3. **Punishing with the biggest size.** With a uniform 50% fold rate, 1/4 pot scores `0.375000` and 2 × pot scores `−0.500000`.
   *Cost*: a swing of `0.875000` chips per attempt turns a profitable punishment into a losing one.
4. **Reading "bottom class" as "hands you can throw away".** Their function is to **pay the line's fold tax**; with them present the opponent's air is exactly `0` (Example 2), with them absent he takes one pot per attempt (Hand 1).
   *Cost*: the confusion produces "tighten the check line", and `f = 1` is precisely the worst outcome.

## 练习 / Drills

- Extend Example 1 with 1/4 pot and 3/2 pot (answers: 1/4 pot keeps 1060.8 / folds 265.2 at a 16.67% threshold; 3/2 pot keeps 530.4 / folds 795.6 at 37.50%).
- Build an `N = 100` check line whose fold tax against a half-pot bet is exactly `0`: how many combos must sit under the 25.00% threshold? (answer: `[0.5/(1+0.5)] × 100 = 33.333`).
- Reproduce the under-defending verdict: `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto.theory import frequencies as fq; r=fq.balance_bluff_and_value(1,F(1,3),defense_frequency=F(1,2),bluff_fraction=F(1,5)); print(r.defense_gap, r.bluff_gap, r.exploitable_side)"` → `-0.25 0.0 under-defending: any two cards profit as a bluff`; then set `defense_frequency` to `3/4` and watch it become balanced.
- Change Example 5's `f = 0.5` to `f = 0.7` and recompute the six sizes (answers: 1/3 pot `0.600000`, 1/2 pot `0.550000`, 3/4 pot `0.475000`, pot `0.400000`, 2 × pot `0.100000`), then explain why the 2 × pot row collapses fastest.

## 自测清单 / Self-check

- [ ] I can convert MDF into "how many combos must continue" and name 994.5 for 1/3 pot.
- [ ] I can compare `C` with `(1 − MDF)·N` to decide whether the bottom class is missing, and price the gap.
- [ ] I can explain why `EV(bluff) = P` at `f = 1` does not depend on the size.
- [ ] I can say what `is_capped` measures against (the best hand any two cards reach on the board) and what the opponent takes when it is true.
- [ ] I know MDF reads only the aggregate defence share, so a line with no raises and no top class can still pass it.

## 来源与置信度 / Provenance and confidence

Floors, thresholds, combo counts and expectations are computed here. The equities `0.30 / 0.05 / 0.45`, `N = 100` and fold rates `0.5 / 0.7` are authored model inputs; the two ranges behind `is_capped` are the teaching ranges already inside `table.03-02.capped-range-check`. This lesson contains no figure such as "the check line should raise X% of the time", because this repository cannot compute one.

| Content | Source type | Location / reproduce with |
|---|---|---|
| Example 1's five rows of MDF, combos and thresholds | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds; [print(float(B), float(odds.minimum_defense_frequency(1,B,exact=True)*1326), float((1-odds.minimum_defense_frequency(1,B,exact=True))*1326), float(odds.equity_needed_to_call(1,B))) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))]"` |
| Example 2's `EV(bluff) = 0` and `indifference_check = True` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds, ev; print(float(ev.ev_pure_bluff(1,F(1,3),F(1,4))), odds.indifference_check(1,F(1,3),F(1,4)))"` |
| Example 3 / Hand 1's `−0.100000`, `−0.500000`, `1.000000` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(float(ev.ev_call(1,F(1),F(3,10))), float(ev.ev_call(1,F(2),F(3,10))), float(ev.ev_pure_bluff(1,F(1,3),1)), float(ev.ev_pure_bluff(1,F(2),1)))"` |
| Example 4's `4.166667` and `10.416667` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(float(25*ev.ev_call(1,F(1,3),F(3,10))), float(25*ev.ev_call(1,F(1,3),F(45,100))))"` |
| Example 5 / trap 3's six `EV(bluff)` rows | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; [print(float(B), float(ev.ev_pure_bluff(1,B,F(1,2)))) for B in (F(1,4),F(1,3),F(1,2),F(3,4),F(1),F(2))]"` |
| Hand 1's three tied bluff sizes | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; rows=ev.compare(1,[('bluff 1/3 pot',F(1,3)),('bluff pot',F(1)),('bluff 2x pot',F(2)),('check',0)],fold_frequencies={'bluff 1/3 pot':1,'bluff pot':1,'bluff 2x pot':1,'check':0},equities_when_called={'bluff 1/3 pot':0,'bluff pot':0,'bluff 2x pot':0,'check':0}); print([(r.action,round(r.ev,6),r.best) for r in rows])"` |
| Step five "MDF reads only the aggregate" | `derived` | the module docstring and the signature of `defense_indifference_gap` in `src/pokergto/theory/frequencies.py`; `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto.theory import frequencies as fq; r=fq.balance_bluff_and_value(1,F(1,3),defense_frequency=F(1,2),bluff_fraction=F(1,5)); print(r.defense_gap, r.bluff_gap, r.exploitable_side)"` |
| The top-class test `is_capped` | `derived` | `data/gen/tables/table.03-02.capped-range-check.json`; `pokergto.theory.range_advantage#is_capped` |
| Equities `0.30 / 0.05 / 0.45`, `N = 100`, fold rates `0.5 / 0.7` | `reference` + **UNVERIFIED** | authored model inputs, no card-removal correction; to verify, write per-size continuing and folding ranges into `data/src/spots/*.yaml` and recompute each band's equity with `poker range` + `poker equity` |
| "The check line should raise X%" and "what size the check line should tolerate" | no implementation → **UNVERIFIED** | `src/pokergto/theory/__init__.py` lists bet-size governance alongside polarisation tests, blocker EV and protection-versus-value as deliberately absent; these need a range-level solve, and not even a two-street toy exists here |
| The line's true cost on a realization basis | no implementation → **UNVERIFIED** | needs equity realization (`01-06`'s concept); EqR is not implemented, and the deleted-module warning lives in `src/pokergto/theory/__init__.py` |

## 术语 / Terms

<!-- terms: checking-range, checking-frequency, minimum-defense-frequency, defend, fold-frequency, required-equity, capped-range, combos, bet-size, indifference -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 过牌范围 | checking range | the part of your range continued by checking, the object being governed |
| — | 过牌频率 | checking frequency | distinct from the continuation share facing a bet; both are computed here |
| MDF | 最低防守频率 | minimum defense frequency | the floor `P/(P+B)` on the aggregate continuation share |
| — | 防守 | defend | continuing in total (call or raise), not the calling action alone |
| — | 弃牌频率 | fold frequency | `1 − MDF`, converted here into "how many combos must fold" |
| — | 所需胜率 | required equity | `B/(P+2B)`, what makes a combo a cheap fold |
| — | 封顶范围 | capped range | the line holds none of the board's ceiling; `is_capped` tests it |
| — | 组合数 | combos | the unit of governance: 994.5, 663 and 442 are combo counts |
| — | 下注尺度 | bet size | the threshold is its function, and so is the punishment size |
| — | 无差别 | indifference | the point where air scores exactly 0, i.e. `f = B/(P+B)` |
