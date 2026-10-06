# Protection or value: what changes the reason for betting

<!-- hands: 2 -->
<!-- terms: protection-bet, semi-bluff, value-bet, equity-realization, flush-draw, outs, equity, showdown, fold-equity, bet-size -->

## 本节目标 / Objectives

- Use `hand_equity` and `draw_probability` to turn "checking lets the opponent see one card for free" into numbers: how often his outs land, what share of the pot he then takes, and what your equity is on that branch.
- Verify and explain the identity `p·e(hit) + (1 − p)·e(miss) = e(now)`, and show from it that "denying equity" is worth exactly 0 chips in a model where both players check to showdown.
- Write `EV(bet) − EV(check)` as three terms -- value, protection, folds -- and state that only the protection term depends on the opponent's future-street input `β`, which is why a "protection bonus" cannot be a verified number here.

## 前置知识 / Prerequisites

- `01-03` outs and exact hit probability, including the trap of "45 or 47 unseen cards?".
- `02-06` `EV(bet) = f·P + (1 − f)·(e(P + 2B) − B)` and `EV(check) = e·P`; `02-07` thin value.
- `01-06` the concept of equity realization (EqR); `adr/0002`: a model with no anchor may not be presented as a conclusion.

## 核心原理 / The principle

**"Protection" is not an extra payoff term. It is the part of the same expectation gap that depends on what the opponent does after the next card.** Three things are computable here:

1. The probability `p` that the opponent's draw lands (`draw_probability`, exact enumeration, not the rule of two and four).
2. Your showdown equity once it lands, `e_hit`, together with the identity that the hit and miss branches, weighted, must return today's equity `e₀`.
3. The decomposition of `EV(bet) − EV(check)` into `B·(2e₀ − 1)` (value) + `B·β·p·(1 − 2e_hit)` (protection) + the fold branch `f·(P − EV(call))`.

Here `β` is "how often he bets the next street after completing". **`β` is not computable in this repository**: making it `derived` needs a solved two-street game, and `docs/development/solver-proof-policy.md` records that neither Leduc nor the ruddy toy is implemented. So the protection term stays a function of `β`, never a number.

## 推导 / Derivation

Notation: pot `P`, hero's bet `B`, the fold frequency he faces `f`; hero's equity if the money goes in now `e₀ = e(now)`; the probability the opponent's draw lands on the next card `p`; hero's equity then `e_hit` (hit) and `e_miss` (miss).

**Step one: equity is a martingale.** By iterated expectation over every possible next card,

```
p·e_hit + (1 − p)·e_miss = e₀
```

This is not an approximation, it is what enumeration forces. For `AcAd` against `QhJh` on `9h5h3d` it holds exactly: `e₀ = 61/99 = 61.6162%`, `e_hit = 7/198 = 3.5354%`, `e_miss = 67/88 = 76.1364%`, `p = 1/5`, and substituting gives `0.6161616161616161`, matching `e₀` to 1e-16.

**The consequence is hard.** If the checking branch is modelled as "he also checks, both see the showdown", then `EV(check) = e₀·P` while the called branch of betting is `e₀(P + 2B) − B`. Their difference:

```
EV(bet) − EV(check) = B·(2e₀ − 1)      (with f = 0)
```

contains **no term called protection**. Denying the opponent a free card wins nothing -- on average that card wins him nothing either.

**Step two: invite protection back in.** It can appear only if, after checking, the opponent gets to **act on the card**. Parameterise that with `β = P(he bets the turn after completing)`, and let this lesson's teaching model be "he checks back when he misses" and "hero calls the turn bet":

```
EV(check) = (1 − p)·e_miss·P + p·[ β·( e_hit(P + 2B) − B ) + (1 − β)·e_hit·P ]
```

The martingale collapses all the `P` terms (`(1−p)e_miss + p·e_hit = e₀`) and one bracket is left:

```
EV(bet) − EV(check) = B·[ (2e₀ − 1) − β·p·(2e_hit − 1) ]      (f = 0)
                    = B·(2e₀ − 1) + B·β·p·(1 − 2e_hit)
```

At `β = 0` this returns to step one and the protection term vanishes exactly. **Protection = `B·β·p·(1 − 2e_hit)`**: linear in the size `B`, linear in the hit probability `p`, growing with how far behind you are once he hits (`1 − 2e_hit`) -- and multiplied by an opponent policy.

**Step three: two folk sayings this kills.**

