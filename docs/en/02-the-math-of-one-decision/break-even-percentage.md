# Break-even percentage: the risk a call takes against the reward it buys

<!-- hands: 2 -->
<!-- terms: expected-value, break-even-percentage, pot-odds, required-equity, pot, bet, call, fold, raise, bluff, shove, overfold -->

## 本节目标 / Objectives

- Write the break-even expression for any gamble as `risk/(risk + reward)`, and say exactly which pile of money `risk` and `reward` measure **at the moment of the decision**.
- Apply that one formula to four actions -- call, bluff, bluff three-bet, shove -- and state what the "success" event is in each.
- Point at the two directions in which "the reward is the pot you win" gets mis-measured, quantify each by how many percentage points it moves the bar, and say which one produces over-folding and which one over-calling.

## 前置知识 / Prerequisites

- `00-02` GTO and expected value (EV): why a long-run average is the only verifiable unit.
- `01-07` The 13x13 grid: combo weighting versus class weighting. Every percentage in this lesson has to stand on that distinction first.

## 核心原理 / The principle

A gamble with two outcomes: succeed and you net `reward`, fail and you net `−risk`. To not lose money it needs

```
break-even = risk / (risk + reward)
```

In the engine this is `pokergto.odds.break_even_percentage(risk, reward)`, which computes over `Fraction` and only converts at the last step. That matters: a teaching repository that prints `1/3` as `0.33` and then calls the result "derived" is committing the exact sin it claims to replace.

There is one formula and four actions; what changes is the **definition of success**:

| Action | risk (new money put in now) | reward (net money won on success) | "success" means |
|---|---|---|---|
| call | `B` | `P + B` -- the pot facing you | your showdown share clears it |
| bluff | `B` | `P` -- the pot before the bet | everyone folds |
| bluff three-bet | the amount added by the raise | the pot facing you before the raise | the opener folds |
| shove | everything still behind | branch-dependent: fold or call | computed twice |

> !!! note "Provenance"
>     Derivation: the next section. Functions: `src/pokergto/odds.py#break_even_percentage`, `#equity_needed_to_call`, `#required_fold_frequency`, `src/pokergto/spr.py#all_in_equity_needed`. Generated tables: `tools/gen_tables.py` -> `data/gen/tables/table.02-02.equity-needed-to-call.json`, `table.03-07.spr-commitment.json`.

## 推导 / Derivation

**Line one: the formula itself.** Let `p` be the success probability:

```
EV = p·reward − (1 − p)·risk = 0
p·reward + p·risk = risk
p = risk / (risk + reward)
```

Three lines, no other premise. It does not require knowing poker; it requires "two outcomes". That last clause bites in the failure section: as soon as a third outcome exists (a chop), `p` has to be a **share**, not "the chance of winning".

**Line two: the call.** At the decision point the pot facing you is `F = P + B` (`P` before the bet, `B` the money the opponent just added). Calling adds `B`, so the final pot is `F + B = P + 2B`. Therefore

```
risk = B,  reward = F = P + B
break-even = B / (B + P + B) = B / (P + 2B)
```

which is exactly `equity_needed_to_call`. The two functions return the same number on the same input, and that identity is worth using as a self-check: `break_even_percentage(2.17, 6.5 + 2.17)` and `equity_needed_to_call(6.5, 2.17)` both produce `0.200184501845…`, i.e. **20.02%**.

**Line three: the bluff.** You bet `B` into `P`. Success (everyone folds) nets `P`; failure nets `−B`.

```
break-even = B / (B + P) = required_fold_frequency
```

At `P = 6, B = 2` (one third pot) that is `1/4` = **25.00%** of folds; at `P = 13, B = 6.5` (half pot) it is **33.33%**. The reward is `P`, not `P + B`: when your bluff wins, the money you just bet comes back to you, and getting your own money back is not a win. **That is the only difference between the two directions of this formula** -- when you call, the opponent's money is in the pot (reward `= P + B`); when you bet, your money is.

**Line four: the bluff three-bet.** BTN opens 2.5 and you are in the big blind with 1 already posted, so the pot facing you is 3.5. You make it 8, which is **7 new** chips, not 8: that posted blind is already in the middle, so it is not your risk now -- it is part of what you can win.

```
break-even = 7 / (7 + 3.5) = 66.67%
```

This 66.67% is a required *fold frequency*. It is not the same kind of object as the 25.00% share needed to call a half-pot bet in line two -- one constrains how often people fold, the other how much of the pot you must own. `02-03` makes that boundary its main subject.

**Line five: the shove.** Pot facing you `F = 6`, stack behind `S = 10`. The same formula, twice, with different success events:

```
folds-only branch:   break-even = S / (S + F) = 10/16 = 62.50%   ← folds required
when called:         e ≥ S / (F + 2S) = 10/26 = 38.46%           ← showdown share required
```

