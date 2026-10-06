# 极化、合并与线性：三种范围形状对应三种尺度逻辑

<!-- hands: 2 -->
<!-- terms: polarized, merged, linear, value-range, bluff-range, range-approach, overbet, capacity, capped-range, bet-size -->

## 本节目标 / Objectives

- 能用一条不等式（`table.04-05.bet-break-even-equity` 的 `regime` 列）说明：单街的盈亏平衡面只能产出"顶端段"或"全体"，产不出"顶端 + 底端、中间为空"。
- 能用每个尺度的诈唬占比与"手里的价值/诈唬组合数供给"，算出该尺度最大能承载多少个组合数，并据此判断这个尺度支持的是合并形状还是极化形状。
- 能指出形状判断里哪一半是本仓库可算的（配额、容量、坚果优势、封顶），哪一半不可算（给定尺度下的跟注范围与中间牌段的期望值），并标为 UNVERIFIED。

## 前置知识 / Prerequisites

- `04-04` 每个尺度各自的配额方程与两尺度的临界胜率 `ē`。
- `03-01` 胜率优势决定"谁常下注"，坚果优势决定"谁下大注"；`03-02` 封顶范围。
- `02-04` 诈唬占比 `B/(P+2B)` 与配比 `(P+B)/B`；`02-03` 每个尺度对手必须留下的组合数。

## 核心原理 / The principle

三种形状不是三种"胆量"，而是**同一个牌力轴被切成的三段落在哪里**：

| 形状 | 定义（按牌力从强到弱排） | 尺度逻辑 |
|---|---|---|
| 极化 polarized | 顶段下注 + 底段下注，中间空 | 只有大尺度 / 超池下注撑得起 |
| 合并 merged | 顶段与底段相邻、连成一片地下注 | 单一中小尺度 |
| 线性 linear | 牌力与尺度单调对应（越强尺度越大） | 尺度阶梯本身是策略 |

本节的核心结论是一句可核验的话：**`pokergto.ev` 的盈亏平衡面对每个尺度只给一条关于胜率 `e` 的一次不等式，一次不等式只能切出"上段"或"下段"，切不出"上段 ∪ 下段"。** 极化必须靠第二个约束进来——每个尺度的诈唬配额与范围容量。这是 `derived`（推导见下），并且已经用 1592 组 `(尺度, 弃牌率)` 的扫描验证过：没有任何一行的 `regime = below` 同时给出 `e* ≤ 1`。

## 推导 / Derivation

`break_even_equity_to_bet(P, B, f)` 解 `EV(bet) = EV(check)`，得

```
e* = ( (1 − f)·B − f·P ) / ( 2B(1 − f) − f·P ),   分母记 D, 分子记 N
```

分母 `D` 的符号决定区间（这是 `BreakEven.regime` 的文档写明的规则，`tests/test_ev.py` 逐支回代验证）：

- `D > 0` → `regime = above`：`e ≥ e*` 才下注，切出**顶段**。
- `D < 0` → `regime = below`：不等号翻向，`e ≤ e*` 才下注。
- `D = 0` → `regime = all / none / indifferent`：尺度与弃牌率单独决定，`e` 不参与。

**关键点一：翻向并不产生"只打空气"。** `D = 0` 的解是 `f = 2B/(P + 2B)`。而对同一个 `B`，`N = 0` 的解是 `f = B/(P + B)`，且

```
B/(P+B) < 2B/(P+2B)   ⟺   P + 2B < 2P + 2B   ⟺   0 < P
```

所以一旦 `f` 越过 `D = 0` 那条线（进入 `below`），`N` 早已是负的：负÷负得正，`e* > 0`。再解一次 `e* = 1`：`N = D` 化简为 `(1 − f)·B = 0`，只有 `f = 1` 才成立。于是在整个 `below` 区间里 `e* > 1` 恒成立——**"越弱越该下注"是真的，但没有任何一手牌会被排除**，`below` 的实际含义是"全范围下注"，不是"只打诈唬"。这不是代数学家的口头保证：8 个尺度 × 1592 个 `f` 的扫描里，`below` 且 `e* ≤ 1` 的行数是 `0`。

