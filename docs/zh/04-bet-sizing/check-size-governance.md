# 过牌的范围同样要被治理：过牌线里必须留什么

<!-- hands: 2 -->
<!-- terms: checking-range, checking-frequency, minimum-defense-frequency, defend, fold-frequency, required-equity, capped-range, combos, bet-size, indifference -->

## 本节目标 / Objectives

- 能用 `minimum_defense_frequency` 与 `equity_needed_to_call` 写出一条过牌线的"必须继续的组合数"与"必须弃掉的组合数"，并把它们换算到 1326 个组合数上。
- 能用一个计数条件（低于门槛胜率的组合数是否够付弃牌税）判断过牌线缺不缺底端牌，并把缺位的代价算成筹码。
- 能用 `is_capped` 判断过线缺不缺顶端牌，并说出缺位时对手的空气在任意尺度上每手能拿走多少。
- 能说明"过牌尺度治理"这个函数本身在本仓库不存在（`src/pokergto/theory/__init__.py` 记录了它被删除的原因），本节只治理它的必要条件。

## 前置知识 / Prerequisites

- `02-03` MDF 的推导与它的补 `f = B/(P + B)`。
- `02-02` 所需胜率 `B/(P + 2B)`；`03-02` 封顶范围与行动线。
- `04-01` 频率法与范围法的分工；`04-05` 顶段存在性是形状的前提。

## 核心原理 / The principle

一条过牌线（你以过牌继续的那部分范围）在被下注时必须同时满足两件事，而它们不是同一件事：

1. **继续的总占比 ≥ MDF**（`pokergto.odds.minimum_defense_frequency`）。这是`derived`，且它只看总占比：`theory/frequencies.py` 的文档明确写了"防守频率是继续的组合数占比，跟注频率只是其中一个动作的份额"，`defense_indifference_gap` 的入参也只有一个合计值。
2. **这个占比要用什么样的牌去满足。** MDF 对"用哪些组合数达到它"完全沉默——范围图的 `assumptions` 里也这么写。于是过牌线可以数值上达标而战略上死亡。

本节给出两个可算的判据，它们正是"过牌线必须自带的两类牌"：

- **底端**：低于门槛胜率 `B/(P + 2B)` 的组合数，数量必须够付弃牌税 `(1 − MDF)·N`。不够时，每一次弃牌弃掉的都是 `EV(call) > 0` 的牌，代价可以直接乘出来。
- **顶端**：`is_capped` 为假。为真时对手的纯空气在任意尺度上每手拿走整个底池（`EV(bluff) = 1·P − 0·B = P`，与尺度无关）。

**"该给过牌线配多大尺度"这个治理函数本身，本仓库没有实现**，`src/pokergto/theory/__init__.py` 把它列为"刻意缺席"的四项之一。所以本节治理的是必要条件，不是充分条件。

## 推导 / Derivation

设过牌线有 `N` 个组合数，面对尺度 `B`（底池 `P`）。

**第一步：两个门槛。**

```
必须弃：   (1 − MDF)·N = [B/(P + B)]·N
必须留下： MDF·N = [P/(P + B)]·N
单组合数该弃： EV(call) = e(P + 2B) − B < 0   ⟺   e < B/(P + 2B)
```

`P = 1` 时门槛胜率是 1/3 池 `20.00%`、半池 `25.00%`、3/4 池 `30.00%`、底池 `33.33%`、2 倍池 `40.00%`（`table.02-02.equity-needed-to-call` 与 `table.02-03.mdf-vs-sizing` 同一列）。

**第二步：底端缺位的代价。** 记"便宜弃牌数" `C` = 门槛以下的组合数。若 `C ≥ (1 − MDF)·N`，弃牌税可以全部由空气支付，成本 `0`；若 `C < (1 − MDF)·N`，短口的 `n = (1 − MDF)·N − C` 手必须从 `e ≥` 门槛的牌里出，每手弃掉的期望值是 `e(P + 2B) − B`。

