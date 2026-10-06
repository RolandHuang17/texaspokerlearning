# Two sizes on one street: how a mixed-size policy splits the range

<!-- hands: 2 -->
<!-- terms: size-set, mixed-strategy, betting-frequency, checking-frequency, bet-size, indifference, combos, value-range, bluff-range, spr -->

## 本节目标 / Objectives

- For a given pair of sizes (say 1/3 pot and 3/4 pot), compute with the engine the one equity at which the two bets tie, and say which strength slice each size then carries.
- Use `pokergto.theory.frequencies.value_bluff_split` to allocate an available block of value combos and bluff combos across the two sizes, and verify that each size's bluff share sits exactly on its own indifference point.
- State which results here are structural (the quota and the crossover equity) and which this repository cannot solve (the cross-size mixing frequencies), and mark the latter UNVERIFIED.

## 前置知识 / Prerequisites

- `04-01` size is governed by two routes, frequency logic and range logic; this lesson handles only the bettor's side of the split.
- `02-04` each size's bluff share `B/(P+2B)` and ratio `(P+B)/B`; `02-03` MDF gives the combos the defender must keep.
- `03-07` SPR decides whether a size is still a size at all (see `table.04-03.size-ceiling-by-stack` below).

## 核心原理 / The principle

With two sizes on one street, exactly two things are auditable here, and both come out of `pokergto.ev` and `pokergto.theory.frequencies`:

1. **Quotas.** Each size's own betting range must satisfy `bluff share = B/(P+2B)`. Two sizes mean two independent quotas, not one shared quota.
2. **Crossover equity.** Given the two fold frequencies `f₁, f₂`, there is an equity `ē` with `EV(bet₁) = EV(bet₂)`: hands above it belong to the bigger size, hands below it to the smaller one. `ē` is solved directly from two `ev_bet` branches, so it is `derived`.

**What this lesson cannot compute is the mixing itself.** Every toy game solved in this repository has a single bet size (`data/gen/solver/toy_1street_*.json`), so no artifact here contains cross-size mixing. That part is labelled UNVERIFIED.

## 推导 / Derivation

Notation: pot `P`, the two sizes `B₁ < B₂`, the fold frequencies the opponent supplies against them `f₁, f₂`, and hero's equity when called `e`. Both branches come from `pokergto.ev.ev_bet`:

```
EV(betᵢ) = fᵢ·P + (1 − fᵢ)·( e·(P + 2Bᵢ) − Bᵢ )
```

Setting them equal is linear in `e`, so one closed form falls out:

```
ē = [ (f₂ − f₁)·P + (1 − f₁)·B₁ − (1 − f₂)·B₂ ] / [ (1 − f₁)(P + 2B₁) − (1 − f₂)(P + 2B₂) ]
```

**The place this can fail is the denominator.** It is the difference between the two sizes' final pots when called, and it changes sign: once `f₂` is generous enough that the big size also earns plenty of folds, the denominator turns positive, `ē` lands at 0 or below, and the sentence "each size owns a band of strength" is simply false -- the big size is better for every `e ≥ 0`. That is not an arithmetic accident; it is this lesson's main warning (Example 3).

There is also a limit inside the closed form that needs no computation. If `f₁ = f₂` (both sizes face the same fold frequency), every `f` term cancels:

```
ē = (1 − f)(B₂ − B₁) / [ 2(1 − f)(B₂ − B₁) ] = 1/2
```

So **when folds do not rise with size, the crossover is exactly 1/2**, whatever the two sizes are: ahead goes big, behind goes small. `ē` only drops below 1/2 when the bigger size buys extra folds (`f₂ > f₁`), and it drops to nothing at 0.

The second result is the allocation. If the line has `V` value combos and `A` bluff combos to spend, split as `V₁, V₂` and `A₁, A₂`, then "neither size is exploitable" requires both equalities:

```
Aᵢ / (Vᵢ + Aᵢ) = Bᵢ / (P + 2Bᵢ),   i = 1, 2
```

Four unknowns and two equations, so one must also fix how many total combos each size carries. `pokergto.theory.frequencies.value_bluff_split(P, B, total combos)` is that solution, and `bluff_indifference_gap` re-checks that the residual is 0.

## 直觉 / Intuition

