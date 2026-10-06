# The bluff-to-value ratio: how indifference sets the mix

<!-- hands: 2 -->
<!-- terms: bluff-to-value-ratio, bluff, value-bet, bluff-range, value-range, indifference, bluff-frequency, alpha, pot, bet, combos -->

## 本节目标 / Objectives

- Re-derive the bluff share of a betting range, `B/(P+2B)`, from the single condition "a bluff-catcher is indifferent between calling and folding", instead of memorising a ratio chart.
- For any bet size, state the value-to-bluff mix immediately, and state which way it moves as the size moves.
- Refute the intuition "a bigger bet means a stronger, tighter range". The algebra says a bigger bet must carry **more** bluffs.

## 前置知识 / Prerequisites

- `02-01` Break-even percentage: risking `R` to win `W` needs `R/(R+W)` equity.
- `02-03` Minimum defense frequency (MDF): `P/(P+B)`. This lesson uses the same indifference move, just aimed at the other player.

## 核心原理 / The principle

On the river, pot `P`, we bet `B`. If the betting range holds `V` value combos and `N` bluff combos, the bluff share is

```
b = N / (V + N) = B / (P + 2B)
value : bluff = (P + B) / B
```

This is a `derived` claim. It needs one condition only -- the bluff-catcher must be indifferent -- and rests on no solver, no chart, no authority.

## 推导 / Derivation

Start with real chips, not with "pot fractions". Pot 12, we bet 6. The opponent holds a hand that **beats nothing but air**: it loses to every value hand, wins against every bluff, no chopping.

- He folds: he is back to zero. Under the convention from `02-03`, money already in the middle is gone in both branches and cancels.
- He calls: the pot becomes `12 + 6 + 6 = 24`. Winning takes 24 having paid 6, so `+18`; losing costs `−6`.

Let `b` be the bluff share of our betting range. The call's expectation:

```
EV(call) = b·18 − (1 − b)·6
indifference:  b·18 = (1 − b)·6
                    24b = 6
                     b = 6/24 = 0.25          ← 25% bluffs
```

Write it with general symbols: a win nets `P + B`, a loss nets `B`:

```
b·(P + B) − (1 − b)·B = 0
b·(P + 2B) = B
b = B / (P + 2B)
```

**Why the pot-fraction convention changes nothing.** Scale both `P` and `B` by any `k > 0`:

```
kB / (kP + 2kB) = B / (P + 2B)
```

The `k` cancels. The 12/6 hand and the `P = 1, B = 0.5` notation give the same `b = 25%`. Expressing size in pot units is a change of ruler, not a change of answer -- which is exactly why one sizing table can serve every stack depth in this curriculum.

The ratio follows from `b`:

```
value : bluff = (1 − b) : b = (P + B) : B
```

Note that `b` and the equity needed to call from `02-02` are **the same expression**, `B/(P+2B)`. That is not a coincidence: the bluff share is precisely the equity that makes a bluff-catcher's call break even. They differ only in whose question they answer -- the share says "how much air do I owe", the equity says "is this hand good enough to continue".

## 直觉 / Intuition

Read the ratio as one sentence: **every value bet has to escort a quota of bluffs, and the bigger the bet, the bigger the escort.**

- One third pot: one bluff for every four value hands.
- Pot: one bluff for every two value hands.
- Two times pot: two bluffs for every three value hands.

Why does it run this way? Because a big bet only earns when the opponent is willing to call, and his willingness depends on how much air he expects you to have. Bet big with value only and he folds every medium hand: your strong hands then win the small pot `P` and never the `P + B` they were betting for. The big size's *value* income is what dies first. To keep him calling you must load air into the range -- air is the tax a big size charges.

A small size is the opposite trade. One third pot demands only 20% bluffs, because a caller needs just 20% equity and is happy to call: your value income was always going to come from worse hands paying a small price. Escort is cheap.

So "big bet = strong range = tight" fuses two different things. A big bet should indeed be made with only part of your range; but that part must contain a *higher* share of air, not a lower one.

## 算例 / Worked examples

