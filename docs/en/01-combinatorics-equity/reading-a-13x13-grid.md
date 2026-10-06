# Reading a 13x13 grid: what a cell counts and what the axes mean

<!-- hands: 2 -->
<!-- terms: grid-13x13, range-chart, range, hand-class, combos, suited, offsuit, pocket-pair, hole-cards, determinism, generated-artifact -->

## 本节目标 / Objectives

- Pick up any chart generated in this repository and state the axis order, what the diagonal is, what the upper and lower triangles are -- and explain why that convention is frozen as a literal string inside every artifact.
- Convert a grid into a list of combo counts: when a cell is 6, 4 or 12, how to check it, and why suited and offsuit cells carry different weights.
- Keep **combo-weighted** and **hand-class-weighted** percentages apart, and produce on the spot an example where the two visibly diverge.
- Recite the shade thresholds (`··/::/++/##/@@`) and say what the sub-1% empty band is for.

## 前置知识 / Prerequisites

- `01-01` Combos: 1,326 hole combos, 169 hand classes, `pairs 6 / suited 4 / offsuit 12`.
- `01-02` Blockers and removal: how a cell's weight changes once a card is accounted for.

## 核心原理 / The principle

One coordinate convention, in four lines:

```
rows and columns:  A K Q J T 9 8 7 6 5 4 3 2   (descending)
diagonal           pocket pairs, 6 combos per cell
upper triangle     suited, 4 combos per cell
lower triangle     offsuit, 12 combos per cell
```

This is not "how we like to draw them". It is pinned as a literal constant:

```python
ORIENTATION = "akqjt98765432-desc-diagonal-pairs-upper-suited"
```

and it appears in four places: `src/pokergto/matrix13.py` (the single definition), `data/schema/range_chart.schema.json` (as a `const`, so a mismatched chart fails validation), every generated chart (the `orientation` field), and the reader-side check in `src/pokergto/ranges.py` -- a chart with another orientation raises `InputError` instead of being interpreted generously.

One more rule is just as hard: **a cell stores a frequency in [0,1], never a combo count** (`Grid13` says so in its own docstring). Combo counts come only from `pokergto.cards`. Exactly one place in the codebase can be wrong about how many combos `AKo` has.

> !!! note "Provenance"
>     Orientation and the mirror invariant: `src/pokergto/matrix13.py`, pinned by `tests/test_matrix13.py`. Cell weights: `pokergto.cards#combos_for_class` -> `data/gen/tables/table.01-01.combo-decomposition.json`. Shade thresholds: `src/pokergto/render.py#FILL_BANDS`.

## 推导 / Derivation

**Step one: where 6 / 4 / 12 come from.** Take two ranks `x` and `y` out of four suits:

- pocket pair: `C(4,2) = 6`.
- suited: both cards in one suit, 4 ways to choose that suit -> **4**.
- offsuit: each rank picks a suit and they must differ -> `4 x 3 = 12`.

So the whole grid weighs

```
13 x 6 + 78 x 4 + 78 x 12 = 78 + 312 + 936 = 1326
```

and `78 = C(13,2)`: 78 cells above the diagonal, 78 below, 13 on it, 169 classes in total. Those three slices are the three rows of the decomposition table, and `Grid13.full().combos()` returns 1326.0 -- the identity closes.

**Step two: the mirror invariant, which is not symmetry.** Transposing a grid (`Grid13.mirror()` is `.T`) moves every upper-triangle class to the mirrored lower-triangle position: **the rank structure is untouched, only `s` becomes `o`**. Measured: `{AA, AKs, ATs}` = 6 + 4 + 4 = **14 combos**; its mirror `{AA, AKo, ATo}` = 6 + 12 + 12 = **30 combos**. The shape survives, the weight does not.

`src/pokergto/matrix13.py` states why the test exists: the interesting property is mirror equivalence rather than symmetry, "because an orientation bug in a chart is invisible to the eye and catastrophic downstream". The test pins what the eye cannot.

**Step three: two percentages, and they will diverge.** The same range, two units:

| Range | Classes | Class share | Combos | Combo share |
|---|---|---|---|---|
| `22+` | 13 | 7.69% | 78 | 5.88% |
| `ATs+,KQs,JTs` | 11 | 6.51% | 44 | 3.32% |
| `88+,ATs+` | 16 | 9.47% | 78 | 5.88% |
| the MDF floor chart below | 114 | 67.46% | 884 | 66.67% |

The class-share column is 1.96x the combo share for the suited row (6.51 / 3.32) and 1.31x for the pairs row. **Every sentence of the form "that range is 20%" has to answer "in which unit" first.** The consequence shows up in `02-03`: MDF is combo-weighted, and reading a chart in classes is how a player thinks he defends 70% while actually defending 55%.

**Step four: the shade bands.** The discretisation lives in `render.FILL_BANDS`:

```
f < 0.01  ->  ··      (documentation renders anything below 1% as the empty band; the terminal prints "..")
f < 0.34  ->  ::
f < 0.67  ->  ++
f < 0.90  ->  ##
otherwise ->  @@
```

To read the code precisely: `fill_for` returns `-` below 0.01, while `chart_to_markdown` and `grid_to_text` substitute `··` there, so the first band in any rendered legend is always the empty one. The band earns its place: a cell included at 0.5% painted as "slightly shaded" reads as being in the range, whereas `··` tells the truth -- it is out. Note that the value is *within-cell* (0..1), not a share of the whole grid; do not mix those two.

**Step five: turning a cell into money.** `Grid13.combos()` sums `values x CELL_COMBOS` over the whole board, so a cell contributes frequency x weight: a full `AKo` cell is 12 combos, a 0.25 `AKo` cell is 3; a full `AKs` cell is only 4, and at 0.5 it is 2. **A half-filled suited cell (2) is lighter than a quarter-filled offsuit cell (3)**, even though it looks paler on the page.

## 直觉 / Intuition

Read the grid as a seating chart for two cards: the row is the rank of the first card, the column is the rank of the second, both axes descending from A to 2. `(row, col)` and `(col, row)` are the same pair of ranks with the suit relationship reversed -- which is why the upper triangle is suited, the lower is offsuit, and why transposing toggles suitedness rather than strength.

The weights are suit-pairing counts, nothing more: 6 is the ways to take two cards of one rank out of four suits, 4 is two cards locked into the same suit, 12 is two cards free to be in different suits. That 12 is three times 4 is not a design choice; it is the price of the clause "must not share a suit".

The order of reading: orientation string first, diagonal second, then decide whether your question is about cells or about combos. Get that order wrong and every later number is a hallucination.

## 算例 / Worked examples

**Example 1 -- six coordinates.** Using `class_for_cell(row, col)` with zero-based indices on the A..2 axis:

| Cell | Class | Combos |
|---|---|---|
| (0,1) | `AKs` | 4 |
| (1,0) | `AKo` | 12 |
| (7,4) | `T7o` | 12 |
| (4,7) | `T7s` | 4 |
| (0,12) | `A2s` | 4 |
| (12,0) | `A2o` | 12 |
| (12,12) | `22` | 6 |

`(7,4)` deserves a word: the row label is `7`, the column label is `T`, because the axis descends so 7 sits after T; `row > col` puts it in the lower triangle, hence offsuit, and the class key always writes the higher rank first, so it is `T7o`.

**Example 2 -- 1326 by hand.** `13 x 6 + 78 x 4 + 78 x 12` = 78 + 312 + 936 = 1326. Those three slices are also the three shares: 5.88%, 23.53%, 70.59% (`78/1326` and so on). Check: `Grid13.full().combos()` -> 1326.0.

**Example 3 -- a range where cell-counting lies.** `python -m pokergto range "ATs+,KQs,JTs" --json` reports `classes: 11`, `combos: 44`, `range_percentage: 3.3183`. 11/169 = 6.51%. **A range covering a sixth of the cells contains a thirty-third of all starting combos.** The pairs-only case `22+`: 13 cells = 7.69% of cells, 78 combos = 5.88%.

**Example 4 -- a full suited cell against a half offsuit one.** A full suited cell is 4 combos; a half-filled offsuit cell is 6. On the page they render as `@@` and `++` respectively, so the *darker* cell is the lighter one. Visual area is uncorrelated with combos; only the rendered stat line ("884.0 combos = 66.67% of all 1,326") corrects the eye.

## 生成表 / Generated tables

The three shapes and their weights, from the actual enumeration in `pokergto.cards#combos_for_class`:

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

Add the rows: `13 + 78 + 78 = 169` classes and `78 + 312 + 936 = 1326` combos. That is where the two axes get their length, and it is the evidence behind "a completely filled grid is 1,326".

## 实战牌局 / Live hands

**Hand 1 (`hand.01-07-read-mdf-grid`) -- heads up, flop `Kh7s3d`, villain bets 3 into a pot of 6 (half pot); you are reading the defense chart on the button.**

Reading that chart is one full grid-to-combo conversion, in order:

1. Read `orientation` = `akqjt98765432-desc-diagonal-pairs-upper-suited`. That string decides the name of every cell that follows; `Grid13.from_chart` refuses anything else, so a chart from somewhere else cannot even be opened here.
2. Ten diagonal cells are full (`AA` through `55`, 10 x 6 = 60 combos); `44`, `33` and `22` are empty. The reason is a generator detail, and the chart in this repository writes it out loudly -- see the Range chart section.
3. The artifact reports its own totals: `total_combos = 884` (the rendered line says "884.0 combos"), `range_percentage = 66.6667%`. The threshold is `MDF = P/(P+B) = 6/9 = 66.67%`, the visualisation of `02-03`'s derivation.
4. Count the cells: 114 non-zero classes, 114/169 = **67.46%**. Its closeness to the combo figure 66.67% is a coincidence of this particular chart (whole cells filled in a fixed order, suited and offsuit appearing in pairs). For a suited-heavy range the two units separate, as in Example 3.
5. Land it on money: 884 of the 1,326 starting combos must continue (call or raise); at most 442 may fold.

