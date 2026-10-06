# SPR: stack depth and pot size collapsed into one number

<!-- hands: 2 -->
<!-- terms: spr, effective-stack, shove, required-equity, pot, bet, call, fold, equity, combos, dead-money, line, break-even-percentage, short-stack, generated-artifact, derivation-ref -->

## 本节目标 / Objectives

- For any line of play, compute the SPR at the start of a decision point -- chips behind divided by pot -- and say how counting or ignoring dead money moves that number.
- Re-derive `SPR/(1+2*SPR)` from the single condition "my share of the final pot must be at least the money I put in", instead of memorising it.
- Use that threshold to decide whether a hand whose equity the engine enumerated is worth committing at a given depth, and explain why the threshold is bounded by 50% and why any hand above 50% may stack off at every depth.

## 前置知识 / Prerequisites

- `02-06` One notation for every action: `pot` is the money in the middle **before** the actor adds anything and `bet` is what they add; a shove is just the case `bet = chips behind`, which is exactly what this lesson substitutes.
- `01-07` Reading a 13x13 grid: SPR changes no range's combo count. It moves the line marking which combos are worth pushing, so both lessons have to weight by combos, not by hand classes.

## 核心原理 / The principle

The stack-to-pot ratio at the start of a street is

```
SPR = effective chips behind S / pot P
```

and the equity required to shove the whole stack behind you is

```
e* = S / (P + 2S) = SPR / (1 + 2*SPR)
```

This is a `derived` claim: it uses one condition -- money must be able to earn itself back -- and no range chart, no solver, no one's authority. Its range is `(0, 1/2)`, it increases with SPR, and it approaches `1/2` as `SPR -> infinity`.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Derivation: next section. Implementation: `src/pokergto/spr.py` (`spr`, `all_in_equity_needed`, `all_in_equity_needed_from_spr`). Generated table: `data/gen/tables/table.03-07.spr-commitment.json`.

## 推导 / Derivation

Let the pot be `P` (dead money included) and let you have `S` behind, with at least `S` behind your opponent. You shove, you get called, the final pot is `P + 2S` and your share of it is `e*(P + 2S)`. Requiring that share to cover the `S` you risked:

```
e*(P + 2S) >= S
e >= S / (P + 2S)                                 <- absolute chips
e >= (S/P) / (1 + 2*S/P) = SPR / (1 + 2*SPR)       <- the same line divided by P
```

The second step divides numerator and denominator by `P`, **which requires `P > 0`**, and that is the only step in this lesson able to fail. `pokergto.spr.spr` raises `SPR needs a positive pot` when it is not: not defensive coding, but the statement that depth is meaningless when nobody has money in. A line with an empty pot has no SPR rather than an infinite one.

The bound follows from the same expression, with no new assumption:

```
lim(SPR->inf) SPR/(1+2*SPR) = 1/2      and       SPR/(1+2*SPR) < 1/2 always
```

because the denominator `1 + 2*SPR` is always the numerator's `2*SPR` plus that extra `1`. **So any hand with equity at or above 50% may get it all in at any depth**, and any hand below 50% has a depth at which it may not. The inverse turns that sentence into arithmetic:

```
SPR* = e / (1 - 2e)          <- the largest SPR at which equity e still justifies a shove
```

At `e = 1/2` the denominator is zero and the inverse diverges -- `python -c` raises `ZeroDivisionError: Fraction(1, 0)`. That exception is the proof of the ceiling, not a wording choice.

## 直觉 / Intuition

SPR answers "**how many all-ins are left in this line**". At SPR 1 the pot and your stack are the same size, so one bet finishes every later decision. At SPR 15 the pot is a token and the real money still has several streets to travel.

That dissolves the question "can I stack off with top pair?" and replaces it with a comparison of two numbers.

- The threshold moves only with SPR: `SPR = 5` is the same line whether the pot is 6bb or 60bb, and the worked examples below compute all four of those pairs.
- Depth moves the **bar**, not your hand: a pot-sized bet does not change your equity.
- The 50% ceiling is the part worth carrying to a table: while you are a favorite, "too deep to stack off" does not exist mathematically.

Mental model: SPR is a leverage ratio and the threshold is the minimum force that lever needs in order to move one all-in.

## 算例 / Worked examples

Every number below comes from a command printed in this lesson; every equity is an exact enumeration (`"exact": true`, no sampling error).

