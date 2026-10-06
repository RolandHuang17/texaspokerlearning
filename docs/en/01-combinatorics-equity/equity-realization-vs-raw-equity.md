# Equity is not money: why realization falls short of raw equity

<!-- hands: 2 -->
<!-- terms: equity, equity-realization, implied-odds, reverse-implied-odds, showdown, tie-chop, spr, effective-stack, pot-commitment, position, unverified-claim, provenance -->

## 本节目标 / Objectives

- Keep the two quantities apart: the **raw equity** the engine computes (a share at showdown) and the **realized equity** you actually collect at the table, and say which question each one answers.
- List at least four structural reasons realization undershoots raw equity, and name which of them this codebase can compute and which are modelling assumptions.
- Identify the hand class that most often gets mistaken for cash, with three computed pieces of evidence from the engine.
- When somebody quotes "top pair realises at eighty per cent", say precisely what kind of claim that is and what would be needed to make it `derived`.

## 前置知识 / Prerequisites

- `01-03` Exact equity by enumeration: `equity = wins + ties/2`, averaged over runouts.
- `01-05` The seven-card evaluator: why a tie share as large as 97.09% is not a curiosity.
- `02-02` Equity needed to call: the threshold `B/(P+2B)`.

## 核心原理 / The principle

The engine produces exactly one thing: your **share** of the pot if the money closes at showdown.

```
raw equity = (weighted winning branches + weighted chops / 2) / all weighted branches
```

It is not "how often you win" and not "how much you get". Realization is about the second question:

```
realized equity = raw equity × r,   r ∈ [0, 1]
```

`r` is produced by position, who acts last, whether you can reach showdown cheaply, and what SPR says about the prices at which money can close. **No function in this repository returns `r`.** That is not an oversight, it is the current boundary: `ROADMAP.md` lists "Equity realization vs SPR as a computed quantity rather than a rule of thumb" under M8, after 1.0. So every statement here about `r` carries **UNVERIFIED**, together with what would verify it; every number about raw equity and about thresholds is computed by the engine.

> !!! note "Provenance"
>     What is computable: `src/pokergto/equity.py` (shares), `src/pokergto/odds.py` and `src/pokergto/spr.py` (thresholds, SPR, implied-odds algebra). Realization itself: no function, no artifact, a modelling assumption -- see M8 in `ROADMAP.md`.

## 推导 / Derivation

**Step one: state what the engine actually computes.** `range_equity` evaluates both hands on every legal runout, weights by combos, and returns three frequencies plus their combination:

```
equity = wins + ties/2          (asserted at construction; the object refuses to exist otherwise)
```

`python -m pokergto equity "AhJh" "KdKc" --board "Qh9h2s"` -> 990 boards, exact: equity **46.5657%**, wins 46.5657%, ties **0.00%**, losses 53.4343%. Note the ties term: this pair of hands never splits on any runout.

**Step two: the threshold side is computed too.** The same hand has to clear two different bars:

```
calling a bet:        e >= B/(P + 2B)           # P=6, B=3 -> 25.00%
committing a stack:   e >= SPR/(1 + 2*SPR)      # spr() and all_in_equity_needed_from_spr()
```

`python -m pokergto spr --stack 97.5 --pot 5` -> SPR 19.500 -> **48.75%** needed; `--stack 92 --pot 16` -> SPR 5.750 -> **46.00%**; `--stack 3.25 --pot 6.5` -> SPR 0.500 -> **25.00%**. These three are the only part of this lesson that touches realization and is still computable: **the raw equity does not move; the price of getting it all in moves with the stacks**.

**Step three: the two places where future money enters a formula.** `pokergto.spr` offers

```
implied odds:        e >= B / (P + 2B + future_winnings)
reverse implied odds: e >= (B + future_losses) / (P + 2B)
```

At `P = 6, B = 3` (half pot):

| Assumption | Equity needed |
|---|---|
| no future money | 25.00% |
| you will win 5 more | 13.70% |
| you will win 20 more | 7.04% |
| you will pay off 3 | 50.00% |

The operative word is *assumption*: `future_winnings` and `future_losses` are not computed, they are supplied. The engine guarantees only the algebra -- given that you will collect 5 extra chips whenever you hit, the required equity is 13.70%. It cannot tell you whether those 5 chips exist.

**Step four: the future money has a ceiling, and the ceiling is computable.** Later streets can only move what is still behind. With `P = 6, B = 3` and a nine-out draw counting only the next card (`draw_probability(9, 47, 1)` = **19.1489%**), the future winnings that make the call break even are

```
3 / 0.191489 - (6 + 6) = 3.67 chips
```

