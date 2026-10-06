# Exact equity by enumeration: turning outs into per-street probabilities

<!-- hands: 2 -->
<!-- terms: equity, win-probability, outs, rule-of-two-and-four, tie-chop, showdown, flop, turn, river, runout, board, monte-carlo-simulation, combos -->

## 本节目标 / Objectives

- From the number of cards already known, compute how many runouts remain on any street, and state precisely when `1176 / 1081 / 990` each apply.
- Derive draw probabilities in closed form with binomial coefficients -- no simulation -- and give the rule of 2 and 4 an error column with a sign.
- Explain where exact equity differs from "the probability of winning" (a chop is worth half).
- Estimate what an enumeration costs, and know at what size the engine refuses to run it.

## 前置知识 / Prerequisites

- `01-01` combos and 1326: the weights an enumeration averages over are still combos.
- `01-02` removal: the fewer cards known, the bigger the remaining deck.
- `00-02` derivation before memory: every number in this lesson is followed by the command that produced it.

## 核心原理 / The principle

**Exact equity = enumerate every possible runout, score each one with the same seven-card evaluator, count a win as 1, a chop as 1/2, a loss as 0, and average under the combo weights.**

```
equity = (wins + ties/2) / (wins + ties + losses)
```

The cost is a single product:

```
cost ~= number of runouts x (hero combos + villain combos)
```

and the runout count depends only on how many cards are already known: `52 - known` cards left, `5 - |board|` still to come, so

```
runouts = C(52 - known, 5 - |board|)
```

In `pokergto.equity.EquityResult` the identity `equity == wins + ties/2` is an **assertion**, not a convention: violating it raises `AssertionError`. That assertion is the mechanical version of "equity is not win probability".

## 推导 / Derivation

**Runout counts. Every row below was measured by calling `runout_boards`, not looked up.**

| What is known | Known cards | Cards to come | Runouts | Measured |
|---|---|---|---|---|
| flop board only | 3 | 2 | `C(49,2)` | 1176 |
| flop + your hole cards | 5 | 2 | `C(47,2)` | 1081 |
| flop + both hole-card sets | 7 | 2 | `C(45,2)` | 990 |
| turn + both hole-card sets | 8 | 1 | `C(44,1)` | 44 |
| preflop, nothing known | 0 | 5 | `C(52,5)` | 2,598,960 |
| preflop, both hands known | 4 | 5 | `C(48,5)` | 1,712,304 |

**The three "flop" numbers must be kept apart.** `1081` is the future space when **you know the board and your own hand** -- the denominator of every `9/47` draw calculation lives in this row (`47 = 52 - 3 - 2`). `990` is the space when **both hands are on the table**, which is what exact hand-vs-hand equity enumerates. `1176` is the space when **only the board is known**: for a range vs range the engine cannot know which two cards you will hold, so it enumerates every 2-card completion of the 49 non-board cards and, runout by runout, masks the combos that use a board card. Confusing these three rows puts the wrong denominator under any draw lesson.

**Draw probability in closed form.** With `u` unseen cards of which `o` improve you:

- improving on the next card: `o/u`. Nine outs, `u = 47` -> `9/47 = 19.1489%`.
- improving over two cards (turn and river): `1 - C(u-o, 2)/C(u, 2)`. `1 - C(38,2)/C(47,2) = 1 - 703/1081 = 34.9676%`.

**Where the rule of 2 and 4 comes from.** Approximate the denominator 47 as 50 and `o/u` becomes `2o%` -- so it always **understates** (the true denominator is smaller). For two cards, adding the two `2o%` terms gives `4o%`, which counts "hits twice" a second time and therefore **overstates** when the outs are many; when the outs are few, the terms the shortcut drops are the larger ones and it flips to **understating**. The generated table's 6-out row is the evidence: exact 24.14% versus rule 24% -- the rule is **low** by 0.15 points; from 7 outs up, the rule runs high.

## 直觉 / Intuition

Enumeration is not brute force, it is **laying every future board on the table and counting**. 990 river futures compared hand by hand costs a couple of thousand evaluations -- trivial. The problem is ranges: replace 990 by 1176 and 2 hands by 1326 combos and you are instantly in the millions.

Three anchors to carry around:

- flop, one hand vs one hand: **990** runouts -- sub-second, always use exact.
- preflop, one hand vs one hand: **1,712,304** runouts -- minutes, worth paying once for a textbook number (that is how the 88.19% below was produced).
- preflop, range vs range: tens of millions of evaluations and up; the engine refuses. That refusal is `01-04`'s reason for existing.

