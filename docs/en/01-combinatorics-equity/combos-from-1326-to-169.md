# From hole combos to hand classes: how many combos each class really has

<!-- hands: 2 -->
<!-- terms: combos, hand-class, suited, offsuit, pocket-pair, hole-cards, range, grid-13x13, capacity, bluff-to-value-ratio, blocker -->

## 本节目标 / Objectives

- Derive `6 / 4 / 12` from the single fact that each rank has four suits, and verify `13*6 + 78*4 + 78*12 == 1326`.
- Convert any range spec (`22+,ATs+`) into a combo count and state what share of the 1,326 that is.
- Quantify the gap between "average over the 169 classes" and "weight by combos", and name the calculations where the gap flips the sign of the answer.
- Do the arithmetic every later chapter depends on: how many combos does my bluff range have?

## 前置知识 / Prerequisites

- `00-01` hole cards, board and the four streets: one hand is two hole cards and five board cards.
- `00-02` derivation before memory: every number below is recomputable from the command line, so memorising it is pointless.
- Binomial coefficients: `C(4,2) = 6`, `C(13,2) = 78`, `C(52,2) = 1326`.

## 核心原理 / The principle

The dealing space has size **1326**: `C(52,2) = 52*51/2 = 1326` distinct two-card holdings.
The classification space has size **169**: 13 pairs, 78 suited classes, 78 offsuit classes.
The ratio between them is not constant -- **pairs carry 6 combos, suited classes 4, offsuit classes 12**.

