# Thin value bets: when winning only a little is still worth betting

<!-- hands: 2 -->
<!-- terms: thin-value, value-bet, value-range, bluff-catcher, required-equity, indifference, fold-equity, pot, bet, combos -->

## 本节目标 / Objectives

- Separate thin value from standard value with two quantities -- how often you are ahead when called, and what your check line is worth -- instead of the claim that a decent hand is reason enough.
- Derive the exact break-even: how much of the opponent's calling range you must beat at a given fold rate and size.
- Say plainly what the engine can and cannot do here: it enumerates equity and solves thresholds, while "will he call with worse" is an input from an opponent model, and asserting a frequency for it must be marked UNVERIFIED.

## 前置知识 / Prerequisites

- `02-04` the bluff-to-value ratio (thin value hands sit at the bottom of the value segment).
- `02-06` the unified template and `EV(check) = e·P`; `02-05` fold equity as the term `f·P`.

## 核心原理 / The principle

Sort three categories by arithmetic, not by adjectives. Write

```
q  = probability you are ahead when called (the share of his calling combos you beat)
e₀ = probability you are ahead if you check and both check to showdown
```

| Category | Test | Reading |
|---|---|---|
| Fat value | `q·(P + 2B) − B ≥ e₀·P` | Worth betting even if he never folds; the fold branch is a bonus |
| Thin value | `q > 1/2` but `q·(P + 2B) − B < e₀·P` | Genuinely ahead of the calling range, but needs the fold branch to cover the gap |
| Bluff | `q ≤ 1/2` | Better than half of what calls him beats you; this is not value |

`02-04` defines a value bet as one where you expect worse hands to call, so `q > 1/2` is the floor of "value". The *thinness* comes from the second inequality: **you win only `P + B` when ahead, you lose `B` when behind, and the line works only because of `f·P`.**

## 推导 / Derivation

Both routes come straight out of the `02-06` template:

```
EV(bet)   = f·P + (1 − f)·( q·(P + 2B) − B )
EV(check) = e₀·P
```

The called branch is written `q·(P + 2B) − B` because winning nets `P + B` and losing nets `−B`, and weighting them by `q` and `1 − q` gives exactly that (expand to check: `q(P+B) − (1−q)B = qP + 2qB − B`).

Betting is at least as good as checking when

```
f·P + (1 − f)·( q·(P + 2B) − B ) ≥ e₀·P
```

a linear inequality in `q`. Solving it is this lesson's break-even point:

```
q* = ( (e₀ − f)·P + (1 − f)·B ) / ( (1 − f)·(P + 2B) )
```

Bet when `q ≥ q*`, check when `q < q*`. The `P + 2B` in the denominator is the same final-pot term from `02-02`: **this is not a new formula**, it is the bluff-catcher's indifference condition solved for the other unknown -- he treats `B/(P+2B)` as the equity he needs, you treat the same `P + 2B` as the bar you must clear.

**Two limits worth memorising.**

First, `f = 0` (he never folds) with the crude `e₀ = q`:

```
q* = [(1−f)B − fP] / [2B − f(P+2B)] = B / 2B = 1/2
```

With no fold equity you must beat the calling range outright -- the original meaning of "value".

Second, `f = B/(P+B)`, i.e. the defender folds exactly the amount `02-03` makes him owe (then `q* = 0`):

```
numerator = (1 − f)B − fP = [P/(P+B)]·B − [B/(P+B)]·P = 0
```

In this model, once the opponent folds his indifference share, *every* bet is at least as good as checking. **That is simultaneously the strongest and the loudest warning in the lesson**: it shows a single fold-frequency line cannot decide whether you should bet. It governs the defender's action, not your range's structure. Reality differs because `e₀ > q` -- the hands that call you are stronger than the whole range -- and that gap `e₀ − q` is the premium thin value has to pay out of fold equity.

For table use, solve instead for the fold rate you need:

```
f* = ( e₀·P − A ) / ( P − A ),   where A = q·(P + 2B) − B
```

## 直觉 / Intuition

A thin value bet trades frequency for margin. You are not paid because he surely calls; you are paid because when he calls you win slightly more often than you lose, and when he folds you take the pot for free. So the judgement always asks two questions:

1. **How much of his calling range do I beat?** (`q`) This decides whether the action is value at all.
2. **What do I win by checking?** (`e₀`) Checking is not zero, and it is usually worth more than people think -- the bigger `e₀ − q` is, the thinner your bet and the more you lean on the fold branch.

Question two is the one people skip, which is where thin value bets go wrong. With a medium hand, checking often beats exactly the worse hands that would never call. Bet those hands and you only get action from better ones. In one sentence: **a thin value bet swaps a small but reliable pot for a package of "sometimes a bit more, sometimes all of it", and only frequent folds make the swap positive.**

