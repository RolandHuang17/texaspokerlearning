# Board texture classes: whom monochrome, two-tone, paired and connected boards help

<!-- hands: 2 -->
<!-- terms: board-texture, monochrome-board, two-tone-board, rainbow-board, paired-board, connected-board, static-board, dynamic-board, wet-board, dry-board, broadway-board, backdoor-draw, flush-draw, range-advantage, equity-advantage, nut-advantage, capacity, range, combos -->

## 本节目标 / Objectives

- Run `pokergto.board.classify` on any 3-to-5-card board, produce its composed id (say `dynamic.two-tone.connected`), and say which predicate wrote each word.
- For one fixed pair of illustrative ranges, compute the three numbers `advantage` returns -- equity edge, nut edge, and `who_can_bet_often` / `who_can_bet_big` -- on boards of different texture.
- Show, with numbers, that a classification is not a measurement: this lesson computes a pair of boards whose labels are opposite (`dynamic` against `static`) whose equity edges differ by 0.40 percentage points, and a pair whose labels are identical whose bet expectations differ by 3.3333 chips.
- Name the two places where the engine contradicts poker speech: `Kh7s3d` is classified `dynamic`, and on a paired board the share of "at least one pair" is 100% by construction. Explain why the rules say so.

## 前置知识 / Prerequisites

- `03-01` equity advantage against nut advantage: the two questions, and why they must not be collapsed into one verdict.
- `01-07` reading a 13x13 grid: one cell is 4, 6 or 12 combos.
- `01-01` combos and classes: `6 / 4 / 12` and the 1,326.
- `01-03` exact equity by enumeration: the outs-to-probability table, quoted directly in Worked example 4.

## 核心原理 / The principle

Board texture is a **set of classification rules**; range advantage is a **measurement**. They are not the same object and neither substitutes for the other.

The rules live on three axes in `pokergto.board`: suit structure (`monochrome` / `two-tone` / `rainbow`), rank structure (`paired` / `connected` / `broadway` / `low` / `max_gap`), and a derived `dynamic` / `static` from the first two. Every one of them returns true or false for a concrete board and can be run.

"There is no predicate for whom a board favours." That sentence can only be answered by `pokergto.theory.range_advantage.advantage(hero, villain, board)` on **one concrete board and two concrete ranges**, which returns the equity edge, the nut shares, and two separate verdicts: who can bet often, who can bet big.

So the fixed phrasing of this lesson is: **the classifier names the box, `advantage` weighs it.** A claim of the form "this kind of board favours the raiser", carrying neither board nor range, is not allowed here.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Classification predicates: `pokergto.board#classify` (derived). Advantage numbers:
>     `pokergto.theory.range_advantage#advantage` (derived, exact enumeration). Both `hero` and `villain`
>     ranges are illustrative inputs authored here (`reference`): nobody's opening range, no solver output.

## 推导 / Derivation

### Three axes, seven predicates

Let `values` be the distinct board ranks and `suits` the set of suits:

```
monochrome  = len({suit}) == 1
two_tone    = len({suit}) == 2
rainbow     = len({suit}) >= 3
paired      = len({rank}) < len(board)
connected   = some two adjacent distinct ranks differ by 1 (A-2-3 counts: the wheel)
max_gap     = max(difference between adjacent distinct ranks), 0 for a one-rank board
flush_draw  = some suit appears >= 2 times on the board
straight_draw = some window of five consecutive ranks contains >= 2 board ranks (an ace joins as 14 and as 1)
dynamic     = connected or (flush_draw and not monochrome) or straight_draw
```

`class_id` is concatenated in a fixed order: `dynamic`/`static` first, then suit structure, then `paired`, `connected`, `broadway`, `low`. The string is stable, so the same board gets the same label in every table.

The three suit predicates are exclusive and exhaustive for a five-card board only in the sense the code defines: `len({suit})` can be 1, 2, 3 or 4, and `rainbow` takes both 3 and 4. The rank axis is independent of it: `Kh7s7d` is `paired` **and** `rainbow`.

### Why `dynamic` is nearly always true

