# Game trees, information sets and strategy profiles: what a player can actually see

<!-- hands: 2 -->
<!-- terms: game-tree, information-set, strategy-profile, mixed-strategy, solver, generated-artifact, determinism, combos, hand-class, range -->

## 本节目标 / Objectives

- State, in one sentence each, how a node, an information set and a strategy profile differ, and name which one this repository's solver stores rows by.
- Count Kuhn's 6 deals, 9 nodes, 4 decision nodes and 12 information sets by hand, and explain why the answer is 12 rather than 24.
- Explain why "public tree plus private vector" is the right mental model: the tree is shared, the vector is cut by my own hole cards.
- Explain why one information set must carry one frequency distribution, and what is wrong with the kind of "best response" that violates it.

## 前置知识 / Prerequisites

- `00-02` Derivation over memory: a number that cannot be recomputed by the engine is not evidence.
- `02-04` Indifference conditions: the reason a mixed strategy exists at all is that two actions have equal expected value.

## 核心原理 / The principle

Three objects. Do not merge them.

1. **Game tree**: every possible deal of chance, plus the public decision nodes, plus the terminals. This repository stores it as "one node carrying a vector over deals" (`src/pokergto/solver/tree.py`).
2. **Information set**: `(node, my private cards)`. Swapping only the opponent's card at the same node leaves the information set unchanged.
3. **Strategy profile**: a table mapping information sets to action distributions. One row per information set, each row summing to one.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Definition and implementation: `src/pokergto/solver/tree.py#TreeBuilder.add_decision`, whose merge key is `(node, player, private_key)`.
>     Counts: `config.tree` in `data/gen/solver/kuhn.json`. The Derivation section gives the command that recomputes them on the spot.

## 推导 / Derivation

Kuhn poker: cards `J < Q < K`, each player antes 1, one street, bet size 1, no raises, player 0 acts first (`src/pokergto/solver/games.py#kuhn`).

**Deals.** Two distinct cards dealt in order: `permutations(("J","Q","K"), 2)` = 6 deals, each with prior probability 1/6:

```
0:(J,Q) 1:(J,K) 2:(Q,J) 3:(Q,K) 4:(K,J) 5:(K,Q)      # (P0's card, P1's card)
```

**Nodes.** Nine: 4 decision nodes and 5 terminals.

```
node 0  P0: check|bet           node 1  P1 after a check: check|bet
node 2  P0 facing a bet: fold|call   node 3  P1 facing a bet: fold|call
node 4  check-check showdown     node 5  P0 folds    node 6  P0 calls
node 7  P1 folds                node 8  P1 calls
```

**Information sets.** Six deals pass through every node, but each player sees only their own card, so node 0's six deals collapse into 3 information sets (`0:0:J`, `0:0:Q`, `0:0:K`). The code makes this visible:

```python
>>> kuhn(1.0).nodes[0].infosets      # information set index, per deal
array([9, 9, 10, 10, 11, 11])       # paired because the merge is on P0's own card
>>> kuhn(1.0).nodes[1].infosets
array([6, 7, 8, 7, 8, 6])           # same node, shuffled order: it merges on P1's card
```

4 decision nodes × 3 private labels = **12 information sets**. Recompute it:

```bash
PYTHONPATH=src python -c "from pokergto.solver.games import kuhn; print(kuhn(1.0).summary())"
# {'deals': 6, 'nodes': 9, 'decision_nodes': 4, 'terminal_nodes': 5, 'infosets': 12}
```

**Why not 24.** 24 = 4 nodes × 6 deals, which is the number of decision points for a player who can see the opponent's card. An information set deletes that dimension: the merge key in `tree.py` is `(node_id, player, my own card)`, never the opponent's card and never anything beyond what the node already makes public.

**The same code on the one-street game.** `one_street_bluff_catcher(pot=1, bet_size=0.5)`: 2 deals (`nut` and `air`, half each), 5 nodes, 2 decision nodes, 3 information sets. Its second node holds a single row -- both deals map to the same information set `1:1:catcher`, because a bluff-catcher cannot tell nut from air:

```bash
PYTHONPATH=src python -c "from pokergto.solver.games import one_street_bluff_catcher as g; print(g(1.0,0.5).summary())"
# {'deals': 2, 'nodes': 5, 'decision_nodes': 2, 'terminal_nodes': 3, 'infosets': 3}
```

## 直觉 / Intuition

**Public tree, private vector.** Picture the tree on a wall where both players can see it, including every action already taken. The one thing you cannot see is the card in front of your opponent. So "your situation" = a node on the wall ⊕ your own card, and the solver stores exactly that split: nodes are shared, an information set is one private slice of a node.

One line to keep: **a strategy is a table whose rows are information sets -- not nodes, not hands.**

