# The seven-card evaluator: hand classification and kicker tie-breaks

<!-- hands: 2 -->
<!-- terms: hand-ranking, hand-strength, kicker, showdown, tie-chop, flush, straight, trips, full-house, equity, board, hole-cards -->

## 本节目标 / Objectives

- Explain why "who won this hand" collapses into one integer comparison in this codebase, and how the bit layout of that integer was chosen.
- Separate the **definition** (the best five of seven cards) from the **optimisation** (the code that evaluates seven cards directly), and name the evidence this repository uses to prove the optimisation does not change the answer.
- Retell A-5-4-3-2, the wheel, as a concrete bug: what goes wrong, what it reports, and how a test pins it.
- Explain why ties force a tie term into equity, and show that term coming out of the engine.

## 前置知识 / Prerequisites

- `01-01` Combos: the 1,326 hole-card combos, the 169 hand classes, and why "class" and "combo" are not the same unit.
- `00-01` Vocabulary: hole cards, board, street.

## 核心原理 / The principle

The evaluator does not score, it **orders**. `pokergto.evaluator.evaluate5` packs five cards into one integer:

```
score = category << 20 | t1 << 16 | t2 << 12 | t3 << 8 | t4 << 4 | t5
```

`category` runs 0..8 (high card 0, straight flush 8); the five tiebreak slots take four bits each, which is enough for a rank because the largest rank, the ace at 14, is below 16. Therefore:

```
a > b   ⟺   a beats b
a == b  ⟺   a genuine tie (the pot is chopped)
```

No tuple comparison, no special case at the call site. Two measured integers: the wheel `Ac5d4h3s2c` = 4521984 and, in the same category, the king-high straight `KdQhJsTc9d` = 5046272. The category bits are identical (both 4); the difference sits in the top slot, 5 against 13.

> !!! note "Provenance"
>     Bit layout and wheel handling: `src/pokergto/evaluator.py`, pinned clause by clause by `tests/test_evaluator.py`. Count table: `tools/gen_tables.py` -> `data/gen/tables/table.01-05.hand-class-counts.json`.

## 推导 / Derivation

**Step one: the definition is one sentence.** From seven cards choose five, which is `C(7,5) = 21` choices, and take the best five-card score. That code exists in this repository: `evaluate7_reference`. It is slow, and it is the rulebook.

**Step two: an optimisation has to be proved, not read.** `evaluate7` takes another route: find a suit holding at least five cards (a straight flush can only come from there), then quads, then a full house, then flush, then straight, then the pairs and finally high card. Faster, and therefore more dangerous: a bug that only misses double trips, or a wheel straight flush, does not fail anywhere an eye can see. The cost being saved is real: one preflop matchup has `C(48,5) = 1,712,304` boards (the four known hole cards are removed from the runout pool), two evaluations per board, so 3,424,608 evaluations; done by the definition that is `3,424,608 × 21 = 71,916,768` five-card evaluations. Measured in one process on the author's laptop (2026-10-07) over the same 20,000 random seven-card hands:

| implementation | hands/s | microseconds per call | extrapolated over one preflop matchup |
|---|---|---|---|
| `evaluate7_reference` -- the definition, one hand at a time | 3,212 | 311.36 | 17.8 min |
| `evaluate7` -- the direct algorithm, one hand at a time | 51,507 | 19.41 | 66 s |
| `evaluate7_many_reference` -- the definition, in a vector | 40,325 | 24.80 | 85 s |
| `evaluate7_many` -- the direct algorithm, in a vector | 331,714 | 3.01 | 10 s (17.3 s measured end to end) |

Read the middle two rows together, because they are the lesson inside the lesson: **vectorising the
definition lost to the scalar algorithm**, 24.80 microseconds against 19.41. Twenty-one sub-hands divided
by a 17x batch speed-up is about a wash, so the only honest way to make seven-card evaluation fast in a
vector is to duplicate the *algorithm* -- which is precisely the thing this step warns you not to trust.
`evaluate7_many_reference` exists so that duplication has something to be measured against, in the same
relationship `evaluate7` has to `evaluate7_reference`, and the duplicate must return the **same integers**,
not merely the same ranking: committed tables store those integers.

