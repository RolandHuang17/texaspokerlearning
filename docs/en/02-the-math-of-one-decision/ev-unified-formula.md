# One notation for every action: call, bet, raise and shove

<!-- hands: 2 -->
<!-- terms: expected-value, ev-decomposition, fold-equity, call, bet, raise, check, shove, regret, equity -->

## 本节目标 / Objectives

- Write the expectation of *any* postflop action from one template, and see call, check, bet, raise and shove as special cases of it rather than five separate formulas.
- Explain why money you already put in the pot never appears in the formula, and quantify what it costs when you forget that convention.
- Compute several candidate actions side by side with the engine, and say what regret is and why it is the number the trainer reports.

## 前置知识 / Prerequisites

- `02-01` Break-even percentage; `02-05` fold equity (its template is this lesson's subject).
- `01-03` The definition of equity, `e = P(赢) + ½·P(tie)`.

## 核心原理 / The principle

There is one formula:

```
EV(bet) = f·P + (1 − f)·(e·(P + 2B) − B)
```

The symbols follow the convention stated in `pokergto/ev.py`: `P` is the money in the middle **before** the actor adds anything, `B` is what the actor adds, `f` is the probability that every opponent folds, and `e` is hero's equity once the money is in.

The convention matters as much as the formula, and it is a single rule: **folding is zero.** Money already committed is lost in both branches, so it cancels out of every difference and must never appear. The repository writes that zero as an explicit function returning `0.0` (`ev_fold`) not for tidiness but because learners who never state the reference point double-count their own prior money -- the most common arithmetic error in self-taught hand review.

## 推导 / Derivation

Five actions, one formula.

**Fold (`ev_fold`)**: zero by definition; the baseline for every comparison below.

**Call (`ev_call`)**: `f = 0`, because nobody folds to your call. The template collapses to

```
EV(call) = e·(P + 2B) − B
```

That is the `02-02` statement "the final pot is `P + 2B` and you pay `B`", and setting it to zero gives the equity needed to call, `B/(P+2B)`. Check: `P = 10, B = 5, e = 0.541414` → `5.82828`, identical to `ev_bet(10, 5, 0, e)`.

**Check (`ev_check`)**: `B = 0`, and a check cannot chase anyone away, so the fold branch does not exist. What is left is a free showdown:

```
EV(check) = e·P
```

**Bet (`ev_bet`)**: the template as written. The branch weights still sum to one, `f + (1 − f) = 1`, which is what makes it an expectation at all.

**Shove (`ev_shove`)**: the template with `B` = the rest of your stack. The engine keeps a separate entry point because short-stack tournament play is exactly the case where `B` is not a free variable; numerically the two are the same action: `ev_bet(12, 15, 0.4, e)` and `ev_shove(12, 15, e, 0.6)` both return `9.443633`.

**Raise**: the only action needing work, and it does not change the formula -- only the values substituted for `P` and `B`. Let the pot be `P`, the opponent bet `B₀`, and you raise to `R`.

- When he folds you win `P + B₀`, including the bet he just made.
- When he calls he tops up `R − B₀`, so the final pot is `P + 2R` and your committed amount is `R`.

Written straight from those two facts:

```
EV(raise to R) = f·(P + B₀) + (1 − f)·(e·(P + 2R) − R)
```

And it is still the same template, because a raise is "call `B₀`, then bet the rest into a pot that is already matched":

```
P₁ = P + 2B₀,   B₁ = R − B₀,   EV = ev_bet(P₁, B₁, f, e) − B₀
```

The trailing `− B₀` moves the reference point from "I have already called" back to "I have not acted yet". Run it with `P = 10, B₀ = 5, R = 20, f = 0.3, e = 0.541414`:

| Route | Result |
|---|---|
| Definition written directly | `9.44949` |
| Template at `P₁ = 20, B₁ = 15`, minus `B₀` | `9.44949` |
| The lazy version: `ev_bet(10, 20, 0.3, e)` | `7.94949` |

The third line is wrong because it assumes you win only `10` when he folds, dropping the `5` he just put in on that street. The error is exactly `f·B₀ = 0.3 × 5 = 1.5`. **A raise is never a new formula; it is the same formula with different arguments.**

## 直觉 / Intuition

The feeling that "different situations need different formulas" comes from notation, not from the game. Only two things ever happen on a street: the opponents fold, or they do not and the money goes in. Actions differ only in which of those two quantities is known and which you must estimate:

- Call: no fold branch, only the showdown branch.
- Bet: both branches.
- Raise: both branches, and the fold branch is fatter by the bet you are facing.
- Shove: identical to a bet, except `B` is fixed by your stack.
- Check: the lower bound `B = 0`.

A good test of any formula you suspect is "special": it should reduce to the template at some value of `f` or `B`. If it cannot, the notation is fooling you.

Comparing actions needs only their differences because every action shares the same zero: in `EV(A) − EV(B)` everything that does not depend on the action -- old money, chop handling -- cancels. That is why the trainer can say "you left 1.62 pot shares on the table", and why regret exists as a quantity at all.

## 算例 / Worked examples

Shared inputs: flop `8d6d2s`, pot 12, hero `AdKd`, villain `QsQh`. Equity is enumerated by the engine, not assumed:

```
PYTHONPATH=src python -m pokergto equity "AdKd" "QsQh" --board "8d6d2s" --mode exact --json
→ "equity": 0.541414, "iterations": 990, "exact": true
```

`iterations` is 990 rather than 1081 because both hands are known, which deletes 91 possible turn-river deals (`01-04` separates those two counts).

**Example 1 -- four actions side by side.** Fold `0`; check `e·P = 6.4970`; call a one-third-pot bet `e·(12+8) − 4 = 6.8283`; bets in Example 2.

**Example 2 -- three sizes, with `f` taken from "the defender plays MDF".** The fold rate is then not an invented estimate but the consequence of `1 − MDF`, i.e. `required_fold_frequency(12, B)`.

| Action | `B` | `f = B/(P+B)` | `EV` | Regret |
|---|---|---|---|---|
| bet pot | 12 | 0.500000 | 9.7455 | 0 |
| bet half pot | 6 | 0.333333 | 8.6626 | 1.0828 |
| bet one third pot | 4 | 0.250000 | 8.1212 | 1.6242 |
| check | 0 | none | 6.4970 | 3.2485 |

Reproduce with `PYTHONPATH=src python -c "from pokergto import ev, odds; e=__import__('fractions').Fraction('0.541414'); rows=ev.compare(12,[('check',0),('bet 1/3',4),('bet 1/2',6),('bet pot',12)],fold_frequencies={a:odds.required_fold_frequency(12,b) for a,b in [('bet 1/3',4),('bet 1/2',6),('bet pot',12)]}|{'check':0},equities_when_called={'check':e,'bet 1/3':e,'bet 1/2':e,'bet pot':e}); print([(r.action,round(r.ev,4)) for r in rows]); print(ev.regret(rows))"`

**Example 3 -- same inputs, one assumption changed: equity when called falls as size rises.** A bigger size is called by a stronger range, so take `e = 0.541414 / 0.48 / 0.35` (check keeps `0.541414`):

| Action | `EV` | Regret |
|---|---|---|
| bet one third pot | 8.1212 | 0 |
| bet half pot | 7.6800 | 0.4412 |
| check | 6.4970 | 1.6242 |
| bet pot | 6.3000 | 1.8212 |

The ranking inverts completely. The template did not change, the code did not change, and the only thing that moved was an **input**. That is the lesson to keep: the engine does not decide `e` for you; it computes whatever you declare.

**Example 4 -- the raise by two roads (`P = 10, B₀ = 5, R = 20, f = 0.3`)**: `9.44949` from the definition and `9.44949` from the substitution; the lazy `ev_bet(10, 20, 0.3, e)` gives `7.94949`.

## 生成表 / Generated tables

The continue branch is already embedded in the `02-02` table: the equity needed to call, `B/(P+2B)`, is precisely the solution of `e·(P+2B) − B = 0`.

<!-- BEGIN AUTO:table.02-02.equity-needed-to-call -->
|   Bet (x pot) | Equity needed |
|---:|---:|
|     0.25x pot |        16.67% |
| 0.333333x pot |        20.00% |
|      0.5x pot |        25.00% |
| 0.666667x pot |        28.57% |
|     0.75x pot |        30.00% |
|        1x pot |        33.33% |
|      1.5x pot |        37.50% |
|        2x pot |        40.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#equity_needed_to_call`

<!-- generated by: tools/gen_tables.py from pokergto.odds::equity_needed_to_call -->
<!-- END AUTO:table.02-02.equity-needed-to-call -->

The fold branch needs `f`, which the "fold frequency a bluff needs" column supplies as `1 − MDF`:

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

Read together the two tables *are* the template: one gives the threshold once you are called, the other gives how much folding you must buy.

## 实战牌局 / Live hands

**Hand 1 (`hand.02-06-flop-size-choice`) -- six-max, BTN versus CO, flop `8d6d2s`, pot 12, hero `AdKd`.**

- Equity `0.541414` from the command above, so this is not a "feel like raising" spot: it is a comparison of four candidates.
- Under "defender plays MDF" plus "equity when called does not vary by size", the pot-sized bet is best, choosing one third pot costs `1.6242` chips of regret, and checking costs `3.2485`.
- Put the realistic input back -- equity when called falls with size (Example 3) -- and one third pot becomes best while the pot-sized bet becomes worst, regret `1.8212`.
- So what this lesson can hand you is not "which size", but something harder: **your sizing conclusion is only as strong as your inputs.** Chapter 03 (range and nut advantage) and chapter 04 (size sets) are in the business of producing those inputs; this lesson only guarantees that once you have them you will not miscompute.
- Where that leaves the decision here: before choosing a size, ask whether you can say how `e` moves with it. If you cannot, use the smallest meaningful size, because that is the choice that keeps your regret bounded.

**Hand 2 (`hand.02-06-raise-not-new-formula`) -- turn, pot 10, opponent bets 5, you raise to 20.**

- Straight from the definition: `0.3 × 15 + 0.7 × (e·50 − 20)` with `e = 0.541414` → `9.44949`.
- Through the template with `P₁ = 10 + 2×5 = 20`, `B₁ = 15`: `ev_bet(20, 15, 0.3, e) − 5` → `9.44949`. The two routes must agree; when they do not, a symbol was substituted wrong.
- The common shortcut is `ev_bet(10, 20, 0.3, e)`, giving `7.94949`. It pretends you win only `10` when he folds and forgets the `5` already in this street; the gap is exactly `f·B₀ = 1.5`.
- That 1.5 is a measured sample of what mishandling prior money costs. When a raise line's expectation disagrees with your intuition, check this term first.

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

The chart is still the defense quota (`threshold = 0.66666667`, 884 of 1,326 combos continue). What has changed is its job: it is where the template's first term gets its value. The 442 combos that are *not* on the chart are your `f`. In other words the picture gives you neither action nor verdict, only the price of the fold branch.

One thing stated plainly: the chart this lesson actually wants -- expectation per action as a surface over `f` and `e` -- has no artifact yet. Producing it means exporting `pokergto.ev.compare` into a new table artifact in `tools/gen_tables.py`, with its own `provenance` block in `data/schema`. That is part of the chapter 09 trainer work; until it exists this lesson uses commands and real numbers in its place.

## 为何成立、何时失效 / Why it works, when it breaks

**What holds it up**: one decision point on one street, chips linear in utility, `e` genuinely the share you realise once money is in, and the two branches mutually exclusive and exhaustive.

**Where it weakens or breaks**:

1. **`e` is not a constant.** Different sizes are called by different ranges (Example 3). The template still computes; it simply will not warn you. This lesson declares that as an input, not a conclusion.
2. **The opponent has more than two actions.** With a raise available, the continue branch forks again and the template is applied one level deeper -- same formula, one more layer. `02-08` and chapter 06 (check-raise lines) do that.
3. **More than one street.** The template prices one street. A flop bet also buys the option to barrel the turn, which needs a game tree chaining several templates (chapter 08), not one line of algebra.
4. **Non-linear utility (tournaments).** Swap `EV` for ICM value and the shape survives while every amount changes (chapter 12).
5. **Chops.** `e` includes half the pot, so board-runout ties and `AA`-into-`AA` require both branches to be adjusted.
6. **Regret is only comparable inside one table.** `ev.regret(rows)` measures "how much this action earns below the best action in this list". Subtracting regrets from two tables with different premises turns an assumption into a number, which is the worst misuse of this lesson.

## 陷阱 / Common mistakes

1. **Counting money you already put in as part of the payoff.** Pot money is gone in both branches and must not appear.
   *Cost*: Hand 2 loses 1.5 chips by dropping the opponent's street bet; the mirror error -- crediting your own old money -- drifts further and never raises an error, it just makes reviews feel right while the arithmetic is wrong.
2. **One formula per action.** A check formula here, a call formula there, a raise formula elsewhere, each with its own private baseline.
   *Cost*: the same hand yields contradictory conclusions in two places and you settle it by mood. Run all candidates through `ev.compare`: they automatically share one `P` and one zero.
3. **Recording regret as if it were a loss.** Regret is a difference inside one candidate set; it is not "loss versus optimal play" and it is not bb/100.
   *Cost*: summing regrets across different candidate sets produces figures such as "I lost three pots in that hand" that no table can check. Fix the candidate set and the premises before comparing across hands.
4. **Changing the formula but not the assumption.** Example 3's inversion shows that debating size while refusing to say how `e` moves with size is debating a model that does not exist.
   *Cost*: chapter 04's sizing discussion degrades into memorised sizes, which fail on the first new board texture.

## 练习 / Drills

- Write down, using only the template: fold; call 5 into 15; check; bet 6 into 12; raise to 20 facing a bet of 5; shove 25 into 15. Then verify each reduces from the template at some `f = 0` or `B = 0`.
- Run Example 2's inputs yourself through `ev.compare`; set every `f` to 0 and see which action becomes worst.
- With `e = 0.30`, `P = 12` and the three sizes, repeat Example 3 and find the `f` at which pot and one-third pot tie.
- Change Hand 2 to `R = 15` instead of `20`, compute by both routes, and confirm they still agree.
- Compute `ev_shove(12, 15, e, 0.6)` and `ev_bet(12, 15, 0.4, e)`; showing they are equal is the smallest proof that a shove is a special case.

## 自测清单 / Self-check

- [ ] I can write the template from memory and state the convention behind each of the four symbols.
- [ ] I can express call, check and shove as special cases, naming whether I substitute `f = 0`, `B = 0` or `B = stack`.
- [ ] I can derive the raise substitution and explain where the trailing `− B₀` comes from.
- [ ] I can explain why comparing actions requires only comparing differences.
- [ ] I can reproduce Example 3: same formula, changed input, inverted conclusion.

## 来源与置信度 / Provenance and confidence

Every number here is computed in this repository. No expectation table from a commercial solver or paid course is used anywhere in this lesson.

| Content | Source type | Location / reproduce with |
|---|---|---|
| Template and its five special cases | `derived` | `src/pokergto/ev.py#ev_bet`, `#ev_call`, `#ev_check`, `#ev_shove`, `#ev_fold` |
| Raise substitution and the `− B₀` correction | `derived` | Derivation above; both routes return `9.44949` |
| `e = 0.541414` (990 enumerated runouts) | `derived` | `poker equity "AdKd" "QsQh" --board "8d6d2s" --mode exact --json` |
| Examples 2 and 3 expectations and regrets | `derived` | `pokergto.ev.compare` + `pokergto.ev.regret` (command under Example 2) |
| Equity-needed and fold-frequency columns | `derived` | `data/gen/tables/table.02-02.equity-needed-to-call.json`, `table.02-03.mdf-vs-sizing.json` |
| The `e = 0.48 / 0.35` pair in Example 3 | `reference` + **UNVERIFIED** | Declared sensitivity inputs, not an output of any opponent model; verification path: per-size calling ranges in `data/src/spots/*.yaml`, then `poker equity` |
| The "defender plays MDF" premise | consequence of a `derived` premise | `pokergto.odds#required_fold_frequency`; whether real players hold the line is chapter 13 and unverified |
| Action-expectation surface chart | no artifact yet | a new builder in `tools/gen_tables.py` plus its schema `provenance`; tracked in ROADMAP.md |

## 术语 / Terms

<!-- terms: expected-value, ev-decomposition, fold-equity, call, bet, raise, check, shove, regret, equity -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| EV | 期望值 | expected value | the template's output, measured against fold = 0 |
| — | 期望值分解 | EV decomposition | splitting an action into fold branch and called branch |
| — | 弃牌赢率 | fold equity | the first term, `f·P` |
| — | 胜率 | equity | `e`, the share you realise once money is in |
| — | 遗憾值 | regret | best-in-table minus this action, `ev.regret` |
| — | 全下 | shove | a bet with `B` = remaining stack, not a new formula |
