# Blockers as range effects: which hands a card keeps out of a range

<!-- hands: 2 -->
<!-- terms: blocker, removal-effect, range, combos, minimum-defense-frequency, bluff-range, value-range, the-nuts, showdown, capacity, hand-class, board -->

## 本节目标 / Objectives

- For any "class + visible cards" pair, produce the remaining combo count with `Range.with_removed`, and say why two visible cards of the same suit remove a different number than two of different suits.
- Predict the removal count from inclusion-exclusion (`hits(c1) + hits(c2) − hits(both in one combo)`) instead of listing combos.
- Write a blocker back into a whole range: remaining combos on the opponent's calling side and folding side, and the defence quota a half-pot bet demands (`MDF x remaining combos`).
- State the expected-value gap between bluff candidates that share a 169 cell, and name the class and the specific combos whose deletion produced it.

## 前置知识 / Prerequisites

- `01-02` blockers and removal effects: how one card rewrites a combo count; this lesson applies that operator to a whole range.
- `03-01` equity against nut advantage: a nut share is a ratio, so removal moves its numerator and its denominator together.
- `02-03` MDF: `pot/(pot+bet)`, and the fact that the defence obligation constrains a total without saying which combos fill it.

## 核心原理 / The principle

A blocker is not the adjective "this hand looks safe". It is an operator that runs item by item: delete every specific combo containing a visible card from a range. The number deleted is set by the **physical suits** of the visible cards, not by their ranks.

The concrete version of that sentence: `AKo` leaves **6** combos when `As` and `Ks` are visible and **7** when `As` and `Kh` are. Same two ranks, one ace and one king; the counts differ by 1 because `(As,Kh)` is itself an `AKo` combo while `(As,Ks)` belongs to `AKs`. Everything in this lesson is a consequence of that single fact.

Hence the method for "reading a blocker as a range effect": never say "he probably cannot have the nuts"; say "the top tier of his range goes from X combos to Y, therefore his defence quota and my bluff's expectation become these numbers".

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Every combo count: `pokergto.ranges.Range.with_removed` (derived; see `table.03-05.removal-effect-by-class`).
>     Expectations and thresholds: `pokergto.evaluator.best_score` per combo plus `pokergto.odds` (derived).
>     The ranges themselves are illustrative inputs authored for this lesson (`reference`).

## 推导 / Derivation

### One formula: inclusion-exclusion

Let `R` be a range (a weight vector over the 1326 combos) and `V` the set of visible cards. The engine's definition is

```
R.with_removed(*V)[i] = 0                if either card of ALL_COMBOS[i] is in V
                      = R.weights[i]      otherwise
```

For a single 169 class `C` the removed count satisfies inclusion-exclusion:

```
removed(C, {c1, c2}) = hits(c1) + hits(c2) - hits(the pair (c1, c2) being a combo of C)
```

