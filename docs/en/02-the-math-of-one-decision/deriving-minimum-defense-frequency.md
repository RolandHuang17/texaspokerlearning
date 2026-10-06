# Minimum defense frequency: why pot/(pot+bet)

<!-- hands: 2 -->
<!-- terms: mdf, pot, bet, fold, call, bluff, value-hand, equity, combos, range -->

## 本节目标 / Objectives

- Re-derive `MDF = pot/(pot+bet)` from the single condition "a pure bluff must be indifferent", instead of memorising it.
- Given any bet size, immediately state how often the defender must continue and how often a bluff must work.
- Explain that MDF constrains a **total frequency**, does not tell you **which hands** supply it, and name where that gap gets exploited.

## 前置知识 / Prerequisites

- `02-01` Break-even percentage: a gamble risking `R` to win `W` needs `R/(R+W)` to break even.
- `02-02` Pot odds to call frequency: the algebra between a pot and a bet facing you.

## 核心原理 / The principle

Facing a bet, the lower bound on how often you must continue is

```
MDF = pot / (pot + bet)
```

where `pot` is the money in the middle **before** the bet and `bet` is the amount added. This is a `derived` claim: it follows from one condition -- a pure bluff must be indifferent -- and depends on no solver, no chart, no one's authority.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Derivation: the next section. Generated table: `tools/gen_tables.py` -> `data/gen/tables/table.02-03.mdf-vs-sizing.json`.

## 推导 / Derivation

Let the pot be `P` and the bet `B`. Consider the bettor holding a hand that can **never** win -- pure air.

- With probability `f` everyone folds, and the bluff wins the pot uncontested: `+P`.
- With probability `1 − f` somebody defends, and air loses the money it put in: `−B`.

