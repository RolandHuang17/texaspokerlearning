# Who already has the straight on this flop: nut advantage, not equity

<!-- hands: 2 -->
<!-- terms: range-advantage, equity-advantage, nut-advantage, the-nuts, capacity, range, equity, combos, board, flop, turn, bet-size, minimum-defense-frequency, bluff-to-value-ratio, bluff, value-bet, showdown -->

## 本节目标 / Objectives

- Explain nut advantage through each range's **capacity for made hands**, and name the decision it settles that equity advantage cannot.
- Given one board and two ranges, recompute both the equity edge and the nut edge, and point at the two rows of this lesson's generated table where the columns **point in opposite directions**.
- State each number's denominator, its reference point and where it stops holding, so that "my range is better" stops being a strategy sentence.

## 前置知识 / Prerequisites

- `01-07` reading a 13x13 grid: what a cell counts. Both columns here are combo-weighted, never class-weighted.
- `02-04` the bluff-to-value ratio: a size dictates a value-to-bluff mix, and the value half has to be filled by real hands.
- `02-03` minimum defense frequency: MDF is a quota; it does not say which hands pay it.
- `01-02` blockers and removal: needed to understand the sentence "the range was not narrowed to the board".

## 核心原理 / The principle

On one board, "who is better on average" and "who stands on the roof when the money goes in" are two different numbers:

```
equity_edge = hero_equity − villain_equity          ← who may bet with FREQUENCY
nut_edge    = hero_nut_share − villain_nut_share     ← who may bet with a BIG SIZE
```

`hero_nut_share` is the share of hero's combos that sit on the highest hand-strength tier **the two ranges can currently reach**. Both are computed by `pokergto.theory.range_advantage`, so both are `derived`. The two ranges themselves are illustrative inputs authored in this repository, which makes them `reference`.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Derivation: the next section. Generated table: `tools/gen_tables.py` -> `data/gen/tables/table.03-01.equity-vs-nut-advantage.json`.

## 推导 / Derivation

Define every symbol before using it. `H` and `V` are the two ranges, `w_i` is the weight of combo `i` (0 or 1 in the example ranges), `B` is the board.

**Equity averages over every river.** A flop has `|Ω| = 1176` completions (`runout_boards(B)`, which is `C(49,2)`):

```
hero_equity = Σ_{ω∈Ω} Σ_{i∈H} Σ_{j∈V} w_i w_j · ½·1[s_i(ω)=s_j(ω)] + 1[s_i(ω)>s_j(ω)]
              ─────────────────────────────────────────────────────────────────────────
              Σ_{ω∈Ω} Σ_{i∈H} Σ_{j∈V} w_i w_j · 1[i and j share no physical card]
```

That last clause in the denominator is the load-bearing one: `range_equity` drops combos that collide with the board or with the other range while enumerating, so equity **is** conditioned on the board.

**Nut share never walks Ω.** It only looks at the board as it stands:

```
T        = max( max_{i∈H} s_i(B), max_{j∈V} s_j(B ) )   ← the best score either range holds now
share(H) = Σ_{i∈H, s_i(B)=T} w_i / Σ_{i∈H} w_i
nut_edge = share(H) − share(V)
```

Three structural differences give the whole lesson:

1. **Future cards or not**: equity averages over 1176 rivers; nut share reads the board as printed.
2. **Relative or absolute**: equity is a **pairwise** comparison of `i` against `j`; nut share is a **level crossing** against one absolute reference `T`. Crossing is 0/1, averaging is continuous.
3. **The denominator**: `nut_advantage` divides by the combos as written on paper (`Advantage.hero_combos` calls `total_combos()` directly), **not** narrowed to the board. On `Kh7s3d` hero's denominator is 52, not the 44 that survive removing `Kh`, `7s`, `3d`.

Point 3 is the step in this section that could silently be wrong, and it is a division whose denominator is never checked for sanity. An empty range does fail loudly: `nut_advantage` raises `InputError("both ranges need combos")`. A denominator that is not empty but contains **physically impossible combos** does not raise at all; it just shrinks the share. The artifact records that in `provenance.assumptions`, and the worked examples below give the narrowed numbers next to the printed ones rather than hiding the gap.

The definitions then give the central fact immediately: **neither edge implies the other**. `equity_edge > 0` does not require `nut_edge > 0`, because one is an average and the other is a tail. Rows 2 and 3 of the next section are the two directional counterexamples, and the artifact carries a check named `edges_disagree` that asserts at least one row really does disagree -- a table where the two always agree would make this lesson decorative.

## 直觉 / Intuition

Equity advantage is **the height of the water**. Nut advantage is **who owns the roof**.