## 算例 / Worked examples

**Example 1 -- the break-even collapses as fold equity grows (`P = 10, B = 5`, with the simplified `e₀ = q`).**

| Opponent fold rate `f` | Share of his calling range you must beat, `q*` |
|---|---|
| 0% | 50.00% |
| 10% | 43.75% |
| 20% | 33.33% |
| 30% | 12.50% |
| 33.33% = `B/(P+B)` | 0% |

Every row can be checked by comparing two expectations, e.g. `PYTHONPATH=src python -c "from pokergto import ev; print(ev.ev_bet(10,5,0.2,1/3), ev.ev_check(10,1/3))"` → both `3.3333`. Read the table as one sentence: **the more he folds, the worse your hand may be.**

**Example 2 -- classifying one hand.** Pot 20, bet 10 (half pot), `q = 34/59 = 57.63%` when called, `e₀ = 0.72` on the checking line (both are inputs; see the provenance table).

- `q > 1/2`: value, not a bluff.
- Set `f = 0`: `A = 0.576271 × 40 − 10 = 13.0508`, while `EV(check) = e₀·P = 14.4`. Since `13.0508 < 14.4`, this is **thin** value: with no fold equity the bet does not belong.
- The fold rate it needs: `f* = (14.4 − 13.0508)/(20 − 13.0508) = 0.194146`, i.e. 19.41%.
- Cross-check in threshold form: at `f = 1/3` (the rate a half-pot bet earns against MDF), `q* = ((0.72 − 1/3)×20 + (2/3)×10)/((2/3)×40) = 0.54`, and `q = 0.5763 > 0.54` → bet.

**Example 3 -- same size, a slightly different `e₀`, opposite conclusion.** Keep `q = 0.5763`, `P = 20, B = 10, f = 1/3`, and move `e₀` from `0.72` to `0.78`: `q*` goes from `0.54` to `0.585`, above `q` → same opponent frequency, same hand, and a single estimate flips bet into check. The flip point is exact: `e₀ ≈ 0.7684`, where `q* = q` and `f* = 33.34%`, right at the half-pot threshold. So the sensitivity in this lesson is not in the size, it is in **the estimate of what checking is worth**: the distance between `0.72` and `0.78` is six percentage points, and it decides the whole line.

**Example 4 -- change the size, change the category.** Bet pot into `P = 20` (`B = 20`) and the calling range hardens: `q = 12/34 = 35.29%`, `e₀ = 0.55`.

- `q ≤ 1/2` → by definition this is no longer a value bet; it is a bluff.
- `A = 0.352941 × 60 − 20 = 1.1765`; `f* = (0.55×20 − 1.1765)/(20 − 1.1765) = 0.521875`, so it needs 52.19% folds.
- A pot-sized bet is only *owed* 50% folds by MDF. Short by 2.19 points, and short in the direction of asking for more than theory supplies → check.

**Example 5 -- lining this up with `02-04`.** A half-pot bet's bluff share is 25%, ratio 3:1. Thin value hands live in the lowest slot of the remaining 75%: too weak for the "beats everything" segment, yet by `q > 1/2` not air. The ratio governs how the two segments are balanced against each other; `q*` governs where the dividing line is drawn. An action is legal and profitable only when both conditions are satisfied.

## 生成表 / Generated tables

This lesson splits the value segment off the bluff segment, and the relative sizes of those two segments come from `pokergto.odds.sizing_table` with `P = 1`:

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

The other side of the bar is this table. Thin value only works if worse hands are willing to call, and their willingness is exactly the equity needed to call -- bigger size, higher bar, fewer worse hands left in:

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

## 实战牌局 / Live hands

**Hand 1 (`hand.02-07-river-thin-value`) -- heads up, river `AcKd8s5h2c`, pot 20, hero `KsQh` (top pair, second kicker), opponent checks.**

- Model input: against a half-pot bet the opponent's calling range contains 34 combos hero beats (lower pairs, kings with worse kickers) and 25 combos that beat hero (`AK/AQ/AA`, two pair, sets). So `q = 34/59 = 57.63%`.
- The checking branch: his check range still holds plenty of worse than a king pair, which supports `e₀ = 0.72`.
- Classification: `q > 1/2` makes it value; `f = 0` gives `EV(bet) = 13.0508 < EV(check) = 14.4`, so it is **thin** value; the required fold rate is `f* = 19.41%`.
- Decision: bet half pot, conditional on being able to say "he folds at least 19.4% on this line". MDF already owes 33.33% folds at this size, so there is 13.9 points of headroom and, under the MDF assumption, the bet is live.
- Bet pot instead and you get Example 4: same hand, same opponent, category changes from thin value to bluff. **Thinness is not a property of the cards; it is a joint property of size and calling range.**