Indifference (the bluff's expected value is exactly zero):

```
f·P − (1 − f)·B = 0
f·(P + B) = B
f = B / (P + B)                    ← the fold frequency a bluff needs
```

The defender's continuation frequency is the complement:

```
MDF = 1 − f = 1 − B/(P+B) = P/(P+B)
```

No new assumption entered between those lines: it is the same equation read from the other side. **That is precisely why MDF and "equity needed to call" get conflated. They are different quantities: one is the complement of a fold frequency, the other is `B/(P+2B)`.**

Defending below the floor is punished. At `P = 1, B = 0.5`, if you defend only 50% instead of `MDF = 66.7%`, any two cards the opponent decides to bluff with earn `0.5·1 − 0.5·0.5 = +0.25` per attempt. The cards are irrelevant; your frequency is the gift.

## 直觉 / Intuition

Read MDF as one sentence in English: **"the share I fold must not exceed the point where your empty hands start printing money."**

- The smaller the bet, the lower the fold frequency it needs, so the more you must defend: one third pot demands 75%.
- The bigger the bet, the more it must be believed, so the less you must defend: two times pot demands only 33.3%.
- Sizing and defense are two sides of one equation. This is arithmetic, not a taste argument about "aggressive" or "passive" players.

Mental model: MDF is a **floor**, not a plan. Above it you may build anything -- raise with the strong part, call with draws, call with the suit that blocks the nut flush. Below it you are not deciding, you are subsidising.

## 算例 / Worked examples

**Example 1 -- a one third pot continuation bet on the flop.** `P = 6.5`, `B = 2.17`.
`MDF = 6.5 / 8.67 = 0.75`. Of the combos your defending range holds, at least 75% must continue (call or raise); at most 25% may fold.

**Example 2 -- a pot-sized bet on the turn.** `P = 12, B = 12`, so `MDF = 12/24 = 0.50`.
Defend 40% and an opponent's air bet earns `0.6·12 − 0.4·12 = +2.4` per attempt: they win 2.4 chips by betting without looking at their cards.

**Example 3 -- a two times pot overbet on the river.** `P = 20, B = 40`, so `MDF = 20/60 = 0.333`.
This row is routinely misread as "overbets are terrifying". The opposite is true: the overbet must be believed *less* often, so your defense quota drops to a third. Your job is not to guess whether they dare; it is to hold the line at 33.3%.

**Example 4 -- side by side with the call threshold.** `P = 10, B = 5`:
`MDF = 10/15 = 66.7%` while equity needed to call is `5/(10+2·5) = 25%`.
One answers "what share of my range continues", the other answers "what does this hand need in order to continue". Two different questions in the same spot, and confusing them is the most common arithmetic error among self-taught players.

## 生成表 / Generated tables

The table below is computed by `pokergto.odds.sizing_table` with `P = 1`. It was not transcribed from a book or a website:

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

The same frequencies have been verified from an entirely independent direction: treat them as the equilibrium of a game and let CFR solve it.

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

**Why two tables**: the left-hand numbers come from one line of algebra; the right-hand numbers come from an iterative algorithm that does not know the answer. Their agreement means neither side is independently wrong -- if `odds.py` or CFR were broken, generation itself fails (`adr/0002`).

## 实战牌局 / Live hands

**Hand 1 (`hand.02-03-c-bet-defense`) -- 6-max cash. CO opens 2.2x, BTN calls. Flop `Kh7s3d`, CO bets one third pot.**

You are on the button with `Jd9d`: an open-ended straight draw plus two overcards. Pot 6.5, bet 2.17.

- By size: `MDF = 75%`. The BTN's range facing a continuation bet must keep 75% of its combos in the fight.
- By hand: calling 2.17 into `8.67 + 2.17` needs `2.17/10.84 = 20.0%` equity. Against CO's value-plus-bluff range `Jd9d` sits around 24-30% (compute it: `poker equity "Jd9d" "88+,ATs+" --board "Kh7s3d"`).
- Decision: call. Not because the draw looks pretty, but because there is a measured margin between the equity required and the equity held.

**Hand 2 (`hand.02-03-river-overbet`) -- heads up. River `AsKd7h5c2s`. Opponent overbets two times pot.**

Pot 20, bet 40. You hold `JhTh`, which beats nothing but air.

- `MDF = 20/60 = 33.3%`: a third of your range must continue.
- Your hand is a textbook bluff-catcher, which is exactly the class of hand that decides whether the opponent's bluffs profit. It therefore belongs near the **front** of the defense queue; folding it means spending your quota on weaker combos instead.
- Equity needed to call: `40/(20+80) = 33.3%`, i.e. bluffs must make up a third of their betting range before this is a call. Compare that against the 40% bluff share the sizing table lists for a two times pot bet, and the margin is positive: call.

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

The chart above is the **MDF floor** for a half-pot bet: combos filled in strength order until they cover `MDF = 66.7%` of the 1,326. `tools/gen_ranges.py` produces it from `pokergto.odds.minimum_defense_frequency`, with `provenance.kind = derived`.

How to read it: **this is a quota, not a plan.** It says how many combos must continue. Which combos do depends on your hand distribution, position and later streets. A real solver's defense range departs from this shape -- it raises part of it, and it defends with blockers rather than with the raw second-best hand. Those departures have reasons; chapter 13 is about them.

## 为何成立、何时失效 / Why it works, when it breaks

**Assumptions that make it hold:** both players respond to what the other does; an opponent will punish defense below the floor; folding forfeits the pot.

It stops being the number to execute in these situations:

1. **Multiway pots.** A bluff must beat *everyone*. If each defender continues independently at rate `d`, then `(1 − d)^N = B/(P+B)`, so
   `d = 1 − (B/(P+B))^(1/N)`. The exponent is `1/N`, which returns this section's formula at `N = 1` -- that fallback is the self-check. For a pot-sized bet with two opponents each defends 29.3%, while the joint defense stays 50%. **Per-player defense falls as players are added; the table's total defense does not.** See `07-01`, and note that the combined formula assumes independent defenders, which card removal makes an approximation.
2. **When the defender can raise.** MDF is derived for a call/fold choice. With raises available, part of the punishment moves to raising, so the *calling* frequency can sit lower while total defense stays at the floor. Misreading this is the most common complaint about solver charts.
3. **Risk aversion (tournaments).** Chips are not linear in utility. Near the money, defending exactly to MDF can leave you eliminated by a coin flip you were mathematically "required" to take; ICM-priced defense below MDF is rational, and lets the opponent's air profit on purpose. Chapter 12.
4. **Opponents who do not punish.** MDF is the floor for *not being exploited*, not the choice that *maximises your win rate*. Against a player who never bluffs, defending below MDF costs nothing and saves money. Deviating against a population is chapter 13's subject.
5. **Card removal.** The multiway formula assumes independence. Real deals couple the ranges -- your spades remove the flushes they can hold -- so it is an approximation. The artifacts record that in `provenance.assumptions` rather than hiding it.

## 陷阱 / Common mistakes

1. **Confusing `MDF` with the equity needed to call.** The denominators differ: `P/(P+B)` versus `B/(P+2B)`.
   *Cost*: at a one third pot, the correct defense is 75%, while "I only need 25% equity" gets misread as "I may fold 75%". Run `poker mdf --pot 6 --bet 2` and `poker odds` once each; a minute of arithmetic ends the confusion permanently.
2. **Judging the range by hand classes instead of combos.** MDF is combo-weighted: `AKo` is 12 combos, `AKs` is 4, `AA` is 6. Averaging over the 169 classes biases every aggregate you build on it.
   *Cost*: a range that "defends about 70%" by class count can be 55% by combos, which pays an opponent `+0.15` pot shares per bluff with any two cards. Check with `poker range "22+,ATs+"`, which prints the combo total.
3. **Reusing the heads-up MDF in a multiway pot.** Defending 50% each against three opponents yields joint defense `1 − 0.5² = 75%`, a quarter of the pot over-defended into value bets.
   *Cost*: see `07-01`'s generated table -- the magnitude is enough to keep a "solid" player net negative in multiway pots alone.

## 练习 / Drills

- From memory: the MDF and required fold frequency for `1/4, 1/3, 1/2, 2/3, 3/4, 1, 1.5, 2` times pot. Verify with `poker odds`.
- Four-way pot, `P = 24, B = 12`: what does each defender need? (Hint: a cube root, not a quarter.)
- Inverse: if an opponent betting into a pot of 10 needs you to defend 45% for their bluffs to break even, what size did they use?
- Re-run the solver from chapter 08 (`poker solve toy1street --sizes 0.5`) and confirm it converges to 66.7% on its own.

## 自测清单 / Self-check

- [ ] I can derive `MDF = P/(P+B)` from bluff indifference inside a minute.
- [ ] I can state which question MDF answers and which question the call threshold answers.
- [ ] I know MDF is combo-weighted, and can verify a range's true defense share.
- [ ] I can explain why per-player defense falls multiway while total defense does not.
- [ ] I can list three situations where defending below MDF is still correct.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number here is computed in this repository. No range chart or strategy output from a commercial solver or paid course is used anywhere in this lesson:

| Content | Source type | Location |
|---|---|---|
| MDF formula | `derived` | `src/pokergto/odds.py#minimum_defense_frequency`; derivation above |
| Sizing table | `derived` | `data/gen/tables/table.02-03.mdf-vs-sizing.json` |
| Solver cross-check | `derived` | `data/gen/solver/*.json`, gates in `src/pokergto/solver/proofs.py` |
| MDF floor chart | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` (assumptions in `provenance.assumptions`) |
| Independence of multiway defenders | `reference` + **UNVERIFIED** | Card removal breaks it; the three-player fixed-action model converts it to `derived` at milestone M5 |

## 术语 / Terms

<!-- terms: mdf, pot, bet, fold, call, bluff, value-hand, equity, combos, range -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| MDF | 最低防守频率 | minimum defense frequency | `P/(P+B)`; not "how I would play" |
| — | 底池 | pot | money in the middle **before** the bet |
| — | 下注 | bet | the amount added, `B` |
| — | 组合 | combos | the weighting unit: `AKo` 12, `AKs` 4, `AA` 6 |
| — | 胜率 | equity | a different quantity from MDF; see mistake 1 |
