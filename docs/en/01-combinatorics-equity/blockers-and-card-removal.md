# Blockers and removal effects: how one card rewrites the opponent's combo count

<!-- hands: 2 -->
<!-- terms: blocker, removal-effect, combos, hand-class, range, flush, straight, board, equity, pocket-pair, suited, offsuit -->

## 本节目标 / Objectives

- Given a hand class and one visible card, compute how many combos survive, and explain why the answer for two visible cards depends on whether those two cards share a suit.
- Quantify the blow one card deals to the supply of flushes, straights and pairs, and say which class loses the largest *percentage*.
- Explain how holding a card changes the **opponent's** distribution, not merely your own strength.
- Know exactly which layer of removal this engine models, and label anything beyond it as unverified.

## 前置知识 / Prerequisites

- `01-01` combos: `6 / 4 / 12` over 1326. Every subtraction in this lesson lands on that substrate.
- `00-01` board and streets: which cards count as visible.
- Inclusion-exclusion: `|A ∪ B| = |A| + |B| − |A ∩ B|`.

## 核心原理 / The principle

**Removal is one subtraction.** As soon as a card is visible -- your own hole cards, the board, or a card shown at showdown -- every combo containing it disappears from everyone else's supply.

For a single class, how much disappears depends only on how many of that class's combos the card participates in:

| Class (visible card) | Combos | Combos containing it | Left |
|---|---|---|---|
| `AA` (`As`) | 6 | 3 | 3 |
| `AKs` (`As`) | 4 | 1 | 3 |
| `AKo` (`As`) | 12 | 3 | 9 |
| `KK` (`As`) | 6 | 0 | 6 |

The last row matters more than the first three: **the same `As` halves `AA`, cuts `AKo` by a quarter, and leaves `KK` untouched.** These are not memorised figures -- `Range.with_removed()` produces them.

**One card can be worth 43 combos or exactly nothing**, depending on whether the range you are blocking contains it at all.

## 推导 / Derivation

**One card.** Take a class `RX` (`R != X`) and suppose `Rs` is visible.

