# Monte Carlo error: variance, standard error and pinned seeds

<!-- hands: 2 -->
<!-- terms: monte-carlo-simulation, variance, standard-error, sample-size, rng-seed, determinism, generated-artifact, equity, tie-chop, provenance, unverified-claim -->

## 本节目标 / Objectives

- Explain how standard error differs from variance, and write down how it moves with sample size.
- Compute the number of simulations required to hit a target precision.
- Read the four fields the engine's `--json` output returns -- `stderr`, `ci95`, `iterations`, `seed` -- and cite all of them whenever a Monte Carlo number is used.
- Show with measured data that the reported standard error is a **conservative upper bound**, and that chops shrink the real error.

## 前置知识 / Prerequisites

- `01-03` exact enumeration: every "how big is the error really" claim below is measured against a known exact value.
- `00-03` random seeds and deterministic output: know what `--seed` is for.
- Variance: `Var(X) = E[X²] - (E[X])²`.

## 核心原理 / The principle

A Monte Carlo equity is not a number, it is a **random variable**. It has its own standard deviation, called the standard error:

```
stderr = sd(one simulated outcome) / sqrt(n)
```

The engine carries `stderr` as a first-class field (`pokergto.equity.EquityResult.stderr`), and `--json` prints `iterations`, `seed`, `stderr` and `ci95` together.

**A Monte Carlo number without its error bar is a guess wearing a decimal point.** `88.19%` and `88.19% +/- 1.43pp` (`n = 2000`, `seed = 1`) are different claims: the first pretends to know more, the second tells you how much it knows.

The engine reports `sqrt(p(1-p)/n)`, where `p` is the equity: the variance a two-point outcome would have. That makes it an **upper bound** on the true error (next section).

## 推导 / Derivation

One simulation produces an outcome `X in {1, 1/2, 0}` (win, chop, loss) with probabilities `w, t, l`, and the equity is `p = w + t/2`.

```
E[X]   = w + t/2                = p
E[X²]  = w + t/4                = p - t/4
Var(X) = E[X²] - E[X]²          = p - t/4 - p²  =  p(1-p) - t/4
stderr = sqrt(Var(X)/n)         =  sqrt(p(1-p) - t/4) / sqrt(n)
```

Three conclusions:

1. **When `t = 0`**, `Var(X) = p(1-p)` and the reported figure *is* the true standard error.
2. **When `t > 0`**, the true variance is smaller by `t/4`. The reported value is therefore **conservative** -- it never lets you underestimate the noise.
3. **`1/sqrt(n)` is the only rate of convergence.** Halve the error and you multiply the work by 4; reach a tenth and you multiply it by 100. There is no second road.

**Inverting for sample size.** Requiring the 95% half-width to be at most `e`:

```
n = z^2 * p(1-p) / e^2        (z = 1.959964)
```

| Target half-width | `p = 88.19%` (AA vs 72o) | Worst case `p = 50%` |
|---|---|---|
| +/-0.50pp | 16,000 | 38,415 |
| +/-0.25pp | 63,999 | 153,659 |
| +/-0.10pp | 399,989 | 960,365 |

The same precision costs 2.4x more iterations near `p = 0.5` than at `p = 0.88`, because `p(1-p)` peaks at 0.5: **a coin flip is harder to measure than a monster.**

**Reading the 95% interval.** `ci95 = [p - 1.96*stderr, p + 1.96*stderr]`, clipped to `[0, 1]` by `error_bar_95`. It is a statement about repetition: run the same command over 100 seeds and the true value should fall inside roughly 95 of the intervals. This lesson tests that sentence by measuring actual coverage.

## 直觉 / Intuition

Think of 2,000 simulations as dealing 2,000 boards. The equity you compute from those boards differs from the one computed from a different 2,000 boards by about a percentage point, by construction -- that is sampling, not a mistake. The seed decides which 2,000 boards you got.

Therefore:

