# Why small sizes exist: converting pot fraction into defence burden

<!-- hands: 2 -->
<!-- terms: pot-fraction,min-bet,minimum-defense-frequency,required-equity,fold-frequency,defend,bet-size,betting-frequency,bluff-to-value-ratio,value-bet,bluff,combos,board-texture -->

## 本节目标 / Objectives

- Translate a pot fraction into three things and state them in absolute chips: how many combos the opponent must continue with, what equity that call costs them, and what fold frequency my bluff needs.
- Derive "the minimum fold rate this size requires" and its inverse "the fold rate this spot supplies caps the largest size I can use", and produce the chip figures on a 6bb pot.
- Name the conditions that rule the small size out -- short fold supply, a range sitting entirely above 1/2 equity, and the table's minimum-bet line -- and say which of those the engine actually computes.

## 前置知识 / Prerequisites

- `02-03` minimum defense frequency (MDF): `MDF = p/(p+b)`; this lesson converts it into a combo quota.
- `04-01` the division of labour between frequency and range: the "why does it exist" argument here uses that lesson's frequency term and does not re-derive it.
- `02-04` the size fixes the value-to-bluff mix; `table.02-04.bluff-value-ratio` is the main evidence below.

## 核心原理 / The principle

A small size is not a cautious choice, it is a conversion: **the smaller `b` is, the larger `MDF = p/(p+b)` becomes, the more combos the opponent must continue with, and the lower the fold rate `b/(p+b)` my bluff needs.** One third pot exists because it lands all three of those in usable territory at once -- it demands 75% defence (994.5 combos) while asking for only 25% folds to break even. This is a `derived` claim, straight out of `pokergto.odds`.

<!-- provenance: kind=derived verified=true -->
> Derived at: `src/pokergto/odds.py#minimum_defense_frequency`, `#required_fold_frequency`, `#value_to_bluff_ratio`; the combo counts come from `data/gen/ranges/range.04-02.mdf-floor-vs-third-pot.json`.

## 推导 / Derivation

Notation: `p` is the chips in the pot before the bet, `b` the amount added, and the fractional size is `s = b/p`.

### Step one: convert the size into a defence quota

```
MDF = p/(p+b) = 1/(1+s)          combos that must continue = 1326 · MDF
```

`1326` is not quoted from a book, it is counted by the engine: `ALL_COMBOS` in `src/pokergto/cards.py` has length 1326 (verified with `python -c`). Size and quota are therefore an inverse table:

```
s = 1/6  ->  MDF = 6/7 = 85.71%  ->  1136.5714 combos
s = 1/4  ->  MDF = 4/5 = 80.00%  ->  1060.8000 combos
s = 1/3  ->  MDF = 3/4 = 75.00%  ->   994.5000 combos
s = 1/2  ->  MDF = 2/3 = 66.67%  ->   884.0000 combos
```

**The row that produces `MDF = 75%` is exactly `s = 1/3`**: solving `1/(1+s) = 3/4` gives `s = 1/3`. One third pot is not a habit, it is the solution of "demand three quarters of the range to continue".

### Step two: the bluff side of the same coin

```
fold rate a bluff needs  f* = b/(p+b) = s/(1+s)
```

A defender who continues at exactly `1 − f*` makes air indifferent (the first boundary in `04-01`); at `s = 1/3` that is `f* = 1/4`. The move that matters here is **solving the same equation for `b`**, which turns it into a size ceiling set by fold supply:

```
b ≤ f·p/(1−f)
```

This is only multiplication and division, but it assumes `f < 1` so that the denominator is positive -- against an opponent who never folds there is no ceiling, because no size is worth bluffing at all. It converts "why one third pot" into a question answerable per spot: **how many folds does this spot actually supply?**

```
f = 0.20  ->  b ≤ 0.25p   (quarter pot)     f = 1/3  ->  b ≤ 0.5p
f = 0.25  ->  b ≤ 0.3333p (that is third pot)  f = 0.50 ->  b ≤ 1.0p
```

### Step three: what the small size costs you in ratios

Shrinking the size raises the defence quota, but how wide a calling range you are inviting is fixed by their price: `equity_needed_to_call = b/(p+2b)`, which is `20%` at `s = 1/3`. At the same time the bluff share inside *your* betting range is nailed to the size by `s/(1+2s)` = 20%, i.e. value:bluff = 4:1 (the 1/3-pot row of `table.02-04.bluff-value-ratio`). **The smaller the bet, the less air it may contain**: 1/4 pot demands 5:1, 1/6 pot demands 7:1. A small size is therefore not "just bet something"; it is a ticket only a range with a dense enough value tier can afford.

