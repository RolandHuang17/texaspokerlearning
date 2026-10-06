# Removal inside your own range: my hole cards delete my own nuts

<!-- hands: 2 -->
<!-- terms: removal-effect, blocker, range, combos, capacity, nut-advantage, hand-class, hole-cards, the-nuts, capped-range, minimum-defense-frequency, showdown -->

## 本节目标 / Objectives

- For my own range, list baseline combos against remaining combos class by class after conditioning on the board **and** my two hole cards, and name the specific combos that disappeared.
- Explain why conditioning on the actual hand changes equity and nut counts together, and in which direction: deleting my strongest tier lowers the equity of everything else in my range, deleting a weak combo raises it.
- Produce an example where one hand deletes **three** of my own nut combos, and explain why the count is larger than 1.
- Compute whether a value-to-bluff ratio still lands on whole combos after conditioning, and say which formula sets that constraint.

## 前置知识 / Prerequisites

- `03-05` blockers as range effects: `Range.with_removed` and inclusion-exclusion; here the same knife points at myself.
- `01-07` reading a 13x13 grid: a cell is not a combo -- only one of `AKs`'s four cards is `AdKd`.
- `01-01` combos and classes: `6 / 4 / 12` is the no-information baseline, not a constant.
- `03-01` nut advantage: a share is a ratio, so numerator and denominator are both combo counts.

## 核心原理 / The principle

Removal is not partisan. `03-05` used it to delete combos from the opponent's range; this lesson uses it on **my own**. The two cards I look at are the hardest constraints my own range has: they first delete the possibilities "I could be holding something else", then they rewrite the count of every tier I own.

Three objects must therefore be kept apart:

1. **The range as authored**: `parse(spec)`, e.g. 46 combos. It is the list of everything I could hold in this line, and it contains physically impossible combos.
2. **The conditioned range**: `parse(spec).with_removed(*board, *my_cards)` -- "the rest of my range, given that I hold this".
3. **The hand itself**: `Range.from_cards(my_cards)`, exactly 1 combo.

The gap between 2 and 3 is the lesson. The same decision (villain shoves, do I call) is correct on object 3 and wrong on object 1 -- not by rounding: this lesson computes both directions.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Counts and equities: `pokergto.ranges.Range.with_removed`, `pokergto.equity.range_equity` (exact enumeration),
>     `pokergto.theory.range_advantage` (derived). The authored ranges are illustrative inputs written for this lesson (`reference`).

## 推导 / Derivation

### Four objects, four denominators

Let `B` be the board (3 to 5 cards), `H = {h1, h2}` my hole cards, and `R` my range as authored.

```
R                       denominator = R.total_combos()                              # contains impossible combos
R.with_removed(*B)      denominator = combos of R using no board card               # board conditioned only
R.with_removed(*B, *H)  denominator = the above, minus combos containing h1 or h2   # "the rest of me"
Range.from_cards(H)     denominator = 1                                             # "this hand"
```

`nut_share = nut-tier combos / denominator`, so four objects give four numbers and none of them is a rounding difference: they answer four questions. `advantage()` uses the second (it calls `with_removed(*board)` internally, so `hero_combos` reports 33 rather than 46); `is_capped()` and `nut_advantage()` both refuse the first (they raise unless the range was narrowed); the third and fourth must be passed in by me.

### Why one hand deletes more than one combo

Each of my two cards hits several combos, and what disappears is the **union**:

```
deleted = {combo in R : combo intersects {h1, h2}}
        = |containing h1| + |containing h2| - |containing both|
```

The point is that "containing `h1`" crosses **several classes**. My `Ad` sits in `AKs`, `AQs`, `ATs`, `A2s` and everywhere else the range lists an ace of diamonds: one glance at my hand rewrites many rows of the list.

The same formula gives the direction: **if you hold the nuts, your range does not have them.** The nut tier is often a single combo (the best flush on a monotone board); delete it and the numerator becomes 0 while the divisor shrinks too -- `1/n` becomes `0/(n-3)` -- and the opponent's nut share goes from 0 to `1/m`, moving the whole nut edge to the other side.

### Whether the ratio lands on whole combos

`02-04`'s indifference condition says value:bluff is set by the size (`python -m pokergto odds --pot 12`: half pot 3 : 1, pot 2 : 1). Written as combos:

```
bluff combos needed = value combos / value_to_bluff
```