- High water means a small punt wins often: that is what governs whether you bet, and how often.
- A high roof means that when the money really goes in and somebody raises, you hold a hand that can go. That is what governs your **maximum** size.
- The bigger the size, the more it is a formal challenge to be raised, and the only insurance against a raise is that the top tier of your range genuinely exists. `02-04` demands value : bluff = 1.5 : 1 at two times pot, and the word "value" has to be cashed by rooftop hands, not by an average.

Mental model: read the two columns of `table.03-01` together and ask one question first -- **do they point the same way?** When they do, you only have to choose a size. When they do not, frequency and size become two independent decisions, and any blanket verdict of "my range is better here" gets one of the two wrong.

## 算例 / Worked examples

All four rows come from `advantage(hero, villain, board, mode="exact")`: exact enumeration, no sampling error. The reproduce command is given for each.

**Example 1 -- a dry high board, `Kh7s3d` (hero = CO opener, 52 combos; villain = BB caller, 64 combos).**
Hero equity 71.5272%, equity edge **+43.0545%**. The best score either range holds here is trips nines -- `99`, 6 combos -- so hero's nut share is 6/52 = **11.5385%**, villain's is 0, nut edge **+11.5385%**. Both columns agree: hero may bet often and bet big.
Narrow hero's range to the board and 44 combos survive, `77` drops to 3, and the nut share becomes 3/44 = **6.8182%**: same direction, roughly half the magnitude. That gap is difference 3 above, not a rounding artifact.
Reproduce: `python -m pokergto equity "AKs,AQs,ATs,KQs,AKo,AQo,99,77" --range-villain "KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s" --board "Kh7s3d" --json` (prints `"equity": 0.715272`, digit for digit with the table).

**Example 2 -- a low connected board, `9h6d3c` (hero = BTN opener, 66 combos; villain = BB caller, 60 combos).**
Hero holds only 36.8154% equity, equity edge **−26.3691%**: on average hero is far behind. But the best score on the board is trips nines, and all 6 of those combos sit in **hero's** range, while none of villain's 60 do: hero nut share 6/66 = **9.0909%**, nut edge **+9.0909%**.
**The losing side owns the roof.** The frequency column says villain, the size column says hero -- that is precisely the row where the artifact prints `can_bet_often = villain` next to `can_bet_big = hero`.
Narrowed: 63 legal hero combos, nut share 3/63 = **4.7619%**.

**Example 3 -- two-tone with a flush draw, `As9s5d` (hero = CO opener, 54 combos; villain = BB caller, 36 combos).**
Hero equity 61.0233%, equity edge **+22.0466%**. The best score here is again trips nines, and all 6 combos of `99` belong to **villain**: hero nut share 0.0000%, villain 6/36 = 16.6667%, nut edge **−16.6667%**.
The mirror image of Example 2: the leading side has no roof. This row prints `can_bet_often = hero`, `can_bet_big = villain`.
Narrowed: villain keeps 29 legal combos, nut share 3/29 = **10.3448%**.

**Example 4 -- the turn after Example 1's flop, `Kh7s3d4c` (hero 50 combos, villain 48 combos).**
Equity edge **+53.9550%**, nut edge **+12.0000%** (the top tier is trips sevens, `77`, 6 combos out of 50). Narrowed: 3/40 = **7.5000%**.
This row is **not** "Example 1 after one card": the turn ranges are separately authored illustrative inputs (`44` enters, and the suited/offsuit mix changes). Subtracting row 4 from row 1 and calling the result "the marginal effect of one card" is an inference this section has no basis for. How streets actually connect is `03-03`'s subject.

## 生成表 / Generated tables

<!-- BEGIN AUTO:table.03-01.equity-vs-nut-advantage -->
|    Board |             Hero |          Villain | Hero equity | Equity edge | Hero nut share |  Nut edge | Who bets often | Who bets big |
|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
|   Kh7s3d |        CO opener |        BB caller |    71.5272% |    43.0545% |       11.5385% |  11.5385% |      hero      |     hero     |
|   9h6d3c |       BTN opener |        BB caller |    36.8154% |   -26.3691% |        9.0909% |   9.0909% |    villain     |     hero     |
|   As9s5d |        CO opener |        BB caller |    61.0233% |    22.0466% |        0.0000% | -16.6667% |      hero      |   villain    |
| Kh7s3d4c | CO opener (turn) | BB caller (turn) |    76.9775% |    53.9550% |       12.0000% |  12.0000% |      hero      |     hero     |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.theory.range_advantage#advantage`