Think of the street as two separate stalls. The small size's stall is cheap: every bluff sold there has to come with 4 value hands (1/3 pot, 4 : 1). The big size's stall is expensive: 1.33 value hands per bluff is enough (3/4 pot, 2.33 : 1). Each stall keeps its own ratio, and only then is there no gap for an opponent to attack.

For the dividing line: what a hand is worth depends on whether he folds, and how much he folds depends on the size. Two sizes give two fold frequencies, so the strength axis is cut into two bands -- **not by the slogan "strong hands bet big", but by a number you can solve**, which in Example 1 is 45.00%.

## 算例 / Worked examples

**Example 1 -- the crossover between two sizes (`P = 20`, `B₁ = 20/3` i.e. 1/3 pot with `f₁ = 25%`; `B₂ = 15` i.e. 3/4 pot with `f₂ = 30%`).**

The closed form gives `ē = −0.225 / −0.5 = 0.45`. Three equity checks:

| Equity when called `e` | EV(1/3 pot) | EV(3/4 pot) | Which size |
|---|---|---|---|
| 0.40 | 10.000000 | 9.500000 | small |
| 0.50 | 12.500000 | 13.000000 | big |
| 0.90 | 22.500000 | 27.000000 | big |

Reproduce with `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(ev.ev_bet(20,20/3,F(1,4),F(2,5)), ev.ev_bet(20,15,F(3,10),F(2,5)))"`. The line `ē = 0.45` is computed, not drawn.

**Example 2 -- the allocation (available strength: 60 value combos + 20 bluff combos).** If each size carries 40 combos:

- 1/3 pot: `value_bluff_split(1, 1/3, 40)` → 32 value + 8 bluffs (share 20.00%, ratio 4 : 1).
- 3/4 pot: `value_bluff_split(1, 3/4, 40)` → 28 value + 12 bluffs (share 30.00%, ratio 2.33 : 1).
- The two together use exactly 60 value and 20 bluffs, and both residuals `bluff_indifference_gap` come back `0.0`.
- In words: **the same block of strength moved to the bigger size has to carry 4 more bluff combos and gives up 4 value combos.** That is the opportunity cost of a size, computed, and it has nothing to do with "bigger feels more aggressive".

**Example 3 -- the degenerate case where the denominator flips.** Take `f₁ = 25%` (the MDF complement of a 1/3-pot bet) and `f₂ = 50%` (the same for a pot-sized bet) with `B₁ = 1/3, B₂ = 1, P = 1`: `ē = 0`. Every `e > 0` then prefers the big size, so no dividing line exists. The same law extends across the whole ladder: when each size earns exactly the fold rate theory owes it, `EV` rises with size for every `e ≥ 0.3`, and pure air (`e = 0`) scores exactly `0` at all eight sizes. **How many sizes a street should use therefore cannot be decided by that street's own arithmetic** (reproduce in the provenance table).

## 生成表 / Generated tables

The eight standard sizes' quotas and thresholds come from this table (same source as `PYTHONPATH=src python -m pokergto odds --pot 1`):

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

Whether those sizes are even available is decided by the stack. This table says where a size stops being a size and becomes an all-in:

<!-- BEGIN AUTO:table.04-03.size-ceiling-by-stack -->
| Stack behind (bb) | Max bet / pot | Largest standard size (bb) |   SPR   | Equity needed all-in | Pot bet commits |
|---:|:---:|---:|:---:|---:|---:|
|          8 combos |    1.3 : 1    |                 6.0 combos | 1.3 : 1 |             36.3636% |             yes |
|         10 combos |    1.7 : 1    |                 9.0 combos | 1.7 : 1 |             38.4615% |             yes |
|         15 combos |    2.5 : 1    |                12.0 combos | 2.5 : 1 |             41.6667% |              no |
|         20 combos |    3.3 : 1    |                12.0 combos | 3.3 : 1 |             43.4783% |              no |
|         30 combos |     5 : 1     |                12.0 combos |  5 : 1  |             45.4545% |              no |
|         50 combos |    8.3 : 1    |                12.0 combos | 8.3 : 1 |             47.1698% |              no |
|        100 combos |    17 : 1     |                12.0 combos | 17 : 1  |             48.5437% |              no |
|        200 combos |    33 : 1     |                12.0 combos | 33 : 1  |             49.2611% |              no |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.spr#all_in_equity_needed_from_spr`

