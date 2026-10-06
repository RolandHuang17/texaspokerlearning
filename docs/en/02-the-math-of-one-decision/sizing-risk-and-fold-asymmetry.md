# Sizing asymmetry: raise risk against what a fold is worth

<!-- hands: 2 -->
<!-- terms: sizing-risk, fold-asymmetry, bet-size, minimum-defense-frequency, fold-equity, offered-odds, polarized, merged, spr, overbet -->

## 本节目标 / Objectives

- Name the two things a larger size changes at once -- the fold rate it demands and the money it risks -- and say which grows linearly and which grows at a decaying rate.
- Use the `02-03` "one equation, two sides" framing to state exactly what a bluff-catcher must do when the size moves.
- Compute the residual expectation after being raised, and show why pure air pays almost nothing for sizing risk while middling hands pay for everyone.

## 前置知识 / Prerequisites

- `02-03` MDF and the fold frequency a bluff needs; `02-06` the unified template, which this lesson extends with a third branch.
- `02-05` fold equity as `f·P`; `02-02` the equity needed to call, `B/(P+2B)`.

## 核心原理 / The principle

A size is not a statement of aggression. It is three quantities moving together:

```
money at risk          B                          ← grows linearly with size
fold rate you must get f = B / (P + B)            ← grows, but at a decaying rate
price you offer him    e_req = B / (P + 2B)       ← grows, and it is his bar for calling
```

The asymmetry lives in the **rates**. Walking the ladder from one quarter pot to two times pot multiplies the risk by 8, multiplies the required fold rate by only 3.33, and cuts the fold rate demanded per chip risked from `0.80` to `0.3333` -- a 57% drop. A big bet buys folds cheaply but pays for them with far more money; a small bet risks almost nothing yet has to extract 2.4 times more folds per chip.

This is a `derived` result: all three expressions come from `src/pokergto/odds.py`, and no range chart is involved.

## 推导 / Derivation

**Step one, the two sides of one equation.** `02-03` gives the bluff's demand `f = B/(P+B)` and the defender's floor `MDF = P/(P+B)`. They sum to one identically:

```
B/(P+B) + P/(P+B) = 1
```

So every notch of size moves both numbers at once, in opposite directions: the bigger you bet, the more folding you collect and the less range you are entitled to expect him to keep. That identity is the whole origin of the trade-off in this lesson -- the income you want and the defense he gives up are one coin.

**Step two, linear risk against convex gain.** Set `P = 1` and differentiate `f(B) = B/(1+B)`:

```
df/dB = 1 / (1 + B)²
```

That is `0.64` at one quarter pot, `0.5625` at one third, `0.25` at pot and `0.1111` at two times pot: the marginal fold rate you buy falls by 5.8x while `B` simply grows linearly. Bigger sizes purchase ever less new folding per extra chip.

The form that is easier to use at a table is the normalised one:

```
f / B = 1 / (P + B)
```

Read it as "how much folding each chip I risk must buy back": `0.80` at one quarter pot, `0.6667` at half, `0.50` at pot, `0.3333` at two times pot. Small bets are expensive in folds, big bets cheap -- and that is the same fact `02-04` stated as "a bigger bet needs a more bluff-heavy range": a big size buys folds at a low price, so you can afford a looser composition.

**Step three, what is left after you are raised.** The `02-06` template has two branches; adding "he raises and you fold" gives three. Let you bet `B`, let the opponent raise to `R` with probability `r`, and let you fold to it:

```
EV(bet) = f·P + (1 − f)·[ (1 − r)·( e·(P + 2B) − B ) + r·( −B ) ]
```

The point sits in the rightmost term: **folding to a raise costs `B` -- exactly as much as being called and losing.** So for pure air (`e = 0`) the raise changes nothing at all: `EV(bluff) = f·P − (1 − f)·B` carries no `r` (check: `ev_pure_bluff(10, 5, 1/3) = 0.0`).

