# Pot odds into a call: required equity and where implied odds break the shortcut

<!-- hands: 2 -->
<!-- terms: pot-odds, required-equity, implied-odds, reverse-implied-odds, break-even-percentage, minimum-defense-frequency, defend, fold-frequency, bet-size, outs, equity, spr -->

## 本节目标 / Objectives

- Derive the call threshold `B/(P+2B)` twice, from two different arguments (risk against reward, and "what share of the final pot must I own"), and explain why they must land on the same equation.
- Put "equity this hand needs" and "frequency this range must keep" side by side in one checkable table, and note that they move in opposite directions as sizing grows and meet near 1.618 times pot.
- Use the engine's `pot_odds` output correctly (it is `P/B`, not the classic "pot including your call"), and quantify how far the wrong denominator takes you.
- Compute where implied odds push the bar down and where reverse implied odds push it up, and state the assumptions that `future` smuggles in.

## 前置知识 / Prerequisites

- `02-01` Break-even percentage: `risk/(risk+reward)` and the rule that money is measured from the decision point.
- `01-06` Raw equity versus realization: the bar is compared with a **share**, and a share is only the computable half.

## 核心原理 / The principle

Facing a bet, the equity a call needs is

```
equity needed = B / (P + 2B)
```

with `P` the pot **before** the bet and `B` the money the opponent added. This is `pokergto.odds.equity_needed_to_call`, and it is bit-for-bit the same number as `break_even_percentage(B, P + B)`.

The contrast this lesson exists to pin down: **that number is not the minimum defense frequency (MDF)**. In the same spot

```
MDF = P / (P + B)
```

and the two move in opposite directions as the bet grows -- a two times pot bet needs 40.00% equity to call but only 33.33% defense. They cross at `B/P = φ = (1+sqrt(5))/2 ≈ 1.618`, where both equal `2 − φ ≈ 38.20%`. That crossing is derived in step four below.

> !!! note "Provenance"
>     Derivation: the next two sections. Functions: `src/pokergto/odds.py#equity_needed_to_call`, `#pot_odds`, `#minimum_defense_frequency`, `src/pokergto/spr.py#implied_odds_break_even_equity`, `#reverse_implied_odds_penalty`. Generated tables: `table.02-02.equity-needed-to-call.json`, `table.02-03.mdf-vs-sizing.json`.

## 推导 / Derivation

