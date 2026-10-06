# Fold equity: the only part of a bet the opponent can hand you

<!-- hands: 2 -->
<!-- terms: fold-equity, fold-frequency, expected-value, ev-decomposition, bluff, minimum-defense-frequency, semi-bluff, pot, bet, range -->

## 本节目标 / Objectives

- Split any bet into a "everyone folds" branch and a "someone continues" branch, and see that fold equity *is* the first branch's term `f·P`, not a separate quantity.
- State the ceiling on fold equity, and show why a pure bluff earns exactly zero once the defender plays the minimum defense frequency (MDF).
- Convert the sentence "I have a lot of fold equity" into a testable claim about **the opponent**, and name the data that would test it.

## 前置知识 / Prerequisites

- `02-01` Break-even percentage; `02-04` the bluff-to-value ratio (same indifference move, from the bettor's side).
- `02-03` MDF and the fold frequency a bluff needs, `B/(P+B)`.

## 核心原理 / The principle

Fold equity is not a kind of income. It is the first term of a bet's expectation:

```
EV(bet) = f·P + (1 − f)·(e·(P + 2B) − B)
          ↑     ↑
      fold equity   the called branch
```

`f` is the probability that **every** opponent folds, `P` is the money you can collect right now, and `e` is your equity once the money goes in. The glossary defines fold equity as "the opponent's fold probability times the pot that is currently collectable", i.e. `f·P`. It differs from "fold frequency" by one word and by kind: one is money, the other is a probability. Mixing them up changes what your formula computes.

## 推导 / Derivation

A bet has exactly two outcomes, so its expectation must have exactly two terms.

**Branch one**: everyone folds (probability `f`). The `B` you put in comes back untouched and the `P` already in the middle is yours: `+P`. Contribution `f·P`.

**Branch two**: somebody continues (probability `1 − f`). Money goes in, the final pot is `P + 2B`, your expected share is `e·(P + 2B)`, and you invested `B` this street: net `e·(P + 2B) − B`.

Add the two branches and you have the template. A pure bluff is the case `e = 0`:

```
EV(bluff) = f·P − (1 − f)·B
```

Set it to zero and you recover the threshold from `02-03`:

```
f·P = (1 − f)·B  →  f = B / (P + B)
```

Which gives the most important sentence in this lesson: **as long as the defender plays MDF, a pure bluff of yours earns exactly zero.** Fold equity has bought you nothing extra, because it is cancelled to the chip by "losing `B` when called". A bluff only makes money when the opponent defends *below* the floor -- that is, only when he deviates from `02-03`.

Now the ceiling. Since `f ≤ 1`,

```
f·P ≤ P
```

An air hand betting can, over its whole life, never earn more than the pot in front of it. And `f = 1` demands a defender who never defends, which contradicts `MDF = P/(P+B) > 0`. So fold equity has a ceiling, and equilibrium never lets you touch it.

Finally, sensitivity. Rewrite `EV(bluff) = f·(P + B) − B`: the slope against `f` is `P + B`. At pot 10 and bet 5, one extra percentage point of folds is worth `0.15` chips. That number is more useful at a table than the feeling that someone is scared of you.

## 直觉 / Intuition

Fold equity is **the balance the opponent's strategy leaves in your account**. It is not a property of your cards. You control two things only: the range your line represents, and the price you ask. The rest -- whether he pays it -- is his decision.

Three things move `f`, in order of importance:

1. **What your line represents.** The same air hand steals far more on a "bet flop, second barrel turn" line than on a "check, then bet" line. Chapters 03 and 06.
2. **Size.** A larger bet needs a larger fold share to break even (`B/(P+B)` rises with `B`), but each point of folds is also worth more, because the slope is `P + B`.
3. **Whether he holds the floor.** An opponent whose fold rate exceeds `B/(P+B)` turns bluffs from zero-EV into positive-EV. One who holds the floor turns your bluffs into tuition.

Mental model: `f·P` is rent you collect, `(1 − f)·B` is the insurance premium you pay. Whether the bluff works is never about how big the rent is; it is about rent minus premium.

## 算例 / Worked examples

**Example 1 -- air betting 5 into a pot of 10 (half pot).**

| Opponent fold rate `f` | Fold equity `f·P` | `EV(bluff)` |
|---|---|---|
| 10% | 1.0 | −3.5 |
| 33.33% (the threshold) | 3.33 | 0.0 |
| 40% | 4.0 | +1.0 |
| 50% | 5.0 | +2.5 |

Reproduce with `PYTHONPATH=src python -c "from pokergto.ev import ev_pure_bluff as e; print(e(10,5,0.4))"`. The threshold is `B/(P+B) = 5/15 = 33.33%`, the same figure `poker odds --pot 10` prints in its fold-frequency column.

**Example 2 -- the ceiling.** Same `P = 10, B = 5`, set `f = 1`: `EV = 10`, exactly the pot. That is the theoretical maximum for an air bet, and it requires a defender who never defends. Since `MDF = 66.67%` pins `f` at 33.33%, even the `+2.5` row above already assumes he is visibly under-defending.

**Example 3 -- a semi-bluff where fold equity buys its way from negative to positive.** Turn, pot 12, you shove 15 holding a nine-out draw, winning only when you hit. Take the enumerated hit probability `19.1489%` for one card from `table.01-03.draw-probability-exact-vs-rule`.
- He calls 100% of the time: `EV = −6.9575` (`ev_shove(12, 15, 0.191489, 1)`).
- He calls 60% (`f = 0.4`): `EV = +0.6255`.
- The fold branch contributes `0.4 × 12 = 4.8` of that. Every chip of profit in this shove comes from the 40% of the time he does not call; the draw itself loses money at showdown.

**Example 4 -- multiway: `f` means *everyone* folds.** Pot 12, bet 12, two opponents. The joint fold rate you need is still `B/(P+B) = 50%`, and that requires *each* of them to fold `70.71%` (each is only required to defend `29.2893%`).
Reproduce with `poker mdf --pot 12 --bet 12 --opponents 2 --json`: `per_player_defense = 0.292893`, `joint_defense = 0.5`. When each folds exactly 70.71%, the joint rate is exactly 50% and the bluff's EV is exactly `0.0` -- supply and requirement are the same number. The common error is to plug the per-player figure into the formula as if it were the joint one: `ev_pure_bluff(12, 12, 0.7071)` returns `+4.8`, turning a break-even bluff into one that appears to print 4.8 chips a try. Read `joint_defense` and you cannot make that mistake. Chapter `07-01`.

**Example 5 -- what a big size demands.** `P = 20, B = 40` (two times pot): threshold `40/60 = 66.67%`. At a 70% fold rate `EV = +2.0`; at 50% `EV = −10.0`. Same action, same hand, folds dropping from 70% to 50% -- 12 chips apart per attempt.

## 生成表 / Generated tables

The table below is computed by `pokergto.odds.sizing_table` with `P = 1`. Read the "fold frequency a bluff needs" column: it is the minimum fold equity you must collect at each size.

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

The second table enumerates draw probabilities against the rule of two and four. Example 3 takes its `e` from here:

<!-- BEGIN AUTO:table.01-03.draw-probability-exact-vs-rule -->
| Outs | Exact, next card | Rule of 2 | Exact, two cards | Rule of 4 |
|---:|---:|---:|---:|---:|
|    3 |            6.38% |     6.00% |           12.49% |    12.00% |
|    4 |            8.51% |     8.00% |           16.47% |    16.00% |
|    5 |           10.64% |    10.00% |           20.35% |    20.00% |
|    6 |           12.77% |    12.00% |           24.14% |    24.00% |
|    8 |           17.02% |    16.00% |           31.45% |    32.00% |
|    9 |           19.15% |    18.00% |           34.97% |    36.00% |
|   10 |           21.28% |    20.00% |           38.39% |    40.00% |
|   12 |           25.53% |    24.00% |           44.96% |    48.00% |
|   15 |           31.91% |    30.00% |           54.12% |    60.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.equity#draw_probability`

<!-- generated by: tools/gen_tables.py from pokergto.equity::draw_probability -->
<!-- END AUTO:table.01-03.draw-probability-exact-vs-rule -->

## 实战牌局 / Live hands

**Hand 1 (`hand.02-05-semi-bluff-shove`) -- heads up, turn `AdKc8s5d`, pot 12, you hold a nine-out draw and shove your remaining 15.**

- Winning only on the hit: nine outs, `19.1489%` on the river (enumerated, table above). If he always calls, `EV = −6.9575`: a pure donation.
- At a 60% call rate `EV = +0.6255`, and the entire positive part is the fold branch, `f·P = 4.8`.
- So this shove rests on one claim about the opponent: "on this line he folds at least 40%". Compare it with the bluff's own threshold, `B/(P+B) = 15/27 = 55.56%` -- note the threshold sits *above* 40%, which tells you that a pure air hand could not shove here. `QdJs` can, because it is not air: the 19.15% of hitting stands behind it.
- How to check the claim: record this player's fold rate facing a turn shove and compare it with 40%. The gap converts straight into chips, exactly as in Example 5.

**Hand 2 (`hand.02-05-assumed-fold`) -- river, pot 20, opponent checks, you bluff 40 (two times pot).**

- You need `40/60 = 66.67%` folds. Your private estimate is "people usually fold 70% to an overbet", and at 70% the EV is `+2.0`, so the bet looks fine.
- Reality: this opponent holds the floor and folds exactly 50%. `EV = −10.0`.
- The leak is not the sizing choice (that is chapter 04). It is that an estimate with no data behind it was allowed into the formula. The 12 chips between `+2.0` and `−10.0` are the price of "I assumed he had fold equity".
- There is one repair: before you write down `f`, write down where it came from. Either your own hand log for that node, or the HUD conventions in `13-02`, or honestly "no data -- assume he plays MDF, so `f = 1 − MDF`". That third option puts your bluff's EV back at zero, which is the formula telling you that without evidence, pure bluffs do not get bet.

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

The chart above is the defense quota against a half-pot bet: `threshold = 0.66666667`, 884 combos continue and `1326 − 884 = 442` fold. Those 442 combos are the entire supply of fold equity at this size -- `442/1326 = 33.33%`, which is exactly `B/(P+B)`.

So the chart's job here is to **draw the ceiling**. Any `f` you claim above 33.33% at this node is an assertion that the opponent deviates from MDF, and it has to be paid for with data. A chart that plots fold-equity ceiling against size does not exist yet: it would need a new generator in `tools/gen_ranges.py` that draws the shrinking defense floor per size. Until then this lesson gives the table and the command, not an unsourced curve.

## 为何成立、何时失效 / Why it works, when it breaks

**What holds it up**: `f` is the probability that all opponents fold; `P` is everything collectable when they do; the two branch weights sum to one; chips are linear in utility.

**Where it stops holding**:

1. **Multiway pots.** Fold probabilities multiply, so fold equity collapses faster than intuition expects (Example 4). The algebra is in `pokergto.odds.defense_frequency_multiway`, and the independent defender assumption is recorded in the artifact's `provenance.assumptions`, because card removal makes independence only an approximation.
2. **Tournament bubble.** Chips are not linear. There the fold buys "survive one more hand", which is worth more than `f·P`, and the risk in the other branch is repriced too. The direction is not fixed; chapter 12 computes it hand by hand with `pokergto.icm`.
3. **The defender can raise.** This lesson's continue branch assumes he merely calls. If he raises, that branch splits into three results, and what you lose is `B` rather than `e·(P+2B) − B`. `02-08` develops this.
4. **Using fold equity to replace range thinking.** Whether a hand *belongs* in a betting range is settled by its quota (`02-04`); fold equity only says whether the action makes money. Blurring the two produces "he folds a lot, so I can bluff with anything".
5. **`f` with no source.** Every `f` in this lesson is either a declared input or the threshold derived from `1 − MDF`. A real opponent's actual fold frequency at a node is not available in this repository, so it is an **UNVERIFIED / 未核验** claim. Path to verification: decision-point samples in `data/src/spots/*.yaml`, responses collected by the trainer, and the counting conventions in `13-02`.

## 陷阱 / Common mistakes

1. **Treating fold equity as a property of your hand.** "I have two overcards, so I have fold equity" -- fold equity is the opponent's probability times the money in the middle. Your cards matter only through which opponents they can threaten.
   *Cost*: against a floor-holding defender `EV = 0`, and every bluff you make is tuition. Check: `poker mdf --pot 10 --bet 5` returns 66.67%, and the 33.33% you need is its complement.
2. **Double-counting the branches.** The usual mis-writing is `EV = f·P + e·(P + 2B)`, which drops the `(1 − f)` weight and the `− B`.
   *Cost*: Example 3's `+0.6255` becomes `0.4×12 + 0.191489×42 = 12.84`, a twentyfold overestimate. Run it through `pokergto.ev.ev_bet` once and the missing parentheses show up.
3. **Reading a per-player fold rate as the joint one.** Two opponents each folding 70.71% gives a joint 50%, not 70.71%.
   *Cost*: Example 4's break-even bluff gets booked as `+4.8` a try, so you keep running multiway bluffs that only look profitable in your own notes. Read `joint_defense` from `poker mdf --pot 12 --bet 12 --opponents 2`.

## 练习 / Drills

- From memory: the fold rate you need at `1/4, 1/3, 1/2, 2/3, 1, 2` times pot. Check with `poker odds --pot 10`.
- A nine-out draw, pot 12, shove 15. Compute the EV at call rates of 100%, 70% and 50% with `ev_shove`, then find the call rate at which the shove turns negative.
- Inverse: you bet 10 into 20 and the opponent defends 55% of the time. What is the air hand's EV? (`f = 45%`.)
- Three-way pot, `P = 24, B = 12`: how much must each player fold for your bluff to break even? (Hint: `poker mdf --pot 24 --bet 12 --opponents 3`.)
- Build a "fold equity source table": for your three most frequent nodes, write your estimate of `f` and the number of hands behind it. Where there are no hands, write `no source -- assume 1 − MDF`.

## 自测清单 / Self-check

- [ ] I can say which term of `EV(bet)` fold equity is, and write the full template.
- [ ] I can prove that a pure bluff earns exactly zero against MDF-correct defense.
- [ ] I can give the ceiling on `f·P` and explain why equilibrium never reaches it.
- [ ] I can separate per-player from joint fold rate, and quantify the difference in chips.
- [ ] Before I bet, I can name the data behind my `f` -- or admit that it is an unverified claim.

## 来源与置信度 / Provenance and confidence

Every number here is computed in this repository. No frequency chart from a commercial solver or a paid course is used anywhere in this lesson.

| Content | Source type | Location / reproduce with |
|---|---|---|
| `EV(bet) = f·P + (1−f)(e(P+2B)−B)` and `EV(bluff)` | `derived` | `src/pokergto/ev.py#ev_bet`, `#ev_pure_bluff`; derivation above |
| Example 1's −3.5 / 0 / +1.0 / +2.5 | `derived` | `PYTHONPATH=src python -c "from pokergto.ev import ev_pure_bluff as e; print(e(10,5,0.4))"` |
| Example 3's −6.9575 and +0.6255 | `derived` | `PYTHONPATH=src python -c "from pokergto.ev import ev_shove; print(ev_shove(12,15,0.191489,1)); print(ev_shove(12,15,0.191489,0.6))"` |
| Nine outs: 19.1489% and 34.9676% | `derived` | `data/gen/tables/table.01-03.draw-probability-exact-vs-rule.json` |
| Example 4's 29.2893% per player and 50% joint | `derived` | `poker mdf --pot 12 --bet 12 --opponents 2 --json` |
| Fold-frequency and MDF columns | `derived` | `data/gen/tables/table.02-03.mdf-vs-sizing.json` |
| Independent defender assumption in the multiway formula | `derived`, with a stated approximation | `pokergto.odds#defense_frequency_multiway`; card removal makes it approximate, recorded in `provenance.assumptions` |
| Real opponents' actual fold frequencies per node | **UNVERIFIED** | No data in this repository yet; path: `data/src/spots/*.yaml` + trainer responses + `13-02` |

## 术语 / Terms

<!-- terms: fold-equity, fold-frequency, expected-value, ev-decomposition, bluff, minimum-defense-frequency, semi-bluff, pot, bet, range -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| FE | 弃牌赢率 | fold equity | `f·P`: an amount of money, not a probability |
| — | 弃牌频率 | fold frequency | the opponent's fold probability `f`, FE's multiplier |
| EV | 期望值 | expected value | the sum of the two branches |
| — | 期望值分解 | EV decomposition | splitting an action by the opponent's reply |
| — | 最低防守频率 | minimum defense frequency | `P/(P+B)`, which sets the ceiling on `f` |
| — | 半诈唬 | semi-bluff | `e > 0`, so its threshold sits below a pure bluff's |