**Hand 2 (`hand.01-07-flip-a-chart`) -- somebody shows you a "pure suited" defense shape and you want to know what it weighs as offsuit.**

Take `{AA, AKs, ATs}`: three cells -- one diagonal, two upper-triangle -- weighing 6 + 4 + 4 = **14**. Transposed: `{AA, AKo, ATo}` = 6 + 12 + 12 = **30**. The same shape weighs 2.14 times as much.

- Why it matters: anyone claiming "the suited and offsuit versions should defend at the same rate" must say whether he means the **frequency** pattern (same shape) or the **combo** count (different shape). Both cannot hold, unless every cell in the range is a pocket pair.
- One line checks it: `Grid13.from_range(parse("AA,AKs,ATs")).mirror().combos()` -> 30.0.

## 范围图 / Range chart

Below is the only chart artifact generated in this repository (`tools/gen_ranges.py`, built from `pokergto.odds.minimum_defense_frequency`, `provenance.kind = derived`). It is not a picture: it is a diffable markdown table, one stat line, one legend line, and the legend's thresholds are Step four above.

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

How to read it. The first column and the first row are the axis labels, `A` down to `2`. The top-left cell is `AA` (diagonal, 6 combos); to its right `(0,1)` is `AKs` (suited, 4) and below it `(1,0)` is `AKo` (offsuit, 12). The cell values are countable: of the 114 non-zero classes, 113 are exactly 1.0 (rendered `@@`) and one is 0.333333 -- `84o` -- which lands in `::` (1-34%) rather than `++`, because 0.34 is the `++` threshold. The remaining 55 classes carry no weight at all and render as `··`. The combos add up the same way: 10 full pairs = 60, 52 full suited cells = 208, 51 full offsuit cells = 612, plus `84o` contributing 12 x 0.333333 = 4, for 884. The artifact also carries two self-checks (`checks`): every cell's combo count must be one of {4,6,12}, and every frequency must lie in [0,1]; both report `pass: true`.

Now the one thing this chart should actually teach. **`T9s`, `98s` and `65s` are inside the quota; `22`, `33` and `44` are outside it.** That is not a hand-strength ordering, it is the generator's fill rule: `strength_key` in `tools/gen_ranges.py` groups classes by the *lower* of their two ranks, then by the higher, then by suitedness (pairs before suited before offsuit), so anything containing a 2, 3 or 4 is sorted last. The artifact records exactly this in `provenance.assumptions`: "MDF constrains only the total frequency; which combos reach it is filled here from strongest rank downward." In other words, the chart gives you **a quota of 884 combos**, not "defend these 114 classes". The stat line -- 884.0 combos = 66.67% of all 1,326 -- is the *only* number to compare against MDF; the eyeballed "about two thirds of the cells" is the class unit, and it is not that number.

## 为何成立、何时失效 / Why it works, when it breaks

**Why it holds.** The grid is just an index over 169 classes: thirteen ranks by thirteen ranks, deduplicated to exactly 169, and `matrix13.py` asserts that when it builds the class-to-cell map -- a wrong count raises at import time, not at chart-reading time. It is graph paper, not a strategy, so it needs no assumptions.

**Where readings go wrong:**

1. **Comparing across suitedness.** `AKs` and `AKo` are not two copies of one hand; they are two classes. The mirror check validates the orientation, never equivalence.
2. **Removal changes the weights.** The grid assumes a fresh deck. Holding `Ah` yourself, several of the twelve `AKo` combos no longer exist (`01-02`); "12 combos" becomes an upper bound rather than a fact.
3. **Cell percentages are not range percentages.** On a mixed chart the two diverge by more than three points (Example 3: 6.51% versus 3.32%).
4. **The grid cannot reach combo level.** It expresses "how much of this class", never "only the `As5h` combo of this class, because it blocks the nut flush". Real equilibrium tilts inside cells -- that is `02-03`'s closing remark and chapter 13's subject -- and this repository's artifacts stop honestly at frequency level.
5. **`··` is not a mathematical zero.** It means "frequency below 1%". To test for a true zero, read the artifact's `weights`, not the shading.
6. **Borrowed charts cannot be read.** `from_chart` accepts only that one literal string, so a flipped chart is an error rather than an hour of your life spent reading a mirror image.

## 陷阱 / Common mistakes