- "Bet to protect even when you are behind." With `e₀ < 1/2` the value term is negative, and flipping the sign needs `β·p·(1 − 2e_hit) > 1 − 2e₀`. But on the drawing side `e_hit` is near 1, so `1 − 2e_hit` is negative and the protection term is **always negative**: for `QhJh` at `B = 5, β = 1` it is `−0.929293`. A draw does not bet for protection; it bets as a semi-bluff, and its case lives in the fold branch.
- "Protection needs a big size." `B` merely multiplies the bracket, so the sign never depends on it. What limits `B` is the stack ceiling (`table.04-03.size-ceiling-by-stack`) and the value you lose as folds rise with size -- not the word "protection".

## 直觉 / Intuition

Read a free card as an option in the opponent's hand: **the option changes nothing about expected equity (the martingale), it changes who gets to ask for money after good news.**

So what you give away by checking is not equity, it is a choice. A bet buys that choice back: he must pay `B` now for the card instead of looking at it and then deciding. That is also why protection gets mentioned most on boards where the next card swings both players hard (there `1 − 2e_hit` is near 1) and never on a settled one: **on the river there is no protection at all, only value and bluffs**, because there is no next card to act on.

## 算例 / Worked examples

**Example 1 -- everything computable about one draw (`9h5h3d`, `AcAd` against `QhJh`).**

| Quantity | Value | Source |
|---|---|---|
| Unseen cards | 45 | 7 known cards (2 + 2 + 3), not 47 |
| Turn hit rate `p` | 20.00% (`9/45`) | `draw_probability(9, 45, 1)` |
| Hit rate by the river | 36.36% (two cards) | `draw_probability(9, 45, 2)` |
| Equity now `e₀` | 61.6162% (`61/99`) | `poker equity "AcAd" "QhJh" --board "9h5h3d"` |
| Hero equity after he hits `e_hit` | 3.5354% (`7/198`) | mean over the 9 heart turns |
| Hero equity after he misses `e_miss` | 76.1364% (`67/88`) | mean over the 36 non-heart turns |
| Pot share he takes when he hits | 96.4646% → `9.6465` chips at `P = 10` | `1 − e_hit` |