The duplicate did break, and only an exhaustive sweep saw it. On five cards a wheel cannot coexist with a
higher run; on seven, `A-2-3-4-5-6-7` contains both, and the first version scored it five-high. No category
changed, so every count-based assertion in the file stayed green. What caught it was comparing every hand of
five structurally chosen subdecks -- 9.6 million seven-card hands -- against the definition, and
`test_batch_seven_card_finds_the_higher_run_when_a_wheel_is_also_present` below is what keeps it caught.

So the wall that pushes exact enumeration into Monte Carlo is no longer one preflop matchup: 17.3 s is a
price worth paying once, and `EXACT_EVAL_BUDGET = 4,000,000` evaluations admits it. The wall is the
*matrix*. 14,365 class pairs at these rates is hundreds of hours, which is what `adr/0006` measured when it
retracted the promise that preflop could simply be enumerated exactly.

**Step three: what this repository proves it with.** Five independent routes, all of them run in CI:

1. A deliberately naive oracle, `tests/reference_evaluator.py` -- tuples, rulebook order, **no code shared with `src/pokergto/evaluator.py`**.
2. Full enumeration: all `C(52,5) = 2,598,960` five-card hands, checked both for category counts and hand-by-hand agreement with the oracle (`pytest -m slow`).
3. The fast seven-card path against the best-of-21 definition: 20,000 random boards at each of the arities 5, 6 and 7, with the seeds written as `20260 + size`.
4. Random seven-card hands against the naive best-of-21: 4,000 hands, seed 4242.
5. The vectorised paths against the scalar ones, element by element and as the *same integers*: all
   `C(52,5) = 2,598,960` five-card hands (`pytest -m slow`), every hand of five structurally chosen
   subdecks, 9.6 million seven-card hands against `evaluate7_many_reference`, and a throughput floor in
   `tools/cost_probe.py` that runs on every build -- because a speed-up nobody guards is a speed-up that
   quietly leaves.

**Step four: a second independent route -- closed-form counts.** Each of the nine numbers the enumeration produces is pure combinatorics (verified in this repository against the enumeration; `math.comb` is enough to redo it by hand):

| Category | Closed form | Value |
|---|---|---|
| straight flush | 4 x 10 straight spans | 40 |
| four of a kind | 13 x 48 | 624 |
| full house | 13 x 12 x C(4,3) x C(4,2) | 3,744 |
| flush | 4 x (C(13,5) - 10) | 5,108 |
| straight | 10 x (4^5 - 4) | 10,200 |
| three of a kind | 13 x C(4,3) x C(12,2) x 4^2 | 54,912 |
| two pair | C(13,2) x C(4,2)^2 x 44 | 123,552 |
| one pair | 13 x C(4,2) x C(12,3) x 4^3 | 1,098,240 |
| high card | (C(13,5) - 10) x (4^5 - 4) | 1,302,540 |

The nine values sum to 2,598,960 = C(52,5) and match the enumeration row by row. **The flush count is 5,108 rather than 4 x 1,287 = 5,148** because the missing 40 are straight flushes: they got moved out of "flush". The straight count is 10 x 1,020, and 1,020 = 4^5 - 4: five chosen ranks in any suits, minus the four monochrome cases.

**Step five: ties are structural, not a corner case.** Run all 2,598,960 hands and count distinct integers: only **7,462** of them, an average of 348.293 hands per integer, and **not one integer belongs to a single hand**. The largest same-score family is 1,020 hands -- precisely every six-high straight there is. The reason is in the design: suits never enter the integer, because hold'em never ranks them. Equal scores therefore happen constantly, which is why `EquityResult` carries a tie term and asserts `equity == wins + ties/2` at construction.

## 直觉 / Intuition