`straight_draw` asks only that two board ranks share a five-wide window. On `Kh7s3d` the window `[3..7]` contains both 3 and 7 -> true, so the textbook dry board is `dynamic.rainbow`. To reach `static` every pair of board ranks must be at least five apart: `Kd 8h 3s` (gaps 5, 5, 10) is `static.rainbow`; `Kh7s3d` (gaps 4, 6, 10) is `dynamic.rainbow`. One step of one rank, opposite labels.

That is a property of the definition, not a bug: `dynamic` means "somebody is holding a draw here", and on K-7-3 somebody really is holding 8-6 or 5-6 for a gutshot. It never claimed to measure what coaches call wet.

### Where the numbers come from

`advantage` does three things:

```
hero_equity, villain_equity = range_equity(hero, villain, board, mode="exact")   # all-in, sums to 1
equity_edge   = hero_equity - villain_equity
nut_share(X)  = combos of X scoring exactly the best score achieved by either range / combos of X
nut_edge      = hero_nut_share - villain_nut_share
who_can_bet_often = sign of equity_edge ; who_can_bet_big = sign of nut_edge
```

The denominator is the point of this chapter: a nut share is a **ratio**, so both its numerator and its denominator are combo counts, and anything that deletes combos -- the board, my own hole cards -- moves the number. That is `03-06`'s subject.

One hard limit: `range_equity` refuses a five-card board (`a board of five cards has no equity left to compute`). After the river there is no equity, only a showdown, so every river comparison below counts hands with `pokergto.evaluator.best_score` instead of computing equity.

## 直觉 / Intuition

A label is what you stick on the box; `advantage` is what the scale says. Labelling does not change the weight. Three transferable causal stories:

1. **The suit axis decides whether flushes exist at all.** Two of a suit on the board plus two in hand is four cards, not a flush, so made flushes number zero; three of a suit on the board makes `C(10,2) = 45` starting combos into a flush on the spot, 3.3937% of the 1,326.
2. **The paired board moves everybody's floor.** A board pair means every hand's best five contains a pair, so "at least one pair" is 100% for both ranges (measured below: hero 50/50, villain 32/32). The informative question becomes who holds the trips and who holds the four of a kind.
3. **Connectedness decides whether straights already live in a range.** Add `4c` to `Kh7s3d` and the illustrative caller suddenly owns four straight combos; the same people on `Kh7s3d` own none.

## 算例 / Worked examples

### Example 1 -- one pair of ranges, one rank set, three suit structures

Ranges (illustrative, `reference`): hero = `AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT` (54 combos), villain = `KQs,QJs,KJs,JTs,98s,76s,99,55` (36 combos). Ranks stay A-9-5; only the suits move:

```bash
PYTHONPATH=src python -c "
from pokergto.cards import parse_cards
from pokergto.notation import parse
from pokergto.theory.range_advantage import advantage
H='AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT'; V='KQs,QJs,KJs,JTs,98s,76s,99,55'
for b in ('Ah9c5d','As9s5d','As9s5s'):
    a=advantage(parse(H),parse(V),parse_cards(b),mode='exact')
    print(b, '%.6f %+.6f %.6f %.6f %+.6f'%(a.hero_equity,a.equity_edge,a.hero_nut_share,a.villain_nut_share,a.nut_edge))
"
```

| Board | `classify` id | hero equity | equity edge | nut share hero / villain | nut edge | combos used |
|---|---|---|---|---|---|---|
| `Ah9c5d` | `dynamic.rainbow` | 0.638385 | +0.276769 | 0.000000 / 0.103448 | −0.103448 | 46 / 29 |
| `As9s5d` | `dynamic.two-tone` | 0.610233 | +0.220466 | 0.000000 / 0.103448 | −0.103448 | 46 / 29 |
| `As9s5s` | `dynamic.monochrome` | 0.569199 | +0.138398 | 0.000000 / 0.034483 | −0.034483 | 46 / 29 |

Every number in those three rows -- equity, nut share, and the combos that took part -- equals the third row of `table.03-01.equity-vs-nut-advantage`, which the injector renders as percentages: 61.0233% / 22.0466% / 0.0000% / -10.3448% with combos 46.0 / 29.0. Three values of one formula, not three sources.