The second expression is `all_in_equity_needed(pot=6, stack=10)`, and it equals the SPR form `SPR/(1 + 2·SPR)`: `python -m pokergto spr --stack 10 --pot 6` gives SPR 1.667 and 0.3846. Three notations of one fact, each pinning the others.

**Line six: whose money is whose -- one test only.** Looking forward from the decision point:

- **The money you add now is `risk`.**
- **The pot you take when you succeed is `reward`.** It contains everything the opponents put in, *and* the dead chips you contributed earlier on -- those chips are no longer in your stack, so they belong to "what gets won".
- **The money you add now is never part of `reward`.** When you win, it returns to you. That is reimbursement, not profit.

Break that test twice and you get the two opposite leaks self-taught players actually run: counting already-dead money as risk again (the bar inflates, and you **over-fold**), or counting the money you are about to add as reward (the bar deflates, and you **over-call and over-bluff**). Both deviations are computed in the next section.

## 直觉 / Intuition

A break-even percentage is not the answer to "should I call?"; it is a **bar**. Share above it: call. Share below it: fold. Everything else -- outs, position, how tight the opponent is -- belongs to the other side of the inequality, "what is my share", not to this formula.

One sentence to carry: **a gamble risking 1 to win 4 needs one success in five.** A one third pot bet gives the caller 1 to win 4 (the pot facing him is four times the money he must add), so the bar is 20%; the same bettor, bluffing, risks 1 to win 3, so he needs 25% of folds. Same size, two numbers, and the only thing that differs is whose money is already in the middle.

## 算例 / Worked examples

**Example 1 -- small: a one third pot on the flop, `P = 6, B = 2`.**

```
call needs:      2/(6+4) = 1/5 = 20.00%
bluff needs:     2/(6+2) = 1/4 = 25.00% of folds
defense floor:   MDF = 6/8 = 3/4 = 75.00%   (that is 02-03; here only as a contrast)
```

Three numbers answering three different questions: how much share this hand needs, how many folds this air needs, how much of the whole range must continue. All three come out of `risk/(risk+reward)`; what differs is whose money sits in which pile.

**Example 2 -- medium: a half pot on the turn, `P = 13, B = 6.5`.** The call bar is **25.00%**. A flush draw here: one card `9/47 = 19.1489%`, two cards **34.9676%** (`draw_probability(9, 47, 1)` and `(9, 47, 2)`, exact). So the verdict lives entirely in "how many cards do you still get": on the turn (the river still comes) 34.97% > 25.00% clears the bar; on the river there are no outs left to reason with. If you insist on counting only one card on the turn, the future money required to break even is

```
6.5 / 0.191489 − (13 + 13) = 7.94 chips
```

Feeding `implied_odds_break_even_equity(13, 6.5, 7.9444)` returns 19.1489% -- the exact statement of implied odds, and the subject of `02-02`: that 7.94 is an **assumption**, not a computation.

**Example 3 -- large: shoving 10 into a pot facing you of 6.** The fold branch needs **62.50%** of folds; the called branch needs **38.46%** of the pot. One hand, one formula, two bars -- one measured in frequencies, one in shares. Players who mix them are simultaneously too loose and too tight on the same board.

**Example 4 -- solving backwards for a size.** Pot 8, and you want a bluff that only needs the opponent to fold 60%. Solve `B/(8+B) = 0.6` → `B = 12`, i.e. one and a half times pot. The inverse is unique at every size, which is the other half of `02-03`'s line that sizing and defense are two sides of one equation.

## 生成表 / Generated tables

The call bar across the sizing ladder, computed by `pokergto.odds.equity_needed_to_call` with `pot = 1`:

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

The same algebra on the stack-depth side (`pokergto.spr.spr_commitment_table`):

<!-- BEGIN AUTO:table.03-07.spr-commitment -->
|  SPR | Equity to commit |
|---:|---:|
| 0.25 |           16.67% |
|  0.5 |           25.00% |
|    1 |           33.33% |
|  1.5 |           37.50% |
|    2 |           40.00% |
|    3 |           42.86% |
|    4 |           44.44% |
|    6 |           46.15% |
|   13 |           48.15% |
|   20 |           48.78% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.spr#all_in_equity_needed_from_spr`

<!-- generated by: tools/gen_tables.py from pokergto.spr::spr_commitment_table -->
<!-- END AUTO:table.03-07.spr-commitment -->

Both tables are one formula read twice: in the first, `reward` is the pot facing you after the bet; in the second, `reward` is the pot plus the whole remaining stack, which is why its axis is SPR -- SPR is what fixes the price at which money can close.

## 实战牌局 / Live hands