**Hand 2 (`hand.02-07-fat-or-thin`) -- same river, pot 20, hero holding the hand that beats every calling range (`AcAh`-class, two pair or better).**

- Here `q ≈ 1`: nothing that calls beats this hand; `e₀` is only about `0.85`.
- At `f = 0`, `A = 1 × (20 + 2B) − B = 20 + B`, which always exceeds `e₀·P = 17` → this is **fat** value: bet it with no fold equity at all, and the bigger the size the better, because `20 + B` grows with `B`.
- The purpose of this hand is the control group. Write the four numbers for both hands (`q`, `e₀`, `A`, `e₀·P`) side by side and the difference between thin and fat is two inequalities, not a feeling.
- The mirror mistake is importing Hand 2's logic into Hand 1 -- "I have a pair, so I should bet big" -- and then pot-sizing a range with `q = 35.29%`, which Example 4 shows needs 52.19% folds when theory only supplies 50%.

<!-- BEGIN AUTO:range.02-03.mdf-floor-vs-half-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. |
| 7 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| 6 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| 5 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| 4 | @@ | @@ | @@ | @@ | @@ | @@ | :: | .. | .. | .. | .. | .. | .. |
| 3 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 2 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |

884.0 combos = 66.67% of all 1,326

Legend: `··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%; the diagonal is pairs, the upper triangle suited, the lower offsuit.

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.02-03.mdf-floor-vs-half-pot -->

## 范围图 / Range chart

The chart shows the 884 combos the opponent must keep against a half-pot bet (`threshold = 0.66666667`). For thin value it is one source of `q`'s denominator: most of the hands you beat are precisely those below that line, the ones he folds or plays elsewhere. So read it as **"where does my thin value bet actually collect money from"**, not as a prescription.

Two honest limits. First, the chart exists only for the half-pot size, and thin value most often lives at pot and overbet sizes, where no chart has been generated. Second, the thing this lesson really needs -- `q` and `e₀` given an opponent model -- is not something the chart or the engine can supply. `pokergto` provides equity enumeration (`equity`) and thresholds (`odds`); range structure belongs to an opponent model (`data/src/spots/*.yaml`) and to chapter 03.

## 为何成立、何时失效 / Why it works, when it breaks

**Premises**: one street, one decision point, only ahead/behind once called (no chops), `q` and `e₀` are the true values under a stated opponent model, and betting does not change how the opponent plays later streets.

**Where it breaks or weakens**:

1. **`e₀` and `q` are inputs, not conclusions.** What the engine computes: equity for given hands, ranges and boards (`poker equity`), and every threshold (`poker odds`). Whether the opponent calls with worse at this size is a claim about his strategy. The `34/59` and `e₀ = 0.72` used here are **authored model inputs** and are **UNVERIFIED / 未核验**; the route to making them checkable is in the provenance table below.
2. **Chops.** When `AA` runs into `AA` or the board plays a straight, a half-win sits between `q` and `1 − q`, and `q*` shifts upward slightly. The closed form here omits that band.
3. **Multiway pots.** `f` becomes "everyone folds", each caller's range differs, and `q` must be re-weighted across players; handled after `07-02`.
4. **Not the river.** A turn thin value bet also buys protection and the right to attack the next street (`04-06`, `06-05`). Omitting those understates `EV(bet)`, which makes you too tight rather than too loose -- a known, stated bias.
5. **The MDF limit case.** Example 1's last row (`q* = 0`) says that in this one-street model, once the opponent folds his required share, every bet beats checking. Real play does not do this, because the checking range also needs a top end: bet all your medium hands and your check line becomes empty, which an opponent attacks freely. That correction belongs to chapter 04's polarized/merged shapes and checking-range construction, and is not proved here.
6. **Tournaments.** When chips are non-linear in utility, replace `P` by its ICM value and thin value frequently becomes a check (chapter 12).

## 陷阱 / Common mistakes

1. **Using "I have a good hand" as the thin-value test.** The tests are `q > 1/2` (is it value) plus one inequality (does it need fold equity), not an adjective about strength.
   *Cost*: Example 4's action gets logged as "thin value, fine", while it needs 52.19% folds and theory owes it 50%. The 2.19-point gap is worth `−0.412` chips per hand (`EV(bet) = 10.5882` against `EV(check) = 11.0000`). Small once, negative on every river you play this way.
2. **Substituting showdown equity for `q`.** `q` is conditional on being called; your overall hand equity includes the folds and is both higher and useless here.
   *Cost*: an inflated `q` clears `q*` trivially and you play a bluff as value. When you run `poker equity`, set the villain range to *what he calls with*, not to his whole range.
3. **Forgetting `e₀`.** Treating checking as zero, or as `q·P`, is the laziest error in this lesson.
   *Cost*: Example 3 shows a move from 0.72 to 0.78 flips the action. Treating checking as 0 yields "bet every hand that beats the calling range", which empties your check line and hands the opponent a free attack.
4. **Confusing 薄价值 / thin value with 抓诈唬牌 / bluff-catcher.** The glossary puts a bluff-catcher on the `q ≤ 1/2` side -- it beats bluffs and nothing else; thin value sits on the other side of that line.
   *Cost*: the two have opposite tests, so blurring the words leaves you unable to decide either the bet or the call.

## 练习 / Drills

- With `P = 20, B = 10`, compute `q*` at `f = 1/3` for `e₀ = 0.6 / 0.7 / 0.8` and read off how much the bar rises per 0.1 of `e₀`.
- Inverse: `q = 0.55`, `e₀ = 0.7`, `P = 15`, pot size. Find the minimum fold rate that makes the bet live.
- With `P = 20, B = 10`, sweep `q` from `0.51` down to `0.49` and locate the moment thin value becomes a bluff; explain why it sits exactly at `1/2`.
- Build your own calling range with `poker equity "KsQh" "..." --board "AcKd8s5h2c"`, compute your own `q`, and write down how far it sits from the `q` you would have guessed.
- Verify all five rows of Example 1 by substituting each `q*` back into `ev_bet` and `ev_check` and confirming the two expectations match. That is the self-check for every number in this lesson.

## 自测清单 / Self-check

- [ ] I can separate fat value, thin value and bluff with two inequalities and no adjectives.
- [ ] I can derive `q*` and name the `P + 2B` it shares with the equity needed to call.
- [ ] I can state both meanings of `q* = 0` at `f = B/(P+B)`: the result and the warning.
- [ ] I can say that `q` and `e₀` are opponent-model inputs and give the concrete path to making them checkable.
- [ ] I can explain why one hand is thin value at half pot and a bluff at pot size.

## 来源与置信度 / Provenance and confidence

Every threshold and expectation here is computed in this repository. Opponent ranges that are quoted are authored teaching inputs and are labelled as such. No range chart or strategy output from a commercial solver or paid course appears in this lesson.

| Content | Source type | Location / reproduce with |
|---|---|---|
| The three-way test, `q*` and `f*` | `derived` | Derivation above; difference of `src/pokergto/ev.py#ev_bet` and `#ev_check` |
| Example 1's five rows (50% / 43.75% / 33.33% / 12.5% / 0%) | `derived` | `PYTHONPATH=src python -c "from pokergto import ev; print(ev.ev_bet(10,5,0.2,1/3), ev.ev_check(10,1/3))"` (each row verified by equality of the two expectations) |
| Example 2's `f* = 0.194146`, `A = 13.0508` | `derived` (inputs per row below) | `PYTHONPATH=src python -c "from pokergto import ev; q=34/59; A=q*(20+20)-10; print(A, ev.ev_check(20,0.72), (0.72*20-A)/(20-A))"` |
| Example 3's flip point `e₀ ≈ 0.7684` | `derived` (same inputs) | same command, `e₀ = 0.78` gives `q* = 0.585`, `f* = 0.366829` |
| Example 4's `f* = 0.521875` and `−0.412` chips | `derived` (same inputs) | same command with `q = 12/34, e₀ = 0.55, P = B = 20` |
| 34/25 with `e₀ = 0.72`; 12/22 with `e₀ = 0.55` | `reference` + **UNVERIFIED** | Authored opponent-model inputs, no card-removal correction. To verify: write per-size calling ranges into `data/src/spots/*.yaml`, count combos with `poker range` plus `pokergto.cards.remove_cards`, then recompute `q` with `poker equity` |
| Ratio and required-equity tables | `derived` | `data/gen/tables/table.02-04.bluff-value-ratio.json`, `table.02-02.equity-needed-to-call.json` |
| "The checking range needs a top end too" | chapter 04 conclusion | **UNVERIFIED** here; path: the polarized/merged derivation in `04-05` plus the two-street toy game in chapter 08 |
| Range chart at pot and overbet sizes | no artifact yet | needs `tools/gen_ranges.py` to accept custom sizes and the bettor's viewpoint |

## 术语 / Terms

<!-- terms: thin-value, value-bet, value-range, bluff-catcher, required-equity, indifference, fold-equity, pot, bet, combos -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 薄价值 | thin value | ahead of the calling range, but needing the fold branch |
| — | 价值下注 | value bet | worse hands are expected to call, i.e. `q > 1/2` |
| — | 价值范围 | value range | the value segment; thin hands sit at its lower edge |
| — | 抓诈唬牌 | bluff catcher | beats bluffs only, the `q ≤ 1/2` side, opposite of thin value |
| — | 所需胜率 | required equity | `B/(P+2B)`, the same equation on his side |
| — | 弃牌赢率 | fold equity | the term that pays the difference, `f·P` |