Look at the divisor. Villain's nut share on `As9s5d` is `3/29 = 0.103448`, not `6/36 = 0.166667`: the `9s` on the board kills three of the six `99` combos (the numerator), and `98s`'s `9s8s` plus three `55` combos containing `5d` go with it (36 -> 29). The engine no longer lets two denominators be mixed -- hand `nut_advantage` a range that was not narrowed and it refuses:

```
error: nut_advantage: range 0 still holds TsAs, a card on the board. Narrow it with
Range.with_removed(*board) or notation.parse(spec, exclude=board); nut shares and combo
counts divide by what the range contains.
```

(`advantage()` needs no help: it calls `with_removed(*board)` internally.) Numerator and denominator conditioned together are what makes every share in this lesson match the artifact, and they are the door into `03-06`.

Reading it: rainbow to two-tone costs hero `0.276769 − 0.220466 = 0.056303`, i.e. **5.63 percentage points**; two-tone to monochrome costs another **8.21** (0.220466 -> 0.138398). The cause is one fact: a made flush needs the third card of that suit, and the suited combos are distributed unevenly between the two ranges -- after board removal 23 of villain's 29 combos (79.3%) are suited pairs against 10 of hero's 46 (21.7%). The nut tier moves the same way: on two suits the nuts are the three combos of trips nines (3/29 = 0.103448); on three suits they are the single best flush, villain's `KsQs` (1/29 = 0.034483). Note the share gets *smaller*: the nut tier counts ties at the top score, not flushes -- villain holds five flush combos in total (Example 4).

### Example 2 -- opposite labels, near-identical numbers

`PYTHONPATH=src python -c "from pokergto.board import classify, parse_board; print(classify(parse_board('Kh7s3d')).class_id, classify(parse_board('Kd8h3s')).class_id)"` prints `dynamic.rainbow` and `static.rainbow`. On the same two ranges:

| Board | engine label | `max_gap` | hero equity | equity edge | nut edge | `often` / `big` |
|---|---|---|---|---|---|---|
| `Kh7s3d` | dynamic | 6 | 0.638489 | +0.276978 | +0.180000 | hero / hero |
| `Kd8h3s` | static | 5 | 0.640480 | +0.280959 | +0.180000 | hero / hero |

Opposite labels, equity edges `0.003981` apart (**0.40 percentage points**), nut edges identical (hero 0.180000 / villain 0.000000 both, over denominators 50 / 33). This pair is the lesson's central counter-example: **a texture label carries almost no information about the advantage measurement.** Who can bet often and who can bet big follow from what the ranges contain, not from whether the board is called wet or dry.

### Example 3 -- a paired board hands the nuts to the caller

`Kh7s7d` (`static.rainbow.paired`, `max_gap` = 6, `connected` = false because 7 and K are six apart and the two sevens do not count as adjacent): hero equity 0.621990, equity edge +0.243981, but nut shares hero 0.000000 / villain 0.062500, nut edge **−0.062500** (over the post-removal denominators 50 and 32), so `who_can_bet_often = hero` while `who_can_bet_big = villain`. Combo by combo: the best tier in hero's range is two pair `K 7` with an ace kicker, 9 combos (three of `AKo`'s twelve are gone because they contain `Kh`); the best tier in villain's range is trips sevens (`6c7c`, `6h7h` -- `7s` and `7d` are already on the board). Once the board pairs, the tier above two pair exists only on the side holding the fourth seven.

Three things must be said about `is_capped` here. First, the board's reachable ceiling is **four of a kind sevens** (whoever holds `7c7h`, legal in `ALL_COMBOS`), and neither illustrative range contains `77` or `KK`, so both sides are capped. Second, `is_capped` now refuses a range that still contains a board card: hand it the authored range and you get `is_capped: range 0 still holds 7c7s, a card on the board. Narrow it with Range.with_removed(*board) or notation.parse(spec, exclude=board)` -- the engine has made "condition the denominator first" a hard error. Third, pairing the board turns "I have a pair" into everybody's floor (Example 4: hero 50/50, villain 32/32) and pushes the tier that actually discriminates into the corners of the range.

### Example 4 -- how many cards a flush needs