例：`N = 100`，`B = 1/3 池`，全部 100 手的 `e = 0.30`（没有底端）。`C = 0`，`n = 25`，每手 `EV(call) = 0.30 × (1 + 2/3) − 1/3 = 0.166667` → 成本 `25 × 0.166667 = 4.166667` 个筹码，每 100 手牌 4.166667（即每手 `0.041667`）。

**第三步：拒绝付税会怎样。** 对手不强制你弃牌，他会**换尺度**。`e = 0.30` 面对底池时 `EV(call) = 0.30 × 3 − 1 = −0.10`，面对 2 倍池 `= 0.30 × 5 − 2 = −0.50` → 全部该弃，于是 `f = 1`，他的空气 `EV(bluff) = 1 × P − 0 × B = 1.000000`（1/3 池、底池、2 倍池三个尺度算出来完全相同，因为 `f = 1` 时 `B` 根本没进过账）。**这就是"底端缺位时对手立刻拿走的东西"：每手 1 个底池，且尺度无关。**

**第四步：顶端缺位是同一句话的另一半。** `is_capped(N 里的最强手) = true` 意味着过牌线里没有能加注、也没有能在最大尺度上跟注的牌；对手的 `f → 1`，第三步的 `EV(bluff) = P` 同样成立。区别在于：底端缺位让他用**大尺度**逼你弃，顶端缺位让他用**任意尺度**白拿。判据本身（`pokergto.theory.range_advantage.is_capped`）是`derived`——它拿范围里最强手的评分与"任意两手牌在该牌面能达到的上限"比较，差超过 `tolerance` 步即判为封顶。

**第五步：MDF 只认合计。** `defense_indifference_gap(P, B, d)` 里 `d` 是一个合计防守占比；`balance_bluff_and_value` 输出的 `exploitable_side` 只看这个合计与诈唬占比。所以"我用 25% 加注 + 41.67% 跟注"与"我用 66.67% 跟注、0 加注"在 MDF 眼里一模一样。**这就是为什么顶端缺位能骗过一个数值达标的过牌线**：地板线测不到它。

## 直觉 / Intuition

过牌线不是一个"剩下的篮子"，它也是一条主张：他打 1/3 池我要留 75%，他打 2 倍池我要留 33.33%。**这 75% 里必然包含打不赢的牌**——因为整个 1326 里根本没有 994.5 手打得赢 1/3 池的牌。底端牌的作用不是赢，是"用它们付弃牌税"，把好牌留在跟注里。

顶端牌的作用是让"加注"这个威胁存在。MDF 看不见它，但对手看得见：一旦他知道你这条线里最长的牌也只是第二对，他就把尺度推到你的门槛之上，让你的正确反应变成弃牌，然后空气开始印钱。

## 算例 / Worked examples

**例 1 — 五个尺度的弃牌与继续的组合数（`P = 1`，按 1326 个组合数展开）。**

| 尺度 | MDF | 必须继续的组合数 | 必须弃的组合数 | 弃牌门槛胜率 |
|---|---|---|---|---|
| 1/3 池 | 75.00% | 994.5 | 331.5 | 20.00% |
| 1/2 池 | 66.67% | 884.0 | 442.0 | 25.00% |
| 3/4 池 | 57.14% | 757.71428 | 568.28571 | 30.00% |
| 底池 | 50.00% | 663.0 | 663.0 | 33.33% |
| 2 倍池 | 33.33% | 442.0 | 884.0 | 40.00% |

复现：`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds; [print(float(B), float(odds.minimum_defense_frequency(1,B,exact=True)*1326), float((1-odds.minimum_defense_frequency(1,B,exact=True))*1326), float(odds.equity_needed_to_call(1,B))) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))]"`。第一行的 994.5 与 `range.04-02.mdf-floor-vs-third-pot` 图上的"覆盖 994.5 组合"逐字吻合。

