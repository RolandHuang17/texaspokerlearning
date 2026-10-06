# Range advantage means something different heads-up and three-way

<!-- hands: 2 -->
<!-- terms: multiway, range-advantage, nut-advantage, capacity, the-nuts, heads-up, independent-defender-assumption, removal-effect, minimum-defense-frequency, equity-advantage, bluff-to-value-ratio, required-equity, combos, range, board, equity, call, fold, bet, pot, bluff, unverified-claim, generated-artifact, derivation-ref -->

## 本节目标 / Objectives

- Use the **head-count** logic of "who can win this pot" to explain why nut advantage collapses on the same board when a third player joins, and which number does not move at all.
- Compute the per-defender floor and the table's floor in a multiway pot, and say why the first falls with the number of players while the second stays exactly equal to the heads-up MDF.
- Restate the two hard constraints this repository puts on such computations -- the independent defender assumption inside the frequency formula, and the two refusals in `odds.py` (no `exact=True`) and `range_advantage.py` (no range that still contains board cards) -- and say what each refusal teaches.

## 前置知识 / Prerequisites

- `03-01` Equity advantage and nut advantage: this lesson rewrites those two "one range versus one range" numbers as "whose share is it", so the definitions have to come along.
- `03-04` Board texture classes: how much dilution happens depends on how many players a texture lets hold strength at once.

## 核心原理 / The principle

Heads-up and three-way, "range advantage" is two differently shaped statements:

1. **Defense side.** With `N` defenders a bluff must win against *everyone*, so if each continues independently at rate `d`, `(1 − d)^N = B/(P + B)`, hence

   ```
   d = 1 − (B/(P + B))^(1/N)          <- each player's floor
   1 − (1 − d)^N = P/(P + B)          <- the table's floor, independent of N, identically the heads-up MDF
   ```

   This is `derived`, but the derivation uses one **independent defender assumption** (recorded in `pokergto.theory.multiway` and in `table.07-01.multiway-defense`'s `provenance.assumptions`): in a real deal the players' cards constrain each other, and removal effects move the joint figure.
2. **Capacity side.** A range's *capacity* on a board is a countable number of combos -- `who_can_win` returns each player's share of the combos that can win. No independence assumption enters this step; it is enumeration, which makes it the only quantity in this lesson that stays exact three-way -- **provided the range has had the board removed**, which the next section shows is enforced by the engine.

Together they are the title: **heads-up range advantage is a sentence; three-way range advantage is a table of shares.**

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Formulas and shares are derived in this repository: `src/pokergto/odds.py#defense_frequency_multiway`, `src/pokergto/theory/multiway.py#who_can_win`. The three ranges are declared illustrative inputs (`reference`), see the provenance section.

## 推导 / Derivation

**Per-player floor and table floor.** Let the pot be `P`, the bet `B`, the number of defenders `N`. An air hand wins the pot only if all `N` players fold. With independent continuation at rate `d`, the joint fold rate is `(1 − d)^N`, and indifference gives

```
(1 − d)^N = B/(P + B)
1 − d = (B/(P + B))^(1/N)
d = 1 − (B/(P + B))^(1/N)
```

The exponent is `1/N` -- not `N`, not `N − 1`. **This is the one step able to fail quietly**: the module docstring of `pokergto.theory.multiway` records that an earlier draft of this curriculum wrote `1 − (1 − single)^(N−1)`, an error that is instructive precisely because it collapses to the right answer at `N = 1`, survives a single sanity check, and only breaks once a second opponent appears. So the `N = 1` fallback is a test, not a coincidence:

```
N = 1:  d = 1 − B/(P+B) = P/(P+B) = MDF          <- the same number as in 02-03
```

The table's floor falls out of the same equation, with `N` cancelling:

```
1 − (1 − d)^N = 1 − B/(P + B) = P/(P + B)          <- identically the heads-up MDF
```

`python -m pokergto mdf --pot 12 --bet 12 --opponents 2` prints `d = 0.2929 each, joint 0.5000 (equals the heads-up MDF)`: each defender needs only 29.29% while the table still has to defend 50% -- **the word "defend" denotes two different quantities in the two sentences**, and in `table.07-01.multiway-defense` the `At least one defends` column equals the `Heads-up MDF` column in every row, which is the machine version of the same fact.

How to read that table: it is blocked by size (five rows each, `Opponents` 1 through 5) and the block order is the order in which `size` appears in `rows` -- `0.33 / 0.5 / 0.75 / 1.0` -- while `columns` does **not** include a `size` column, so the rendered blocks carry no size label. Every figure this lesson takes from it is quoted with its own command or division, never read off the block alone.

**The engine refuses exact values.** The `N`-th root of a rational is irrational in general, so `defense_frequency_multiway` raises when `N > 1` and `exact=True`. Quoted from the engine, verbatim:

```
>>> defense_frequency_multiway(12, 12, 2, exact=True)
ValueError: multiway MDF involves an N-th root, which is irrational for most inputs; call with exact=False, or request N=1 for the closed form
```

The refusal teaches more than the return value would: **a multiway frequency is exact given its assumption, but lives outside the rationals.** The single-street bars of `02-02` can be written as `Fraction`s; these cannot. When this lesson prints 29.29% it is printing a decimal reading of the irrational `1 − 1/√2` (with `B/(P+B) = 1/2`, `N = 2`).

**Capacity shares, and why the board must come out first.** For each range `R_i` and board `b`, count `v_i = #{combo in R_i : category(best_score(combo, b)) >= bar}` and then `share_i = v_i / Σ v_j`. That is everything `who_can_win` does -- **it is not a probability**, it is "of the combos on this board that can win, what fraction does each player own".

One of the engine's refusals belongs in the lesson because it *is* the lesson: `nut_advantage` and `is_capped` require a range that has already had the board removed, otherwise they stop:

```
>>> is_capped(parse("AKs,AQs,ATs,KQs,AKo,AQo,99,77"), parse_cards("Kh7s3d"))
InputError: is_capped: range 0 still holds 7c7s, a card on the board. Narrow it with Range.with_removed(*board) or notation.parse(spec, exclude=board); nut shares and combo counts divide by what the range contains.
```

The reason is the denominator: `range_equity` masks board-colliding combos by itself, while a nut share divides by whatever combos it was handed. Two columns of one table would then answer two different questions -- **equity honest, the share beside it inflated, by a factor that never looks like an error.** Every capacity figure in this lesson is computed after `Range.with_removed(*board)`. Feeding the same ranges in both ways makes the difference measurable (board `Kh7s3d`, CO's declared range):

- after removing the board: combos `44.0`, `>= one pair` combos `24`, `>= two pair` combos `3` (the three `77` combos that do not contain `7s`).
- without removing it: combos `52.0`, `>= one pair` `32`, `>= two pair` `6` -- the extra 8 and 3 are combos that **cannot be dealt**.
- the shares barely move: three-way `>= one pair` goes from `0.347826 / 0.260870 / 0.391304` (filtered) to `0.340426 / 0.255319 / 0.404255` (unfiltered). **Shares stable, counts wrong** -- exactly the class of error that never looks like one.

A structural boundary also needs stating: `>= flush` is identically `0` on any flop with at most two of a suit (two hole cards plus three board cards cannot make five of a suit), and `who_can_win` then returns all zeros; on a monochrome board such as `Ts8s2s` it is not zero (Example 3). The bar itself (`minimum_category`) is a choice: swapping "one pair" for "two pair" swaps the story.

## 直觉 / Intuition

Heads-up, "my range is stronger" is tug of war: one rope, two ends. Three-way, the pot is a pie being cut: **your absolute strength did not change; your share of the table did.**

- On `Kh7s3d`, after the board is removed, CO owns just `3` combos in the "two pair or better" tier; BTN brings `9`. Those 3 go from "100% of the tier" to "25% of it". Nut advantage collapses in the ownership column, not in the cards.
- Defense runs the other way: more people, and **your own** required continuation rate falls (50% -> 29.29%). Not because you got weaker, but because the table's 50% is no longer yours alone to carry -- which is still not a licence to fold, since part of that 50% is yours.
- One sentence to carry: **heads change shares and frequencies, but not the fold rate a bluff needs** (`B/(P+B)` contains no `N`; `continuation_fold_requirement` returns that invariant).

## 算例 / Worked examples

Every figure comes from a command printed here; capacity figures are computed after `Range.with_removed(*board)`, and equities come from exact enumeration (no sampling error).

**Example 1 -- per-player floor and table floor (the `mdf` subcommand).**

- `python -m pokergto mdf --pot 12 --bet 12 --opponents 2` -> each `0.2929`, joint `0.5000`, equal to the heads-up MDF `0.5000`.
- `python -m pokergto mdf --pot 12 --bet 12 --opponents 3` -> each `0.2063`, joint still `0.5000`.
- `python -m pokergto mdf --pot 12 --bet 4 --opponents 2` (one third pot) -> each `0.5000`, joint `0.7500`.
- `python -m pokergto mdf --pot 6.5 --bet 2.1667 --opponents 2` -> each `0.5000`, joint `0.7500`; drop `--opponents` and the same command prints the heads-up MDF `0.7500`.

The third line holds a coincidence worth pausing on: with one third pot and two defenders, **each player's floor is exactly 50%** -- the same number as the heads-up floor against a pot-sized bet. The same "defend half" answers two different questions: there it is "you plus one other must cover 75%", here it is "you are that 50%".

**Example 2 -- ownership of the two-pair tier dilutes (board `Kh7s3d`).** Three declared ranges (the first two are the hero/villain specs of the first row of `table.03-01.equity-vs-nut-advantage`): CO `"AKs,AQs,ATs,KQs,AKo,AQo,99,77"`, BB `"KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s"`, BTN `"KK,QQ,JJ,77,33,AKs,AQs,KJs,QJs,JTs"`. Combos after removing the board: `44.0 / 58.0 / 39.0`. With `python -c` calling `pokergto.theory.multiway`:

- Bar `ONE_PAIR`: able-to-win combos `24 / 18 / 27`. Two-way (CO vs BB) shares `0.571429 / 0.428571`; three-way `0.347826 / 0.260870 / 0.391304`. CO falls from clear majority to about a third.
- Bar `TWO_PAIR`: `3 / 0 / 9`. Two-way shares `[1.0, 0.0]` -- CO **owns** the tier; three-way `[0.25, 0.0, 0.75]`, and BTN is its holder. That is the exact meaning of "nut advantage dilutes": CO did not get weaker; somebody else also holds the top tier.
- Bar `FLUSH`: `0 / 0 / 0`, and `who_can_win` returns all zeros -- no flush exists on this at-most-two-of-a-suit flop.

**Example 3 -- a monochrome board makes the dilution visible (`Ts8s2s`).** Declared ranges CO `"AA,KK,QQ,AKo,AQs,ATs,KQs"`, BB `"JTs,T9s,98s,76s,QJs,J9s,54s"`, BTN `"99,88,77,AJs,KJs,QTs,T9o,ATo"`; combos after removal `41.0 / 25.0 / 44.0`. Flush-tier counts `2 / 4 / 2`:

- two-way (CO vs BB): `[0.333333, 0.666667]`; three-way: `[0.25, 0.5, 0.25]`.
- one-pair tier counts `23 / 13 / 38`: two-way `[0.638889, 0.361111]`; three-way `[0.310811, 0.175676, 0.513514]`.

Same board, one more player: the top tier moves 0.3333 -> 0.25 (8.33 points) while the pair tier moves 0.6389 -> 0.3108 (32.81 points). **The lower tier is diluted harder**, because the entrant brings pair-level hands. That is the combinatorial source of "multiway, the value bar for betting goes up" -- not a style recommendation.

**Example 4 -- the pairwise nut reading flips when the opponent changes (`Kh7s3d`).** `python -c` calling `pokergto.theory.range_advantage.nut_advantage` (`near_nuts=0`) and `is_capped`; both demand board-excluded ranges:

- `nut_advantage(CO, BB)` = `[0.068182, 0.0]`: heads-up, CO is the only range holding the current top tier (three sevens).
- `nut_advantage(CO, BTN)` = `[0.0, 0.076923]`: **against BTN as the opponent CO's nut share is zero**, because BTN's range contains `KK` (trips kings is the ceiling this board allows) and CO's does not.
- `is_capped`: CO `True`, BB `True`, BTN `False` (definition: the range's best holding sits below the ceiling any two cards can reach here).

Same board, same combos, only "who is across from you" changed, and the reading goes from "CO may bet big" to "CO's range is capped". This is precisely why a heads-up sentence cannot be moved into a three-way pot.

**Example 5 -- heads-up claims must sit on a computed row.** With `python -c` calling `pokergto.theory.range_advantage.advantage(..., mode="exact")` (it removes the board itself), the equity columns line up digit for digit with the artifact `table.03-01.equity-vs-nut-advantage` cited in this lesson:

- `Kh7s3d`, CO opener versus BB caller: hero equity `0.715272`, villain `0.284728` (edge `+0.430545`); nut shares `0.068182` versus `0.0`; `who_can_bet_often = hero`, `who_can_bet_big = hero`.
- `9h6d3c`, BTN opener `"AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs"` versus BB `"87s,76s,65s,54s,T8s,T9s,98o,97o,66,55"`: hero equity `0.368154`, villain `0.631846` (edge `−0.263691`), yet nut shares `0.047619` versus `0.0` (nut edge `+0.047619`); `who_can_bet_often = villain`, `who_can_bet_big = hero`. **On a low connected board the raiser is neither simply ahead nor simply behind -- the two edges point opposite ways.**
- `As9s5d`, CO `"AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT"` versus BB `"KQs,QJs,KJs,JTs,98s,76s,99,55"`: hero equity `0.610233` (edge `+0.220466`), nut shares `0.0` versus `0.103448` (nut edge `−0.103448`) -> `who_can_bet_often = hero`, `who_can_bet_big = villain`.

Where there is no row, this lesson writes no heads-up sentence.

**Example 6 -- the bluff-to-value mix: the bar is unchanged, what a range can supply is not.** `pokergto.theory.multiway.bluff_value_ratio` counts air per value (value = at least one pair, ranges board-excluded). On `Kh7s3d`: CO `0.833333` (value 24, air 20), BB `2.222222` (18/40), BTN `0.444444` (27/12). Compare the ratios the indifference condition allows (the reciprocal of the `Value : bluff` column of `table.02-04.bluff-value-ratio`: one third pot -> `0.25`, half pot -> `0.3333`, two thirds -> `0.4`, three quarters -> `0.4286`, pot -> `0.5`, three halves -> `0.6`, two times pot -> `0.6667`):

- BTN's `0.444444` sits between three quarters pot (`0.4286`) and pot (`0.5`) -- the only one of the three ranges that balances at a medium-to-large size.
- CO's `0.833333` is **already above what the most extreme rung of the standard ladder, two times pot (`0.6667`), allows**, and BB's `2.222222` is far above it. **Neither range can be balanced at any standard size on this board** -- not "should not bet", but "too few combos that can win to support a bet".
- Switch to `9h6d3c`: CO `4.444444`, BB `4.0`, BTN `0.740741`, all over the line -- and the "at least one pair" counts on that low connected board are only `9 / 12 / 27` (board-excluded), thinner than `Kh7s3d`'s `24 / 18 / 27`.

The indifference ratio itself does not contain `N` (it comes from `B/(P+2B)`); what changes multiway is how much value a range can supply. **That is the arithmetic location where "small and frequent" dies in a multiway pot.**

## 生成表 / Generated tables

The first artifact is this lesson's main table: per-player defense, joint defense and the heads-up MDF for every size and every number of opponents.

<!-- BEGIN AUTO:table.07-01.multiway-defense -->
| Opponents | Per-player defense | At least one defends | Heads-up MDF |
|---:|---:|---:|---:|
|         1 |             75.19% |               75.19% |       75.19% |
|         2 |             50.19% |               75.19% |       75.19% |
|         3 |             37.16% |               75.19% |       75.19% |
|         4 |             29.42% |               75.19% |       75.19% |
|         5 |             24.33% |               75.19% |       75.19% |
|         1 |             66.67% |               66.67% |       66.67% |
|         2 |             42.27% |               66.67% |       66.67% |
|         3 |             30.66% |               66.67% |       66.67% |
|         4 |             24.02% |               66.67% |       66.67% |
|         5 |             19.73% |               66.67% |       66.67% |
|         1 |             57.14% |               57.14% |       57.14% |
|         2 |             34.53% |               57.14% |       57.14% |
|         3 |             24.61% |               57.14% |       57.14% |
|         4 |             19.09% |               57.14% |       57.14% |
|         5 |             15.59% |               57.14% |       57.14% |
|         1 |             50.00% |               50.00% |       50.00% |
|         2 |             29.29% |               50.00% |       50.00% |
|         3 |             20.63% |               50.00% |       50.00% |
|         4 |             15.91% |               50.00% |       50.00% |
|         5 |             12.94% |               50.00% |       50.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#defense_frequency_multiway`

<!-- generated by: tools/gen_tables.py from pokergto.odds::defense_frequency_multiway -->
<!-- END AUTO:table.07-01.multiway-defense -->

The same numbers are pinned from two directions: the artifact's `checks` require `N = 1` to reproduce the heads-up MDF (`mdf_equality`) and the joint defense to equal it for every `N` (`ev_matches_direct_calculation`, tolerance `1e-9`), both passing. The independence assumption is written in the same artifact's `provenance.assumptions` rather than hidden inside the formula.

The second gives the indifference mix, the comparison column for Example 6 (`Value : bluff` is the reciprocal of the allowed air share):

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

## 实战牌局 / Live hands

**Hand 1 (`hand.03-09-three-owners-of-one-tier`) -- how "my range is strongest" breaks in a three-way pot.**

Seats and money: 100bb, 6-max. CO opens 2.5, BTN calls, BB completes to 2.5 (SB folds; its 0.5 is dead money) -> pot `2.5*3 + 0.5 = 8.0`, each of the three has `97.5` behind (`spr(97.5, 8.0) = 12.1875`). Flop `Kh7s3d`, ranges as declared in Example 2.

- Example 2's numbers decide who has a voice on this line: **two pair or better** combos are CO `3`, BB `0`, BTN `9`. With BTN out of the hand CO owns 100% of the tier; with BTN still in, CO owns `0.25` and BTN `0.75`.
- Decision point: does CO bet pot? Read the heads-up facts first -- `nut_advantage(CO, BTN) = [0.0, 0.076923]` and `is_capped(CO) = True`. Those two lines veto "CO can bet big": **the top tier on this board belongs to BTN, and CO cannot even reach the ceiling the board allows.**
- Replace BTN by BB as the opponent (BTN folds) and the same board reads `nut_advantage(CO, BB) = [0.068182, 0.0]`, making CO the only holder of the trips tier. Same CO, same `Kh7s3d`, opposite verdicts, and the only difference is whether a third player is still in.
- None of this needs an opponent model: every number is an enumerated combo count taken after removing the board.

**Hand 2 (`hand.03-09-joint-defense-1-3-pot`) -- applying the heads-up MDF per player has a computable price.**

Seats and money: pot `8.0` as above; CO bets one third pot `2.6667`; BTN has not acted, hero is in the BB. That is the structure `defense_frequency_multiway` describes: `N = 2` defenders still to act.

- Command: `python -m pokergto mdf --pot 6.5 --bet 2.1667 --opponents 2` gives the same shape: each `0.5000`, joint `0.7500`. The pot here is 8.0 and the ratio is what matters (one third pot: `B/(P+B) = 0.25`).
- Correct reading: BB's **personal** floor is 50% of combos continuing; the table's floor is 75%. If BB defends the heads-up 75% (importing `02-03`'s number) and BTN does the same, joint defense is `at_least_one_defense(0.75, 2) = 0.9375` -- **18.75 points over**, the table calling a one third pot bet almost every time.
- Over-defending is not "solid"; by definition it means continuing with weaker hands, and weaker hands miss the one-street bar: `equity_needed_to_call(8.0, 2.6667) = 20.00%`, while `Jd9d` against `"AA,KK,QQ,JJ,TT,AKs,AQs,ATs,KQs,AKo,AQo"` holds `0.152320`, worth `ev_call(8.0, 2.6667, 0.152320) = -0.635757` per hand. At pot size the same 15.2320% is `ev_call(12, 12, 0.152320) = -6.51648`.
- In the other direction, if BB and BTN each defend only 25% (far below the 50% a one third pot demands), the joint fold rate is `0.75² = 0.5625`, above the `25.00%` the size needs, and a pure bluff earns `ev_pure_bluff(12, 4, 0.5625) = +5.0` per hand; at pot size `ev_pure_bluff(12, 12, 0.5625) = +1.5`. **The punishment for under-defending does not require the opponent to read you -- only to compute.**

## 范围图 / Range chart

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

The chart is the **heads-up** MDF quota for a one third pot bet: combos filled in strength order until they cover `994.5` of the 1,326 (75.00%). Its correct use in a three-way pot is as the **table's** quota, not each player's: against the same one third pot, two defenders at 50% each already supply the joint 75% (Example 1 and Hand 2), while treating the chart as a personal assignment makes both fill 75% and pushes the table to `0.9375`.

The legend keeps its boundary too: **a quota answers "how many", not "which hands"**. Multiway, "which hands" additionally depends on how the player behind you reacts, which is the cell `03-08` marks as unverified.

## 为何成立、何时失效 / Why it works, when it breaks

**Assumptions**, in two groups because their strength differs:

- The frequency claim needs only: a bluff must beat everyone, and defenders act **independently**. The second is an assumption, not a fact: `table.07-01.multiway-defense` states in `provenance.assumptions` that removal effects move the joint figure, and `02-03` lists the same limit. So the per-player rates are exact *given* independence, and real deals break independence (two players holding the same suit is the everyday case). This repository does not invent numbers for that deviation; it records it in an assumption field.
- The capacity claim needs no independence, but it needs board-excluded ranges: `nut_advantage` and `is_capped` refuse otherwise, while `who_can_win` does not refuse -- it simply counts combos that cannot be dealt. Its price is that it answers "share", **never "probability"**: "at least one player has a pair" requires joint enumeration over deals, and `pokergto.equity.range_equity` takes exactly hero and villain -- no multiway all-in equity function exists here. So every "who can win" sentence in this lesson is a combo share, and any multiway percentage written as a probability is UNVERIFIED (see mistake 3).

**Where these are not yet the number to execute:**

1. **You may raise.** The floor constrains total continuation; the calling frequency may sit lower if raises supply the rest (`02-03`, unchanged multiway).
2. **Your action changes the pot for the player behind you.** Your call gives the third player better odds -- implied and reverse implied odds (`03-08`), outside this lesson's formula.
3. **On an incomplete board the nut tier is the strongest hand reachable now.** `nut_advantage` is defined on the current board rather than over all runouts, which understates the drawing side; the same caveat is recorded in `table.03-01.equity-vs-nut-advantage`'s assumption fields. FLUSH being identically `0` on flops with at most two of a suit is the extreme case.
4. **ICM.** The floors assume linear chips (chapter 12).
5. **More players still.** At `N = 5` the per-player floor against one third pot drops to `0.243285` (`table.07-01.multiway-defense`), and the formula has not broken -- the independence assumption has broken harder, because five overlapping ranges are no longer a small correction.

## 陷阱 / Common mistakes

1. **Importing the heads-up MDF per player.** Against a pot-sized bet, 50% each gives joint `at_least_one_defense(0.5, 2) = 0.75`, i.e. 25 points more than required. *Cost:* it forces continuation with hands that miss the bar -- `QdJc` at `0.102222` against `"AA,KK,QQ,JJ,TT,AKs,AQs,AKo,AQo"` is `ev_call(12, 12, 0.102222) = -8.320008` per hand at pot size. Over-defending is not insurance; it is a one-way ticket.
2. **Carrying a heads-up nut sentence into a three-way pot.** Example 2's `TWO_PAIR` tier: CO is `[1.0, 0.0]` two-way and `[0.25, 0.0, 0.75]` three-way, while its absolute count stays `3`. *Cost:* reading heads-up, CO treats this dry high board as its own big-size spot; in fact BTN holds 9 of those combos, and `nut_advantage(CO, BTN) = [0.0, 0.076923]` with `is_capped(CO) = True` have already handed the big size to BTN.
3. **Reading capacity shares as "the probability somebody has it".** The usual sentence is "three-way, at least one player has a pair about 70% of the time". This repository has no function producing that: `range_equity` takes two ranges, `who_can_win` returns combo shares. *Cost:* numbers of that kind get used to price floats and bluffs (`03-08`), while those two actions only ever need `B/(P+B)` and `B/(P+2B)`, both computable. **Trading a computable threshold for an uncomputable probability converts a checkable decision into an unchecked one.**

## 练习 / Drills

- By hand: pot 12, bet 4, three defenders -- per-player and table floors? (`python -m pokergto mdf --pot 12 --bet 4 --opponents 3` -> each `0.3700`, joint `0.7500`)
- Per-player fold rate: pot 12, bet 12, two defenders -- what is `1 − d`, and its square? (`1 − 0.292893 = 0.707107`, `0.707107² = 0.5`, which is exactly `continuation_fold_requirement(12, 12, 2) = 0.5`)
- Self-check the formula: set `N = 1` and verify `d` collapses to `P/(P+B)`, aligning with `python -m pokergto mdf --pot 12 --bet 6` (heads-up half pot, prints `0.6667`).
- The refusal of exact values: run `defense_frequency_multiway(12, 12, 2, exact=True)`, read the `ValueError`, and explain why the answer in that case, `1 − 1/√2`, is not a rational number.
- The refusal of un-excluded ranges: hand `is_capped(..., parse_cards("Kh7s3d"))` the raw `parse("AKs,AQs,ATs,KQs,AKo,AQo,99,77")`, read the `InputError`, then compute it again the way the message says. Note the observation: `>= two pair` combos go from `6` to `3` while the shares barely move.
- Share exercise: with `python -c`, take this lesson's CO and BB specs to the board `As9s5d` and BTN `"KK,QQ,AQs,ATs,KTs,QTs,99,55,77"` (all board-excluded). `>= one pair` counts `36 / 26 / 30` -> two-way `[0.580645, 0.419355]`, three-way `[0.391304, 0.282609, 0.326087]`; `>= two pair` counts `3 / 2 / 6` -> two-way `[0.6, 0.4]`, three-way `[0.272727, 0.181818, 0.545455]`; `>= three of a kind` counts `3 / 0 / 6` -> two-way `[1.0, 0.0]`, three-way `[0.333333, 0.0, 0.666667]`. Say why raising the bar from "two pair" to "trips" moves BTN from 0.5455 to 0.6667.

## 自测清单 / Self-check

- [ ] I can derive `d = 1 − (B/(P+B))^(1/N)` from "the bluff must beat everyone" and say why the exponent is `1/N` rather than `N − 1`.
- [ ] I can state that joint defense equals the heads-up MDF for every `N`, and point to the two `checks` in `table.07-01.multiway-defense` that pin it.
- [ ] I can explain why `exact=True` is refused for `N > 1`, and why `nut_advantage` refuses a range that still contains a board card.
- [ ] Given a board and three ranges, I can compute shares of able-to-win combos and say precisely what they are not.
- [ ] I can name one computed row where the heads-up nut reading flips when the opponent changes, and the function that produced it.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->

| Content | Source type | Location / the command that produced it |
|---|---|---|
| Per-player and joint multiway defense | `derived` (given the independent defender assumption) | `src/pokergto/odds.py#defense_frequency_multiway`, `src/pokergto/theory/multiway.py#per_player_defense / #joint_defense`; `python -m pokergto mdf --pot … --bet … --opponents …` |
| Joint fold rate a bluff needs (independent of N) | `derived` | `src/pokergto/theory/multiway.py#continuation_fold_requirement` |
| The `N>1` refusal of `exact=True` | engine behaviour, quoted verbatim | `ValueError: multiway MDF involves an N-th root, which is irrational for most inputs; …` |
| The refusal of ranges that still contain board cards | engine behaviour, quoted verbatim | `InputError: is_capped: range 0 still holds 7c7s, a card on the board. …`; implemented at `src/pokergto/theory/range_advantage.py#_assert_board_excluded` |
| Capacity shares (24/18/27, 3/0/9, 2/4/2, …) | `derived`, no independence assumption but requires board removal | `python -c`: `Range.with_removed(*board)` first, then `pokergto.theory.multiway.who_can_win / value_and_air_combos` |
| Nut shares and capped verdicts (0.068182, 0.076923, True/False) | `derived` | `python -c` calling `pokergto.theory.range_advantage.nut_advantage / is_capped` (board-excluded) |
| The three heads-up rows: equities (0.715272, 0.368154, 0.610233) and nut shares (0.068182, 0.047619, 0.103448) | `derived` | `python -c` calling `pokergto.theory.range_advantage.advantage(..., mode="exact")`; the equity columns match `table.03-01.equity-vs-nut-advantage` digit for digit |
| Air-to-value counts (0.833333, 2.222222, 0.444444; 4.444444, 4.0, 0.740741) | `derived` | `python -c` calling `pokergto.theory.multiway.bluff_value_ratio` (board-excluded) |
| EVs (−0.635757, −8.320008, −6.51648, +5.0, +1.5), 0.9375, 0.75 | `derived` | `python -c` calling `pokergto.ev.ev_call / ev_pure_bluff`, `pokergto.odds.at_least_one_defense / equity_needed_to_call` |
| The **nut-share columns** of `table.03-01.equity-vs-nut-advantage` (11.5385%, 9.0909%, 16.6667%) | **UNVERIFIED / disagrees with this lesson's commands** | The commands here give 6.8182%, 4.7619%, 10.3448%. The difference is that the engine now requires board-excluded ranges (see the two refusals above) while those two columns were emitted before that rule. This lesson uses the recomputable set throughout; the discrepancy is a `data/gen` versus `src/` coordination issue and is recorded here, not fixed here. |
| The three declared ranges (CO/BB/BTN spec strings) | `reference` + **UNVERIFIED** | Illustrative inputs: not solved, not measured opening or calling ranges from any population. A solved decision would need a spot artifact in `data/src` plus `tools/gen_tables.py`. |
| The independent defender assumption itself | `reference` + **UNVERIFIED** | Removal effects break it; the artifact records this in `provenance.assumptions`. No artifact yet quantifies the bias -- a multiway showdown equity function does not exist (`range_equity` takes two ranges). |
| Sentences like "the probability at least one player has a pair three-way" | **UNVERIFIED**; this lesson refuses to print one | No function produces them; no such percentage anywhere in this lesson is a claim of this repository. |

No commercial solver output, no transcribed range chart, no screenshots.

## 术语 / Terms

<!-- terms: multiway, range-advantage, nut-advantage, capacity, the-nuts, heads-up, independent-defender-assumption, removal-effect, minimum-defense-frequency, equity-advantage, bluff-to-value-ratio, required-equity, combos, range, board, equity, call, fold, bet, pot, bluff, unverified-claim, generated-artifact, derivation-ref -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 多人底池 | multiway | an environment with two or more defenders still acting, not "many players preflop" |
| — | 单挑 | heads-up | the two-player structure; the `N = 1` fallback point |
| — | 范围优势 | range advantage | a sentence heads-up, a table of shares three-way |
| — | 胜率优势 | equity advantage | the difference in average equity between distributions, from a named row (Example 5) |
| — | 坚果优势 | nut advantage | who owns the top tier on this board; diluted by head count |
| — | 坚果 | the nuts | the best hand reachable on the board now, not "a very good hand" |
| — | 牌型容量 | capacity | how many strong made hands a range can hold, counted in combos here |
| — | 独立防守假设 | independent defender assumption | the premise of the frequency formula, stored in the artifact |
| — | 移除效应 | removal effects | why that premise is only an assumption, and why this lesson removes the board |
| MDF | 最低防守频率 | minimum defense frequency | `P/(P+B)`, the table's floor; per-player floors in Example 1 |
| B:V | 诈唬与价值比 | bluff-to-value ratio | the indifference mix, the comparison column of Example 6 |
| — | 所需胜率 | required equity | the one-street bar, `equity_needed_to_call` |
| — | 组合数 | combos | the numerator and denominator of every share in this lesson |
| — | 未核验声明 | unverified claim | declared ranges, probability-shaped multiway sentences |
| — | 生成物 | generated artifact | tables and charts under `data/gen` |
| — | 推导指针 | derivation reference | `provenance.derivation_ref` in an artifact |
