# How to use this curriculum: hole cards, board, the four streets and position names

<!-- hands: 3 -->
<!-- terms: hole-cards, board, street, preflop, flop, turn, river, pot, bet, raise, call, fold, check, hero, villain, six-max, position, button, small-blind, big-blind -->

## 本节目标 / Objectives

- Given any lesson, say within half a minute: which command produced its numbers, which kind of provenance each claim carries, and which lessons it depends on.
- Recite what each of the 15 fixed sections is for, and explain why one section too many or too few breaks the build.
- Use this repository's sanctioned spelling for hole cards, board, the four streets and the seats; stop treating "hand", "the table" or "round" as interchangeable synonyms.
- Plot your own route by game format: 100bb cash, tournaments, heads-up and button versus big blind, population exploitation — which chapter opens each one, and which chapters all four routes share.

## 前置知识 / Prerequisites

- None. `data/src/curriculum.yaml` records an empty `prereq` list for `00-01`; it is the root of the dependency graph.
- You need a terminal and the ability to `cd` into the repository root. Whether the commands run at all is `00-03`'s problem; this lesson is about how to read.

## 核心原理 / The principle

The repository holds three things, each with one job, and confusing them is where trouble starts:

| Thing | Where | Its job | How you should treat it |
|---|---|---|---|
| The curriculum | `docs/en/**`, `docs/zh/**` | Explain why something is true | Read it, never copy a number into it |
| The engine | `src/pokergto/**` | Compute every number | Run it yourself; its output is the answer |
| The trainer | `trainer/**` | Turn the same numbers into repetition | Three screens exist (sizing scale, 13x13 viewer, solver deck); graded range scoring waits for the M4 EV oracle |

One generation step sits between the engine and the prose: `tools/gen_all.py` writes the engine's
results into JSON under `data/gen/**`, and `tools/inject_doc_tables.py` renders that JSON into a
lesson's AUTO blocks. The direction is one-way, so a number in the prose has only two legitimate
parents: it was generated into an AUTO block, or it is arithmetic you can do against a generated
artifact.

Reading any lesson comes down to two threads: **where the numbers come from** (the AUTO block plus
the `<!-- provenance: ... -->` line under it) and **where the claim comes from**
(`derived` / `reference` / `external`; a missing field fails the build).

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     This section restates no external range chart. The structural rules come from `adr/0001`, `adr/0005`, `NOTICE` and `data/README.md`.

## 推导 / Derivation

"Fixed sections, generated tables" is not a taste question. Three premises force it.

Premise 1: the same conclusions are published in two languages at once. The `totals` object in
`data/gen/index.zh.json` records `lessons: 92`; one lesson is two files, so 92 × 2 = 184 lesson files.

Premise 2: most readers never open the engine source. They read markdown.

Premise 3: free, offline, no accounts is a promise, so "is this number right" cannot be outsourced to
a network service.

From 1: once you type a number by hand you own at least 2 copies of it, and more with every citation.
Whether the copies agree can then only be remembered, and remembered things drift. Drift looks like
chapter 02 printing 66.67% and chapter 07 printing 67%, once per language.
From 2: the reader cannot catch the drift, because they hold no second source to compare against.
From 3: the only thing a reader can check for themselves is a command that emits the same bytes on
their machine.

Put together, those give the repository's three structural rules:

1. A number is computed once, in `src/pokergto/**`, lands in `data/gen/**`, and prose only embeds an
   AUTO block (`adr/0001`).
2. Every strategy claim carries `provenance`; a missing field fails the build instead of waiting for
   a reviewer (`adr/0005`).
3. The two language files must be machine-comparable: section count, total H1/H2/H3 headings, the
   ordered sequence of AUTO ids, and the declared terms all match item by item.

The fixed 15 sections implement rule 3, because anything a machine compares has to be locatable at a
glance. That is why each section heading is one bilingual pair written out in full —
the line `## 推导 / Derivation` is the same byte sequence in the Chinese and the English file, so the
comparison needs no translation. Stated honestly: what `tools/check_bilingual.py` compares today is
the **section count, heading total and AUTO id sequence**. Section *order* is still a human review
job, and `docs/development/bilingual-style.md` says so instead of pretending otherwise.

