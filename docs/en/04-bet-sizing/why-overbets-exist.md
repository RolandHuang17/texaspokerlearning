# Why overbets exist: nut capacity that carries a huge size

<!-- hands: 2 -->
<!-- terms: overbet,pot-fraction,capped-range,the-nuts,capacity,nut-advantage,spr,effective-stack,bet-size,minimum-defense-frequency,exploitability,bluff,combos -->

## 本节目标 / Objectives

- Given a pot and the chips still behind, decide first whether "2x pot" exists at all before asking whether it is right, and use `table.04-03.size-ceiling-by-stack` to name the line where a size stops being a size and becomes an all-in.
- Compute the minimum defense frequency (MDF) a pot fraction imposes, and the chip cost of defending 10 points under it, then explain why the identical error costs an order of magnitude more against an overbet than against one third pot.
- Use combo counts and the `is_capped` verdict to state how much air a range must produce to carry a 2x-pot size, and why the size is hollow when it cannot.

## 前置知识 / Prerequisites

- `04-02` the conversion from pot fraction to defence burden, and the ceiling `b ≤ f·p/(1−f)`.
- `02-03` minimum defense frequency: `MDF = p/(p+b)`; the bigger the bet, the smaller the quota.
- `03-01` nut advantage and capacity: who holds the best hand when the money goes in is this lesson's entry requirement.

## 核心原理 / The principle

Overbets exist because **the value term grows linearly in `b` while the defence quota they demand falls with `b`** -- but they are also the rung on the ladder most often cut off by the chips, so you must ask about stacks before you ask about cards: **a 2x-pot bet is `2p` chips, so it exists only if at least `2p` are still behind (at exactly `2p` it is simultaneously an all-in), and it is a chosen size only when `S > 2p`.** What carries the size is the range's nut capacity: only the uncapped side in `table.03-02.capped-range-check` can pay the bluff share the size demands. This is `derived`: the chip part from `pokergto.spr`, the ratio part from `pokergto.odds`, the capacity part from `pokergto.theory.range_advantage`.

<!-- provenance: kind=derived verified=true -->
> Derived at: `src/pokergto/spr.py#all_in_equity_needed_from_spr`, `src/pokergto/odds.py#minimum_defense_frequency`; the independent cross-check is `src/pokergto/solver/proofs.py#PUBLISHED_PROOFS`.

## 推导 / Derivation

Notation carried over from the two previous lessons: `p` the pot before the bet, `b` the amount added, `f` the frequency with which every opponent folds (a declared input), `e` hero's equity when the money goes in, `S` the chips still behind the actor (effective stack).

### Step one: existence comes before optimality

A size is first of all chips: `b ≤ S`. Since "largest bet as a fraction of pot" is `S/p`, that number is the SPR, and

```
2x pot exists            <=>  2p ≤ S      <=>  SPR ≥ 2      (at equality it is also an all-in)
another pot-sized bet fits  <=>  S − p > p  <=>  SPR > 2
```

`table.04-03.size-ceiling-by-stack` is that conversion written out for eight stack depths on a fixed 6bb pot. Its last column, `Pot bet commits`, uses the generator's test `stack <= 2 * pot`, i.e. `SPR ≤ 2`: it is true in the 8bb and 10bb rows, meaning **after betting pot there is not enough left to bet pot again**, so the street is no longer choosing a size but deciding whether to commit. The MDF formula still holds in those rows, but the ladder is no longer a free choice of variable -- the 1x pot row of `table.02-03.mdf-vs-sizing` is describing a near-shove there.

### Step two: why the overbet pays (the value term is linear)

In `04-01`'s closed form the called branch is `(1−f)·b·(2e−1)`: with `e > 1/2` it grows linearly in `b`. Double the size and you roughly double the gain -- at `e = 3/4` on a 6bb pot, each size faced with its own MDF fold rate: 1/3 pot `1.125bb`, pot `2.25bb`, 2x pot `3.0bb`.

The defence side moves at the same time, and it moves **down**: `MDF = 1/(1+s)`, so `s = 2` asks only `33.33%` (442 combos, see the Range chart section). Price a defence shortfall of Δ points as `Δ·(p+b)`: at `s = 1/3` that is `p+b = 8bb`; at `s = 2` with `p = 20bb` it is `p+b = 60bb`. **The same 13.33-point hole hands air `1.066667bb` against a third-pot bet and `8.000000bb` against a double-pot bet -- 7.5 times more.** That is the menace of the overbet: not that it scares people, but that you cannot afford to miss defending it.