**例 2 — 底端在位的过牌线：100 个组合数 = 75 手 `e = 0.30` + 25 手 `e = 0.05`，面对 1/3 池。** 门槛 20.00%：只有 25 手空气低于它，而必须弃的正好是 `[1/3 ÷ (1 + 1/3)] × 100 = 25` 手。`C = 25 = 要求`，弃牌税成本 `0`；空气的 `EV(bluff) = 0.25 × 1 − 0.75 × 1/3 = 0.000000`（`odds.indifference_check(1, 1/3, 1/4)` → `True`）。**这就是"底端牌的价值"：它把对手的空气打到 0，而自己不损失任何正期望的跟注。**

**例 3 — 同一张线换对手换尺度：`e = 0.30` 的 75 手面对底池。** 门槛 33.33% > 30%，于是这 75 手的 `EV(call) = −0.100000`，全部该弃；25 手空气也弃 → `f = 1`，空气的 `EV(bluff) = 1.000000`（任意尺度）。同一手牌在 1/3 池该跟（`+0.166667`）、在底池该弃（`−0.100000`），**门槛是尺度函数，牌力不是**——这就是 `02-02` 与 `04-02` 在本节的交点。

**例 4 — 底端缺位的账：100 手全在 `e = 0.30`，面对 1/3 池。** `C = 0`，短口 `n = 25`：`25 × 0.166667 = 4.166667` 个筹码 / 100 手。若这 25 手改成 `e = 0.45`（更强的线），每手弃掉 `0.45 × (5/3) − 1/3 = 0.416667`，成本升到 `10.416667` / 100 手——**线越强，缺底端时付的税越重**，因为弃掉的期望值更大。复现：`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(float(25*ev.ev_call(1,F(1,3),F(3,10))), float(25*ev.ev_call(1,F(1,3),F(45,100))))"`。

**例 5 — 均一弃牌率下对手该用哪个尺度（过牌线对每个尺度都弃 50%）。** `EV(bluff)`：1/4 池 `0.375000`、1/3 池 `0.333333`、1/2 池 `0.250000`、3/4 池 `0.125000`、底池 `0.000000`、2 倍池 `−0.500000`。**对手的最优惩罚尺度是最小的那一个**，不是最大的：惩罚过度弃牌要挑他"弃牌率刚好超过门槛"的尺度。复现：`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; [print(float(B), float(ev.ev_pure_bluff(1,B,F(1,2)))) for B in (F(1,4),F(1,3),F(1,2),F(3,4),F(1),F(2))]"`。

## 生成表 / Generated tables

MDF、门槛胜率与弃牌率要求（治理地板线的三列同源）：

<!-- BEGIN AUTO:table.02-03.mdf-vs-sizing -->
|    尺度 | MDF 防守频率 | 诈唬所需弃牌率 | 跟注所需胜率 |
|---:|---:|---:|---:|
| 1/4 pot |       80.00% |         20.00% |       16.67% |
| 1/3 pot |       75.00% |         25.00% |       20.00% |
| 1/2 pot |       66.67% |         33.33% |       25.00% |
| 2/3 pot |       60.00% |         40.00% |       28.57% |
| 3/4 pot |       57.14% |         42.86% |       30.00% |
|  1x pot |       50.00% |         50.00% |       33.33% |
| 3/2 pot |       40.00% |         60.00% |       37.50% |
|  2x pot |       33.33% |         66.67% |       40.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_tables.py from pokergto.odds::sizing_table -->
<!-- END AUTO:table.02-03.mdf-vs-sizing -->

同一门槛的另一侧写法——过牌线里的单手可跟/该弃的分界：

<!-- BEGIN AUTO:table.02-02.equity-needed-to-call -->
| 对手下注(倍底池) | 所需胜率 |
|---:|---:|
|        0.25x pot |   16.67% |
|    0.333333x pot |   20.00% |
|         0.5x pot |   25.00% |
|    0.666667x pot |   28.57% |
|        0.75x pot |   30.00% |
|           1x pot |   33.33% |
|         1.5x pot |   37.50% |
|           2x pot |   40.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.odds#equity_needed_to_call`