## 直觉 / Intuition

Picture a shop that keeps exactly one ledger. The engine is the till, `data/gen` is the ledger, and
the Chinese lessons, English lessons and trainer are three menu boards. Menu boards carry no prices;
prices get printed from the till and stuck on. Write your own price on a board and you have created a
fourth number that agrees with nobody.

So there is one reading habit: **when you meet a number, ask which command produced it.** Where that
question has no answer, the lesson says so out loud — `reference` or `UNVERIFIED` is also an answer,
and it beats a false one.

## 算例 / Worked examples

Here is the whole reading method applied to `02-03`, minimum defense frequency. Type it and you will
have re-derived that lesson's numbers in a few minutes. Docs in this repository abbreviate commands as
`poker xxx`, which stands for `python -m pokergto xxx`; the short form only exists once the editable
install succeeds, and `00-03` covers that, so everything below uses the install-free spelling.

**Example 1 — from lesson id to file.** Search `id: "02-03"` in `data/src/curriculum.yaml` and read
`slug: deriving-minimum-defense-frequency`, `prereq: ["02-01", "02-02"]`, `status_zh: draft`.
The lesson slug is the file name and the chapter slug is the directory, so the path is fully
determined: `docs/zh/02-the-math-of-one-decision/deriving-minimum-defense-frequency.md`.
The id `02-03` appears nowhere in that path. Ids are permanent; file names may change.

**Example 2 — compute the sizing ladder instead of reading it.** From the repository root:

```bash
PYTHONPATH=src python -m pokergto odds --lang zh
```

Eight rows, eight sizes. The `1/3 pot` row gives MDF 75.00%, equity needed to call 20.00%, bluff
share 20.00% and a `value:bluff` ratio of 4 : 1. That row and the `table.02-03.mdf-vs-sizing` block
below are the same computation wearing different clothes.

**Example 3 — turn the sentence into a command.** The lesson says "defend 75% facing a one third pot
bet into a pot of 4.4". Check it:

```bash
PYTHONPATH=src python -m pokergto mdf --pot 4.4 --bet 1.4667
```

It answers `MDF = pot/(pot+bet) = 4.400/(4.400+1.467) = 0.7500`. The formula and the substituted
values are printed together, which means you are auditing the working, not just the verdict.

**Example 4 — range notation and combo counts; do not size a range by class count.**

```bash
PYTHONPATH=src python -m pokergto range "22+,ATs+" --lang zh
```

It prints `114.0 combos = 8.60% of 1326`, with `classes` 22. That is 114 ÷ 22 ≈ 5.2 combos per class,
which sounds like a uniform average — but
`data/gen/tables/table.01-01.combo-decomposition.json` says pairs are 13 classes × 6 = 78, suited are
78 classes × 4 = 312, and offsuit are 78 classes × 12 = 936, and 78 + 312 + 936 = 1326. Within one
rank class the count moves between 4, 6 and 12, so averaging over classes counts a hypothetical
"average hand" that no deck contains.

**Example 5 — one hand's equity, and the edge of enumeration.**

```bash
PYTHONPATH=src python -m pokergto equity J9o --range-villain "88+,ATs+" --board "Kh7s3d" --mode exact
```

That gives `17.49%`; the `iterations` field reports how many runouts the engine enumerated, 1,176 this
time, and exact mode has no sampling error at all (standard error 0). Compare it with the 20.00% from
Example 2: this hand does not clear a one third pot bet.

## 生成表 / Generated tables

A lesson body keeps only a pair of HTML comments and leaves the middle empty. The shape is (each line
belongs inside its own `<!--` and `-->` wrapper to be a real block; this lesson deliberately does not
write one, because `tools/check_provenance.py` counts every `BEGIN AUTO` under `docs/**` and demands a
provenance badge for it — a purely illustrative block would turn the build red):

