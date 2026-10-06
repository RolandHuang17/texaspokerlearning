# Regret matching: iterating only on what you should have done

<!-- hands: 2 -->
<!-- terms: regret, regret-matching, cfr, information-set, mixed-strategy, ev-decomposition, indifference, average-strategy -->

## 本节目标 / Objectives

- Turn a vector of accumulated regrets into that row's current frequencies: keep the positive part, normalise, fall back to uniform when nothing is positive.
- Do it twice by hand -- one row with two actions, one with three -- and check both against the five lines of code in this repository.
- Explain why regret must be weighted by "opponent reach times deal probability" (counterfactual), and what goes wrong without that weight.
- Name the quantity that actually converges: the iteration-weighted average, not the current frequencies (numbers in `08-04`).

## 前置知识 / Prerequisites

- `08-01` Information sets: a strategy is a table whose rows are information sets.
- `02-04` Indifference: the condition under which two actions share a row.
- `00-02` Derivation over memory: every number in this lesson ships with the command that recomputes it.

## 核心原理 / The principle

Write the accumulated regret at information set `I`, action `a` as `R(I, a)`. The current strategy is

```
σ(I, a) = max(R(I, a), 0) / Σ_b max(R(I, b), 0)     when that sum is positive
σ(I, a) = 1 / n                                       otherwise
```

In one sentence: **allocate frequencies only by what you should have done; when nothing has been learned, play uniform.** That is the whole idea of CFR, and in this repository it is five lines (`src/pokergto/solver/tree.py#regret_matching`):

```python
positive = np.clip(regrets, 0.0, None)
totals = positive.sum(axis=1, keepdims=True)
where = totals > 0.0
uniform = np.full_like(regrets, 1.0 / max(regrets.shape[1], 1))
return np.where(where, positive / np.where(where, totals, 1.0), uniform)
```

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Implementation: `src/pokergto/solver/tree.py#regret_matching`. The definition of regret and its weights:
>     `src/pokergto/solver/cfr.py#CFRSolver._cfr`. Every figure below was computed with the commands shown.

## 推导 / Derivation

**What a regret is.** At iteration `t`, for information set `I` and action `a`:

```
ΔR_t(I, a) = π_{-i}^{σt}(I) · chance(I) · ( u(I, a) − u(I) )
```

- `u(I, a)`: expected chips from `I` if `a` is taken now and both players follow their current strategy afterwards, measured in my own frame.
- `u(I)`: the value of the row under the current mixture, `Σ_a σ(I, a)·u(I, a)`.
- `π_{-i}(I)`: the probability that **the opponent's** actions lead here (excluding me and excluding chance); `chance(I)` is the deal probability.

Those two weights are the entire meaning of "counterfactual": **ask only how often the things I cannot see -- the deal and your choices -- bring me here, and never weight by my own frequency.** My own reach appears only in the strategy-sum update (`own_weight * reach_self * sigma` in `cfr.py`), never in the regret.

**Kuhn's first iteration, in full.** Start: `R = 0` everywhere, so `σ = (check 0.5, bet 0.5)` in every row. Take P0's `0:0:J`, which covers deal 0 `(J,Q)` and deal 1 `(J,K)`. With both players still uniform downstream:

```
u(bet | deal 0)   = 0.5·(+1) + 0.5·(−2) = −0.5      # P1 holds Q: folds half, calls half and J always loses
u(check | deal 0) = 0.5·(−1) + 0.5·(−1.5) = −1.25   # half showdown, half a bet I then have to answer
u(bet | deal 1)   = −0.5,  u(check | deal 1) = −1.25   # P1 holds K: same numbers, different reason
u(I)              = 0.5·(−0.5) + 0.5·(−1.25) = −0.875
```

So on each deal `bet` is worth `+0.375` over the row's own value and `check` is worth `-0.375`. The weight is `chance = 1/6` and `π_{-i} = 1` (nobody has acted yet), and two deals add up:

```
ΔR(bet)   = 1/6 · 0.375 · 2 = +0.125
ΔR(check) = −0.125
```

Verify it:

```bash
PYTHONPATH=src python -c "
import numpy as np
from pokergto.solver.games import kuhn
from pokergto.solver.cfr import CFRSolver
t=kuhn(1.0); s=CFRSolver(t); s.iteration=1; s.step(0)
i=list(t.infoset_labels).index('0:0:J'); print(np.round(s.regrets[i],6))"
# [-0.125  0.125]
```

Plain CFR keeps `[-0.125, +0.125]` and regret matching returns `σ = (check 0, bet 1)`. CFR+ first floors the negative entry at 0 (`np.maximum(regret_row, 0.0, ...)` in `cfr.py`), giving `[0, 0.125]` and the same row `(0, 1)`. On iteration 2, P0 bluffs the jack every time. **That is the move this chapter is about: not "was this hand right", but "which action gets more frequency next time".**

**One real detail that comes from alternating updates.** Within a single iteration `step(0)` runs first, so P0's regrets -- and therefore P0's strategy -- have already been rewritten when `step(1)` recomputes `sigma_by_infoset`. P1 therefore faces P0's *updated* pure strategy (bet with J, Q and K at frequency 1). That is why the first increment on `3:1:Q` is `±0.166667` rather than `±0.0833`: the weight went from `1/6 · 0.5` to `1/6 · 1`.

```bash
PYTHONPATH=src python -c "
import numpy as np
from pokergto.solver.games import kuhn
from pokergto.solver.cfr import CFRSolver
t=kuhn(1.0); s=CFRSolver(t); s.iteration=1; s.step(0); s.step(1)
for l in ('0:0:J','3:1:Q'): print(l, np.round(s.regrets[list(t.infoset_labels).index(l)],6))"
# 0:0:J [-0.125  0.125]
# 3:1:Q [-0.166667  0.166667]
```

**What is not converging.** The current strategy `σ` swings between rows. The quantity whose exploitability falls toward zero is the weighted history in `strategy_sum` -- the average strategy. `08-04` puts numbers on the size of the swing.

## 直觉 / Intuition

Treat regret as bookkeeping, not as feeling. Each information set gets a page, and each line records three things:

- what this action was actually worth (`u(I, a)`);
- what the page averaged under the mixture I was playing (`u(I)`);
- how often the invisible part of the world -- the deal and the opponent -- produced that line at all (`π_{-i} · chance`).

Therefore:

- **Positive regret = I under-played it** -> raise its frequency next time.
- **Negative regret = I over-played it** -> regret matching treats it as zero rather than steering backwards. Crude-looking, and the reason CFR+ is faster (08-05).
- **All zero, i.e. the cold start -> uniform.** Uniform is the only answer that prefers nothing when nothing is known, and the only way to start collecting evidence.
- **Only ratios matter**: `[2, −1, 4]` and `[1, −0.5, 2]` produce the same row. The ledger's unit (chips) can be rescaled and the frequencies do not move -- which is also why this update needs no learning rate.

## 算例 / Worked examples

**Example 1 -- two actions, twice by hand.** `R = [3.0, −1.0]`: positive part `[3.0, 0]`, sum 3.0, so `σ = [1.0, 0.0]`. Now a real ledger: `R = [0.33489, 0.10880]`, the `0:0:J` row of Kuhn after 200 CFR+ iterations. Positive sum = 0.443681, `0.33489/0.443681 = 0.754788` and `0.10880/0.443681 = 0.245212`, so `σ = (check 0.754788, bet 0.245212)`. The average strategy in the same run is `(0.775625, 0.224375)`: close, not equal -- that gap is exactly "current" versus "history".

**Example 2 -- three actions.** `R = [2.0, −1.0, 4.0]` -> positive part `[2, 0, 4]`, sum 6 -> `[0.333333, 0, 0.666667]`. Halve the whole row: `R = [1.0, −0.5, 2.0]` -> identical output `[0.333333, 0, 0.666667]`. Scale invariance, verified by the code.

**Example 3 -- nothing learned yet.** `R = [0.0, 0.0]` -> `[0.5, 0.5]`; `R = [−0.5, −2.0]` -> positive part `[0, 0]`, sum 0, so still `[0.5, 0.5]`. The branch lives in `where = totals > 0.0`. Delete it and the first iteration divides by zero, produces `nan`, and the whole tree rots from that row outward.

