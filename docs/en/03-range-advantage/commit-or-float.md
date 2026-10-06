# Commit or hold back: the two levels of commitment SPR creates

<!-- hands: 2 -->
<!-- terms: pot-commitment, float, spr, effective-stack, shove, required-equity, implied-odds, reverse-implied-odds, decision-plan, line, minimum-defense-frequency, call, fold, bet, pot, equity, regret, unverified-claim, dead-money, combos -->

## 本节目标 / Objectives

- Describe, with a computable line, the node in a line after which "fold later" is no longer a coherent plan, and name the formula that computes that line.
- Compute the two prices separately: the equity needed to continue one more street, and the equity needed to play out the rest of the stack behind you -- and explain why the first rises with bet size while the second falls with each node.
- State that the repository has **no** number for "how often the opponent fires a second barrel on the turn" or "how often they check it back", name the exact path that would turn one into `derived`, and invent no frequency in the meantime.

## 前置知识 / Prerequisites

- `03-07` SPR and the all-in threshold: this lesson walks that same expression street by street and watches what happens to it at every node.

## 核心原理 / The principle

At any node let `P` be the pot (dead money included) and `S` the chips behind you. Two levels of commitment, two thresholds:

```
one more street:  e_call    = B / (P + 2B)                  <- call this bet
committed:        e_commit  = S / (P + 2S) = SPR/(1+2*SPR)   <- play the rest of the stack
```

If your equity `e >= e_commit`, then "call now, decide later" is empty words: **there is no future left in which you may fold**, because every future all-in is already justified. That is pot commitment -- not a sunk-cost story, but a statement about the expectation of money still to be invested.

The band `e_call <= e < e_commit` is the only space in which a float can live: affordable to continue, but a plan that can only be cashed in by the opponent's behaviour on a later street. **That behaviour is not a quantity this repository computes** -- it is the one place in this lesson that must be labelled `reference` + UNVERIFIED.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     The two thresholds and the invariant below are derivations (implemented in `src/pokergto/spr.py` and `src/pokergto/odds.py`). Every node figure comes from a command printed here. Opponent future frequencies: no artifact, no source -- see the provenance section.

## 推导 / Derivation

**The invariant.** Follow the call-only path: after calling `B`, the pot is `P + 2B` and you have `S - B` behind. Substitute into the denominator of the commit threshold:

```
(P + 2B) + 2(S - B) = P + 2S
```

The `B` cancels. **Along a call-only path `P + 2S` is constant: it is the final pot when the money goes in.** So the commit threshold at node k is simply

```
e_commit(k) = (S - total called so far) / (P0 + 2*S0)     <- denominator fixed, numerator loses one B per call
```

strictly decreasing. That is the arithmetic body of "pot committed": **every call drags your own all-in threshold down one notch.**

Now the one-street threshold. Writing `f = B/P` it is `e_call = f/(1+2f)`, strictly **increasing** in `f`. Two curves running opposite ways must cross, and the crossing is the most useful formula in this lesson:

```
(S - fP)/(P + 2S) = f/(1+2f)      ->      2f^2 + 2f - SPR = 0      ->      f* = (sqrt(1 + 2*SPR) - 1) / 2
```

(substitute `S = SPR*P` and collect; the square root step cannot fail because `1 + 2*SPR > 0` always). `f*` means: **above this size the one-street bar is already higher than the commit bar** -- any hand that may call may also shove, and the third action called "float" does not exist arithmetically. Three depths, computed with `python -c` (`pokergto.spr.spr`, `all_in_equity_needed_from_spr`, `pokergto.odds.equity_needed_to_call`):

- 40bb 3-bet pot (`P = 16.5, S = 32.5`, SPR `1.9697`): `f* = 0.611237` pot, both bars meeting at `27.5026%`.
- 100bb 3-bet pot (SPR `5.6061`): `f* = 1.247292` pot, meeting at `35.6921%`.
- 100bb single-raised pot (`P = 5.5, S = 97.5`, SPR `17.7273`): `f* = 2.518880` pot, meeting at `41.7188%`.