That is where the asymmetry actually lands. **Sizing risk is not paid by air; it is paid by middling hands.** Air folds to a raise and `B` was always going to be lost. A hand with equity could have won `P + B` when called; instead the big size lets a raise push it into "fold and donate `B`" or "pay a much higher price to continue". Continuing does cost a higher price, and the closed form is short: the matched pot is `P + 2B`, you add `R − B`, and with both sides filled the final pot is `P + 2R`, so

```
e_req = (R − B) / (P + 2R)
```

With `P = 10, B = 5, R = 20` that is `15/50 = 30%`. Through the engine it is even shorter -- read a raise as "call `B`, then bet the rest into the already matched pot `P + 2B`" (`02-06`):

```
equity_needed_to_call(P + 2B, R − B)
pot 10, you bet 5: raise to 12 → 20.59%; to 15 → 25.00%; to 20 → 30.00%; to 30 → 35.71%
```

The opponent only has to **raise bigger** and you need a stronger hand to continue. This clause never fires against air, which folds anyway; it fires on your middle.

## 直觉 / Intuition

Get the two ends straight and the middle stops being mysterious.

- **A small bet is a cast net.** You drop a quarter pot; a raise does not hurt and a call does not hurt much. The price is that this net must collect a lot of folding to pay -- `f/B = 0.80` -- while one quarter pot only requires 20% folds, so you do not get much, because calling a small bet is comfortable for him. The binding constraint on a small bet is not risk, it is that nobody is fooled.
- **A big bet is a buyout.** Two times pot needs only 33.33% real defense to reach your threshold (`f = 66.67%`), so folds are cheap; but you commit two pots, and your middling hands get pushed into "fold and waste 2 pots" or "pay 35.71% to continue".

Which is exactly why "which size" has no single answer: on the same board, air can afford the big size, middling hands cannot, and the nuts can afford it best because a raise is answered by a re-raise. Chapter 03 (range and nut advantage) decides who can use a big size on a given texture, and chapter 04 turns that into a size set. This lesson does one job: **different strengths pay different prices for the same size.**

## 算例 / Worked examples

**Example 1 -- the three rows across eight sizes (`P = 1`, from `pokergto.odds`).**

| Size | `B` | Required fold rate `f` | `f/B` | Marginal `1/(1+B)²` |
|---|---|---|---|---|
| 1/4 pot | 0.25 | 20.00% | 0.8000 | 0.6400 |
| 1/3 pot | 0.3333 | 25.00% | 0.7500 | 0.5625 |
| 1/2 pot | 0.5 | 33.33% | 0.6667 | 0.4444 |
| 2/3 pot | 0.6667 | 40.00% | 0.6000 | 0.3600 |
| 3/4 pot | 0.75 | 42.86% | 0.5714 | 0.3265 |
| pot | 1.0 | 50.00% | 0.5000 | 0.2500 |
| 1.5x pot | 1.5 | 60.00% | 0.4000 | 0.1600 |
| 2x pot | 2.0 | 66.67% | 0.3333 | 0.1111 |

**Example 2 -- pricing a raise against a middling hand (`P = 10, B = 5`).** Folds needed to continue: `R = 12 → 20.59%`, `15 → 25.00%`, `20 → 30.00%`, `30 → 35.71%`. Reproduce: `PYTHONPATH=src python -c "from pokergto.odds import equity_needed_to_call as q; print([(R, round(q(20, R-5), 4)) for R in (12,15,20,30)])"` (with `P + 2B = 20`).

**Example 3 -- how much raise risk eats the big-size bonus.** Pot 10, `f = 0.3`, equity when called `e = 0.62` (a hand that is ahead), with `r` at 0 and 0.15:

| `B` | `r = 0` | `r = 0.15` |
|---|---|---|
| 4 (1/3 pot) | 8.0120 | 6.8402 |
| 5 (1/2 pot) | 8.1800 | 6.8780 |
| 10 (pot) | 9.0200 | 7.0670 |

The pot bet's edge over one third pot shrinks from `1.0080` to `0.2268`: 77.5% of the bonus is gone.
Reproduce: `PYTHONPATH=src python -c "P=10;f=0.3;EV=lambda B,e,r: f*P+(1-f)*((1-r)*(e*(P+2*B)-B)+r*(-B)); print([(B, round(EV(B,0.62,0),4), round(EV(B,0.62,0.15),4)) for B in (4,5,10)])"`