```text
BEGIN AUTO:table.02-03.mdf-vs-sizing     ← opens the block
END AUTO:table.02-03.mdf-vs-sizing       ← closes it, same id
```

`tools/inject_doc_tables.py` reads `data/gen/tables/table.02-03.mdf-vs-sizing.json`, takes the locale
from the file path (`docs/zh/**` gets Chinese headers) and writes four things: the table,
a `<!-- provenance: kind=... verified=... -->` line, the provenance badge, and a trailing
`<!-- source: module::function via generator -->` line. Both languages embed the same id, so the two
tables cannot disagree in any commit: they are one JSON rendered twice.

`02-03`'s two tables are embedded below so you can check them cell by cell against Example 2:

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

<!-- BEGIN AUTO:table.02-02.equity-needed-to-call -->
|   Bet (x pot) | Equity needed |
|---:|---:|
|     0.25x pot |        16.67% |
| 0.333333x pot |        20.00% |
|      0.5x pot |        25.00% |
| 0.666667x pot |        28.57% |
|     0.75x pot |        30.00% |
|        1x pot |        33.33% |
|      1.5x pot |        37.50% |
|        2x pot |        40.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.odds#equity_needed_to_call`

<!-- generated by: tools/gen_tables.py from pokergto.odds::equity_needed_to_call -->
<!-- END AUTO:table.02-02.equity-needed-to-call -->

Three things about reading these tables, all of which have caught people:

1. **Both tables are the same ladder wearing different labels.** The first writes `1/4 pot`, `2x pot`;
   the second writes `0.25x pot`, `0.333333x pot`. Same eight rows, same order, and the order is
   exactly what `PYTHONPATH=src python -m pokergto sizes` prints: 0.2500, 0.3333, 0.5000, 0.6667,
   0.7500, 1.0000, 1.5000, 2.0000. Match them by row number, never by label string.
2. **The badge's type name is always `unverified`**, even when `verified=true`; in that case its title
   reads "verified". Read the `kind` and `verified` fields, not the styling.
3. **A column name is not the question it answers.** `fold_frequency_needed` is the bettor's threshold,
   `MDF` is the defender's range quota, and `equity_needed` is one hand's threshold. Three numbers,
   three questions; chapter 02 pulls them apart.

Two more machine-read markers sit at the top of a lesson, invisible once rendered: one declares the
hand count, how many live hands the lesson carries (`check_bilingual.py` requires a `ready` lesson to
have at least two); the other declares its terms, and every id listed there must exist in
`data/src/glossary.yaml`, so an unregistered term is a CI failure.

## 实战牌局 / Live hands

All three hands use the same routine: name the decision point, compute everything computable, then
price the wrong play. Every EV here is the one-street approximation "treat this street as all-in":
`EV(call) = equity × (pot + 2 × call) − call`, with folding worth 0. Later-street implied odds and
equity realization belong to `01-06` and chapter 06; none of that is smuggled in here.

**Hand 1 (`hand.00-01-bb-defense-call`) — 6-max cash, 100 big blinds effective.**
The button opens 2.2bb, the small blind folds, the big blind calls: pot 4.4bb. Flop `Kd7d3h`, and the
button continuation-bets 1.4667bb, one third pot. Hero is in the big blind with `Ad5d`.

- Decision point: fold, call or raise are all legal, so this is a real decision.
- Quota: `mdf --pot 4.4 --bet 1.4667` → 0.7500. At least 75% of the big blind's combos must continue.
- Threshold: the `1/3 pot` row from Example 2 → calling 1.4667 into 7.3334 needs 20.00% equity.
- What you hold: `equity A5s --range-villain "KQs+,ATs+,QJs+,AJo,TT-22,98s,87s" --board "Kd7d3h" --mode exact`
  → 37.26%. Note that `A5s` is a **class** of 4 combos: the notation in `src/pokergto/notation.py`
  cannot name "only the diamond one", and `Ad5d` happens to be the combo carrying the nut flush draw,
  so 37.26% understates this specific hand. Spot check against one villain hand:
  `equity Ad5d KsQc --board "Kd7d3h" --mode exact` → 46.77%.