<!-- generated by: tools/gen_tables.py from pokergto.odds::equity_needed_to_call -->
<!-- END AUTO:table.02-02.equity-needed-to-call -->

顶端牌是否存在是机器判据，不是辩论；`is_capped` 用"该牌面任意两手牌能达到的上限"作参照：

<!-- BEGIN AUTO:table.03-02.capped-range-check -->
|   牌面 |    角色 |      组合数 |   范围最强手 | 牌面可达上限 | 是否封顶 |
|---:|---:|---:|---:|---:|---:|
| Kh7s3d |    hero | 44.0 combos |   三条 7 K 3 |   三条 K 7 3 |       是 |
| Kh7s3d | villain | 58.0 combos | 一对 K Q 7 3 |   三条 K 7 3 |       是 |
| AsKsQh |    hero | 65.0 combos |       顺子 A |       顺子 A |       否 |
| AsKsQh | villain | 80.0 combos | 一对 K A Q 9 |       顺子 A |       是 |
| 9h6d3c |    hero | 63.0 combos |   三条 9 6 3 |   三条 9 6 3 |       否 |
| 9h6d3c | villain | 48.0 combos |   三条 6 9 3 |   三条 9 6 3 |       是 |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.theory.range_advantage#is_capped`

<!-- generated by: tools/gen_tables.py from pokergto.theory.range_advantage::is_capped -->
<!-- END AUTO:table.03-02.capped-range-check -->

## 实战牌局 / Live hands

**牌局 1（`hand.04-07-checkline-no-air`）— 翻牌 `Kh7s3d`，我方在 BB 过牌后面对 1/3 池（底池 12 bb）。过牌线 100 个组合数，模型输入：全部是顶对弱踢脚与中对，被跟注胜率统一 `e = 0.30`，手里没有任何低于 20% 门槛的空气。**

- 账：1/3 池要求继续 75%、弃掉 25 个组合数，门槛胜率 20.00%；这条线里低于门槛的 `C = 0` → 短口 `n = 25`，成本 `25 × 0.166667 = 4.166667` 个筹码 / 100 手（`P = 1` 口径，按 `P = 12` 折算为 `50.0` bb / 100 手）。
- 决策：这条线不能按"弃 25 手"执行。要么 100 手全跟（此时对手的 bluff 期望值是 `−1/3`，但他会换尺度而不是继续亏钱），要么补进底端牌。本节的结论落在构建阶段：**先把 `C ≥ 25` 造出来，再谈这一手怎么打。**
- 对手立刻拿走的：一旦他把尺度推到底池，`EV(call) = −0.100000 × 12 = −1.2` bb/手，全部该弃，他的空气每手拿走 `1.000000` 个底池 = `12` bb。`compare` 给出的三个空气尺度期望值全部为 `1.000000` 且并列最优，检查（不下注）只有 `0`：**尺度选择在这种情况下无关紧要，因为 `f = 1` 时 `B` 不进账。**
- 修法可算：把 25 个组合数的 `e = 0.05` 空气放进来（例 2 的形状），弃牌税成本变 `0`，空气的期望值变 `0.000000`。

**牌局 2（`hand.04-07-checkline-capped`）— 转牌 `Kh7s3d4c`，我方 CO 先过牌，河牌面对 2 倍池（底池 40 bb，对手可用尺度到 2 倍池）。模型输入：我方过牌线最强手是 `KQ` 顶对两高牌，`is_capped` 判为真。**