**Hand 1 (`hand.02-01-turn-flushdraw`) -- turn, pot 13, villain bets 6.5 (half pot), you hold a flush draw with nine outs and nothing else.**

Bar: `6.5/(13+13) = 25.00%`. Your share: one card **19.1489%**, two cards **34.9676%**.

- On the turn (the river still comes): 34.97% > 25.00%, so call. **The break-even number decides this on its own**; no read is involved.
- On the river the cards are dealt: "outs" is no longer a quantity, and only a showdown share can be compared with a bar. The reasoning changes kind, not just size.
- If someone says "one card is enough, I might win another 8 chips": that is precisely the 7.94 assumption of Example 2. Inverting it takes one second with `break_even_percentage`; whether those 7.94 chips actually arrive is **not computed here and is marked UNVERIFIED**.

**Hand 2 (`hand.02-01-overfold-check`) -- flop `Kh7s3d`, pot 6.5, villain bets 2.17, you are in the big blind (you already posted 1) holding the class `J9s`.**

Correct bar: `2.17/(6.5 + 4.34) = 20.02%`. What you actually hold, enumerated exactly over 1,176 runouts: `python -m pokergto equity "J9s" --range-villain "88+,ATs+" --board "Kh7s3d"` -> **20.16%**. 20.16% > 20.02%, so call, by 0.15 of a percentage point.

Now commit the common mistake: count the posted blind as risk again, so `risk = 3.17` and `reward = 8.67`, and `break_even_percentage(3.17, 8.67)` gives **26.77%**. The bar jumps from 20.02% to 26.77% and the hand becomes a fold. **The extra 6.75 points are not judgement, they are double entry.** Run the mistake in the other direction -- put the money you must call into the reward (`reward = 10.84`) -- and the bar falls to **16.68%**, so you call with a stack of hands that are losing, and never notice, because reimbursement felt like profit.

## 范围图 / Range chart

No grid here, and the reason is a units issue. A break-even percentage is a bar for **one hand against one number** (share ≥ bar). A 13x13 grid shows **which classes are included, and how much of them**. The only place the two meet is `02-03`, where the bar becomes a combo-weighted quota for the whole range (`MDF = P/(P+B)`). To read any grid correctly, go back to `01-07`: the cell-value distribution there, the band thresholds, and the line "884.0 combos = 66.67% of all 1,326" are the ground under every later frequency discussion. What this lesson can add is one sentence: **decide whether your percentage is a share, a fold frequency, or a range frequency -- then talk about break-even.**

## 为何成立、何时失效 / Why it works, when it breaks

**Premises:** two outcomes only; the money closes on this action (no further decision after it); no third outcome (no chop); risk neutrality (chips are linear in money); no rake.

**How it fails, and what happens when it does:**

1. **A chop exists.** Then `p` must be a **share** (`wins + ties/2`), not "the chance of taking it all". From `01-05`: `AcKd` versus `AdKh` holds 49.63% share of which only 1.09% are outright wins. Someone who reads "break even at 20%" as "I need a 20% chance of winning the whole pot" is pricing an event that barely occurs.
2. **More streets remain.** `risk = B` holds only when this is the last money you will have to put in. Call now and you may face three quarters pot on the river; the real risk is larger than `B` and the bar is systematically too low. The proper treatment is `02-02` (implied odds) and the betting-line material in chapter 06.
3. **Rake.** Cash pots are taxed, so the reward is smaller than the face value. This repository has no rake model (the glossary files `rake` under `07-04`), so any "after rake the bar becomes X%" statement is **UNVERIFIED** here until there is a rake convention plus a per-hand EV decomposition.
4. **Tournaments.** Chips are not money; risk neutrality fails (ICM, chapter 12). The same 25.00% bar can imply a different action on the bubble.
5. **Multiway pots.** A bluff must beat several defenders at once. The reward is still `P`, but "everyone folds" is no longer a heads-up frequency; `07-01` handles that dimension with `d = 1 − (B/(P+B))^(1/N)`.

## 陷阱 / Common mistakes

1. **Counting the chips you already put in as risk.** `risk = B + your dead money` moves the bar from 20.02% to **26.77%** at `P = 6.5, B = 2.17`.
   *Cost*: this is the arithmetic engine behind over-folding in self-taught players (`overfold`). It reliably pushes the whole 20-27% share band from "call" to "fold", and Hand 2 is exactly the kind of hand it eats (`J9s` at 20.16%).
2. **Counting the money you must add now as part of the reward.** `reward = P + 2B` drops the bar to **16.68%**.
   *Cost*: the mirror leak, and just as expensive. You call one third pot with 17-20% shares, and because reimbursement was counted as profit the result never looks wrong.