- Arithmetic: `0.3726 × 7.3334 − 1.4667 = +1.27bb`.
- Decision: call. Folding throws away +1.27bb, and this combo belongs in the part of the range the
  quota demands you keep.

**Hand 2 (`hand.00-01-bb-defense-fold`) — same line, different hole cards.**
Flop `Kh7s3c` this time, and the button again bets 1/3 pot, 1.4667bb. Hero's `Tc9h` is class `T9o`.

- Quota and threshold are unchanged: MDF 75%, need 20.00%.
- What you hold: `equity T9o --range-villain "KQs+,AJs+,KJo+,QQ,77,66" --board "Kh7s3c" --mode exact` → 10.72%.
- Arithmetic: `0.1072 × 7.3334 − 1.4667 = −0.68bb`; every call loses 0.68bb.
- Decision: fold. Not because the draw is ugly — because it is 9.28 percentage points short.
- The point to keep: folding does **not** violate MDF. MDF counts combos across the range, and a 10.72%
  hand sits squarely in the 25% you are allowed to give up. Reading MDF as "defend 75% of every hand"
  is the most expensive misreading in the game.

**Hand 3 (`hand.00-01-river-bluffcatch`) — heads up, on the river.**
Board `AsKd7h5c2s`, all five cards known. Pot 20, opponent bets 10 (half pot). Hero holds a pure
bluff-catcher.

- Threshold: the `1/2 pot` row of Example 2 → MDF 66.67%, equity needed to call 25.00%, bluff share 25.00%.
- There is no equity left to compute here. Ask the engine for it and it refuses:
  `error: a board of five cards has no equity left to compute`. The cards are dealt; what remains is
  a comparison, not a probability. **On the river the test is the share of air in the opponent's
  betting range**, never "how much equity do I have".
- Arithmetic: if exactly 25% of that betting range is air, calling is worth
  `0.25 × (20 + 2 × 10) − 10 = 0`. Above 25% it is a call, below it is a fold.
- Quota: the same row says the bettor needs a 33.33% fold rate for the size to break even, so Hero's
  range must keep 66.67% alive — and bluff-catchers are what that 66.67% is made of.

## 范围图 / Range chart

An orientation lesson issues no range chart, because it has no "which range must defend" question yet.
This section starts carrying weight from chapter 01 onward. In strategy lessons it holds a `range.*`
chart from `tools/gen_ranges.py`, and the reading rule never changes: **the chart is a quota, not a
plan.** For instance `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` records `threshold`
0.66666667, `total_combos` 884 and `range_percentage` 66.67%. That answers only "how many combos must
continue against a half-pot bet"; it says nothing about which cards do.

First, look at a real 13×13 grid on the command line
(`PYTHONPATH=src python -m pokergto range "22+,ATs+" --lang zh`):

```text
     A  K  Q  J  T  9  8  7  6  5  4  3  2 
A    @@ .. .. .. @@ @@ @@ @@ @@ @@ @@ @@ @@
K    .. @@ .. .. .. .. .. .. .. .. .. .. ..
Q    .. .. @@ .. .. .. .. .. .. .. .. .. ..
J    .. .. .. @@ .. .. .. .. .. .. .. .. ..
T    .. .. .. .. @@ .. .. .. .. .. .. .. ..
9    .. .. .. .. .. @@ .. .. .. .. .. .. ..
8    .. .. .. .. .. .. @@ .. .. .. .. .. ..
7    .. .. .. .. .. .. .. @@ .. .. .. .. ..
6    .. .. .. .. .. .. .. .. @@ .. .. .. ..
5    .. .. .. .. .. .. .. .. .. @@ .. .. ..
4    .. .. .. .. .. .. .. .. .. .. @@ .. ..
3    .. .. .. .. .. .. .. .. .. .. .. @@ ..
2    .. .. .. .. .. .. .. .. .. .. .. .. @@
图例: .. <1%  :: 1-34%  ++ 34-67%  ## 67-90%  @@ >90%
```

