# Advantage changes hands: flop, turn and river ranges are not the same argument

<!-- hands: 2 -->
<!-- terms: range-advantage, nut-advantage, equity-advantage, runout, flop, turn, river, capacity, equity-realization, the-nuts, capped-range, combos, range, board, showdown, minimum-defense-frequency, blocker, removal-effect -->

## 本节目标 / Objectives

- Use **runout structure** to explain why one street's nut advantage can vanish on the next card: substitute each of the 49 possible turn cards and report how many hand the nut edge over.
- State each number's **domain**: `nut_advantage` accepts three to five cards, `range_equity` stops at the turn -- on the river there is a showdown and no equity left to compute.
- Separate "the board's function changed" from "the range changed", and label the second one UNVERIFIED.

## 前置知识 / Prerequisites

- `03-01` equity advantage versus nut advantage: this lesson reads those two columns as functions of the board, not properties of it.
- `03-02` capped ranges: the roof's position is set by the board, so the cap verdict moves with every card.
- `01-03` exact equity by enumeration: the `1176 / 48` cost ladder is what makes a board sweep affordable at all.
- `01-02` blockers and removal: needed for the sentence "the range was never narrowed to the board".

## 核心原理 / The principle

Both advantages are **functions of the board**, not attributes of the hand:

```
flop     B3    : (equity_edge(B3),    nut_edge(B3))
turn     B3+t  : (equity_edge(B3+t),  nut_edge(B3+t))     <- once per each of 49 cards t
river    B3+t+r: (undefined,          nut_edge(B3+t+r))   <- no equity left to compute
```

Three facts, all computed: the same ranges produce completely different columns on different boards; the nut edge changes owner on 19 of the 49 turn cards; and on the river the first column **does not exist**, because `range_equity` raises `InputError("a board of five cards has no equity left to compute")`.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Derivation: the next section. Board sweeps: `pokergto.theory.range_advantage#advantage` and `#nut_advantage`, called board by board in this session.

## 推导 / Derivation

**The two functions have different domains, and that is the hardest structural fact in this lesson.**

```
nut_advantage(H, V, B)   requires 3 <= len(B) <= 5   <- five cards fine, it only reads the board
range_equity(H, V, B)    requires len(B) <= 4        <- five cards raises immediately
```

`range_equity`'s refusal is not laziness in the implementation, it is the definition: equity averages over every way to complete the current board to five cards, and `runout_boards(B)` raises `InputError("cannot complete a 5-card board to five cards")` at `len(B) = 5`. The set `Ω` is empty. **After the showdown there is no randomness left, therefore nothing to take an expectation over -- only winning and losing.**

**The cost ladder is what makes a board sweep possible.** Completions to five cards: `|Ω| = 1176` on a flop (`C(49,2)`), `48` on a turn (`C(48,1)`), `0` on a river (the function refuses). Exact enumeration costs `|Ω| x (|H| + |V|)` evaluations: on `9h6d3c`, with 66 + 60 combos, that is `1176 x 126 ~ 148,176` evaluations; on a turn board only `48 x 126 = 6,048`. So sweeping all 49 turn cards is 49 full equity calculations plus 49 `max` operations, and it finishes in seconds; the 2352 turn-and-river lines below compute only the nut tier, which is pure `best_score`, and they also finish.

**The nut edge is a step function of the runout; the equity edge is a continuous one.** Substituting each of the 49 turn cards after `9h6d3c` (hero = BTN, 66 combos; villain = BB, 60 combos):