<!-- generated by: tools/gen_tables.py from pokergto.theory.range_advantage::advantage -->
<!-- END AUTO:table.03-01.equity-vs-nut-advantage -->

Three rules for reading it:

1. The `Hero`/`Villain` columns name a **role**. The ranges are the illustrative inputs written in `ADVANTAGE_SPOTS` inside `tools/gen_tables.py`; they are not a solved strategy.
2. `Who bets often` is the sign of `equity_edge`; `Who bets big` is the sign of `nut_edge`. They are two verdicts on purpose; collapsing them into one "who is better" is the error this table exists to make visible.
3. Every board has three or four cards, none has five: `range_equity` raises `InputError("a board of five cards has no equity left to compute")`. After the river there is only a showdown.

The sizes themselves oblige a mix, which is why nut capacity matters at all:

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

Read the two tables together: Example 3's CO would like two times pot, which demands 1.5 : 1, yet it holds zero combos on the top tier; Example 2's BTN has 9.09% of its range up there, which is exactly what a 1.5 : 1 mix needs -- a small value segment carrying a large size.

## 实战牌局 / Live hands

**Hand 1 (`hand.03-01-low-connected-flop`) -- 6-max, blinds 0.5/1. BTN opens 2.2 bb, BB calls 1.2 bb; pot 2.2 + 1 + 1.2 = 4.4 bb. Flop `9h6d3c`.**

The ranges are Example 2's: BTN 66 combos with nut share 9.0909%, BB 60 combos with 0%, BTN equity 36.8154%.

- **The decision: should BTN use two times pot (8.8 bb) rather than one third pot?** One third pot needs `f* = 0.250426` folds, gives BB `MDF = 0.749574`, and requires 0.200272 equity to call; two times pot needs `f* = 0.666667`, gives `MDF = 0.333333`, and requires 0.400000 (`python -m pokergto mdf --pot 4.4 --bet 8.8`).
- **BTN's two-times-pot range built at indifference**: value = the 6 combos of `99`, bluff = the 4 combos of `AJs` (`python -m pokergto range "99,AJs"` prints 10 combos), so value : bluff = 6 : 4 = 1.5 : 1, exactly the ratio the sizing table demands at two times pot.
- **How should BB answer?** Computed against BTN's 10-combo polarised range: BB's `T9s,98o,97o,66,55` (40 combos) holds **56.0624%**; BB's `87s,76s,65s,54s,T8s` (20 combos) holds **39.4966%**, which is 0.5034 percentage points short of the 40% required; BB's whole 60-combo range holds **48.9628%**. So the 33.33% quota -- 20 of 60 -- is not the problem; which 20 pay it is.
- **What the wrong play costs.** If BTN refuses two times pot because "I only hold 9.09% of the roof and I am 26.37% behind on average", it is throwing away the only column that licenses the size. If BB folds all 40 of its call-worthy combos, it forfeits `ev_call(4.4, 8.8, 0.560624) = **+3.5337 bb**` per attempt, **141.35 bb** over the 40 combos. Calling with the 20 draw combos instead costs **−0.1107 bb** each: a hair short, and "a hair" is the measurement, not a vibe.

**Hand 2 (`hand.03-01-two-tone-flush-flop`) -- same table, CO opens 2.2 bb, BB calls 1.2 bb, pot 4.4 bb. Flop `As9s5d`.**

Example 3's numbers: CO 54 combos with 61.0233% equity, BB 36 combos with nut share 16.6667% (the 6 combos of `99`). The table says `can_bet_often = hero`, `can_bet_big = villain`.

