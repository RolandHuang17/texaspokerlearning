# Derivation before memory: every number must be recomputable by the engine

<!-- hands: 2 -->
<!-- terms: gto, nash-equilibrium, exploitability, best-response, provenance, unverified-claim, derivation-ref, minimum-defense-frequency, required-equity, indifference, multiway, icm, overbet, bet-size, fold-frequency, combos, bluff, spr -->

## 本节目标 / Objectives

- Derive `MDF = pot/(pot+bet)` from the single condition "a pure bluff must be indifferent" inside a minute, then use it on a sizing you have never memorised.
- State where memory belongs: the compressed product you keep **after** a derivation, not a substitute for one — and put a price on the difference.
- Tell `derived`, `reference` and `external` apart, and explain why an UNVERIFIED claim can stay in a lesson instead of being deleted.
- Name at least three places where memorised numbers charge you a quantifiable bill: the size changes, the player count changes, chips turn into money.

## 前置知识 / Prerequisites

- `00-01`: the fixed sections, where an AUTO table's numbers come from, how to read a provenance line.
- Solving a one-variable linear equation is the whole requirement. `02-01` and `02-02` derive the two
  formulas used here properly later on, and `02-03` is the full version; this lesson exists to give you
  the feel of producing a number yourself first.

## 核心原理 / The principle

**Recomputability is the floor of verifiability.** A number that a command can reproduce on your own
machine needs no one's endorsement. A number that cannot be recomputed leaves you with exactly one
option: deciding whom to trust. Trusting is the thing this curriculum is meant to replace.

So every claim must be able to answer "how do you know", and the answer must land in one of three kinds:

- `derived` — produced in this repository's `src/pokergto/**`, carrying a derivation pointer you can open.
- `reference` — illustrative content authored here, permitted only where it is independently checkable.
- `external` — someone else's, which requires both `upstream` and a `license` listed in the licensing manifest.

Memory is not banned. What is banned is **sourceless recall**: you hold a number and you have no road
that leads to it.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     The semantics and required fields of the three kinds come from `adr/0005`; "external sources must be registered" comes from `NOTICE`.

## 推导 / Derivation

Take the most quoted conclusion in poker education and do it in two lines. Let the pot be `P` and the
added bet `B`, and let the bettor hold air that can never win.

- With probability `f` everyone folds and the bluff collects the pot uncontested: `+P`.
- With probability `1 − f` somebody defends and the bluff loses the money it put in: `−B`.