- `nut_edge` takes only **3 values**: `+9.0909%` (hero's trips nines still on top), `−6.6667%` (four combos make a straight), `−10.0000%` (`66` makes quads, 6 combos).
- `equity_edge` slides continuously between **−0.6714 and +0.3412**.

That is the cleanest mathematical statement of "advantage changes hands": **one jumps, the other slides.** When they have to be read together is the next table.

**Grouping all 49 turn cards (computed):**

| Turn group | Cards | Equity edge | Nut edge |
|---|---:|---|---|
| every `A`, `K`, `Q` | 12 | hero positive | hero positive |
| every `3`, `4`, `8`, `9`, `J` | 18 | villain positive | hero positive (the two disagree) |
| every `2`, `5`, `6`, `7`, `T` | 19 | villain positive | villain positive |

The 19 cards of the last group are exactly those that put `87s`, `76s`, `65s`, `54s`, `T8s` or `66` on top. **Which column a card changes, and how many combos it moves, can be listed card by card -- that is the mental model to take to a table.**

**Taking two streets together (computed).** Of the 49 x 48 = 2352 turn-and-river lines, BB holds the top tier at the end on **1096** (46.5986%) and BTN on **1308** (55.6122%); the two sets overlap on 52 lines (one tied combo from each side sits at `T`), which is why they sum above 100%. On the flop BB's nut share was 0.0000%. That gap is the price of the assumption stated in `03-01`: **the reference is the best hand reachable now, so the share is systematically too low for the side holding draws.**

## 直觉 / Intuition

Read a street's advantage as a **weather map**, not a verdict.

- "BTN has 9.09% on the roof but is 26.37% behind on average" on the flop is not a statement about what BTN should do; it is a statement that BTN owns one big size carried by exactly 6 combos, plus a mass of small sizes whose justification changes with the card.
- The turn is where the justification changes. One card can relocate the roof wholesale (`2`, `5`, `6`, `7`, `T`), while the average slides (from −26.37% to −54.48%, or to +18.66%).
- The river is where every slide ends and where the word "equity" ends too. The only range advantage still computable there is **who stands on the top tier at showdown**: `nut_advantage` keeps working on five cards, `range_equity` stops.

Mental model: three sentences, rewritten on every street -- "who is higher now" (equity), "who is on top now" (nuts), and "how long can this board keep me on top" (runout). The third matters most on the flop and does not exist on the river.

## 算例 / Worked examples

All rows use one fixed pair of illustrative ranges (`table.03-01`, row 2): BTN = `AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs` (66 combos), BB = `87s,76s,65s,54s,T8s,T9s,98o,97o,66,55` (60 combos). The ranges do not move, only the board -- **that is the one comparison this lesson is allowed to make**, because nothing in this repository narrows a range to an action line.

**Example 1 -- flop `9h6d3c`.** Hero equity 36.8154% (edge **−26.3691%**); nut share 9.0909% versus 0.0000% (edge **+9.0909%**). The top tier is trips nines: the 6 combos of `99`, all in hero's range. The columns disagree: BB owns frequency, BTN owns size.

**Example 2 -- turn `5h` (the `2/5/6/7/T` group).** Hero equity **22.7588%** (edge **−54.4824%**); nut share 0.0000% versus 6.6667% (edge **−6.6667%**). The roof moved to BB: the 4 combos of `87s` make the `5-6-7-8-9` straight on `9h6d3c5h`, and all 6 of BTN's trips nines sit below them (combo by combo: BB combos on the tier = 4, BTN = 0). Reproduce: `python -m pokergto equity "AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs" --range-villain "87s,76s,65s,54s,T8s,T9s,98o,97o,66,55" --board "9h6d3c5h" --json`.

**Example 3 -- turn `4h` (the `3/4/8/9/J` group, columns still opposed).** Hero equity **31.3392%** (edge **−37.3216%**) while the nut edge stays **+9.0909%**. A card that made hero worse on average did not stop hero owning the top tier. **"This hand got worse" and "can I still use this size" are different questions.**

**Example 4 -- turn `Ks` (the `A/K/Q` group).** Hero equity **59.3284%** (edge **+18.6568%**), nut edge **+9.0909%**: both columns now point at hero. Note that `C(B)` on `9h6d3cKs` is trips kings (`KK`, held by nobody), so **both ranges are capped here** while the nut edge is still positive -- `nut_edge` and `is_capped` are separate verdicts, exactly as `03-02` warns.

**Example 5 -- river `9h6d3c4h2c`.** `range_equity` raises `InputError("a board of five cards has no equity left to compute")`, while `nut_advantage` returns **BTN 0.0000% / BB 23.3333%**: 14 of BB's combos sit on `straight 6` (`54s` 4 + `65s` 4 + `55` 6), and BTN's best tier is trips nines (6 combos), beaten by all 14. The flop's sentence "BTN 9.0909%, BB 0.0000%" has turned completely around.

**Example 6 -- a made straight is not 100%.** On `9h6d3c5h`, `87s` (already a straight) holds **77.8409%** against `99`, i.e. `99` keeps **22.1591%** rather than zero. Three mechanisms, each checkable: **12 of the 48 rivers pair the board** (three remaining `9`s, `6`s, `5`s and `3`s) and `99` then makes at least a full house (on river `3d`: `99` = full house, `87s` = straight 9); `9h` is already on the board, so the 6 written combos of `99` shrink to **3** legal ones (`parse("99").with_removed(*board).total_combos()` = 3.0), and only **1** survives when the river is a nine; and the river `6h` gives `8h7h` a **straight flush** `5h 6h 7h 8h 9h`, which a full house cannot beat (the same river leaves `8s7s` with merely a straight 9). Together these fix `99`'s share at 22.1591%, below the naive `12/48 = 25%`. **Runout structure changes not only who owns the roof but what standing on it is worth.**

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

Rows 1 and 4 are **two streets of one hand** (`Kh7s3d` and its turn `Kh7s3d4c`) -- but they cannot be read as "the effect of one card": the ranges on the two rows were authored separately (row 4 adds `44`, and its villain drops `A5s-A2s` and `76s`). To read a single card's effect, pin the ranges and move the board, as Examples 1 to 5 do.

What a size demands of the defender also changes street by street, because the sizes change (the same MDF table read across is sizes, read down is streets):

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

One third pot is the flop default (quota 75.00%); pot to two times pot is the river default (quota 50.00% down to 33.33%). **The lower the quota, the more it demands that your range actually contains the top tier** -- which is the arithmetic version of "a flop's big-betting logic does not transfer to the river".

## 实战牌局 / Live hands

**Hand 1 (`hand.03-03-turn-flips-the-argument`) -- 6-max, blinds 0.5/1. BTN opens 2.2 bb, BB calls 1.2 bb, pot 4.4 bb. Flop `9h6d3c`: BTN bets 1.47 bb (one third pot), BB calls. Turn `5h`, pot 7.34 bb.**

Ranges pinned to Example 1's pair (66 versus 60). On the flop BTN's two-times-pot size leaned on the 6 rooftop combos of `99`; on the `5h` turn, Example 2 moved the roof to BB (4 straight combos), so BTN's nut edge went from **+9.0909%** to **−6.6667%**.

- **The decision: can BTN keep firing two times pot, 14.68 bb?** Size arithmetic: `f* = 14.68/(7.34+14.68) = 0.666667`, BB's `MDF = 7.34/22.02 = 0.333333`, equity to call `0.400000` (`python -m pokergto mdf --pot 7.34 --bet 14.68`; the same size on the flop is `--pot 4.4 --bet 8.8`, also 0.3333).
- **The equity column is more direct**: BTN's whole range holds **22.7588%** on `9h6d3c5h` (Example 2), BB 77.2412%, against a threshold of only 40.0000%. On a range-average basis BB can pay its 33.33% quota without folding anything that matters -- range-average evidence, not a combo-by-combo ruling, and this lesson has no per-combo defence artifact to appeal to.
- **The price (computed)**: BTN betting two times pot with its whole range into a full defence is worth `0.227588 x (7.34 + 2 x 14.68) − 14.68 = **−6.3275 bb**`; the same hands checking back are worth `0.227588 x 7.34 = **+1.6705 bb**`. **Carrying the flop's sizing verdict across the turn costs 7.9980 bb per hand.**
- **What about BTN's 6 rooftop combos?** `99` versus BB's whole range drops from **88.2789%** equity on the flop to **80.0157%** on the turn (the pairing mechanism of Example 6): it is still BTN's best hand, it is simply no longer the board's highest tier. "The size can no longer be run" is not "this hand can no longer continue".

**Hand 2 (`hand.03-03-river-has-no-equity`) -- a different line from the same flop: the turn is `4h` (Example 3, BTN's roof still stands). BTN checks, BB bets 2.45 bb (one third pot), BTN calls, pot 12.24 bb. River `2c`.**

Board `9h6d3c4h2c`. Example 5 priced it: `nut_advantage` gives BTN 0.0000% / BB 23.3333% (14 combos on `straight 6`), and `range_equity` raises `InputError`.

- **After BB bets 6.12 bb (half pot)**: BTN's `MDF = 12.24/18.36 = 0.666667`, i.e. **44.00** of its 66 combos must continue, and the call needs `6.12/(12.24+12.24) = 0.250000` equity (`python -m pokergto mdf --pot 12.24 --bet 6.12`).
- **The quota cannot be paid.** Write BB's betting range as authored: 14 straights for value plus the 12 weakest combos as bluffs (`one pair 6` and the two high-card tiers). BTN combos that beat **all 12** bluff candidates: **18** (6 of `99`, 6 of `TT`, 6 of `88`) = **27.2727%**, which is **39.3940** percentage points and **26 combos** short of the 66.67% MDF demands.
- **Both directions have a price (computed).** Calling only those 18 and folding 48 (`f = 0.727273`) makes each of BB's bluff combos worth `0.727273 x 12.24 − 0.272727 x 6.12 = **+7.2327 bb**`, **+86.79 bb** over the 12. Padding to the quota with 26 more combos that beat no bluff at all costs each of them `0 x (12.24 + 12.24) − 6.12 = **−6.12 bb**`, **−159.12 bb** in total, which is **−2.4109 bb** spread over BTN's whole 66-combo range.
- **So the correct move was upstream.** There is no river-side repair here: no equity left to compute, only showdown ownership. BTN's turn check (the setting of this hand) is what leaves it with nothing to call on the `2c` -- the nut edge's **direction** was still BTN's on the turn, and its **survival** depended on two unseen cards, not on the one already dealt.

## 范围图 / Range chart

The two charts use the same 1,326 combos and the same "fill in preflop strength order" rule; only the target frequency differs. Put side by side they are the picture version of "different street, different size, different quota".

**The flop default, one third pot (MDF 75.00%, 994.5 combos):**

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

**A pot-sized bet (MDF 50.00%, 663.0 combos):**

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

How to read them:

- The difference between the two is the 331.5 combos the defender is allowed to drop when the size grows from one third pot to pot, and because both are filled by preflop rank, what leaves first is always `32o`, `72o` and their neighbours -- the cells that the deep quota let in and the shallow quota throws out.
- **Neither chart looks at a board.** Hand 2's 26-combo shortfall is invisible on them: the quota is allocated by preflop strength, the ability to pay is set by the board. That is the visual proof that streets are separate arguments.
- As in `03-01` and `03-02`, the denominators are 1,326 and are not narrowed to any board. In Hand 2 the 6 written combos of `99` are only **3** legal on `9h6d3c4h2c` (`9h` is on the board); BTN's 66 combos are 63 legal and BB's 60 are **47** legal.

## 为何成立、何时失效 / Why it works, when it breaks

**What it requires**: that the ranges are **pinned** across streets (every number here is "ranges fixed, board moving"); that the evaluator gives the same total order on every board; and that `nut_advantage`'s reference is "the best score either range can reach on this board".

Where it fails, mostly on the premises themselves:

1. **On incomplete boards the nut advantage under-states the drawing side.** This comes from the definition, not from an error: BB's flop nut share is 0.0000%, yet 19 of 49 turn cards put it on top, and 1096 of the 2352 turn-and-river lines (46.5986%) end with BB holding the tier. The artifact's `caption` and the module docstring both say so; the sweeps above are the numbers attached to that sentence.
2. **Ranges do not narrow themselves along a line.** This repository has no artifact for "which combos remain in BB's range after a flop bet and call", so both live hands carry the flop ranges to the river. Any statement like "BTN's `88` is gone by now" is a **strategy claim** and is **UNVERIFIED**. Every conclusion here is conditional on ranges not moving, and that is a strong condition.
3. **The two columns move at different speeds.** Measured: across the 49 turn cards `nut_edge` jumps between 3 discrete values while `equity_edge` slides over [−0.6714, +0.3412]. Inferring a river's nut ownership from a flop's equity edge, or the reverse, is therefore not the same argument twice. Why `03-04`'s board texture matters is exactly that it decides how many cards can trigger the jump.
4. **On five cards the first column does not exist.** Both `range_equity` and `runout_boards` raise `InputError`. Any river "equity advantage" phrasing has no recomputable source and can only be written as showdown ownership, i.e. `nut_edge`.
5. **The un-narrowed denominator runs through all three lessons.** BTN's "6 combos of trips nines" on the river are 3 legal. This does not change the **direction** of either column (in the sweeps every narrowed ratio fell the same way) but it does change the **magnitude**, so any share read as a probability must ask this question first.
6. **A paired board can unseat a hand already on the roof.** Example 6: `87s` with a made straight holds only 77.8409%. Nut advantage is a statement about now; equity is a statement about the future; neither guarantees survival to the next card.

## 陷阱 / Common mistakes

1. **Transporting the flop's sizing verdict to the turn.** Hand 1: BTN's two-times-pot size was carried by 6 rooftop combos on the flop; after `5h` the roof belongs to BB.
   *Cost*: **7.9980 bb per hand** (betting −6.3275 bb against checking +1.6705 bb) -- the most expensive single arithmetic fact in this lesson.
2. **Assuming a made straight is 100%.** Example 6: `87s` versus `99` is **77.8409%**, because 12 of the 48 rivers pair the board and one of them even makes a straight flush for the other combo of the same class.
   *Cost*: shoving those 4 combos as "absolute nuts" ignores the **22.1591%** `99` recovers; and the `03-02` cap verdict flips wholesale with such a card (hero is capped on 46 of 49 turn cards after `9h6d3c`).
3. **Quoting an "equity advantage" on the river.** On `9h6d3c4h2c` the engine raises `InputError("a board of five cards has no equity left to compute")`.
   *Cost*: a number nobody can recompute silently invalidates everything built on it. The only river-computable range advantage is tier ownership: Hand 2's shortfall is **39.3940** percentage points / **26** combos, and the two ways of living with it cost **+7.2327 bb** per opponent bluff (fold) or **−159.12 bb** (call anyway).
4. **Reading a board sweep as a strategy sweep.** The 19-of-49 flip is computed with the ranges **pinned**.
   *Cost*: turning it into "BB overtakes 38.78% of the time here" gives a conditional statistic an unconditional meaning; in a real line BB's flop calling range would already have deleted part of the combos that make those straights -- the difference between supply and frequency is `01-02`'s lesson and `03-05`'s subject.

## 练习 / Drills

- Reproduce Examples 2 to 4 one card at a time: `python -m pokergto equity "AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs" --range-villain "87s,76s,65s,54s,T8s,T9s,98o,97o,66,55" --board "9h6d3c5h" --json`, then the same with `--board "9h6d3c4h"` and `--board "9h6d3cKs"`, and confirm `"iterations"` is 48 in all three.
- Write a twenty-line loop that runs `nut_advantage` over all 49 turn cards after `9h6d3c`; verify the 30 / 19 split and report the three values `nut_edge` takes.
- Verify Example 6: `python -m pokergto equity "87s" "99" --board "9h6d3c5h" --json` returns 0.778409; count how many of the 48 rivers pair the board, and explain why 22.1591% is below the naive `12/48`.
- Recompute both prices in Hand 2 (`ev_pure_bluff(12.24, 6.12, 0.727273)`, and 26 x −6.12) and say why paying MDF is the more expensive of the two here.
- State why `equity_edge` is undefined on a river while `nut_edge` is not, and give the board-length constraint of each function verbatim.

## 自测清单 / Self-check

- [ ] I can say how many of the 49 turn cards after `9h6d3c` hand the nut edge to BB (19) and list their ranks.
- [ ] I can explain why 46.5986% and 55.6122% over 2352 lines sum to more than 100%.
- [ ] I can name which function raises `InputError` on a five-card board, which one still returns, and why.
- [ ] I can quote 7.9980 bb per hand as the price of transporting a sizing verdict across a street.
- [ ] I can state that every sweep here assumes pinned ranges, and name the real-world mechanism that breaks that assumption.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->

| Content | Source type | Location |
|---|---|---|
| The four rows of equity and nut shares | `derived` | `data/gen/tables/table.03-01.equity-vs-nut-advantage.json`; `pokergto.theory.range_advantage#advantage` |
| Sizes, defence quotas and the two charts | `derived` | `data/gen/tables/table.02-03.mdf-vs-sizing.json`; `range.04-02.mdf-floor-vs-third-pot.json`; `range.04-02.mdf-floor-vs-pot.json` |
| The 12 / 18 / 19 turn grouping and the three `nut_edge` values | `derived` | `pokergto.theory.range_advantage.nut_advantage` called board by board, this session |
| 1096 / 1308 / 52 over 2352 lines | `derived` | same function, full turn-and-river enumeration |
| 22.7588% / 31.3392% / 59.3284% / 80.0157% / 88.2789% / 77.8409% | `derived`, exact enumeration | `pokergto.equity.range_equity(..., mode="exact")`, `iterations` 48 or 1176 |
| The 1176 / 48 cost ladder and the two `InputError` messages | `derived` | branches and messages of `pokergto.equity.runout_boards` and `pokergto.equity.range_equity` |
| 0.666667 / 0.333333 / 0.400000 / 0.250000 sizing arithmetic | `derived` | `python -m pokergto mdf --pot 7.34 --bet 14.68` and `--pot 12.24 --bet 6.12` |
| 18 payable combos / 27.2727% / 39.3940 pp / 26 short | `derived` | combo-by-combo `pokergto.evaluator.best_score` comparison, this session |
| −6.3275 / +1.6705 / −7.9980 / +7.2327 / +86.79 / −159.12 / −2.4109 bb | `derived` | `pokergto.ev.ev_bet`, `ev_check`, `ev_pure_bluff`, `ev_call`, this session |
| 63 / 47 legal combos and `99` shrinking 6 -> 3 -> 1 | `derived` | `pokergto.ranges.Range.with_removed` plus `total_combos()` |
| Both ranges (66 and 60 combos) | `reference` | `ADVANTAGE_SPOTS` in `tools/gen_tables.py`: illustrative inputs, not a solved strategy |
| "BTN checks the turn and BB bluffs exactly these 12 combos on the river" | **UNVERIFIED / 未核验** | no postflop equilibrium artifact exists; the actions in both live hands are **assumed in order to have a decision to price**, not computed strategy |
| Re-running any sweep on line-conditioned ranges | **UNVERIFIED / 未核验** | needs line conditioning; `nut_advantage` and `is_capped` take a board plus one range, so every scan here keeps the range fixed |
| Second-order removal across streets (a turn card changing the river deal distribution) | **UNVERIFIED / 未核验** | `Range.with_removed` performs single-step deletion only; `01-02` states that this repository does not chain removal across streets |

## 术语 / Terms

<!-- terms: range-advantage, nut-advantage, equity-advantage, runout, flop, turn, river, capacity, equity-realization, the-nuts, capped-range, combos, range, board, showdown, minimum-defense-frequency, blocker, removal-effect -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 发展牌序 | runout | every way to complete three cards to five: 1176 lines on a flop, 48 on a turn, 0 on a river |
| — | 胜率优势 | equity advantage | a function of the board, and **undefined** on five cards |
| — | 坚果优势 | nut advantage | a function of the board, still defined on five cards: showdown ownership |
| — | 牌面可达上限 | board ceiling | `03-02`'s `C(B)`; used here for why a made straight is not 100% |
| — | 牌型容量 | capacity | recomputed every street; 46 of 49 turn cards cap hero |
| — | 胜率实现 | equity realization | nominal equity against the money actually collected, `01-06` |
| — | 摊牌 | showdown | the only thing left on the river |
| — | 组合数 | combos | the denominator; note these ranges still contain board-clashing combos |
| MDF | 最低防守频率 | minimum defense frequency | a quota; Hand 2 shows it may be unpayable with hands that win |
| — | 移除效应 | removal effects | single-step deletion; this repository does not chain it across streets |