`value_to_bluff` is a ratio of numbers while combos are integers, so **for most value counts no size produces a whole number of bluff combos**. Conditioning changes the input "value combos", so it also changes which sizes are executable at all. That is the second way removal reaches into my own range: not whether I am strong, but whether my plan can be written down as actual cards.

## 直觉 / Intuition

The two cards you know for certain are your own, yet "my range" in coaching talk is usually the unconditioned list. Carry this sentence instead:

**Before I look, my range is 46 combos. After I look it is "46 minus the possibilities my cards just killed". And "this hand" is always 1 combo.** All three are real, but only the second and the third can decide anything: the second says what is left in the line to threaten with, the third says what to do.

Three transferable rules:

1. **Holding the nuts leaves your range without nuts.** Your hand is the only copy of that tier; once it is out, what remains is stuff that folds to a big bet.
2. **Deleting your worst combo makes the range stronger.** Holding `AhKh` (no flush, no straight, just overcards) makes the equity of the rest of my range go **up**, because the deleted combos were the dead weight. The direction depends on which tier you remove, not on the act of conditioning.
3. **One card punches through several cells.** My `Ad` has combos inside `AKs`, `AQs`, `ATs`, `A2s`; a single look at my hand changes many rows.

## 算例 / Worked examples

### Example 1 -- baseline versus remaining, class by class

Board: the monotone flop `Td 9d 5d`. My range as authored `R = AKs,AQs,KQs,ATs,KTs,QTs,JTs,TT,99,55` (`parse(R).total_combos()` = **46**). First condition on the three board cards (`33` combos), then delete whatever my actual cards kill:

| Class | Baseline | After board | Holding `AdKd` | Holding `AhKh` | Holding `AdKh` |
|---|---|---|---|---|---|
| `AKs` | 4 | 4 | **3** (`AdKd` gone) | **3** (`AhKh` gone) | **2** (both gone) |
| `AQs` | 4 | 4 | **3** (`AdQd`) | **3** (`AhQh`) | **3** (`AdQd`) |
| `KQs` | 4 | 4 | **3** (`KdQd`) | **3** (`KhQh`) | **3** (`KhQh`) |
| `ATs` | 4 | 3 | 3 | **2** (`AhTh`) | 3 |
| `KTs` | 4 | 3 | 3 | **2** (`KhTh`) | **2** (`KhTh`) |
| `QTs` | 4 | 3 | 3 | 3 | 3 |
| `JTs` | 4 | 3 | 3 | 3 | 3 |
| `TT` | 6 | 3 | 3 | 3 | 3 |
| `99` | 6 | 3 | 3 | 3 | 3 |
| `55` | 6 | 3 | 3 | 3 | 3 |
| **Total** | **46** | **33** | **30** | **28** | **28** |

Each column tells a different story. `AdKd` deletes **3** combos spread over 3 classes (`AdKd`, `AdQd`, `KdQd`) -- two cards take three of my own flushes out of the list, including the only nut flush. `AhKh` deletes 5 combos and **no flush at all** (two hearts touch nothing in the diamond tier). `AdKh` mixes them: one heart one diamond, 5 deleted, 2 of them flushes. The `TT/99/55` rows fall from 6 to 3 because `Td`, `9d`, `5d` are already on the board -- that is where chapter 01's `6 / 4 / 12` stops being a constant.

Reproduce:

```bash
PYTHONPATH=src python -c "
from pokergto.cards import parse_cards, Card
from pokergto.notation import parse
R='AKs,AQs,KQs,ATs,KTs,QTs,JTs,TT,99,55'; b=parse_cards('Td9d5d')
full=parse(R); bc=full.with_removed(*b)
print(full.total_combos(), bc.total_combos())
for mine in ('AdKd','AhKh','AdKh'):
    h=[Card.parse(mine[:2]),Card.parse(mine[2:])]
    r=bc.with_removed(*h)
    print(mine, r.total_combos(), {k:round(v,1) for k,v in sorted(r.classes().items())})
"
```

### Example 2 -- how conditioning moves equity: one range, four objects

Against the same opponent range `V = KJs,QJs,T9s,98s,87s,66,65s,A2s` (34 combos authored, 31 after the board):