**Example 1 -- one third pot, `P = 12, B = 4`.** `b = 4/(12+8) = 20%`, ratio `16/4 = 4 : 1`.
With 24 value combos (`QQ,JJ,TT,99`; `poker range "QQ,JJ,TT,99"` returns 24) you are allowed `24/4 = 6` bluff combos.

**Example 2 -- pot, `P = 20, B = 20`.** `b = 20/60 = 33.33%`, ratio `40/20 = 2 : 1`.
The same 24 value combos now carry 12 bluff combos: twice the escort of Example 1.

**Example 3 -- two times pot overbet, `P = 20, B = 40`.** `b = 40/(20+80) = 40%`, ratio `60/40 = 1.5 : 1`.
24 value combos now need 16 bluffs. **This is the line that matters most in the lesson**: going from one third pot to two times pot multiplies the money at risk by 6 and multiplies the air your range must contain. It does not tighten anything.

**Example 4 -- asking the reverse question, "how big can I go".** Suppose the river gives you only 4 combos worth bluffing with (the missed flush draws). Then `b = B/(P+2B) ≤ 4/(4+24) = 1/7 ≈ 14.29%`.
Solving `B/(P+2B) = 1/7` gives `B = 0.2P`: **one fifth of the pot**. Check it: `equity_needed_to_call(1, 0.2)` returns exactly `0.142857`. A 24:4 structure therefore cannot support any size on the engine's standard ladder, because its smallest rung, one quarter pot, already demands 16.67% air.

**Example 5 -- side by side with MDF.** For a pot-sized bet: `MDF = 20/40 = 50%` and ratio `2 : 1`. Both come out of the same indifference condition; one is a frequency the defender owes, the other is a composition the bettor owes. Do not put them in the same column.

## 生成表 / Generated tables

The table below is computed by `pokergto.odds.sizing_table` with `P = 1`; it lists the bluff share and the mix for every size:

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

The same numbers have been checked from a completely independent direction: let CFR solve a toy game and read off the bluff share it converges to.

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

Compare `solved_bluff_share` with `algebra_bluff_share`: one third pot `0.20003` against `0.2`, half pot `0.250003` against `0.25`, pot `0.333366` against `0.333333`. One column is one line of algebra, the other is an iterative algorithm that was never told the answer (`adr/0002`).

## 实战牌局 / Live hands

**Hand 1 (`hand.02-04-river-over-bluff`) -- heads up, river `AcKd8s5h2c`, pot 20, we bet 20.**

Our betting range: value `QQ,JJ,TT,99` = 24 combos (`poker range "QQ,JJ,TT,99"`), bluffs `JTs,T9s,98s,QJs,T8s` = 20 combos (`poker range "JTs,T9s,98s,QJs,T8s"`).

- Actual bluff share `20/44 = 45.45%` against the `33.33%` a pot bet requires: **12.12 percentage points over quota**.
- The cost is computable to the chip. The opponent's bluff-catcher `KsQs`, which beats exactly those 20 bluff combos, calls for
  `PYTHONPATH=src python -c "from pokergto.ev import ev_call; print(ev_call(20,20,20/44))"` → `7.2727` chips.
  With the mix fixed (24 value + 12 bluffs, share `1/3`) the same call returns `0.0`.
- So eight surplus bluff combos convert a hand that was exactly break-even into one that prints 7.27 chips every time. You are not out-read; you are over-quota.
- Two repairs exist. Cut the bluffs to 12 combos, keeping the ones that block his calling hands. Or ask the reverse question -- how big would the size have to be for 20 bluffs to be exactly legal -- and solve `B/(20+2B) = 20/44`, which gives `B = 100`: five times pot, more than double the top of the engine's ladder, so not a size anyone can use. For this hand only the first repair is real. Note the direction, because it is easy to get backwards: **over-quota is absorbed by betting bigger, never smaller** -- the price is simply prohibitive.

**Hand 2 (`hand.02-04-value-heavy-small`) -- same river, pot 20, thick value and almost no air.**

Value is still 24 combos, but the only bluff candidates left are `T8s`: 4 combos.