**关键点二：形状由配额与容量决定。** 一个尺度能承载的最大组合数是

```
stall(B) = min( 诈唬供给 A / s(B),  价值供给 V / (1 − s(B)) ),   s(B) = B/(P + 2B)
```

供给由牌面决定（`capacity`），`s(B)` 由尺度决定。`A, V` 固定时，小尺度是价值受限（`V/(1−s)` 先到顶），大尺度是诈唬受限（`A/s` 先到顶）。**诈唬受限就意味着必须把一部分成牌留在过牌线里**，于是下注范围被压成"顶段 + 底段"，中间空出来——这就是极化的来源，它是数出来的，不是选出来的。

**关键点三：`f` 是否随尺度上升，决定尺度与牌力是否单调。** 由 `ev_bet` 对 `B` 求导（`f` 视为常数）：

```
∂EV(bet)/∂B = (1 − f)·( 2e − 1 )
```

`f` 不变时，这条式子给出"强者要大尺度、弱者要小尺度"= 线性；`e = 1/2` 时它精确为 0，尺度怎么选都一样。极化需要 `f` 随 `B` 上升，而 `f(B)` 是对手模型的输入，不是本仓库能算的量。

## 直觉 / Intuition

把尺度想成一个摊位的大小：摊位越大，每卖一手诈唬所需搭配的价值牌就越少（1/4 池要 5 : 1，2 倍池只要 1.5 : 1）。听起来大摊位"更宽容"，实际上它把要求挪到了另一头：**大摊位要你拿出更多诈唬来填满配比**，而空气是有限的。空气不够时，你只能少带价值牌——把中等成牌留在过牌线，下注范围自然就变成"两头"。

小尺度反过来：配比苛刻（5 手价值配 1 手诈唬），你舍不得把价值牌留在外面，于是从最强的牌一路带到很薄的价值，中间几乎没有缝——那就是合并。

线性是第三种情形：你手里既有足够的空气也有足够的坚果，尺度阶梯本身成了"报牌力"的暗号。它要求对手对每个尺度的弃牌率真的不同，而这正是唯一无法在本仓库核验的输入。

## 算例 / Worked examples

**例 1 — `regime` 翻向线在哪（`P = 1`）。** `f_all = 2B/(P + 2B)`：

| 尺度 | `f_all` | 略低于 | 恰在 | 略高于 |
|---|---|---|---|---|
| 1/3 池 | 40.00% | `above` | `all` | `below` |
| 1/2 池 | 50.00% | `above` | `all` | `below` |
| 3/4 池 | 60.00% | `above` | `all` | `below` |
| 底池 | 66.67% | `above` | `all` | `below` |
| 2 倍池 | 80.00% | `above` | `all` | `below` |

复现：`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; B=F(1,2); fa=2*B/(1+2*B); print([ev.break_even_equity_to_bet(1,B,x).regime for x in (fa-F(1,100),fa,fa+F(1,100))])"` → `['above', 'all', 'below']`。对照 `table.04-05.bet-break-even-equity`：`1/2 pot` 在 `f = 0.5` 正是 `all`，`1/3 pot` 在 `f = 0.4` 正是 `all`，逐行吻合。

**例 2 — `f` 固定时的尺度阶梯（`P = 1, f = 0.30`）。** 三个胜率的期望值：

| `e` | 1/3 池 | 1/2 池 | 3/4 池 | 底池 | 2 倍池 | 形状读法 |
|---|---|---|---|---|---|---|
| 1.00 | 1.233333 | 1.350000 | 1.525000 | 1.700000 | 2.400000 | 单调上升 → 线性 |
| 0.50 | 0.650000 | 0.650000 | 0.650000 | 0.650000 | 0.650000 | 完全平坦 → 尺度无关 |
| 0.00 | 0.066667 | −0.050000 | −0.225000 | −0.400000 | −1.100000 | 单调下降 → 空气只配小尺度 |

`e = 0.50` 那一行的平坦不是巧合，正是 `∂EV/∂B = (1 − f)(2e − 1) = 0`。**这张表也说明：`f` 不随尺度上升时，极化不出现**（空气偏好的是小尺度，不是大尺度）。复现：`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print([float(ev.ev_bet(1,B,F(3,10),F(1,2))) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))])"`。