Picture the integer as a nine-storey building: the floor is the category, and each floor has five drawers holding card ranks. Comparing two hands means comparing floors first, then drawers -- which is exactly what your eyes do at showdown, compressed into one `>`.

The wheel is the one place where a drawer and a card disagree about size: there the ace is not the boss, it is a 1, so A-5-4-3-2 is a **five**-high straight, not Broadway. Every evaluator eventually misses this mirror rule, because it is the only ace that needs special treatment.

Chopping is not luck. It is the necessary consequence of one floor and one identical drawer sequence, and it means suits cannot decide money.

## 算例 / Worked examples

**Example 1 -- the wheel's two integers.** `evaluate5("Ac5d4h3s2c")` = 4521984, and `describe()` returns `straight 5` -- it ends in 5, not in A. `evaluate5("KdQhJsTc9d")` = 5046272 > 4521984. Those are the two assertions in `test_wheel_scores_as_high_five_not_broadway`.

**Example 2 -- how two sets of trips become one full house.** `AcAdAsKhKdQc9h` contains trips of aces and trips of kings. The rule is: the higher set is the trips, the lower becomes the pair. The code needs no extra branch, because `ordered` is already sorted by (count, rank). Output: `full house A K`.

**Example 3 -- the six-card path gets walked too.** With six cards `evaluate7` goes through `C(6,5) = 6` sub-hands, a branch the seven-card tests never touch. Three assertions from the test file: `Ac5d4h3s2cKh` is a straight (the extra king changes nothing), `Ac5c4c3cKcQc` is a flush, and `Ac5c4c3c2cKc` is a **wheel straight flush** -- the same ace-mirror rule, at a different arity.

**Example 4 -- the tie is computed, not assumed.** `showdown(2d3c, 4d5c, AcKdQhJsTh) = 0`. On the turn board `AcKdQhJs`, the equity of those two hands (`equity "2d3c" "4d5c" --board "AcKdQhJs"`, all 44 rivers, exact) is **13.64% win / 72.73% tie / 13.64% lose**. The reason is checkable: only a river that pairs one of your own hole cards (a 2 or a 3, three of each still unseen) beats the board; the other 32 rivers leave both hands playing the board, and the money splits.

**Example 5 -- outs are not two disjoint sets.** `JhTh` on `9h8h3s`: nine cards to a flush, eight to a straight, and the memorised answer is "17 outs". `outs_from_enumeration(..., improve_to="STRAIGHT")`, which counts the cards whose category reaches at least a straight, returns **15** (`2h3h4h5h6h7c7d7h7sQcQdQhQsKhAh`) because `7h` and `Qh` belong to both sets and were each counted twice. 15/47 = 31.91% against 17/47 = 36.17%: two phantom outs inflate your next card by 4.26 percentage points.

## 生成表 / Generated tables

The full enumeration, produced by `pokergto.evaluator.evaluate5`, agreeing row by row with the closed forms above:

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

**Hand 1 (`hand.01-05-wheel-nuts`) -- 6-max cash. Flop `5d4c3h`. Hero `Ah2s`, villain `KdQh`.**

`python -m pokergto equity "Ah2s" "KdQh" --board "5d4c3h"`: 990 runouts (a flop with both hands known, enumerated exactly), **98.13% equity, made of 96.26% pure wins and 3.74% chops, and 0.00% losses**.

- What the evaluator did here: `best_score(Ah2s, 5d4c3h)` = `straight 5`. If the code treated the ace only as high, this hand would be reported as `high card A` and the nuts would be counted as air; if it reported the wheel as Broadway, it would overcharge boards where a real king-high straight exists. Both errors change numbers and neither raises an exception.
- Why "0.00% losses" is a fact and not luck: the flop holds no pair, and no five-card runout can build a better hand than hero's without also handing him a share; at worst the board becomes its own straight (a runout of `6s7c` makes a seven-high straight on the board and `showdown` returns 0).
- The consequence is about money, not about leading: everything left to decide is how to get paid.