- Share `4/28 = 14.29%`. Example 4 says the largest size this supports is one fifth of the pot.
- So this range bets **small** with its value hands and checks most of its air. The reason is not that small bets are safer, it is the price you offer: a worse hand calls only if its equity reaches `B/(P+2B)`, and moving from one quarter pot to pot lifts that bar from 16.67% to 33.33% while you can supply just 14.29%. Every worse hand folds cleanly and your value income locks itself out.
- At one fifth pot the bar equals your 14.29% exactly: worse hands are indifferent, which is the last moment at which you can still be paid `P + B`.
- "I have a good hand so I should bet big" is wrong in this algebra. Size is chosen first by the air you can pay, then by which value hands that size suits.

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

The chart above is the **defender's** quota against a half-pot bet (`threshold = 0.66666667`, 884 of the 1,326 combos). `tools/gen_ranges.py` builds it from `pokergto.odds.minimum_defense_frequency`, `provenance.kind = derived`.

For this lesson the chart supplies the other half of the denominator: 66.67% defense means 33.33% folds, and that fold share is what a half-pot bet's "one bluff per three value hands" is measured against. Same picture, two readings: `02-03` asks "how much do I keep", this lesson asks "how much do they keep, and therefore how much air do I owe".

To be plain about it: this lesson's own object -- bluff share plotted against size -- exists today only as a table (`table.02-04.bluff-value-ratio`). There is no range chart generated from the bettor's side. Turning it into a chart needs a new generator in `tools/gen_ranges.py` that fills combos by betting-range share rather than by defense floor; that belongs to chapter 04.

## 为何成立、何时失效 / Why it works, when it breaks

Assumptions that hold it up: **the river** (no card can change who wins), one decision point, the bluff-catcher either wins or loses (no chops), and both sides responding to what the other does.

It stops being the number to execute when:

1. **It is not the river.** A semi-bluff has a way to win on a later street and should not sit in `N`. Ratios that include future improvement are chapter 04's work (`04-06`, semi-bluffs).
2. **The defender can raise.** This derivation charges pure air `−B` when it gets raised and folds -- the same `−B` it would have paid anyway, so air's arithmetic survives. But the medium hands in your range re-route, and the mix has to be recomputed. `02-08` takes that up.
3. **There are chops.** Equity is defined as `e = P(赢) + ½·P(tie)`; a board that lets `AA` run into `AA` shifts `b` slightly. The closed form here ignores ties.
4. **More than one size is available.** The ratio is per size. The same hand belongs to a different sub-range at one third pot and at two times pot, so a single ratio for the whole range is a fiction of one-size games.
5. **The opponent defends badly.** `b` is the composition that stops you being exploited, not the one that earns most. Against someone who over-folds, the right move is to exceed quota (chapter 13). You need the baseline before you can spend the deviation.

One preview, clearly labelled: because a big size charges air, in practice big sizes pair with **极化 / polarized** shapes (top of the range plus bottom, nothing in between) and small sizes with **合并 / merged** shapes that also include medium hands. This lesson does not prove that. It is chapter 04's conclusion (`04-05`), and until `src/pokergto/theory/` derives it and the two-street toy game reproduces it, the claim is **UNVERIFIED / 未核验**. Path to verification: a sizing derivation in `theory/` plus a reproduce-the-shape check in chapter 08.

## 陷阱 / Common mistakes

1. **Reading the MDF column as the ratio column.** At one third pot: `MDF = 75%`, the fold frequency a bluff needs is `25%`, the bluff share is `20%`, and the ratio is `4 : 1`. Inside one row, 25% and 20% sit five points apart and mean completely different things: the first is the share *the opponent* should fold, the second is the share *your range* must contain. (And "equity needed to call" is 20% as well, because it is literally the same expression.)
   *Cost*: believing "they fold 25%, so I bluff 25%" makes you carry one bluff per three value hands where the size demands one per four. On a pot-sized bet that surplus is worth 7.27 chips to a single bluff-catcher (Hand 1). Run `poker odds --pot 1` and read all four columns at once; it is faster and surer than a memorised chart.