- **The decision: may CO turn its frequency edge into a two-times-pot 8.8 bb bet?** Two times pot pushes BB's quota down to `MDF = 0.333333`, and CO would love that. But CO holds **zero** combos above BB's 12 set combos (`99` and `55`, which are 12/36 = 33.33% of BB's range).
- **The arithmetic when CO gets raised**: BB check-raise-shoves for 17.6 bb more. The pot before CO's call is 4.4 + 8.8 + 8.8 = 22.0 bb, CO faces 17.6 bb, so the requirement is `17.6/(22 + 35.2) = 0.307692`. CO's entire 54-combo range holds **6.4625%** against `99,55`. `ev_call(22.0, 17.6, 0.064625) = **−13.9035 bb**` per attempt, versus −8.8 bb for folding.
- **Conclusion.** CO's frequency stays -- one third pot, `f* = 0.250426` -- and its ceiling comes from the `nut_edge` column. Not because "the opponent might be strong", but because a combo-by-combo count shows CO has nothing that outranks the part of BB's range that would raise.

## 范围图 / Range chart

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

This is `02-03`'s half-pot MDF floor: combos filled in **preflop** strength order until they cover 884.0 of the 1,326 (66.67%). It appears in this lesson to make one thing unmissable: **the chart carries no board, therefore no nut information whatsoever.**

- The `@@` and `··` cells are a quota taken down a preflop ordering, not a strength ordering on any `board`. The same `AKs` cell is top pair ace kicker on `Kh7s3d` and an ace-high bluff on `9h6d3c`.
- Its denominator is likewise **not narrowed to a board**, which is exactly the same assumption class as point 3 in the derivation. Ask that question of every chart in this repository before reading a percentage off it.
- So the chart says "pay 884 combos" and this section says "here is how many of those combos can actually stand on the current top tier". Both are required; either alone gives the wrong size.

## 为何成立、何时失效 / Why it works, when it breaks

**What it requires**: that the two ranges are the distribution you are actually facing rather than "what he might have"; that the weighting is by combos; that the evaluator imposes one total order on every combo. All three live in `pokergto`, so both columns are `derived`.

Where it stops holding, or needs discounting:

1. **On an incomplete board nut advantage under-states the side holding draws.** `nut_advantage` measures against the best hand reachable **now**, not the best reachable after every runout. The artifact's `caption` and the module docstring both say so; here is the size of it. On `9h6d3c` BTN's nut share is 9.0909% and BB's is 0. Substituting each of the 49 possible turn cards in turn hands the top tier to BB on **19** of them (every `2`, `5`, `6`, `7`, `T`). Substituting all 49 x 48 = 2352 turn-and-river runouts: BB holds the top tier at the end on **1096** of them (**46.5986%**), BTN on **1308** (**55.6122%**). These are not complementary -- on 52 runouts one combo from each side ties at `T`, which is why the two counts sum above 100%. Read "BB nut share 0" as "BB is at 0 right now", never as "this line has no nuts for BB". How streets connect is `03-03`.
2. **The nut denominator is not narrowed to the board.** Across the four examples: 11.5385% -> 6.8182%, 9.0909% -> 4.7619%, 16.6667% -> 10.3448%, 12.0000% -> 7.5000%, all computed in this session. Equity **is** conditioned (collisions are dropped during enumeration) while the nut share is not, so the two columns of one table use different denominators. That is the current implementation, not a typo; read `6/52` as "six of the combos as written", never as "16.67% chance the opponent holds trips".
3. **`T` is the best of these two ranges, not the board's ceiling.** On `Kh7s3d` the reference for both columns is trips nines, while the strongest hand the board can produce at all is trips kings (`KK`). "Hero has the nut advantage" is therefore a **relative** claim, and both sides can simultaneously be capped against the ceiling -- which is the pair of concepts `03-02` separates.
4. **`near_nuts` does not do what its name suggests.** A "step" there is one unit of the evaluator's integer ordering, not one hand type. Measured on three-card boards: on `Kh7s3d` the smallest gap between two adjacent distinct strengths is 16 units and the gap between trips nines and trips kings is 368,640 units, so `near_nuts = 0,1,2,3` return identical shares. Do not let it define "second-nuts" for you.
5. **The equity column is all-in equity.** It averages to showdown with no later-street folding, so it over-states realisable value; that discount is `01-06`'s subject.

## 陷阱 / Common mistakes

1. **Sizing up on the equity edge alone.** Example 3's CO is 22.0466% ahead and holds zero rooftop combos.
   *Cost*: Hand 2 measured it -- calling a `99,55` shove is **−13.9035 bb** per attempt while folding loses 8.8 bb, so **5.1035 bb** of the bill is bought purely by confusing frequency with capacity.
2. **Reading a zero nut share as "this line has nothing".** Example 2's BTN has nut share 9.0909% against BB's 0%, yet BB holds 63.1846% equity; and BTN's 6 rooftop combos survive on only 30 of the 49 turn cards.
   *Cost*: folding BB's 40 call-worthy combos forfeits **+3.5337 bb** each, **141.35 bb** in total. That is the mirror image of "I paid my quota, with the wrong combos".
3. **Doing arithmetic across two tables.** `table.03-01` and `table.03-02` both use `9h6d3c` with the labels "BTN opener vs BB caller", but the ranges differ: 03-01's villain is `87s,76s,65s,54s,T8s,T9s,98o,97o,66,55` (60 combos), 03-02's omits `97o` (48 combos).
   *Cost*: villain's equity in "the same" matchup is 63.1846% on the 60-combo range and 61.2680% on the 48-combo one, **1.9166** percentage points apart; dividing 03-01's nut-combo count by 03-02's denominator produces a number neither artifact supports. Read each table's own `spec`.

## 练习 / Drills

- Reproduce row 1: `python -m pokergto equity "AKs,AQs,ATs,KQs,AKo,AQo,99,77" --range-villain "KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s" --board "Kh7s3d" --json`, and confirm `"equity": 0.715272`, `"exact": true`, `"iterations": 1176`.
- For all four examples run `nut_advantage(rng, rng2, board)` and `nut_advantage(rng.with_removed(*board), rng2.with_removed(*board), board)`, tabulate the eight numbers, and explain why every narrowed share is smaller.
- Author two ranges with class names only (`notation.parse` accepts `AKs`, `99`, `A5s-A2s` and rejects explicit combos such as `KsQs`) so that the two columns disagree, then verify and name the hand tier responsible.
- Quota in reverse: on `9h6d3c` facing BTN's two-times-pot 8.8 bb, BB's MDF needs how many of its 60 combos? BTN's value segment is the 6 combos of `99`; at 1.5 : 1 how many bluff combos belong with it? (Hint: 6/1.5 = 4, which is exactly `AJs`.)
- Say which hand type is `T` in Example 1 and which is `Kh7s3d`'s reachable ceiling, then name the two functions that use those two references.

## 自测清单 / Self-check

- [ ] I can write both formulas and say which one integrates over 1176 rivers and which one reads only the current top tier.
- [ ] I can point at the two disagreeing rows and state, for each, which single action the row forbids.
- [ ] I know the nut share divides by combos as written, and I can produce both the narrowed and the printed value for Example 2.
- [ ] I can explain that `nut_advantage` references the best of the two ranges, not the best the board allows.
- [ ] I can explain why "0% nut share" is a statement about **now**, not a verdict on the line.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every figure is computed in this repository or taken from a committed artifact. No commercial solver output and no paid-course range chart appears anywhere in this lesson:

| Content | Source type | Location |
|---|---|---|
| The four rows of equity and nut shares | `derived` | `data/gen/tables/table.03-01.equity-vs-nut-advantage.json`; `pokergto.theory.range_advantage#advantage` |
| Size to value : bluff mapping | `derived` | `data/gen/tables/table.02-04.bluff-value-ratio.json` |
| MDF floor chart | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` |
| 0.250426 / 0.333333 / 0.400000 sizing arithmetic | `derived` | `python -m pokergto mdf --pot 4.4 --bet 1.47` and `--bet 8.8` |
| 56.0624% / 39.4966% / 48.9628% / 6.4625% range equities | `derived`, exact enumeration | `pokergto.equity.range_equity(..., mode="exact")`, commands in the text |
| 3.5337 / 141.35 / −0.1107 / −13.9035 bb | `derived` | `pokergto.ev.ev_call`, computed in this session |
| 19 of 49 turns; 1096 / 1308 of 2352 runouts | `derived` | `nut_advantage` evaluated board by board in this session |
| Narrowed denominators and shares (44, 63, 29, 40) | `derived` | `pokergto.ranges.Range.with_removed` plus `total_combos()` |
| The four example ranges | `reference` | `ADVANTAGE_SPOTS` in `tools/gen_tables.py`: illustrative inputs, not a solved strategy |
| How a solved line would actually play these spots | **UNVERIFIED / 未核验** | this repository holds no postflop equilibrium; `data/gen/solver` contains Kuhn- and Leduc-scale toys only. Any claim that "the solver bets two times pot here" has no artifact behind it |
| The same comparison three-way | **UNVERIFIED / 未核验** | `nut_advantage` takes two ranges; `03-09` currently states the dilution direction without a computed three-range table |

## 术语 / Terms

<!-- terms: range-advantage, equity-advantage, nut-advantage, the-nuts, capacity, range, equity, combos, board, flop, turn, bet-size, minimum-defense-frequency, bluff-to-value-ratio, bluff, value-bet, showdown -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 范围优势 | range advantage | the umbrella term; this lesson splits it into two columns |
| — | 胜率优势 | equity advantage | `hero_equity − villain_equity`; governs betting frequency |
| — | 坚果优势 | nut advantage | the gap between the two ranges' shares of the current top tier; governs the maximum size |
| — | 坚果 | the nuts | the reference `T`: the best score either range holds **now** |
| — | 牌型容量 | capacity | how many combos a range can put on that tier; the value side of `02-04` |
| — | 组合数 | combos | the weighting unit of both columns |
| MDF | 最低防守频率 | minimum defense frequency | a quota, silent on which combos pay it |
| — | 下注尺度 | bet size | the bigger it is, the more it depends on capacity |
| — | 摊牌 | showdown | the only thing left after five community cards; no equity to compute |