**Hand 2 (`hand.01-05-split-river`) -- turn `AcKdQhJs`. Hero `2d3c`, villain `4d5c`.**

Forty-four rivers, and the evaluator hands down win, chop or lose for every one of them (Example 4). Before the river you know only this: the equity is 50%, but it is **not** a coin flip -- it is "13.64% take it all, 72.73% split, 13.64% nothing". Same expectation, different variance shape. Any tool that reports one aggregate number and no decomposition will mislead you here, which is why `EquityResult` refuses to build unless `wins + ties/2` equals the equity it reports.

## 范围图 / Range chart

No grid is embedded in this lesson, and the reason is worth stating. The evaluator produces **verdicts** -- an ordered integer -- and allocates no combos and defines no range. The grid is a range notation; how to read it is `01-07`, and the only range-chart artifact generated in this repository today is `range.02-03.mdf-floor-vs-half-pot`, embedded in `02-03`. Confusing the verdict tool for the range tool is where questions like "can the evaluator tell me whether to call?" come from. It cannot. It answers one thing: if the money goes in, who gets how much.

## 为何成立、何时失效 / Why it works, when it breaks

**What makes it hold:** hold'em's rule really is "choose five of seven"; suits are unordered; ranks 2..14 fit in four bits; the nine categories fit above them. Given all four, one integer comparison is a complete showdown.

**Where it stops:**

1. **Arity is a hard constraint.** `evaluate5` takes exactly five cards, `evaluate7` takes 5, 6 or 7, and `best_score` wants exactly two hole cards plus three to five board cards. Eight cards is a `ValueError`, not "best five of eight".
2. **No side pots.** `split_pot` answers "who shares the top score", not "who receives how much when three players are all-in at different levels". Side-pot allocation is not implemented here, so any claim about side-pot amounts is **UNVERIFIED** and needs a money model outside `evaluator`.
3. **Suits cannot break a tie.** That is the rule, not a defect -- but it means any game that needs a suit ordering (some lowball variants, odd-chip awards) cannot reuse this integer.
4. **A wheel straight flush is not a royal flush.** `describe` says royal only for an ace-high straight flush; the five-high one is `straight flush 5`. Deliberate: do not "fix" it.
5. **The closed forms stop at five cards.** They count five-card hands. Seven-card category counts need inclusion-exclusion redone from scratch; you cannot multiply by 21.
6. **Every ratio in the table is a hardware number.** This run put the definition-to-algorithm ratio at 16.04x and vectorising the algorithm at 6.44x; an earlier run on the same machine read 15.57x and 6.8x, and another machine will differ again. The parts of this that are portable and therefore quotable are `AUTO_EXACT_BUDGET = 250_000`, `EXACT_EVAL_BUDGET = 4_000_000` (both in evaluations) and the 100,000-hands-per-second floor `tools/cost_probe.py` enforces.

## 陷阱 / Common mistakes

1. **Reading the wheel as Broadway.** Treat the ace only as 14 and `A-5-4-3-2` becomes either "high card A" or a king-high straight.
   *Cost*: the 98.13% of `Ah2s` on `5d4c3h` turns into a number that is entirely wrong, and it goes wrong on the easiest board class to compute, so the result never looks suspicious. The check is the test's own assertion: `describe(...)` must end in 5.
2. **Believing "same category" means "I win".** Suits never enter the score, so equal scores chop.
   *Cost*: `AcKd` against `AdKh` -- the same AKo class, two suits apart -- enumerates to **1.09% pure wins, 97.09% chops, 1.82% losses**, 49.63% equity. Pricing that as "half the time I take it all" mistakes 97.09% of the branches for something they are not.
3. **Adding outs as if the sets were disjoint.** Example 5: 17 becomes 15, and the next card drops from 36.17% to 31.91%.
   *Cost*: a 4.26-point self-inflation, quite enough to turn a call into a donation. Count with `outs_from_enumeration` before deciding.