- The spread you see by changing seeds *is* the size the error bar should report. Measured here: AA vs 72o at `n = 2000` over 40 seeds ranges `[86.75%, 89.45%]` -- **2.70 points of spread** -- entirely normal.
- A fourth decimal place (`88.1937%`) should make you ask whether this was enumerated or sampled. An exact run reports `stderr = 0` and a degenerate `ci95`, and those two fields are themselves the receipt that exact was affordable.
- The engine returns byte-identical output for the same `seed` -- that is `adr/0001`'s promise, and the promise is *within a pinned dependency set*: `python tools/gen_all.py` prints the Python and numpy versions and the commit it built from, because stream stability is a per-version guarantee, not a universal one. That provenance goes to the build log rather than into a committed artifact, because a file that is byte-compared must depend on its inputs and nothing else.

## 算例 / Worked examples

**Example 1 -- real spread: AA vs 72o, `n = 2000`, 40 seeds.**
Exact value `88.1937%` (from `01-03`). Forty simulations (`seed = 1..40`): mean `88.1330%`, across-seed standard deviation `0.7101pp`, minimum `86.75%`, maximum `89.45%`.
Compare the mean to the exact value: `0.0607pp` apart, over a standard error of `0.7101/sqrt(40) = 0.112pp`, i.e. **minus 0.54 sigma** -- completely normal. **But a single seed can sit more than a point from the truth**, and any sentence of the form "I ran 2,000 simulations and got 89.45%, so AA has 89.45% equity" is misleading the listener.

**Example 2 -- the `1/sqrt(n)` law, measured on the same matchup.**

| `n` | reported stderr | true stderr (formula) | observed across-seed sd | observed spread |
|---|---|---|---|---|
| 2,000 | 0.722pp | 0.718pp | 0.710pp (40 seeds) | 2.70pp |
| 20,000 | 0.228pp | 0.227pp | 0.225pp (8 seeds) | 0.73pp |
| 50,000 | 0.144pp | 0.144pp | 0.127pp (20 seeds) | -- |
| 200,000 | 0.072pp | 0.072pp | 0.035pp (8 seeds) | 0.13pp |

The formula column is `sqrt(p - t/4 - p²)/sqrt(n)` computed on the spot (AA vs 72o has `t = 0.3998%`, so it nearly coincides with the reported column). Going from 2,000 to 20,000 is 10x the work and `0.722/0.228 ~= 3.17`x less error -- exactly `sqrt(10)`. The last row's observed sd (0.035pp) is half the theory (0.072pp): **estimating a standard deviation from 8 seeds carries about 27% relative uncertainty** (`1/sqrt(2(N-1))`), so that row is a reminder that this tool lies when you use few seeds.

**Example 3 -- coverage: is the true value inside the interval?** For AA vs 72o (truth `88.1937%`), check whether the engine's `ci95` contains the truth, seed by seed:

| `n` | seeds | covered |
|---|---|---|
| 2,000 | 20 | 20/20 |
| 20,000 | 20 | 18/20 |
| 50,000 | 20 | 19/20 |

Expected 95%, measured 100% / 90% / 95%. **Missing one of twenty is entirely normal** -- nobody should doubt the engine over a single 18/20. That is the point of the lesson: an interval means frequency, not guarantee.

