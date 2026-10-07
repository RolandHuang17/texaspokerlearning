# Capped ranges: why one line contains no nuts

<!-- hands: 2 -->
<!-- terms: capped-range, the-nuts, capacity, line, range-advantage, nut-advantage, bet-size, overbet, polarized, combos, range, hand-strength, minimum-defense-frequency, bluff-to-value-ratio, board, value-bet, bluff -->

## 本节目标 / Objectives

- Read the **upper bound** an action line imposes on a range: use `is_capped` to decide whether a range can hold the strongest hand the board allows.
- State that the subject of "capped" is **my range**, not this board -- and quantify how far below the ceiling the range actually sits in evaluator units.
- Show how that bound removes sizes: connect the value share demanded by `02-04` with the break-even equity `e*` from `04-05` and say which hands are even eligible to bet a given size.

## 前置知识 / Prerequisites

- `03-01` nut advantage: its reference is the best of the two ranges. This lesson's reference is the best of the 1,176 combos that can still be dealt on this board. They are not the same object.
- `01-05` the seven-card evaluator: `is_capped` compares integers from that total order.
- `01-01` combos: `KK` is 6 combos, and on `Kh7s3d` it is the only thing on the roof.
- `02-04` the bluff-to-value ratio: a big size needs a value segment, and capacity is what fills it.

## 核心原理 / The principle

A range is **capped** on a board exactly when its own best holding sits below what that board can produce:

```
C(B)             = max over the 1,176 dealt combos of best_score(hand, B)  -- the board's ceiling
best(H, B)       = max over i in H of             best_score(i, B)         -- the range's strongest hand
is_capped(H, B)  <=>  best(H, B) < C(B) - tolerance
```

`H` must already exclude `B`: `is_capped` calls the same guard `nut_advantage` uses and raises `InputError("is_capped: range 0 still holds ... a card on the board")` rather than scoring a hand that cannot be dealt. `tolerance` defaults to **0**, which is the literal question: is the ceiling missing from this range or not. This is a `derived` claim: `C(B)` and `best(H,B)` are both computed combo by combo by the evaluator, with no external table. **The ranges themselves are illustrative inputs (`reference`)**, so every "capped" in this lesson means "capped for the range as written and then narrowed to the board", never "capped for the real line".

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Derivation: the next section. Generated table: `tools/gen_tables.py` -> `data/gen/tables/table.03-02.capped-range-check.json`.

## 推导 / Derivation

Three quantities have to be defined separately; conflating them is this lesson's only real error.

**The board's ceiling `C(B)`.** Its universe is **every combo that can still be dealt** -- 1,176 on a flop, 1,081 once the board shows four or five cards -- not "what I hold" or "what he holds", and not the 1,326 preflop combos either. The code is `pokergto.theory.range_advantage.board_ceiling(board)`, which the table generator calls too, so the printed ceiling and the verdict cannot drift apart.

The exclusion is not hygiene, and this is where a definition that sounds obvious stops being one. A combo holding a card the board already shows adds a **phantom** copy of that rank, and the evaluator takes its cards as given, so the phantom counts twice -- and a repeated card can beat every real hand. On `5c Kh 3s Th 4h` the board shows three hearts, so the best dealable flush is `A-K-Q-T-4`, made by `Ah Qh`. The undealable `Kh Ah` is read as `A-K-K-T-4`, and a second king outranks a queen in the third slot. Scored over 4,000 random boards, 100 of them put such a phantom above the real ceiling. It changes no number in this lesson's table (all three spots agree, which is exactly why a rule has to be stated rather than inferred from a case that happens to be harmless), and it is pinned by `tests/test_range_advantage.py::test_the_board_ceiling_counts_only_hands_that_can_be_dealt`.

**The range's best `best(H,B)`.** The same maximum, taken only over `H`.

**The test.** `best(H, B) < C(B) - tolerance`. Note that this is an **integer comparison** on the evaluator's total order.

One detail has to be stated, because it is the trap in this section. `tolerance` is counted in **units of the evaluator's packed integer score**, not in hand types. Measured on the four three-card boards used here:

- Each of them is covered by only **91** distinct final strengths, and the count is 91 on either universe (all 1,326 combos, or only the 1,176 that can be dealt) -- measured, not assumed.
- On `AsKsQh` the smallest gap between two adjacent distinct strengths is **1** unit (high card `A-K-Q-4-2` versus `A-K-Q-4-3`), so a tolerance of 2 really can absorb two kicker-level differences.
- But gaps with hand-type meaning are far larger: the smallest gap on `Kh7s3d` is **16**, trips sevens sit **368,640** units below trips kings, the capped `AsKsQh` row is **3,150,704** units below the ceiling, and the capped villain on `9h6d3c` is **184,320** units below.

That is why the default is 0 and not 2. A tolerance of 2 forgives about two kicker steps, which is nothing next to a 184,320-unit hand-type gap: it cannot silently reclassify a capped range. The earlier default of 2 was therefore not a soft margin but a rounding allowance whose size nobody had measured -- and the artifact caption that described it as "one step = one distinct hand strength" described something the code does not do. Both are corrected here; `data/gen/tables/table.03-02.capped-range-check.json` carries the new wording.

**Why this is a sizing conclusion and not a hand-strength conclusion.** A big bet is a formal challenge to be raised, and the top of the raise chain has to be occupiable, otherwise every hand that actually goes to war sits on the other side. `is_capped` judges exactly "can I stand on top", so it deletes big sizes and raises -- not the ability to win the hand on average, which Live hand 2 prices at a counter-intuitive number.

**The ceiling is a knife-edge, not a slope.** Computed per board, the classes that reach `C(B)` are: `Kh7s3d` -> only `KK`; `AsKsQh` -> only `JT`; `9h6d3c` -> only `99`; `As9s5d` -> only `AA`. **Each board has exactly one class on the roof.** Narrowed to the board those cells hold 3, 16, 3 and 3 legal combos respectively -- the pairs lose three of their six combos to the board's own rank, while `JT` shares no rank with `AsKsQh` and keeps all sixteen. So "is this line capped" usually reduces to whether one cell made it into the range.

## 直觉 / Intuition

Think of `C(B)` as the top floor of this particular building. Whether your range is capped asks not "is my floor high" but **do you have a key to the top floor**.

- With the key you may bet big, because when the opponent raises you hold hands that answer, and his raise becomes his own risk.
- Without the key your strongest hand is already downstairs. The opponent does not have to read your cards, only your line: he knows the top is empty on your side, so he can raise and call large sizes freely, **because nothing in your range is above what he raises with**.
- "Capped" and "behind" are different axes. Capped is an **upper bound**; behind is an **average**. A capped range can be comfortably ahead on average (Live hand 2 measures 63.1846%) and still be unable to supply the value segment a big size requires.

Mental model: `03-01` put a roof on the table; this lesson adds one rule -- **the position of that roof is set by the board, not by the two ranges**. `03-01` asks "who stands highest right now"; `03-02` asks "does your range even contain the highest floor this board has".

## 算例 / Worked examples

All verdicts come from `is_capped(parse(spec, exclude=board), board)` with the default `tolerance = 0`. Combo counts below are the narrowed ones unless a parenthesised "as written" count says otherwise; `python -m pokergto range "spec"` prints the written count, and `Range.with_removed(*board).total_combos()` the narrowed one.