The third figure is the proof of the sentence "floating is a deep-stack concept": the standard size ladder (`pokergto.odds.STANDARD_SIZES`) stops at 2x pot, and `2.5189 > 2`, so at that depth **every size on the ladder still satisfies `e_call < e_commit`** and calling remains distinct from committing. At the 40bb depth a two-thirds-pot bet (`0.6667 > 0.61124`) has already crossed.

**The inverse question** -- "my equity only pays for part of the stack" -- is answered by `pokergto.spr.max_profitable_commit_fraction`. Solving `S'/(P + 2S') = e` gives `S' = eP/(1 - 2e)`, and dividing by `S = SPR*P`:

```
committable fraction = e / ((1 - 2e) * SPR)      capped at 1
```

The only step able to fail is `1 - 2e`: as `e -> 1/2` it divides toward zero, the same divergence as `03-07`'s inverse. So "above 50% you may commit everything" reappears here, and every hand below 50% owns a fraction strictly smaller than 1.

## 直觉 / Intuition

Think of a street as two divisions running toward each other:

- the **one-street** bar only looks at what this bet costs, and it rises with the size;
- the **commit** bar looks at how much you can still lose, and it falls with every call.

The gap between them is exactly the width of "I may continue, but I have not committed". Deep, the gap is wide (100bb single-raised pot: between 20.00% and 48.6284%); short, it narrows and even inverts (40bb 3-bet pot against two thirds pot: 28.5714% versus 26.3804%).

**The word "committed" should not evoke dead money.** In every expression above, the part of `P0` and `S0` already invested never appears on its own; what appears is always "how much is left / how big the final pot is".

## 算例 / Worked examples

**Example 1 -- a 40bb 3-bet pot: three divisions going downhill.** CO opens 2.5, BTN 3-bets to 7.5, CO calls; pot `16.5` (1.5 of it dead money), `32.5` behind each.

- Flop start: `P = 16.5, S = 32.5` -> SPR `1.9697`, commit bar **39.8773%**, 18.75% of the stack already in.
- After calling a one-third-pot `5.5`: `P = 27.5, S = 27.0` -> SPR `0.9818`, commit bar **33.1288%**; this street alone cost **20.00%**; 32.50% of the stack in.
- After calling a turn half-pot `13.75`: `P = 55.0, S = 13.25` -> SPR `0.2409`, commit bar **16.2577%**; this street alone costs **25.00%**; **66.875%** of the stack in.

Every figure comes from `python -c` calling `pokergto.spr.spr / all_in_equity_needed_from_spr` and `pokergto.odds.equity_needed_to_call`. Check the invariant: the denominator is `16.5 + 2*32.5 = 81.5` at all three nodes, while the numerator runs `32.5 -> 27.0 -> 13.25`, i.e. exactly the two calls `5.5 + 13.75` subtracted. At the third node an all-in needs 16.2577% -- **3.74 points less** than the flop call needed.