`hits(c)` inside a class is "combos of that class containing c": 3 in a pair class (of `AA`'s six, three contain `As`), 1 in a suited class, 3 in an offsuit class. The third term is non-zero only when `(c1, c2)` is itself one of `C`'s combos.

### Why two suited visible cards delete more

`AKo`'s twelve combos are "an ace and a king of different suits". Make `As` visible: it hits 3 combos (`As` with `Kh`, `Kd`, `Kc`). Now make `Kh` visible too: it hits 3 more (`Ah Kh`, `As Kh`, `Ac Kh`). The intersection is the single combo `(As,Kh)`, and `(As,Kh)` really is an `AKo` combo because the two cards differ in suit, so `removed = 3 + 3 - 1 = 5` -> **7** left.

Swap in `Ks`: `As` hits 3, `Ks` hits 3, but `(As,Ks)` is suited, it belongs to `AKs`, so it is not among `AKo`'s twelve -> the intersection is empty -> `removed = 3 + 3 - 0 = 6` -> **6** left.

**The same sentence read backwards also holds, with the opposite direction.** For the suited class `AKs` (4 combos): `As+Ks` gives `1+1-1 = 1` removed -> 3 left; `As+Kh` gives `1+1-0 = 2` -> 2 left. The rule is: **your two cards delete the most from the classes they themselves cannot belong to.** Hold two cards of one suit and you cannot delete your own suited class, but you can take six combos out of the opponent's offsuit class.

### Removal on a range versus removal on a chart

`with_removed` acts on the 1326-wide vector, so it knows physical combos. A 13x13 frequency chart (one number per cell) does not: a cell stores a frequency, not a suit list. The consequences are:

- For a range filled **by class** (`parse("AKo,AQo,KQs,99")`), removing `Kd` and removing `Kh` give the same total, because each class holds all its suits symmetrically. The suit only decides *which* combos inside the class disappear.
- For a **specific hand against a range** (`Range.from_cards` on one side), suits start to matter for real: in Hand 1 three candidates that all read `AJ` delete 0, 1 and 2 of the opponent's flush combos, and their expectations differ by 11.76 chips.
- Fractional cells (`0.333333`) stay fractional after removal: `12 x 0.333333 = 3.999996`. That is the notational cost already shown in `01-01`, not a counting error.

## 直觉 / Intuition

Picture a range as a wall of drawers in a warehouse, each drawer holding 4, 6 or 12 physical boxes. **A blocker is not "this drawer gets less likely"; it takes boxes out of the drawer**, and how many it takes depends on the shape of the two cards in your hand, not on how loud their ranks sound.

Three sentences worth carrying to a table:

1. **Two cards of one suit are "clean" blockers.** They can never both sit inside one offsuit class, so their deletions do not overlap and the class loses more (6 against 5 for `AKo`).
2. **One card touches three buckets at once.** `Ad` deletes the opponent's nut flush (one fewer calling combo) and also deletes the `AJo` combos containing `Ad` (several fewer splitting combos). Counting only one bucket gets the sign wrong.
3. **With only two cards of a suit on the board, the flush bucket is empty.** The third suited card is what creates it, and only then can it be blocked (see `03-04`, Example 4).

## 算例 / Worked examples

### Example 1 -- reproducing every row of the generated table

```bash
PYTHONPATH=src python -c "
from pokergto.notation import parse
from pokergto.cards import Card
for spec, cards in [('AKo',('As',)),('AKo',('As','Kh')),('AKo',('As','Ks')),
                    ('AA',('As',)),('AA',('As','Ah')),('99',('9d',)),
                    ('KQs',('Ks',)),('KQs',('Kh','Qh')),('KJs',('As','Ks'))]:
    full=parse(spec); rem=full.with_removed(*[Card.parse(c) for c in cards])
    print(spec, cards, full.total_combos(), rem.total_combos())
"
```

The output matches the ten rows of `table.03-05.removal-effect-by-class` digit for digit: `AKo` 12 -> 9 -> 7 -> 6; `AA` 6 -> 3 -> 1; `99` 6 -> 3; `KQs` 4 -> 3 with `Ks` visible, and 4 -> 3 with `Kh+Qh` visible (both cards hit the *same* combo `KhQh`, so `1+1-1 = 1`); `KJs` 4 -> 3 with `As+Ks`.

### Example 2 -- the shape of the class decides the direction

Same ranks, different suitedness of the class, every number from `Range.with_removed`:

| Class | Baseline | `As+Ks` visible (suited) | `As+Kh` visible (offsuit) | Reading |
|---|---|---|---|---|
| `AKo` | 12 | **6** (6 removed) | **7** (5 removed) | Two suited cards remove more: no overlap |
| `AKs` | 4 | **3** (1 removed) | **2** (2 removed) | The direction flips for a suited class |
| `AJo` | 12 | 9 | **6** with `Ah+Jh` (6 removed) / **7** with `Ah+Jc` (5) | The deciding factor is suitedness, not rank |
| `QJs` | 4 | 4 (`As+Ks` touches nothing here) | **3** with `Qh+Jh` / **2** with `Qh+Jc` | One cell, a one-combo or two-combo difference |

The `AJo` row deserves a pause: `Ah+Jh` are two hearts, so `(Ah,Jh)` is an `AJs` combo, not in `AJo`'s twelve -> `3+3-0 = 6` removed -> 6 left; `Ah+Jc` are different suits, `(Ah,Jc)` is in the class -> `3+3-1 = 5` -> 7 left. It is the same inclusion-exclusion line as the `AKo` row, applied twice.

### Example 3 -- a whole range: what survives the board

Board `Kd 9d 6d 4s 2h` (three diamonds, so flushes exist right now), opponent's range written `AQs,KQs,QJs,JTs,T8s,AJo,99,44` (44 combos). Running `parse(spec).with_removed(*board)`:

| Class | Baseline | Left | What was deleted |
|---|---|---|---|
| `AQs` | 4 | 4 | nothing (both `Ad` and `Qd` are still unplayed) |
| `KQs` | 4 | 3 | `KdQd` (`Kd` is on the board) |
| `QJs` | 4 | 4 | nothing |
| `JTs` | 4 | 4 | nothing |
| `T8s` | 4 | 4 | nothing |
| `AJo` | 12 | 12 | nothing |
| `99` | 6 | 3 | the three combos containing `9d` |
| `44` | 6 | 3 | the three combos containing `4s` |
| Total | 44 | **37** | 7 |

The flush bucket is exactly 4 combos: `AdQd`, `QdJd`, `JdTd`, `Td8d` (found by filtering combos with `category_of(best_score(...)) == Category.FLUSH`). Those four numbers do all the work later: they are this range's nut capacity, and capacity is something a suit can move.

### Example 4 -- turning MDF into combos

`PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5` -> MDF 0.6667 heads-up. The obligation in absolute chips is `0.6667 x remaining combos`:

| Remaining combos | Where it comes from | Combos that must defend |
|---|---|---|
| 1326 | the whole space | 884.000000 |
| 37 | Example 3, after board removal | 24.666667 |
| 29 | board + hero's `AhJd` | 19.333333 |
| 28 | board + hero's `AhJh` | 18.666667 |

Same range, same size, and the opponent's quota moves from 18.666667 combos to 19.333333 combos purely because of which two physical cards hero holds. **MDF is a ratio; the quota is combos, and only the second one can be audited.** The folding threshold comes from the same algebra: `50/150 = 33.3333%` (`pokergto.odds#required_fold_frequency`).

## 生成表 / Generated tables

The first table is this lesson's spine. Compare rows 2 and 3: two visible cards of the same suit remove 6 from `AKo`, two of different suits remove 5; then look at `KQs`, where two suited visible cards remove only 1. **The asymmetry is deliberate**, because the symmetric phrasing ("an ace and a king is five fewer combos") is the sentence that gets quoted everywhere and survives no recomputation.

<!-- BEGIN AUTO:table.03-05.removal-effect-by-class -->
| Class | Visible cards | Baseline combos | Combos left | Combos removed |
|---:|---:|---:|---:|---:|
|   AKo |            As |     12.0 combos |  9.0 combos |     3.0 combos |
|   AKo |         As+Kh |     12.0 combos |  7.0 combos |     5.0 combos |
|   AKo |         As+Ks |     12.0 combos |  6.0 combos |     6.0 combos |
|    AA |            As |      6.0 combos |  3.0 combos |     3.0 combos |
|    AA |         As+Ah |      6.0 combos |  1.0 combos |     5.0 combos |
|    99 |            9d |      6.0 combos |  3.0 combos |     3.0 combos |
|   KQs |            Ks |      4.0 combos |  3.0 combos |     1.0 combos |
|   KQs |            Qh |      4.0 combos |  3.0 combos |     1.0 combos |
|   KQs |         Kh+Qh |      4.0 combos |  3.0 combos |     1.0 combos |
|   KJs |         As+Ks |      4.0 combos |  3.0 combos |     1.0 combos |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.ranges#Range.with_removed`

<!-- generated by: tools/gen_tables.py from pokergto.ranges::Range.with_removed -->
<!-- END AUTO:table.03-05.removal-effect-by-class -->

The second table puts the defence obligation against every size in one place so Example 4's conversion has a source: the `mdf` column times remaining combos is the quota, and the `fold_frequency_needed` column is the bluff's threshold.

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

## 实战牌局 / Live hands

### Hand 1 (`hand.03-05-flush-combo-blocker`) -- three candidates in one cell, 11.76 chips apart

Six-max cash. CO opens 2.5x, BB calls. Flop `Kd 9d 6d`, turn `4s`, river `2h`. Pot 100; hero (CO) bets 50 as a bluff. Opponent's range: `AQs,KQs,QJs,JTs,T8s,AJo,99,44` (44 combos, 37 after board removal). Hero's three candidates all read `AJ` in 169 notation and all score `high card A-K-J-9-6`:

| Hero's cards | Class | Opponent combos left | Beat hero | Split | Hero wins | Defence share | EV of the bet |
|---|---|---|---|---|---|---|---|
| `AhJh` | `AJs` | 28 | 15 | 6 | 7 | 75.00% | **+8.93** |
| `AdJh` | `AJo` | 29 | 15 | 7 | 7 | 75.86% | **+10.34** |
| `AhJd` | `AJo` | 29 | 13 | 7 | 9 | 68.97% | **+20.69** |

Where the difference lives: after board removal the opponent's 37 combos split into **16 calling, 12 splitting (all of `AJo`) and 9 folding**, and the flush bucket is exactly 4 combos: `AdQd`, `QdJd`, `JdTd`, `Td8d`. Each candidate cuts something different:

- `AhJh` deletes **no flush at all**. It removes 9 combos: 6 splitters (`AJo` 12 -> 6) plus `AhQh` (a caller) plus `JhTh` and `QhJh` (folders). The calling bucket is still 15 and the folding bucket drops to 7.
- `AdJh`: `Ad` kills the nut flush `AdQd` (one fewer caller) and `Jh` kills `JhTh` (one fewer folder); `AJo` falls 12 -> 7, i.e. 5 removed -- the `3+3-1` case, since `(Ad,Jh)` is itself an `AJo` combo.
- `AhJd`: `Jd` kills **two** flushes at once (`JdTd` and `QdJd`, two fewer callers), plus `AhQh` (a caller) and 5 `AJo` splitters -- and it leaves the opponent's folding bucket of 9 untouched, which is why hero's own win count is the highest of the three at 9.

So the intuition "I block the nuts" paints all three candidates the same, while the books read 0, 1 and 2 callers deleted -- and `AhJh` additionally throws away two of hero's own winning combos.

Model: worst case. Every combo scoring **at or above** hero's counts as a call (a split pays hero `+100/2 - 50 = +50`); only strictly worse combos count as folds. `EV = (wins x 100 + splits x 50 - called x 50) / combos left`. Threshold: `PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5` -> hero needs `50/150 = 33.3333%` of folds. All three clear it, and the spread between best and worst is **11.76 chips per attempt**.

Reproduce:

```python
from pokergto.cards import Card, class_key
from pokergto.notation import parse
from pokergto.evaluator import best_score
board = [Card.parse(c) for c in ("Kd","9d","6d","4s","2h")]
v = parse("AQs,KQs,QJs,JTs,T8s,AJo,99,44").with_removed(*board)   # 37.0
for hand in ("AhJh","AdJh","AhJd"):
    h = [Card.parse(hand[:2]), Card.parse(hand[2:])]
    hs = best_score(h, board)
    rest = v.with_removed(*h)
    win = sum(w for a,b,w in rest if best_score([a,b],board) < hs)
    tie = sum(w for a,b,w in rest if best_score([a,b],board) == hs)
    lose = rest.total_combos() - win - tie
    print(hand, class_key(*h), rest.total_combos(), lose, tie, win,
          100*(lose+tie)/rest.total_combos(), (win*100+tie*50-lose*50)/rest.total_combos())
```

### Hand 2 (`hand.03-05-same-class-different-suit`) -- one cell, one showdown rank, 0.00 against -1.79

Same session, a different deal: river `Kd 9d 6c 4s 2h` (only two diamonds, so the flush bucket **does not exist**; see `03-04` Example 4). Pot 100, hero bets 50. Opponent's range `AQo,KQs,99,66,QJs,JTs,T8s`: 33 combos after board removal (`KQs` down to 3, `99` and `66` to 3 each). Both candidates sit in the `QJs` cell and both score `high card K-Q-J-9-6`:

| Hero's cards | Opponent left | Beat hero | Split | Hero wins | Fold share | Combos defence needs (2/3) | EV |
|---|---|---|---|---|---|---|---|
| `QhJh` | 27 | 17 | 3 | 7 | 25.93% | 18.000000 | **+0.00** |
| `QdJd` | 28 | 18 | 3 | 7 | 25.00% | 18.666667 | **-1.79** |

There is exactly one mechanism. After board removal the opponent's 33 combos are 21 calling (`AQo` 12 + `KQs` 3 + `99` 3 + `66` 3), 8 folding (`JTs` 4 + `T8s` 4) and 4 splitting (`QJs`, same score as hero). `Qh` and `Qd` each delete 3 `AQo` callers and their own `QJs` splitter; the third cut lands somewhere different:

- `QhJh` also deletes `KhQh`. Of `KQs`'s three survivors (`KsQs`, `KhQh`, `KcQc` -- `KdQd` is gone with the board) that is a **calling** combo, so callers fall to 17.
- `QdJd` also deletes `JdTd`, a high-card `JTs` -- a **folding** combo, so callers stay at 18.

Two hands of identical strength: one thins the opponent's hardest bucket by 1, the other thins the softest bucket by 1. The decisions therefore split: `QhJh` is exactly break-even (**0.00**), `QdJd` loses **1.79** per attempt.

Switching the candidates to `AhQh` and `AhQd` (both in the `AQ` family) shows the table's two rows inside a range even more clearly:

| Hero's cards | Opponent's `AQo` left | Combos left | Beat hero | Split | Hero wins | EV |
|---|---|---|---|---|---|---|
| `AhQh` (two hearts) | 12 -> **6** | 25 | 8 | 6 | 11 | **+40.00** |
| `AhQd` (two different suits) | 12 -> **7** | 27 | 9 | 7 | 11 | **+37.04** |

`AhQh` deletes 6 `AQo` (`3+3-0`: `(Ah,Qh)` belongs to `AQs`), `AhQd` only 5 (`3+3-1`). Those twelve `AQo` combos are hero's **split** bucket here, so `AhQh` cuts it 12 -> 6 and `AhQd` only 12 -> 7. Both hands win the same 11 folding combos, so both numerators are `11x100 + splits x 50 - callers x 50 = 1000`, and the smaller denominator wins: `1000/25 = +40.00` against `1000/27 = +37.04`, a gap of **2.96**. The same "I hold AQ" intuition points the opposite way depending on which bucket the blocked combos sit in -- which is precisely why the subtraction must be done class by class.

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

This is `02-03`'s MDF floor for a half-pot bet, covering 884 combos (`1326 x 2/3`; the artifact records `total_combos = 883.999996`). It is here to make a point that is easy to skip: **a frequency chart cannot see a blocker.**

1. A cell stores a **frequency**, not a suit list. On this chart removing `Kd` and removing `Kh` give the identical answer: `884 -> 737.999997`, i.e. 145.999999 combos lost (per-combo filtering with `with_removed`), and the defence quota falls from `883.999996 x 2/3 = 589.333331` to `737.999997 x 2/3 = 491.999998`. The suit asymmetry -- the entire argument of this lesson -- is not expressible on a class-level chart.
2. For blockers to bite, the range has to be at combo granularity: `Range.from_cards` (my exact hand) against a class-level range (the opponent), exactly as in Hands 1 and 2. Only then does the question "which specific combos disappear" change a ratio.
3. The chart contains no opponent adjustment. "He defends less because of this texture / because of his blockers" is not something this picture supports: it is one feasible MDF fill. Such sentences are handled in the UNVERIFIED block below.

## 为何成立、何时失效 / Why it works, when it breaks

**Why it holds.** `with_removed` does one thing: zero the weight of every combo containing a visible card. Its correctness rests on `ALL_COMBOS` really being all 1326 physical combos (asserted by `InvariantError` in `pokergto.cards`), and touches no hand strength, no player, no size. Inclusion-exclusion only uses "a combo is exactly two cards".

**Where it stops being usable:**

1. **Class notation limits the granularity.** `notation.parse` accepts 169-class specs only: `PYTHONPATH=src python -m pokergto range "KsQs" --json` -> `error: cannot parse range token 'KsQs'`. To name "only `KsQs` survives" you must work at combo level (`Range.from_cards`, or a weight vector), not by stuffing suits into a spec.
2. **Removal is exact only for the combos you enumerated.** Every table here is a range written out class by class and then reduced. Once the opponent's range is "roughly what I think he has", you are no longer computing removal, you are computing a guess.
3. **The opponent's response is not in this repository.** "Blocked on the flush, he defends with a different bucket" is an opponent model; nothing here computes it. The sentence can only appear as `reference` / UNVERIFIED (path in the next section).
4. **A split is not a fold.** Hands 1 and 2 use the worst case: splits count as calls and pay hero half the pot (`+50`). Scoring splits as folds instead inflates EV by `splits x 50 / combos` -- for `AhJh` in Hand 1 that turns +8.93 into +19.64. Say which model you used.
5. **Below three cards of a suit the flush bucket is empty.** There is nothing to block; go back to `03-04` Example 4 first.

## 陷阱 / Common mistakes

1. **Using "an ace and a king block it" as "five fewer `AKo`" everywhere.** Table rows 2 and 3: `As+Kh` leaves **7** (5 removed), `As+Ks` leaves **6** (6 removed).
   *Cost*: one combo. It sounds trivial, but in Hand 2 one calling combo is the difference between **0.00** and **-1.79** per attempt, and on a river where the class is down to six combos that single combo is a sixth of the bucket.
2. **Counting only the nuts a blocker deletes and ignoring the buckets it also empties.** `Ad` kills the opponent's `AdQd` (a caller) and five `AJo` splitters. In Hand 1 the EV gaps are 1.42 between `AhJh` and `AdJh` and 11.76 between `AhJh` and `AhJd`, and every chip of them comes from the **net** across three buckets.
   *Cost*: the sign. The candidate the intuition "I block the nuts, so bluff" selects (`AhJh`) is the worst of the three (+8.93 against +20.69).
3. **Doing blocker reasoning on a class-level frequency chart.** The failure mode is visible in a command: on the chart, `Kd` and `Kh` both give `884 -> 737.999997`.
   *Cost*: you conclude blockers do not change the quota, when the real quotas are 18.000000 of 27 combos against 18.666667 of 28. Only a combo-granular range can show it.

## 练习 / Drills

- Predict, then check with `Range.with_removed`: how many `QJs` combos are left when `Qh+Js` are visible? And `Qh+Jh`? And `Qd+Jd`? (Hint: which term of inclusion-exclusion changes?)
- Take Example 3's board and range, replace `AJo` with `AJs`, and recompute the remaining total and the size of the flush bucket. Which column moves?
- Variant of Hand 1: hero holds `AdJd` (two diamonds). Predict the EV, then run the same block. Why is this hand no longer a bluff?
- With `python -m pokergto mdf --pot 10 --bet 5` and `--bet 3.3333`, convert the opponent's 37 remaining combos into a defence quota at both sizes and state each number.

## 自测清单 / Self-check

- [ ] I can state that `AKo` leaves 6 after two suited visible cards and 7 after two offsuit ones, and write `3+3-0` and `3+3-1`.
- [ ] I can explain why the direction reverses for a suited class (`AKs`: 4 -> 3 against 4 -> 2).
- [ ] I convert MDF from a ratio into a combo quota, and recompute it on a range already reduced by the board and my own cards.
- [ ] I know a class-level chart is suit-blind: `Kd` and `Kh` both give `884 -> 737.999997`, so blockers cannot be shown there.
- [ ] I can name which claims here are opponent models (and must be UNVERIFIED), and what path would make them derived.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every count and expectation in this lesson is computed in this repository; no commercial solver output appears anywhere:

| Content | Source type | Location |
|---|---|---|
| Example 1's rows and Example 2's table | `derived` | `PYTHONPATH=src python -c` over `pokergto.notation.parse` + `Range.with_removed`; digit-for-digit equal to `table.03-05.removal-effect-by-class` |
| Example 3's 44 -> 37, the per-class column, the 4 flush combos | `derived` | `Range.with_removed(*board)`, `Range.classes()`, `category_of(best_score(...))` |
| Example 4's thresholds (0.6667, 33.3333%) | `derived` | `PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5`; `pokergto.odds#required_fold_frequency` |
| All counts and EVs in Hands 1 and 2 | `derived` | the Python blocks in the text: per-combo three-way split (win / split / lose), `EV = (wins x 100 + splits x 50 - called x 50) / combos left`, worst case (splits counted as calls) |
| Chart figures `884 -> 737.999997`, `589.333331 -> 491.999998` | `derived` | per-combo filtering of the committed artifact `range.02-03.mdf-floor-vs-half-pot` (`Range.from_classes` + `with_removed`) |
| The three opponent ranges and hero's candidate lists | `reference` | authored for the lesson, checkable line by line; every decision uses only algebra and counts |

<!-- provenance: kind=reference verified=false -->
!!! unverified "UNVERIFIED"
    Absent from this lesson on purpose: that the opponent **changes his frequencies** because he is blocked ("without the flush he folds more often"), the true composition of a real opponent's range, and any strategy conclusion resting on those. Making such a sentence derived requires solving the spot -- `src/pokergto/solver` for the river board and range, `tools/run_solver.py` to emit an artifact carrying `solver_run` -- and then letting `tools/inject_doc_tables.py` fill an AUTO block from it. Until that exists, these claims may only appear marked UNVERIFIED.

## 术语 / Terms

<!-- terms: blocker, removal-effect, range, combos, minimum-defense-frequency, bluff-range, value-range, the-nuts, showdown, capacity, hand-class, board -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 阻断牌 | blocker | a visible card that makes specific combos impossible |
| — | 移除效应 | removal effect | `Range.with_removed`: zero the weight of every combo containing it |
| — | 组合数 | combos | the unit being deleted; 6 / 4 / 12 are only the no-information baselines |
| — | 范围 | range | a vector over 1326 combos; a chart is its class-level projection, suit-blind |
| — | 手牌类别 | hand class | one of 169 cells, the finest thing `parse` can name |
| — | 最低防守频率 | minimum defense frequency | `pot/(pot+bet)`; multiplied by remaining combos it becomes an auditable quota |
| — | 价值范围 | value range | here: the combos computed to beat hero, per combo, never asserted |
| — | 诈唬范围 | bluff range | the combos computed to lose to hero |
| — | 坚果 | the nuts | the top score achieved by either range on this board |
| — | 成牌容量 | capacity | how many combos of a tier a range holds, e.g. those 4 flushes |
| — | 摊牌 | showdown | the only comparison that exists after the fifth board card |