**Example 4 -- one action survives.** `R = [−4.0, 8.0]` -> `[0, 1]`: a pure strategy. A row floored to 0 under CFR+ is not dead forever: if the action improves, its increment turns positive again. The 200-iteration ledger for `0:0:Q` is `[0.18547, 0.0]` (check, bet) -- the floored entry is "bet the queen", so the current row is `(1, 0)`.

**Example 5 -- why the weight matters.** Weight the ledger by "how often I actually played this line" instead of `π_{-i} · chance`, and `0:0:J`'s page gets polluted by my own frequency: the more I bluff, the more often I reach the branches where I get paid off, so my own choice gets counted as evidence. This is close kin to a bug this repository actually shipped during development, whose symptom is a false fixed point at exploitability 0.079 (`08-04` tells that story).

## 生成表 / Generated tables

Regret matching produces no table of its own; it needs to know what it is iterating toward. In the one-street game that answer is chapter 02's algebra, and the table below is the target the iterations must land on:

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

How to read it: `MDF` is the least the defender may continue, `Fold freq a bluff needs` is the fold rate a pure bluff requires, and the two columns always sum to 1. `08-04` puts the solver's own numbers beside these: at half pot, algebra 0.666667 versus solved 0.666668.

## 实战牌局 / Live hands

Two hands: the first is one Kuhn information set's ledger from iteration 1 to iteration 2, played through the solver; the second applies the same ledger discipline to a real river spot, with all arithmetic from `pokergto.ev`.

**Hand 1 (`hand.08-02-kuhn-first-ledger`) -- `0:0:J`, iteration 1.**

- Start: `R = [0, 0]` -> `σ = (check 0.5, bet 0.5)`.
- End of the traversal: `ΔR = [−0.125, +0.125]` (computed term by term above: `u(bet) = −0.5`, `u(check) = −1.25`, `u(I) = −0.875`, two deals at weight 1/6 each).
- Iteration 2's current strategy: `(0, 1)` -- bet the jack every time.
- What then happens: the opponent, updated one traversal later, starts answering with `Q` at a positive rate, and the bluff's increment shrinks. At 200 iterations the ledger reads `[0.33489, 0.10880]` and the row is `(0.754788, 0.245212)`; at 20,000 the average strategy rests at `bet 0.213282` (`data/gen/solver/kuhn.json`).
- One line to keep: **iteration 1's ledger is not the equilibrium, it is only the truth about an opponent who has not learned yet.** The value of regret matching is that it keeps rewriting.

**Hand 2 (`hand.08-02-river-bluff-ledger`) -- heads up, river `9h6d3c2s7h`, pot 30, opponent bets 15 (half pot).**

You hold `AdKd`: no flush, beats only air. This hand is not about equity, it is about the ledger on your row `(river facing a half-pot bet, AdKd)`.

- Calling needs `15/(30+30) = 25.0%` equity (`python -m pokergto odds --pot 30`, the 1/2 pot row).
- The bluff's value is computed from **the opponent's fold frequency**, not from whether your last bluff worked. `pokergto.ev#ev_pure_bluff(30, 15, f)`:
  - he folds 62% -> `0.62·30 − 0.38·15 = +12.9` chips per attempt;
  - he folds 40% -> `+3.0`;
  - he folds 33.333% (= 1 − MDF, the half-pot row of `table.02-03.mdf-vs-sizing`) -> exactly `0`.
- Translated into the ledger discipline: **record the counterfactually weighted difference of the action, not the result of the hand.** Your last bluff winning 30 does not give `bet` a positive regret -- if the opponent was almost certain to call, the money came from the air in his range and your page should read negative. Reviewing by results instead of by response structure is the most human error available here.
- State the boundary of the transfer: the `62%` is an assumed opponent tendency (`reference`, not solver output anywhere), while `+12.9`, `+3.0` and `0` are computed by `pokergto.ev`. A real river has several sizes, later streets and card removal, so no equilibrium frequency follows from this arithmetic.

## 范围图 / Range chart