### Step three: capacity -- who can pay the air tax of a big size

`02-04`'s ratio says the bluff share inside the betting range is `s/(1+2s)`: 20% at `s = 1/3`, and **40%** at `s = 2` (value:bluff 1.5:1, last row of `table.02-04.bluff-value-ratio`). Bigger sizes therefore demand *more* air, not less: 2 bluff combos for every 3 value combos. Air loses on its own, and that mix is only survivable when enough hands behind it can win a big pot -- which is what nut capacity means: the side where `is_capped` is false can produce the 40% because it also holds the nut-tier combos. Measured in the engine (turn board `AsKsQhJd`, ranges authored for teaching):

```
python -c "..."  ->  villain capped True   hero capped False
```

Read the other way, the popular line "overbets are polarised so they are all nuts" is half wrong: what is polarised is the **ratio** -- 40% of the range is air and 60% is the hands that carry it.

## 直觉 / Intuition

Picture the sizing ladder as a building: one third pot is the foundation, demanding 75% defence (994.5 combos) while letting you carry only 20% air upstairs; 2x pot is the top floor, demanding just 33.33% (442 combos) but requiring 40% air -- **and you must check that the roof has not arrived**, because the chips behind are the roof.

Three nails to hang on it:

- The ceiling on a size is chips, not nerve: below `SPR = 2` the "2x pot" rung does not physically exist.
- A big size punishes frequency errors, not strength errors: its bill is settled at `Δ·(p+b)`, and the bigger `p+b`, the more it costs.
- The air share is the ticket: without 40% air, or without the nut combos that back it, the size is empty for you.

## 算例 / Worked examples

**Example 1 -- existence check (pot 6bb).** `python -m pokergto spr --stack 8 --pot 6` → SPR `1.333`, equity needed to commit `0.3636`; `python -m pokergto mdf --pot 6 --bet 8` → `MDF = 0.4286`. There is no 2x pot here (`2p = 12bb > 8bb`); the largest bet is 8bb = 1.3333 pot and it *is* the all-in. A defender who mistakenly applies the ladder's `MDF = 33.33%` for a 2x-pot row is 9.5238 points short, settled at `Δ·(p+b)`: `0.095238 × 14 = 1.333333bb`, measured as `ev_pure_bluff(6,8,2/3) = 1.333333`. **Defending with the numbers of a size that does not exist gifts 1.33bb every time.**

**Example 2 -- what a legal overbet is worth (pot 20bb, 60bb behind, `e = 0.919545`).** `python -m pokergto spr --stack 60 --pot 20` → SPR `3.000`, so 2x pot = 40bb is a size, not a shove (20bb still left after it). Gains per hand with each size at its own MDF fold rate: 1/3 pot `4.597725bb` · pot `9.195450bb` · 2x pot `12.260600bb`; `compare` plus `regret` puts one third pot `7.994944bb/hand` below the best row. **The claim "betting smaller is safer" costs 8bb a hand in this hand.**

**Example 3 -- the defence shortfall inflates with the size (pot 20bb, 2x pot = 40bb).** `python -m pokergto mdf --pot 20 --bet 40` → `MDF = 0.3333`. Defending 20% (13.33 points short) gives air `ev_pure_bluff(20,40,0.8) = 8.000000bb`; defending exactly 33.33% gives `0.000000bb` (indifference); defending 40% (folding only 60%) costs hero `−4.000000bb` -- over-defending is the opponent's profit, not your insurance.

**Example 4 -- the bluff ticket and where the regime flips (`p = 1, b = 2`).** Air needs `f ≥ b/(p+b) = 66.67%`; solving `b ≤ f·p/(1−f)` the other way, at `f = 0.5` the ceiling is only 1x pot. Higher up: `D = 2b(1−f) − f·p` vanishes at `f = 0.8`, and `break_even_equity_to_bet` only returns `regime=below, e* = 1.4` from `f = 0.9` (measured: `f = 0.75 → above, e* = −100%`; `f = 0.8 → all`; `f = 0.9 → below`). **An overbet needs the opponent folding more than 80% before it enters the "weaker hands bet more eagerly" region, while a third-pot bet gets there at `f = 0.4`.** This is also why the `2 pot` block of `table.04-05.bet-break-even-equity` contains no sign flip at all across its declared fold rates.