So: every "how much of the range" question (what percentage, how many combos, what value-to-bluff ratio) is arithmetic over the 1326. Every "which hand" question (does this class continue) is arithmetic over the 169. **Mixing the two weightings in one calculation is the disease chapter 01 exists to cure.**

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Derivation below. Generated table: `tools/gen_tables.py` -> `data/gen/tables/table.01-01.combo-decomposition.json`,
>     which carries its own two checks (`13*6 + 78*4 + 78*12 == 1326`, and the 13x13 grid's own combo total).

## 推导 / Derivation

**Six combos per pair.** `AA` is "choose two of the four aces": `C(4,2) = 6`. Two cards of the same rank cannot share a suit, so pairs have no `s/o` split.

**Four combos per suited class.** `AKs` requires both cards in the same suit, so the suit is the only free choice: `AcKc, AdKd, AhKh, AsKs`. Four.

**Twelve combos per offsuit class.** `AKo` requires different suits: pick the ace's suit (4 ways), the king may then take any of the other 3 suits. `4*3 = 12`.

**How many classes.** 13 pairs (one per rank). The unordered rank pairs are `C(13,2) = 78`, and each splits into one suited and one offsuit class, so 78 suited and 78 offsuit. `13 + 78 + 78 = 169`.

**Put them together:**

```
13*6  +  78*4  +  78*12   =   78  +  312  +  936   =   1326
```

The engine asserts this rather than trusting it: `pokergto.cards` raises `InvariantError` unless `ALL_COMBOS` has length 1326 and `HAND_CLASSES_169` has length 169. Two commands show the same arithmetic from the other side:

```bash
PYTHONPATH=src python -m pokergto range "22+" --json      # combos: 78.0, classes: 13
PYTHONPATH=src python -m pokergto range "22+,ATs+" --json  # combos: 114.0, classes: 22, range_percentage: 8.5973
```

## 直觉 / Intuition

Read the 13x13 grid as a board whose **cells are different sizes**: the diagonal (pairs) is 6 combos, the upper triangle (suited) is 4, the lower triangle (offsuit) is 12. **One cell is not "one hand"; one cell is four, six or twelve physical decks-of-two.**

Which gives a sentence worth memorising: **two ranges that look equally wide differ by a factor of three depending on whether they are written suited or offsuit.** `AA,AKs` is 10 combos; `AA,AKo` is 18. Same two classes: 0.75% versus 1.36% of the dealing space. A defense range built out of suited connectors holds far fewer combos than its cell count suggests.

Mental model: classes are the **catalogue**, combos are the **stock**. Bet sizes, frequencies and bluff-to-value ratios count stock; the sentence "this hand continues" talks about the catalogue.

## 算例 / Worked examples

**Example 1 -- how many combos in `22+,ATs+`.** 13 pairs give `13*6 = 78`; `ATs+` in this repository's notation expands to `ATs, A9s, ..., A2s` -- 9 suited classes (`AKs/AQs/AJs` are *not* included) -- `9*4 = 36`. Total **114 combos**, i.e. `114/1326 = 8.597%`.
The same command reports **22 classes**, and `22/169 = 13.018%`. **Counting classes overstates the range by 4.42 percentage points, a factor of 1.51.** That is not rounding; it is what happens when a 4-combo cell and a 6-combo cell are treated as equal weight.

**Example 2 -- a suited-only range.** `88+,A9s+,KTs+,QTs+,JTs,T8s+,96s+,85s+,75s,64s,54s` (the skeleton of a typical BTN call-vs-3-bet range): 53 classes = `31.36%` of 169; 226 combos = `17.04%` of 1326. **A factor of 1.84.** The more suited the range, the worse the class-count illusion. This is why a claim like "I continue 30% on the button" must say how it was counted.

**Example 3 -- how many `AKo` combos are left.** One ace and one king are visible (`As` and `Kh` dead): `AKo` falls from 12 to **7** (engine: `parse("AKo").with_removed(As, Kh)` -> 7). With only `As` visible it is **9**; with `As` and `Ks` it is **6**, because `As` deletes 3 combos, `Ks` deletes another 3, and `AsKs` belongs to `AKs`, so the two deletions do not overlap. **Two blockers of the same suit delete more offsuit combos than two blockers of different suits.** That is `01-02`'s subject; here the point is only that 12 is not a constant.

**Example 4 -- how many combos a bluff needs.** A half-pot bet's indifference ratio is **value:bluff = 3:1** (see the generated table below; closed form `s/(1+2s)`). If the line carries 12 value combos, it must carry **4 bluff combos**. Four combos is exactly one whole suited class (`A5s` gives 4), or one third of an offsuit class (`12/3`).
In other words, "bluff with `A5s`" and "bluff with a third of `KQo`" deliver the same combo count but occupy the chart differently. **The ratio speaks about combos, not about cells.**

**Example 5 -- pot-share anchors.** Learn to move between 1326 and percentages instantly: 884 = `2/3`, 442 = `1/3`, 663 = 50%, 114 ~= 8.6%, 22 ~= 1.66%, 6 = 0.45%, 1 = 0.075%. Every "how many combos must I defend" question later in the book is arithmetic on these anchors.

## 生成表 / Generated tables

The first table is computed by `tools/gen_tables.py` through `pokergto.cards.combos_for_class`. It was not transcribed from a book or a website:

<!-- BEGIN AUTO:table.01-01.combo-decomposition -->
|   Shape | Classes | Combos each |        Combos |
|---:|---:|---:|---:|
|   pairs |      13 |           6 |  78.00 combos |
|  suited |      78 |           4 | 312.00 combos |
| offsuit |      78 |          12 | 936.00 combos |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.cards#combos_for_class`

<!-- generated by: tools/gen_tables.py from pokergto.cards::combos_for_class -->
<!-- END AUTO:table.01-01.combo-decomposition -->

The second table belongs to `02-04`, and it is borrowed here because **its unit is combos**: the `value_to_bluff` column is not "classes to classes", it is "combos to combos". Pair the 3:1 half-pot row with Example 4's 12 value combos needing 4 bluff combos, and that is the only thing in this chapter worth memorising; everything else is recomputable on demand.

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

## 实战牌局 / Live hands

**Hand 1 (`hand.01-01-river-bluff-blockers`) -- 6-max cash. BTN opens 2.5x, BB calls. River board `Ah 9d 6c 4s 2h`, pot 100, hero (BTN) considering a 60-chip shove as a bluff.**

Hero holds `Qc Jc`: no pair, and the `Ah` on the board means no hand in villain's calling range is one hero beats. This is pure air, so whether the bluff works is a combo-counting question:

- Write villain's **calling** part as `ATs-A2s, AJo, AQo, AKo, 99, 66`. After the five visible board cards are removed that is **57 combos** (`AKo` is down to 9 because `Ah` is dead; `99` and `66` are down to 3 each; `A4s/A6s/A9s` to 2 each).
- Write villain's **folding** part as `KQo, QJo, JTo, 88, 77, 55, 33`: **60 combos** with the board removed.
- Now remove hero's two cards too: calling **53**, folding **48**. Fold frequency `48/(53+48) = 47.52%`.
- The threshold comes from `02-03`'s algebra: risking 60 to win 100 needs `60/160 = 37.5%` of the combos to fold. `47.52% > 37.5%`, **the bluff works**, and its value is `0.4752*100 - 0.5248*60 = +16.04` per attempt.
- Here is the point. Swap hero to `Kc Jc`: only 9 folding combos are deleted instead of 12, the calling side is still 53, so fold frequency is **49.04%** and value **+18.46**. Two hands that both "have nothing" differ by **2.4 chips per attempt**, purely because of which combos they delete. You cannot see this without counting combos.

Both ranges are authored by this repository for the exercise (`reference`: every line is checkable); the counts and the expected value are `derived`. To reproduce (board removal goes through `Range.with_removed`):

```python
from pokergto.notation import parse
from pokergto.cards import Card
board = [Card.parse(c) for c in ("Ah", "9d", "6c", "4s", "2h")]
hero  = [Card.parse("Qc"), Card.parse("Jc")]
parse("ATs-A2s,AJo,AQo,AKo,99,66").with_removed(*board).total_combos()   # 57.0
parse("KQo,QJo,JTo,88,77,55,33").with_removed(*board).total_combos()     # 60.0
parse("ATs-A2s,AJo,AQo,AKo,99,66").with_removed(*board, *hero).total_combos()  # 53.0
parse("KQo,QJo,JTo,88,77,55,33").with_removed(*board, *hero).total_combos()    # 48.0
```

Before the board is removed those two specs hold 84 and 60 combos, so the five visible cards took 27 combos out of the calling side alone -- **which is exactly why subtraction, not class counting, is the honest method**: the calling spec has only 14 classes, and nothing about "14 classes" changes when the board comes out.

**Hand 2 (`hand.01-01-three-bet-call-count`) -- BTN opens 2.5x, BB 3-bets to 9x, everyone else folds, pot 12x. Hero (BTN) must call 6.5x with `AQo`.**

- Equity needed: `6.5/(12+6.5) = 6.5/18.5 = 35.14%`. Pure algebra, independent of who BB is.
- If BB's 3-bet range is value only, `QQ+,AKs`: **22 combos** (18 pairs + 4 `AKs`). `AQo` has **23.88% +/- 0.59pp** against it (Monte Carlo, `n = 20000`, `seed = 4`; with `n = 200000`, 23.79% +/- 0.19pp). Exact enumeration of a preflop range matchup costs 88,364,640 evaluations and the engine refuses -- `01-03` explains why. `23.88% < 35.14%`: **fold**.
- Add `A5s-A4s`, i.e. **8** bluff combos (30 total). The same `AQo` now holds **37.08% +/- 0.67pp** (`n = 20000`, `seed = 4`; 36.47% +/- 0.22pp at `n = 200000`): **above the line, call**.
- The conclusion is driven entirely by combos. Those 8 extra combos change value:bluff from "no bluffs at all" to `22:8 = 2.75:1`, and they change hero's action from fold to call. **That is why you count stock, not the catalogue.**

```bash
PYTHONPATH=src python -m pokergto equity "AQo" --range-villain "QQ+,AKs" \
    --mode mc --iterations 20000 --seed 4 --json
PYTHONPATH=src python -m pokergto equity "AQo" --range-villain "QQ+,AKs,A5s-A4s" \
    --mode mc --iterations 20000 --seed 4 --json
```

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

The chart above is `02-03`'s **MDF floor for a half-pot bet**: it has to cover `2/3` of the dealing space, i.e. **884 combos** (`1326*2/3`). The artifact reports `total_combos = 883.999996`, and that is not a typo: the cell `84o` is filled at the six-decimal frequency `0.333333`, and `12*0.333333 = 3.999996`. This is the price of ADR-0001's pinned float formatting, and a reason to treat combo totals as **sourced numbers** rather than as integers.

Three ways to read it:

1. The chart has **114 non-empty cells** (13 pairs and other classes fully filled -- 113 of them -- plus `84o` at one third). By cells that is `114/169 = 67.46%`; by combos `884/1326 = 66.67%`. **This chart happens to be one of the rare cases where the two agree**, because it was filled in strength order, so the mix of pair/suited/offsuit cells it fills is close to the mix in the deck as a whole. Do the same comparison on a suited-heavy range and you get Example 2's factor of 1.84.
2. The `84o` cell carries a **mixed frequency**: `0.333333 * 12 = 4` combos. Whenever a solver chart shows `0.5`, multiply by `4/6/12` before you compare ratios.
3. The chart contains no removal information. If the board carries `Ah`, this defense chart loses **43 combos** (`884 -> 841`, i.e. `63.42%` of 1326); if the visible card is `2h`, the chart loses **nothing** -- that card is not in the range at all. That is the door into `01-02`.

## 为何成立、何时失效 / Why it works, when it breaks

**Why it holds.** `6/4/12` uses one fact only: four suits, one card per suit per rank. It depends on no hand strength, no player, no bet size. It is a property of the shuffle, not of strategy.

**Where it stops being directly usable:**

1. **Visible cards (removal).** 12 stops being 12: board cards and your own hole cards delete combos (Example 3). This lesson gives the no-information ceiling; `01-02` does the subtraction.
2. **Fractional frequencies.** Under a mixed strategy a cell's combo count can be fractional (`84o`'s 4 combos come from `0.333333*12`). Ratios still hold, but "half a combo" has no physical counterpart: it means the same hand plays the line at different frequencies on different streets.
3. **Notation cannot name a physical subset.** `pokergto.notation` goes down to the class level; it cannot say "only `AsKs`". When you truly need one suit combination, `to_spec()` flags the range `lossy` -- not a cosmetic issue: it means a cell on the chart is not always the same physical set.
4. **Multiway pots.** The combo counts are unchanged, but the target ratio is: three- and four-way value:bluff structures are not this lesson's table (see `07-01`).
5. **Tournaments.** Combos still count the same; `02-04`'s table assumes linear chip value, and ICM bends the 3:1 (chapter 12).