2. **Believing a big bet means a tight range.** Two times pot requires the highest bluff share on the whole ladder, 40%.
   *Cost*: a value-only overbet gets folded to by everything medium, so your strong hands collect `P` and never `P + B`; and the rare time you do bluff, you are risking two pots. Two losses from one backwards intuition.
3. **Counting hand classes instead of combos.** `AKo` is 12 combos, `AKs` 4, `AA` 6 (`table.01-01.combo-decomposition`).
   *Cost*: three value classes with one bluff class *looks* like 3:1 and is 18:4 = 4.5:1 in combos; you cannot tell whether you are over or under quota without converting. Convert first, then verify with `poker range "..."`.

## 练习 / Drills

- From memory: the bluff share and mix for `1/4, 1/3, 1/2, 2/3, 3/4, 1, 1.5, 2` times pot. Check with `poker odds --pot 1`.
- Reverse: you have 8 combos suited to bluffing. How many value combos do you need for a pot-sized bet to be unexploitable? (`2 : 1` → 16.)
- Reverse again: 30 value combos and 5 bluff combos -- what is the largest size you can use? Solve `B/(1+2B) = 5/35`.
- In Hand 1, after cutting the bluffs to 12 combos, is `KsQs` a call or a fold? Write out `EV(call)`.
- Cross-check `02-03`: a pot-sized bet facing two opponents, each defending 29.29% and jointly 50%. Is the bluff share still `33.33%`? (Hint: what the denominator counts has changed.)

## 自测清单 / Self-check

- [ ] I can derive `b = B/(P+2B)` from the bluff-catcher's indifference and say why the chip unit is irrelevant.
- [ ] I can state the mix for six sizes and name which one demands the most air.
- [ ] I can explain in words why a bigger bet needs *more* bluffs, not just restate the formula.
- [ ] I know that `b` and the equity needed to call are one expression answering two questions.
- [ ] I can list three situations where this lesson's number is not the target, and say why the polarized/merged preview is still unverified.

## 来源与置信度 / Provenance and confidence

Every number below is computed in this repository. No range chart or strategy output from a commercial solver or a paid course appears anywhere in this lesson.

| Content | Source type | Location / reproduce with |
|---|---|---|
| `b = B/(P+2B)`, ratio `(P+B)/B` | `derived` | `src/pokergto/odds.py#bluff_fraction_at_indifference`, `#value_to_bluff_ratio`; derivation above |
| Sizing/ratio table | `derived` | `data/gen/tables/table.02-04.bluff-value-ratio.json`, `poker odds --pot 1` |
| Solver cross-check of the bluff share | `derived` | `data/gen/tables/table.08-04.solver-vs-algebra.json`, gates in `src/pokergto/solver/proofs.py` |
| 24 and 20 combos | `derived` | `poker range "QQ,JJ,TT,99"`, `poker range "JTs,T9s,98s,QJs,T8s"` |
| Hand 1's `EV(call) = 7.2727` | `derived` | `PYTHONPATH=src python -c "from pokergto.ev import ev_call; print(ev_call(20,20,20/44))"` |
| Defense quota chart | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` (assumptions in `provenance.assumptions`) |
| The "range shape chooses the size" reading in Example 4 | `reference` | Constructed teaching example; combo counts skip card removal, exact counts via `pokergto.cards.remove_cards` |
| Big sizes suit polarized shapes, small sizes merged | **UNVERIFIED** | Chapter 04's conclusion; verify via `src/pokergto/theory/` plus the two-street toy game in chapter 08 |

## 术语 / Terms

<!-- terms: bluff-to-value-ratio, bluff, value-bet, bluff-range, value-range, indifference, bluff-frequency, alpha, pot, bet, combos -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| B:V | 诈唬与价值比 | bluff-to-value ratio | `(P+B)/B`, value first, bluff second |
| α | 河牌诈唬率 | alpha | the bluff share `b = B/(P+2B)` of the betting range |
| — | 诈唬频率 | bluff frequency | combo-weighted share, not a count of hand classes |
| — | 价值下注 | value bet | worse hands are expected to call; not "this hand wins" |
| — | 无差别 | indifference | the condition that two actions have equal expectation |
| — | 底池 / 下注 | pot / bet | `P` before the bet, `B` the amount added |