<!-- generated by: tools/gen_tables.py from pokergto.spr::spr -->
<!-- END AUTO:table.04-03.size-ceiling-by-stack -->

Read it as: with `pot_bb = 6`, an 8 bb stack can bet at most 1.3333 × pot, a 2 × pot size is outright illegal (`double_pot_is_legal = false`), and "two sizes" collapses into "one size plus a shove". The line only loosens at 15 bb (`PYTHONPATH=src python -m pokergto spr --stack 15 --pot 6` → SPR 2.500, equity needed to commit 41.67%).

## 实战牌局 / Live hands

**Hand 1 (`hand.04-04-two-size-allocation`) -- flop `9h6d3c`, pot 30 bb, hero in CO, betting strength estimated at 60 value combos + 20 bluff combos, size set {1/3 pot, 3/4 pot}.**

- Quotas: 1/3 pot carries 40 combos → 32 value + 8 bluffs; 3/4 pot carries 40 combos → 28 value + 12 bluffs (`value_bluff_split`; the same command with `P = 30` gives identical numbers, because shares depend only on `B/P`).
- Dividing line: `ē = 45.00%`. The 3/4-pot stall takes the top of the value band (`e ≥ 45.00%`) plus all 12 bluffs; the 1/3-pot stall takes the thin-value band (`e < 45.00%`) plus the remaining 8 bluffs.
- Decision: the 4 combos sitting at `e = 0.40` bet small; betting them 3/4 pot costs 0.5 chips per hand (`EV` 10.000000 against 9.500000, at `P = 20` scale).
- Cost of getting it wrong: dump all 20 bluffs into the 1/3-pot stall alongside the 32 strongest value combos (52 combos) and that size's bluff share becomes `20/52 = 38.46%` where indifference demands 20.00%, i.e. `bluff_indifference_gap = +0.184615`. Every bluff-catcher then calls profitably and the thin-value band stops getting paid.

**Hand 2 (`hand.04-04-stack-ceiling`) -- turn `9h6d3c2s`, pot 12 bb, 8 bb effective, wanting the two-level set {1/3 pot, 2 × pot}.**

- 2 × pot is 24 bb > 8 bb, illegal. The `pot_bb = 6, stack_bb = 8` row of `table.04-03.size-ceiling-by-stack` says the same thing: largest bet 1.3333 × pot, `largest_standard_size_bb = 6`, and a pot-sized bet already commits (`pot_size_bet_commits = true`).
- The size set is therefore {1/3 pot, shove}, and the allocation changes with it: 1/3 pot at `f = 25%`, the shove at `f = 0` (he either calls or folds, and there is no later street).
- Decision: estimate the same `f = 25%` for both (a shove at this depth does not buy many extra folds), and the closed form collapses to `ē = 1/2`. A hand at `e = 0.45` then goes small: `EV(1/3 pot) = 6.75` against `EV(shove) = 6.45`, 0.30 chips apart; at `e = 0.90` it reverses, `13.50` against `15.90`, and goes big. Reproduce: `PYTHONPATH=src python -c "from pokergto import ev; print(ev.ev_bet(12,4,0.25,0.45), ev.ev_bet(12,8,0.25,0.45), ev.ev_bet(12,4,0.25,0.9), ev.ev_bet(12,8,0.25,0.9))"`.
- The point of this hand is that "two sizes" is a constraint-satisfaction problem, not aesthetics: SPR deletes illegal options first, then quotas and `ē` distribute what is left.

## 范围图 / Range chart

Two sizes mean the opponent faces two different floors. The chart below is the 1/3-pot one:

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

Its use here is to supply the denominator side of the crossover: a 1/3-pot bet demands 75.00% of the range, while `range.04-02.mdf-floor-vs-pot` demands only 50.00%. The bigger the size, the fewer combos stand up, so the 12 bluff combos in the big stall meet thinner defence. **Note what the chart does not show: how much he must keep, not with which hands, and certainly not what shape my two stalls take.** Range structure belongs to an opponent model; see the next section.

## 为何成立、何时失效 / Why it works, when it breaks

**Premises**: one street; `f₁, f₂` are stated inputs rather than measurements; `e` does not change with size (the same hand's equity against a calling range is treated as size-independent -- this is the lesson's biggest simplification); and the two quotas settle independently.

**Where it breaks**:

1. **`e` does move with size.** A bigger bet forces a stronger calling range, so `e₁ > e₂` and the closed form for `ē` is invalidated. This repository cannot compute "the calling range at a given size": `02-07` treats `q` as an input, and so does this lesson. Treating `e` as constant makes the crossover a **`reference`-grade simplification**.
2. **Mixing frequencies are not solved here.** How often a specific hand uses each size requires a solve that actually produces mixing. The five one-street toys in `PUBLISHED_PROOFS` each carry a single size, and no two-street game (Leduc, ruddy) is implemented in this repository (`docs/development/solver-proof-policy.md`). **UNVERIFIED**; the path is either a two-size one-street toy with a closed-form anchor, or the ruddy two-street game.
3. **The checking half is not proved in this lesson.** The computable part of "how the two sizes share the check" is combo bookkeeping: `1326 − betting combos = checking combos`, so once the quotas are fixed the strength left in the check line is fixed too. What the check line must *contain* is `04-07`'s subject; here it is only counted.
4. **Across streets.** If the size set spans two streets (small flop bet, big turn bet), `EV` has to be recomputed over the later street and every closed form here applies to one street only.
5. **Multiway pots.** `f` becomes "everyone folds", which is not a single defender's frequency (`pokergto.odds.defense_frequency_multiway`).

## 陷阱 / Common mistakes

1. **Treating two sizes as one shared ratio.** Quotas settle per size: 1/3 pot wants 20.00% bluffs, 3/4 pot wants 30.00%. Pooled together at 25% the shapes are wrong.
   *Cost*: Hand 1's `bluff_indifference_gap = +0.184615`, i.e. the 1/3-pot stall carries 18.46 points too many bluffs, and his bluff-catchers go from indifferent to reliably profitable.
2. **Believing "strong bets big, weak bets small" is a law.** The crossover exists only while the denominator is non-zero and `ē > 0`; Example 3 shows `ē = 0` when each size earns exactly its MDF-complement fold rate, so there is no line at all.
   *Cost*: taking the slogan as a theorem makes you systematically under-use the big size against an opponent who defends the floor.
3. **Ignoring how SPR prunes the size set.** At 8 bb, discussing a 2 × pot size is discussing an illegal action.
   *Cost*: `table.04-03.size-ceiling-by-stack` row 1, `max_bet_as_pot_fraction = 1.3333`; a two-level policy built around 2 × pot cannot be executed at all there.
4. **Writing mixing frequencies as if this repository produced them.** Those numbers exist only in external solvers, and neither the licence chain nor the proof chain here accepts them.
   *Cost*: it violates `adr/0002`, and no reader can reproduce the number with any command in this repository.

## 练习 / Drills

- Solve `ē` for `P = 1, B₁ = 1/2, f₁ = 1/3, B₂ = 3/4, f₂ = 0.3`, then substitute back into `ev_bet` to confirm both branches tie (answer: `ē = 27/50 = 0.54`, both at `EV = 0.720000`).
- Swap Example 2's sizes for {1/3 pot, pot}: `value_bluff_split(1, 1, 40)` → 26.667 value + 13.333 bluffs. Ask whether the same 20 bluff combos fill two 40-combo stalls (hint: 8 + 13.333 < 20, so 1.333 bluffs must either crowd into the small stall or the total-combo allocation must change).
- Run `PYTHONPATH=src python -m pokergto odds --pot 1` and check that the value : bluff column and the bluff share column are the same equation read twice: `V/B = (P+B)/B` versus `B/(P+2B)`.
- Take Example 3 and change `f₂ = 50%` to `f₂ = 40%`; recompute `ē`, watch the sign of the denominator, and say which size has the larger final pot when called.

## 自测清单 / Self-check

- [ ] I can write the closed form for `ē` and say what a sign change in its denominator means.
- [ ] I can split 60 value + 20 bluff combos across two sizes with `value_bluff_split` and prove the residual is 0 with `bluff_indifference_gap`.
- [ ] I can name the two computable quantities here (quota, crossover) and the uncomputable one (mixing frequency), and say which artifact is missing.
- [ ] I can give an SPR at which a stated size set becomes illegal.
- [ ] I know that "strong hands bet big" stops holding once folds are exactly at the MDF line, and can show it with `EV` monotonicity.

## 来源与置信度 / Provenance and confidence