Three readings: the diagonal is pairs, one triangle is suited and the other offsuit (the axis
convention is fixed in `pokergto.matrix13.Grid13`, and `range.02-03.mdf-floor-vs-half-pot` cited above
records the same convention in its `orientation` field); a cell's shade is **how many of that cell's
combos are included**, not "how
hard should I play this hand"; and 13 filled diagonal cells are 13 × 6 = 78 combos, which ties exactly
back to Example 4's decomposition.

## 为何成立、何时失效 / Why it works, when it breaks

The reading method works while **`data/gen` is the same age as the code**. It stops working in these
situations, all of which are reachable today:

1. `data/gen/**` falls behind `src/pokergto/**`. The table is the old one, the formula is new.
   Detect it with `python tools/gen_all.py --check`, which recomputes the whole tree and byte-compares
   it; it is read-only, so nothing you check will dirty the working copy.
2. You are reading a cached site instead of the repository. Generated files move with commits, and
   `data/gen/manifest.json` stores a sha256 for each one.
3. The lesson is `draft`. `data/gen/index.en.json`'s `totals` says how far the spine has actually been
   authored -- read it rather than trusting a count quoted in prose, because a draft section may still
   be scaffolding and a number may not yet be wired to an
   AUTO block.
4. Someone edited a digit inside an AUTO block. That is this repository's category error, and
   `inject_doc_tables.py --check` says so in public.
5. You go looking for a file by lesson id. Paths contain slugs only.

## 陷阱 / Common mistakes

1. **"Correcting" a number inside an AUTO block.** You edited a copy, not the source.
   *Cost*: `python tools/inject_doc_tables.py --check` immediately reports `AUTO block ... is stale`;
   worse, a reader who never ran it now has two different numbers across 184 files and no mechanism
   to tell them which is real.
2. **Treating a lesson id as a path.** `02-03` is a permanent number; the file name is the slug.
   *Cost*: `check_bilingual.py` maps file names back to ids with `stem_to_id()`, so guessing wrong
   creates an orphan file *and* a registered-but-missing lesson, and reports both.
3. **Reading `reference` as if it were `derived`.** `adr/0005` permits `reference` only for authored
   content that is independently checkable.
   *Cost*: the widely quoted "continuation-bet frequency collapses as players are added" is carried
   here as `reference` plus unverified (see `NOTICE`). Treating it as engine output means building
   ranges on a number nobody derived. What to do instead: open the artifact's `unverified_claims`,
   follow `derivation_ref` to see whether an executable symbol exists, then run
   `mdf --pot 10 --bet 5 --opponents 2` yourself — the 42.27% per defender and 66.67% joint defense it
   prints are the derived facts.
4. **Sizing a range by class count.** Example 4 gives 114 ÷ 22 ≈ 5.2, while real classes hold 4, 6 or
   12 combos.
   *Cost*: 12 ÷ 4 = 3, so a per-class average can be off by a factor of three inside one rank class,
   and any MDF quota built on it is wrong.

## 练习 / Drills

- From `data/src/curriculum.yaml` alone, state the file path of `07-01` and its prerequisites, then
  open the file and count its sections: is it 15?
- Run `PYTHONPATH=src python -m pokergto mdf --pot 12 --bet 12 --opponents 2` and compare the
  per-player figure with the pot-sized block of `data/gen/tables/table.07-01.multiway-defense.json`.
- Run `PYTHONPATH=src python -m pokergto range "88+,AKs,AQs" --json`; state the 50.0 combos, 3.7707%
  and 9 classes, then explain why `canonical_spec` comes back as `88+,AKs-AQs`.
- Change one digit inside an AUTO block, run `python tools/inject_doc_tables.py --check`, read the
  whole sentence, then put it back.
- Explain why the AUTO id sequences of the Chinese and English files must be **equal element by
  element**, not merely "the same set".