This lesson carries no range chart, and that is not an omission: regret matching operates on a handful of numbers inside one row and has no notion of a 13×13 grid. A range chart is the same object -- the strategy table -- sliced at one layer of a real game, which needs a board, a position and a combo granularity to draw. Today `data/gen/ranges/` holds exactly one file, `range.02-03.mdf-floor-vs-half-pot.json`, and it comes from algebra rather than from iteration.

To see the shape of "regret -> frequency", read the artifact rows instead: in Kuhn, `0:0:Q` is `(check 1.0, bet 0.0)` and `0:0:K` is `(check 0.360082, bet 0.639918)` (`data/gen/solver/kuhn.json`). Colour is only what that same information becomes at real scale.

## 为何成立、何时失效 / Why it works, when it breaks

**Why it works.** Regret matching guarantees that after `T` iterations the total "what the best single action on this page would have earned extra" is driven down -- regret minimisation in the literal sense -- and CFR bolts that guarantee to the tree by weighting each increment only with the opponent and chance, so every row can catch up independently. When all rows' regrets shrink together, the average strategy's exploitability shrinks. The `O(√T)` statement of that guarantee is a textbook result (treated here as `reference`, see the provenance table); its **direction** is checkable in this repository: Kuhn's CFR+ curve runs from 2.45050e-04 at 500 iterations to 1.08333e-05 at 20,000 (`curve` in `data/gen/solver/kuhn.json`), a log-log slope of about 0.8457 -- faster than `1/√T`, slightly slower than `1/T`.

**When it stops working:**

1. **Wrong information-set numbering.** Merging two decisions that should stay apart (or splitting one) means optimising a ledger in a world that does not exist. `tree.py` keeps the numbering in one place and `validate()` demands that every row of an information set has the same action count -- that is the guard.
2. **Wrong weights.** Squaring the opponent's probability, or folding your own reach into the regret. This repository did both; `08-04` gives the symptoms.
3. **A game with no anchor.** Regret matching converges to *something*, and that is not evidence of correctness, so `adr/0002` asks for a validation mechanism per game -- and only one of its four is an analytic value. Leduc has no closed form and ships anyway, because three checks that need none are writable for it: the best-response value bracket, dominance at the information sets the solved strategy actually reaches, and exploitability itself. The two-street toy still has no entry, and with no entry `tools/run_solver.py` cannot write it an artifact at all.
4. **What does not transfer.** Toy rows hold 2 actions and the tree holds 1 to 2 streets. A real postflop tree has orders of magnitude more rows: same mechanism, incomparable scale.

## 陷阱 / Common mistakes

1. **Reporting the current strategy as the answer.** The ledger says what to over-play next, not what is optimal.
   *Cost*: at 200 iterations Kuhn's current strategy is exploitable for 2.557e-02 chips per hand while its average strategy sits at 2.919e-04 -- same code, same run (command in the Drills). Copying the current strategy copies an error about 88 times larger.
2. **Forgetting the uniform fallback when no regret is positive.** The `totals > 0` branch is not decoration.
   *Cost*: on iteration 1 every row is all-zero, `0/0` becomes `nan`, and the whole tree is poisoned -- usually noticed only dozens of iterations later, when something that should have been 0.64 reads as `nan`. `python -c "...regret_matching(np.array([[0.0, 0.0]]))"` shows it in one second.
3. **Weighting the regret by your own reach.** Putting `reach_self` into the regret update instead of only into `strategy_sum`.
   *Cost*: convergence to a false fixed point. `cfr.py` documents which of the two quantities each factor belongs to; swapping them was the first real bug in this solver's history.
4. **Believing frequencies depend on the ledger's magnitude.** `[2, −1, 4]` and `[1, −0.5, 2]` give the same row.
   *Cost*: not a bug but a wrong intuition -- "multiply my regrets by ten to play more aggressively" changes nothing. Only the relative structure inside a row moves the frequencies.
5. **Adding regrets across information sets.** Writing node 0 and node 2 into one page couples decisions that the player distinguishes.
   *Cost*: the frequencies stop being a function of that one situation, breaking `08-01`'s definition. It shows up only in exploitability, never to the eye.

## 练习 / Drills