Counting 47 unseen (removing only hero's cards and the board) gives `p = 19.1489%` and 34.9676% by the river -- exactly the row in `table.01-03.draw-probability-exact-vs-rule`. **0.85 percentage points for one hand of card removal**, which is why this lesson states the unseen count as an input instead of trusting memory.

**Example 2 -- the three-term split (`P = 10`, the turn bet uses the same size `B`, `β = 1`).**

| `B` | value `B(2e₀ − 1)` | protection `Bβp(1 − 2e_hit)` | total `EV(bet) − EV(check)` |
|---|---|---|---|
| 1/3 pot (3.333) | 0.774411 | 0.619529 | 1.393939 |
| 1/2 pot (5) | 1.161616 | 0.929293 | 2.090909 |
| pot (10) | 2.323232 | 1.858586 | 4.181818 |

With `β = 0` every protection entry is `0.000000` and the total collapses back to the value term. With `β = 1/2` protection halves (the half-pot row reads `0.464646`, total `1.626263`). **That is what a protection bonus really is: not a number but a line in `β`.**

**Example 3 -- the fold branch (same hand, `B = 5, f = 1/3`).** `EV(bet) = 8.215488` and `EV(check) = 5.232323` at `β = 1`, a gap of `2.983165`. Against the `f = 0` gap of `2.090909`, folds add only `0.892256` chips, not `f·P = 3.3333` -- because the fold branch saves the part of the called branch you would have lost, i.e. `f·(P − EV(call))`. Adding `f·P` as if it were the whole contribution is the easiest arithmetic error in this lesson.

**Example 4 -- outs more than halve, protection does not (`Kd9c4s`, `AcAd` against `QhTh`, a four-out gutshot).** `p = 4/45 = 8.8889%`, `e₀ = 81.3131%`, `e_hit = 0.000000`, `e_miss = 89.2461%`; at `B = 5, β = 1` the protection term is `0.444444` and the total `3.575758`. Versus Example 2 the ratio of `p` is `9 : 4 = 2.25`, but the ratio of the protection terms is `2.09` -- because `1 − 2e_hit` differs (`0.929293` against `1.000000`). **Protection is not a monotone function of outs: it also reads how lost you are after the card lands**, and that is an enumeration, not a pulse.

## 生成表 / Generated tables

Outs against exact hit rates (that table uses 47 unseen cards, Example 1 uses 45 -- the contrast is deliberate):

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

The protection term scales linearly with the size, so the size ceiling is the protection ceiling:

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

And how much of a betting range a size may carry is still governed by the bluff/value quota -- a draw sits in the bluff segment, not the value segment:

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

**Hand 1 (`hand.04-06-flushdraw-protection`) -- flop `9h5h3d`, pot 10 bb, hero `AcAd`, opponent `QhJh` (flush draw plus two overcards), assume `f = 1/3` (the MDF complement of a half-pot bet).**

- Computable: `p = 20.00%`, `e₀ = 61.6162%`, `e_hit = 3.5354%`, `e_miss = 76.1364%`; when he hits he takes `9.6465` bb of the 10 bb pot.
- Value term `1.161616`, protection term `β·0.929293`, fold branch `0.892256` (at `f = 1/3`).
- Decision: **bet half pot**, and state the reason in verifiable order: first `EV(bet) = 8.215488 > EV(check) = 5.232323` (gap `2.983165` bb), then how much of that gap is an opponent policy (`0.929293` bb at `β = 1`, i.e. 31.2%), then the admission that `β` is unverified.
- If he never barrels (`β = 0`): `EV(check) = 6.161616` and the gap shrinks to `2.053872`, with protection contributing `0`. **Same hand, same action, protection's share falling from 31.2% to 0% -- that is a reason, not a ledger entry.**

**Hand 2 (`hand.04-06-draw-not-protection`) -- the same flop `9h5h3d`, pot 10 bb, now from the opponent's seat: hero is `QhJh`, the side that is behind, and the question is "should I bet to protect my equity".**

- His side of the numbers: `e₀ = 38.3838%`, `e_hit = 96.4646%`, `1 − 2e_hit = −0.929293`. Value term `B(2e₀ − 1) = 5 × (−0.232323) = −1.161616`; protection term `Bβp(1 − 2e_hit) = −0.929293` at `β = 1`. Both negative.
- Conclusion: **protection cannot be his reason to bet**, and any write-up that makes it one is wrong. His bet is a semi-bluff resting on `02-05`'s fold branch: pure air breaks even at `f = B/(P+B) = 1/3` (`ev_pure_bluff`), and his 20.00% hit rate pushes that bar down -- which is exactly why `02-04` says a semi-bluff is cheaper than air.
- Cost of mis-booking it: reading the `−0.929293` as `+0.929293` puts the action's expectation off by `1.858586` bb per hand and in the wrong direction.
- Teaching point: the protection term's sign comes from `1 − 2e_hit`, so **only the side that ends up behind after the card can have protection at all**.

## 范围图 / Range chart

Protection bets usually live around 3/4 pot, where the defender owes 57.14% of his range:

<!-- BEGIN AUTO:range.04-02.mdf-floor-vs-three-quarter-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| 7 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. |
| 6 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. |
| 5 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | .. | .. | .. | .. | .. |
| 4 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 3 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |
| 2 | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. |

757.7 combos = 57.14% of all 1,326

Legend: `··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%; the diagonal is pairs, the upper triangle suited, the lower offsuit.

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.04-02.mdf-floor-vs-three-quarter-pot -->

Those 757.71 combos are a floor: they say he may not fold everything, so the value term (which needs calls) is not replaced by the fold branch. They say nothing about protection -- **protection is a next-street action problem and a range chart has one street.** This has to be spelled out, because reading an MDF chart as "should I bet" is the most likely misuse in this repository.

## 为何成立、何时失效 / Why it works, when it breaks

**Premises**: `p`, `e_hit`, `e_miss`, `e₀` come from exact enumeration (no sampling error); `f` and `β` are declared inputs; the checking branch assumes "he checks back a miss, bets a completion" and hero calls the turn bet; one card to come.

**Where it breaks**:

1. **`β` is not computable.** It is the frequency with which the opponent fires after improving, which needs a two-street solve. This repository has none (`docs/development/solver-proof-policy.md`: `PUBLISHED_PROOFS` holds Kuhn plus five one-street size toys). The protection term can only be written as a linear function of `β`; any "protection is worth X bb/100" is an external assertion and must be labelled `reference` + UNVERIFIED.
2. **The martingale holds for one fixed deal and one fixed opponent hand.** If the bet itself changes who continues, `e₀` gets a new domain -- the identity still holds, but you must re-enumerate.
3. **On the river there is no protection term.** There is no next card, so `p` and the whole term do not exist; calling a river bet "protection" is a terminology error.
4. **Multiway pots**: hit rates and the joint "everyone folds" `f` both change with player count (`pokergto.odds.defense_frequency_multiway`); reopened after `07-02`.
5. **Only calls are modelled on the turn.** A raise would change the value of the `e_hit` branch, and it needs the same kind of policy input as `β`.
6. **No invented exponent is reintroduced here.** `src/pokergto/theory/__init__.py` records why three modules were deleted: they turned fabricated exponents into precise-looking numbers. This lesson prefers one undetermined `β` to one assumed power.

## 陷阱 / Common mistakes

1. **Treating "denying the free card" as money won.** The martingale says that piece is 0 (at `β = 0` the total collapses to the value term).
   *Cost*: in this lesson's branch the protection term is only `0.929293` bb per hand at half pot; claiming protection is why you bet turns 31.2% into 100%.
2. **Booking the fold branch as `f·P`.** The fold branch saves what you would have lost when called.
   *Cost*: Example 3, `3.3333` against the true `0.892256`, an overstatement of `2.44` bb per hand.
3. **Assigning protection to the player who is behind.** His `e_hit` is higher, so the term is negative (Hand 2).
   *Cost*: a sign error worth `1.858586` bb per hand in the wrong direction -- precisely what happens when a semi-bluff is described as a protection bet.
4. **Using memorised hit rates instead of enumeration.** The 45-versus-47 difference, and the rule of four's error at 12 outs (`table.01-03.draw-probability-exact-vs-rule`: exact `44.9584%` against `48%`, 3.04 points).
   *Cost*: `p` enters protection multiplicatively, so an inflated `p` inflates the term by the same ratio and can flip "is this extra size worth it".

## 练习 / Drills

- Check the martingale with Example 1's four numbers: does `p·e_hit + (1 − p)·e_miss` equal `e₀`? (answer: `0.6161616161616161` both sides).
- With `β = 1/3`, `B = 1/2 pot`, `P = 10`, compute the three terms and add them (answer: value `1.161616`, protection `0.309764`, total `1.471381`).
- Find a matchup with `e₀ = 1/2` using `poker equity` and show that the value term is 0 while protection stays positive -- the one strength point where a "protection bet" can stand alone.
- Compute both counting conventions: `draw_probability(9, 45, 2)` = `36.3636%` against `draw_probability(9, 47, 2)` = `34.9676%`, and explain why the opponent's two hole cards must be removed.

## 自测清单 / Self-check

- [ ] I can write `p·e_hit + (1 − p)·e_miss = e₀` and explain what it kills.
- [ ] I can write `EV(bet) − EV(check) = B[(2e₀ − 1) + βp(1 − 2e_hit)]` at `f = 0` and attribute each term.
- [ ] I can name the two cases where the protection term is negative (`e₀ < 1/2` with insufficient `β`; `e_hit > 1/2`, i.e. I am the draw).
- [ ] I can say which artifact would make `β` a `derived` quantity (a solved two-street game with a `PUBLISHED_PROOFS` entry).
- [ ] I know there is no protection term on the river and can say why in one sentence.

## 来源与置信度 / Provenance and confidence

All equities, conditional equities, hit rates and expectations are computed here by exact enumeration (no Monte Carlo). `f = 1/3`, the three values of `β`, and "the turn bet uses the flop's size" are declared model inputs. This lesson introduces no protection coefficient and no realization exponent, and cites no external solver output.

| Content | Source type | Location / reproduce with |
|---|---|---|
| `e₀ = 61/99`, `e_hit = 7/198`, `e_miss = 67/88`, `p = 1/5` and the martingale | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto.equity import hand_equity as he; from pokergto.cards import parse_cards as pc, standard_deck as sd; h,v,b=pc('AcAd'),pc('QhJh'),pc('9h5h3d'); rest=[c for c in sd() if c not in list(b)+list(h)+list(v)]; eq=lambda t: F(he(h,v,tuple(b)+(t,)).equity).limit_denominator(10**12); hs=[c for c in rest if c.code[-1]=='h']; ns=[c for c in rest if c.code[-1]!='h']; eh=sum(eq(c) for c in hs)/len(hs); em=sum(eq(c) for c in ns)/len(ns); p=F(len(hs),len(rest)); print(len(rest), he(h,v,b).equity, float(eh), float(em), float(p), float(p*eh+(1-p)*em))"` |
| `e₀` through the CLI | `derived` | `PYTHONPATH=src python -m pokergto equity "AcAd" "QhJh" --board "9h5h3d" --json` |
| Example 2's three rows (`0.774411 / 1.393939`, `1.161616 / 2.090909`, `2.323232 / 4.181818`) | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; P=F(10); e0=F(61,99); eh=F(7,198); em=F(67,88); p=F(1,5); [print(float(B), float(B*(2*e0-1)), float(B*p*(1-2*eh)), float(ev.ev_bet(P,B,0,e0)-((1-p)*em*P+p*(ev.ev_call(P,B,eh))))) for B in (F(10,3),F(5),F(10))]"` |
| Example 3's `8.215488`, `2.983165`, `0.892256` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; P=F(10); e0=F(61,99); eh=F(7,198); em=F(67,88); p=F(1,5); B=F(5); chk=(1-p)*em*P+p*ev.ev_call(P,B,eh); print(float(ev.ev_bet(P,B,F(1,3),e0)), float(ev.ev_bet(P,B,F(1,3),e0)-chk), float(ev.ev_bet(P,B,F(1,3),e0)-ev.ev_bet(P,B,0,e0)))"` |
| Example 4's `p = 8.8889%`, `e₀ = 81.3131%`, protection `0.444444` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto.equity import hand_equity as he; from pokergto.cards import parse_cards as pc, standard_deck as sd; h,v,b=pc('AcAd'),pc('QhTh'),pc('Kd9c4s'); rest=[c for c in sd() if c not in list(b)+list(h)+list(v)]; eq=lambda t: F(he(h,v,tuple(b)+(t,)).equity).limit_denominator(10**12); js=[c for c in rest if c.code[0]=='J']; ns=[c for c in rest if c.code[0]!='J']; eh=sum(eq(c) for c in js)/len(js); em=sum(eq(c) for c in ns)/len(ns); p=F(len(js),len(rest)); print(float(p), float(he(h,v,b).equity), float(eh), float(em), float(F(5)*p*(1-2*eh)))"` |
| Hand 2's `−1.161616`, `−0.929293`, `1.858586` | `derived` | the same command as Example 2 with `e₀ = 38/99` and `e_hit = 191/198` (villain's seat, `1 − e_hit`); the signs flip automatically |
| 45 vs 47 unseen cards and `0.200000 / 0.191489 / 0.349676 / 0.363636` | `derived` | rates: `PYTHONPATH=src python -c "from pokergto.equity import draw_probability as dp; print(dp(9,45,1), dp(9,45,2), dp(9,47,1), dp(9,47,2))"`; unseen count: `PYTHONPATH=src python -c "from pokergto.equity import unseen_after; from pokergto.cards import parse_cards as pc; print(unseen_after(pc('9h5h3d'),[pc('AcAd'),pc('QhJh')]))"` → `45` |
| `f = 1/3`, `β = 1`, turn size = flop size | `reference` + **UNVERIFIED** | declared model inputs. The 1/3 comes from `pokergto.odds.required_fold_frequency(10, 5)`, but "he actually folds that often" is not measured |
| **A protection bonus as a number** | no artifact → **UNVERIFIED** | needs a two-street solve: `docs/development/solver-proof-policy.md` records Leduc and ruddy as unimplemented, and `src/pokergto/solver/proofs.py` currently lists Kuhn plus five one-street size toys |
| "How often the opponent barrels after improving" (`β`) | no artifact → **UNVERIFIED** | same as above; `data/src/spots/*.yaml` records single-node actions and cannot express a cross-street policy |
| Equity realization (EqR) as used here | `reference` | the concept from `01-06` only; no EqR value is quoted, because this repository implements none -- see the deletion note in `src/pokergto/theory/__init__.py` |

## 术语 / Terms

<!-- terms: protection-bet, semi-bluff, value-bet, equity-realization, flush-draw, outs, equity, showdown, fold-equity, bet-size -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 保护性下注 | protection bet | the `B·β·p·(1 − 2e_hit)` term, whose existence depends on a future-street action |
| — | 半诈唬 | semi-bluff | the behind hand's bet: fold branch plus hit rate, never protection |
| — | 价值下注 | value bet | the `B(2e₀ − 1)` term, expecting worse hands to call |
| EqR | 胜率实现 | equity realization | concept only; not implemented here, so no EqR number is quoted |
| — | 同花听牌 | flush draw | Example 1's 9 outs, `p = 20.00%` at 45 unseen |
| — | 补牌 | outs | the only free parameter of `draw_probability` |
| — | 胜率 | equity | the three conditional equities `e₀ / e_hit / e_miss`, tied by the martingale |
| — | 摊牌 | showdown | where `EV(check) = e·P` ends, and where protection disappears |
| FE | 弃牌赢率 | fold equity | the branch `f·(P − EV(call))`, not `f·P` |
| — | 下注尺度 | bet size | protection is linear in `B`; `B`'s ceiling is set by the stack |