**Example 1 -- scale invariance.** `python -m pokergto spr --stack 60 --pot 12` prints `SPR = 60.0/12.0 = 5.000` and `0.4545` (exact `5/11 = 45.4545%`). The same command with `--stack 30 --pot 6`, `--stack 15 --pot 3` and `--stack 120 --pot 24` prints `5.000` and `45.4545%` as well. **Four situations that look completely different are one situation**, which is the entire reason SPR exists.

**Example 2 -- four real lines.** (100bb means 100; the 0.5/1 blinds are dead money and counted into the pot.)

- 100bb, CO opens 2.5 / BTN calls: `S = 97.5`, `P = 6.5` -> SPR `15.0000`, shove needs `48.3871%` (exact `15/31`).
- 100bb, CO 2.5 / BTN 3-bet 7.5 / CO calls: `S = 92.5`, `P = 16.5` -> SPR `5.6061`, needs `45.9057%` (`185/403`).
- 25bb, the same 3-bet line: `S = 17.5`, `P = 16.5` -> SPR `1.0606`, needs `33.9806%` (`35/103`).
- 10bb, CO 2.2 / BTN 3-bet 6.5 / CO calls: `S = 3.5`, `P = 14.5` -> SPR `0.2414`, needs `16.2791%` (`7/43`).

The four rows come from `python -m pokergto spr --stack 97.5 --pot 6.5` (prints `15.000 / 0.4839`), `--stack 92.5 --pot 16.5` (`5.606 / 0.4591`), `--stack 17.5 --pot 16.5` (`1.061 / 0.3398`) and `--stack 3.5 --pot 14.5` (`0.241 / 0.1628`); the exact fractions come from `python -c` calling `pokergto.spr.all_in_equity_needed(pot, stack, exact=True)`.

**Example 3 -- dead money moves the bar.** Same 100bb 3-bet line, but counting only the two players' money, `P = 7.5 * 2 = 15`: `spr(92.5, 15) = 6.1667` and the threshold rises to `46.25%`; counting the 1.5bb of blinds gives `5.6061` and `45.9057%`. A third of a percentage point looks trivial, but **it is enough to flip a verdict**: a 46.0% hand passes under one convention and fails under the other. That is not rounding, it is a definition, which is why this repository states the convention at the head of every sentence: the pot includes dead money.

**Example 4 -- threshold against actual hand equity.** `python -m pokergto equity "9d7d" "AA,KK,QQ,JJ,TT,AKo,AQo,ATo,KQo,AJs" --board "Th8s2c"` gives `0.395521`. That open-ended straight draw:

- may shove at SPR `1.0606` (the 25bb line, needs 33.98%);
- may not at SPR `5.6061` (the 100bb 3-bet line, needs 45.91%);
- certainly may not at SPR `15.0` (the 100bb single-raised pot, needs 48.39%).

Same hand, same board, same bet size, only the stacks differ. **That is the only checkable form the sentence "SPR decides commitment" has.**

**Example 5 -- the 50% ceiling is alive.** `python -m pokergto equity "Ah4h" "KK,QQ,JJ,TT,AKo,AQs,KQs" --board "9h5d2h"` gives `0.571768`. 57.18% exceeds 50%, so this hand may commit at SPR `0.2414 / 1.0606 / 5.6061 / 15.0 / 20.0 / 100.0`, whose thresholds are `16.28% / 33.98% / 45.91% / 48.39% / 48.78% / 49.75%`. In the other direction, `python -m pokergto equity "Jd9d" "AA,KK,QQ,JJ,TT,AKs,AQs,ATs,KQs,AKo,AQo" --board "Kh7s3d"` gives `0.152320`, which fails to justify a shove at every SPR from `0.2414` upward -- even a 10bb stack (16.28%) cannot rescue it.