**Example 4 -- same command, `e = 0.45` (a genuinely middling hand)**: `B = 4 → 5.8700 / 5.0195`, `B = 5 → 5.8000 / 4.8550`, `B = 10 → 5.4500 / 4.0325`. The small size was already better with no raise threat; the threat widens the gap from `0.42` to `0.99`. One table, one `r`, and moving only `e` from 0.62 to 0.45 relocates the best size from pot to one third pot (`r` is an opponent-model input; see the provenance table).

**Example 5 -- the defender has two thresholds, not one.** Moving from one third pot to two times pot changes both: `MDF` falls from 75% to 33.33% (your quota) while `equity_needed_to_call` rises from 20% to 40% (your hand). Read `poker odds --pot 1` column by column; do not memorise only the first one.

## 生成表 / Generated tables

The main table is the full unfolding of "one equation, two sides" (`pokergto.odds.sizing_table`, `P = 1`): within a row, MDF and the required fold rate are complements, and `equity_needed` is the price you offer.

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

Sizing risk has a depth dimension too: "bet half the pot" means something entirely different at `SPR = 1` and at `SPR = 10`, because the all-in threshold moves with stack behind (`pokergto.spr`):

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

The deeper the stacks, the closer committing needs to 50% equity -- `48.78%` at `SPR = 20`. So a large size pushes middling hands past what they can pay in exactly the deep spots, and the denominator of sizing risk is your stack behind, not the current pot.

## 实战牌局 / Live hands

**Hand 1 (`hand.02-08-turn-size-and-raise-risk`) -- turn `AcKd8s5h`, pot 10, hero `KsQh` (top pair, good kicker, `e = 0.62` when called), opponent check-raises 15% of the time.**

- The three sizes are exactly Example 3's three rows: pot is best at `7.0670`, one third pot gives `6.8402`, cost `0.2268`.
- Look at how thin that bonus is. With no raise threat pot beats one third pot by `1.008`; with a 15% raise threat only `0.2268` survives. **The bonus of the big size is mostly confiscated by one raise line**, so the sizing question is often not "will he call" but "what do you do when he raises".
- Drop `e` from `0.62` to `0.45` and the order reverses outright (Example 4): `5.0195` against `4.0325`, and the pot bet becomes the worst option. Same board, same raise rate, one strength bracket apart, a whole size bracket different.
- Where that leaves the decision: first ask whether this hand still has a second road after being raised (a call or a re-raise). If it does, the big size is affordable; if not, bet small or check rather than donating `B`.

**Hand 2 (`hand.02-08-river-overbet-air`) -- river, pot 20, hero holds pure air, considering a two-times-pot overbet of 40.**

- Required fold rate `B/(P+B) = 40/60 = 66.67%`; MDF is only `33.33%` (`poker mdf --pot 20 --bet 40`). Cheap folds are the overbet's only advantage.
- Raise risk prices air at zero: `EV(bluff) = f·P − (1 − f)·B` contains no `r`. When he raises you fold, and either way the loss is `B = 40`. That contrast with Hand 1's middling hand is the point of this lesson.
- But air pays in full for a bad **fold-rate** estimate: moving `f` from 70% to 50% swings `+2.0` to `−10.0` (`02-05` Example 5). So the right checklist for an overbet bluff is: does my `f` have a source; does the range carry the 40% bluff share `02-04` demands; and only then, am I afraid of a raise -- which for air is not a real question.
- This is also why big sizes arrive with polarized shapes in practice: the top end (a raise answers with a re-raise) and the bottom end (a raise meets a fold) can both pay for the size, while the middle cannot. **The shape conclusion belongs to chapter 04; this lesson supplies only the mechanism.**

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

The chart is the half-pot defense quota (884 of 1,326 combos). What this lesson reads off it is **movement**: from one third pot to two times pot the line shrinks from `1326 × 0.75 = 994.5` combos to `1326 × 1/3 = 442` (filled as 995 and 442). The defender's range gets thinner as the size grows, but it does not thin at random: what he drops is precisely the part that neither reaches `B/(P+2B)` -- 40% at two times pot -- nor blocks any value segment.