**例 3 — 门槛随尺度上升（同一 `f = 0.30`）。** `e*` 分别是 `−0.400000 / 0.125000 / 0.300000 / 0.363636 / 0.440000`（1/3 池 → 2 倍池）。也就是"**他不多弃牌时，大尺度要更强的牌**"。这与"大尺度更凶"的口号正好相反，是本节要写下来的矛盾之一。

**例 4 — 容量决定形状（供给 `V = 40` 价值 + `A = 15` 诈唬，`P = 1`）。**

| 尺度 | 诈唬占比 `s(B)` | 最大承载组合数 | 价值 / 诈唬 | 剩余 |
|---|---|---|---|---|
| 1/4 池 | 16.67% | 48.0000 | 40.0 / 8.0 | 空气剩 7.0 |
| 1/3 池 | 20.00% | 50.0000 | 40.0 / 10.0 | 空气剩 5.0 |
| 1/2 池 | 25.00% | 53.3333 | 40.0 / 13.3333 | 空气剩 1.6667 |
| 3/4 池 | 30.00% | 50.0000 | 35.0 / 15.0 | 价值剩 5.0 |
| 底池 | 33.33% | 45.0000 | 30.0 / 15.0 | 价值剩 10.0 |
| 2 倍池 | 40.00% | 37.5000 | 22.5 / 15.0 | 价值剩 17.5 |

1/2 池及以下是**价值受限**：40 个价值组合数全下注，形状连成一片 = 合并。3/4 池起是**诈唬受限**：想打 2 倍池就必须把 17.5 个价值组合数留在过牌线里，下注摊只剩"22.5 个顶端 + 15 个空气" = 极化，而且这个极化是除法算出来的。复现：`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds; V,A=F(40),F(15); [print(float(B), float(odds.bluff_fraction_at_indifference(1,B,exact=True)), float(min(A/odds.bluff_fraction_at_indifference(1,B,exact=True), V/(1-odds.bluff_fraction_at_indifference(1,B,exact=True))))) for B in (F(1,4),F(1,3),F(1,2),F(3,4),F(1),F(3,2),F(2))]"`。

## 生成表 / Generated tables

本节的地基是这张表：每个尺度、每个弃牌率下的盈亏平衡胜率与 `regime`。它由 `break_even_equity_to_bet` 闭式解出，并逐行用 `ev_bet` / `ev_check` 回代（`residual` 列为 0）：

<!-- BEGIN AUTO:table.04-05.bet-break-even-equity -->
|    尺度 | 对手弃牌率 f | 该尺度的 MDF | 盈亏平衡胜率 e* |  区间 | 回代残差 |
|---:|---:|---:|---:|---:|---:|
| 1/3 pot |       25.00% |     75.0000% |         0.0000% | above |        0 |
| 1/3 pot |       40.00% |     75.0000% |               - |   all |        - |
| 1/3 pot |       50.00% |     75.0000% |       200.0000% | below |        0 |
| 1/3 pot |       60.00% |     75.0000% |       140.0000% | below |        0 |
| 1/3 pot |       75.00% |     75.0000% |       114.2857% | below |        0 |
| 1/2 pot |       25.00% |     66.6667% |        25.0000% | above |        0 |
| 1/2 pot |       40.00% |     66.6667% |       -50.0000% | above |        0 |
| 1/2 pot |       50.00% |     66.6667% |               - |   all |        - |
| 1/2 pot |       60.00% |     66.6667% |       200.0000% | below |        0 |
| 1/2 pot |       75.00% |     66.6667% |       125.0000% | below |        0 |
| 3/4 pot |       25.00% |     57.1429% |        35.7143% | above |        0 |
| 3/4 pot |       40.00% |     57.1429% |        10.0000% | above |        0 |
| 3/4 pot |       50.00% |     57.1429% |       -50.0000% | above |        0 |
| 3/4 pot |       60.00% |     57.1429% |               - |   all |        - |
| 3/4 pot |       75.00% |     57.1429% |       150.0000% | below |        0 |
|     pot |       25.00% |     50.0000% |        40.0000% | above |        0 |
|     pot |       40.00% |     50.0000% |        25.0000% | above |        0 |
|     pot |       50.00% |     50.0000% |         0.0000% | above |        0 |
|     pot |       60.00% |     50.0000% |      -100.0000% | above |        0 |
|     pot |       75.00% |     50.0000% |       200.0000% | below |        0 |
|   2 pot |       25.00% |     33.3333% |        45.4545% | above |        0 |
|   2 pot |       40.00% |     33.3333% |        40.0000% | above |        0 |
|   2 pot |       50.00% |     33.3333% |        33.3333% | above |        0 |
|   2 pot |       60.00% |     33.3333% |        20.0000% | above |        0 |
|   2 pot |       75.00% |     33.3333% |      -100.0000% | above |        0 |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.ev#break_even_equity_to_bet`