## 陷阱 / Common mistakes

1. **Reporting range width by classes.** Example 1: `22+,ATs+` is 13.02% by class, 8.60% by combos.
   *Cost*: you believe your defense range is 1.5x wider than it is, and you take on an MDF quota with 8.6% of the stock you thought you had. In `02-03`'s language, that is a gift to any two cards the opponent decides to bluff with. Run `python -m pokergto range "<spec>" --json` and read `combos` next to `range_percentage`; a minute of arithmetic ends the habit.
2. **Treating `6/4/12` as permanent.** Example 3: `AKo` is 7 or 6 once two cards are visible; `99` is 3 once a nine is on the board.
   *Cost*: you assume villain has 12 `AKo` value combos, conclude their bluff share is large, and call with a bluff-catching range that was never thin enough. Use `parse(spec).with_removed(*cards)`.
3. **Filling the value:bluff ratio with classes.** 3:1 is a ratio of combos. Executing it as "three value cells to one bluff cell" can produce `3*12 : 1*4 = 9:1` (value all offsuit, bluff suited) or `3*4 : 1*12 = 1:1`.
   *Cost*: Hand 1's margin is 48 folding combos against 53 calling ones -- ten percentage points of fold frequency. Get the unit wrong once and the same line turns negative. Count combos, not cells.