4. **Trusting optimised code because it reads correctly.** Every branch of the direct seven-card path exists to handle a rare shape: double trips, six cards, the wheel straight flush.
   *Cost*: the bug never appears in the hands you test by hand. The repository's answer is to keep the oracle in `tests/` so production code cannot depend on it, then run the full enumeration over it.

## 练习 / Drills

- Derive 5,108 = 4 x (C(13,5) - 10) and 1,302,540 = 1,277 x 1,020 by hand, and explain why the two "minus 4" are the same object.
- Run `PYTHONPATH=src python -m pytest tests/test_evaluator.py -m slow -q`, note how long the full enumeration takes on your machine, and record your own ratio against the reference path.
- Verify with `equity "Ah7c" "As7d" --board "KdQc3s"` that two hands of the same class in different suits report exactly 50% equity with ties = 100% and wins = 0%. Then explain why no runout lets either hand take it all.
- List the cards that raise `Td9c` on `Ah8h6s` to at least a straight (answer: four, `7c7d7h7s`), then ask why "at least three of a kind" returns the same four cards.
- State the board-card requirements of `best_score`, and why three boards must be accepted.

## 自测清单 / Self-check

- [ ] I can write the bit layout of the score and say why four bits per slot suffice.
- [ ] I can separate the definition (best of 21) from the optimisation (direct seven cards) and list the four independent proofs this repository runs.
- [ ] I can give the wheel's integer and say where it differs from a king-high straight's.
- [ ] I can explain why 2,598,960 hands map to only 7,462 integers, and what that has to do with equity's tie term.
- [ ] I can name two things the evaluator does not model: side pots and suit tie-breaks.

## 来源与置信度 / Provenance and confidence

Every number here is computed in this repository. No range chart or strategy output from a commercial solver or paid course appears anywhere in this lesson:

| Content | Source type | Location |
|---|---|---|
| Integer layout, wheel handling | `derived` | `src/pokergto/evaluator.py#evaluate5`, `#_straight_high_from`; test `tests/test_evaluator.py#test_wheel_scores_as_high_five_not_broadway` |
| Nine category counts | `derived` | `data/gen/tables/table.01-05.hand-class-counts.json`; independent closed forms above |
| The best-of-21 definition itself | `derived` | `src/pokergto/evaluator.py#evaluate7_reference` (oracle in `tests/reference_evaluator.py`, deliberately sharing no code with `src/`) |
| Equity decompositions (98.13 / 13.64 / 72.73 / 97.09 ...) | `derived` | `python -m pokergto equity`, `exact=True`, `iterations` of 990 / 44 / 1,712,304 |
| The per-call table (3,212 / 51,507 / 40,325 / 331,714 hands/s) and its extrapolations | measured here, **UNVERIFIED** as a portable figure | it changes per machine; rerun the same timing script. The portable part is the throughput floor in `tools/cost_probe.py` |
| Side pots, suit tie-breaks | out of model | need a money model; `split_pot` only reports who shares the top score |

## 术语 / Terms

<!-- terms: hand-ranking, hand-strength, kicker, showdown, tie-chop, flush, straight, trips, full-house, equity, board, hole-cards -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 牌型等级 | hand-ranking | the total order of nine categories, packed into the high bits |
| — | 牌力 | hand-strength | an ordering of integers, not a feeling about a hand |
| — | 踢脚 | kicker | the slots compared in order once the category matches |
| — | 平分底池 | chop | the necessary result of equal scores; equity's tie term |
| — | 摊牌 | showdown | the only question the evaluator answers |
| — | 胜率 | equity | `wins + ties/2`, not "how often I win" |
| — | 顺子 | straight | includes the wheel: A-5-4-3-2 is five-high |
| — | 同花 | flush | the category that had 40 hands moved out of it |
| — | 公共牌面 | board | three to five cards, the second argument of `best_score` |
| — | 底牌 | hole-cards | exactly two, always |