Feeding `implied_odds_break_even_equity(6, 3, 3.6667)` back gives exactly 19.1489% -- that is the self-check. But if only 3.25 chips are left behind, the best case is `3/(6+6+3.25)` = **19.67%** required, still above the 19.15% you hold: **short stacks clamp implied odds back onto their own ceiling**, so one card is not enough and you need both (`draw_probability(9, 47, 2)` = **34.9676%**). This line of argument is entirely computed, and it is the part of realization that is not a feeling.

**Step five: the hardest computed evidence that a share is not money.** `AcKd` against `AdKh` -- the same AKo class, suits rotated -- enumerates all 1,712,304 preflop boards as **49.6327% equity made of 1.09% pure wins and 97.0872% chops**. The share is a half; the branch where this hand takes it all is one per cent. Anything that multiplies 49.63% by the pot is pricing a set of victories that barely exist.

## 直觉 / Intuition

Ask three questions and refuse to answer all three with one number:

1. What share do I own if the money closes? Raw equity; the engine answers this.
2. Can I get to showdown cheaply? Position and the opponent's line; the engine does not answer this.
3. At what price can the money close? SPR, and the threshold `SPR/(1+2*SPR)` is computed.

Raw equity answers only question one. Realization falls short mostly for a structural reason, not a temperamental one: **your share is concentrated in the branches where you have to put more money in to collect it**. Two hands with the same 46% are not worth the same when one of them gets to watch the river for free and the other has to declare first on every street.

One sentence to keep: a chop is not a win, a fold is not zero, and raw equity is not a receivable.

## 算例 / Worked examples

**Example 1 -- flush draw plus two overcards.** `AhJh` on `Qh9h2s` against `KdKc`: raw 46.5657% (exact), ties 0.00%. Facing a half pot (`P = 6, B = 3`) it needs 25.00%, so the bar is cleared by 21.57 percentage points. But 46.5657% is the share *if the money closes*: to collect it from the flop you need to survive the other 53.4343% of branches cheaply. That second half is a realization statement, and this lesson does not attach a percentage to it.

**Example 2 -- one hand, three stack depths.** `Td9d` against `AcKc`, preflop exact: **38.7187%** (wins 38.4852%, ties 0.4670%). The number does not depend on stack depth; the bar does:

| Spot (effective stack / pot) | SPR | Equity to commit | Does 38.72% clear it? |
|---|---|---|---|
| 97.5 / 5 (100bb single-raised pot) | 19.500 | 48.75% | short by 10.03 points |
| 92 / 16 (three-bet pot) | 5.750 | 46.00% | short by 7.28 points |
| 3.25 / 6.5 (already shallow) | 0.500 | 25.00% | over by 13.72 points |

The conclusion stops at the price of closing the money: **the same raw equity is a stack-off hand at SPR 0.5 and cannot even reach a three-bet pot commit at SPR 5.75**. How much of it you actually realise while playing it deep is M8's business, and is left blank on purpose.

**Example 3 -- a dominated top pair.** `K9s` against `KQo,KQs` on `Kh8c3d`, exact over 1,176 runouts: **16.6246% equity, wins 14.8485%, ties 3.5522%**. Facing one third pot (`P = 6, B = 2`) it needs 20.00%, so **raw equity alone already fails**, short by 3.38 points. Two separate pieces of bad news: one is computed (the share is under the bar), the other is structural (the ways it does clear the bar all cost extra money). The second is realization language, so it stays a sentence, not a number.

**Example 4 -- the arithmetic of reverse implied odds.** Continuing from `P = 6, B = 3`: if you expect to pay off 3 more chips whenever you are beaten, `reverse_implied_odds_penalty(6, 3, 3)` says the required equity is **50.00%** -- double the 25.00% baseline. One assumption changing from "I pay nothing" to "I pay 3" doubles the bar. That is what "dominated draws exit fast" means when it is true; it is `(B + f)/(P + 2B)`, not temperament.

## 生成表 / Generated tables

SPR against the equity needed to commit a whole stack, computed by `pokergto.spr.spr_commitment_table`:

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

This table carries two checkable quantities, SPR and `SPR/(1+2*SPR)`. There is no realization column. If a column of `r` values ever appears here, the provenance section of this lesson has to change in the same pull request, because that would mean M8 got done.

## 实战牌局 / Live hands

**Hand 1 (`hand.01-06-flushdraw-two-questions`) -- heads up, flop `Qh9h2s`, hero `AhJh`, villain `KdKc`.**

Pot 6, bet 3. Raw equity 46.5657% against a 25.00% bar, a margin of +21.57 points. **That layer is computed, and the call/fold verdict stops there.**

- In position (villain acts first): you never have to pay to keep the share; you check behind the branches you do not want and decide on the ones you hit. The path from share to cash is the shortest one available.
- Out of position: you declare first on the turn, and in 53.4343% of the branches you are going to fold -- declaring first is exactly where that cost lives.
- This lesson refuses to write "out of position, multiply by 0.8". `python -m pokergto` exposes `odds, mdf, equity, range, spr, icm, sizes`; none of them returns `r`. The 0.8 would be an **unverified claim**, and it appears here only to be classified.