## 算例 / Worked examples

**Example 1 -- exact preflop: `AhAs` vs `7d2s`.** 1,712,304 runouts, fully enumerated:

```
equity 88.1937%   wins 87.9938%   ties 0.3998%   losses 11.6064%
```

```bash
PYTHONPATH=src python -m pokergto equity AhAs 7d2s --mode exact --json
```

Look at that `ties` row: 0.4%. AA versus 72 offsuit does get chopped (the board itself makes a straight, flush or boat). **"AA has 88% equity" is a share of the pot including chops; the probability of winning is 87.99%.** Two tenths of a point, and at an all-in boundary it is the half pot you are supposed to collect.

**Example 2 -- three famous preflop numbers, each recomputed here.**

| Matchup | Exact equity | Wins | Ties |
|---|---|---|---|
| `KsQh` vs `AcAd` | 13.6519% | 13.4882% | 0.3273% |
| `AhKh` vs `QdJs` | 66.6408% | 66.4187% | 0.4441% |
| `Td9d` vs `AcKc` | 38.7187% | 38.4852% | 0.4670% |

Commands: `equity KsQh AcAd --mode exact`, `equity AhKh QdJs --mode exact`, `equity Td9d AcKc --mode exact`. Note `Td9d` vs `AcKc` is **38.72%**, while folklore rounds it to "about 40%": those 1.3 points are enough to change the sign at a call/fold boundary.
The same matchup sampled instead of enumerated, `equity KsQh AcAd --mode mc --iterations 20000 --seed 7`, returns 13.69% +/- 0.48pp -- inside the bar of the exact 13.6519%, which is the least you should demand of a simulation.

**Example 3 -- exact on the flop, 990 runouts.** `JhTh` vs `AcKc`, board `Kh7h2d`:

```
equity 39.4949%   wins 39.4949%   ties 0.0%
```

```bash
PYTHONPATH=src python -m pokergto equity JhTh AcKc --board "Kh7h2d" --mode exact
```

Hero has nine heart outs plus a gutshot needing a queen, and `Qh` belongs to both sets; `ties` is exactly zero because this board texture cannot produce the same hand for both players.

**Example 4 -- outs must not be added.** Board `9h8h2s`, hero `JhTh`:

```python
from pokergto.equity import outs_from_enumeration
outs_from_enumeration(hero, board, improve_to="FLUSH")     # 9 cards
outs_from_enumeration(hero, board, improve_to="STRAIGHT")  # 15 cards (a flush also qualifies)
```

The union is still **15**: the genuine straight cards are only `7c 7d 7s Qc Qd Qs` -- six -- and the other nine are hearts (`7h` sits in both sets). The spoken version "flush 9 + straight 8 = 17 outs" is wrong twice: **`Th` is in hero's hand, so there are not four tens**, and `7h` was counted twice. Follow the wrong number through: 17 outs over two cards is `1 - C(30,2)/C(47,2) = 59.76%`, while the true 15 outs give `54.12%` -- **5.6 points of inflation**, enough to turn a fold into a donation.

## 生成表 / Generated tables

The first table is computed by `pokergto.equity.draw_probability`, exact values side by side with the rule of 2 and 4 (the generator keeps its own error columns): `tools/gen_tables.py` -> `data/gen/tables/table.01-03.draw-probability-exact-vs-rule.json`.

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

The same combinatorial machinery asked a different question gives the five-card category counts. That table belongs to `01-05` and is borrowed here because it is **the cheapest full enumeration in the repository**: run this repository's own `evaluate5` over all `C(52,5) = 2,598,960` hands, and the nine category counts must sum to 2,598,960. If they do not, the evaluator is wrong -- not the counting.

<!-- BEGIN AUTO:table.01-05.hand-class-counts -->
|        Category |            Hands | Probability |
|---:|---:|---:|
|  straight flush |      40.00 hands |     0.0015% |
|  four of a kind |     624.00 hands |     0.0240% |
|      full house |    3744.00 hands |     0.1441% |
|           flush |    5108.00 hands |     0.1965% |
|        straight |   10200.00 hands |     0.3925% |
| three of a kind |   54912.00 hands |     2.1128% |
|        two pair |  123552.00 hands |     4.7539% |
|        one pair | 1098240.00 hands |    42.2569% |
|       high card | 1302540.00 hands |    50.1177% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.evaluator#evaluate5`

<!-- generated by: tools/gen_tables.py from pokergto.evaluator::evaluate5 -->
<!-- END AUTO:table.01-05.hand-class-counts -->