- 判据来自 `table.03-02.capped-range-check`：`Kh7s3d` 那两行里 `range_best` 与 `ceiling` 不同（"三条 7 K 3" / "一对 K Q 7 3" 对 "三条 K 7 3"），`is_capped` 分别为 `true`/`true`。`4c` 之后坚果上限仍在 `9T`/两对以上，我的线里没有。
- 对手拿走什么：2 倍池要求我继续 33.33%（442 个组合数），而我的线里能跟 2 倍池的手需要 `e ≥ 40.00%`（`table.02-02.equity-needed-to-call`）；封顶的线里能过这个门槛的组合数为 `0` → `f = 1` → 空气 `EV(bluff) = 40` bb/手（`1.000000` 个底池）。
- 决策：这条线必须**在转牌圈就不用过牌**（把 `KQ` 类拿到下注或加注线里），因为治理过牌线的手段是"构建时分配组合数"，不是"临场决定不弃牌"。
- 与底端缺位的区别写清楚：底端缺位时对手靠**加大尺度**逼你弃牌；顶端缺位时对手靠**任意尺度白拿**，而且他不需要弃牌率超过门槛——`EV(bluff) = P` 与 `B` 无关，这是本节唯一一条"尺度无关"的结论。

## 范围图 / Range chart

1/3 池的地板线要求继续 994.5 个组合数，这就是"底端牌必须存在"的证据：

<!-- BEGIN AUTO:range.04-02.mdf-floor-vs-third-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | :: | ·· |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 7 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 6 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 5 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 4 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 3 | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |
| 2 | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |

覆盖 994.5 组合 = 全 1326 的 75.00%

图例：`··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%；对角线为对子，上三角同花，下三角不同花。

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.04-02.mdf-floor-vs-third-pot -->

75.00% 的 1326 里，装不下纯粹"打得赢 1/3 池"的牌——图按牌力从高到低填充（`assumptions` 写明），所以它的**下边缘本身就是空气与抓诈唬牌**。读这张图的正确方式是：它给出你必须拥有的底端数量下界，而不是"该弃哪些"。它不能告诉你：加注与跟注怎么分（第五步：MDF 对分法沉默），也不能告诉你这条线缺不缺顶端（`is_capped` 才管这个）。

## 为何成立、何时失效 / Why it works, when it breaks

**成立的前提**：底池 `P` 与尺度 `B` 固定；`f` 指合计继续占比；门槛胜率用全压胜率口径（忽略后续街的实现差）；单街、无加注分支。

**失效之处**：

1. **门槛胜率不等于真实价值。** `e` 是"把钱推进去"的胜率；一条线在转牌与河牌还能实现多少，属于胜率实现（`01-06`），而本仓库**没有实现 EqR**（`src/pokergto/theory/__init__.py`）。所以本节所有 `C` 与 `n` 都是"以全压口径计"的下界估计，不是现实成本。
2. **治理函数本身缺席。** "过牌线该配多大尺度、哪一段用加注"这类判断需要范围层的答案，`src/pokergto/theory/__init__.py` 把 bet-size governance 列为刻意不实现的四项之一。本节给的是必要条件与代价账，不是策略表。
3. **加注分支未建模。** 第五步说 MDF 对分法沉默，但真实对手的诈唬面对加注时必须弃或跟，这会改变他的空气期望值；要算它需要两街解（本仓库没有，见 `docs/development/solver-proof-policy.md`）。**任何"加注占过牌线的 X%"的数字在这里都是 UNVERIFIED。**
4. **多人底池**：`f` 变成"所有人一起弃"，合计门槛按人数摊薄（`pokergto.odds.defense_frequency_multiway`）。
5. **`e` 由对手范围决定，而对手范围是输入。** 例 2/3/4 里的 `0.30`、`0.05`、`0.45` 都是作者设定的模型值。
6. **锦标赛**：`P` 换成 ICM 值后门槛不再是 `B/(P+2B)`（第 12 章）。

## 陷阱 / Common mistakes

1. **"我弃得比 MDF 多一点，反正弃的是弱牌。"** 如果过牌线里没有足够弱牌，多弃的每一手都是正期望跟注。
   *代价*：例 4 的 `4.166667` 筹码 / 100 手（`P = 1` 口径），线越强越贵（`e = 0.45` 时 `10.416667`）。
2. **用 MDF 达标当作过牌线健康。** `defense_indifference_gap` 只看合计，`balance_bluff_and_value` 的 `exploitable_side` 也只看合计与诈唬占比。
   *代价*：合计 66.67%、全部由抓诈唬牌组成的线，面对底池时 `f` 仍是 1（例 3），空气拿走 `1.000000` 个底池。
3. **惩罚对手时挑最大的尺度。** 均一弃牌率 50% 下，1/4 池的空气赚 `0.375000`，2 倍池的空气亏 `−0.500000`。
   *代价*：`0.875000` 个筹码/手的落差，正好把一个 +EV 惩罚打成 −EV。
4. **把"底端牌"理解成"随便弃的牌"。** 它们的用途是**替这条线付弃牌税**，不是被进攻的靶子；底端在位时对手的空气恰好 `0`（例 2），不在位时他每手拿 1 个底池（牌局 1）。
   *代价*：混淆之后会得出"过牌线越紧越好"，而 `f = 1` 的分支正是最坏结局。

## 练习 / Drills

- 用例 1 的命令算 1/4 池与 3/2 池两行（答案：1/4 池继续 1060.8 / 弃 265.2，门槛 16.67%；3/2 池继续 530.4 / 弃 795.6，门槛 37.50%）。
- 构造一条 `N = 100` 的过牌线，使 1/2 池的弃牌税成本精确为 `0`：给出必须有几个组合数低于 25.00% 门槛（答案：`[0.5/(1+0.5)] × 100 = 33.333` 个）。
- 用 `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto.theory import frequencies as fq; r=fq.balance_bluff_and_value(1,F(1,3),defense_frequency=F(1,2),bluff_fraction=F(1,5)); print(r.defense_gap, r.bluff_gap, r.exploitable_side)"` 复现"under-defending: any two cards profit as a bluff"，并把 `defense_frequency` 换成 `3/4` 看它变回 balanced。
- 把例 5 的 `f = 0.5` 换成 `f = 0.7`，重算六个尺度的 `EV(bluff)`（答案：1/3 池 `0.600000` / 1/2 池 `0.550000` / 3/4 池 `0.475000` / 底池 `0.400000` / 2 倍池 `0.100000`），并说明为什么 2 倍池那行掉得最快。