**Example 2 -- a 100bb big-blind defence: barely moves.** BTN opens 2.5, BB calls (the SB's 0.5 is dead money): `P = 5.5, S = 97.5` -> SPR `17.7273`, commit bar **48.6284%**. BB calls a one-third-pot `1.8333` -> `P = 9.1667, S = 95.6667` -> SPR `10.4364`, bar **47.7140%**, while the street itself needed only **20.00%**. BB calls a turn pot-sized `9.1667` -> `P = 27.5, S = 86.5` -> SPR `3.1455`, bar **43.1421%**, and only **13.5%** of the stack is in. **The same two calls cut 23.62 points off the bar in the 40bb line and 5.49 points off it here** (39.8773-16.2577 versus 48.6284-43.1421).

**Example 3 -- a hand sitting in the gap.** `python -m pokergto equity "T9o" "AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT" --board "As9s5d" --json` gives **0.221839**.

- Right at the node where BTN has just bet one third pot and BB has not called: the one-street bar is **20.00%** (cleared by 2.1839 points, `ev_call(5.5, 5.5/3, 0.221839) = +0.200191` chips), the commit bar is **48.6284%** (`SPR = 17.7273`), and `max_profitable_commit_fraction(17.7273, 0.221839) = 0.022494` -- the hand pays for **2.25%** of the chips behind it.
- After calling (`SPR = 10.4364`) the bar falls to **47.7140%** and the affordable share rises to `0.038209` (**3.82%**); after calling a turn pot-sized bet (`SPR = 3.1455`) the bar is **43.1421%** and the share `0.126772` (**12.68%**).

**Every call pushes the bar down and the affordable share up**, yet the distance between the two stays above 20 points all the way (48.6284 / 47.7140 / 43.1421 against 22.1839 in hand).

**Example 4 -- how a size closes the gap (same node, four flop bets).** 40bb 3-bet pot, `P = 16.5, S = 32.5`:

- one third pot `5.5`: street 20.00%, commit after calling 33.1288%;
- half pot `8.25`: street 25.00%, commit 29.7546%;
- two thirds pot `11.0`: street **28.5714%**, commit **26.3804%** <- the gap has inverted;
- pot `16.5`: street 33.3333%, commit 19.6319%.

The conclusion is computed, not a matter of taste: **at this depth a bet of two thirds pot or more abolishes the option "call and see"** (the bar to call is above the bar to commit), and the crossover is the `f* = 0.611237` derived above.

**Example 5 -- what a probe owes in folds (a property of the size, not of the pot).** Take the complement of the MDF column of `python -m pokergto odds --pot 1`: one third pot needs 25% folds (MDF 75%), half pot 33.33% (MDF 66.67%), two thirds 40% (MDF 60%), pot 50% (MDF 50%). So probing the turn half pot at Example 2's node requires the opponent to give up in one third of cases -- **that third follows from the size, not from anything measured on a player.**

**Example 6 -- implied odds are the float's ledger, and a line of it is blank.** At the same turn node (`P = 9.1667, B = 9.1667`): `pokergto.spr.implied_odds_break_even_equity` says that if another 20 is expected to be won later, the bar falls from **33.3333%** to **19.2982%** -- which is how `T9o`'s 22.1839% gets there; if instead 15 is expected to be paid off, `reverse_implied_odds_penalty` gives **87.8788%**. One expression, two fates, and the only difference is that future amount -- the quantity the next section marks UNVERIFIED.

## 生成表 / Generated tables

The one-street bar, MDF and "the folds a bluff needs", at `P = 1`:

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

Break-even equity between betting and checking, solved by `pokergto.ev.break_even_equity_to_bet`; the `Residual` column is what re-substitution leaves behind:

<!-- BEGIN AUTO:table.04-05.bet-break-even-equity -->
|    Size | Fold frequency f | MDF at this size | Break-even equity e* | Regime | Residual |
|---:|---:|---:|---:|---:|---:|
| 1/3 pot |           25.00% |         75.0000% |              0.0000% |  above |        0 |
| 1/3 pot |           40.00% |         75.0000% |                    - |    all |        - |
| 1/3 pot |           50.00% |         75.0000% |            200.0000% |  below |        0 |
| 1/3 pot |           60.00% |         75.0000% |            140.0000% |  below |        0 |
| 1/3 pot |           75.00% |         75.0000% |            114.2857% |  below |        0 |
| 1/2 pot |           25.00% |         66.6667% |             25.0000% |  above |        0 |
| 1/2 pot |           40.00% |         66.6667% |            -50.0000% |  above |        0 |
| 1/2 pot |           50.00% |         66.6667% |                    - |    all |        - |
| 1/2 pot |           60.00% |         66.6667% |            200.0000% |  below |        0 |
| 1/2 pot |           75.00% |         66.6667% |            125.0000% |  below |        0 |
| 3/4 pot |           25.00% |         57.1429% |             35.7143% |  above |        0 |
| 3/4 pot |           40.00% |         57.1429% |             10.0000% |  above |        0 |
| 3/4 pot |           50.00% |         57.1429% |            -50.0000% |  above |        0 |
| 3/4 pot |           60.00% |         57.1429% |                    - |    all |        - |
| 3/4 pot |           75.00% |         57.1429% |            150.0000% |  below |        0 |
|     pot |           25.00% |         50.0000% |             40.0000% |  above |        0 |
|     pot |           40.00% |         50.0000% |             25.0000% |  above |        0 |
|     pot |           50.00% |         50.0000% |              0.0000% |  above |        0 |
|     pot |           60.00% |         50.0000% |           -100.0000% |  above |        0 |
|     pot |           75.00% |         50.0000% |            200.0000% |  below |        0 |
|   2 pot |           25.00% |         33.3333% |             45.4545% |  above |        0 |
|   2 pot |           40.00% |         33.3333% |             40.0000% |  above |        0 |
|   2 pot |           50.00% |         33.3333% |             33.3333% |  above |        0 |
|   2 pot |           60.00% |         33.3333% |             20.0000% |  above |        0 |
|   2 pot |           75.00% |         33.3333% |           -100.0000% |  above |        0 |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.ev#break_even_equity_to_bet`

<!-- generated by: tools/gen_tables.py from pokergto.ev::break_even_equity_to_bet -->
<!-- END AUTO:table.04-05.bet-break-even-equity -->

The column most often misread here is `Fold frequency f`: **it is a declared input, not a measurement of any population** (the artifact records exactly that in `provenance.assumptions`). Rows with `Regime = below` are the bluff region, where weaker hands should bet -- produced by the denominator changing sign, not by a typo. And when `f` equals the size's own indifference rate the threshold lands on zero (`1/3 pot` at `f = 25.00%` gives `e* = 0.0000%`), which is `02-03`'s MDF read from the bettor's side.

## 实战牌局 / Live hands

**Hand 1 (`hand.03-08-adkc-40bb-commit`) -- three nodes, all above the bar, so "and see" never existed.**

Seats and money: 6-max, everyone 40bb. CO opens 2.5 with `AdKc`, BTN 3-bets to 7.5, CO calls. Flop `Kh7s3d`, pot `16.5`, CO has `32.5` behind (SPR `1.9697`, commit bar **39.8773%**).

- `AdKc` holds **79.4731%** against BTN's declared 3-bet range `"AA,KK,QQ,JJ,TT,98s,AKs,AQs,AKo,AQo"` (`python -m pokergto equity "AdKc" "AA,KK,QQ,JJ,TT,98s,AKs,AQs,AKo,AQo" --board "Kh7s3d" --json`). Twice the flop bar, so the question was never "call or not" but "with which size do I move the rest in".
- BTN bets 5.5 (one third pot): `ev_call(16.5, 5.5, 0.794731) = +16.3551`. If BTN instead bets 11.0 (two thirds), the commit bar after the call drops to 26.3804% and `ev_call(16.5, 11.0, 0.794731) = +19.5971`, higher still. This is not "bigger bets are more welcome": it is algebra -- `ev_call = e*P + B*(2e - 1)` increases in `B` exactly when `e > 1/2`, the 50% ceiling of `03-07` reappearing a second time.
- Turn `2c`, BTN barrels 13.75 into 27.5: street bar 25.00%, commit bar 16.2577%. 79.47% dwarfs both, and `ev_call(27.5, 13.75, 0.794731) = +29.9602`. The price of a "pot-controlled" check here is those 29.96 chips -- roughly half the pot handed to an opponent for a decision that should not exist.
- The river leaves only 13.25 behind into a pot of 55. **This line stopped having a "hold back" branch on the flop**, because the commit bar (39.8773%) was already nearly 40 points below the equity in hand (79.4731%).

**Hand 2 (`hand.03-08-t9o-float-unpriced`) -- affordable to call, impossible to price the plan.**

Seats and money: 100bb. BTN opens 2.5, BB calls with `T9o` (SB folds, its 0.5 is dead money). Pot `5.5`, BB has `97.5` behind, SPR `17.7273`, commit bar 48.6284%. Flop `As9s5d`, BTN bets one third pot `1.8333`.

- One street: the bar is **20.00%** and `T9o` holds **22.1839%** against BTN's declared betting range `"AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT"` (`python -m pokergto equity "T9o" "AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT" --board "As9s5d" --json`), giving `ev_call = +0.200191`. **This half of the float is computable, and it is positive.**
- Commitment: at that same still-uncalled node the bar is **48.6284%**, i.e. 26.4445 points above the 22.1839% in hand, and `max_profitable_commit_fraction(17.7273, 0.221839) = 0.022494` says it more bluntly: 2.25% is what the hand buys. So "and if he fires again?" needs an answer in advance.
- Turn `2c`, BTN bets pot `9.1667`: the bar jumps to **33.3333%** and `ev_call(9.1667, 9.1667, 0.221839) = -3.066094`. **Only future money rescues it**: if 20 more is expected to be won, the bar is 19.2982% (Example 6). How often BTN fires that second barrel, and how often he checks back so a probe can take the pot, are two frequencies for which this repository has no artifact and no command. **That is the defining gap of a float**, not a section this lesson forgot to finish.
- The computable half continues: BB's turn probe at half pot needs **33.33%** folds (Example 5). So the honest sentence is "if BTN continues less than two thirds of the time on this line, the probe has a price" -- **the condition is unverified, the price is derived.**

## 范围图 / Range chart

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

The chart is the **MDF quota** for a half-pot bet: combos filled in strength order until they cover `884.0` of the 1,326 (66.67%). It answers "how much must continue"; this lesson answers "how far continuing reaches". The half-pot one-street bar is always **25.00%** (independent of pot size, per the size table above), while the commit bar depends entirely on SPR: the same 30%-equity hand is merely "call one more street" at SPR `1.9697` (bar 39.8773%) and already committed at SPR `0.2409` (bar 16.2577%) -- same hand, same line, two correct answers, because the two questions are different.

So the chart cannot be the whole decision plan: **the quota says how many, the thresholds say how far, and the next step needs a model of the opponent.** What the chart does not contain -- which combos should raise -- is chapter 13's subject of exploitable deviation.

## 为何成立、何时失效 / Why it works, when it breaks

**Assumptions:** chips are linear; after a call the only future actions are fold, call, shove; and `S > 0` -- once `S <= B` the phrase "call and see" abolishes itself and only fold-or-shove remains, which is the operational definition of being committed.

**Where it must be rewritten:**

1. **Your shove can be folded.** Then `e_commit` is a bound on a bound and the tool becomes `break_even_equity_to_bet(pot, bet, f)`: with `f > 0` the bar sits below the pure-showdown value. Example: `break_even_equity_to_bet(27.5, 27.0, 0.35)` returns regime `above` with threshold **31.1089%**, whereas the showdown-style commit bar at that same node is 33.1288%.
2. **Equity is not constant.** Both bars above are statements about the *average* runout; real equity moves with the turn and river, so "committed on the flop" must not be read as "committed behind any two cards". Runout structure is `03-03`, nut capacity multiway is this chapter's `03-09`.
3. **Multiway pots.** A shove has to beat two distributions at once, which changes what `e` means (`03-09` and `07-01`).
4. **ICM.** Elimination risk makes the money behind you non-linear and the downhill curves invalid (chapter 12).
5. **The unverified cell: future frequencies.** A float's entire EV comes from the opponent's behaviour on a later street. Every game this repository solves is one street (`kuhn` and `one_street_bluff_catcher` in `src/pokergto/solver/games.py`, registered in `pokergto.solver.proofs.PUBLISHED_PROOFS`), so there is no second-barrel frequency to compute. **The exact path to `derived`:** add a two-street game tree in `games.py` (flop bet/call, then a turn bet), give it an anchor entry in `PUBLISHED_PROOFS` (`tools/run_solver.py` refuses a game without one), solve it into `data/gen/solver/solver.<game>.json`, and emit a `table.*` artifact through `tools/gen_tables.py`. Only after that may this lesson print a frequency.

## 陷阱 / Common mistakes

1. **Explaining commitment with sunk cost.** The expression has no "already invested" term: the third node of Example 1 is `13.25/81.5 = 16.2577%`, all of it "money left over final pot". *Cost:* the sunk-cost story is exactly what makes you call `T9o` on the turn of Example 2, where `ev_call(9.1667, 9.1667, 0.221839) = -3.066094` per hand -- and "I already called once" appears in that number zero times.
2. **Treating the one-street bar as the ticket for the whole line.** At the node where BTN has just bet one third pot, 20.00% and 48.6284% are **28.6284 points** apart (Example 3). *Cost,* as an exact ratio: `max_profitable_commit_fraction(17.7273, 0.221839) = 0.022494` -- every chip invested beyond that buys equity the hand does not own; conversely, playing a hand that covers 2.25% of a stack as a commitment means paying a 48.6284% price at SPR `17.7273`.
3. **Inventing an opponent frequency for the float.** The usual sentence is "he gave up 60% of the time on the turn after a flop c-bet, so the float profits". No command in this repository produces that 60%, so the sentence is fiction rather than a strategy conclusion. *Cost* is expressible as sensitivity, not as a fixed number: a half-pot probe needs 33.33% folds (Example 5); at a true 25% the same action is `ev_pure_bluff(9.1667, 4.5833, 0.25) = -1.1458` per hand; at exactly the derived indifference rate it is `ev_pure_bluff(9.1667, 4.5833, 0.333333) = +0.000029` (air is indifferent -- the third appearance of `02-03`'s equation); at 40% it becomes `+0.9167`. **The verdict hangs entirely on the unverified input; the arithmetic stayed clean throughout.**

## 练习 / Drills

- In Example 1's line, replace the flop bet with half pot: what are the SPR and commit bar after the call? (`24.25/33.0` -> SPR `0.7348`, bar **29.7546%**, street bar 25.00%)
- Verify the invariant with `python -c`: compute `P + 2S` on the 40bb line, then again after a 5.5 call. (Both `81.5`)
- How far does the commit bar fall by the third node of the 40bb line, and is it now below the flop's calling bar? (**16.2577%** versus 20.00% -- lower, which is why "call then fold" is incoherent on that line)
- The crossover: with SPR `1.9697`, what is `f*`? (`(sqrt(1+2*1.9697) - 1)/2 = 0.611237` pot, where both bars equal `27.5026%`) And with SPR `17.7273`? (`2.518880` pot -- above the standard ladder)
- Build a table with `max_profitable_commit_fraction` over `SPR in {1, 2, 4}` and `e in {0.30, 0.35, 0.40}`; find the cells that hit 1 and relate them to the 50% ceiling. (`SPR 1, e 0.35 -> 1.0`; `SPR 2, e 0.35 -> 0.5833`; `SPR 4, e 0.35 -> 0.2917`; `SPR 1, e 0.30 -> 0.75`)

## 自测清单 / Self-check

- [ ] I can prove that `P + 2S` is invariant along a call-only path and write the commit threshold at any node from it.
- [ ] I can state the two opposite directions of the street bar and the commit bar, and compute the size `f*` where they meet.
- [ ] Given an equity and an SPR I can compute the fraction the hand pays for (`e/((1-2e)*SPR)`) and explain why it diverges at `e = 1/2`.
- [ ] I can separate "commitment is forward-looking arithmetic" from sunk cost, and price both with `ev_call` at two concrete nodes.
- [ ] I can name which input in this lesson is UNVERIFIED, why the engine cannot produce it, and which three files would have to change to make it derived.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->

| Content | Source type | Location / the command that produced it |
|---|---|---|
| One-street bar `B/(P+2B)` | `derived` | `src/pokergto/odds.py#equity_needed_to_call`; `table.02-03.mdf-vs-sizing` |
| Commit bar, invariant, crossover `f*` | `derived` | `src/pokergto/spr.py#all_in_equity_needed_from_spr`; `python -c` (every figure in Examples 1-4) |
| Committable fraction | `derived` | `src/pokergto/spr.py#max_profitable_commit_fraction` (0.022494, 0.038209, 0.126772, 0.2917, 0.5833, 0.75, 1.0) |
| Bet-vs-check thresholds and regimes | `derived` | `src/pokergto/ev.py#break_even_equity_to_bet`; `table.04-05.bet-break-even-equity` (31.1089% at f = 0.35) |
| Fold requirements (25% / 33.33% / 40% / 50%) | `derived` | complement of the MDF column of `python -m pokergto odds --pot 1` |
| Hand equities 22.1839% (`T9o`), 79.4731% (`AdKc`) | `derived` | `python -m pokergto equity ... --json`, `exact: true` |
| EVs: +0.200191, -3.066094, +16.3551, +19.5971, +29.9602, -1.1458, +0.000029, +0.9167 | `derived` | `python -c` calling `pokergto.ev.ev_call / ev_pure_bluff` |
| Implied 19.2982% / reverse 87.8788% | `derived` (given a future amount) | `python -c` calling `pokergto.spr.implied_odds_break_even_equity / reverse_implied_odds_penalty` |
| **Opponent future bet / check / fold frequencies, including the amounts 20 and 15 themselves** | `reference` + **UNVERIFIED** | No such artifact exists: `src/pokergto/solver/` registers one-street games only; path in item 5 above. Every sentence depending on them is written conditionally. |
| Declared opponent ranges `"AA,KK,QQ,JJ,TT,98s,AKs,AQs,AKo,AQo"`, `"AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT"` | `reference` + **UNVERIFIED** | Illustrative inputs, neither solved nor measured; converting them into a solved decision needs a spot artifact in `data/src` plus `tools/gen_tables.py` |

No commercial solver output, no transcribed range chart, no screenshots, and no sentence of the form "solvers say" anywhere in this lesson.

## 术语 / Terms

<!-- terms: pot-commitment, float, spr, effective-stack, shove, required-equity, implied-odds, reverse-implied-odds, decision-plan, line, minimum-defense-frequency, call, fold, bet, pot, equity, regret, unverified-claim, dead-money, combos -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 套池 | pot commitment | `e >= S/(P+2S)`: every future all-in is justified, regardless of what is already in |
| — | 试探性跟注 | float | clears the street bar, not the commit bar, and needs a future frequency |
| SPR | 筹码底池比 | stack-to-pot ratio | the division recomputed at every node |
| — | 有效筹码 | effective stack | the smaller stack behind, the `S` of the invariant |
| — | 全下 | shove | the action that makes `P + 2S` the final pot |
| — | 所需胜率 | required equity | the one-street bar `B/(P+2B)` |
| — | 隐含赔率 | implied odds | future money won lowers the bar: `B/(P+2B+future)` |
| — | 反向隐含赔率 | reverse implied odds | future money paid raises the bar |
| — | 决策计划 | decision plan | the cross-street arrangement; this lesson shows when it collapses into one action |
| — | 行动线 | line | an ordered list of actions; a node is one division inside it |
| — | 最低防守频率 | minimum defense frequency | the complement of what a probe needs, Example 5 |
| — | 遗憾值 | regret | chips lost relative to the best action (defined in chapter 08) |
| — | 死钱 | dead money | changes `P`, hence the bar, and nothing else |
| — | 组合数 | combos | the weighting unit of the quota chart |
| — | 未核验声明 | unverified claim | the class of conditional sentences this lesson uses for future frequencies |