**Example 6 -- calling is not committing.** In the 100bb 3-bet pot, BTN bets 5.5 into 16.5. One more street costs `5.5/(16.5+11) = 20.00%`; pushing the whole 92.5 costs `92.5/(22 + 2*92.5) = 44.6860%` (the opponent's 5.5 is already in the middle, which is why this is slightly below the street-start 45.91%). `9d7d` at 39.55% sits between them: calling is worth `ev_call(16.5, 5.5, 0.395521) = +5.3768` chips, and shoving still falls 5.13 points short.

## 生成表 / Generated tables

The first table walks the whole SPR axis; `all_in_equity_needed` is computed by `pokergto.spr.all_in_equity_needed_from_spr`:

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

The dual question is **the ceiling that chips behind put on bet sizes**. It contains no notion of hand strength, only "does this size exist". With the pot fixed at 6bb, three rungs computed with `python -c` (`pokergto.spr.spr` and `all_in_equity_needed_from_spr`):

- 8bb behind: `SPR = 1.3333`, shove threshold `36.3636%`; the largest rung of the standard size ladder not exceeding 8bb is `6bb = 1x pot`.
- 10bb behind: `SPR = 1.6667`, threshold `38.4615%`; the largest usable rung is `9bb = 1.5x pot`.
- 15bb behind: `SPR = 2.5`, threshold `41.6667%`; only here does `12bb = 2x pot` become a legal size for the first time.

One test decides all of it: `2x pot` on a 6bb pot is 12bb, so the size exists exactly when `S >= 2P`. The full grid lives in `04-03`'s artifact `table.04-03.size-ceiling-by-stack`; sizing itself is chapter `04`, and this lesson takes only the half that SPR caps.

## 实战牌局 / Live hands

**Hand 1 (`hand.03-07-openender-two-depths`) -- the same draw answered twice, by depth alone.**

Seats and money: 6-max. In the first line everyone has 100bb; in the second everyone has 25bb. CO holds `9d7d` and calls BTN's 3-bet in both lines. The flop is `Th8s2c` in both.

- 100bb line: pot `16.5` (1.5 of it dead money), `92.5` behind each -> SPR `5.6061` -> a shove needs **45.9057%**. BTN bets 5.5. `9d7d` holds **39.5521%** against BTN's declared betting range `"AA,KK,QQ,JJ,TT,AKo,AQo,ATo,KQo,AJs"`. Decision: **call, do not shove.** Calling is worth `ev_call(16.5, 5.5, 0.395521) = +5.3768`; shoving 92.5 into 22 costs 44.6860%, 5.13 points above what the hand actually owns, and the extra 87 chips buy nothing.
- 25bb line: same pot `16.5`, but `17.5` behind each -> SPR `1.0606` -> a shove needs only **33.9806%**. The identical 39.5521% now clears the bar by **5.57 points**. Decision: **shove.** Flatting here does not buy flexibility, it only postpones the same decision to a turn bar whose threshold is higher again.
- Nothing in either line is a sentence about how the opponent plays. The whole difference is the two divisions `17.5/16.5` and `92.5/16.5`.

**Hand 2 (`hand.03-07-adkc-two-lines`) -- top pair, and the third dimension nobody names.**

Seats and money: 40bb stacks. CO opens 2.5 with `AdKc`, BTN 3-bets to 7.5, CO calls. Flop `Kh7s3d`, pot `16.5`, CO has `32.5` behind -> SPR `1.9697` -> a shove needs **39.8773%**.

- `AdKc` holds **79.4731%** against BTN's declared 3-bet range `"AA,KK,QQ,JJ,TT,98s,AKs,AQs,AKo,AQo"` (`python -m pokergto equity "AdKc" "AA,KK,QQ,JJ,TT,98s,AKs,AQs,AKo,AQo" --board "Kh7s3d" --json`). 79.47% is twice the bar, so from the flop on this line has exactly one action: put the money in. Facing BTN's 5.5, `ev_call(16.5, 5.5, 0.794731) = +16.3551`, and folding discards that entire amount.
- Widen the same 3-bet line to 100bb: SPR `5.6061`, bar `45.9057%` -- 79.47% still clears it, verdict unchanged. The unchanged verdict is the point: **"can I stack off with top pair" was never a question about top pair.** It is a question about SPR, and depth becomes the deciding factor only when the hand's equity lands between two thresholds -- which is exactly where `9d7d`'s 39.5521% sits in Hand 1.

## 范围图 / Range chart

<!-- BEGIN AUTO:range.04-02.mdf-floor-vs-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | :: | .. | .. | .. |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 7 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 6 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 5 | @@ | @@ | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 4 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 3 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 2 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |

663.0 combos = 50.00% of all 1,326

Legend: `··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%; the diagonal is pairs, the upper triangle suited, the lower offsuit.

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.04-02.mdf-floor-vs-pot -->

The chart is the **MDF quota for a pot-sized bet**: combos filled in strength order until they cover `663.0` of the 1,326 (50.00%). It describes the same decision as this lesson's formula, read from the other side. How deep do you have to be before "bet the pot" already means "shove"? The three ceiling rungs above answer it: with a 6bb pot, stacks of 8bb and 10bb both satisfy `S <= 2P`, so after a pot-sized bet and call there is no more money left than the bet just made; at 15bb that stops being true (`SPR` 1.3333, 1.6667 and 2.5). So **below roughly SPR 1.67 one pot-sized bet triggers two quotas at once**: the defender must continue with 50% of combos (this chart), while the attacker's entire stack needs only a 36.36%-38.46% threshold (the same divisions as Example 2).

The boundary to keep: **the 50% in the chart is a defense quota, not an all-in equity threshold.** The denominators differ (`P/(P+B)` versus `S/(P+2S)`), and reading the chart as the latter is this lesson's most common error.

## 为何成立、何时失效 / Why it works, when it breaks

**The assumptions, one by one:**

1. **Chips are linear in utility.** True in cash; false near a tournament bubble, where the correct bar is the ICM-priced one and sits above this section's threshold (chapter 12).
2. **A shove runs to showdown.** The formula assumes nobody can fold once the money is in. If the opponent can fold to your shove, the shove carries bluff equity and the right tool becomes `pokergto.ev.break_even_equity_to_bet` (chapter `04`).
3. **The equity you feed in is the real equity.** This is where the rule of thumb fails, and the engine says so out loud: `python -m pokergto equity "AhKh" "7c7d" --board "7s6d2c" --json` returns **0.000000** -- zero wins and zero ties in all 990 turn-river combinations. "Two overcards have 6 outs, about 24%" is a statement about being behind **a pair**, not behind **three of a kind**: against a set, pairing your ace still leaves you with a pair, and a pair loses to trips. Change one card's suit and the number moves: the same two hands on `7h6s2c` give **0.028283**, because now runner-runner hearts exist.
4. **SPR is a snapshot, not a property of the line.** Every chip added to the pot lowers the threshold: the 100bb 3-bet pot starts at SPR `5.6061` (45.9057%), becomes `spr(87.0, 27.5) = 3.1636` (43.1762%) after a one-third-pot bet is called, and the shove facing that uncalled bet costs 44.6860%. Three thresholds, all correct, all computable, all for the same hand (Example 6).

**Where it must be rewritten:** in multiway pots "winning the money in" means beating two distributions at once, so `e` is no longer a two-player showdown equity (see `07-01` and this chapter's `03-09`); when raises are available, continuation frequency and commit frequency separate, exactly as in `02-03`; and at equal equity, 39.55% is worth more in a line where the opponent's range is capped than in one where somebody owns the nut tier -- that is `03-01`'s subject, not this formula's.

## 陷阱 / Common mistakes

1. **Computing SPR once preflop and treating it as the line's number.** SPR belongs to the decision point. In the same 100bb 3-bet line it falls from `5.6061` to `3.1636` after a one-third-pot bet is called, and the bar falls with it, from 45.9057% to 43.1762%. Using the street-start bar on later streets throws away every hand between 43.18% and 45.91% -- and that interval is not hypothetical: `python -m pokergto equity "9d7d" "AKo,AQo,KQo,ATo" --board "Th8s2c" --json` prints **44.4242%**, which lands strictly between 43.1762% and 45.9057%. Judged with the street-start bar that hand is a fold; judged with the bar one decision later it is a shove, and the only thing that changed is a division.
2. **Memorising "top pair commits, draws don't".** Counterexample is Example 4: `9d7d` is a shove at SPR 1.0606 and merely a call at SPR 5.6061, while `Ah4h` -- also a draw -- commits at SPR 100. *Cost, exactly:* folding `9d7d` in the SPR `1.0606` line discards `ev_call(16.5, 5.5, 0.395521) = +5.3768` chips per hand; shoving the same hand into the SPR `15.0` single-raised pot (`python -m pokergto spr --stack 97.5 --pot 6.5`) means paying a 48.3871% bar with 39.5521% in hand, i.e. buying insurance 8.83 points too cheap to pay for itself.
3. **Substituting the call threshold for the commit threshold.** At one third pot they are 20.00% versus 44.6860% (or the street-start 45.9057%) in the same spot. *Cost:* `Jd9d` against `"AA,KK,QQ,JJ,TT,AKs,AQs,ATs,KQs,AKo,AQo"` owns 15.2320%, so `ev_call(16.5, 5.5, 0.152320) = -1.3112` -- it does not even pass the calling bar; playing it as "a draw, so a cheap call" repeats that loss on the turn, at which point SPR forces 92.5 into a pot that needed 44.69%.

## 练习 / Drills

Mental arithmetic first, then the command; every answer below was produced this session.

- 100bb, CO opens 2.5 / BTN calls, blinds counted as dead money: SPR and the shove threshold? (`python -m pokergto spr --stack 97.5 --pot 6.5` -> SPR 15.000, bar 48.3871%)
- A 4-bet pot: BTN 3-bets 7.5, CO 4-bets 18.5, BTN calls, 100bb. `spr(81.5, 38.5) = 2.1169`, bar 40.4467%. How many points lower is that than the 3-bet pot's bar? (45.9057% - 40.4467% = 5.46 points)
- Inverse: a hand is exactly worth a shove at SPR 3. What is its equity? (`all_in_equity_needed_from_spr(3) = 0.428571`, i.e. 42.8571%)
- Ceiling check: `all_in_equity_needed_from_spr(1000)` = 0.499750, still below 1/2. Now call the inverse `SPR* = e/(1-2e)` with `e = 1/2` via `python -c`, watch the `ZeroDivisionError`, and explain why that is a theorem rather than a bug.
- Maxim check: why does `python -m pokergto equity "AhKh" "7c7d" --board "7s6d2c" --json` print 0? Re-run it on `7h6s2c` (0.028283) and name the hand class each number is paying for.

## 自测清单 / Self-check

- [ ] I can derive `e* = S/(P+2S)` from "share at least equals risk" and point out that dividing by `P` requires `P > 0`.
- [ ] I can explain why SPR 5 gives one threshold in a 6bb pot and a 60bb pot, and how much dead money moves that number.
- [ ] I can state the 50% ceiling and prove it with the inverse `SPR* = e/(1-2e)` diverging at `e = 1/2`.
- [ ] Given a line, I can compute the SPR at that decision point, read the threshold, and choose shove/call/fold against an engine-computed equity.
- [ ] I can list two situations where the threshold is right but applied to the wrong quantity (ICM; a shove that can be folded), and name the function that replaces it.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->

| Content | Source type | Location / the command that produced it |
|---|---|---|
| SPR definition and threshold | `derived` | `src/pokergto/spr.py#spr`, `#all_in_equity_needed`, `#all_in_equity_needed_from_spr`; derivation above |
| SPR -> threshold table | `derived` | `data/gen/tables/table.03-07.spr-commitment.json` |
| MDF quota chart (pot size) | `derived` | `data/gen/ranges/range.04-02.mdf-floor-vs-pot.json`, assumptions recorded in `provenance.assumptions` |
| The four lines' S/P and thresholds | `derived` | `python -m pokergto spr --stack ... --pot ...`; `python -c` calling `pokergto.spr.spr` |
| All hand equities (39.5521%, 44.4242%, 57.1768%, 79.4731%, 15.2320%, 47.7778%, 0.000000, 0.028283) | `derived` | `python -m pokergto equity ... --json`, `exact: true`, enumeration of all 990 runouts |
| EVs (+5.3768, +16.3551, -1.3112) | `derived` | `python -c` calling `pokergto.ev.ev_call`, formula `e(P+2B) - B` |
| The declared opponent ranges `"AA,KK,QQ,JJ,TT,98s,AKs,AQs,AKo,AQo"` and friends | `reference` + **UNVERIFIED** | Illustrative inputs chosen so the exact enumeration stays cheap; they are not a solved strategy nor a measured population. Turning them into a solved decision needs a spot definition in `data/src` plus an artifact emitted by `tools/gen_tables.py`. |
| "Top pair can stack off" / "two overcards have 6 outs" | refuted in this lesson | Refuted by commands above: two overcards against a set on `7s6d2c` hold 0.000000 |

No commercial solver output, no transcribed range chart, no screenshots anywhere in this lesson.

## 术语 / Terms

<!-- terms: spr, effective-stack, shove, required-equity, pot, bet, call, fold, equity, combos, dead-money, line, break-even-percentage, short-stack, generated-artifact, derivation-ref -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| SPR | 筹码底池比 | stack-to-pot ratio | `S/P` at a decision point, `S` the effective stack |
| — | 有效筹码 | effective stack | the smaller of the two stacks behind, not "chips remaining" |
| — | 全下 | shove | the case `bet = S`, threshold `S/(P+2S)` |
| — | 套池 | pot commitment | equity already above the shove bar, so no later street contains a fold |
| — | 所需胜率 | required equity | the one-street bar `B/(P+2B)`, a different quantity |
| — | 死钱 | dead money | antes and folded players' money; counting it slightly lowers the bar |
| — | 行动线 | line | an ordered list of actions; SPR belongs to its points, not to it |
| — | 短码 | short stack | relative to the blinds; here the 25bb and 10bb lines |
| — | 组合数 | combos | the weighting unit everywhere: `AKo` 12, `AKs` 4, `AA` 6 |
| — | 生成物 | generated artifact | tables and charts under `data/gen`, the only source of numbers |
| — | 推导指针 | derivation reference | `provenance.derivation_ref`, a pointer CI resolves to a real symbol |