Per-combo hand categories (`best_score` + `category_of`) for the same two ranges:

| Board | suited cards on board | hero flush combos | villain flush combos | hero at least a pair | villain at least a pair |
|---|---|---|---|---|---|
| `As9s5d` | 2 spades | 0 | 0 | 42 / 46 | 9 / 29 |
| `As9s5d2s` | 3 spades | 1 | 5 | 43 / 46 | 14 / 29 |
| `Kh7s3d` | 0 | 0 | 0 | 30 / 50 | 21 / 33 |
| `Kh7s7d` | 0 | 0 | 0 | 50 / 50 | 32 / 32 |

Rows one and two carry the real consequence of the suit axis: **on a two-suit board no flush exists** (2 in hand + 2 on board = 4); the third card of that suit gives villain five flush combos and hero one. The global counts agree: with three of a suit on the board, `C(10,2) = 45` starting combos are made flushes = 3.3937% of 1,326; with two, `C(11,2) = 55` combos hold a flush draw = 4.1478%. Rows three and four carry the rank axis: on an unconnected three-rainbow board, 30 of hero's 50 combos contain a pair; once the board pairs, all 50 do.

`table.01-03.draw-probability-exact-vs-rule` is the next step, turning a draw into a probability: 9 outs improve by the river exactly 34.9676% of the time while the rule of four says 36%, an overstatement of 1.0324 percentage points. There is no shortcut from classification to probability; both steps must be computed.

### Example 5 -- connectedness changes which categories exist