## 自测清单 / Self-check

- [ ] 我能把 MDF 换算成"必须继续多少个组合数"，并说出 1/3 池对应 994.5。
- [ ] 我能用 `C` 与 `(1 − MDF)·N` 的大小关系判断过牌线缺不缺底端牌，并算出成本。
- [ ] 我能解释 `f = 1` 时 `EV(bluff) = P` 为什么与尺度无关。
- [ ] 我能说出 `is_capped` 的参照物是什么（牌面上任意两手牌的上限），以及它判 `true` 时对手拿走什么。
- [ ] 我知道 MDF 只看合计防守占比，因此它能被一条没有加注、也没有顶端牌的线"骗过"。

## 来源与置信度 / Provenance and confidence

地板线、门槛胜率、组合数与期望值全部由本仓库现算。`e = 0.30 / 0.05 / 0.45`、`N = 100`、`f = 0.5 / 0.7` 是作者设定的模型输入；`is_capped` 的两个范围是 `table.03-02.capped-range-check` 里已有的教学范围。本节没有任何"过牌线的加注占比应该是 X%"的数字，因为本仓库不能算它。

| 内容 | 来源类型 | 位置 / 复现命令 |
|---|---|---|
| 例 1 的 MDF / 组合数 / 门槛五行 | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds; [print(float(B), float(odds.minimum_defense_frequency(1,B,exact=True)*1326), float((1-odds.minimum_defense_frequency(1,B,exact=True))*1326), float(odds.equity_needed_to_call(1,B))) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))]"` |
| 例 2 的 `EV(bluff) = 0` 与 `indifference_check = True` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds, ev; print(float(ev.ev_pure_bluff(1,F(1,3),F(1,4))), odds.indifference_check(1,F(1,3),F(1,4)))"` |
| 例 3 / 牌局 1 的 `−0.100000`、`−0.500000`、`1.000000` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(float(ev.ev_call(1,F(1),F(3,10))), float(ev.ev_call(1,F(2),F(3,10))), float(ev.ev_pure_bluff(1,F(1,3),1)), float(ev.ev_pure_bluff(1,F(2),1)))"` |
| 例 4 的 `4.166667` 与 `10.416667` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(float(25*ev.ev_call(1,F(1,3),F(3,10))), float(25*ev.ev_call(1,F(1,3),F(45,100))))"` |
| 例 5 / 陷阱 3 的六行 `EV(bluff)` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; [print(float(B), float(ev.ev_pure_bluff(1,B,F(1,2)))) for B in (F(1,4),F(1,3),F(1,2),F(3,4),F(1),F(2))]"` |
| 牌局 1 里三个空气尺度并列最优 | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; rows=ev.compare(1,[('bluff 1/3 pot',F(1,3)),('bluff pot',F(1)),('bluff 2x pot',F(2)),('check',0)],fold_frequencies={'bluff 1/3 pot':1,'bluff pot':1,'bluff 2x pot':1,'check':0},equities_when_called={'bluff 1/3 pot':0,'bluff pot':0,'bluff 2x pot':0,'check':0}); print([(r.action,round(r.ev,6),r.best) for r in rows])"` |
| 第五步"MDF 只看合计" | `derived` | `src/pokergto/theory/frequencies.py` 模块文档与 `defense_indifference_gap` 的签名；`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto.theory import frequencies as fq; r=fq.balance_bluff_and_value(1,F(1,3),defense_frequency=F(1,2),bluff_fraction=F(1,5)); print(r.defense_gap, r.bluff_gap, r.exploitable_side)"` |
| 顶端缺位判据 `is_capped` | `derived` | `data/gen/tables/table.03-02.capped-range-check.json`；`pokergto.theory.range_advantage#is_capped` |
| `e = 0.30 / 0.05 / 0.45`、`N = 100`、`f = 0.5 / 0.7` | `reference` + **UNVERIFIED** | 作者设定的模型输入，未做牌面移除校正；核验路径：把逐尺度的过牌/继续范围写进 `data/src/spots/*.yaml`，用 `poker range` + `poker equity` 复算每段胜率 |
| "过牌线的加注占该线的 X%"、"这条线该配多大尺度" | 无实现 → **UNVERIFIED** | `src/pokergto/theory/__init__.py` 把 bet-size governance 与极化判据、阻断牌 EV、保护 vs 价值并列为刻意缺席四项；需要范围层的解，而本仓库连两街玩具都未实现 |
| 过牌线的真实成本（不是全压口径） | 无实现 → **UNVERIFIED** | 需要胜率实现 EqR（`01-06` 的概念），本仓库未实现；被删除模块的教训见 `src/pokergto/theory/__init__.py` |