The chart also marks what the bettor cannot obtain: `f` is capped by exactly those 442 uncovered combos. Wanting more folding means counting on a deviation from MDF, which is chapter 13's subject. Only the half-pot floor exists today; a family of floors indexed by size needs `tools/gen_ranges.py` to accept a size sequence, so this lesson uses `poker mdf --pot ... --bet ...` in the meantime.

## 为何成立、何时失效 / Why it works, when it breaks

**Premises**: a single street's expectation, you genuinely fold when raised, the opponent's raise rate does not depend on your size, `e` holds once called, chips are linear in utility.

**Where it fails**:

1. **`r` depends on size.** In real play larger sizes trigger more raises (only stronger hands dare). Writing `r = r(B)` makes Example 3's confiscation steeper. The engine accepts any shape for `r`; it will not estimate one for you -- that is chapter 04 plus an opponent model.
2. **You do not fold to a raise.** If you have a call or a re-raise available, the `r·(−B)` term is replaced by a branch with its own expectation, and the "air ignores raise risk" conclusion holds only for air that truly folds.
3. **Multiway pots.** Two opponents can raise, `f` becomes the joint fold rate (`02-05` Example 4), and the raise branch must be weighted by "neither raises". Handled after `07-02`.
4. **Later streets exist.** This lesson's "loss `B`" is settled inside one street; a turn bet also buys the river option (`06-05`, double barrel), and omitting it makes small sizes look better than they are.
5. **Deep stacks.** `B` is capped by what is behind you. `table.03-07.spr-commitment` shows the all-in bar converging to 50% as SPR grows, so sizing risk is nearly a non-issue below `SPR = 1` and the main issue above `SPR = 4` (`03-08`, pot commitment).
6. **Non-linear utility.** On a tournament bubble the cost of `B` far exceeds its chip value (chapter 12).

**What this lesson deliberately does not answer**: which size to use. That is range advantage and nut advantage (chapter 03), then size sets and the frequency logic (chapter 04). The trade-off here is risk against need, and it is board-independent; writing "this texture suits a big bet" into this lesson would be a claim with no source behind it.

## 陷阱 / Common mistakes

1. **Reading "needs more folds" as "easier to steal with".** A big bet does collect more folds (`f` from 20% to 66.67%), but it buys them with 8 times the risk; the like-for-like comparison is the `f/B` column, `0.80 → 0.3333`.
   *Cost*: concluding that big bets are the most efficient and overbetting every river, while paying a linearly growing amount for a decaying margin. Read the second and fourth columns of `poker odds --pot 1` together.
2. **Believing a big size means a tight range.** The same backwards intuition as `02-04`, seen from the risk side: two times pot demands the ladder's highest bluff share, 40%.
   *Cost*: value-only overbets get folded to by everything medium, so your value segment collects `P` and never `P + B` -- which is exactly the bonus Example 3 shows being confiscated. The quota is in `table.02-04.bluff-value-ratio`.
3. **Giving every hand the same answer about size.** Example 3 and Example 4 differ only in `e` (0.62 against 0.45) and the best size moves from pot to one third pot.
   *Cost*: transporting "this hand, this size" as a general rule abandons a gap of 0.987 chips per hand, which is not a rounding error.
4. **Adjusting the defense frequency but not the hand's own bar.** From one third pot to pot, `MDF` falls 75% → 50% while the equity needed rises 20% → 33.33%.
   *Cost*: letting the quota decide which specific hands to keep, so you fold your bluff-catchers and keep your draws -- frequency satisfied, every individual decision wrong. Check both with `poker odds --pot 20` and `poker mdf --pot 20 --bet 20`.

## 练习 / Drills