- Rows set the problem size: Kuhn has 12, the one-street game has 3, and both solve exactly on a laptop.
- A row holds frequencies (a `mixed-strategy`), not an action. The frequencies are not hesitation; they are the only device that stops your behaviour from disclosing your hand (`02-04`).
- A range chart is one layer of that table at real scale: every cell belongs to some information set, and the cell's colour is that row's frequency for one action.

## 算例 / Worked examples

**Example 1 -- which rows one deal touches.** Deal 1 = `(J,K)`: P0 holds `J`, P1 holds `K`. On the line check -> bet -> fold the deal walks through three rows: `0:0:J` (P0 checks), `1:1:K` (P1 bets), `2:0:J` (P0 folds). Three information sets, three rows of frequencies, one deal threading them. Note that step 2 is not `1:1:J`: that row belongs to the two deals where P1 holds the jack.

**Example 2 -- two deals, one row, one frequency.** `0:0:J` covers deal 0 `(J,Q)` and deal 1 `(J,K)`. The committed artifact gives that row a bet frequency of **0.213282** (`data/gen/solver/kuhn.json`, `average_strategy["0:0:J"]["bet"]`). Writing "bluff 30% when he holds Q, 10% when he holds K" is not a strategy; it is knowledge of your opponent's card. Exploitability refuses it by definition: a best response must commit to **one action per information set** (`src/pokergto/solver/exploitability.py`), and an argmax taken per deal measures "how well does someone who sees your cards do", which is not a property of the strategy.

**Example 3 -- how to read a terminal payoff vector.** Node 5 (P0 folds) carries six copies of `-1`: card strength irrelevant, folding forfeits the ante. Node 6 (P0 calls) carries `[-2,-2,2,-2,2,2]`, whose sign is exactly `sign(P0 card - P1 card)`. Player 1's payoff is the negative: every game here is zero-sum, and `games.py` fixes the accounting convention in its module docstring -- terminal payoffs are net chips **from the start of the hand**, antes already committed.

**Example 4 -- how big the private dimension is in real hold'em.** A preflop hand has 1,326 combos (table below). Bucketed by hand class it is 169 rows; bucketed into strength buckets it might be 5 to 9 rows. Solver size is never set by node count; it is set by **rows × actions per row × number of streets**. That product is the only thing card abstraction trades on, which is lesson 08-06's subject.

## 生成表 / Generated tables

Size the private dimension in real hold'em once, so the scale discussion has a floor under it:

<!-- BEGIN AUTO:table.01-01.combo-decomposition -->
|   Shape | Classes | Combos each |        Combos |
|---:|---:|---:|---:|
|   pairs |      13 |           6 |  78.00 combos |
|  suited |      78 |           4 | 312.00 combos |
| offsuit |      78 |          12 | 936.00 combos |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.cards#combos_for_class`

<!-- generated by: tools/gen_tables.py from pokergto.cards::combos_for_class -->
<!-- END AUTO:table.01-01.combo-decomposition -->

`78 + 312 + 936 = 1326`. The same deck read differently: 13 pair classes of 6 combos, 78 suited classes of 4, 78 offsuit classes of 12. Storing private information by class gives 169 rows; by combo gives 1,326. Both are legitimate definitions of an information set -- what differs is whether you admit suited-versus-offsuit as distinguishable private information. **Before reading any solver chart, ask at which granularity its rows were built.**

## 实战牌局 / Live hands

Both hands go through the solver for their numbers: the first plays one Kuhn hand to the end, node by node; the second is a transfer hand that restates a real river spot in the same information-set language, with every number taken from committed artifacts.

**Hand 1 (`hand.08-01-kuhn-jack-versus-king`) -- deal 1: P0 holds `J`, P1 holds `K`.**

| Step | Node | Who acts | Information set (row) | That row's frequencies (from `kuhn.json`) | Running net chips, P0 |
|---|---|---|---|---|---|
| 1 | 0 | P0 | `0:0:J` | check 0.786718 / bet 0.213282 | ante already in: -1 |
| 2 | 1 | P1 | `1:1:K` | bet 1.0 | - |
| 3 | 2 | P0 | `2:0:J` | fold 1.0 / call 0.0 | -1 |

- Step 3 is not a judgement call, it is a strictly dominated action being excluded: `J` never wins a showdown, so calling only adds a chip to a lost pot. `proofs.py#assert_jack_never_calls` asserts exactly this (measured 0 against a tolerance of 1e-3).
- The hand ends at node 5 with payoff -1: P0 loses the ante. Had P0 bluffed on step 1 and P1 folded `Q`, the terminal would be node 7 with payoff +1. There are only four possible outcomes in this game, -2, -1, +1, +2, and all five payoff vectors are written out in `games.py#kuhn`.