| Object | Combos (denominator) | Hero equity | Hero nut share | Villain nut share | Capped? |
|---|---|---|---|---|---|
| Range as authored ( `advantage` narrows it internally ) | 33 / 31 | 0.603938 | 0.030303 (1/33) | 0.000000 | no (`is_capped` = False) |
| The rest of me, `R − AdKd` | 30 / 31 | 0.568338 | **0.000000** | **0.032258** (1/31) | **yes** (True) |
| The rest of me, `R − AhKh` | 28 / 31 | **0.634024** | 0.035714 (1/28) | 0.000000 | no |
| The rest of me, `R − AdKh` | 28 / 31 | 0.596833 | 0.000000 | 0.032258 | yes |
| This hand, `AdKd` | 1 / 31 | 0.965587 | — | — | — |
| This hand, `AhKh` | 1 / 31 | 0.317659 | — | — | — |

The directions are unambiguous. Deleting the nuts (`AdKd`) takes the rest of my range from 0.603938 down to 0.568338 (**−3.56 percentage points**) and hands the nut tier to the opponent: my share goes `1/33 -> 0`, theirs `0 -> 1/31`, and my `is_capped` flips to **True**. Deleting a drag (`AhKh`) does the opposite: the rest rises to 0.634024 (**+3.01 points**) and the nuts stay home. And "this hand" is a different kind of fact entirely: 96.5587% for `AdKd`, 31.7659% for `AhKh` -- **the range number 0.603938 is true of neither.**

```bash
PYTHONPATH=src python -m pokergto equity "AdKd" "KJs,QJs,T9s,98s,87s,66,65s,A2s" --board "Td9d5d" --mode exact --json
PYTHONPATH=src python -m pokergto equity "AhKh" "KJs,QJs,T9s,98s,87s,66,65s,A2s" --board "Td9d5d" --mode exact --json
```

Both report `exact: true, iterations: 1176` (every `C(47,2) = 1176` runout, no sampling error).

### Example 3 -- one look at my cards changes seven numbers

Ranges and board fixed, swapping only `H` between `AdKd` and `AhKh`:

| Quantity | `H = AdKd` | `H = AhKh` | Difference |
|---|---|---|---|
| Combos left in the rest of my range | 30 | 28 | 2 |
| Combos of mine that got deleted | 3 | 5 | -2 |
| Nut combos of mine that got deleted | 1 (`AdKd`) plus 2 other flushes | 0 | -- |
| Equity of the rest | 0.568338 | 0.634024 | -0.065686 |
| Nut share of the rest | 0.000000 | 0.035714 | -- |
| `is_capped` on the rest | True | False | flips |
| Equity of this exact hand | 0.965587 | 0.317659 | +0.647928 |

Same board, same opponent range, same "I am the preflop raiser" -- seven numbers all move. One cause: conditioning deleted a different set of combos.

### Example 4 -- is the value tier a class or a combo? the most expensive mistake here

My betting range is `AKs,AQs,KQs,JTs,87s,ATs,KTs` (`python -m pokergto range "AKs,AQs,KQs,JTs,87s,ATs,KTs" --json` -> **28 combos / 7 classes**). On the monotone flop `Td9d5d` the "nut tier" is the best flush, and filtering combo by combo (`category_of(best_score(...)) == Category.FLUSH`) shows that of the 25 combos surviving the board only **4** are flushes: `AdKd`, `AdQd`, `KdQd`, `7d8d`.

| My cards | My own combos deleted | Combos left | Flushes left (the value tier) | Bluff combos needed at half pot = value/3 | At pot size = value/2 |
|---|---|---|---|---|---|
| no conditioning | -- | 25 | 4 | 1.3333 | 2.0000 |
| `AhKh` | 5 | 20 | 4 | 1.3333 | 2.0000 |
| `JsTh` | 4 | 21 | 4 | 1.3333 | 2.0000 |
| `QdJd` | 2 | 23 | **2** (`AdKd`, `7d8d`) | 0.6667 | 1.0000 |
| `AdKd` | **3** | 22 | **1** (`7d8d`) | 0.3333 | 0.5000 |
| `KdQd` | **3** | 22 | **1** (`7d8d`) | 0.3333 | 0.5000 |

Two counter-intuitive facts. First, `AdKd` is **one** nut but it deletes **three** flush combos (`AdKd`, `AdQd`, `KdQd`), because my `Ad` and my `Kd` each also appear in other cells. Second, `AhKh` deletes 5 combos and no flush at all -- those five are heart pairs, unrelated to the diamond tier. So "I hold something from class X" is not "the count of class X goes down by 1".