<!-- generated by: tools/gen_tables.py from pokergto.ev::break_even_equity_to_bet -->
<!-- END AUTO:table.04-05.bet-break-even-equity -->

`regime = below` 的行是"方向翻过来了"的区间，但注意本表所有 `below` 行的 `break_even_equity` 都大于 1（`2.0`、`1.4`、`1.142857`…），按推导里的关键点一，它们排除不了任何一手牌；`regime = all` 的行才是"尺度自己决定"。

下一张表给出每个尺度要求的诈唬配额，即例 4 里 `s(B)` 那一列的来源：

<!-- BEGIN AUTO:table.02-04.bluff-value-ratio -->
|    尺度 | 诈唬占比 | 价值:诈唬 |
|---:|---:|:---:|
| 1/4 pot |   16.67% |   5 : 1   |
| 1/3 pot |   20.00% |   4 : 1   |
| 1/2 pot |   25.00% |   3 : 1   |
| 2/3 pot |   28.57% |  2.5 : 1  |
| 3/4 pot |   30.00% | 2.33 : 1  |
|  1x pot |   33.33% |   2 : 1   |
| 3/2 pot |   37.50% | 1.67 : 1  |
|  2x pot |   40.00% |  1.5 : 1  |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.odds#bluff_fraction_at_indifference`

<!-- generated by: tools/gen_tables.py from pokergto.odds::sizing_table -->
<!-- END AUTO:table.02-04.bluff-value-ratio -->

形状不只由自己的牌决定，还由谁有坚果决定。`can_bet_big` 与 `can_bet_often` 两列在下面这张表里是分开计算的，而且四行里有两行它们指向不同的人：

<!-- BEGIN AUTO:table.03-01.equity-vs-nut-advantage -->
|     牌面 |                        Hero 范围 |                            Villain 范围 |             Hero |          Villain | Hero 胜率 |  胜率优势 | Hero 坚果占比 |  坚果优势 | 谁能常下注 | 谁能下大注 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
|   Kh7s3d |    AKs,AQs,ATs,KQs,AKo,AQo,99,77 | KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s |        CO opener |        BB caller |  71.5272% |  43.0545% |       6.8182% |   6.8182% |    hero    |    hero    |
|   9h6d3c | AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs |   87s,76s,65s,54s,T8s,T9s,98o,97o,66,55 |       BTN opener |        BB caller |  36.8154% | -26.3691% |       4.7619% |   4.7619% |  villain   |    hero    |
|   As9s5d |     AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT |           KQs,QJs,KJs,JTs,98s,76s,99,55 |        CO opener |        BB caller |  61.0233% |  22.0466% |       0.0000% | -10.3448% |    hero    |  villain   |
| Kh7s3d4c |         AKo,AQo,ATs,KQs,99,77,44 |         KJs,QJs,JTs,T9s,98s,A5s,KQo,AJo | CO opener (turn) | BB caller (turn) |  76.9775% |  53.9550% |       7.5000% |   7.5000% |    hero    |    hero    |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.theory.range_advantage#advantage`

<!-- generated by: tools/gen_tables.py from pokergto.theory.range_advantage::advantage -->
<!-- END AUTO:table.03-01.equity-vs-nut-advantage -->