**Example 4 -- the report is conservative: `AhKh` vs `AsKs`.** Exact result: equity `50.0000%`, wins `7.1574%`, ties `85.6853%` (reproducible with the same `--mode exact` command as `01-03`'s examples).
With `t = 85.69%` the true variance is `0.25 - 0.2142 = 0.0358`, standard deviation `0.1892`; the bound the engine uses is `sqrt(0.25) = 0.5`. **Ratio 2.64.**
Measured: `n = 2000` over 20 seeds gives an across-seed sd of `0.4253pp` against a true-theory `0.4237pp` (agreement), while the reported stderr says `1.1180pp`. At `n = 20000`: observed `0.1109pp`, true theory `0.1338pp`, reported `0.3536pp`.
**Conclusion: in chop-heavy matchups the published error bar is roughly three times too wide.** Saying "+/-1.1pp" is safe, but if you use it to decide whether two equities differ, you will wrongly conclude they do not.

**Example 5 -- pinning the seed.** The identical command (`AhAs 7d2s`, `n = 2000`, `seed = 7`) run twice returns byte-identical output (`equity = 0.88199`, `stderr = 0.00707888`). Change the seed to 8 and the equity is `88.875%`. **"Reproducible" never meant "invariant"; it means someone else can obtain your number.**

## 生成表 / Generated tables

This lesson's reference points are exact values, and the cheapest exact reference available is `01-03`'s draw table -- generated from closed-form binomials, with **no** sampling anywhere in it:

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

Every Monte Carlo run should be checkable against a table like this one: with `n` large enough, the simulated hit frequency must land within its own error bar of the exact entry. If it does not, either the code is wrong or you misread the bar.

## 实战牌局 / Live hands

**Hand 1 (`hand.01-04-is-this-margin-real`) -- preflop. BTN opens 2.5x, BB 3-bets to 9x, hero holds `AQo` and must call 6.5x.**

The threshold is exact algebra: `6.5/18.5 = 35.135%`. The equity is only available by simulation (`01-03` Hand 2: a preflop range matchup needs about 88 million evaluations). Measurement: `equity "AQo" --range-villain "QQ+,AKs,A5s-A4s" --mode mc --iterations 20000 --seed 4 --json` -> **37.075%, stderr 0.3415pp, 95% interval [36.41%, 37.74%]**; raising `n` to 200,000 with the same seed -> **36.473%, stderr 0.1076pp, interval [36.26%, 36.68%]**.

- Is the margin real? Distance from threshold to point estimate is `37.075 - 35.135 = 1.94pp`, i.e. **5.7 standard errors**. The call is supported by data.
- But the two runs' point estimates differ by `0.60pp` -- larger than two standard errors of the second run. **That is exactly what changing `n` and keeping the seed can do.** The decision survives because both intervals sit above the threshold; had you published point estimates only, nobody could have checked that.
- Counter-example: two runs giving 35.6% and 34.9% with +/-0.3pp bars would **not** license "one says call, the other says fold", because 35.135% lies inside both intervals.

**Hand 2 (`hand.01-04-cheap-run-vs-exact`) -- heads up, flop `Kh7h2d`, pot 100, hero holds `JhTh` facing a 100-chip shove.**

Equity needed `33.33%`. This hand can afford exact: `39.4949%` (`01-03` Example 3). What learners actually do is run the default sampler: `equity JhTh AcKc --board "Kh7h2d" --mode mc --iterations 2000 --seed 1` -> **38.85% +/- 2.14pp**, 95% interval `[36.70%, 41.00%]`.

- The exact value `39.4949%` is inside that interval, and the decision (call) matches exact.
- Yet the interval's lower edge, 36.70%, leaves only 3.4 points above the 33.33% threshold: **an `n = 2000` run can answer "do I call", not "how much margin do I have".** A flop hand-vs-hand has only 990 runouts in total -- enumeration is faster *and* exact, as `01-03` already showed. **Sampling where exact is affordable is donating an error bar to your opponent.**

## 范围图 / Range chart

The AUTO block above (`range.02-03.mdf-floor-vs-half-pot`) is a committed range artifact and deserves to be read with this lesson's eyes:

- Its metadata says `provenance.kind = derived`, `verified = true`, `derivation_ref = pokergto.odds#minimum_defense_frequency`. It is closed-form, contains no sampling, and therefore has **no seed**: in this repository the `source.seed` field of `data/gen/tables/*.json` is `null`, and `tools/gen_tables.py` writes `None` explicitly.
- By contrast `data/gen/solver/kuhn.json` carries `seed` and `iterations` as required content (committed values `seed = 0`, `iterations = 20000`), and `data/schema/solver_run.schema.json` constrains `seed` to an integer and `iterations >= 1`. The reason is blunt: **CFR's deal sampling is random, and not recording the seed means not recording the result.**
- So the repository rule is "**whoever samples writes down `seed` and `iterations`**". Any `--mode mc` number quoted in prose must come with all three of `n`, `seed` and `stderr`, otherwise the sentence cannot be checked. Hand 2 of `01-01`, and both hands above, follow that format.

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

## 为何成立、何时失效 / Why it works, when it breaks

**Premises**: simulations are independent and identically distributed (each draw takes a `(combo pair, runout)` from the same joint distribution), `n` is large enough for the normal approximation (a few thousand is plenty in poker), and `p` is not pinned against 0 or 1.

**Where it fails or needs care:**

1. **`p` near 0 or 1.** The normal approximation degrades at the boundary; `error_bar_95` clipping to `[0,1]` stops the bleeding but does not cure it. Measuring a 2% event properly requires re-running the sample-size formula (the worst-case column above gives the scale).
2. **The reported figure is a bound.** It overstates when `t > 0` (Example 4: 2.64x). Fine for conservative decisions, wrong for significance tests, where you should use `sqrt(p - t/4 - p²)`.
3. **With few seeds, the measured standard deviation is itself an estimate.** The sd from 8 seeds carries about 27% relative uncertainty (Example 2, last row). "Proving" an error bar is wrong using a handful of seeds is bad reasoning.
4. **Reproducibility is versioned.** `numpy.random.default_rng(seed)` is stable for a given numpy version; upgrading numpy may change the stream. Committed artifacts cover this with a pinned seed, and the Python/numpy versions that produced them are printed by `tools/gen_all.py` -- and every number in this lesson still needs one re-run on your machine.
5. **One measured discrepancy that remains unexplained (stated plainly).** Take `01-03`'s defense chart (884 combos) against its complement (442 combos) on `Kh7h2d`: exact is `55.92%`. Simulations of the same question: `n = 20000, seed = 3` gives `54.64% +/- 0.69pp`, `n = 200000, seed = 9` gives `55.16% +/- 0.22pp` -- both below exact, and the first miss is about 3.6 times its own reported standard error. **This repository does not explain that.** Until it is explained, prefer exact for range-vs-range where the budget allows, and treat simulated range numbers as estimates under question. Reproduction commands are in the table below.

## 陷阱 / Common mistakes

1. **Citing a simulated number without `n`, `seed` and an error bar.**
   *Cost*: the reader cannot tell whether the margin over a threshold is real, and cannot reproduce it. This is the one habit chapter 01 exists to forbid; the engine's `--json` already prints all four fields, so copying them costs nothing.
2. **Believing that doubling the iterations halves the error.** It is `1/sqrt(n)`: multiply `n` by 4 to halve the error.
   *Cost*: going from 20,000 to 40,000 and seeing the number barely move, you conclude it "converged", then treat +/-0.3pp of noise as a strategic difference and change a frequency that was already right.
3. **Reading the gap between two different seeds as a real change.** In Example 1, changing seeds moves AA vs 72o from `86.75%` to `89.45%` at `n = 2000`.
   *Cost*: deciding between two "different" equities that are only sampling. Compare intervals first, then point estimates.
4. **Simulating where exact is affordable.** A flop hand-vs-hand is 990 runouts (Hand 2).
   *Cost*: importing 1-2 points of error for nothing, then dressing it up as "my number has four decimals".
5. **Reading the conservative bound as the true error.** Example 4's factor of 2.64.
   *Cost*: the opposite error -- concluding "no significant difference" in chop-heavy spots and missing a real structural gap.

## 练习 / Drills

**Predict first, measure second (this lesson's main drill).**
Use `equity AhKh QdJs --mode mc --iterations 5000 --seed 1 --json`.

1. Write three predictions on paper: (a) roughly what the point estimate will be (hint: `01-03` gives the exact `66.6408%`); (b) roughly how large the `stderr` will be, in points; (c) whether the exact value will fall inside the interval.
2. Run it, and compare each prediction with what came out.
3. Change `--iterations` to `20000` and run `--seed 2, 3, 4`. Is the spread what the `stderr` predicted? (With `p ~= 66.64%` and `t ~= 0.44%`, stderr is about `0.33pp`, so the difference between two seeds has sd about `0.47pp`, and a max-to-min gap under `1pp` is normal.)
4. Invert: how many iterations for a +/-0.25pp half-width? Compute it with the formula, then run once and check the reported `stderr`.

Others:

- Run `equity AhAs 7d2s --mode exact` and `--mode mc --iterations 2000`, and explain why one `stderr` is 0.
- Run `equity AhKh AsKs --mode mc --iterations 2000 --seed 1..8` and compare the observed spread with the reported stderr to confirm Example 4's conservatism.
- Open `data/gen/tables/table.01-01.combo-decomposition.json` and `data/gen/solver/kuhn.json`, find the `seed` field in each, and explain why one may be empty and the other may not.

## 自测清单 / Self-check

- [ ] I can write `Var(X) = p(1-p) - t/4` and say where each term comes from.
- [ ] I can invert a target half-width into `n`, and say why `p = 0.5` is the expensive case.
- [ ] I know the reported stderr is a bound, and that it can be 2.6x too wide when most pots are chopped.
- [ ] I can name what `iterations`, `seed`, `stderr` and `ci95` are each for.
- [ ] I cite every simulated number with `n / seed / +/-` attached.
- [ ] I can state the one unexplained deviation in this lesson and which class of conclusions it weakens.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every spread in this lesson was measured by running this repository; no external simulation result is cited:

| Content | Source type | Location |
|---|---|---|
| `stderr = sqrt(p(1-p)/n)` and `ci95` | `derived` | `src/pokergto/equity.py#EquityResult` (`stderr`, `error_bar_95`) |
| Derivation of the true variance `p - t/4 - p²` | `derived` | derivation above, checked against Examples 2 and 4 |
| AA vs 72o spread over 40 seeds (86.75-89.45%) | `derived` (simulation) | `equity AhAs 7d2s --mode mc --iterations 2000 --seed 1..40 --json` |
| The `n` ladder (2,000 / 20,000 / 50,000 / 200,000) | `derived` (simulation) | same command with `--iterations` varied, seeds 1..20 |
| Coverage 20/20, 18/20, 19/20 | `derived` (simulation) | per-seed test of whether `ci95` contains `0.881937` |
| `AhKh` vs `AsKs` exact 50.0000% / ties 85.6853% | `derived` | `equity AhKh AsKs --mode exact --json` |
| The 2.64 conservatism ratio and its measured check | `derived` | `equity AhKh AsKs --mode mc --iterations 2000/20000 --seed 1..20 --json` |
| Required-`n` table (16,000 / 38,415 / ...) | `derived` | `n = z^2 p(1-p)/e^2` with `z = 1.959963984540054` (the same constant as `_Z95`) |
| Hand 1's two measurements | `derived` (simulation) | `equity "AQo" --range-villain "QQ+,AKs,A5s-A4s" --mode mc --iterations 20000/200000 --seed 4 --json` |
| Range simulation below exact (54.64%/55.16% vs 55.92%) | **UNVERIFIED / 未核验** | `range_equity(defend, complement, "Kh7h2d", mode="mc", iterations=20000, seed=3)` (and `n=200000, seed=9`); classifying it as defect or coincidence needs a code review or an independent re-implementation |
| Committed tables carry no seed, solver artifacts do | `derived` (structural fact) | `source.seed = null` in `data/gen/tables/*.json`; `data/gen/solver/kuhn.json` (`seed = 0`, `iterations = 20000`); `data/schema/solver_run.schema.json` |

## 术语 / Terms

<!-- terms: monte-carlo-simulation, variance, standard-error, sample-size, rng-seed, determinism, generated-artifact, equity, tie-chop, provenance, unverified-claim -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 蒙特卡洛模拟 | Monte Carlo simulation | the sampling approximation, priced in error bars |
| — | 方差 | variance | spread of a single outcome: `p(1-p) - t/4` |
| — | 标准误 | standard error | uncertainty of the mean, `sd/sqrt(n)` |
| — | 样本量 | sample size | `iterations`; precision is only bought with `sqrt` |
| — | 随机种子 | random seed | the key that lets someone else get your number |
| — | 确定性输出 | determinism | same version, same seed, same bytes |
| — | 生成物 | generated artifact | where `seed` and `iterations` must be written down |
| — | 未核验声明 | unverified claim | how this lesson's open deviation is marked |