## 生成表 / Generated tables

The table below is step one finished: chips behind, largest bet as a fraction of pot, largest standard size, stack-to-pot ratio (SPR), equity needed to commit, and whether a pot-sized bet already commits. It contains no notion of hand strength.

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

The air share demanded of the betting range rises with the size -- the ratio that capacity has to pay.

<!-- BEGIN AUTO:table.02-04.bluff-value-ratio -->
|    Size | Bluff share of betting range | Value : bluff |
|---:|---:|:---:|
| 1/4 pot |                       16.67% |     5 : 1     |
| 1/3 pot |                       20.00% |     4 : 1     |
| 1/2 pot |                       25.00% |     3 : 1     |
| 2/3 pot |                       28.57% |    2.5 : 1    |
| 3/4 pot |                       30.00% |   2.33 : 1    |
|  1x pot |                       33.33% |     2 : 1     |
| 3/2 pot |                       37.50% |   1.67 : 1    |
|  2x pot |                       40.00% |    1.5 : 1    |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#bluff_fraction_at_indifference`

<!-- generated by: tools/gen_tables.py from pokergto.odds::sizing_table -->
<!-- END AUTO:table.02-04.bluff-value-ratio -->

The overbet rung is cross-checked by an iterative algorithm that never sees the closed form (the `2.0000x pot` row):

<!-- BEGIN AUTO:table.08-04.solver-vs-algebra -->
|        Size | Solved defence | Algebraic MDF | Solved bluff share | Algebraic bluff share | Exploitability (chips/hand) |
|---:|---:|---:|---:|---:|---:|
| 0.5000x pot |         66.67% |        66.67% |             25.00% |                25.00% |              0.000001 chips |
| 0.3333x pot |         75.01% |        75.00% |             20.00% |                20.00% |              0.000014 chips |
| 1.0000x pot |         50.01% |        50.00% |             33.34% |                33.33% |              0.000043 chips |
| 0.7500x pot |         57.16% |        57.14% |             30.02% |                30.00% |              0.000098 chips |
| 2.0000x pot |         33.33% |        33.33% |             40.00% |                40.00% |              0.000008 chips |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `src/pokergto/solver/proofs.py#PUBLISHED_PROOFS`

<!-- generated by: tools/gen_tables.py from pokergto.solver.cfr::solve -->
<!-- END AUTO:table.08-04.solver-vs-algebra -->

## 实战牌局 / Live hands

**Hand 1 (`hand.04-03-the-size-that-does-not-exist`) -- 6-max cash, effective stacks 15bb. BTN opens 3bb, BB calls (pot 6bb). Flop `Kh7s3d`: BTN bets 2bb, BB calls (pot 12bb), 10bb left behind each. Turn `4c`. Hero is the BTN with `AdKc`.**

- Existence: `python -m pokergto spr --stack 10 --pot 12` → SPR `0.833`, equity needed to commit `0.3125`. A 2x-pot bet would be 24bb against 10bb -- **the size does not exist**; the largest bet is 10bb = `0.8333` pot, and that is the all-in.
- The real numbers: `python -m pokergto mdf --pot 12 --bet 10` → `MDF = 0.5455`, folds needed `45.45%`, not the `66.67%` printed on the ladder's 2x-pot row.
- Strength: `python -m pokergto equity "AdKc" "KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s" --board "Kh7s3d4c"` → `0.953095`, far above the `31.25%` a commit needs.
- Decision: shove 10bb. If BB defends this line using the "2x pot" quota of 33.33%, he is `21.2121` points short and air takes `0.212121 × 22 = 4.666667bb` per attempt (measured `ev_pure_bluff(12,10,2/3) = 4.666667`).

**Hand 2 (`hand.04-03-legal-overbet-on-a-capped-line`) -- heads-up, deep. Pot 20bb after a preflop 3-bet sequence, 60bb behind each. Turn `AsKsQhJd`. Hero holds `Td9d` (the ace-high straight, the nuts right now); villain's range is the teaching input `98s,76s,54s,65s,K9s,K8s,Q9s,J9s`.**