顶段是否存在，是可以判定而不是可以辩论的——`is_capped` 给出机器判据：

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

最后，配额不是只有代数为证。五个尺度各自求解决的单街玩具，其解出的防守频率与诈唬占比与闭式的差距如下：

<!-- BEGIN AUTO:table.08-04.solver-vs-algebra -->
|        尺度 | 求解器防守 | 代数 MDF | 求解器诈唬占比 | 代数诈唬占比 | 可剥削度(筹码/手) |
|---:|---:|---:|---:|---:|---:|
| 0.5000x pot |     66.67% |   66.67% |         25.00% |       25.00% |    0.000001 chips |
| 0.3333x pot |     75.01% |   75.00% |         20.00% |       20.00% |    0.000014 chips |
| 1.0000x pot |     50.01% |   50.00% |         33.34% |       33.33% |    0.000043 chips |
| 0.7500x pot |     57.16% |   57.14% |         30.02% |       30.00% |    0.000098 chips |
| 2.0000x pot |     33.33% |   33.33% |         40.00% |       40.00% |    0.000008 chips |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`src/pokergto/solver/proofs.py#PUBLISHED_PROOFS`

<!-- generated by: tools/gen_tables.py from pokergto.solver.cfr::solve -->
<!-- END AUTO:table.08-04.solver-vs-algebra -->

## 实战牌局 / Live hands

**牌局 1（`hand.04-05-polarized-river`）— 河牌 `Kh7s3d8c6d`，底池 100 bb，我方 CO 进攻后在转牌圈已建立坚果优势，手里能凑出的牌力供给是 40 个价值组合数 + 15 个空气组合数，尺度集合 {1/3 池, 2 倍池}。**

- 容量：2 倍池要求 40.00% 的诈唬占比，`stall(2x) = min(15/0.4, 40/0.6) = 37.5` 个组合数，摊开是 22.5 个价值 + 15 个空气；剩下的 17.5 个价值组合数**必须不在里面**。
- 决策：打 2 倍池，范围是顶端 22.5 + 全部 15 个空气。若硬凑满 50 个组合数，需要 20 个空气而只有 15 个，缺的 5 个只能用中间成牌补——那就不再是极化，而是"中间牌打 2 倍池"。
- 代价（可算）：一手 `e = 0.35`、对手弃牌率 `f = 0.30` 的中间牌，`EV(2 倍池) = 12.5000`、`EV(check) = 35.0000`、`EV(1/3 池) = 47.5000`（`P = 100` 口径，`ev.compare` 排序并给出 regret：2 倍池相对最优少 35.0000 个筹码）。
- 这一牌局的结论形状是数出来的：`table.03-01.equity-vs-nut-advantage` 里 `Kh7s3d` 那行给出 `can_bet_big = hero`（`nut_edge = 0.115385`），`table.04-05.bet-break-even-equity` 里 2 倍池在 `f = 0.25` 的 `e* = 0.454545` 说明顶段门槛确实高，只有顶段过得了。

**牌局 2（`hand.04-05-merged-flop`）— 翻牌 `9h6d3c`，底池 20 bb，同样 40 价值 + 15 空气的供给，对手在 MDF 线附近弃牌（`f = 25%`，1/3 池的理论弃牌率）。**

- 容量：`stall(1/3 pot) = min(15/0.2, 40/0.8) = 50` 个组合数 = 40 价值 + 10 空气，空气还剩 5 个进过牌线。整个价值段（含最薄的价值）都在下注摊里，形状连成一片 = 合并。
- 门槛核对：`f = 0.25` 时 1/3 池的 `e* = 0`（`table.04-05.bet-break-even-equity` 第一行）。**这既是许可也是警告**：`e* = 0` 说"任何牌下注都不比过牌差"，可它同时说明这条街上没有选出形状的东西——形状来自上一行的容量除法，不来自门槛。
- 决策：用 1/3 池一个尺度，而不是"1/3 池 + 2 倍池"两级：2 倍池在这里是诈唬受限（37.5 个组合数封顶），而 1/3 池能装 50 个；把价值段拆到装不下的尺度上，等于把能收到钱的牌挪出下注范围。
- 反例代价：`e = 0.35` 的中间牌打 1/3 池是 `47.5000`，打 2 倍池是 `12.5000`（牌局 1 同一命令），差 `35.0000` 个筹码；这不是"尺度大小"的口味差，是同一手牌在同一 `f` 下的期望值差。