If the turn is `4c`, `classify(parse_board('Kh7s3d4c'))` returns `dynamic.rainbow.connected` (3 and 4 are adjacent). The committed table's fourth row (`table.03-01.equity-vs-nut-advantage`) gives hero equity 76.9775%, equity edge +53.9550%, nut share 7.5000% (that is `3/40`, numerator and denominator both already conditioned) over combos 40 / 44. With this lesson's own two ranges: turn `Kh7s3d4c` gives hero 0.644791, equity edge +0.289582, nut edge +0.180000; turn `Kh7s3dQh` gives 0.704721, +0.409442, +0.068182 (hero's three `QQ` combos make trips queens, over a denominator of 44). The numbers move with the board, the labels move with the rules, and the denominator moves with conditioning -- the one quantity that shifts numerator and divisor at once, which is the whole subject of `03-06`.

## 生成表 / Generated tables

The first table is the source of every advantage number in this lesson. Its `lesson` field says `03-01`: reuse inside the chapter is deliberate -- one table, one set of ranges, one set of numbers, rather than a fifth texture taxonomy invented here.

<!-- BEGIN AUTO:table.03-01.equity-vs-nut-advantage -->
|    Board |                       Hero range |                           Villain range |             Hero |          Villain | Hero equity | Equity edge | Hero nut share |  Nut edge | Who bets often | Who bets big |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
|   Kh7s3d |    AKs,AQs,ATs,KQs,AKo,AQo,99,77 | KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s |        CO opener |        BB caller |    71.5272% |    43.0545% |        6.8182% |   6.8182% |      hero      |     hero     |
|   9h6d3c | AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs |   87s,76s,65s,54s,T8s,T9s,98o,97o,66,55 |       BTN opener |        BB caller |    36.8154% |   -26.3691% |        4.7619% |   4.7619% |    villain     |     hero     |
|   As9s5d |     AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT |           KQs,QJs,KJs,JTs,98s,76s,99,55 |        CO opener |        BB caller |    61.0233% |    22.0466% |        0.0000% | -10.3448% |      hero      |   villain    |
| Kh7s3d4c |         AKo,AQo,ATs,KQs,99,77,44 |         KJs,QJs,JTs,T9s,98s,A5s,KQo,AJo | CO opener (turn) | BB caller (turn) |    76.9775% |    53.9550% |        7.5000% |   7.5000% |      hero      |     hero     |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.theory.range_advantage#advantage`

<!-- generated by: tools/gen_tables.py from pokergto.theory.range_advantage::advantage -->
<!-- END AUTO:table.03-01.equity-vs-nut-advantage -->

The second table converts texture into probability. By out count it gives the exact turn and river improvement rates next to the rule of 2 and rule of 4. What the suit axis adds is not a feeling of "wetness" but the 45 starting combos that become flushes once the third card of the suit lands; and a nine-out hand improves exactly 34.9676% of the time against the rule's 36%.

<!-- BEGIN AUTO:table.01-03.draw-probability-exact-vs-rule -->
| Outs | Exact, next card | Rule of 2 | Exact, two cards | Rule of 4 |
|---:|---:|---:|---:|---:|
|    3 |            6.38% |     6.00% |           12.49% |    12.00% |
|    4 |            8.51% |     8.00% |           16.47% |    16.00% |
|    5 |           10.64% |    10.00% |           20.35% |    20.00% |
|    6 |           12.77% |    12.00% |           24.14% |    24.00% |
|    8 |           17.02% |    16.00% |           31.45% |    32.00% |
|    9 |           19.15% |    18.00% |           34.97% |    36.00% |
|   10 |           21.28% |    20.00% |           38.39% |    40.00% |
|   12 |           25.53% |    24.00% |           44.96% |    48.00% |
|   15 |           31.91% |    30.00% |           54.12% |    60.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.equity#draw_probability`

<!-- generated by: tools/gen_tables.py from pokergto.equity::draw_probability -->
<!-- END AUTO:table.01-03.draw-probability-exact-vs-rule -->

## 实战牌局 / Live hands

### Hand 1 (`hand.03-04-monochrome-river-flush-count`) -- the suit structure moves three numbers, and there is no equity on a river

Six-max cash. CO opens 2.5x, BB calls; pot 12. Flop `As 9s 5d`, turn `2s` (the third spade), river `4h`. Hero (CO) holds `AdKc`: one pair of aces, king kicker.

Two illustrative ranges (hero `AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT`, villain `KQs,QJs,KJs,JTs,98s,76s,99,55`). Villain's side is reduced by the board **and by hero's two cards**, leaving 27 combos. Hero bets 6 into 12:

- The three-spade river `As9s5d2s4h`: of those 27 combos **16 fold and 11 call**. The 11 callers are 5 flushes (`KsQs`, `KsJs`, `QsJs`, `JsTs`, `7s6s`), 3 trips nines and 3 trips fives. Fold frequency **59.2593%**, expected value **+4.6667** per attempt.
- Same ranks, no third card of any suit, `Ad9c5d2h4s` (four suits): **21 fold, 6 call** (only the two trip buckets), fold frequency **77.7778%**, expected value **+8.0000**.
- Here is the point. `classify` gives both boards the **same** id, `dynamic.rainbow.connected`, because `is_rainbow` is "at least three suits" and three spades plus `5d` plus `4h` is already three suits. Identical label, **3.3333 chips** apart per attempt.
- The threshold is the same algebra as always: `PYTHONPATH=src python -m pokergto mdf --pot 12 --bet 6` -> MDF 0.6667, so hero needs 33.3333% of folds. Both boards clear it, so the decision is not made by the label; it is made by those five combos that exist only when three cards share a suit.

Try equity instead of a showdown count and the engine refuses: `PYTHONPATH=src python -m pokergto equity "AdKc" "KQs,QJs,KJs,JTs,98s,76s,99,55" --board "As9s5d2s4c"` -> `error: a board of five cards has no equity left to compute`. After the river there is only a showdown. That is not a limitation to work around: with no further card there is no such quantity as equity.

Reproduce:

```python
from pokergto.cards import parse_cards, Card
from pokergto.notation import parse
from pokergto.evaluator import best_score, describe
board = parse_cards("As9s5d2s4h")          # swap in Ad9c5d2h4s for the no-flush version
hero  = [Card.parse("Ad"), Card.parse("Kc")]
hs = best_score(hero, board)
v = parse("KQs,QJs,KJs,JTs,98s,76s,99,55").with_removed(*board, *hero)
fold = sum(w for a, b, w in v if best_score([a, b], board) < hs)
call = sum(w for a, b, w in v if best_score([a, b], board) > hs)
print(v.total_combos(), fold, call, 100 * fold / v.total_combos(),
      (fold * 12 - call * 6) / v.total_combos(), describe(hs, lang="en"))
```

### Hand 2 (`hand.03-04-paired-vs-connected-size`) -- paired and connected boards change the number of calling combos, which is what makes a size expensive

Same session, a different deal. BB's illustrative range is written `KQs,QJs,JTs,T9s,98s,76s,65s,55` (34 combos). Hero still holds `AcKd`, pot still 12, and villain's combos are again reduced by board and by hero's cards. Two river boards:

| River | `classify` | hero's best hand | villain combos left | folds | calls | folds needed for 6 | for 24 | EV of 6 | EV of 24 |
|---|---|---|---|---|---|---|---|---|---|
| `Kh7s7d4c2s` | `dynamic.rainbow.paired` | two pair `K 7`, ace kicker | 30 | 28 | 2 | 33.3333% | 66.6667% | **+10.8000** | +9.6000 |
| `Kh7s3d4c2s` | `dynamic.rainbow.connected` | one pair `K`, ace kicker | 31 | 27 | 4 | 33.3333% | 66.6667% | +9.6774 | +7.3548 |

Both rows read the same fact: **a bigger size demands a bigger fold frequency, and the board does not change the part of the range that can call.** On the paired board only 2 combos call (`6c7c`, `6h7h`: with `7s7d` on the board the third seven is trips, which beats two pair `K 7`), so moving 6 -> 24 costs 1.2000. On the connected board villain holds 4 straight combos (`65s` makes 7-6-5-4-3), so it costs 2.3226. The overbet loses to the half-pot on both, and the size of the loss equals "calling combos x extra chips / total combos" -- nothing to do with how scary the board looks.

On the same paired board `PYTHONPATH=src python -m pokergto mdf --pot 12 --bet 24` -> MDF 0.3333: villain needs to defend only 10.000 of his 30 combos to meet the floor, and this range contains just 2 combos that beat hero's two pair. The under-defence is not a mistake by villain; the range **has nothing to defend with**. That is what the chart below is about.

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

This chart comes from `04-02` and is borrowed to show a consequence of texture rather than a name for it. It draws the **442 combos a defender must cover facing a double-pot overbet** (`1326 x 1/3`; the artifact records `total_combos = 442.0`, `range_percentage = 33.3333%`, `threshold = 0.33333333`, 57 non-empty cells).

Three ways to read it:

1. The half-pot version (`range.02-03.mdf-floor-vs-half-pot`) demands 884 combos; this one demands 442. **Doubling the size halves the defence obligation**, which is the same arithmetic that made the overbet expensive in Hand 2.
2. These 442 combos are one feasible fill chosen by this repository in strength order. MDF constrains the total only; it does not say which combos may fill it. Whether they exist at all depends on the board: on `Kh7s7d` hero's range contains no trips at all (Example 3), so the nuts that would licence an overbet cannot be produced from it. That is `03-02`'s capping argument, not a property of this picture.
3. The chart carries no removal. The moment a board card kills an ace or a king the corresponding cells lose combos -- `03-05` does this to the opponent's range, `03-06` to your own.

## 为何成立、何时失效 / Why it works, when it breaks

**Why it holds.** The classification predicates read only suits and ranks on the board; the advantage numbers read only combo counts and the seven-card evaluator. Each side is closed under its own definition, so every row here recomputes.

**Where it stops being usable:**

1. **Swap the ranges for real players and it fails.** Every "favours" in this lesson takes as its subject one of two hard-coded illustrative ranges. A real CO range depends on position, sizing and opponent, and this repository has no model of that. Reporting 0.220466 as "the CO's advantage on a two-tone board" would be overreaching; such sentences must stay `reference` / UNVERIFIED.
2. **A nut share must be divided by a conditioned denominator.** `advantage` narrows before taking the top tier, and `nut_advantage` and `is_capped` go further: they raise when handed an un-narrowed range -- `nut_advantage: range 0 still holds TsAs, a card on the board. Narrow it with Range.with_removed(*board) or notation.parse(spec, exclude=board)`. That is why the committed `table.03-01.equity-vs-nut-advantage` and `table.03-02.capped-range-check` carry conditioned counts (3/29 = 10.3448%, combos 40 / 44, and 44 / 58) while `parse(spec).total_combos()` on the same strings returns 54 and 52. Both are true; they answer different questions, and the text says which one it is using.
3. **A five-card board has no equity.** `range_equity` raises `a board of five cards has no equity left to compute`. River comparisons are showdown counts.
4. **`dynamic` is not `wet`.** There is no `is_wet` predicate; `wet-board` and `dry-board` are glossary entries only. The runnable pair is `dynamic` / `static`, defined in the first derivation section. Arguing from "this board is dry" is arguing from a predicate that is not implemented.
5. **Exact enumeration has a budget.** The three `advantage` calls in Example 1 cost roughly 1176 x 90 = about 106,000 evaluations each, affordable with `mode="exact"`. Widen to a real opening range (hundreds of combos) and you hit `BudgetExceeded`; then you must use `mode="mc"` and carry the error bar (`01-04`).

## 陷阱 / Common mistakes

1. **Reading `dynamic` as "wet, therefore bet small".** Measured here: `Kh7s3d` (`dynamic.rainbow`) and `Kd8h3s` (`static.rainbow`) give equity edges of +0.276978 and +0.280959 on the same ranges, **0.40 percentage points** apart, with identical nut edges; and the two boards in Hand 1 carry an **identical** label while their bet expectations differ by 3.3333.
   *Cost*: one size tier wrong. Hand 2 loses 1.2000 on the paired board and 2.3226 on the connected one by moving from half-pot to double-pot. The number that decides is the count of calling combos, not the label. If you want to reason from a label, run the label and the number together.
2. **Counting flush capacity on a two-suit board.** Example 4, first row: on `As9s5d` both ranges hold **0** flush combos (2 in hand + 2 on the board = 4 cards, which is not a flush).
   *Cost*: you credit villain with five flush combos that do not exist yet and point `who_can_bet_big` at the wrong side -- Hand 1's two same-labelled boards are 3.3333 chips apart purely because of those five. A two-tone board gives **draws** (`flush-draw`, `backdoor-draw`); the third suited card gives **made hands**.
3. **Calling equity on the river.** `equity ... --board "As9s5d2s4c"` answers `error: a board of five cards has no equity left to compute`.
   *Cost*: either a sum you cannot finish, or worse, a flop equity used to justify a river decision. On the river only the ordering of `best_score` exists, which is what Hand 1 uses.

## 练习 / Drills

- Print the ids of `Td8s6h`, `KsQs7h`, `8s7s2d`, `Tc9d4h`, `AdKc7s` with `PYTHONPATH=src python -c "from pokergto.board import classify, parse_board; print(classify(parse_board(b)).class_id)"`. Predict `paired` and `connected` before you look. Which `connected` contradicts your intuition, and why does the wheel rule say so?
- Take Example 1's script and swap in `Ah9c5d`, `Ad9h5c`, `Ac9d5h` (all rainbow, suits merely shuffled): which columns stay identical? Then try `Ah9s5d`: from which column does the row start to move?
- Recompute Example 3 with villain's range changed to `KQs,QJs,KJs,JTs,98s,76s,99` (drop `55`). Do the nut share and `who_can_bet_big` move?
- Variant of Hand 2: size 12 into 12 (one pot, needs 50.00% of folds per `table.02-03.mdf-vs-sizing`). Rerun the same script for both boards. Which texture loses more?

## 自测清单 / Self-check

- [ ] I can write the three disjuncts of `dynamic` and produce a textbook-dry board the engine calls dynamic, with the reason (`Kh7s3d`, because the window `[3..7]` holds both 3 and 7).
- [ ] I can run `classify` on any board and explain the order of the words in `class_id`.
- [ ] I remember that `Kh7s3d` and `Kd8h3s` differ by 0.40 percentage points of equity edge, and that this is evidence a label is not a measurement.
- [ ] I can say "zero flush combos" for a two-suit board and "45 starting combos, 3.3937% of 1,326" for a three-suit board.
- [ ] I know a river needs `best_score` rather than `range_equity`, and that a nut share is divided by conditioned combos (3/29 = 0.103448), while an un-narrowed `parse(spec).total_combos()` is the denominator of a different question.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number in this lesson is computed in this repository. No commercial solver output or paid-course chart appears here:

| Content | Source type | Location |
|---|---|---|
| The seven predicates and the `class_id` concatenation | `derived` | `src/pokergto/board.py` (`is_monochrome` ... `classify`); derivation section above |
| Example 1's three advantage rows (0.638385 / 0.610233 / 0.569199) | `derived` | `advantage(parse(H), parse(V), parse_cards(b), mode="exact")`, command in Example 1; the `As9s5d` row equals row 3 of `table.03-01.equity-vs-nut-advantage` |
| Example 1's nut shares (0.103448, 0.034483) and the combos behind them (46 / 29) | `derived` | `advantage(...)`, which calls `with_removed(*board)` internally; same values as row 3 of `table.03-01.equity-vs-nut-advantage`. Passing an un-narrowed range to `nut_advantage` is now an `InputError`, quoted in Example 1 |
| Examples 2, 3 and 5 | `derived` | same call, boards `Kh7s3d`, `Kd8h3s`, `Kh7s7d`, `Kh7s3d4c`, `Kh7s3dQh`; Example 3's ceiling comes from `pokergto.theory.range_advantage#is_capped` maximised over `ALL_COMBOS`; `is_capped` requires a range already narrowed with `with_removed` and raises otherwise |
| Example 4's category counts and the 45 / 55 | `derived` | `best_score` + `category_of` per combo; `math.comb(10,2)`, `math.comb(11,2)` against 1,326 |
| Hand 1's 16/11, 21/6, +4.6667, +8.0000 | `derived` (showdown counts) | the Python block in the text, `with_removed(*board, *hero)` |
| Thresholds in both hands (33.3333%, 66.6667%, MDF 0.6667 / 0.3333) | `derived` | `PYTHONPATH=src python -m pokergto mdf --pot 12 --bet 6` and `--bet 24` |
| Hand 2's four expectations (+10.8000, +9.6000, +9.6774, +7.3548) | `derived` | same script, sizes 6 and 24, villain range reduced by board and hero's cards |
| The two ranges (hero / villain spec strings) | `reference` | illustrative inputs authored for the lesson, as `table.03-01`'s own `provenance.assumptions` states |

<!-- provenance: kind=reference verified=false -->
!!! unverified "UNVERIFIED"
    Claims such as "this texture favours a certain type of player", "a real CO range's frequency on a two-tone board", and "the opponent defends differently because of this texture" are opponent models. Nothing in this repository computes them, so they appear nowhere in this lesson as numbers. The path that would make them derived runs through `src/pokergto/solver` (solve the spot) and `tools/run_solver.py` (emit an artifact carrying `solver_run`); until then every such sentence must be labelled UNVERIFIED.

## 术语 / Terms

<!-- terms: board-texture, monochrome-board, two-tone-board, rainbow-board, paired-board, connected-board, static-board, dynamic-board, wet-board, dry-board, broadway-board, backdoor-draw, flush-draw, range-advantage, equity-advantage, nut-advantage, capacity, range, combos -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 牌面质地 | board texture | the classification on three axes -- not a measurement |
| — | 单色牌面 | monochrome board | `len({suit}) == 1`; flushes may already exist |
| — | 双色牌面 | two-tone board | `len({suit}) == 2`; a flush is **not yet** possible |
| — | 彩虹牌面 | rainbow board | `len({suit}) >= 3` -- which a three-spade river also satisfies |
| — | 成对牌面 | paired board | `len({rank}) < len(board)`; everyone holds at least a pair |
| — | 连张牌面 | connected board | two adjacent board ranks differ by 1 (the wheel counts) |
| — | 宽面 / 干面 | wet board / dry board | speech labels; no predicate exists, only the two below |
| — | 动态牌面 | dynamic board | `connected or (flush_draw and not monochrome) or straight_draw` |
| — | 静态牌面 | static board | `dynamic` is false |
| — | 成牌容量 | capacity | how many combos of a category a range holds: Example 4's table |
| — | 坚果优势 | nut advantage | difference of nut-tier shares; decides who can bet big |
| — | 胜率优势 | equity advantage | difference of equities; decides who can bet often |