**Hand 2 (`hand.01-06-dominated-checkdown`) -- flop `Kh8c3d`, hero `K9s`, villain `KQo,KQs`, pot 6.**

- Villain bets 3: 25.00% needed, 16.6246% held (14.8485% pure wins, 3.5522% chops). Fold. Raw equity decides this on its own; realization is not even needed as an argument.
- Both check, the turn is `2d`, a brick. A free card does not add share: recomputing `equity "K9s" --range-villain "KQo,KQs" --board "Kh8c3d2d"` over all 48 rivers gives exactly **13.2576%** (13.2576% wins, 0.00% ties, 86.7424% losses), 3.37 points *below* the flop number. Seeing a card for free changes the money you do not have to pay, not the share you own -- conflating those two is the origin of "I checked, so my hand got better".
- Note the asymmetry of that share: hero's is concentrated in branches that require paying again, villain's in branches that need no payment at all. Same `Kh` on the board, two different conversion structures.

## 范围图 / Range chart

No grid in this lesson, and the reason is substantive rather than cosmetic. A range chart answers "which combos are in"; realization asks "for each combo, across the branches where it appears, how much money ends up in front of you". The grid has no such dimension, and drawing it more finely will not produce an `r`. The only generated chart artifact in the repository today is `range.02-03.mdf-floor-vs-half-pot`, a frequency quota (see `01-07` and `02-03`).

One fact tied to this lesson's own number belongs here: `tools/gen_ranges.py` reserves a chart named for 01-06, range.01-06.bb-call-vs-co-open -- the big blind's call against a 2.2x cutoff open, cut by equity against that opening range. It is marked **deferred** in the source, with the reason written next to it: a rebuild costs roughly 4.5 minutes of Monte Carlo, and classes near the cut flip between runs, so "a chart that cannot be regenerated cheaply and identically is not a teaching artifact". It is not in `data/gen/ranges/`, so this lesson does not embed it. That is the honest shape this lesson asks for: what can be computed (equity against a stated range) has an implementation and an artifact; what cannot be recomputed cheaply and reproducibly sits in the source waiting for M8 instead of being papered over with a picture.

One adjacent quantity worth naming so it does not get over-read: `pokergto.equity.vs_random` computes a range's share against a single random hand, which is the raw material for chapter 03's range and equity advantage. It is **Monte Carlo** -- the result carries `iterations`, `seed` and `stderr`, and prints as `mc(n=20000,seed=...)`. It is more honest than a realization figure precisely because it admits to being a sample. A sampled share is still a share, not a realization.

## 为何成立、何时失效 / Why it works, when it breaks

**Raw equity equals realized equity in exactly one situation:** the money is already closed. After a preflop all-in is called, or once the chips are in on the river, position and later betting lines cannot change anyone's share, and the raw number is the whole cash expectation. That is the one statement in this lesson where realization and raw equity coincide, and it comes from the definition -- no `r` needed.

**Everywhere else they differ**, because these factors move `r` without moving the share:

1. **Who acts last.** The last actor converts share with free cards; the first actor buys the same share with bets.
2. **Whether you can reach showdown cheaply.** Share concentrated in branches you fold realises poorly; share concentrated in branches you get to see realises well.
3. **SPR.** It fixes the price at which money closes: the bar runs from 25.00% at SPR 0.5 to 48.75% at SPR 19.5. The same hand's whole realization path reshapes with it.
4. **Domination.** Example 3: the low share is computed, and the share that exists is additionally attached to branches that cost money. Two layers of bad.
5. **Multiway pots.** Conversion multiplies against lines you do not control; `07-01` handles the frequency side, and this repository computes nothing on the realization side there either.

**Where this lesson is knowingly incomplete.** If someone gives you a realization figure for a spot, ask three things: which function returns it, which test verifies it, and which artifact in `data/gen` carries its provenance. Today the answer to all three is "none". The route to making it `derived` is the M8 line in `ROADMAP.md` -- realization as a computed quantity -- which needs a postflop abstraction study (a fixed set of betting lines with a checkable EV decomposition), not a table of discounts somebody tuned.

## 陷阱 / Common mistakes

1. **Paying an all-in price with a showdown share.** Pushing 38.7187% into a 48.75% bar at SPR 19.5, or defending a deep stack with the 25.00% bar that belongs to SPR 0.5.
   *Cost*: Example 2 prints the gap -- 10.03 points. One minute with `python -m pokergto spr --stack 97.5 --pot 5` catches it.