1. **Taking the diagonal for suited cells.** The diagonal is pocket pairs -- two cards of one rank, no suitedness to speak of, 6 per cell.
   *Cost*: a thirteen-cell pair band counted as 13 x 4 = 52 instead of 78, so `22+` reads as 3.92% of the deck instead of 5.88%. One command settles it: `poker range "22+"`.
2. **Measuring a range in cells.** 11 cells becomes "6.51%" when the range is 3.32% of combos.
   *Cost*: you believe you defend two thirds while you defend barely over half, and pure bluffs against you start printing (that is the arithmetic in `02-03`).
3. **Reading the mirror as "symmetric, therefore the same".** The shape is preserved; the weight goes from 4 to 12 per off-diagonal cell (14 -> 30 in Hand 2).
   *Cost*: every aggregate built on top of that comparison is off by the suited/offsuit ratio.
4. **Treating `··` as exactly zero and `++` as exactly 50%.** Five discrete bands are not a number.
   *Cost*: eyeballed precision is on the order of plus or minus sixteen points -- the widest band runs from 1% to 34%. For exact values read `weights`, or the `combos` field of `python -m pokergto range "<spec>" --json`.

## 练习 / Drills

- Derive `13 x 6 + 78 x 4 + 78 x 12` by hand, then explain why both triangles have exactly 78 cells (hint: `C(13,2)`).
- With `python -m pokergto range "AKo,AKs" --json`, and the two specs separately, verify the 12 : 4 = 3 : 1 relation and say why it ruins any statistic weighted by cells.
- Name the class and the weight of cells (4,7), (7,4), (0,9), (9,0) before checking with `class_for_cell`.
- Mirror `{TT+, AQs+}`: predict whether the combo count rises or falls, then verify with `Grid13` (the answer follows from which triangle holds more of the range).
- Read the MDF chart in this lesson and point to the single number that may be compared against 66.67%, then to the lookalike number that must not be.

## 自测清单 / Self-check

- [ ] I can recite the orientation constant and name the four places it is pinned.
- [ ] I can say what the diagonal, upper and lower triangles hold, how many combos each cell weighs, and where those numbers come from.
- [ ] I can convert a grid into a combo list and keep the combo unit apart from the class unit.
- [ ] I can say what `mirror()` preserves and what it does not, with a three-class example giving both numbers.
- [ ] I can state the five band thresholds and why the sub-1% band exists.

## 来源与置信度 / Provenance and confidence

Every number here is computed in this repository. No range chart or strategy output from a commercial solver or paid course appears anywhere in this lesson:

| Content | Source type | Location |
|---|---|---|
| Orientation convention | `derived` | `src/pokergto/matrix13.py#ORIENTATION`; `const` in `data/schema/range_chart.schema.json`; reader check in `src/pokergto/ranges.py` |
| Cell weights 6/4/12, 169 classes, 1,326 combos | `derived` | `pokergto.cards#combos_for_class` -> `data/gen/tables/table.01-01.combo-decomposition.json`; test `tests/test_evaluator.py#test_combos_enumeration_covers_the_deck_exactly` |
| Mirror invariant and the 14 -> 30 pair | `derived` | `src/pokergto/matrix13.py#Grid13.mirror`; `tests/test_matrix13.py` |
| The five shade thresholds | `derived` (a fact about the renderer, not about poker) | `src/pokergto/render.py#FILL_BANDS`, `#chart_to_markdown`, `#grid_to_text` |
| Range combo counts (78 / 44 / 114 / 40 ...) | `derived` | `python -m pokergto range "<spec>" --json`, fields `combos` and `range_percentage` |
| MDF floor chart (884 combos, 66.67%, 114 classes, fill order) | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json`; the fill rule is recorded in `provenance.assumptions` and in `tools/gen_ranges.py#strength_key` |

## 术语 / Terms

<!-- terms: grid-13x13, range-chart, range, hand-class, combos, suited, offsuit, pocket-pair, hole-cards, determinism, generated-artifact -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 13×13 网格 | grid-13x13 | the index over 169 classes; cell values are frequencies in [0,1] |
| — | 范围图 | range chart | one rendering of a grid: table + stat line + legend |
| — | 范围 | range | classes with frequencies, not a list of names |
| — | 手牌类别 | hand-class | one cell, e.g. `AKo` |
| — | 组合数 | combos | the only weighting unit: 6 / 4 / 12 |
| s | 起手同花 | suited | upper triangle, 4 per cell |
| o | 起手不同花 | offsuit | lower triangle, 12 per cell |
| — | 手对 | pocket pair | diagonal, 6 per cell |
| — | 底牌 | hole-cards | the two specific cards inside a cell |
| — | 确定性输出 | determinism | the same artifact renders byte-identically, which is what lets an orientation be frozen |
| — | 生成物 | generated artifact | charts come from `data/gen`, never from a screenshot |