**Derivation one: risk against reward.** Following `02-01`: `risk` is the money you add now, `B`; `reward` is the pot you win when you win, which is the pot facing you, `P + B` (the opponent's bet is already in the middle, so it is winnable money).

```
break-even = risk/(risk + reward) = B / (B + P + B) = B / (P + 2B)
```

At `P = 13, B = 6.5` (half pot): `6.5/26 = 1/4 = 25.00%`.

**Derivation two: the share of the final pot.** After you call, the pot is `P + 2B`. Let `e` be your showdown share (definition in `01-05`: `wins + ties/2`). Measured from the decision point,

```
EV = e·(P + 2B) − B
EV ≥ 0  ⟺  e ≥ B/(P + 2B)
```

Both derivations produce the same line of algebra: `e·(P+2B) ≥ B` is the same inequality as `B/(B + (P+B))`. That is not a coincidence -- "you must own back at least the fraction you invest" and "your risk-to-reward ratio is the bar" are two bookkeeping routes to one statement. Both are written out because each saves you from a different mistake: the first from mis-measuring the reward, the second from confusing share with win probability.

**Third: `pot_odds` returns `P/B`, which is not the classic "pot including your call".** The engine defines `pot_odds(pot, bet) = pot/bet` on the pot **before** the bet. Converting it to the bar:

```
equity needed = 1 / (pot_odds + 2)
```

Half pot gives `pot_odds(13, 6.5) = 2.0`, so `1/(2+2) = 25.00%` -- correct. Using the memorised `1/(odds+1)` gives `1/3 = 33.33%`, inventing 8.33 extra percentage points, and the error only ever makes you fold more. The missing "1" is your own call: it belongs to the final pot (hence the denominator) but never to the reward.

**Fourth: where the two lines meet.** Set them equal with `s = B/P`:

```
1/(1+s) = s/(1+2s)  ⟹  1 + 2s = s + s²  ⟹  s² − s − 1 = 0  ⟹  s = (1+√5)/2 = φ ≈ 1.618034
```

At that size `MDF = 1/(1+φ) = 38.1966%` and `equity needed = φ/(1+2φ) = 38.1966%`; the two engine values differ only from the 12th decimal, where float rendering separates them: `mdf(1, φ)` = 0.3819660112500109 and `equity_needed_to_call(1, φ)` = 0.3819660112501411. The numbers `φ` and `2 − φ` are public mathematics, not somebody's conclusion. The point of the crossing is that it kills the popular idea that "MDF is the complement of the call threshold": the two lines touch once, and everywhere else one rises while the other falls.

| Size | Equity needed to call | MDF |
|---|---|---|
| 1/3 pot | 20.00% | 75.00% |
| 1/2 pot | 25.00% | 66.67% |
| 1x pot | 33.33% | 50.00% |
| 1.618x pot | 38.20% | 38.20% |
| 2x pot | 40.00% | 33.33% |

Every percentage in this table except the crossing row appears in the two generated tables below, so it can be checked row by row.

**Fifth: implied odds change the denominator; reverse implied odds change the numerator.** From `pokergto.spr`:

```
implied odds:         e ≥ B / (P + 2B + future_winnings)
reverse implied odds: e ≥ (B + future_losses) / (P + 2B)
```

At `P = 6, B = 3` (half pot), where the bar is 25.00%:

| Assumption | Equity needed | Against 25.00% |
|---|---|---|
| you win 5 more later | 13.6995% | 11.30 points lower |
| you win 20 more later | 7.0363% | 17.96 points lower |
| you pay 3 more later | 50.0000% | 25.00 points higher |

One direction adds `future` underneath, the other adds it **on top**, which is why "reverse implied odds are expensive" is arithmetic rather than a mood: when `f = B` the bar doubles (`(B+B)/(P+2B)`, and with `P = 2B` that is exactly `2B/4B = 1/2`).

**Sixth: the ceiling on `future` is computable; `future` itself is not.** Later streets can only move what is still behind. Nine outs counting one card (`draw_probability(9, 47, 1) = 19.1489%`) breaks even at `P = 6, B = 3` if

```
3 / 0.191489 − (6 + 6) = 3.67 chips of future value
```

arrive. With only 3.25 chips behind, the best case is `implied_odds_break_even_equity(6, 3, 3.25)` = **19.6721%**, still above the 19.1489% you hold. The same arithmetic gives the price of closing the money: `python -m pokergto spr --stack 3.25 --pot 6` -> SPR 0.542, 26.00% needed to shove (`all_in_equity_needed(pot=6, stack=3.25)` and `all_in_equity_needed_from_spr(spr(3.25, 6))` both return 0.26, two notations locking each other in). Conclusion: stack depth decides what implied odds are worth, and "will the opponent pay" is never something this lesson computes.

## 直觉 / Intuition

The threshold answers "is **this hand** worth the bet"; MDF answers "how much of **my whole range** must stay in". Same spot, two questions, opposite slopes: the bigger the bet, the easier it is to find a hand that clears 40%, and the more reason you have to drop most of your range (only a third must continue). People who merge the two say "it's a two times pot bet so I have to fold 60%" and then get pushed around by value bets.

A draw's bar has to travel with the number of cards you still get: 19.15% (one card) and 34.97% (two cards) are 15.82 points apart, which is enough on its own to flip a half-pot decision. Align the street count before comparing numbers, otherwise two correct figures will appear to disagree.

## 算例 / Worked examples

**Example 1 -- half pot, friendly integers: `P = 13, B = 6.5`.** Bar `6.5/(13+13) = 25.00%`; `pot_odds = 2.0`, and `1/(2+2)` reproduces the same figure; MDF `13/19.5 = 66.67%`. Nine outs: two cards 34.9676% clears it, one card 19.1489% does not -- it needs 7.94 chips of future value (`6.5/0.191489 − 26`).

**Example 2 -- one third pot: `P = 6, B = 2`.** Bar `2/10 = 1/5 = 20.00%`; MDF `6/8 = 3/4 = 75.00%`; the fold frequency a bluff of the same size needs is `2/8 = 1/4 = 25.00%` (`02-01`). Three numbers on one bet, three different questions.

**Example 3 -- solving backwards.** Pot 10; for the bar to be exactly 30%, what did the opponent bet? Solve `B/(10+2B) = 0.3` -> `B = 7.5`, three quarters pot, and the generated table's 3/4-pot row does read 30.00%.

**Example 4 -- the crossing.** At `B = 1.618 × P` both numbers are 38.20%. Above it, "bigger bets are harder to call but easier to fold"; below it, "smaller bets are easier to call but you must defend more". That shape is what `02-03` builds its frequency quota on.

## 生成表 / Generated tables

The call bar across the sizing ladder (`pokergto.odds.equity_needed_to_call`):

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

The same sizes with the threshold and MDF side by side (`pokergto.odds.sizing_table`) -- this is the contrast table the lesson asks you to check line by line:

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

How to check it: pick any row, set `P = 1` and `B = size`, and compute `B/(1+2B)` and `1/(1+B)` by hand. The two columns should match your arithmetic, and the fold-frequency column is exactly the complement of MDF. With all three in one table there is nowhere for the "MDF is the call threshold" reading to hide.

## 实战牌局 / Live hands

**Hand 1 (`hand.02-02-margin-of-015`) -- flop `Kh7s3d`, pot 6.5, CO bets 2.17 (about one third pot), you are on the button with the class `J9s`.**

- Bar: `2.17/(6.5 + 4.34) = 20.02%` (`equity_needed_to_call`, identical to `break_even_percentage(2.17, 8.67)`).
- Share: `python -m pokergto equity "J9s" --range-villain "88+,ATs+" --board "Kh7s3d"` -> exactly **20.1649%** over 1,176 runouts, with the ties term at 0.00%.
- Decision: call, by **+0.15 of a percentage point**. Not "sounds fine" -- the difference of two reproducible numbers.
- The frequency layer is a separate matter: at that size `MDF = 6.5/8.67 = 74.97%`, i.e. about three quarters of your **range's** combos must continue while this hand only needed a fifth of the pot. `02-03` is where that boundary is worked.

**Hand 2 (`hand.02-02-payoff-flip`) -- the turn after `Qh9h2s`, pot 13, opponent bets 13 (pot), you hold `AhJh` (flush draw plus two overcards).**

- Share: 46.5657% was computed at the flop (`01-06`). The pot-sized bar is `13/(13+26) = 33.33%`, so on "this bet closes the money" it is a call.
- But if you miss and the opponent fires again for 13 on the river, you pay 13 more: `reverse_implied_odds_penalty(13, 13, 13) = (13+13)/(13+26) = 66.67%`. The bar jumps from 33.33% to 66.67% and 46.57% is no longer enough.
- Conversely, against a range that bets the turn and checks the river you pay nothing more, and if you hit you win 13 more: `implied_odds_break_even_equity(13, 13, 13)` -> **25.00%**, 8.33 points below 33.33%.
- The lesson of this hand is not the verdict, it is the **premise**: three bars for three different betting-line assumptions. Choosing between them needs a stated source (your own plan, chapter 06's lines, or chapter 13's population data). `future` is not something the engine computes.

## 范围图 / Range chart

The chart embedded here is the frequency-layer one, which is exactly what separates the two questions:

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

Its stat line says **884.0 combos = 66.67% of all 1,326**: the MDF quota at the half-pot size, an answer about the range. The other line in this lesson, at the same size, is **25.00%**, an answer about a single hand. One `P = 1, B = 0.5`, two numbers, two questions -- reading them as one is where "my range only needs 25% to continue" comes from, and that sentence loses money fast.

Before reading the grid, go back to `01-07`: the chart is filled by grouping classes on their *lower* rank, so `22 33 44` fall outside the quota while `T9s` sits inside it. A quota is a quota, not a defence list; and the reason a real range would pick different cells -- blockers, later streets -- is what `02-03` closes with and chapter 13 develops.

## 为何成立、何时失效 / Why it works, when it breaks

**Premises of the bar:** one decision point only (after this bet the money closes or you fold); the outcome is measured as a share (chops already live inside `ties/2`); the opponent cannot raise the price again after you call (that belongs to the reverse-implied branch); chips are linear in money.

**The four premises you must state alongside any `future` term** -- this is the "where the shortcut breaks" part of the lesson title:

1. **The opponent keeps paying when you hit** (implied branch) or **stops betting when you miss** (reverse branch). That is a strategy claim. This repository publishes no action frequencies for anyone: making it a number requires a stated population model (chapter 13) or a validated solver artifact, and `adr/0002` says plainly that no six-max postflop NLHE tree is solved here.
2. **The chips exist.** `future` has a hard ceiling -- the money behind -- and that part is computable (step six: need 3.67, at most 3.25, so it cannot be made to work).
3. **Your share appears only in the hitting branch.** If you also win something on the miss (backdoor hands, overcards), the full `future` does not belong in the denominator.
4. **It is added once.** In spots where you will pay on two streets, `future` is a sum while the bar itself changes street by street; combining the rule of four's two-card discount with implied odds counts the same future money twice.

**Other failure settings.** Multiway pots do not change the algebra of the bar (the definition of a share is unchanged), but `range_equity` here takes two ranges only, so "this hand's share in a three-way pot" is currently unimplemented -- **UNVERIFIED**. Tournaments need the bar priced through ICM (chapter 12), and rake is not modelled (`07-04`).

## 陷阱 / Common mistakes

1. **Reading `pot_odds` as "pot including your call".** The engine returns `P/B` (2.0 at half pot), and the bar is `1/(odds+2)`, not `1/(odds+1)`.
   *Cost*: at `P = 13, B = 6.5` the right answer is 25.00%, the memorised one is 33.33% -- 8.33 points of extra demand, in the folding direction. One command checks it: `python -m pokergto odds --pot 1`, comparing the `pot_odds` and `equity_needed` columns.
2. **Treating MDF and the call threshold as complements.** At half pot they are 66.67% and 25.00%; they touch only at `B = 1.618P`.
   *Cost*: at small sizes you believe you may fold a lot (you must defend 75-80%), at big sizes you believe you must defend a lot (you may fold 60-66%). Mistake 1 of `02-03` is the same error seen from the other side.
3. **Treating implied odds as free.** They need a ceiling, an opponent-behaviour premise, and "share only when I hit".
   *Cost*: at `P = 6, B = 3` with nine outs and one card the arithmetic never closes -- 3.67 chips of future value are required and at most 3.25 exist, so the best possible bar is 19.67% against the 19.15% you hold.
4. **Comparing numbers with mismatched street counts**, e.g. 34.9676% (two cards) against a one-card bar.
   *Cost*: 15.82 percentage points of pure unit error, larger than most real margins. Declare the street count with `draw_probability(outs, 47, cards_to_come)` first.
5. **Stacking the rule of two and four on top of implied odds.** One is an approximation for a share, the other is money added above the share; together they double-count the same future winnings.
   *Cost*: hands that should be folds get scored as barely positive, and the error is small enough to survive a long session unnoticed.

## 练习 / Drills

- For the eight ladder sizes (`1/4 … 2`) write both numbers: the call bar and the MDF. Then compute both again at `B = 1.618P` and note how many decimals still agree.
- `P = 12, B = 4` (one third pot): compute the bar for `future_winnings = 6` and for `future_losses = 6` (answers 15.3846% and 50.0000%), and say in one sentence why the same "6" sits in a different place in the two formulas.
- Verify the shove bar at `pot = 6, stack = 3.25` in both notations (`all_in_equity_needed` and `all_in_equity_needed_from_spr(spr(...))`, both 0.26), and explain why the SPR form has coefficients 1 and 2.
- Pot 10: what bet sizes make the bar exactly 30% and exactly 37.5%? (Answers 7.5 and 15, i.e. three quarters pot and 1.5 times pot -- check them against the generated table.)
- List the betting-line premise behind each of the three bars in Hand 2, and say which of them is computable in this repository today.

## 自测清单 / Self-check

- [ ] I can derive `B/(P+2B)` twice and explain why both routes are the same inequality.
- [ ] I can state the unit of `pot_odds` and the identity `equity needed = 1/(pot_odds + 2)`.
- [ ] I can give the crossing size and crossing value of the bar and MDF, and name the folk belief that crossing refutes.
- [ ] I can compute the ceiling on `future` and list the four premises that using `future` requires.
- [ ] I can keep "what this hand needs" apart from "what this range must keep".

## 来源与置信度 / Provenance and confidence

Every number here is computed in this repository. No range chart or strategy output from a commercial solver or paid course appears anywhere in this lesson:

| Content | Source type | Location |
|---|---|---|
| The bar `B/(P+2B)` and its two derivations | `derived` | `src/pokergto/odds.py#equity_needed_to_call`; identity with `#break_even_percentage(B, P+B)` checked in this lesson |
| `pot_odds = P/B` and `1/(odds+2)` | `derived` | `src/pokergto/odds.py#pot_odds`; consistent with the `pot_odds`/`equity_needed` columns of `table.02-03.mdf-vs-sizing.json` |
| MDF column and bluff fold-requirement column | `derived` | `src/pokergto/odds.py#minimum_defense_frequency`, `#required_fold_frequency` -> `data/gen/tables/table.02-03.mdf-vs-sizing.json` |
| Crossing at `B/P = φ`, value 38.20% | `derived` (a quadratic; public-domain mathematics) | step four above; checked to 12 decimals with `mdf(1, φ)` and `equity_needed_to_call(1, φ)` |
| Implied and reverse bars (13.6995% / 7.0363% / 50.0000% / 15.3846% / 25.00% / 7.94 / 3.67 / 19.6721%) | `derived` algebra over assumed inputs | `src/pokergto/spr.py#implied_odds_break_even_equity`, `#reverse_implied_odds_penalty` |
| SPR and the commit threshold (0.542 -> 26.00%) | `derived` | `python -m pokergto spr --stack 3.25 --pot 6`; `src/pokergto/spr.py#all_in_equity_needed_from_spr` |
| `J9s` versus `88+,ATs+` on `Kh7s3d` = 20.1649% | `derived` | `python -m pokergto equity`, exact, 1,176 runouts |
| Whether an opponent will pay on later streets (the value of `future`) | **UNVERIFIED** | needs a stated population model (chapter 13) or a validated solver artifact; `adr/0002` rules out a six-max postflop solver here |
| This hand's share in a multiway pot | **UNVERIFIED** | `range_equity` accepts two ranges only; multiway share is not implemented |

## 术语 / Terms

<!-- terms: pot-odds, required-equity, implied-odds, reverse-implied-odds, break-even-percentage, minimum-defense-frequency, defend, fold-frequency, bet-size, outs, equity, spr -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 底池赔率 | pot odds | engine unit `P/B`, not the pot including your call |
| — | 所需胜率 | required equity | `B/(P+2B)`: one hand, one bar |
| — | 隐含赔率 | implied odds | future winnings added to the denominator |
| — | 反向隐含赔率 | reverse implied odds | future losses added to the numerator; the bar can double |
| — | 保本百分比 | break-even percentage | the parent formula from `02-01` |
| MDF | 最低防守频率 | minimum defense frequency | `P/(P+B)`: a range quota, not a threshold |
| — | 防守 | defend | call or raise; this lesson sizes the quota, it does not assign actions |
| — | 弃牌频率 | fold frequency | the complement of MDF, not an estimate of anyone's folding |
| — | 下注尺度 | bet size | `s = B/P`, the shared input of both lines |
| — | 补牌 | outs | always declare "within how many cards" |
| — | 胜率 | equity | a share including chops, not a chance of taking it all |
| SPR | 筹码底池比 | stack-to-pot ratio | the source of the hard ceiling on `future` |