2. **Treating a chop as a win.** `AcKd` versus `AdKh` chops 97.0872% of the time.
   *Cost*: you size as if the half you "own" were a full you "win". Read the `[W.../T...]` decomposition in the `equity` output, not the aggregate.
3. **Treating implied odds as free.** The ceiling is the money behind, and that ceiling is computable (needed 3.67, available at most 3.25, so the best case still demands 19.67% against 19.15% held).
   *Cost*: calling with deep-stack reasoning at short stack depths, which is a steady annual loss.
4. **Inventing a realization percentage and teaching it as `derived`.** "Top pair realises 80%", "flush draws realise 85%" -- none of these has a source in this repository.
   *Cost*: this is exactly the confident, unattributed number the project exists to replace. Either it is marked UNVERIFIED, or it gets built in M8.

## 练习 / Drills

- Compute what `AhJh` on `Qh9h2s` needs against one third pot, half pot and pot, and compare each with 46.5657% (`python -m pokergto odds --pot 1` prints the whole column).
- Run `equity "AcKd" "AdKh"` (exact, 1,712,304 boards), read the tie term, and explain why pure wins are only 1.09%.
- With `P = 12, B = 4`: compute the required equity for `future_winnings = 6` and for `future_losses = 6`. You will get 15.38% and 50.00% -- why does the same "6" move the bar so far in opposite directions?
- Type `python -m pokergto --help`, list the subcommands, and state in one sentence which one returns a realization figure.
- For four spots (in/out of position x deep/shallow), describe only the *direction* of realization, with no percentages. That is the expressive discipline this lesson asks for.

## 自测清单 / Self-check

- [ ] I can state the definition of raw equity and why the result object asserts `wins + ties/2`.
- [ ] I can separate "share" (computable), "threshold" (computable) and "realization" (not computable today).
- [ ] I can explain why realization and raw equity coincide once the money is closed, without needing `r`.
- [ ] I can compute the ceiling on implied odds and say why stacks, not hopes, set it.
- [ ] I can file any realization percentage as UNVERIFIED and name the work that would make it `derived` (M8).

## 来源与置信度 / Provenance and confidence

Every number here is computed in this repository. No range chart or strategy output from a commercial solver or paid course appears anywhere in this lesson:

| Content | Source type | Location |
|---|---|---|
| Raw equity and its decomposition (46.5657 / 38.7187 / 16.6246 / 49.6327 / 13.2576) | `derived` | `python -m pokergto equity`, `exact=True`; `src/pokergto/equity.py#range_equity` |
| Draw probabilities (19.1489% / 34.9676%) | `derived` | `src/pokergto/equity.py#draw_probability`, same source as `data/gen/tables/table.01-03.draw-probability-exact-vs-rule.json` |
| Call threshold, commit threshold, SPR table | `derived` | `src/pokergto/odds.py#equity_needed_to_call`, `src/pokergto/spr.py`; `data/gen/tables/table.03-07.spr-commitment.json` |
| Implied / reverse implied odds algebra (13.70%, 7.04%, 50.00%, 3.67, 19.67%) | `derived` algebra over supplied inputs | `src/pokergto/spr.py#implied_odds_break_even_equity`, `#reverse_implied_odds_penalty`; the `future_*` terms are the user's assumption |
| Any value of the realization factor `r` | **UNVERIFIED** | no function, no artifact; verification path is the M8 postflop abstraction study (`ROADMAP.md`: "Equity realization vs SPR as a computed quantity rather than a rule of thumb") |
| Directional effects of position and multiway play on `r` | `reference` + **UNVERIFIED** | structural argument only; this lesson gives direction, never a percentage. Frequency side: `07-01` |

## 术语 / Terms

<!-- terms: equity, equity-realization, implied-odds, reverse-implied-odds, showdown, tie-chop, spr, effective-stack, pot-commitment, position, unverified-claim, provenance -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 胜率 | equity | the pot share if the money closes: `wins + ties/2` |
| EqR | 胜率实现 | equity realization | raw equity times an `r` nobody has computed yet |
| — | 隐含赔率 | implied odds | future winnings in the denominator, supplied as an assumption |
| — | 反向隐含赔率 | reverse implied odds | future losses added to the numerator; watch the bar double |
| — | 摊牌 | showdown | the one moment raw equity is true |
| — | 平分底池 | chop | the `ties` term, which is not a win |
| SPR | 筹码底池比 | stack-to-pot ratio | the price at which money can close |
| — | 有效筹码 | effective stack | the hard ceiling on implied odds |
| — | 套池 | pot commitment | the `SPR/(1+2*SPR)` bar |
| — | 位置 | position | the biggest mover of `r`, not of share |
| — | 未核验声明 | unverified claim | the official status of realization here |
| — | 来源标注 | provenance | the table that decides whether a number may be quoted |