## 生成表 / Generated tables

The first table carries the baselines this lesson keeps subtracting from: `6 / 4 / 12` are the per-class combo counts **with nothing visible**. Every row of Example 1 is one of them after subtraction (`TT` 6 -> 3, `AKs` 4 -> 2).

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

The second is `03-02`'s capped-range check, borrowed because its `Combos` column is the quantity this lesson keeps auditing: the column already holds **conditioned** counts (hero 44, villain 58 on `Kh7s3d`), while the very same spec strings handed to `parse(spec).total_combos()` return the authored 52 and 64. Both are computable; the conditioned one is what a share divides by. The verdicts recompute -- `is_capped` on narrowed ranges reproduces every row (hero capped on `Kh7s3d`, not capped on `AsKsQh`; villain capped on both) -- and handing it an un-narrowed range is refused outright:

```
error: is_capped: range 0 still holds 7c7s, a card on the board. Narrow it with
Range.with_removed(*board) or notation.parse(spec, exclude=board); nut shares and combo
counts divide by what the range contains.
```

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

### Hand 1 (`hand.03-06-nut-flush-is-my-own-hand`) -- one line, three objects, three answers

Six-max cash. CO opens 2.5x, BB calls. Flop `Td 9d 5d` (monotone), pot 12, effective stacks 24. BB shoves 24; hero (CO) must call 24 to win 36.

The threshold: `PYTHONPATH=src python -m pokergto spr --stack 24 --pot 12` -> SPR 2.000 and all-in equity needed `SPR/(1+2*SPR)` = **0.4000**; the same line appears in `python -m pokergto odds --pot 12` under 2x pot (MDF 33.33%, equity to call 40.00%).

Three objects, three answers:

| Object used for the equity | Equity | EV (`equity x 60 − 24`) | Decision | Against the range row |
|---|---|---|---|---|
| My range as authored (46 -> conditioned 33) | 0.603938 | **+12.2363** | call | -- |
| This hand, holding `AdKd` | 0.965587 | **+33.9352** | call | +21.70 |
| This hand, holding `AhKh` | 0.317659 | **−4.9404** | fold | −17.18 |
| This hand, holding `AdKh` | 0.577377 | +10.6426 | call | −1.59 |

The `AhKh` row is the reason this lesson exists: **deciding with the average of the range pays 24 chips into a hand that wins 31.7659% of the time.** The two answers differ by `+12.2363 − (−4.9404) = 17.18` chips per attempt, and the whole gap comes from the word "average".

There is a second layer. When I do hold `AdKd`, the **rest** of my range (30 combos) has zero nut share, `is_capped` True, equity 0.568338. My nuts left with me, so the rest of the line is made of things that fold to 24 chips -- the part of my range that should be calling is exactly the part that does not contain the nut flush, and the line cannot be played to `AdKd`'s standard.

Reproduce (equity, shares and the cap all need conditioning):

```bash
PYTHONPATH=src python -m pokergto equity "AhKh" "KJs,QJs,T9s,98s,87s,66,65s,A2s" --board "Td9d5d" --mode exact --json
PYTHONPATH=src python -c "
from pokergto.cards import parse_cards, Card
from pokergto.notation import parse
from pokergto.ranges import Range
from pokergto.theory.range_advantage import advantage, is_capped
b=parse_cards('Td9d5d'); H='AKs,AQs,KQs,ATs,KTs,QTs,JTs,TT,99,55'
V=parse('KJs,QJs,T9s,98s,87s,66,65s,A2s').with_removed(*b)
for mine in ('AdKd','AhKh','AdKh'):
    h=[Card.parse(mine[:2]),Card.parse(mine[2:])]
    a=advantage(parse(H).with_removed(*b,*h), V, b, mode='exact')
    s=advantage(Range.from_cards(h), V, b, mode='exact')
    print(mine, round(a.hero_combos,1), '%.6f'%a.hero_equity, '%.6f'%a.hero_nut_share,
          '%.6f'%a.villain_nut_share, is_capped(parse(H).with_removed(*b,*h), b), '%.6f'%s.hero_equity)
"
```

### Hand 2 (`hand.03-06-value-bucket-three-combos`) -- my two cards decide which size can still be written as whole hands