**Hand 2 (`hand.08-01-river-bluff-catcher-one-row`) -- heads up, river `AsKd7h5c2s`, opponent bets pot.**

Pot 20, opponent bets 20. You hold `JhTh`, which beats nothing but air.

- Your situation is one information set: `(river decision node, JhTh)`. You cannot see the opponent's cards, so the two real-world states "he has the nuts" and "he is bluffing" must be met with **one and the same frequency** (the MDF quota here is 50%, the `1x pot` row of `table.02-03.mdf-vs-sizing`).
- That is precisely the shape of the one-street game's `1:1:catcher` row: 2 deals, 1 row of strategy. The solver's defense frequency 0.666668 at half pot differs from the algebra `pot/(pot+bet)` by 1.33e-6 (`data/gen/solver/toy_1street_half_pot.json`).
- What transfers is the structure -- one row covering several real states, with the frequency pinned by an indifference condition. What does not transfer is the number: the toy bettor holds only two buckets, while a real river range runs to hundreds of combos, several sizes, and your fold feeds back into his later-street choices. Drawing that boundary is lesson 08-07's job.

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

The chart above is this section's object at real scale: **one information-set layer** (facing a half-pot bet) rendered as a strategy. Every cell belongs to some information set, the fill is that row's continuation frequency, and combos are stacked in strength order until they cover `MDF = 66.7%`.

Read it with the vocabulary of this section:

- It is a **slice of a table**, not a plan. The same table has the raise column of this node and every row of the turn and flop nodes.
- Its granularity is the hand class (169 of them). A solver may equally store the same layer by combo (1,326) or by bucket; abstraction merges information sets, and only merged ones. **Asking "at what granularity is this drawn" beats asking "why is this cell red".**
- No chart generator exists for Kuhn or the one-street game. `data/gen/ranges/` holds this one file, and it comes from `pokergto.odds`, not from a solver. For a toy game the "chart" *is* the 12-row frequency table, sitting in `data/gen/solver/kuhn.json`.

## 为何成立、何时失效 / Why it works, when it breaks

**What makes it hold:** perfect recall. Each player remembers their own actions and all public actions, and is merely unable to distinguish private deals. Because `TreeBuilder` keys rows by `(node, player, private_key)` and the node already encodes the public history, perfect recall is structural here rather than assumed.

It stops being free in these cases:

1. **After card abstraction.** Putting `AhKh` and `AhQh` in one bucket creates an information set that cannot see its own cards. The strategy is still defined on the merged row, but the true optimum could have separated them, and that gap is the abstraction error. 08-06 measures its direction.
2. **Multiway pots.** Every opponent brings a private vector. The row-per-information-set structure survives; the balance constants do not, because a bluff must beat everyone (`07-01` derives `d = 1 - (B/(P+B))^(1/N)`).
3. **Games with imperfect recall.** Lines that reconverge on a board can blur a real player's memory of their own action. That is a distinct theoretical difficulty and this repository does not model it.
4. **Model size.** Leduc is where "free" stops being free: 360 deals, 85 public nodes and **3,780 information sets**, against 12 rows for Kuhn. The per-deal recursion spends about 0.23 s per iteration there, so the 10,000 iterations its gate registers would take about thirty-eight minutes; the public-tree form in `solver/vector.py` does the same solve in 35 s, and it has to clear every registered gate before it may write an artifact (`tests/test_solver_vector.py`). What `adr/0002` refuses is a game with no validation anchor -- `tools/run_solver.py` errors out for anything missing from `solver/proofs.py` -- and a two-street toy with no closed form is where that refusal still bites. Leduc got in because three gates that need no closed form were writable for it; `08-04` names them.
5. **What does transfer to real hold'em:** why an information set is one row (you cannot see the opponent), the habit of asking granularity before numbers, and the discipline that a per-deal argmax is not a best response. **What does not:** 12 rows solve exactly, a real postflop tree does not, and this project deliberately cut the 6-max postflop solver (`adr/0002`, Rule B).

## 陷阱 / Common mistakes

1. **Reading a node as an information set.** "What do I do on this flop" is a node; "what do I do on this flop holding this hand facing this bet" is a row.
   *Cost*: in Kuhn the counts are 4 nodes, 12 information sets, 24 decision points for a card-peeker. Planning with 24 overestimates the problem by a factor of two; writing strategy with 4 merges distinct hands into one row, which is cheating, not strategy. `kuhn(1.0).summary()` prints all three numbers at once.
2. **Giving the two deals inside one information set different frequencies.** "Bluff when he has Q, fold when he has K" branches on hidden information.
   *Cost*: your EV table looks implausibly good, because the solver's best response commits per information set while your "strategy" commits per deal -- the two are no longer in the same space. `exploitability.py` names this error, and `np.bincount(node.infosets, ...)` is the line that prevents it.