Indifference (the bluff's expected value is exactly zero):

```
f·P − (1 − f)·B = 0  ⟹  f = B/(P+B)  ⟹  MDF = 1 − f = P/(P+B)
```

At this point you own a whole curve, not a point. Reading the same equation in other directions gives
three things nobody can carry in their head:

```
heads-up defense quota   MDF = P/(P+B)
per-player quota, N      d   = 1 − (B/(P+B))^(1/N)     ← N=1 collapses to the line above: that is the self-check
all-in commitment level  e   = SPR/(1+2·SPR)           ← the same equation with B = S
```

The first lives in `src/pokergto/odds.py#minimum_defense_frequency`, the second in
`src/pokergto/odds.py#defense_frequency_multiway`, the third in `src/pokergto/spr.py`, and the command
line prints all three on demand. They are not three facts to memorise; they are three substitutions
into one fact.

Now count what memory has to hold. There are 8 sizes, 5 player counts, and SPR varies continuously
from 0.25 to 20. `data/gen/tables/table.02-03.mdf-vs-sizing.json` is 8 rows,
`table.07-01.multiway-defense` is 20 rows and `table.03-07.spr-commitment` is 10 rows:
38 numbers, and they only cover the cells that were printed. Opponent bets 1.15 times pot? Three
players to a bet of 2.2 into 8? Not on any card. Derivation is one equation plus one substitution,
and it covers the whole surface.

One more point, and it is the one this lesson actually wants you to keep: **memory is still useful
after derivation, and it must be.** `P/(P+B)` is too slow at a table where you get fifteen seconds.
The right move is to derive it once, then compress the handful of sizes you meet into spoken
numbers (1/3 pot → 75%, half pot → 66.67%, pot size → 50%) and treat that table as a cache. The
difference is that a cache can be rebuilt, because you know how it was generated. A memorised table,
once the spot falls outside it, leaves you guessing.

## 直觉 / Intuition

A memorised number is a photograph: however sharp, it covers one corner of one frame. An equation is
the rule for drawing the map, and it keeps drawing outside the frame.

There is a crude test for which one you hold: **change a number and ask yourself.** Swap half pot for
0.7 times pot, swap heads-up for three players, swap cash for a final table. If an answer still comes,
you own the equation. If it starts to wobble, you only owned a photograph.

## 算例 / Worked examples

**Example 1 — the memorised 66% against the derived 66.67%.** Half pot: `P = 1, B = 0.5`, so
`MDF = 1/1.5 = 0.6667`, and `PYTHONPATH=src python -m pokergto mdf --pot 1 --bet 0.5` returns 0.6667.
Numerically you would not notice a thing. The difference shows up one row up: a person working from
"defend about two thirds" will say "seventy-ish is fine" at one third pot, while the `1/3 pot` row of
`odds` says 75.00%. Five percentage points.

**Example 2 — the size moves and memory falls off the table.** A river overbet of 1.5 times pot,
`P = 20, B = 30`:

```bash
PYTHONPATH=src python -m pokergto mdf --pot 20 --bet 30
```

prints `bet = 1.500 pot` and `MDF = 0.4000`, and the `3/2 pot` row of `odds --lang zh` gives an equity
needed to call of 37.50%. Now price the habit. Someone running the old "half pot, so 25% is enough"
rule will call 30 with a bluff-catcher that beats 25% of the betting range. The pot after the call is
`20 + 2 × 30 = 80`:

```
0.25 × 80 − 30 = −10      and the correct boundary 0.375 × 80 − 30 = 0
```

Same hand, same table, wrong frame of reference: ten chips a call.

**Example 3 — the player count moves and the error changes sign.** Three-way pot, you are one of two
defenders, facing a one third pot bet: `P = 6.6, B = 2.2`.

```bash
PYTHONPATH=src python -m pokergto mdf --pot 6.6 --bet 2.2 --opponents 2
```

gives `d = 1−((2.2/8.8)^(1/2)) = 0.5000` each with joint defense 0.7500 — which equals the heads-up
MDF for the same size. So the memorised heads-up number makes you defend **more** here, 75% instead of
50%. Check it the way the derivation does, using the identity the engine prints: with each defender
continuing at 50%, everyone folds `0.5² = 0.25 = B/(P+B)` of the time, so the bluff is worth
`0.25 × 6.6 − 0.75 × 2.2 = 1.65 − 1.65 = 0`, exactly indifferent — the premise of the derivation,
verified on the spot. If both defend at 75%, both fold only `0.25² = 0.0625` of the time and air
becomes `0.0625 × 6.6 − 0.9375 × 2.2 = 0.41 − 2.06 = −1.65`: eighteen and three-quarter percentage
points of extra joint defense, paid for by every bluff the opponent ever makes with nothing.

**Example 4 — chips turn into money and the threshold jumps a whole tier.** Three players remain with
5000 / 3000 / 2000 chips and payouts 6000 / 3000 / 1500. The 2000 stack shoves and the chip leader,
Hero, must call 2000 into a pot of 2300 (blinds of 300 included).

- Chip frame: needs `2000/4300 = 46.51%`, which is just the equity-needed-to-call formula.
- Money frame: three `icm` calls give the branch values.
  `PYTHONPATH=src python -m pokergto icm --chips 5000,3000,2000 --payouts 6000,3000,1500` prices the
  winner's seat at 4258.93; `--chips 7000,3000 --payouts 6000,3000` prices the after-winning table at
  5100.00; `--chips 3000,3000,4000 --payouts 6000,3000,1500` prices Hero after losing at 3342.86.
  Solve `e × 5100 + (1 − e) × 3342.86 = 4258.93` and you get `e = 916.07/1757.14 = 52.13%`.

One hand, one stack of chips, one decision, two thresholds: 46.51% and 52.13%. Those 5.62 percentage
points between them are the price tag on "chips are not money". `table.12-03.icm-vs-chip-share`
spreads the whole effect over five rows: the seat holding 37.50% of the chips owns 29.39% of the money,
the seat holding 6.25% owns 10.86%. The memoriser learns "don't call with a short stack around"; the
deriver knows what is expensive, and by how much.

## 生成表 / Generated tables

Three tables, one per way memory failed above: sizing, player count, and the value of a chip. Every
figure in them is computed by the engine, not transcribed, and every one can be reproduced with the
commands given in this lesson.

The sizing curve (Examples 1 and 2):

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

The player-count curve (Example 3). Rows come in blocks of five sizes; the first column is the number
of opponents:

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

The chips-versus-money curve (Example 4):

<!-- BEGIN AUTO:table.12-03.icm-vs-chip-share -->
| Seat | Chip share | Money share | Gap (pp) |
|---:|---:|---:|---:|
|    0 |     37.50% |      29.39% |   -8.11% |
|    1 |     25.00% |      23.67% |   -1.33% |
|    2 |     18.75% |      20.12% |    1.37% |
|    3 |     12.50% |      15.97% |    3.47% |
|    4 |      6.25% |      10.86% |    4.61% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.icm#icm`

<!-- generated by: tools/gen_tables.py from pokergto.icm::icm -->
<!-- END AUTO:table.12-03.icm-vs-chip-share -->

Look at the last block of the middle table (pot-sized bets): per-player defense runs 50.00% at one
opponent, 29.29% at two, 12.94% at five — while the joint column never moves off 50.00%. A column that
stays flat while its neighbour collapses is Example 3 drawn instead of argued: per-player defense falls
with player count, total defense does not. No retyped chart shows that column, because it was not
copied, it was computed.

## 实战牌局 / Live hands

Every EV here uses the one-street approximation: expected value of a call = probability you win ×
(pot + 2 × call) − call.

**Hand 1 (`hand.00-02-river-overbet-memory-fail`) — heads up, on the river.**
Board `AsKd7h5c2s`, pot 20, opponent bets 30 (1.5 times pot). Hero holds a bluff-catcher whose only
wins come against air.

- Decision point: call 30 or fold.
- Computed now: `mdf --pot 20 --bet 30` → `bet = 1.500 pot`, MDF 0.4000; the `3/2 pot` row of
  `odds --lang zh` → equity needed to call 37.50%, bluff share 37.50%.
- The test: air must exceed 37.50% of that betting range before calling pays.
- The memorised play: drag the old "half pot means 25%" rule onto the river and call. Pot after the
  call is `20 + 60 = 80`, and beating only 25% gives `0.25 × 80 − 30 = −10`.
- The derived play: 0.375 × 80 − 30 = 0 is the boundary, so below 37.50% it is a fold. Hero is below
  it. Fold.
- Cost: ten chips per mistake. Notice the sign — here memorisation did not make Hero too passive,
  it made them **too aggressive**.

**Hand 2 (`hand.00-02-three-way-defense-quota`) — 6-max cash, flop, three players.**
CO opens 2.2bb, BTN calls, BB calls: pot 6.6bb. Flop `9h6d3c`, CO bets 2.2bb (one third pot). Hero is
BTN with a medium-weak holding, right at the edge of the quota.

- Decision point: fold, call or raise.
- Computed now: `mdf --pot 6.6 --bet 2.2 --opponents 2` → 0.5000 each, joint 0.7500. Compare the
  heads-up call on the same sizing: `mdf --pot 6.6 --bet 2.2` → 0.7500.
- The test: Hero needs to keep only 50% of their own range alive, not 75%. The 75% joint defense is
  contributed by three people, not carried by one.
- Cost of the memorised quota: defending 75% each drops the both-fold rate to `0.25² = 0.0625`, turning
  the opponent's air from 0.000 into −1.65 per attempt. That extra quarter of the range is made of the
  weakest calls available, which is precisely the cohort a `9h6d3c` board punishes under value bets.
- What derivation gives instead: keep a 50% quota, put the weakest combos on the fold side, and let
  the other two defenders supply the rest of the joint rate. The rule does not care whether N is 2,
  3 or 5 — it costs one substitution to change it.

## 范围图 / Range chart

An orientation lesson issues no range chart: the argument here is that quotas come from an equation,
not from a particular range. In strategy lessons this section carries a `range.*` chart from
`tools/gen_ranges.py`. A real one, read the way you will read them all:
`data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` records `threshold` 0.66666667,
`total_combos` 884, `range_percentage` 66.67%, `provenance.kind` = `derived`, and its
`provenance.assumptions` states outright that combos are filled strongest-first and that MDF constrains
only the total frequency. Those two assumption lines are the artifact's whole secret: 884 combos is a
quota, not a plan.

## 为何成立、何时失效 / Why it works, when it breaks

**Conditions for the derivation to hold:** both players respond to what the other does, defense below
the floor gets punished, folding forfeits the pot, and chips are linear in value (a good approximation
in cash).

**Where the derivation itself stops being the answer — and the boundaries are nameable:**

1. `d = 1 − (B/(P+B))^(1/N)` assumes defenders act **independently**. Real deals couple the ranges
   through card removal, so it is an approximation. The repository writes that into
   `provenance.assumptions` and chapter 07 pushes it forward with a fixed-action three-player model.
2. When the defender can raise, MDF is derived for a call-or-fold choice. Raising absorbs part of the
   defending *action*, but the floor on total defense does not move. Reading "the solver calls less
   than MDF" as "you may defend less" is the standard misfire.
3. In a tournament chips are not money (Example 4). Defending below MDF can be right — and this time
   the *objective function* changed, which is not a memory error. That is chapter 12.
4. When opponents do not punish, MDF is only the floor for not being exploited, not the choice that
   makes the most money. Deviating against a real population is chapter 13.
5. When you do not have time. This is memory's home ground: keep the common sizes compressed as a
   cache, and never try to solve an equation in fifteen seconds.

## 陷阱 / Common mistakes

1. **Confusing MDF with the equity needed to call.** `P/(P+B)` is a range quota; `B/(P+2B)` is one
   hand's threshold.
   *Cost*: in Example 3's spot the `1/3 pot` row prints 75.00% and 20.00% (heads-up frame). Mixing them
   yields "I only need 20% equity, so I may fold 75%", which points the wrong way entirely. Run
   `mdf --pot 6.6 --bet 2.2` and `odds --lang zh` once each; a minute separates them for good.
2. **Treating memory as the conclusion and derivation as decoration** — "I will never compute at the
   table anyway, so just give me the chart".
   *Cost*: the −10 chips of Example 2 is one such off-table call. Outside the table you hold no
   equation, so you can only guess.
3. **Skipping anything marked UNVERIFIED, or the reverse, quoting it as settled.** Both lose
   information.
   *Cost*: `NOTICE` and `adr/0005` currently carry the popular multiway continuation-bet collapse
   (the one usually written as roughly 65% heads-up, 30% three-way, 15% four-way and lower still) as
   `reference` plus UNVERIFIED. Skip it and you have no model of a real three-way pot; quote it as fact
   and you are building ranges on a number nobody derived. The right three steps: read the artifact's
   `unverified_claims`, follow `derivation_ref` to see whether an executable symbol exists, then run
   `mdf --pot 6.6 --bet 2.2 --opponents 2` yourself and anchor on the *derived* structure — 50.00% each,
   75.00% joint.
4. **Judging a quota by hand classes instead of combos.**
   `data/gen/tables/table.01-01.combo-decomposition.json` fixes the per-class counts at 4, 6 and 12.
   *Cost*: up to a factor of three (12 ÷ 4) inside a single rank class, so a range that "defends about
   70%" by class count can really be at 55%.

## 练习 / Drills

- With no table in front of you, derive `MDF`, then derive `d = 1 − (B/(P+B))^(1/N)`; then run
  `PYTHONPATH=src python -m pokergto mdf --pot 24 --bet 12 --opponents 3` and check the 0.3066.
- Recite the MDF and required fold rate for all eight sizes, then score yourself with
  `PYTHONPATH=src python -m pokergto odds --lang zh`. For every miss, write down which step you guessed at.
- Inverse: pot 10, and an opponent's bet requires you to defend 45% for their bluffs to break even —
  what size did they use? (Hint: at `f = 0.55`, `B/(P+B) = 0.55`; solve it.)
- Re-run the three `icm` calls of Example 4 against a payout structure you invent, recompute the money
  threshold, and see how far it moves from 46.51%.
- Write the 15 section headings of `02-03` in order from memory, and mark which two sections are there
  to hand you numbers and which one is there to hand you a source.

## 自测清单 / Self-check

- [ ] I can derive `MDF = P/(P+B)` from bluff indifference inside a minute.
- [ ] I can rewrite the same equation for N players and for an all-in, and say why the N=1 fallback counts as a self-check.
- [ ] I can name an environment change that breaks a memorised number and state that failure's expected value.
- [ ] I can separate `derived`, `reference` and `external`, and say what each is permitted to be used for.
- [ ] I know why an unverified claim is kept rather than deleted, and which three steps to take when I meet one.
- [ ] I can state where memory belongs: after the derivation, as a cache that recomputation can always reset.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number in this lesson comes from a command listed below or from a committed artifact under
`data/gen/`. No range chart or strategy output from a commercial solver or a paid course appears in it.

| Content | Source type | Location |
|---|---|---|
| The two-line derivation of `MDF = P/(P+B)` | `derived` | `src/pokergto/odds.py#minimum_defense_frequency`; full version in `02-03` |
| The N-player formula and the all-in threshold | `derived` | `src/pokergto/odds.py#defense_frequency_multiway`, `src/pokergto/spr.py` |
| 75.00% / 66.67% / 40.00% / 50.00% sizing rows | `derived` | `pokergto odds --lang zh`, `pokergto mdf --pot 20 --bet 30`, `pokergto mdf --pot 6.6 --bet 2.2 --opponents 2` |
| 42.27% each, 66.67% joint at half pot | `derived` | `pokergto mdf --pot 10 --bet 5 --opponents 2` |
| 4258.93 / 5100.00 / 3342.86 and the 52.13% threshold | `derived` | three `pokergto icm` calls; the threshold solves the displayed equation |
| The 46.51% chip-frame threshold | `derived` | `B/(P+2B)` with B = 2000, P = 300, i.e. 2000/4300 |
| 37.50% and the −10 cost | `derived` | the `3/2 pot` row of `pokergto odds --lang zh` plus the EV line above |
| Multiway continuation-bet collapse figures | `reference` + **UNVERIFIED** | `NOTICE`, `adr/0005`; held until `theory/multiway.py` reproduces them |
| Per-class combo counts 4 / 6 / 12 | `derived` | `data/gen/tables/table.01-01.combo-decomposition.json` |

## 术语 / Terms

<!-- terms: gto, nash-equilibrium, exploitability, best-response, provenance, unverified-claim, derivation-ref, minimum-defense-frequency, required-equity, indifference, multiway, icm, overbet, bet-size, fold-frequency, combos, bluff, spr -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| MDF | 最低防守频率 | minimum defense frequency | `P/(P+B)`; a range quota, not a hand's threshold |
| — | 所需胜率 | equity needed to call | `B/(P+2B)`; the threshold for one specific hand |
| — | 无差别 | indifference | the point where a bluff is worth exactly zero: the derivation's premise |
| — | 弃牌频率 | fold frequency | the bettor's side of the same equation; MDF is its complement |
| — | 超池下注 | overbet | a size above the pot, where memory usually fails first |
| — | 多人底池 | multiway | player count moves the per-player quota, not the joint one |
| — | 组合数 | combos | the weighting unit: 6 for a pair, 4 suited, 12 offsuit |
| GTO | 博弈论最优 | game theory optimal | the family of states where neither player gains from changing |
| — | 纳什均衡 | Nash equilibrium | the formal name of that state |
| — | 最优应对 | best response | the strongest reply to a given opponent strategy |
| — | 可剥削度 | exploitability | what a departure from equilibrium costs; chapter 08 gates on it |
| ICM | 独立筹码模型 | independent chip model | the model that converts chips into money |
| SPR | 筹码底池比 | stack-to-pot ratio | the `S/P` inside the all-in threshold |
| — | 来源标注 | provenance | required fields: kind, verified, and a pointer or licence |
| — | 未核验声明 | unverified claim | a bilingual badge plus the `unverified_claims` array; never deleted |
| — | 推导指针 | derivation reference | the field pointing at an executable symbol in `src/pokergto` |