## 直觉 / Intuition

Read a small size as a **tax bill**, not a threat: one third pot is not frightening anyone, it says "you must answer with a large share of 994.5 combos, and answering costs you only 2bb". Its mechanism is a quota, not fear.

Both sides of that bill carry numbers: the opponent is asked to defend 75%, and needs only 20% equity to do it -- so "he continues with almost his whole range" is the *expected result* of a small bet, not its failure. The only way the small bet fails is: you expected 25% folds and got 20%.

And why not go smaller, to 1/6 pot: the quota rises to 85.71% while your bluff allowance collapses to 12.5% (7:1), which means the size can only be used for value. "Small" has a floor, and the floor is set by your own range composition.

## 算例 / Worked examples

**Example 1 -- one third pot converted to a quota (`p = 6bb, b = 2bb`).** `python -m pokergto mdf --pot 6 --bet 2` → `MDF = 0.7500`. Combos `1326 × 0.75 = 994.5` (picture in the Range chart section); only `331.5` combos may fold. Equity needed to call `2/(6+4) = 20%` (`pokergto.odds#equity_needed_to_call`; the same module's `pot_odds(6,2) = 3` uses the convention "pot before the bet divided by the call", and switching to the "risk 2 to win 8" 4:1 wording lands on the same 20%). My air needs 25% folds.

**Example 2 -- fold supply caps the size (`p = 6bb, f = 0.2`).** The ceiling is `0.2/0.8 × 6 = 1.5bb`, exactly quarter pot. Measured air EV: 1bb `+0.400000bb` · 1.5bb `0.000000bb` · 2bb `−0.400000bb` · 3bb `−1.200000bb` (`ev_pure_bluff`). **Same pot; drop the fold rate from 25% to 20% and a third-pot bet turns from break-even into a 0.4bb loss per hand.** Real equity moves the ceiling: `Td8c` holds `0.219128` against BB's calling range on `Kh7s3d`, and at the same `f = 0.2` its ceiling is `2.085128bb` (`0.3475p`) -- equity buys back a little size.

**Example 3 -- the price of under-defending (`p = 6bb, b = 2bb`).** Every 10 percentage points the opponent stops defending hands air `Δ·(p+b) = 0.10 × 8 = 0.8bb` per attempt; 15 points is `1.2bb`. Measured: `ev_pure_bluff(6,2,0.35) = 0.8` and `ev_pure_bluff(6,2,0.40) = 1.2`. The same conversion applies to small sizes, but because `p+b` is small the identical error is far cheaper than against an overbet (`04-03` supplies the comparison: 8bb against 60bb).

**Example 4 -- a multiway pot dilutes the quota (`p = 6bb, b = 2bb`, two opponents).** `python -m pokergto mdf --pot 6 --bet 2 --opponents 2` → each defends `d = 0.5000`, jointly `0.7500`. **Each player only needs 50%, yet the table's total defence is still 75%.** In a multiway pot the small size's defence-burden effect moves entirely onto the head count: the quota you demand is unchanged, while the difficulty of getting 25% to fold everyone multiplies.

## 生成表 / Generated tables

The value-to-bluff column is the main evidence of this section: "small" is not free, it requires a value-dense range.

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

The call-equity table shows the price a small size offers: one third pot asks 20%, so almost any draw clears it.

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

Whether a small size is ruled out on a given board depends on whether that line can still hold the nuts, which is what `is_capped` answers -- a computation, not an opinion. All six rows use ranges authored for teaching (`provenance.assumptions` records this), not solved strategies.

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

**Hand 1 (`hand.04-02-quota-is-not-a-hand-decision`) -- 6-max cash. BTN opens 3bb, BB (hero) calls, pot 6bb. Flop `Kh7s3d`, BTN bets 2bb (one third pot), hero holds `QdJd`.**

- Quota: `MDF = 6/(6+2) = 75%`, i.e. 994.5 combos of the defending range -- hero's own BB range here -- must continue (`python -m pokergto mdf --pot 6 --bet 2`).
- This hand: `python -m pokergto equity "QdJd" "AKs,AQs,ATs,KQs,AKo,AQo,99,77" --board "Kh7s3d"` → `0.161202`, below the 20% price. Call EV `0.161202 × 10 − 2 = −0.387980bb`.
- But BTN's betting range is not value only. Add `86o,75o` and it is 76 combos of which 24 are air (bluff share `31.58%`, above the `20%` a third-pot bet needs for indifference): `python -m pokergto equity "QdJd" "AKs,AQs,ATs,KQs,AKo,AQo,99,77,86o,75o" --board "Kh7s3d"` → `0.300926`, call EV `+1.009260bb`.
- Decision: call, and state the reason precisely -- **the 75% is a quota about BTN's betting range, the 20% is a price about this hand**; neither number answers the other's question. If BTN bet only value here, the same hand becomes a fold worth `−0.388bb` per attempt. His bluff share is a declared input, not a measured population stat from this repository.

**Hand 2 (`hand.04-02-third-pot-not-available`) -- same table, same flop `Kh7s3d`, pot 6bb. This time hero is on the button with `Td8c` (`0.219128` against BB's calling range), and BB checks. The deciding quantity is fold supply: `f = 0.2`.**

- Size ceiling: `0.2/0.8 × 6 = 1.5bb`. Betting 2bb (one third pot) is `−0.400000bb` for air, while `Td8c` measures `+0.038256bb` -- barely positive, and its room disappears by half pot: 3bb gives `−0.411139bb`.
- Decision: bet `1.5bb` (quarter pot, gain `+0.262954bb`) or check; do not fire a third-pot bet to "apply pressure". This hand runs the title's conversion backwards: **measure the fold supply first, then choose the pot fraction**, rather than choosing a fraction and praying for folds.

## 范围图 / Range chart

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

This chart is the defence burden made visible: facing one third pot, combos are filled in strength order up to `MDF = 75%`, covering 994.5 combos (the `total_combos` field of `range.04-02.mdf-floor-vs-third-pot.json`). Read it the way `02-03` teaches -- **a quota, not a list**: 75% of combos must continue and the chart does not say which. The evidence that "one third pot exists" lives in the height of that line, not in the colour of any cell.

## 为何成立、何时失效 / Why it works, when it breaks

**Assumptions that make it hold:** heads-up, one street, `f` given as a declared input, folding worth `p` forgone. The quota conversion `1326 × MDF` additionally assumes the defender's range is the full 1326 combo space; a real defending range is narrower, so the quota must be recomputed against that range.

Where it stops applying:

1. **Fold supply below `b/(p+b)`.** One third pot asks for 25%. At `f = 0.2` it loses 0.4bb per hand and the ceiling drops to quarter pot (Example 2). This is the section's only hard constraint, and it is a function of `f`, not of the board.
2. **The whole range sits above 1/2 equity.** The `Kh7s3d4c` row of `table.03-01` puts hero's turn equity at `76.9775%`; Example 4 of `04-01` shows the gain rising monotonically with size at `e = 3/4`, with one third pot `1.875bb/hand` below the 2x-pot figure. **When your range contains no weak hands that need a small size for protection, the small size loses its reason to exist.**
3. **More than one defender.** Each needs 50% rather than 75% (Example 4) and everyone-fold probability is a product; importing the heads-up quota into a three-way pot over-demands defence, which `07-01` works out.
4. **The table's minimum-bet rule.** One sixth of a 6bb pot is 1bb and remains legal, but on a 1bb pot a third-pot bet can fall under the minimum bet. **This is not an engine result**: nothing in `pokergto` models betting-rule constraints, so it is a room rule (`min-bet`), labelled `reference` + **UNVERIFIED**.
5. **"Dry boards get a small c-bet" style texture advice.** No artifact in this repository maps `board-texture` onto an obtainable fold rate, so this lesson refuses to name board classes that "rule the small size in". The only texture effect that can be checked travels through equity and capping, as in item 2. Treat any "three-spade boards never bet small" claim as **UNVERIFIED**.

## 陷阱 / Common mistakes

1. **Treating one third pot as the default continuation bet.** It is a function of `f ≥ 25%`, not a default. *Cost*: with fold supply at 20%, air betting 2bb is `−0.4bb` per hand; the same bluff at 1.5bb is `0.0bb` (Example 2).
2. **Using MDF to decide a single hand.** In hand 1 the price says fold (`−0.387980bb`), BTN's 4:1 structure says call (`+1.009260bb`), and the 75% quota tells you neither. *Cost*: `1.009260bb` per hand for folding what should be called, `0.387980bb` for calling what should be folded -- both figures come from that hand.
3. **Believing a small size is "safe because little is risked".** The chips you risk are small, and so is everything you give up with your strong hands: at `e = 3/4, p = 6bb, f = 1/4` the gain is `1.125bb` at one third pot against `3.0bb` at 2x pot. *Cost*: `1.875bb` per hand. A small size is not cheap for strong hands; it is only cheap for weak ones.

## 练习 / Drills

- From memory, give the MDF, required fold rate and value-to-bluff ratio for 1/4, 1/3 and 1/2 pot using `python -m pokergto odds --pot 1`, then convert each MDF into combos with `1326 × MDF` and compare against `range.04-02.mdf-floor-vs-third-pot.json`.
- Solve for the size that makes `MDF = 0.8` (answer `0.25` pot), then for the size whose defence quota reaches 1200 combos (hint: `1200/1326 = 0.904977`, `s = 1/MDF − 1 = 0.105`, about `1/9.5` pot).
- Redo Example 2 on a 12bb pot: what is the ceiling in bb at `f = 0.25`? And at `f = 1/3`?
- Use `python -c` with `ev_pure_bluff` to verify that "defending Δ points less hands air `Δ·(p+b)` more" has a different slope at one third pot than at pot size, and report both slopes.

## 自测清单 / Self-check

- [ ] I can convert any pot fraction into MDF, a combo quota, the equity a call needs and the fold rate a bluff needs.
- [ ] I can write `b ≤ f·p/(1−f)` and explain why it makes size selection a function of fold supply.
- [ ] I know that one third pot corresponding to `MDF = 75%` solves an equation rather than naming a convention.
- [ ] I can name the two engine conditions that rule a small size out (fold supply, an all-above-1/2 range) and one that is not an engine condition (the minimum-bet rule).
- [ ] I can explain why "board texture decides the size" is still an unverified claim in this repository.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every chip figure in this lesson is computed by `pokergto`. No commercial solver output, third-party range chart or screenshot appears in it.

| Content | Source type | Location |
|---|---|---|
| Size → MDF / folds needed / value-to-bluff | `derived` | `data/gen/tables/table.02-04.bluff-value-ratio.json`, `pokergto.odds#value_to_bluff_ratio` |
| Equity needed to call | `derived` | `data/gen/tables/table.02-02.equity-needed-to-call.json` |
| 1326 and 994.5 combos | `derived` | `src/pokergto/cards.py#ALL_COMBOS` (measured length 1326); `total_combos` in `data/gen/ranges/range.04-02.mdf-floor-vs-third-pot.json` |
| Air and hand-specific EVs | `derived` | `pokergto.ev#ev_pure_bluff`, `#ev_bet`; every figure in Examples 2-3 was recomputed with `python -c` |
| Hand equity | `derived` | `python -m pokergto equity ...`, exact enumeration (`exact=true`) |
| Multiway quota | `derived` | `pokergto.odds#defense_frequency_multiway`; independence assumption as in `02-03` |
| Capped-range verdicts | `derived` | `data/gen/tables/table.03-02.capped-range-check.json`; ranges are teaching inputs |
| The fold rate `f` | declared input | **UNVERIFIED**: `f = 0.2` in Example 2 and hand 2 is set by this repository for teaching, not measured on any population. Read every ceiling as "if `f` is this value". |
| Minimum-bet rule | `reference` + **UNVERIFIED** | `min-bet` is a room rule; `pokergto` contains no model of it. |
| Board texture → obtainable fold rate | **UNVERIFIED** | No artifact here supports that mapping, so this lesson declines to publish a "which boards bet small" list. |

## 术语 / Terms

| Abbreviation | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 底池比例 | pot-fraction | this lesson writes a size as `s = b/p`; the engine itself reads `pot` and `bet` |
| MDF | 最低防守频率 | minimum-defense-frequency | `1/(1+s)`, converted below into a combo quota |
| — | 最小下注 | min-bet | the floor set by the rules of the table, not modelled here |
| — | 所需胜率 | required-equity | `b/(p+2b)`, the price a small size offers the caller |
| — | 弃牌频率 | fold-frequency | `f`, a declared input and the argument of `b ≤ f·p/(1−f)` |
| — | 价值:诈唬 | bluff-to-value-ratio | the reciprocal of `s/(1+2s)`; small sizes demand value density |
| — | 组合数 | combos | the quota unit; 1326 is every starting hand |
| — | 牌面质地 | board-texture | acknowledged only where it acts through equity and capping |