## 术语 / Terms

<!-- terms: checking-range, checking-frequency, minimum-defense-frequency, defend, fold-frequency, required-equity, capped-range, combos, bet-size, indifference -->

| 缩写 | 中文 | English | 本节里的含义 |
|---|---|---|---|
| — | 过牌范围 | checking range | 你以过牌继续的那部分范围，本节要治理的对象 |
| — | 过牌频率 | checking frequency | 它与"面对下注时的继续频率"是两件事，本节两者都算 |
| MDF | 最低防守频率 | minimum defense frequency | 继续占比的下界 `P/(P+B)`，只看合计 |
| — | 防守 | defend | 继续（跟注或加注）的合计动作，不是其中的跟注 |
| — | 弃牌频率 | fold frequency | `1 − MDF`，本节把它换算成"必须弃多少个组合数" |
| — | 所需胜率 | required equity | `B/(P+2B)`，判定一条线里谁是"便宜弃牌" |
| — | 封顶范围 | capped range | 线里没有牌面可达上限；`is_capped` 判据 |
| — | 组合数 | combos | 治理的单位：994.5、663、442 都是组合数 |
| — | 下注尺度 | bet size | 门槛是它的函数，对手的惩罚尺度也是 |
| — | 无差别 | indifference | 空气 `EV = 0` 的那一点，即 `f = B/(P+B)` |