## 自测清单 / Self-check

- [ ] I can get from a lesson id to its real file path and state what a slug does that an id does not.
- [ ] In any lesson I can point at which numbers came from an AUTO block and which are arithmetic.
- [ ] I can read `<!-- provenance: kind=... verified=... -->` and name the three kinds' different permissions.
- [ ] I know the drill for `UNVERIFIED`: read `unverified_claims`, follow `derivation_ref`, re-run a command.
- [ ] I can lay out my four routes (100bb cash, MTT, heads-up/BvB, population) and say which chapter opens each.
- [ ] I can name the four streets, the required spellings for hole cards and board, and which field stores the rejected synonyms.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number in this lesson comes either from a command listed below or from a committed artifact
under `data/gen/`. No range chart or strategy output from a commercial solver or a paid course appears
anywhere in it.

| Content | Source type | Location |
|---|---|---|
| 15-section template, lesson ids, prereq | Authored source of record | `data/src/curriculum.yaml`: `lesson_template`, `chapters` |
| 92 lessons / 184 files, and how many are `ready` | Generated artifact | `data/gen/index.en.json` `totals` -- read the count there; this lesson deliberately does not quote one |
| MDF, equity needed, bluff share | `derived` | `src/pokergto/odds.py`; `pokergto mdf`, `pokergto odds` |
| 114 combos / 8.60% / 22 classes | `derived` | `pokergto range "22+,ATs+"`; `data/gen/tables/table.01-01.combo-decomposition.json` |
| 37.26%, 46.77%, 10.72%, 17.49% | `derived` | `pokergto equity ... --mode exact`, enumerating 1,176 runouts, standard error 0 |
| Half-pot defense quota 884 / 66.67% | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` |
| Multiway continuation-bet collapse figures | `reference` + **UNVERIFIED** | `NOTICE`, `adr/0005`; not usable as a conclusion until `theory/multiway.py` reproduces them |
| 13×13 axis order and legend | Implementation convention | `src/pokergto/matrix13.py#Grid13`, `src/pokergto/render.py` |

## 术语 / Terms

<!-- terms: hole-cards, board, street, preflop, flop, turn, river, pot, bet, raise, call, fold, check, hero, villain, six-max, position, button, small-blind, big-blind -->

The Chinese, English and rejected columns below are taken from `data/src/glossary.yaml`. Chinese poker
vocabulary has no industry standard, so that file *is* the standard for this repository; the "不写"
column is the same entry's `avoid` field.

| Abbrev | 中文 | English | Meaning in this lesson | Avoid |
|---|---|---|---|---|
| — | 底牌 | Hole cards | the two cards dealt to you | 私牌、手牌 |
| — | 公共牌面 | Board | the shared cards, shortened to 牌面 | 公牌、桌面 |
| — | 街 | Street | one betting round after one deal | 轮、下注轮次 |
| — | 翻前 | Preflop | before the first three community cards | — |
| — | 翻牌圈 | Flop | the round of the first three | — |
| — | 转牌圈 | Turn | the round of the fourth | — |
| — | 河牌圈 | River | the fifth card; the hand is fixed | — |
| — | 底池 | Pot | money already in the middle | — |
| — | 下注 | Bet | the money newly added | — |
| — | 加注 | Raise | topping what is already bet | — |
| — | 跟注 | Call | matching to the same level | — |
| — | 弃牌 | Fold | giving up the pot | — |
| — | 过牌 | Check | neither betting nor folding | 让牌 |
| — | 我方 | Hero | the side being analysed | 主角 |
| — | 对手 | Villain | the other side, unjudged | 坏人 |
| — | 六人桌 | Six-max | seat count of a full cash ring | — |
| — | 位置 | Position | the information edge of acting later | 座位 |
| BTN | 按钮位 | Button | acts last on every street | — |
| SB | 小盲注 | Small blind | the forced half-bet already in the pot | — |
| BB | 大盲注 | Big blind | the forced full bet already in the pot | — |