- By hand: for `P = 1`, the four numbers `f`, `MDF`, `f/B`, `equity_needed` at one third pot and two times pot; verify with `poker odds --pot 1` and say which pair is complementary and which pair merely looks alike.
- Retune Example 2: `P = 12, B = 6`. What equity do you need against a raise to 24? Against a raise to 18?
- Sweep `r` in Example 3 over `0 / 0.10 / 0.20 / 0.30` and plot the pot-versus-one-third-pot advantage; find the `r` where it hits zero.
- Defense drill: pot 24, opponent bets 24 (`MDF = 50%`) versus bets 8 (`MDF = 75%`). With `JhTh`, which beats only air, should the hand be kept in each case? Compute both `equity_needed` first.
- Depth drill: pot 20 with 20 behind (`SPR = 1`) versus pot 20 with 200 behind (`SPR = 10`). Run `poker spr --stack ... --pot ...` for both and explain why "bet half pot" is not the same decision.

## 自测清单 / Self-check

- [ ] I can list the three quantities a size moves at once and state each one's rate of growth.
- [ ] I can use `f + MDF = 1` to explain why sizing and defense are two sides of one equation.
- [ ] I can derive that folding to a raise costs `B`, and say why that exempts air from sizing risk.
- [ ] I can compute the equity needed to continue against a raise via the `P + 2B` and `R − B` substitution.
- [ ] I can say that choosing the size is out of scope here, and name the chapter 03 and 04 results that own it.

## 来源与置信度 / Provenance and confidence

Every number here is computed in this repository. No range chart or strategy output from a commercial solver or paid course is used in this lesson.

| Content | Source type | Location / reproduce with |
|---|---|---|
| `f = B/(P+B)`, `MDF = P/(P+B)`, `f + MDF = 1` | `derived` | `src/pokergto/odds.py#required_fold_frequency`, `#minimum_defense_frequency` |
| `f/B = 1/(P+B)`, marginal `P/(P+B)²`, Example 1 | `derived` | Derivation above; each cell re-checkable with `poker odds --pot 1` (`f/B` and the marginal come from those same columns) |
| Raise prices 20.59% / 25.00% / 30.00% / 35.71% | `derived` | `PYTHONPATH=src python -c "from pokergto.odds import equity_needed_to_call as q; print([(R, round(q(20, R-5), 4)) for R in (12,15,20,30)])"` |
| The three-branch expectation and "air is insensitive to `r`" | `derived` | Derivation above plus `src/pokergto/ev.py#ev_bet`; `ev_pure_bluff(10,5,1/3)` = `0.0` |
| The six expectations in Examples 3 and 4 | `derived` (`e`, `r` are inputs) | The `EV=lambda` command under Example 3; swap `e` to `0.45` for Example 4 |
| Sizing table and SPR commitment table | `derived` | `data/gen/tables/table.02-03.mdf-vs-sizing.json`, `table.03-07.spr-commitment.json` |
| Defense quota chart | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json`; combo conversion `1326 × 0.75 = 994.5`, `1326 × 1/3 = 442` |
| Hand 1's `e = 0.62` and `r = 0.15` | `reference` + **UNVERIFIED** | Authored opponent-model inputs, not engine output. Path: per-node ranges in `data/src/spots/*.yaml` re-priced with `poker equity`, raise rates collected by the trainer |
| "Big sizes go with polarized shapes" | chapter 04 conclusion | **UNVERIFIED** here; path: the polarized/merged derivation in `04-05` plus reproducing the shape in the chapter 08 two-street toy game |
| Family of defense floors indexed by size | no artifact yet | needs `tools/gen_ranges.py` to accept a size sequence |

## 术语 / Terms

<!-- terms: sizing-risk, fold-asymmetry, bet-size, minimum-defense-frequency, fold-equity, offered-odds, polarized, merged, spr, overbet -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 尺度风险 | sizing risk | the extra being-outdrawn and being-raised loss a larger size buys |
| — | 弃牌不对称 | fold asymmetry | folds given up and risk carried are not in proportion |
| — | 下注尺度 | bet size | `B` expressed as a pot fraction |
| MDF | 最低防守频率 | minimum defense frequency | `P/(P+B)`, complement of `f` |
| — | 给对手的赔率 | odds offered | `B/(P+2B)`, his reason to call |
| FE | 弃牌赢率 | fold equity | `f·P`, what the big size buys |
| SPR | 筹码底池比 | stack-to-pot ratio | effective stack / pot, the cap on sizing risk |