- Compute by hand, then verify: `R = [5.0, −2.0]`, `R = [1.0, 3.0, −3.0]`, `R = [−1.0, −1.0, 0.0]`.
  `PYTHONPATH=src python -c "import numpy as np; from pokergto.solver.tree import regret_matching as rm; [print(v,'->',rm(np.array([v]))[0]) for v in ([5.0,-2.0],[1.0,3.0,-3.0],[-1.0,-1.0,0.0])]"`
  Expected: `[1, 0]`, `[0.25, 0.75, 0]`, `[0.333333, 0.333333, 0.333333]`.
- Run 200 iterations, copy every row's ledger, apply the formula yourself and compare with `s.current_strategy()`:
  `PYTHONPATH=src python -c "import numpy as np; from pokergto.solver.games import kuhn; from pokergto.solver.cfr import CFRSolver; t=kuhn(1.0); s=CFRSolver(t, plus=True); s.run(200); print(list(zip(t.infoset_labels, np.round([r for r in s.regrets],4))))"`
- Say why the average strategy needs iteration weighting, and point at the `own_weight` line in `cfr.py`. (Hint: early iterations carry little information.)
- Recompute the three EVs of hand 2 with `python -m pokergto odds --pot 30` and `python -m pokergto mdf --pot 30 --bet 15`.

## 自测清单 / Self-check

- [ ] I can write regret matching in two lines of pseudocode, including the all-non-positive -> uniform branch.
- [ ] For a two-action and a three-action regret vector I can produce the current strategy by hand, and I know it is scale-invariant.
- [ ] I can name the weight in a regret update (opponent reach times deal probability) and say where my own reach goes instead.
- [ ] I can reproduce Kuhn's `±0.125` on `0:0:J` in iteration 1 and explain where the `0.375` comes from.
- [ ] I know the current strategy oscillates and that the average strategy is what converges (`08-04` has the numbers).

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every Kuhn number here comes from running `src/pokergto/solver/{tree,cfr,games}.py`, or from `data/gen/solver/kuhn.json`; the algebra cross-checks come from `pokergto.odds` and `pokergto.ev`.

| Content | Source type | Location |
|---|---|---|
| The five-line regret matching implementation | `derived` | `src/pokergto/solver/tree.py#regret_matching` |
| Regret increment and the division of the two reach factors | `derived` | `src/pokergto/solver/cfr.py#CFRSolver._cfr` |
| Iteration-1 `±0.125` and `±0.166667`; the 200-iteration ledgers and rows | `derived` | the `python -c` commands above; recomputable |
| The 20,000-iteration average strategy rows | `derived` | `average_strategy` in `data/gen/solver/kuhn.json` |
| Curve points 2.45050e-04 (500) and 1.08333e-05 (20,000) | `derived` | `curve` in `data/gen/solver/kuhn.json`, `measure_every: 500` |
| MDF and required-fold table | `derived` | `data/gen/tables/table.02-03.mdf-vs-sizing.json` |
| `f = 0.62 -> +12.9` bluff EVs | `derived` | `pokergto.ev#ev_pure_bluff` at `P = 30, B = 15` |
| The `O(√T)` bound | `reference` + **UNVERIFIED** | textbook result (the Zinkevich 2003 line), not re-proved here; only the measured slope 0.8457 from the committed curve is checked |
| The 62% fold tendency in hand 2 | `reference` + **UNVERIFIED** | an assumed opponent model, not an equilibrium claim and not output from any commercial solver |

## 术语 / Terms

<!-- terms: regret, regret-matching, cfr, information-set, mixed-strategy, ev-decomposition, indifference, average-strategy -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 遗憾值 | regret | one ledger line: the action's counterfactual value minus the row's |
| — | 遗憾匹配 | regret matching | positive part, normalised; uniform if nothing is positive |
| CFR | 反事实遗憾最小化 | counterfactual regret minimization | the five lines fed by the tree recursion |
| — | 信息集 | information set | one page of the ledger: `(node, my cards)` |
| — | 混合策略 | mixed strategy | the frequencies inside one page |
| — | 期望值分解 | EV decomposition | how `u(I, a)` is split over branches |
| — | 无差别 | indifference | at equilibrium the actions sharing a row differ by 0 |
| — | 平均策略 | average strategy | the quantity that converges; the subject of `08-04` |