## 实战牌局 / Live hands

**Hand 1 (`hand.01-03-flop-allin-exact`) -- heads up, flop `Kh7h2d`, pot 100. Hero holds `JhTh` facing BTN's 100-chip shove.**

- Equity needed: calling 100 to win 300 -> `100/(100+200) = 33.33%` (`02-02`'s `B/(P+2B)`).
- Equity held: **39.4949%**, enumerated over 990 runouts, no error bar.
- Margin +6.2 points -> **call**. No approximation, no "roughly four in ten": one hand against one hand on a flop is always affordable exactly.
- Check the cost formula: `990 x (1 + 1) = 1,980` evaluations -- two orders of magnitude below the `mode="auto"` threshold `AUTO_EXACT_BUDGET = 250,000`, so even the automatic switch picks exact.

**Hand 2 (`hand.01-03-range-too-wide-for-exact`) -- preflop. BTN opens 2.5x, BB 3-bets to 9x, hero (BTN) holds `AQo` and must call 6.5x.**

- The threshold `6.5/18.5 = 35.14%`, same as `01-01` Hand 2.
- Try to enumerate `AQo` (12 combos) versus `QQ+,AKs` (22 combos) preflop: the runout space is `C(52,5) = 2,598,960` and the cost is `2,598,960 x (12 + 22) = 88,364,640` evaluations, over the hard limit `EXACT_EVAL_BUDGET = 4,000,000`, so `mode="exact"` raises `BudgetExceeded` and prints the runout count, the combo count and the alternative in its message.
- Only two exits: shrink the question until exact is affordable (a flop, one hand each), or simulate and accept an error bar (`01-04`). Demo of the second: `equity "AQo" --range-villain "QQ+,AKs" --mode mc --iterations 20000 --seed 4 --json` -> **23.88% +/- 0.59pp**, below 35.14%, fold.
- Honest label: how much to trust that line depends entirely on the bar and the seed -- see `01-04`. Treating it as an exact answer is the mistake this lesson exists to prevent.

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

The committed chart above supplies a real range for this lesson: `02-03`'s MDF floor, 884 combos, against the complementary 442 combos it folds. Put both on the flop `Kh7h2d` and enumeration is affordable:

```
defense range vs fold range, board Kh7h2d, mode=exact
equity 55.92% (wins 55.2%, ties 1.5%), 1176 runouts x 1326 combos ~= 1.56M evaluations
```

That run took about 41 seconds on this machine. **Note it used `1176`, not `990`**: in a range matchup the engine does not know which four hole cards will be dealt, so it enumerates every 2-card completion of the 49 non-board cards and masks the illegal combos -- precisely the third row of the derivation table. With that number, `02-03`'s floor line acquires a meaning in equity: the two thirds of the space filled in strength order hold 55.92% of the pot against the third it discards, on a two-heart flop.

## 为何成立、何时失效 / Why it works, when it breaks

**Premises**: the evaluator is correct (the nine counts summing to 2,598,960 is the strongest available check on it), the deal distribution is correct (every runout equally weighted, combo weights from `01-01`), and a chop is worth half. All three live in code, not in verbal convention.

**When not to enumerate:**

1. **Cost.** Once `runouts x combos` reaches the tens of millions the engine refuses (Hand 2). Do not route around that guard; it is a designed rail (`adr/0001`).
2. **Wrong denominator.** Using `1081` to describe a hand-vs-hand enumeration (really 990), or `990` to describe "board only" (really 1176), produces an equity that no reproducible run will confirm.
3. **Equity is not money.** Exact enumeration gives a share, not realisation. A dominated hand (`KsQh` at 13.65%) is hard to play because it wins small and loses a whole range (`01-06`).
4. **The module's prose disagrees with its code.** The docstring of `src/pokergto/equity.py` calls `C(47,2) = 1081` the space "when only the board is known", while `runout_boards(board)` measures `C(49,2) = 1176`; `1081` is really "board plus your own hand". This lesson states the three measured rows and records the wording mismatch below as **UNVERIFIED**: closing it takes a comment fix or a test, not a change to this text.

## 陷阱 / Common mistakes

1. **Treating `1081 / 990 / 1176` as one number.**
   *Cost*: every "how many futures are left" conversion is off by 9-19%, and draw probability is built on exactly that denominator. Print `len(runout_boards(...))` once instead of memorising three numbers.
2. **Reading equity as win probability.** AA vs 72o's 88.19% contains 0.40% of chops; `KsQh` vs `AcAd`'s 13.65% contains 0.33%.
   *Cost*: booking half a pot as zero in an all-in EV. `EquityResult` asserts the decomposition for the engine; nothing asserts it for your mental arithmetic.
3. **Adding outs across draw types.** Example 4: 15 real outs recited as 17.
   *Cost*: 5.6 points of inflated river probability, i.e. calling a shove you should fold. Let `outs_from_enumeration` hand you the sets and take the union yourself.
4. **Believing the rule of 4 always overstates.** At 6 outs and below it **understates** (24% versus 24.14%).
   *Cost*: treating "the shortcut keeps me safe" as a cushion, then calling small-outs draws that were never priced right. The table's error column exists to make this row visible.

## 练习 / Drills

- Without looking anything up, derive the runout count for: turn with both hands known, river, and flop with only the board known. Then check with `len(runout_boards(...))` (44 / 1 / 1176).
- Use the closed form for 8, 10 and 12 outs over two cards, compare against the generated table, and state the rule-of-4 error sign for each.
- Run `equity AhAs 7d2s --mode exact --json` and point at the difference between `equity` and `wins` (that is `ties/2`). Then run `equity Td9d AcKc --mode exact` and do the same.
- Cost drill: how many evaluations does an exact flop enumeration of `"22+,ATs+"` (114 combos) against `"88+,AQs+"` (86 combos) need, and which mode should you use? (Hint: `1176 x` the combo total, and compare with the two budget constants.)

## 自测清单 / Self-check

- [ ] I can say which known-card configuration each of `1176 / 1081 / 990 / 44 / 1,712,304 / 2,598,960` belongs to.
- [ ] I can derive 34.97% from `1 - C(38,2)/C(47,2)` and explain why the rule of 4 overstates at 9 outs but understates at 6.
- [ ] I can state the difference between exact equity and win probability using AA vs 72o's 0.40% of chops.
- [ ] I can estimate an enumeration's cost and name the threshold at which the engine refuses.
- [ ] I can explain why the range-vs-range flop figure (55.92%) used 1176 and not 990.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every equity here was computed in this repository. No commercial solver, paid course or third-party equity chart is used:

| Content | Source type | Location |
|---|---|---|
| Runout counts (1176 / 1081 / 990 / 44 / 1,712,304 / 2,598,960) | `derived` | measured lengths from `src/pokergto/equity.py#runout_boards`, cross-checked against `math.comb` |
| Exact preflop equities (88.1937 / 13.6519 / 66.6408 / 38.7187) | `derived` | `equity <hero> <villain> --mode exact --json`, four runs, 1,712,304 runouts each |
| Exact flop equity (39.4949%) | `derived` | `equity JhTh AcKc --board "Kh7h2d" --mode exact`; independently re-enumerated the 990 runouts with a separate script and got the same number |
| Defense range vs fold range (55.92%) | `derived` | `range_equity(from_chart, complement, "Kh7h2d", mode="exact")`, 1176 x 1326 evaluations, ~41 s |
| Draw probabilities and rule-of-2/4 errors | `derived` | `data/gen/tables/table.01-03.draw-probability-exact-vs-rule.json` |
| Five-card category counts | `derived` | `data/gen/tables/table.01-05.hand-class-counts.json` (`evaluate5` over `C(52,5)`) |
| Outs sets (9 and 15 cards) | `derived` | `src/pokergto/equity.py#outs_from_enumeration` |
| Hand 2's 23.88% +/- 0.59pp | `derived`, **Monte Carlo** | `equity "AQo" --range-villain "QQ+,AKs" --mode mc --iterations 20000 --seed 4 --json` |
| `equity.py`'s docstring calling 1081 "board only" | **UNVERIFIED / 未核验** | disagrees with the measured 1176 from `runout_boards`; closed by fixing the comment or adding an assertion test, not by editing this lesson |

## 术语 / Terms

<!-- terms: equity, win-probability, outs, rule-of-two-and-four, tie-chop, showdown, flop, turn, river, runout, board, monte-carlo-simulation, combos -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 胜率 | equity | share of the pot including chops: `wins + ties/2` |
| — | 纯赢率 | win probability | `wins` alone, one half-chop away from the row above |
| — | 补牌 | outs | the cards that upgrade your hand; take the union |
| — | 二四法则 | rule of two and four | an approximation whose error changes sign |
| — | 平分底池 | chop | counted as half, never as zero |
| — | 发展牌序 | runout | the object being enumerated; its count follows from known cards |
| — | 蒙特卡洛模拟 | Monte Carlo simulation | the fallback when exact is unaffordable; see `01-04` |