## 范围图 / Range chart

大尺度对防守方范围的挤压是极化"看起来合理"的来源之一——他只留 1/3 的范围：

<!-- BEGIN AUTO:range.04-02.mdf-floor-vs-two-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· | ·· |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· | ·· |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· | ·· |
| 7 | @@ | @@ | @@ | @@ | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |
| 6 | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |
| 5 | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |
| 4 | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |
| 3 | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |
| 2 | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |

覆盖 442.0 组合 = 全 1326 的 33.33%

图例：`··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%；对角线为对子，上三角同花，下三角不同花。

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.04-02.mdf-floor-vs-two-pot -->

图上那 442 个组合数（33.33%）是地板线，不是解：`pokergto.odds` 只约束总频率，"用哪些组合数达到它"按牌力从高到低填（图的 `assumptions` 里写着这条）。所以这张图能证明"大尺度让防守面变窄"，不能证明"我的下注范围该长成两头"。后者要的是给定尺度下的跟注范围，本仓库没有这个东西，见下一节与来源表。

## 为何成立、何时失效 / Why it works, when it breaks

**成立的前提**：牌力轴可以用一个标量 `e` 排序；每个尺度的诈唬占比是无差别条件 `s(B) = B/(P+2B)`；供给 `V, A` 是给定的；`f` 与 `e` 在同一尺度内不随尺度变化（关键点三用它做极限讨论）。

**失效之处**：

1. **`e` 是"被跟注时的胜率"，而跟注范围随尺度变。** 极化的定义是"中间牌在这个尺度上被更强的跟注范围打死"，这要的是**每个尺度对应的跟注范围**。本仓库没有这个能力：`02-07` 把 `q` 当输入，`04-01` 的范围法同样把范围结构当输入。因此"某段牌在该尺度上变差"是 **`reference` + UNVERIFIED**；核验路径：把逐尺度跟注范围写进 `data/src/spots/*.yaml`，用 `poker range` + `pokergto.cards.remove_cards` 数组合数、`poker equity` 算每尺度的 `e`。
2. **一街模型给不出"多街保护"。** 合并形状常靠"下一条街继续施压"来撑起中段。Leduc 确实有第二条下注街并且已解出（`data/gen/solver/leduc.json`），也就是说这个结构在本仓库里是存在的——但它是六张牌、每街一个尺度、没有牌面发展的博弈，不是本节这张转牌所制造的那条"稍后的街"。下面用到的闭合式仍然只属于一条街。
3. **`f` 与 `B` 的关系是输入。** 例 2 的"平坦行"和极化不出现，都建立在 `f` 不随尺度变化这个假设上；真实对手面对 2 倍池会弃更多，`f(B)` 递增是常识但不可核验。
4. **`regime = below` 被广泛误读。** 关键点一给出 `e* > 1` 恒成立，所以"below = 只打空气"是错的；它等于"全打"。任何以此为由写出的"极化证明"都不成立。
5. **多人底池**：`s(B)` 与 `f` 都要按人数改（`pokergto.theory.multiway`），形状讨论要重开。

## 陷阱 / Common mistakes

1. **把 `regime = below` 读成"该用空气下注"。** 该区间里 `e* > 1`（推导关键点一，扫描 1592 行为 0 例外），没有任何牌被排除，正确读法是"全范围下注"。
   *代价*：把"全打"当"只打空气"，会在对手高频弃牌时用空气替代全部价值下注，而例 3 显示同一个 `f` 下大尺度的门槛是 `0.44`。
2. **用形容词分类形状，不做容量除法。** "我这手牌适合超池"没有内容；`stall(B) = min(A/s, V/(1−s))` 有内容。
   *代价*：牌局 1 里凑满 50 个组合数需要 20 个空气而只有 15 个，缺的 5 个用中间成牌补，每手少 35.0000 个筹码（`EV(2 倍池) = 12.5` 对 `EV(1/3 池) = 47.5`）。
3. **以为坚果多就能极化。** 顶段存在是必要条件而非充分条件：`table.03-02.capped-range-check` 里 `is_capped = true` 的两行说明该线根本没有顶端，超池尺度直接失去法律依据。
   *代价*：范围封顶时打大尺度，对手的诈唬占比要求你无法反驳——`range.04-02.mdf-floor-vs-two-pot` 只需他留 442 个组合数，而那 442 个里全是你打不动的牌。
4. **把形状当成尺度选完之后的副产品。** 例 2 说明形状与尺度是同一个约束系统的两个解：`f` 不随尺度升时阶梯是线性的，`f` 随尺度升时才谈极化，而 `f(B)` 是输入。
   *代价*：把"极化 = 用大尺度"当定义，会在对手守线（`f = B/(P+B)`）时得出"空气在每个尺度都恰好 0 期望值"的无差别结论，等于什么都没教。

## 练习 / Drills

- 复现"关键点一"的扫描（正确答案：`1592 0`，即扫过 1592 行、0 行是 `below` 且 `e* ≤ 1`）：`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; sizes=[F(1,4),F(1,3),F(1,2),F(2,3),F(3,4),F(1),F(3,2),F(2)]; pairs=[(B,2*B/(1+2*B)+F(k,1000)) for B in sizes for k in range(1,200) if 2*B/(1+2*B)+F(k,1000)<1]; print(len(pairs), sum(1 for B,f in pairs if (be:=ev.break_even_equity_to_bet(1,B,f)).regime=='below' and be.threshold is not None and be.threshold<=1))"`。
- 对 `P = 1, V = 40, A = 15`，自己算 `stall` 在 3/2 池的值，并说出它是价值受限还是诈唬受限（答案：`s = 37.50%`，`stall = 40.0000`，诈唬受限，需要 15 个空气、装 25 个价值）。
- 用例 2 的三个 `e` 各写出 `∂EV/∂B`，解释为什么 `e = 1/2` 那一行必须完全平坦（`0.65` 五个尺度相同），并验证 `EV(check)` 恰为 `0.5`。
- 从 `table.08-04.solver-vs-algebra` 读出 2 倍池那行：解出的诈唬占比 `0.399993` 对闭式 `0.4`、防守 `0.333323` 对 `0.333333`，并说明为什么这个玩具不能用来判定形状（每个玩具只有一个尺度、三种手牌类型）。

## 自测清单 / Self-check

- [ ] 我能写出 `e*` 的闭式，并说明 `D = 0` 与 `N = 0` 两条线的先后关系。
- [ ] 我能证明 `regime = below` 时 `e* > 1`，并用一句话说清它为什么不叫"只打空气"。
- [ ] 我能用 `stall(B) = min(A/s, V/(1−s))` 判断某个尺度是价值受限还是诈唬受限，并推出形状。
- [ ] 我能指出"极化"定义里必须有的那个非可算量（每个尺度的跟注范围），并给出让它变成可核验的具体路径。
- [ ] 我能区分 `can_bet_often` 与 `can_bet_big`，并说出它们不一致时该信哪个。

## 来源与置信度 / Provenance and confidence

本节所有区间、门槛、期望值与容量除法都由本仓库现算；`V = 40`、`A = 15`、`f = 0.30`、`f = 0.25` 是作者设定的模型输入。没有引用任何商业求解器的范围或策略表；引用的求解器数据是本仓库自产并自证的单街玩具。

| 内容 | 来源类型 | 位置 / 复现命令 |
|---|---|---|
| `e*` 闭式、`regime` 分支、`residual = 0` | `derived` | `data/gen/tables/table.04-05.bet-break-even-equity.json`；`PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print(ev.break_even_equity_to_bet(1,F(1,2),F(1,2)))"`；逐支回代在 `tests/test_ev.py` |
| 例 1 的 `f_all` 五条与三态序列 | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; [print(float(B), float(2*B/(1+2*B)), [ev.break_even_equity_to_bet(1,B,x).regime for x in (2*B/(1+2*B)-F(1,100), 2*B/(1+2*B), 2*B/(1+2*B)+F(1,100))]) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))]"` |
| 例 2 的五行平坦 / 单调阶梯 | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print([[round(float(ev.ev_bet(1,B,F(3,10),F(e))),6) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))] for e in (F(1),F(1,2),0)])"` |
| 例 3 的 `e*` 随尺度上升（−0.4 → 0.44） | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; print([None if ev.break_even_equity_to_bet(1,B,F(3,10)).threshold is None else round(float(ev.break_even_equity_to_bet(1,B,F(3,10)).threshold),6) for B in (F(1,3),F(1,2),F(3,4),F(1),F(2))])"` |
| 例 4 的 `stall` 六行与剩余 | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import odds; V,A=F(40),F(15); [print(float(B), float(odds.bluff_fraction_at_indifference(1,B,exact=True)), float(min(A/odds.bluff_fraction_at_indifference(1,B,exact=True), V/(1-odds.bluff_fraction_at_indifference(1,B,exact=True))))) for B in (F(1,4),F(1,3),F(1,2),F(3,4),F(1),F(3,2),F(2))]"` |
| 牌局 1 / 2 的 `12.5`、`35.0`、`47.5` | `derived` | `PYTHONPATH=src python -c "from fractions import Fraction as F; from pokergto import ev; rows=ev.compare(100,[('check',0),('1/3 pot',100/3),('2x pot',200)],fold_frequencies={'check':0,'1/3 pot':F(3,10),'2x pot':F(3,10)},equities_when_called={'check':F(35,100),'1/3 pot':F(35,100),'2x pot':F(35,100)}); print([(r.action, round(r.ev,4)) for r in rows], ev.regret(rows))"` |
| 关键点一的"1592 行 0 例外"扫描 | `derived` | 练习 1 的命令（同一逻辑在 `PYTHONPATH=src python -c` 里手写，不依赖生成物） |
| `V = 40 / A = 15`、`f = 0.30 / 0.25`、供给随牌面的分布 | `reference` + **UNVERIFIED** | 作者设定的模型输入，未做牌面移除校正；核验路径同 `04-04` |
| "中间牌在该尺度被更强的跟注范围打死"（极化的定义项） | 无生成物 → **UNVERIFIED** | 需要逐尺度跟注范围：`data/src/spots/*.yaml` + `poker equity`；本仓库当前无任何"给定尺度求跟注范围"的实现 |
| 多街施压对合并形状的贡献 | 无生成物 → **UNVERIFIED** | 本仓库未求解两街博弈（`docs/development/solver-proof-policy.md`） |
| 五个尺度的解出频率与闭式差距 | `derived` | `data/gen/tables/table.08-04.solver-vs-algebra.json`，产物 `data/gen/solver/toy_1street_*.json`，`src/pokergto/solver/proofs.py` |

## 术语 / Terms

<!-- terms: polarized, merged, linear, value-range, bluff-range, range-approach, overbet, capacity, capped-range, bet-size -->

| 缩写 | 中文 | English | 本节里的含义 |
|---|---|---|---|
| — | 极化 | polarized | 顶段 + 底段下注、中间为空；由诈唬受限的容量除法产生 |
| — | 合并 | merged | 价值段与诈唬段连成一片；价值受限的小尺度 |
| — | 线性 | linear | 牌力与尺度单调对应；`f` 不随尺度上升时的极限形状 |
| — | 价值范围 | value range | 供给 `V`，本节取 40 个组合数 |
| — | 诈唬范围 | bluff range | 供给 `A`，本节取 15 个组合数；`s(B)` 决定它能不能填满某个尺度 |
| — | 范围法 | range-based sizing logic | 由范围形状与容量决定尺度的那条路径，本节是它的算术版本 |
| — | 超池下注 | overbet | `B > P`；本节里它首先是个配额要求（40% 诈唬） |
| — | 牌型容量 | capacity | 一个范围能装下多少强牌与多少空气，即 `V` 与 `A` |
| — | 封顶范围 | capped range | 没有顶端的范围；`is_capped` 给出机器判据 |
| — | 下注尺度 | bet size | `B`；`s(B)`、`e*`、`stall(B)` 都是它的函数 |