- Strength: `python -m pokergto equity "Td9d" "98s,76s,54s,65s,K9s,K8s,Q9s,J9s" --board "AsKsQhJd"` → `0.919545`; not 100%, because any spade on the river gives the suited hands a flush.
- Capacity: `is_capped` returns `True` for that defending line on `AsKsQhJd` (the range cannot even form a straight) and `False` for hero's. **Only the side that can threaten the nuts can afford a 2x-pot bet's 40% air.**
- Decision: bet 40bb (2x pot). Gains at each size's own MDF fold rate: 1/3 pot `4.597725bb` · pot `9.195450bb` · 2x pot `12.260600bb`; dropping to one third pot costs `7.994944bb` of regret per hand.
- Villain's arithmetic: `MDF = 20/60 = 33.33%`, so at most 884 of 1,326 combos may fold (442 continue); fold 80% and air makes `+8.000000bb` a hand here.

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

This is the defence floor against a 2x-pot bet: it needs to cover only `33.33%` of the 1,326 combos, i.e. 442 of them (the `total_combos` field of `range.04-02.mdf-floor-vs-two-pot.json`). Set beside `04-02`'s 994.5-combo picture and you have this lesson's claim in one glance: **the bigger the size, the fewer combos the opponent is required to defend.** The overbet's power is not that it forces folds -- it is that it raises the price `p+b` of the whole equation, so any defence shortfall settles at 60bb instead of 8bb.

## 为何成立、何时失效 / Why it works, when it breaks

**Assumptions that make it hold:** `S ≥ 2p` (the size exists); the range contains enough hands with `e > 1/2` to feed the linear value term; the betting range can produce 40% air backed by nut-tier combos; the opponent defends near MDF (otherwise you are discussing exploitation, not structure).

1. **`SPR < 2`.** The first two rows of `table.04-03.size-ceiling-by-stack` (8bb and 10bb behind a 6bb pot) have no 2x pot at all; at `SPR ≤ 2` the `Pot bet commits` column is true, betting pot leaves no room for a second pot-sized bet, and "choose a size" has become "commit".
2. **The capped side.** Where `is_capped` is true, your range cannot back the 40% air that the 1.5:1 requirement demands, so the threat is not credible -- the `AsKsQh` villain row of `table.03-02.capped-range-check` is that shape (capped, 92 combos, best hand a single pair).
3. **Short fold supply.** Air needs 66.67% of folds at 2x pot; at `f = 0.5` the ceiling is pot size and forcing 2x pot prices air at `−10.000000bb` (`p = 20`). Same ruler as `04-02` Example 2, this time measuring what you may *not* do.
4. **The raise option.** This model lets the defender only call or fold. Real overbet sizes invite raises, and a big bet is precisely the price at which raising pays -- no one-street model here contains a re-raise branch, so that part is **UNVERIFIED**.
5. **Risk aversion.** Committing chips is not linear in tournament payout terms; the threshold in `all_in_equity_needed` has to be repriced by ICM. Chapter 12.

## 陷阱 / Common mistakes