3. **Reading the number before asking the granularity.** Copying "KTs defends 60% here" without knowing whether that row is combo-level, class-level or bucket-level.
   *Cost*: a bucket's 60% can decompose into 40% and 90%, and you spend the extra quarter of your quota on the weakest combos. Check the distribution yourself with `python -m pokergto range "22+,ATs+"`, which prints the combo total.
4. **Treating an information set as "everything I know".** The board and the opponent's actions are known, but they do not split information sets; the node already carries them.
   *Cost*: duplicate rows that learn separate regrets for one decision. Convergence slows and the result is not equivalent to the single row.

## 练习 / Drills

- Recompute the counts live: `kuhn(1.0).summary()`, `one_street_bluff_catcher(1.0, 0.5).summary()`, then print `nodes[0].infosets` and `nodes[1].infosets` and say in one sentence why they merge on different cards.
- By hand: if Kuhn allowed one raise (P0 may raise back to 2 after P1 bets), how many nodes and how many information sets? (Hint: the new node splits only along P0's three private labels.)
- By hand: if the bluff-catcher game gave player 1 three buckets (nut / bluff-catcher / air), how many information sets, and how many frequencies in total?
- With `python -m pokergto range "88+,AJs+,KQs,QJs+,JTs"` and `python -m pokergto odds --pot 30`: state first whether your private granularity is 169 classes or 1,326 combos, then talk frequencies.

## 自测清单 / Self-check

- [ ] I can distinguish node, information set and strategy profile in one sentence, and quote Kuhn's 6/9/4/12.
- [ ] I can explain why `0:0:J` covers two deals yet has one row of frequencies.
- [ ] I can name the merge key this repository uses for information sets and why the opponent's card is never in it.
- [ ] I can explain why a per-deal argmax measures cheating rather than exploitability.
- [ ] Before reading a solver chart, I ask what granularity its rows were built at.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number here is recomputable with one command. No range chart or strategy output from a commercial solver or paid course appears anywhere in this lesson:

| Content | Source type | Location |
|---|---|---|
| Definitions of tree, information set, merge key | `derived` | `src/pokergto/solver/tree.py#TreeBuilder.add_decision`, `GameTree.summary` |
| Kuhn counts 6/9/4/5/12 | `derived` | `config.tree` in `data/gen/solver/kuhn.json`; command in the Derivation |
| Kuhn's 12 average-strategy rows | `derived` | `average_strategy` in `data/gen/solver/kuhn.json`, 20,000 CFR+ iterations |
| Kuhn payoff vectors (-2, -1, +1, +2) | `derived` | `src/pokergto/solver/games.py#kuhn` |
| One-street counts 2/5/2/3/3 | `derived` | `config.tree` in `data/gen/solver/toy_1street_half_pot.json` |
| The 1,326 combo decomposition | `derived` | `data/gen/tables/table.01-01.combo-decomposition.json` |
| MDF floor range chart | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` (algebra, not solver output) |
| The Leduc tree shape (360 deals, 85 nodes, 36 decision, 49 terminal, 3,780 infosets) | `derived` | `config.tree` in `data/gen/solver/leduc.json`, asserted again in `tests/test_solver.py` |
| The Leduc solve (value -0.043661 chips/hand, exploitability 2.25e-6) | `derived` | `data/gen/solver/leduc.json`; gate at `src/pokergto/solver/proofs.py#leduc` |
| A two-street toy with a closed form | not implemented | `adr/0002` and `docs/development/solver-proof-policy.md` argue the refusal |
| The real river spot in hand 2 | `reference` + **UNVERIFIED** | author-built illustration; its only factual numbers (MDF 50%, defense 0.666668) come from the `derived` artifacts above |

## 术语 / Terms

<!-- terms: game-tree, information-set, strategy-profile, mixed-strategy, solver, generated-artifact, determinism, combos, hand-class, range -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 博弈树 | game tree | public nodes plus a vector over deals; not a machine-learning decision tree |
| — | 信息集 | information set | `(node, my cards)`; one row of the strategy |
| — | 策略组合 | strategy profile | the whole table; unrelated to "combos" |
| — | 混合策略 | mixed strategy | the frequencies inside one row, pinned by indifference |
| — | 求解器 | solver | this repository's own CFR implementation |
| — | 生成物 | generated artifact | the JSON files under `data/gen/**` |
| — | 确定性输出 | determinism | same input, same bytes; the toy solvers sample nothing |
| — | 组合数 | combos | 1326 = 78 + 312 + 936 |
| — | 手牌类别 | hand class | 169 of them; the other private granularity |
| — | 范围 | range | never "hand range" |