3. **Comparing a win probability against a share bar.** Ignoring the chop term.
   *Cost*: the 49.63% share of `AcKd`/`AdKh` reads as 1.09% and you treat yourself as air; on draws you instead undervalue yourself, because the chop branches get swallowed. Always read the `[W.../T...]` decomposition that `equity` prints.
4. **Reading "my bluff needs 25% folds" as "this bluff gets 25% folds".** `B/(P+B)` is a requirement, not an estimate.
   *Cost*: the actual fold frequency has to come from a stated sample or a stated strategy model (chapter 13 for the population side). Any "this opponent folds 40% of the time" is **UNVERIFIED** here unless the source and the verification method are written down.

## 练习 / Drills

- From memory, the call bar and the bluff bar for `1/4, 1/3, 1/2, 2/3, 3/4, 1, 2` times pot; check with `python -m pokergto odds --pot 1` (read the "Equity to call" column, and take the complement of the MDF column for the bluff bar).
- Pot 10, 15 behind you: what fold frequency does a shove need, and what share does it need when called? Why is the second smaller than the first? (`python -m pokergto spr --stack 15 --pot 10`)
- Inverse: at `P = 8`, what size needs exactly 60% folds? (Answer 12, i.e. 1.5 times pot -- Example 4.)
- Write out both mis-measurements (`risk = B + dead money`, `reward = P + 2B`), compute how many points each moves the bar, and name the leak each one produces.
- Say which pile of money `reward` refers to in three actions: call, bluff, shove-called.

## 自测清单 / Self-check

- [ ] I can derive `risk/(risk+reward)` from `EV = 0` in two lines.
- [ ] For the four actions I can state what `risk` and `reward` measure and what counts as success.
- [ ] I can show that `B/(P+2B)` and `break_even_percentage(B, P+B)` are one equation, and give the exact fractions at `P = 6, B = 2`.
- [ ] I can quantify both double-entry mistakes in percentage points and name the direction each pushes you.
- [ ] I can list the settings where break-even stops being the target to execute (chops, later streets, rake, ICM, multiway).

## 来源与置信度 / Provenance and confidence

Every number here is computed in this repository. No range chart or strategy output from a commercial solver or paid course appears anywhere in this lesson:

| Content | Source type | Location |
|---|---|---|
| The break-even formula and both mis-measurements (20.02 / 26.77 / 16.68) | `derived` | `src/pokergto/odds.py#break_even_percentage`, exact over `Fraction` |
| Call bar `B/(P+2B)` and the sizing table | `derived` | `src/pokergto/odds.py#equity_needed_to_call` -> `data/gen/tables/table.02-02.equity-needed-to-call.json` |
| Bluff fold requirement `B/(P+B)` | `derived` | `src/pokergto/odds.py#required_fold_frequency`; same column as `fold_frequency_needed` in `table.02-03.mdf-vs-sizing.json` |
| The two shove branches (62.50% / 38.46%) and the SPR table | `derived` | `src/pokergto/spr.py#all_in_equity_needed`, `#spr_commitment_table` -> `data/gen/tables/table.03-07.spr-commitment.json` |
| Draw probabilities (19.1489% / 34.9676%) and the required 7.94 of future money | `derived` algebra; the future money itself is an assumption | `src/pokergto/equity.py#draw_probability`, `src/pokergto/spr.py#implied_odds_break_even_equity` |
| `J9s` versus `88+,ATs+` on `Kh7s3d` = 20.16% | `derived` | `python -m pokergto equity "J9s" --range-villain "88+,ATs+" --board "Kh7s3d"`, exact, 1,176 runouts |
| Rake's effect on the bar | **UNVERIFIED** | no rake model in the repository; verification needs a stated rake convention plus a per-hand EV decomposition |
| Any actual fold frequency of an opponent or population | **UNVERIFIED** | needs a stated sample; chapter 13 covers the population side |

## 术语 / Terms

<!-- terms: expected-value, break-even-percentage, pot-odds, required-equity, pot, bet, call, fold, raise, bluff, shove, overfold -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| EV | 期望值 | expected value | the only verifiable unit: the long-run average |
| — | 保本百分比 | break-even percentage | `risk/(risk+reward)`, the probability success needs |
| — | 底池赔率 | pot odds | the ratio of the pot facing you to the money you must add |
| — | 所需胜率 | required equity | the call direction of this bar: `B/(P+2B)` |
| — | 底池 | pot | which moment's pot -- stated twice on purpose |
| — | 下注 | bet | `B`, the money added now |
| — | 跟注 | call | risk `B`, reward `P + B` |
| — | 弃牌 | fold | giving up further investment, not "this bet was mine" |
| — | 加注 | raise | only the added part is risk |
| — | 诈唬 | bluff | success = everyone folds |
| — | 全下 | shove | two branches, two bars, never mix them |
| — | 过度弃牌 | over-fold | the leak produced by mistake 1 |