Same flop `Td 9d 5d`, pot 12. Hero (CO) plans to bet the flush tier for value and the rest as bluffs, sizing at half pot (6 into 12). `python -m pokergto odds --pot 12` gives value:bluff **3 : 1** at 1/2 pot and **2 : 1** at 1x pot. The value tier is the per-combo filter from Example 4 (25 combos after the board, 4 flushes):

| My cards | Value tier (flush combos) | Bluff combos needed at half pot | Whole? | Bluff combos needed at pot size | Whole? |
|---|---|---|---|---|---|
| `AhKh` | 4 | 1.3333 | no | 2.0000 | **yes** |
| `QdJd` | 2 | 0.6667 | no | 1.0000 | **yes** |
| `AdKd` | 1 | 0.3333 | no | 0.5000 | no |

So the decision is concrete: holding `AhKh`, the half-pot 3:1 **cannot be built out of whole combos** in my range (it wants 1.3333 bluff combos); the size that can be built is one pot (exactly 2). Same for `QdJd` (exactly 1). Holding `AdKd` neither works -- one value combo demands a fraction of a bluff at every size.

The cost of getting it wrong is computable. Take villain's side as a bluff-catcher that beats every bluff and loses to every value hand (it calls 6 into a pot of `12 + 6 = 18`: wins 18, loses 6), so its EV is `(bluffs x 18 - value x 6) / total`:

| Mix that actually goes in | Villain's bluff-catcher EV | Reading |
|---|---|---|
| value 4 : bluff 1 (under-bluffed) | **-1.2000** | villain should fold every bluff-catcher -- my value bets get no callers |
| value 3 : bluff 1 (the balanced half-pot mix) | **0.0000** | the indifference point, which is exactly what the 3 : 1 row of `odds` means |
| value 4 : bluff 2 (over-bluffed) | +2.0000 | villain calls any two cards and gains 2.00 per attempt |
| value 1 : bluff 1 (I hold `AdKd` but still deal 1 bluff per the unconditioned list of "4 flushes") | **+6.0000** | villain gains 6.00 per call -- the direct price of skipping the subtraction |

The last row is the point of this lesson: the value tier went from 4 to 1 because my own two cards deleted three of my flush combos. If I deal cards off the unconditioned list, what actually goes into the pot is a 1 : 1 mix, and any bluff-catcher villain owns earns 6.00 while I believe I am running a 3 : 1 policy. Conditioning is not tidiness; it is the difference between executing the plan I wrote and executing a different one.

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

This chart is `04-02`'s defence floor against a one-third-pot bet: `total_combos = 994.5` (`1326 x 3/4`, `range_percentage = 75.0%`, `threshold = 0.75`), 128 non-empty cells. It appears here as a **counter-example**: a chart filled by class cannot see my hole cards.

1. Cells store frequencies, not physical combos. The chart cannot express "my hand is the `AdKd` of the four in the `AKs` cell"; that needs combo granularity, i.e. Example 1's table.
2. The quota still moves under conditioning. Filtering the chart's 994.5 combos by the board `Td 9d 5d` leaves **868.5** (quota `868.5 x 0.75 = 651.375`, against `994.5 x 0.75 = 745.875`); filtering by the board plus my two cards leaves **781.5**. But that last step is where the chart lies: `AdKd` and `AhKh` both give 781.5, because a class-level chart is **suit-blind**. One chart, three numbers (994.5 / 868.5 / 781.5) -- and the half of conditioning that matters most is precisely the half the picture cannot show.
3. The chart contains no "the opponent adjusts". Everything said about villain in this lesson is a range I wrote down (`reference`); any sentence about him changing frequencies because of my conditioning must carry an UNVERIFIED marker (next section).

## 为何成立、何时失效 / Why it works, when it breaks

**Why it holds.** Everything used here follows from "a combo is two specific cards": `with_removed` zeroes combos containing a visible card; inclusion-exclusion counts the deletions; a nut share is a division whose numerator and denominator both have to be conditioned. Nothing uses hand strength, an opponent, or a size.

**Where it stops being usable:**