## 练习 / Drills

- Predict, then check with `python -m pokergto range "<spec>" --json`: `22+,ATs+`; `99+,AJs+,KQs`; `77-22,ATo+`; `55+,AQs+,AJo+`. Which cell type did you mis-weight when your guess was wrong?
- Variant of Example 3: board `Kd 7h 2s`, villain's range written `KK,AKs,AKo,KQo`. How many combos are left in each class, and in total?
- Ratio question: you shove 120 into a pot of 120 on the river and hold 9 value combos. How many bluff combos does the generated table require? If only `A5s` (4) and `A3s` (4) are available, what is the closest you can get?
- Take the grid printed by `python -m pokergto range "22+,ATs+"`, write `6/4/12` on every filled cell and add them up. If you do not land on 114, you scored the upper triangle as 12.

## 自测清单 / Self-check

- [ ] I can write down where `6 / 4 / 12` come from in a minute, and show that `C(52,2) = 1326` agrees.
- [ ] I can state `22+,ATs+`'s combo count, its share of 1326, and the wrong answer class-counting gives.
- [ ] I know `AKo` leaves 7 combos after two offsuit-visible cards and 6 after two suited-visible ones, and why.
- [ ] I can translate "value:bluff 3:1" into an actual deck of cards (12 value combos, 4 bluff combos).
- [ ] I can convert a mixed frequency on a 13x13 chart (`0.333333`) into combos.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number here is computed in this repository. No range chart or strategy output from a commercial solver or paid course appears in this lesson:

| Content | Source type | Location |
|---|---|---|
| `6/4/12` and the 1326 identity | `derived` | `src/pokergto/cards.py#combos_for_class`; the two `checks` inside `table.01-01.combo-decomposition` |
| Range combo counts and shares (114 / 8.597%, 226 / 17.04%, 53 classes / 31.36%) | `derived` | `PYTHONPATH=src python -m pokergto range "<spec>" --json` |
| Bluff-to-value table | `derived` | `data/gen/tables/table.02-04.bluff-value-ratio.json` (`pokergto.odds#bluff_fraction_at_indifference`) |
| MDF floor chart (884 combos / 114 cells / `84o` = 4 combos) | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` |
| Hand 1's range split (57 / 60 -> 53 / 48) | `reference` (ranges) + `derived` (counts and EV) | ranges authored here and checkable line by line; counts from `pokergto.notation.parse` + `Range.with_removed`; the decision uses only algebra |
| Hand 2's equities (23.88% / 37.08%) | `derived`, **Monte Carlo** | `equity "AQo" --range-villain "QQ+,AKs" --mode mc --iterations 20000 --seed 4 --json` (and the same command with `A5s-A4s` added); bars and seed in the text |
| The chart losing 43 combos when `Ah` is visible | `derived` | per-combo enumeration over the committed artifact's `weights` (`cards.ALL_COMBOS` + `class_key`) |

## 术语 / Terms

<!-- terms: combos, hand-class, suited, offsuit, pocket-pair, hole-cards, range, grid-13x13, capacity, bluff-to-value-ratio, blocker -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 组合数 | combos | the weighting unit: pairs 6, suited 4, offsuit 12 |
| — | 手牌类别 | hand class | one of 169 catalogue entries -- not 169 equally common hands |
| — | 起手同花 | suited | 4 combos per class |
| — | 起手不同花 | offsuit | 12 combos per class, three times suited |
| — | 范围 | range | a frequency vector over the 1326 combos, not a set of cells |
| — | 诈唬与价值比 | bluff-to-value ratio | combos to combos, never classes to classes |
| — | 阻断牌 | blocker | the card that makes `6/4/12` smaller; see `01-02` |