No commercial solver output and no external range table appears in this lesson. `ē`, the quotas and every expectation are computed here; the 60/20 combo budget and `f₁ = 25%, f₂ = 30%` are authored model inputs.

| Content | Source type | Location / reproduce with |
|---|---|---|
| Example 1's `ē = 0.45` and three EV rows | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; num=(F(3,10)-F(1,4))*20+(3/4)*(20/3)-0.7*15; den=(3/4)*(20+2*20/3)-0.7*(20+30); print(num/den, ev.ev_bet(20,20/3,F(1,4),F(2,5)), ev.ev_bet(20,15,F(3,10),F(2,5)))"` |
| Example 2's 32/8 and 28/12, residual 0.0 | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto.theory import frequencies as fq; print(fq.value_bluff_split(1,F(1,3),40), fq.value_bluff_split(1,F(3,4),40), fq.bluff_indifference_gap(1,F(1,3),F(8,40)), fq.bluff_indifference_gap(1,F(3,4),F(12,40)))"` |
| Example 3's `ē = 0` and ladder monotonicity | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; sizes=[F(1,4),F(1,3),F(1,2),F(2,3),F(3,4),F(1),F(3,2),F(2)]; [print(float(e), max((float(ev.ev_bet(1,B,min(B/(1+B),1),e)),float(B)) for B in sizes)) for e in [F(1),F(7,10),F(1,2),F(3,10),0]]"` (with `f = B/(P+B)`, the best size is the largest for every equity tested, and air scores 0 at all eight sizes) |
| Hand 2's `6.75` vs `6.45` and `13.50` vs `15.90` | `derived` | `PYTHONPATH=src python -c "from pokergto import ev; print(ev.ev_bet(12,4,0.25,0.45), ev.ev_bet(12,8,0.25,0.45), ev.ev_bet(12,4,0.25,0.9), ev.ev_bet(12,8,0.25,0.9))"` |
| The eight sizes' MDF, thresholds and ratios | `derived` | `PYTHONPATH=src python -m pokergto odds --pot 1`, same source as `data/gen/tables/table.02-03.mdf-vs-sizing.json` |
| SPR and the size ceiling | `derived` | `PYTHONPATH=src python -m pokergto spr --stack 8 --pot 6`, `data/gen/tables/table.04-03.size-ceiling-by-stack.json` |
| `f₁ = 25%, f₂ = 30%`; the 60 value + 20 bluff combo budget | `reference` + **UNVERIFIED** | Authored model inputs, no card-removal correction. To verify: write per-size betting and calling ranges into `data/src/spots/*.yaml`, count combos with `poker range` plus `pokergto.cards.remove_cards` |
| Cross-size mixing frequencies on one street | no artifact → **UNVERIFIED** | needs a solve that produces mixing: the five one-street toys in `src/pokergto/solver/proofs.py` each carry one size, and no two-street game is implemented (see `docs/development/solver-proof-policy.md`) |
| Pruning of a size set at low SPR | `derived` | the `double_pot_is_legal` and `max_bet_as_pot_fraction` columns of `table.04-03.size-ceiling-by-stack` |

## 术语 / Terms

<!-- terms: size-set, mixed-strategy, betting-frequency, checking-frequency, bet-size, indifference, combos, value-range, bluff-range, spr -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 尺度集合 | size set | every size permitted on the street, pruned first by SPR |
| — | 混合策略 | mixed strategy | the frequency split inside one information set; its cross-size part is not computable here |
| — | 下注频率 | betting frequency | share of the range that bets at this node, i.e. the two stalls' combos over the range |
| — | 过牌频率 | checking frequency | the complement; used here only for combo bookkeeping |
| — | 下注尺度 | bet size | `B`; both the quota and the crossover are functions of it |
| — | 无差别 | indifference | `EV(bet₁) = EV(bet₂)`, or a bluff scoring exactly 0; this lesson uses both |
| — | 组合数 | combos | the unit of a quota; `value_bluff_split` takes combos and returns combos |
| — | 价值范围 | value range | `V₁ + V₂`, assumed to be 60 combos here |
| — | 诈唬范围 | bluff range | `A₁ + A₂`, assumed to be 20 combos here |
| SPR | 筹码底池比 | stack-to-pot ratio | decides whether a size set can still hold two sizes |