1. **The flush tier on a monotone board is fragile.** In Example 4 the value tier is 1 combo out of 4 in that class. Assuming "I listed `AKs`, so I have four value combos" is mistake number two of this lesson: only `AdKd` of the four is a flush.
2. **Notation stops at the class.** `parse` rejects `KsQs` (`error: cannot parse range token 'KsQs'`); naming one physical combo needs `Range.from_cards` or combo-level weights. Also measured here: `python -m pokergto range "AKs,AQs,KQs,ATs,KTs,QTs,JTs,TT,99,55" --json` fails with `error: strict round-trip failed: 'TT-55' re-parses to a different range (differing classes: ['66','77','88'] ...)` -- a non-contiguous set of pairs is rendered by `to_spec()` as one run, which re-parses into extra middle pairs. That is a defect of the notation layer, so this lesson quotes `python -c` with `total_combos()` instead of that command.
3. **`range_equity` refuses a five-card board.** After the river there is no equity, only a showdown: `error: a board of five cards has no equity left to compute`. On a river, condition and then compare with `best_score` (that is how both hands in `03-05` were computed).
4. **Exact enumeration has a budget.** Example 2's two single-hand calls cost 1176 runouts each with `mode="exact"`; widen villain to a real defence range (hundreds of combos) and you meet `BudgetExceeded`, then `--mode mc` with an error bar is the only honest option (`01-04`).
5. **My two cards delete my possibilities, not his.** The same `Ad` deletes a different batch of combos from the opponent's range (`03-05`). The two sides must be computed separately before they meet in one expectation, and every single-sided number above says which range it was taken over.

## 陷阱 / Common mistakes

1. **Deciding a specific hand with the range's average equity.** Hand 1: the range says 0.603938 (EV +12.2363), the hand `AhKh` says 0.317659 (EV **−4.9404**).
   *Cost*: 17.18 chips per attempt, and the sign is wrong -- the average says call, this hand says fold. Whenever the question is "what do I do with these cards", the subject must be `Range.from_cards`, or simply the `equity "AhKh" ...` command.
2. **Believing "I hold something from class X, so class X loses one combo".** Example 1: `AdKd` deletes **3** combos spread over `AKs`, `AQs` and `KQs`; `AhKh` deletes 5. Example 4: holding `KdQd` also deletes 3 of the 4 flushes.
   *Cost*: the value tier is wrong by a whole combo, and with it the ratio. `4/3 = 1.3333` cannot be dealt, but `3/3 = 1` looks "exact" -- so the mistake shows up as a plan that is arithmetically tidy and physically impossible. Subtract class by class.
3. **Feeding `is_capped` or `nut_advantage` an unconditioned range.** Both refuse it: `is_capped: range 0 still holds 7c7s, a card on the board.` and `nut_advantage: range 0 still holds TsAs, a card on the board.`, each demanding `Range.with_removed(*board)` or `notation.parse(spec, exclude=board)`. That is not pedantry: the `Combos` column of `table.03-02.capped-range-check` (44, 58) and `parse(spec).total_combos()` (52, 64) answer two different questions, and only the first may sit under a share.
   *Cost*: shares are systematically understated. `1/33 = 0.030303` against `1/46 = 0.021739` is a 39.4% gap (46/33 − 1) on one hand on one board: both are computable, and only the first is what `advantage` reports as `hero_combos`.

## 练习 / Drills

- Rerun Example 1's script with `H = AKo,AQs,KQs,TT` and my cards `AdQd`. List baseline / after board / after hand per class. Which row moves in `AKo`, and by how much?
- Variant of Hand 1: change the shove from 24 to 12 into a pot of 12 (one pot). Read the new threshold in `python -m pokergto odds --pot 12` (33.33%) and recompute the four decisions with the four equities above.
- Variant of Example 4: board `Td 9d 5d 2d` (four diamonds). Predict the size of the value tier, then run the per-combo filter. Why does it not necessarily get bigger?
- Verify the inclusion-exclusion yourself: `R = ATs,A2s`, my cards `Ad2d`. How many of my own combos disappear? Write them out.

## 自测清单 / Self-check

- [ ] I can separate four objects -- authored range, board-conditioned range, "board and my cards" range, and this hand (1 combo) -- and state each one's denominator.
- [ ] I can give an example where two cards delete three of my own flush combos (holding `AdKd` on `Td9d5d`).
- [ ] I know conditioning can go either way: delete the nuts and the rest loses equity, the nut share goes to zero and `is_capped` can flip true; delete a drag and the rest gains equity.
- [ ] I can compute whether `value/3` and `value/2` are whole numbers after conditioning, and say which sizes that leaves executable.
- [ ] I know `is_capped` and `nut_advantage` both reject an unconditioned range, and that `parse(spec).total_combos()` still returns an authored divisor -- the divisor of a different question, not of a share.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number here is computed in this repository; no commercial solver output and no paid-course content appears:

| Content | Source type | Location |
|---|---|---|
| Example 1's 46 / 33 / 30 / 28 / 28 and the per-class table | `derived` | `python -c` over `pokergto.notation.parse` + `Range.with_removed` + `Range.classes()`; command in Example 1 |
| Example 2's equities 0.603938 / 0.568338 / 0.634024 / 0.596833 | `derived` | `advantage(parse(R).with_removed(*board, *H), V.with_removed(*board), board, mode="exact")` (exact, 1176 runouts) |
| Example 2's nut shares 0.030303 / 0.000000 / 0.035714 / 0.032258 and the `is_capped` flip | `derived` | the same call's `hero_nut_share` / `villain_nut_share`, plus `pokergto.theory.range_advantage#is_capped` |
| Example 2 and Hand 1's single-hand equities 0.965587 / 0.317659 / 0.577377 | `derived` | `PYTHONPATH=src python -m pokergto equity "AdKd" "KJs,QJs,T9s,98s,87s,66,65s,A2s" --board "Td9d5d" --mode exact --json` (and the same command naming `AhKh`, `AdKh`) |
| Hand 1's thresholds SPR 2.000 / 0.4000 and the 2x-pot row | `derived` | `python -m pokergto spr --stack 24 --pot 12`; `python -m pokergto odds --pot 12` |
| Hand 1 and 2's EVs +12.2363 / +33.9352 / -4.9404 / +10.6426 and `(equity x 60 - 24)` | `derived` | the equities above times the threshold line; bluff-catcher EV `(bluffs x 18 - value x 6) / total`, threshold `pokergto.odds#equity_needed_to_call(12, 6)` = 0.25 |
| Example 4's flush tiers (4 / 2 / 1) and the 28 / 25 counts | `derived` | `best_score` + `category_of == Category.FLUSH` per combo; `python -m pokergto range "AKs,AQs,KQs,JTs,87s,ATs,KTs" --json` -> 28 combos / 7 classes |
| Chart figures 994.5 (75.0%), 868.5, 781.5 | `derived` | per-combo filtering of the committed artifact `range.04-02.mdf-floor-vs-third-pot` plus `with_removed` |
| All ranges (hero / villain spec strings) and the chosen hole cards | `reference` | illustrative inputs authored for the lesson; every decision uses only algebra and counts |

<!-- provenance: kind=reference verified=false -->
!!! unverified "UNVERIFIED"
    Not computed anywhere in this repository, and therefore absent from the lesson as numbers: that the opponent changes his frequencies because my range got conditioned, what a real CO range does on a monotone flop, and "he folds more because he knows you hold `AdKd`". The path that would make such a sentence derived runs through `src/pokergto/solver` (solve the spot with the board, both ranges and the size set fixed) and `tools/run_solver.py` (emit an artifact whose provenance carries `solver_run`), then `tools/inject_doc_tables.py` fills the AUTO block. Until then these claims may only appear as UNVERIFIED, without numbers.

## 术语 / Terms

<!-- terms: removal-effect, blocker, range, combos, capacity, nut-advantage, hand-class, hole-cards, the-nuts, capped-range, minimum-defense-frequency, showdown -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 移除效应 | removal effect | one operator, two targets: the opponent's range (`03-05`) and my own (here) |
| — | 阻断牌 | blocker | my two cards -- the hardest constraints on my own range |
| — | 底牌 | hole cards | one specific combo; `Range.from_cards` is the only honest representation |
| — | 范围 | range | a 1326-wide vector; "my range" is a different object before and after conditioning |
| — | 手牌类别 | hand class | a cell of 4 / 6 / 12 combos; cells are not combos |
| — | 组合数 | combos | the unit of every table here; 6/4/12 is the baseline, not a constant |
| — | 成牌容量 | capacity | how many combos of a tier (those 4 flushes) my range holds |
| — | 坚果优势 | nut advantage | the share difference; it crosses to the other side once I hold the nuts |
| — | 坚果 | the nuts | the best score either range can reach on this board |
| — | 封顶范围 | capped range | the side that cannot reach the ceiling; `is_capped` demands a narrowed range |
| — | 最低防守频率 | minimum defense frequency | times remaining combos gives the quota, and the quota is conditioned too |
| — | 摊牌 | showdown | the only comparison that survives the fifth board card |