1. **Announcing a size the chips do not support.** With 12bb in the pot and 10bb behind, "2x pot" does not exist; defending it with the 2x-pot row's 33.33% quota lets air take `4.666667bb` per attempt. *Cost*: `4.666667bb` per hand (hand 1).
2. **Believing an overbet means "all nuts".** The last row of `table.02-04.bluff-value-ratio` demands value:bluff = 1.5:1 at 2x pot, i.e. 40% of the range is air. *Cost*: a range that cannot produce that 40% still needs the opponent to fold 66.67% for air to break even, and the value you failed to collect by shrinking is `7.994944bb/hand` (Example 2's regret).
3. **Carrying the small size's defence price over to the overbet.** The same 13.33-point shortfall: `+1.066667bb` for air against a third-pot bet (`p=6, b=2`) and `+8.000000bb` against a double-pot bet (`p=20, b=40`). *Cost*: a `6.933333bb` per-hand error in judgement -- set your defence frequency against a price of 60bb, not the 8bb you rehearsed with.

## 练习 / Drills

- Pot 6bb, 20bb behind: how many chips is a 2x pot? Is a pot-sized bet already committing? Check `python -m pokergto spr --stack 20 --pot 6` against the matching row of `table.04-03.size-ceiling-by-stack`.
- Find the `f` at which air breaks even on a 2x pot, then the `f` at which `regime` flips to `below`, and explain why the second is larger (hint: `N = 0` and `D = 0` are two different lines).
- Sweep `f = 0.4 … 0.8` at `p=20, b=40` with `python -c`, report the slope of air's EV, and compare it with the slope at one third pot -- the answer is `p+b`.
- Give two four-card boards, one where `is_capped` returns true and one where it returns false for the same range, and paste the command with its output.

## 自测清单 / Self-check

- [ ] Before discussing a size I compute `S/p`, and can name the SPR at which a 2x-pot bet starts to exist.
- [ ] I can state that a 2x pot has MDF `33.33%`, needs `66.67%` folds and carries a `40%` bluff share, with the table each comes from.
- [ ] I can use `Δ·(p+b)` to explain why the same defence hole costs 7.5 times more here.
- [ ] I can explain how capacity (nut combo counts) pays for the 1.5:1 mix, and why a capped range cannot.
- [ ] I can name one thing this section's model does not contain (the raise threat) and label it unverified instead of treating it as known.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number in this lesson is computed in this repository. No commercial solver output, third-party range chart or screenshot appears here.

| Content | Source type | Location |
|---|---|---|
| Size ceiling, SPR, equity needed to commit | `derived` | `data/gen/tables/table.04-03.size-ceiling-by-stack.json` (from `pokergto.spr`); each figure in Example 1 and hand 1 recomputed with `python -m pokergto spr/mdf` |
| 2x pot MDF / folds needed / air share | `derived` | `data/gen/tables/table.02-04.bluff-value-ratio.json`; `pokergto.odds#bluff_fraction_at_indifference` |
| Solver cross-check of the overbet frequencies | `derived` | the `2.0000x pot` row of `data/gen/tables/table.08-04.solver-vs-algebra.json`, gates in `src/pokergto/solver/proofs.py` |
| Regimes and critical `f` (`all` / `below`) | `derived` | `pokergto.ev#break_even_equity_to_bet`; `table.04-05.bet-break-even-equity` |
| Hand equity | `derived` | `python -m pokergto equity ...`, exact enumeration (`exact=true`) |
| Capped-range verdict | `derived` | `pokergto.theory.range_advantage#is_capped`; measured `villain capped True / hero capped False` on `AsKsQhJd` |
| The 442-combo defence quota | `derived` | `total_combos` in `data/gen/ranges/range.04-02.mdf-floor-vs-two-pot.json` |
| Every `f` value | declared input | **UNVERIFIED**: the fold rates in Examples 3-4 are conditions set by this repository, not population measurements. Every "it pays / it does not pay" here holds only for the stated `f`. |
| Re-raises and raise pressure against overbet sizes | **UNVERIFIED** | The one-street model here has bet/check and call/fold only, no re-raise branch, so no claim about it is made. |
| Enumerated ranges are not thinned by board cards | measured limitation | **UNVERIFIED**: range parsing keeps combos that collide with the board, so combo counts and nut shares are upper-biased (same note as in `04-01`). This lesson uses only the truth value of `is_capped`, never its counts, as a quota. |

## 术语 / Terms

| Abbreviation | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 超池下注 | overbet | any `b > p` needs `S > p`; a 2x pot needs `S ≥ 2p`, and at equality it is already an all-in |
| SPR | 筹码底池比 | spr | `S/p`, this lesson's first gate |
| — | 有效筹码 | effective-stack | `S`, the number that turns an idea of a size into chips |
| — | 容量 | capacity | how many nut-tier combos the range holds; it pays the air tax |
| — | 封顶范围 | capped-range | `is_capped` true: cannot afford the 40% air share |
| — | 坚果 | the-nuts | the top score in the evaluator's order, `0` steps of tolerance |
| MDF | 最低防守频率 | minimum-defense-frequency | `1/(1+s)`, which is `33.33%` at 2x pot |
| — | 可剥削度 | exploitability | the solver table's last column: `0.000008` chips/hand at 2x pot |