**Example 1 -- `Kh7s3d`, hero = `AKs,AQs,ATs,KQs,AKo,AQo,99,77` (44 combos, 52 as written).**
`best(H,B)` = trips sevens (`77`, 3 combos left after the board's `7s`), `C(B)` = trips kings; the gap is 368,640 units -> **capped**.
How knife-edge that is: `is_capped(parse("AKs,AQs,ATs,KQs,AKo,AQo,99,77,KK", exclude=board), board)` -> **False** (47 combos, 58 as written, and hero's nut share moves from 3/44 = 6.8182% to 3/47 = **6.3830%** because the reference rises from trips sevens to trips kings -- and `KK` itself loses three of its six combos to the board's `Kh`). Adding `K7s` (two pair) stays capped; adding `73o` stays capped. **This is not a question of how many combos, it is a question of whether that one cell is present.**

**Example 2 -- `AsKsQh`, hero = `AA,KK,QQ,JT,T9,AT,KT` (65 combos, 82 as written).**
`best(H,B)` = straight to an ace = `C(B)` -> **not capped**, gap 0. Hero's nut share is 16/65 = **24.6154%**: all 16 `JT` combos survive, since neither rank appears on the board, while 17 of the spec's 82 combos are deals the board already made impossible.
Same board, villain = `98s,76s,54s,65,K9,K8,Q9,J9` (80 combos, 92 as written): `best` = one pair `K A Q 9`, **3,150,704** units below the ceiling -> **capped**. Add `JT` -> False. Add `T9s` -> still capped (`T9s` is only ace-high on this board; the straight needs a `J`).

**Example 3 -- `9h6d3c`: one side capped, the other not, on the same board.**
hero = `AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs` (63 combos, 66 as written) contains `99` -- 3 combos, not 6, because `9h` is on the board -- so `best` = trips nines = `C(B)` -> **not capped**.
Delete `99`: `is_capped(parse("AKo,AQo,AJs,KQo,TT,88,AKs,AQs", exclude=board), board)` -> **True**. One cell of range notation reverses the whole sizing conclusion.
villain = `87s,76s,65s,54s,T8s,T9s,98o,66,55` (39 combos, 48 as written): `best` = trips sixes, 184,320 units below -> **capped**.

**Example 4 -- capped does not mean weak.** Example 3's villain, all 39 capped combos, holds **61.2680%** equity against hero's 63 combos while its nut share is **0.0000%** and the verdict is **capped**. It is the favourite on average and it owns nothing on the ceiling. That pair of numbers is the cheapest available separation of "upper bound" from "average".

**Example 5 -- the roof moves with the card.** Sweeping all 49 possible turn cards after `9h6d3c`, hero is uncapped on exactly **3** of them (`9c`, `9d`, `9s`) and capped on the other **46**. The reason is plain: any non-nine turn either raises the ceiling (straights, full houses, quads arrive) or pushes `99` off the top. **"This line is capped" is a per-street proposition, not a verdict on the hand** -- which is `03-03`'s subject.

## 生成表 / Generated tables

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

`Best in range` and `Board ceiling` are the derivation's `best(H,B)` and `C(B)`; `Capped?` is `is_capped`'s return value. Note that these hero and villain ranges are **not** the ones in `table.03-01` (on `9h6d3c` the villain here omits `97o`: 48 combos instead of 60). Check the `spec` before carrying a number between tables.

The size side of the constraint is the break-even equity, which capacity has to clear:

<!-- BEGIN AUTO:table.04-05.bet-break-even-equity -->
|    Size | Fold frequency f | MDF at this size | Break-even equity e* | Regime | Residual |
|---:|---:|---:|---:|---:|---:|
| 1/3 pot |           25.00% |         75.0000% |              0.0000% |  above |        0 |
| 1/3 pot |           40.00% |         75.0000% |                    - |    all |        - |
| 1/3 pot |           50.00% |         75.0000% |            200.0000% |  below |        0 |
| 1/3 pot |           60.00% |         75.0000% |            140.0000% |  below |        0 |
| 1/3 pot |           75.00% |         75.0000% |            114.2857% |  below |        0 |
| 1/2 pot |           25.00% |         66.6667% |             25.0000% |  above |        0 |
| 1/2 pot |           40.00% |         66.6667% |            -50.0000% |  above |        0 |
| 1/2 pot |           50.00% |         66.6667% |                    - |    all |        - |
| 1/2 pot |           60.00% |         66.6667% |            200.0000% |  below |        0 |
| 1/2 pot |           75.00% |         66.6667% |            125.0000% |  below |        0 |
| 3/4 pot |           25.00% |         57.1429% |             35.7143% |  above |        0 |
| 3/4 pot |           40.00% |         57.1429% |             10.0000% |  above |        0 |
| 3/4 pot |           50.00% |         57.1429% |            -50.0000% |  above |        0 |
| 3/4 pot |           60.00% |         57.1429% |                    - |    all |        - |
| 3/4 pot |           75.00% |         57.1429% |            150.0000% |  below |        0 |
|     pot |           25.00% |         50.0000% |             40.0000% |  above |        0 |
|     pot |           40.00% |         50.0000% |             25.0000% |  above |        0 |
|     pot |           50.00% |         50.0000% |              0.0000% |  above |        0 |
|     pot |           60.00% |         50.0000% |           -100.0000% |  above |        0 |
|     pot |           75.00% |         50.0000% |            200.0000% |  below |        0 |
|   2 pot |           25.00% |         33.3333% |             45.4545% |  above |        0 |
|   2 pot |           40.00% |         33.3333% |             40.0000% |  above |        0 |
|   2 pot |           50.00% |         33.3333% |             33.3333% |  above |        0 |
|   2 pot |           60.00% |         33.3333% |             20.0000% |  above |        0 |
|   2 pot |           75.00% |         33.3333% |           -100.0000% |  above |        0 |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.ev#break_even_equity_to_bet`

<!-- generated by: tools/gen_tables.py from pokergto.ev::break_even_equity_to_bet -->
<!-- END AUTO:table.04-05.bet-break-even-equity -->

Three rules for reading it:

1. With `regime = above` only hands whose equity is **at least** `e*` want to bet; `below` is the inverted bluff region (caused by the denominator changing sign, not a slip); `all` means the size decides for every hand.
2. Two rows land exactly on `e* = 0.0000%`: one third pot at `f = 25.00%`, and pot at `f = 50.00%`. Not a coincidence -- that `f` is the fold frequency the size needs (`02-03`), at which air is indifferent between betting and checking. **A small size costs no capacity**, and that fact is why `04-02` exists.
3. Two pot at `f = 25.00%` requires `e* = 45.4545%`. Now look back at Example 1's `Kh7s3d`: the capped villain's two strongest segments, `KQo,AJo` (21 legal combos, 24 as written), hold only **36.3348%** against hero's rooftop segment `77,99` (9 legal, 12 as written), which does not even reach the **40.0000%** a two-times-pot call requires -- `ev_call(4.4, 8.8, 0.363348) = **−0.8063 bb**` per attempt. **That is the concrete path from "this line contains no nuts" to "you may not use this size".**

## 实战牌局 / Live hands

**Hand 1 (`hand.03-02-broadway-nut-cap`) -- heads up, turn `AsKsQh`, pot 12 bb. Hero holds 65 legal combos (82 as written) and fires the second barrel; Villain holds 80 (92 as written).**

The ranges are Example 2's. Verdicts: hero not capped (the 16 combos of `JT`, all legal here, nut share 16/65 = 24.6154%), villain capped (its best is one pair kings).

- **The decision: may hero bet two times pot, 24 bb?** After `is_capped` and the nut share, price the size. Villain's `MDF = 12/(12+24) = 0.333333` (`python -m pokergto mdf --pot 12 --bet 24`), so 26.67 of its 80 legal combos must continue. Betting 24 bb with `JT`, which wins always:
  `ev_bet(12, 24, 2/3, 1.0) = **20.0 bb**` against `ev_check(12, 1.0) = **12.0 bb**` -> the big size is worth **+8.0 bb** more per hand. Those 8 bb come from exactly one place: the 16 combos that stand on the board's ceiling.
- **What the wrong play costs: villain folds everything.** At `f = 1`, hero's air segment `T9` (16 combos) takes the whole pot uncontested every time: `ev_pure_bluff(12, 24, 1.0) = **+12.0 bb**` per attempt, **192.0 bb** across the 16 combos, which is **2.4000 bb** per combo of villain's 80-combo range. If villain instead defends exactly MDF (`f = 2/3`), `ev_pure_bluff(12, 24, 2/3) = **0.0**` -- that is `02-03`'s floor line, met in chapter 03.
- **Where is villain's quota?** Suppose hero sizes 2x pot with a deliberately 1 : 1 mix (`JT` 16 + `T9` 16, bluff-heavy against the required 1.5 : 1). Villain's best available segment `K9,K8` (24 legal combos, 32 as written) holds **39.2917%** against that betting range while calling 24 bb into 60 bb needs **40.0000%**; it misses by **0.7083** percentage points and `ev_call(12, 24, 0.392917) = **−0.4250 bb**` per attempt. The other 56 legal combos (`98s,76s,54s,65,Q9,J9`, 60 as written) hold **27.4958%**. A capped range must pay its quota with the segment closest to the top, and here it is within 0.7083 pp of not being able to.

**Hand 2 (`hand.03-02-capped-equals-not-weak`) -- 6-max, blinds 0.5/1, BTN opens 2.2 bb, BB calls 1.2 bb, pot 4.4 bb. Flop `9h6d3c`, BTN bets two times pot, 8.8 bb.**

Use the `table.03-02` pair: BTN 63 legal combos (66 as written), **not capped** (`99` is the board's ceiling); BB 48 (60 as written), **capped** (best is trips sixes), nut share **0.0000%**. Against BTN's whole range BB holds **63.1846%** -- the equity this row is computed from, not Example 3's 48-combo spec.

- **The counter-intuitive number**: those 48 capped combos hold **63.1846%** equity against BTN's 63. The capped side is the average favourite.
- **The decision: should BB call?** Calling 8.8 bb into `4.4 + 8.8 + 8.8 = 22.0 bb` needs **40.0000%**; BB's whole range holds 61.2680% and MDF asks only 33.3333% (16 of 48). Segment by segment against BTN's value-plus-bluff `99,AJs`: the two-pair-and-straight tier `T9s,98o,97o` (21 legal combos, 28 as written) **60.7937%**, the set tier `66,55` (9 of 12) **48.1770%**, and the 18 legal draw combos `87s,76s,65s,54s,T8s` (20 as written) only **39.4966%** -- 0.5034 pp short.
- **So the cap changes the direction, not the eligibility.** BTN's two-times-pot bet is licensed by owning the board's unique rooftop, but that rooftop is 3 legal combos and cannot carry 63. BB, though capped, can pay its 16-combo quota with the 30 legal combos that beat BTN's value-plus-bluff segment and still have spare. **"You are capped" deletes your raises and your big sizes; it does not delete your equity.**
- **What the wrong play costs.** If BTN reads "BB is capped" as "BB folds two thirds of it" and bets 2x pot with its whole range, the air segment runs into those 30 call-worthy combos; the capacity-legal construction is `99` (3 legal combos) plus two of the four `AJs` combos, and `3 : 2 = 1.5 : 1` is exactly what `table.02-04` demands at two times pot -- which two `AJs` combos is a free choice no artifact makes.

## 范围图 / Range chart

<!-- BEGIN AUTO:range.04-02.mdf-floor-vs-two-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. |
| 7 | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 6 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 5 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 4 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 3 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 2 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |

442.0 combos = 33.33% of all 1,326

Legend: `··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%; the diagonal is pairs, the upper triangle suited, the lower offsuit.

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.04-02.mdf-floor-vs-two-pot -->

This chart is the 33.33% a defender must keep facing a double-pot bet: 442.0 of all 1,326 combos, filled in **preflop** strength order. It is the mirror of this lesson's verdict:

- The quota question (the chart) says "keep 442.0 combos". The capacity question (`is_capped`) says "is the cell at `C(B)` among them". **The quota is always payable; the capacity is not.** This chart is filled by preflop rank and never looks at whether the board is `AsKsQh` or `9h6d3c`, so it cannot say one word about who owns the roof.
- Which is why any "defend 33% here" style conclusion deserves two questions first: which board-relevant tiers make up that 33%, and does any of them reach `C(B)`? When the two answers differ you get Live hand 1's shape -- quota payable, size not.
- Its denominator is all 1,326 preflop combos, which is a different quantity from `03-01`'s board-narrowed share denominators: this chart asks "how much of the whole deck's starting hand space clears the quota", not "how much of *this range on this board".

## 为何成立、何时失效 / Why it works, when it breaks

**What it requires**: that `C(B)` really is an upper bound for the board (it is, it scans every combo that can still be dealt, and it must not scan the ones that cannot); that the comparison is at combo level, not class level; and that the evaluator gives one total order to every combo.

Where it stops meaning what you want:

1. **The subject is this range, not this line.** The artifact's ranges are illustrative inputs authored here. A real CO opening range contains `KK`, so "hero is capped on `Kh7s3d`" is a property of this illustration, not of "CO is capped on a dry king-high flop". Turning it into the latter needs ranges generated from an equilibrium strategy plus an action line, and this repository has no such artifact (see the provenance table).
2. **`tolerance`'s unit is not "hand types".** Measured above: minimum adjacent gap 16 on `Kh7s3d`, 1 on `AsKsQh`, while trips nines sit 368,640 units below trips kings. The default is therefore 0: the test is exactly "strictly below". Even a tolerance of 2 would not change a single verdict on these boards, because no hand-type step is smaller than 184,320 units.
3. **A cap is per street and can be reversed by a card.** Example 5: hero is capped on 46 of the 49 turn cards after `9h6d3c`, uncapped on 3 (`9c`, `9d`, `9s`). Carrying a flop verdict to the river is this lesson's most common misuse.
4. **Nut advantage and capped can coexist, in opposite directions.** The `Kh7s3d` row is capped for **both** sides while hero still shows +6.8182% nut edge -- `nut_advantage` references the best of the two ranges, `is_capped` references `C(B)`. **One sentence that explains both columns is guaranteed to be wrong about one of them.**
5. **The ceiling is usually one cell.** On all four boards `C(B)` is reached by exactly one class (`KK`, `JT`, `99`, `AA`). Omitting or including that cell flips the verdict, so any "this range is probably not capped" estimate is unsafe; run it.
6. **Nothing here extends to multiway pots.** `is_capped` takes one range and one board; three-way "who can raise to the top" is an interaction of three upper bounds and this repository has no generated table for it.

## 陷阱 / Common mistakes

1. **Reading "capped" as "behind".** Example 4: BB is capped, nut share 0.0000%, and holds 61.2680% equity -- 63.1846% for the range Live hand 2 uses.
   *Cost*: BTN reads the cap as mass folding and puts 2x pot on all 63 combos, walking into BB's 30 call-worthy combos; the capacity-legal mix is `99` with two `AJs` combos at `1.5 : 1`. Conversely, the capped side folding its quota entirely is priced in Live hand 1: **+12.0 bb** per air attempt, **+192.0 bb** over 16 combos, **2.4000 bb** per combo of the defender's 80-combo range.
2. **Reading a small `tolerance` as "up to two hand types below still counts as the ceiling".** The unit is the evaluator's integer scale: trips sixes sit **184,320** units below trips nines on `9h6d3c`, and the default tolerance is 0.
   *Cost*: the verdict itself does not flip, but you invent a slope that does not exist and start treating "one tier below the roof" as almost good enough. Example 1 proves it is not: `+K7s` (two pair) stays capped, only `+KK` flips it.
3. **Treating the verdict as permanent.** Example 5: 3 uncapped turn cards out of 49.
   *Cost*: BTN keeps the flop's rooftop conclusion and overbets the turn; measured after `5h` BTN's whole range holds **22.7588%** equity while a two-times-pot size is asking for `f* = 0.666667` folds, so BB needs no folding at all to make hero's air segment lose a full bet each time.
4. **Carrying numbers between the two chapter-03 tables.** `table.03-01` and `table.03-02` deliberately share one `9h6d3c` villain spec, and a `checks` entry asserts the two tables really do. This lesson's Example 3 then drops `97o` from that spec, and that is where the two numbers come from: BB's equity is 63.1846% on the artifact's range and 61.2680% on the lesson's own, **1.9166** percentage points apart.
   *Cost*: dividing a combo count from one table by the denominator of the other yields a share neither artifact produced.

## 练习 / Drills

- Reproduce Example 1's three reversals: run `is_capped` on `AKs,AQs,ATs,KQs,AKo,AQo,99,77`, the same plus `KK`, and the same plus `K7s`, and report the verdict and combo counts -- capped True / False / True, over 44 / 47 / 46 legal combos (52 / 58 / 56 as written).
- Find which class reaches `C(B)` on `As9s5d` (hint: one class per board, as in Example 4's list) and explain why adding `99` to hero there does **not** uncap it -- the roof is trips aces, and `99` is only trips nines.
- Both ends of Live hand 1: `python -m pokergto mdf --pot 12 --bet 24`, then `ev_pure_bluff(12, 24, 1)` and `ev_pure_bluff(12, 24, 2/3)`, and explain why the second is 0.
- Build your own board-and-range pair where **both** sides are capped, then say what `is_capped` still contributes to sizing there. (Hint: only relative information remains, which is `03-01`'s `nut_edge`.)
- Sweep the 49 possible turn cards after `Kh7s3d` and count how many leave hero (`...,99,77`) capped, then state what the three uncapped cards have in common. (Hint: the answer is 46 versus 3, like Example 5, but the three cards are different -- work out what `C(B)` has become.)

## 自测清单 / Self-check

- [ ] I can name the two universes `is_capped` scans (the combos still dealable on this board, versus this range) and say which verdict needs which.
- [ ] I can list the single ceiling-reaching class for each of the four boards and explain why that makes the ceiling a knife-edge.
- [ ] I can separate "capped" from "behind" and produce the 61.2680% counterexample.
- [ ] I can state the real unit of `tolerance` and quote 184,320.
- [ ] I can explain why "this line is capped" is not "this hand loses", and why the verdict only holds for one street.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->

| Content | Source type | Location |
|---|---|---|
| The six rows of `best` / `C(B)` / `is_capped`, with their board-narrowed `Combos` column (44, 58, 65, 80, 63, 48) | `derived` | `data/gen/tables/table.03-02.capped-range-check.json`; `pokergto.theory.range_advantage#is_capped` |
| Break-even equity per size | `derived` | `data/gen/tables/table.04-05.bet-break-even-equity.json`; `pokergto.ev#break_even_equity_to_bet` |
| The 2 : 1 and 1.5 : 1 mixes at pot and double pot | `derived` | `table.02-04.bluff-value-ratio.json` from `02-04` |
| Double-pot MDF chart | `derived` | `data/gen/ranges/range.04-02.mdf-floor-vs-two-pot.json` (assumptions in `provenance.assumptions`) |
| Ceiling-reaching classes, the 368,640 / 3,150,704 / 184,320 gaps, 91 strengths per board, minimum gaps of 16 and 1 | `derived` | computed in this session over `pokergto.cards.ALL_COMBOS` with `pokergto.evaluator.best_score` |
| The cap reversals (`+KK`, `+K7s`, `-99`, `+JT`, `+T9s`, `+99` on `As9s5d`) | `derived` | `is_capped(parse(spec, exclude=board), board)`, commands and results in the text |
| 20.0 / 12.0 / +8.0 / +12.0 / +192.0 / 2.4000 / 0.0 bb | `derived` | `pokergto.ev.ev_bet`, `ev_check`, `ev_pure_bluff`, computed in this session |
| 63.1846% / 61.2680% / 48.1770% / 60.7937% / 39.4966% / 39.2917% / 27.4958% / 36.3348% | `derived`, exact enumeration | `pokergto.equity.range_equity(..., mode="exact")` |
| −0.8063 bb / −0.4250 bb | `derived` | `pokergto.ev.ev_call`, computed in this session |
| 3 uncapped turn cards of 49 (`9c/9d/9s` on `9h6d3c`, `7c/7d/7h` on `Kh7s3d`) | `derived` | `is_capped` evaluated board by board in this session |
| The six example ranges | `reference` | `CAPPED_SPOTS` in `tools/gen_tables.py`: illustrative inputs, not a range derived from any real line |
| The claim that a real opening range is capped on a real flop | **UNVERIFIED / 未核验** | needs preflop and postflop equilibrium output plus line conditioning; `data/gen/ranges` holds MDF floor charts only |
| Three-way interaction of upper bounds | **UNVERIFIED / 未核验** | `is_capped` accepts a single range; `03-09` currently gives the direction, not a three-range table |

## 术语 / Terms

<!-- terms: capped-range, the-nuts, capacity, line, range-advantage, nut-advantage, bet-size, overbet, polarized, combos, range, hand-strength, minimum-defense-frequency, bluff-to-value-ratio, board, value-bet, bluff -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 封顶范围 | capped range | `best(H,B) < C(B) - tolerance`; the subject is this range |
| — | 牌面可达上限 | board ceiling | `C(B)`: the best score any dealable combo makes on this board (1,176 of them on a flop) |
| — | 坚果 | the nuts | here the **absolute** top; in `03-01` the top of the two ranges |
| — | 牌型容量 | capacity | how many of a range's legal combos can place at `C(B)` |
| — | 行动线 | line | where a real range would come from; this lesson can only inspect authored ones |
| — | 下注尺度 | bet size | the degree of freedom capacity deletes |
| — | 超池下注 | overbet | the size most dependent on the roof |
| — | 极化 | polarized | top plus air; without capacity the middle has nowhere to stand, so it collapses to merged |
| MDF | 最低防守频率 | minimum defense frequency | a quota; an independent constraint on capacity |
| — | 诈唬与价值的配比 | bluff-to-value ratio | `02-04`'s mix, whose value side is cashed by capacity |