- Pair `RR`: of the `C(4,2) = 6` combos, `C(3,1) = 3` contain `Rs` (`Rs` with each of the other three R's), leaving `6 − 3 = 3`.
- Suited `RX`: a suited combo needs both cards in the same suit, so `Rs` pairs only with `Xs`: exactly 1 of the 4, leaving 3.
- Offsuit `RX`: `Rs` pairs with the three `X` cards of the other suits, so 3 of the 12, leaving 9.
- If the visible card's rank is not in the class at all: subtract 0.

**Two cards: inclusion-exclusion.** For `AKo` with `As` and `Kh` visible:

```
combos containing As = 3, combos containing Kh = 3,
and AsKh is itself an AKo combo  ->  |intersection| = 1
12 − 3 − 3 + 1 = 7                                    (engine: 7)
```

With `As` and `Ks` visible, `AsKs` belongs to `AKs`, not `AKo`, so the intersection is empty:

```
12 − 3 − 3 = 6                                        (engine: 6)
```

**Flush supply.** Board `Kh 7h 2d`: 11 hearts remain, so a two-card flush is `C(11,2) = 55` combos. Kill one heart -- say you hold `Ah` -- and it is `C(10,2) = 45`: **10 combos gone, 18.18% of the supply.** Hold two hearts and the survivor count is `C(9,2) = 36`.

**Straight supply.** Board `9h 8h 2s`: `JT` (the open-ended core) has `JTs 4 + JTo 12 = 16` combos. Once `Th` is dead only 12 remain (`JTs 3 + JTo 9`), because `Th` participated in one suited and three offsuit combos.

## 直觉 / Intuition

A blocker is not the vague claim "I hold it so they cannot"; it is a **specific subtraction**. Three sentences carry the intuition:

- **Thin classes bleed the most.** `AKs` has 4 combos, so one card takes a quarter of it; `AKo` has 12 and one card also takes a quarter (coincidence of scale); a pair loses *half*. **One `As` costs `AA` 50% and `KK` 0%.**
- **Blocking their calls beats blocking their folds; both beat blocking nothing.** When you bluff you want the calling side smaller and the folding side... also smaller, and the *net* of the two directions is the whole answer. Hand 1 in `01-01` differs by 2.4 chips per attempt for exactly this reason.
- **A card absent from their range blocks nothing.** The easiest rule to forget and the most expensive one to ignore.

Mental model: the opponent's range is a stack of **stock boxes** (4, 6 or 12 units per cell). Revealing a card removes one unit from every box that contains it. The thinner the box, the bigger the percentage; empty boxes do not move.

## 算例 / Worked examples

**Example 1 -- `AKo` at three levels.** Start 12. `As` visible -> **9**. `As, Kh` visible -> **7**. `As, Ks` visible -> **6**. All three from `parse("AKo").with_removed(...)`. The gap between 7 and 6 is the intersection term.

**Example 2 -- all of `AK` (suited plus offsuit, 16 combos).** `As` visible -> 12 (`AKs` 3 + `AKo` 9). Also `Kh` visible -> 9 (`AKs` 2 + `AKo` 7). **"AK has 16 combos" stops being true the moment one ace is in your hand.**

**Example 3 -- heart supply.** Board `Th 9h 5d 3c 2s`: 11 hearts alive, `C(11,2) = 55` flush combos.
- You hold `Ah`: the opponent is left with **45** flush combos, and the 10 combos that contained `Ah` (`Ah` with each of the other 10 live hearts) are **all** gone -- which is to say, not one nut flush remains in their supply.
- You hold `Ad Td` (no heart): all 55 stay available to them.
**The same card deletes a different number of combos depending on what the opponent's range actually contains.**

**Example 4 -- a 4-bet value range.** Opponent shoves `QQ+,AKs` = 22 combos (18 pairs + 4 `AKs`).
- You hold `As`: `AA` 6 -> 3, `AKs` 4 -> 3, total **18**. **Your hand alone deleted 18.2% of their value range.**
- You hold `As Kc`: `AA` 3, `KK` 3, `QQ` 6, `AKs` 2 = **14**. The shape changes too: pairs-to-`AKs` moves from `18:4 = 4.5:1` to `12:2 = 6:1`.
- The shape matters more than the total: of the 14 survivors, 12 are pairs sitting above you and 2 are `AKs` (chop or flush-runout territory). That is the arithmetic reason `AKo` must be careful facing a shove whose range contains both an ace and a king it can use (`AKo` vs `QQ+,AKs` = 33.03% +/- 0.66pp, `n = 20000`, `seed = 6`, of which 13.7% is chop -- the `AKo`/`AKs` overlaps).

**Example 5 -- a committed chart.** The repository's half-pot MDF floor (`02-03`, `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json`) covers 884 combos. Enumerating its `weights` per combo and applying removal:

| Visible card | Combos lost | Remaining | Share of 1326 |
|---|---|---|---|
| `Ah` | 43 | 841 | 63.42% |
| `As` | 43 | 841 | 63.42% |
| `Kh` | 43 | 841 | 63.42% |
| `Th` | 43 | 841 | 63.42% |
| `2h` | **0** | 884 | 66.67% |

The `2h` row is this entire lesson: **that card is not in the range** (none of the 114 non-empty cells' combos uses `2h`), so as a blocker it is worthless. The gap between four rows of 43 and one row of 0 is more useful than any slogan about blockers.

## 生成表 / Generated tables

Removal operates on the substrate from `01-01`: cells must first be worth `6 / 4 / 12` before anything can be subtracted. Generated by `tools/gen_tables.py` via `pokergto.cards.combos_for_class`, with its own two checks:

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

This repository has **no** generated "after removal" table or chart artifact yet (`data/gen/tables/` holds this one table plus other chapters' tables). Every figure in Examples 1-5 comes from running `Range.with_removed()` at the time of writing, not from a committed artifact -- which makes it one level weaker than a generated table, and that is why it is listed in the provenance table below.

## 实战牌局 / Live hands

**Hand 1 (`hand.01-02-river-flush-blocker`) -- heads up, river `Th 9h 5d 3c 2s`, pot 100. BTN faces BB's 100-chip shove.**

Hero (BTN) holds `Ah 6d`: no two pair, no flush (one heart only), so the hand beats nothing but air. BB shoves pot into 100; hero must call 100 to win 300 and needs `100/(100+200) = 33.33%`. For a pure bluff-catcher the condition is "air must be at least 33.33% of the hands he shoves with".

Counting combos by the authored ranges (board removed):

- Value = flushes `C(11,2) = 55` + sets `55,33,22` at 3 each = 9 -> **64**.
- Bluffs = missed straight draws, written `KQo, KJo, QJo` = 12+12+12 = **36**.
- Air share `36/(64+36) = 36.0%` > 33.33% -> **call**.

Hero's `Ah` is not doing work through strength here; it is **deleting 10 value combos**: 64 becomes 54, and air share becomes `36/(54+36) = 40.0%`. Same board, same written ranges, and the margin over the threshold grows from +2.7 to +6.7 percentage points.
Now test sensitivity: if the bluff side held only 30 combos, the unblocked share would be `30/94 = 31.91%` -- **fold** -- while holding `Ah` gives `30/84 = 35.71%` -- **call**. There the blocker flips the decision outright.

**Hand 2 (`hand.01-02-four-bet-shape`) -- preflop. Hero (BTN) holds `As Kc`; BB jams a 4-bet shove written `QQ+,AKs`.**

- Baseline: `QQ+,AKs` = 22 combos, and `AKo` as a class holds 33.03% +/- 0.66pp against it (`n = 20000`, `seed = 6`).
- Your two cards delete the range down to `AA 3 + KK 3 + QQ 6 + AKs 2 = 14` combos: **36% smaller**.
- What matters is the **shape**: 12 of the 14 survivors are pairs that sit above you, 2 are `AKs`. Pairs-to-`AKs` moved from `4.5:1` to `6:1`.
- How to talk about the decision: before asking "am I good?", ask "what is left for me to beat", and spread the 14 combos on the table by class. `As Kc` simultaneously halves `AA`, halves `KK` and takes one quarter of `AKs`. **Your strength did not change; their stock did.**

```python
from pokergto.notation import parse
from pokergto.cards import Card
parse("QQ+,AKs").with_removed(Card.parse("As"), Card.parse("Kc")).classes()
# {'AA': 3.0, 'KK': 3.0, 'QQ': 6.0, 'AKs': 2.0}
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

The chart above is the defense range Example 5 was measured on: 884 combos across 114 non-empty cells. The chart itself carries **no** removal information -- it is the quota under "nothing else is visible".

To draw removal into a chart you need a new committed artifact: run `Range.with_removed(*board, *hero)` on the range before writing `weights`, and record which cards were removed in `provenance.assumptions`. That step has not been built here, so this lesson can only offer **subtractions you can re-run right now** (the 43 and the 0), not a post-removal chart. **That is a stated gap, not an oversight.**

One reading warning: the `84o` cell in that chart is only one third full (4 combos). When mixed frequencies and removal stack up, **count combos first and multiply by the frequency afterwards**; subtracting on the frequency line invents combos that never existed.

## 为何成立、何时失效 / Why it works, when it breaks

**What it requires**: that you are subtracting *physical* combos, and that the range really contains them. The first is a fact about the shuffle, the second a fact about the opponent.

Where it breaks or needs care:

1. **The engine models removal in exactly two places.** `Range.with_removed()` zeroes combos containing a named card among the 1326 -- every subtraction here comes from that call. And `pokergto.equity.runout_boards(board, known_hands=...)` shrinks the *deal* space when cards are known (the `1176 / 1081 / 990` ladder of `01-03`). **The engine does not chain removal effects across streets for you**, so second-order claims of the sort "and therefore his turn card probability changes too" get no number in this lesson.
2. **Supply is not frequency.** `AKs` down to 3 combos does not mean the opponent plays those three combos 100% of the time. Removal answers "how many", never "does he".
3. **Multiway pots stack removal.** Three opponents each hold cards, so the same card is deleted four times over. `02-03`'s multiway MDF formula assumes defenders are **independent**, and card removal is precisely the mechanism that breaks independence -- which is why that formula is an approximation. The assumption lives in `provenance.assumptions`; `07-01` handles it.
4. **Notation loss.** `pokergto.notation` cannot express "only the `AsKs` combo", so class-level subtraction is exact only when the answer lives at class level (all of this lesson's examples qualify). The moment you say "he only calls with the heart version", you are outside what the notation can compute (`to_spec()` marks such ranges `lossy`).

## 陷阱 / Common mistakes

1. **Blocking a card that is not in the opponent's range.** Example 5's `2h`: zero combos deleted.
   *Cost*: this is the root of "I have a blocker" being used to justify a bluff that never worked. Ask first "is this card in his range at all?", then "how many?".
2. **Forgetting inclusion-exclusion.** Assuming two visible cards must delete 6 `AKo` combos. In truth `As+Kh` deletes 5 (overlap 1) and `As+Ks` deletes 6.
   *Cost*: 7 versus 6 looks trivial until you divide: on a "how many bluffs are allowed" question the difference is the gap between fold frequencies that decide the line. Pass both cards to `with_removed(*cards)` instead of adding by hand.
3. **Treating removal as strength.** `AKo` against `QQ+,AKs` still holds 33.03% (`n = 20000`, bar +/- 0.66pp): shrinking the range does not turn you from an underdog into a favourite.
   *Cost*: calling shoves because "I removed his hands". Removal changes the **shape of the distribution**; whether you win is a separate equity question.
4. **Reporting absolute losses but not percentages.** Losing 1 combo from `AKs` (-25%) is not the same event as losing 1 from `AKo` (-8.3%), and `AA` losing 3 (-50%) is the most violent row in the table.
   *Cost*: you rank blockers in the wrong order and pick the worse bluff candidate.

## 练习 / Drills

- Compute by hand, then check with `with_removed`: board `Kd 8c 3h`, villain's range `KK,AKs,AKo,KQo,QQ,JTs`. How many combos per class, and in total?
- Inclusion-exclusion drill: how many `QJo` combos survive `Qs, Jh` visible? What about `Qs, Js`? Predict the intersection before you compute.
- Recast Example 3 in spades: board `Ts 8s 4c`. What is the flush supply, what is it after `As` is dead, and what percentage was lost?
- Variant of Example 5: remove `Ad`, `3d` and `Qd` in turn from the committed MDF chart; find which lose 43 and which lose 0, and explain the pattern.
- Decision drill: in Hand 1 shrink the bluff side to `KQo, QJo` (24 combos). Does the 33.33% threshold hold? What about holding `Ah`?

## 自测清单 / Self-check

- [ ] I can state what removing `As` does to `AA / AKs / AKo / KK`, in combos and in percent.
- [ ] I can explain why `AKo` leaves 7 after `As, Kh` but 6 after `As, Ks`.
- [ ] I can compute the flush supply on a two-heart board (`C(11,2) = 55`) and its value after one heart dies (45).
- [ ] I know a blocker worth zero exists whenever the card is not in the range, and can show it with `2h` on the MDF chart.
- [ ] I can name the two functions where this engine models removal, and the class of claims that fall outside them.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every subtraction in this lesson comes from this repository's code. No commercial solver or paid-course blocker chart is cited:

| Content | Source type | Location |
|---|---|---|
| The `6 / 4 / 12` substrate | `derived` | `src/pokergto/cards.py#combos_for_class`; `table.01-01.combo-decomposition` |
| All survivor counts (9/7/6, 12/9, 55/45/36, 16/12, 22/18/14, 43/0) | `derived` | `src/pokergto/ranges.py#Range.with_removed`, commands in the text; run at the time of writing, not a committed artifact |
| Hand 1's air shares (36.0% / 40.0% / 31.91% / 35.71%) | `derived` (counts) + `reference` (the range split) | counts from the subtraction above; the 33.33% requirement is `02-02`'s `B/(P+2B)` |
| `AKo` vs `QQ+,AKs` equity (33.03% +/- 0.66pp, 13.7% chop) | `derived`, **Monte Carlo** | `equity "AKo" --range-villain "QQ+,AKs" --mode mc --iterations 20000 --seed 6 --json` |
| A post-removal range chart | does not exist | needs `tools/gen_ranges.py` extended so visible cards are written into `provenance.assumptions` |
| Quantifying removal against the independent-defender assumption multiway | **UNVERIFIED / 未核验** | needs `src/pokergto/theory/multiway.py` or an equivalent fixed-action three-player model; `07-01` currently gives only the independent approximation |

## 术语 / Terms

<!-- terms: blocker, removal-effect, combos, hand-class, range, flush, straight, board, equity, pocket-pair, suited, offsuit -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 阻断牌 | blocker | a visible card; its action is deleting combos from the opponent's range |
| — | 移除效应 | removal effects | the subtraction itself and its percentage impact on supply |
| — | 组合数 | combos | what gets subtracted -- never the class |
| — | 手牌类别 | hand class | the cell the subtraction happens in: 4 / 6 / 12 |
| — | 公共牌面 | board | the first batch of visible cards, the default starting point |
| — | 胜率 | equity | removal reshapes the distribution, it does not decide the winner |
