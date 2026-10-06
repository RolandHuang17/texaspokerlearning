# 单挑与三人池的范围优势不是同一件事

<!-- hands: 2 -->
<!-- terms: multiway, range-advantage, nut-advantage, capacity, the-nuts, heads-up, independent-defender-assumption, removal-effect, minimum-defense-frequency, equity-advantage, bluff-to-value-ratio, required-equity, combos, range, board, equity, call, fold, bet, pot, bluff, unverified-claim, generated-artifact, derivation-ref -->

## 本节目标 / Objectives

- 能用"这个底池里谁能赢"的**人数逻辑**解释：同一张牌面、同一批组合数，加入第三个玩家之后坚果优势为什么会塌掉，而哪个数字其实没有变。
- 能算出多人底池里每名防守者的频率地板与整桌的频率地板，并说出前者为什么随人数下降、后者为什么恒等于单挑 MDF。
- 能复述本仓库对这类计算的两条硬约束：频率公式里的独立防守假设，以及 `odds.py` 对 `exact=True` 的拒绝、`range_advantage.py` 对未排除牌面的范围的拒绝——并说清这两次拒绝各自在教什么。

## 前置知识 / Prerequisites

- `03-01` 胜率优势与坚果优势：本节把那两个"一家 vs 一家"的数改写成"一家占全桌多少"，所以要先把它们的定义带进来。
- `03-04` 牌面质地分类：稀释的幅度取决于这张牌面能让几家同时持有强牌，质地就是这件事的分类。

## 核心原理 / The principle

单挑与三人池里，"范围优势"是两个不同形状的陈述：

1. **防守端**：`N` 名防守者各自以频率 `d` 继续时，诈唬要成立需要**所有人**都弃牌，所以 `(1 − d)^N = B/(P + B)`，即

   ```
   d = 1 − (B/(P + B))^(1/N)          ← 每人地板
   1 − (1 − d)^N = P/(P + B)          ← 整桌地板，与 N 无关，恒等于单挑 MDF
   ```

   这是 `derived`，但推导用了一次**独立防守假设**（`pokergto.theory.multiway` 与 `table.07-01.multiway-defense` 的 `provenance.assumptions` 都写着这条）：真实发牌里各家的牌互相约束，移除效应会让合并值偏离。
2. **容量端**：一个范围对某个牌面的**牌型容量**（capacity）是能数的组合数——`who_can_win` 给出各家"能赢的组合数"占全桌的比例。这一步不需要独立性假设，纯粹是枚举，因此它是本节里唯一在三人池中也精确的量——**前提是范围先排除牌面**（下一节解释这条前提为什么由引擎强制）。

两件事合起来就是标题：**单挑的范围优势是一句话，三人池的范围优势是一份份额表。**

<!-- provenance: kind=derived verified=true -->
> !!! note "来源 / Provenance"
>     公式与份额都由本仓库实现推导：`src/pokergto/odds.py#defense_frequency_multiway`、`src/pokergto/theory/multiway.py#who_can_win`。三个范围是讲解用的声明输入（`reference`），见来源一节。

## 推导 / Derivation

**每人地板与整桌地板。** 设底池 `P`、下注 `B`、防守者 `N` 名。一名拿空气的对手要赢下底池，必须 `N` 家**同时**弃牌。若各家独立地以 `d` 继续，全桌弃牌率是 `(1 − d)^N`，无差别条件：

```
(1 − d)^N = B/(P + B)
1 − d = (B/(P + B))^(1/N)
d = 1 − (B/(P + B))^(1/N)
```

`1/N` 是指数——不是 `N`、也不是 `N − 1`。这一步是**唯一可能悄悄失败的地方**：`pokergto.theory.multiway` 的模块文档记录过一次真实的草稿错误，写成了 `1 − (1 − single)^(N−1)`，而它在 `N = 1` 时恰好退化成正确答案，所以通过了单挑检查、只在加入第二个对手之后才出错。因此 `N = 1` 回退是这条公式的自检而不是装饰：

```
N = 1:  d = 1 − B/(P+B) = P/(P+B) = MDF          ← 与 02-03 同一个数
```

整桌地板由同一个等式直接得到，`N` 消掉了：

```
1 − (1 − d)^N = 1 − B/(P + B) = P/(P + B)          ← 恒等于单挑 MDF
```

`python -m pokergto mdf --pot 12 --bet 12 --opponents 2` 打印 `d = 0.2929 each, joint 0.5000 (equals the heads-up MDF)`，即每人只需防守 29.29%，而全桌仍须防守 50%——**两句"要防守"里的"防守"是两个不同的量**；`table.07-01.multiway-defense` 的 `至少一人防守` 列与 `单挑 MDF` 列在每一行都相等，就是这件事的机器版本。

读那张表要先知道它的分组方式：产物按尺度分块（每块 5 行，`对手数` 从 1 到 5），块序就是 `rows` 里 `size` 字段的出现顺序 `0.33 / 0.5 / 0.75 / 1.0`，而 `columns` 里**没有** `size` 这一列——所以四个块在渲染后没有尺度标签。本节引用它的每一个数都另附一条命令或一次除法，不靠那张表认尺度。

**引擎拒绝精确值。** 分母开 `N` 次方一般是有理数的无理根，所以 `defense_frequency_multiway` 在 `N > 1` 且 `exact=True` 时直接抛错，本节原样引用：

```
>>> defense_frequency_multiway(12, 12, 2, exact=True)
ValueError: multiway MDF involves an N-th root, which is irrational for most inputs; call with exact=False, or request N=1 for the closed form
```

这条拒绝教的东西比返回值更多：**多人频率是一个给定假设下精确、但不在有理数域里的量。**`02-02` 那一类单街门槛能化成 `Fraction`，这里不能。本节写 29.29% 的时候，它是无理数 `1 − 1/√2`（`B/(P+B) = 1/2`、`N = 2`）的十进制读数。

**容量份额，以及必须先排除牌面。** 对每个范围 `R_i` 与牌面 `b`：`v_i = #{combo ∈ R_i : category(best_score(combo, b)) ≥ 门槛}`，然后 `share_i = v_i / Σ v_j`。这就是 `who_can_win` 的全部——**它不是概率**，它是"这张牌面上能赢的组合数里，各家占几成"。

这里有一次引擎的拒绝必须写进课程，因为它本身就是内容：`nut_advantage` 与 `is_capped` 要求传进来的范围**已经排除牌面**，否则拒绝计算：

```
>>> is_capped(parse("AKs,AQs,ATs,KQs,AKo,AQo,99,77"), parse_cards("Kh7s3d"))
InputError: is_capped: range 0 still holds 7c7s, a card on the board. Narrow it with Range.with_removed(*board) or notation.parse(spec, exclude=board); nut shares and combo counts divide by what the range contains.
```

原因是分母：`range_equity` 会自己屏蔽与牌面冲突的组合，而坚果占比除以"你交给它的那些组合"。两条列因此回答两个不同的问题——**同一张表里胜率是诚实的、份额是被放大的，而且放大的幅度看起来永远不像错误。**本节的每个容量数都在 `Range.with_removed(*board)` 之后计算。把同一批范围按两种方式喂给引擎，差异可测（牌面 `Kh7s3d`，CO 的声明范围）：

- 排除牌面后：组合数 `44.0`，`≥ 一对` 的组合 `24`，`≥ 两对` 的组合 `3`（就是 `77` 里不含 `7s` 的那三组三条）。
- 不排除：组合数 `52.0`，`≥ 一对` `32`，`≥ 两对` `6`——多出来的 8 个与 3 个是**物理上不可能被发到**的组合。
- 份额反而几乎不动：`≥ 一对` 的三家份额从 `0.347826 / 0.260870 / 0.391304`（排除后）变成 `0.340426 / 0.255319 / 0.404255`（未排除）。**份额稳、计数错**，正是那种"看起来永远不像错误"的错。

结构性边界也要说清：`≥ 同花` 在最多两张同花的三张牌面上恒为 `0`（两家手牌加三张公共牌凑不出五张同花色），此时 `who_can_win` 返回全零；而在单色牌面 `Ts8s2s` 上它不为零（例 3）。门槛（`minimum_category`）本身是选择，把"一对"换成"两对"就是换一个故事。

## 直觉 / Intuition

单挑时"我的范围更强"像拔河：一根绳子，两边比谁的力大。三人池时底池变成一个被切开的饼：**你的绝对实力没变，你的份额变了。**

- `Kh7s3d` 上，排除牌面之后 CO 在"两对及以上"这一档只有 `3` 个组合；BTN 带来 `9` 个。CO 的 3 个从"全桌的 100%"变成"全桌的 25%"——坚果优势塌掉的不是牌，是所有权。
- 防守端方向相反：人在变多，而你**自己**必须继续的比例在变小（50% → 29.29%）。不是因为你变弱，而是因为整桌的 50% 不必由你一个人扛——但也不是弃牌许可，因为那 50% 里有你的一份。
- 一句可带走的记忆：**人数改变份额与频率，不改变诈唬需要的弃牌率**（`B/(P+B)` 里没有 `N`；`continuation_fold_requirement` 返回的就是这个不变量）。

## 算例 / Worked examples

以下每个数都由本节列出的命令产生；容量类数字一律在 `Range.with_removed(*board)` 之后计算；胜率来自精确枚举（无抽样误差）。

**例 1 — 每人地板与整桌地板（`mdf` 子命令）。**

- `python -m pokergto mdf --pot 12 --bet 12 --opponents 2` → 每人 `0.2929`，整桌 `0.5000`，等于单挑 MDF `0.5000`。
- `python -m pokergto mdf --pot 12 --bet 12 --opponents 3` → 每人 `0.2063`，整桌仍是 `0.5000`。
- `python -m pokergto mdf --pot 12 --bet 4 --opponents 2`（1/3 池）→ 每人 `0.5000`，整桌 `0.7500`。
- `python -m pokergto mdf --pot 6.5 --bet 2.1667 --opponents 2` → 每人 `0.5000`，整桌 `0.7500`；同一命令去掉 `--opponents` 得到单挑 MDF `0.7500`。

第三条里有个值得停一下的巧合：1/3 池、两名防守者时**每人的地板正好是 50%**，与单挑面对底池下注的地板同一个数。同一句"防守一半"回答两个不同问题：那里是"你加另一个人要凑够 75%"，这里是"你就是那 50%"。

**例 2 — 两对档的所有权稀释（牌面 `Kh7s3d`）。** 三个声明范围（前两个与 `table.03-01.equity-vs-nut-advantage` 第一行的 hero/villain 同源）：CO `"AKs,AQs,ATs,KQs,AKo,AQo,99,77"`、BB `"KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s"`、BTN `"KK,QQ,JJ,77,33,AKs,AQs,KJs,QJs,JTs"`。排除牌面后组合数 `44.0 / 58.0 / 39.0`。用 `python -c` 调 `pokergto.theory.multiway`：

- 门槛 `ONE_PAIR`：能赢的组合数 `24 / 18 / 27`。两家（CO vs BB）份额 `0.571429 / 0.428571`；三家份额 `0.347826 / 0.260870 / 0.391304`。CO 从明显多数掉到三分之一强。
- 门槛 `TWO_PAIR`：`3 / 0 / 9`。两家份额 `[1.0, 0.0]`——CO **独占**这一档；三家份额 `[0.25, 0.0, 0.75]`，BTN 成为持有者。这就是"坚果优势被稀释"的确切含义：CO 没变弱，而是顶端组合有人一起持有。
- 门槛 `FLUSH`：`0 / 0 / 0`，`who_can_win` 返回全零——这张最多两同花的三张牌面上同花不存在。

**例 3 — 单色牌面让稀释可见（`Ts8s2s`）。** 声明范围 CO `"AA,KK,QQ,AKo,AQs,ATs,KQs"`、BB `"JTs,T9s,98s,76s,QJs,J9s,54s"`、BTN `"99,88,77,AJs,KJs,QTs,T9o,ATo"`，排除牌面后组合数 `41.0 / 25.0 / 44.0`。同花档计数 `2 / 4 / 2`：

- 两家（CO vs BB）`[0.333333, 0.666667]`；三家 `[0.25, 0.5, 0.25]`。
- 一对档计数 `23 / 13 / 38`：两家 `[0.638889, 0.361111]`；三家 `[0.310811, 0.175676, 0.513514]`。

同一张牌面、只多了一家：顶端档从 0.3333 掉到 0.25（掉 8.33 个百分点），一对档从 0.6389 掉到 0.3108（掉 32.81 个百分点）。**低档被稀释得更狠**，因为新进来的一家带来的是对子级别的牌。这就是"多人底池里价值门槛要抬高"的组合学来源，不是风格建议。

**例 4 — 坚果优势的成对读数在换对手时翻掉（`Kh7s3d`）。** `python -c` 调 `pokergto.theory.range_advantage.nut_advantage`（`near_nuts=0`）与 `is_capped`，两个函数都要求范围已排除牌面：

- `nut_advantage(CO, BB)` = `[0.068182, 0.0]`：单挑时 CO 是唯一持有当前顶端档（三条 7）的范围。
- `nut_advantage(CO, BTN)` = `[0.0, 0.076923]`：**换成 BTN 做对手，CO 的坚果占比归零**，因为 BTN 的范围里有 `KK`（三条 K 才是这张牌面可达的上限），而 CO 没有。
- `is_capped`：CO `True`、BB `True`、BTN `False`（定义：范围里的最强手低于"任意两张牌在此牌面可达的上限"）。

同一条牌面、同一批组合，只换了"对面是谁"，结论从"CO 能下大注"变成"CO 的范围封顶"。这正是单挑句子不能原样搬进三人池的原因。

**例 5 — 单挑句必须落在具体算出的行上。** 用 `python -c` 调 `pokergto.theory.range_advantage.advantage(..., mode="exact")`（它自己会做牌面排除），三行的胜率列都能与本节引用的产物 `table.03-01.equity-vs-nut-advantage` 逐位对齐：

- `Kh7s3d`，CO 开池范围 vs BB 跟注范围：hero 胜率 `0.715272`、对手 `0.284728`（优势 `+0.430545`）；坚果占比 `0.068182` 对 `0.0`；`who_can_bet_often = hero`、`who_can_bet_big = hero`。
- `9h6d3c`，BTN 开池 `"AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs"` vs BB `"87s,76s,65s,54s,T8s,T9s,98o,97o,66,55"`：hero 胜率 `0.368154`、对手 `0.631846`（优势 `−0.263691`），但坚果占比 `0.047619` 对 `0.0`（坚果优势 `+0.047619`）；`who_can_bet_often = villain`、`who_can_bet_big = hero`。**低连接面上开池方既不是"更强"也不是"更弱"，两个方向不一致。**
- `As9s5d`，CO `"AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT"` vs BB `"KQs,QJs,KJs,JTs,98s,76s,99,55"`：hero 胜率 `0.610233`（优势 `+0.220466`），坚果占比 `0.0` 对 `0.103448`（坚果优势 `−0.103448`）→ `who_can_bet_often = hero`、`who_can_bet_big = villain`。

没有行的地方，本节不写单挑结论。

**例 6 — 诈唬与价值配比：门槛不变，范围能给的变了。** `pokergto.theory.multiway.bluff_value_ratio` 数"空气 : 价值"（价值 = 至少一对，范围已排除牌面）。牌面 `Kh7s3d`：CO `0.833333`（价值 24、空气 20）、BB `2.222222`（18/40）、BTN `0.444444`（27/12）。对照 `table.02-04.bluff-value-ratio` 里无差别条件允许的比值（`价值:诈唬` 列取倒数：1/3 池 → `0.25`、1/2 池 → `0.3333`、2/3 池 → `0.4`、3/4 池 → `0.4286`、底池 → `0.5`、3/2 池 → `0.6`、2x 池 → `0.6667`）：

- BTN 的 `0.444444` 落在 3/4 池（`0.4286`）与底池（`0.5`）之间 → 它是三者里唯一能用中到大尺度配平的范围。
- CO 的 `0.833333` 已经**超过标准阶梯最极端一档 2x 池允许的 `0.6667`**；BB 的 `2.222222` 更远。**这两个范围在这张牌面上无法用任何标准尺度配平**——不是"不该下注"，是"能赢的组合太少，撑不起下注"。
- 换成牌面 `9h6d3c`：CO `4.444444`、BB `4.0`、BTN `0.740741`，三家都超线；而这张低连接面上"至少一对"的组合数只有 `9 / 12 / 27`（排除牌面后），比 `Kh7s3d` 的 `24 / 18 / 27` 更薄。

无差别比例本身不含 `N`（它来自 `B/(P+2B)`），多人改变的是"你的范围能装下多少价值"。**这就是"小尺度高频"在多人底池死掉的算术位置。**

## 生成表 / Generated tables

第一张是本节的主产物：每个尺度 × 每个对手数的每人防守频率、整桌频率与单挑 MDF。

<!-- BEGIN AUTO:table.07-01.multiway-defense -->
| 对手数 | 每人防守频率 | 至少一人防守 | 单挑 MDF |
|---:|---:|---:|---:|
|      1 |       75.19% |       75.19% |   75.19% |
|      2 |       50.19% |       75.19% |   75.19% |
|      3 |       37.16% |       75.19% |   75.19% |
|      4 |       29.42% |       75.19% |   75.19% |
|      5 |       24.33% |       75.19% |   75.19% |
|      1 |       66.67% |       66.67% |   66.67% |
|      2 |       42.27% |       66.67% |   66.67% |
|      3 |       30.66% |       66.67% |   66.67% |
|      4 |       24.02% |       66.67% |   66.67% |
|      5 |       19.73% |       66.67% |   66.67% |
|      1 |       57.14% |       57.14% |   57.14% |
|      2 |       34.53% |       57.14% |   57.14% |
|      3 |       24.61% |       57.14% |   57.14% |
|      4 |       19.09% |       57.14% |   57.14% |
|      5 |       15.59% |       57.14% |   57.14% |
|      1 |       50.00% |       50.00% |   50.00% |
|      2 |       29.29% |       50.00% |   50.00% |
|      3 |       20.63% |       50.00% |   50.00% |
|      4 |       15.91% |       50.00% |   50.00% |
|      5 |       12.94% |       50.00% |   50.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.odds#defense_frequency_multiway`

<!-- generated by: tools/gen_tables.py from pokergto.odds::defense_frequency_multiway -->
<!-- END AUTO:table.07-01.multiway-defense -->

同一批数字从两个方向被钉住：产物 `checks` 里 `N=1` 必须复现单挑 MDF（`mdf_equality`），"整桌防守等于单挑 MDF"必须对每个 `N` 成立（`ev_matches_direct_calculation`，容差 `1e-9`），两条都通过。独立性假设写在同一产物的 `provenance.assumptions`，而不是被公式藏起来。

第二张给出无差别配比——例 6 的对照列，`价值:诈唬` 与允许的空气比例互为倒数：

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

## 实战牌局 / Live hands

**牌局 1（`hand.03-09-three-owners-of-one-tier`）— 三人池里"我的范围最强"这句话怎么碎。**

座位与钱：100bb，6 人局。CO 开池 2.5，BTN 跟注，BB 补齐到 2.5（SB 弃，其 0.5 为死钱）→ 底池 `2.5·3 + 0.5 = 8.0`，三家各身后 `97.5`（`spr(97.5, 8.0) = 12.1875`）。翻牌 `Kh7s3d`，三家范围比例子 2 的声明范围。

- 例 2 的数字直接决定这条线上谁有发言权：**两对及以上**的组合数是 CO `3`、BB `0`、BTN `9`。若 BTN 已弃牌（单挑），CO 拥有这一档的 100%；BTN 还在池里时 CO 只剩 `0.25`，BTN 拿走 `0.75`。
- 决策点：CO 要不要底池大小下注？先看单挑读数——`nut_advantage(CO, BTN) = [0.0, 0.076923]`、`is_capped(CO) = True`。这两行把"CO 可以下大注"直接否决：**这张牌面的顶端组合属于 BTN，CO 连牌面可达上限都碰不到。**
- 把对手换回 BB（BTN 弃牌），同一张牌面变成 `nut_advantage(CO, BB) = [0.068182, 0.0]`，CO 反而成了顶端档唯一持有者。同一个 CO、同一个 `Kh7s3d`，**只因为第三家是否还在，结论相反。**
- 这里没有一个数来自对手模型：它们是排除牌面之后枚举出来的组合计数。

**牌局 2（`hand.03-09-joint-defense-1-3-pot`）— 把单挑 MDF 逐人套用，代价算得出来。**

座位与钱：底池 `8.0`（同上），CO 下 1/3 池 `2.6667`，BTN 尚未行动，英雄在 BB——"你后面还有一个防守者"的结构，正是 `defense_frequency_multiway` 的语义（`N = 2`）。

- 命令：`python -m pokergto mdf --pot 6.5 --bet 2.1667 --opponents 2` 给出同尺度的两人结构：每人 `0.5000`、整桌 `0.7500`。本手牌底池是 8.0，比率先落地（1/3 池：`B/(P+B) = 0.25`）。
- 正确读法：BB 的**个人**地板是 50% 的组合数继续，整桌地板是 75%。若 BB 按单挑的 75% 防守（把 `02-03` 的数搬来），BTN 也照做，则整桌防守 `at_least_one_defense(0.75, 2) = 0.9375`——**超额 18.75 个百分点**，全桌几乎每次都跟一个 1/3 池。
- 超额防守不是"稳健"，它按定义要求你拿更弱的牌继续，而弱牌过不了单街门槛：`equity_needed_to_call(8.0, 2.6667) = 20.00%`，而 `Jd9d` 对 `"AA,KK,QQ,JJ,TT,AKs,AQs,ATs,KQs,AKo,AQo"` 只有 `0.152320`，跟一次是 `ev_call(8.0, 2.6667, 0.152320) = −0.635757`；尺度换成底池下注，同一个 15.2320% 是 `ev_call(12, 12, 0.152320) = −6.51648`。
- 反方向：若 BB 与 BTN 各只防 25%（远低于 1/3 池要求的每人 50%），整桌弃牌率 `0.75² = 0.5625` 超过所需的 `25.00%`，空气下注每手 `ev_pure_bluff(12, 4, 0.5625) = +5.0`；底池尺度版本是 `ev_pure_bluff(12, 12, 0.5625) = +1.5`。**少防的惩罚不需要读你，只需要对手会算。**

## 范围图 / Range chart

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

这张图是**单挑** 1/3 池下注的 MDF 配额：按牌力从高到低填到覆盖 1326 组合中的 `994.5` 个（75.00%）。它在三人池里的正确用法是"整桌的配额"，不是"每个人的配额"：同样面对 1/3 池，两名防守者各防 50% 就凑够整桌 75%（例 1 与牌局 2）；把这张图当成个人任务，会让两人各填 75%，整桌到 `0.9375`。

图例本身也不改：**配额解决"多少"，不解决"用哪些牌"**。多人底池里"用哪些牌"还额外取决于你后面那家会怎么反应——那正是 `03-08` 标为未核验的那一格。

## 为何成立、何时失效 / Why it works, when it breaks

**成立的前提**（两组强度不同，所以分开列）：

- 频率那条只需要：诈唬必须赢下**所有人**，且各家防守**相互独立**。第二条是假设不是事实：`table.07-01.multiway-defense` 的 `provenance.assumptions` 明写"移除效应会让真实合并值偏离"，`02-03` 也把这条列进"何时失效"。所以每人的频率是**给定独立性时精确**的量，而真实发牌会破坏独立性（两家同时持有同一花色就是最常见的例子）。本仓库不为这个偏差编数字：它记在假设字段里。
- 容量那条不需要独立性，但需要范围排除牌面（`nut_advantage`/`is_capped` 会拒绝不排除的输入，`who_can_win` 不拒绝、只是会算进不可能的组合）。它的代价是只回答"份额"，**不回答概率**——"至少一人成对"的概率要对多家联合发牌枚举，而 `pokergto.equity.range_equity` 只接 hero 与 villain：本仓库没有多人摊牌胜率函数。所以本节所有"谁能赢"的句子都是组合数份额，任何写成百分比概率的多人句子都是 UNVERIFIED（见陷阱 3）。

**它不再是该直接执行的句子的地方**：

1. **你可以加注。** 地板约束的是"继续"总量，跟注比例可以更低，只要加注补上（`02-03` 讲过，多人同样适用）。
2. **你后面那家改变你的底池。** 你的跟注给第三家更好的赔率——隐含/反向隐含的领域（`03-08`），不在这条公式里。
3. **未完成牌面上的坚果档是"当前可达最强"。** `nut_advantage` 按当前牌面而不是全部发展牌序取基准，因此对听牌方偏低；同一条也写在 `table.03-01.equity-vs-nut-advantage` 的假设字段里。最多两同花的三张牌面上同花档恒为 `0` 是这件事的极端例。
4. **ICM。** 地板假设筹码线性（第 12 章）。
5. **人数继续增加。** `N = 5` 时 1/3 池的每人地板掉到 `0.243285`（`table.07-01.multiway-defense`），公式没坏，但独立性坏得更厉害：五家范围在牌面上的重叠不再是小修正。

## 陷阱 / Common mistakes

1. **把单挑 MDF 逐人套进多人底池。** 面对底池下注，每人 50% → 整桌 `at_least_one_defense(0.5, 2) = 0.75`，比所需多 25 个百分点。*代价*：按定义要用更弱的牌继续，而 `QdJc` 对 `"AA,KK,QQ,JJ,TT,AKs,AQs,AKo,AQo"` 的 `0.102222` 在底池尺度上是 `ev_call(12, 12, 0.102222) = −8.320008` 每手——超额防守不是买保险，是买了一张单程票。
2. **把单挑的坚果优势句子原样搬进三人池。** 例 2 的 `TWO_PAIR` 档：两家 `[1.0, 0.0]`、三家 `[0.25, 0.0, 0.75]`，而 CO 的绝对组合数一直是 `3`。*代价*：按单挑读法 CO 会把这张干燥高牌面当成自己的大尺度场；实际顶端组合的 9 个在 BTN 手里，`nut_advantage(CO, BTN) = [0.0, 0.076923]` 与 `is_capped(CO) = True` 已经把大尺度还给了 BTN。
3. **把容量份额读成"有人拿好牌的概率"。** 常见句子是"三人池里 70% 的情况下至少有人成对"。本仓库没有产生它的函数：`range_equity` 只接两家，`who_can_win` 给的是组合数占比。*代价*：这类数一旦被写进句子，就会被拿去给 float 或诈唬定价（`03-08`），而那两件事真正需要的只是 `B/(P+B)` 与 `B/(P+2B)`——都可算。**把一个可算的门槛换成一个不可算的概率，就是把能核验的决定换成不能核验的决定。**

## 练习 / Drills

- 手算：底池 12、下注 4、三名防守者，每人地板与整桌地板？（`python -m pokergto mdf --pot 12 --bet 4 --opponents 3` → 每人 `0.3700`，整桌 `0.7500`）
- 每人弃牌率：底池 12、下注 12、两名防守者时 `1 − d` 是多少？平方之后呢？（`1 − 0.292893 = 0.707107`，`0.707107² = 0.5`，正是 `continuation_fold_requirement(12, 12, 2) = 0.5`）
- 自检公式：令 `N = 1`，验证 `d` 回退成 `P/(P+B)`，并与 `python -m pokergto mdf --pot 12 --bet 6`（单挑 1/2 池，打印 `0.6667`）对齐。
- 拒绝精确值：跑 `defense_frequency_multiway(12, 12, 2, exact=True)`，读出 `ValueError` 原文，并解释为什么这个情形下的答案 `1 − 1/√2` 不是有理数。
- 拒绝未排除的范围：把 `parse("AKs,AQs,ATs,KQs,AKo,AQo,99,77")` 直接喂给 `is_capped(..., parse_cards("Kh7s3d"))`，读出那条 `InputError`；再按它提示的 `with_removed` 算一次，记下"`≥ 两对` 的组合数从 `6` 变成 `3`、而份额几乎不变"这个观察。
- 份额练习：用 `python -c` 在本节的 CO/BB 范围上换到牌面 `As9s5d`，BTN 用 `"KK,QQ,AQs,ATs,KTs,QTs,99,55,77"`（全部先排除牌面）。`≥ 一对` 计数 `36 / 26 / 30` → 两家 `[0.580645, 0.419355]`、三家 `[0.391304, 0.282609, 0.326087]`；`≥ 两对` 计数 `3 / 2 / 6` → 两家 `[0.6, 0.4]`、三家 `[0.272727, 0.181818, 0.545455]`；`≥ 三条` 计数 `3 / 0 / 6` → 两家 `[1.0, 0.0]`、三家 `[0.333333, 0.0, 0.666667]`。说出为什么把门槛从"两对"抬到"三条"会让 BTN 的份额从 0.5455 升到 0.6667。

## 自测清单 / Self-check

- [ ] 我能从"诈唬必须让所有人弃牌"推出 `d = 1 − (B/(P+B))^(1/N)`，并说明指数为什么是 `1/N` 而不是 `N − 1`。
- [ ] 我能说出整桌防守频率恒等于单挑 MDF，并指出 `table.07-01.multiway-defense` 里钉住它的两条 checks。
- [ ] 我能解释 `exact=True` 在 `N > 1` 时被拒绝的原因，以及 `nut_advantage` 为什么拒绝没排除牌面的范围。
- [ ] 给定牌面与三个范围，我能算出"能赢的组合数"份额，并说清它不是什么。
- [ ] 我能举出一个"单挑坚果读数在换对手之后翻掉"的具体行，并说出给出它的函数。

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->

| 内容 | 来源类型 | 位置 / 产生它的命令 |
|---|---|---|
| 多人每人防守频率与整桌防守频率 | `derived`（给定独立防守假设） | `src/pokergto/odds.py#defense_frequency_multiway`、`src/pokergto/theory/multiway.py#per_player_defense / #joint_defense`；`python -m pokergto mdf --pot … --bet … --opponents …` |
| 诈唬所需的联合弃牌率（与 N 无关） | `derived` | `src/pokergto/theory/multiway.py#continuation_fold_requirement` |
| `N>1` 时拒绝 `exact=True` | 引擎行为，原文引用 | `ValueError: multiway MDF involves an N-th root, which is irrational for most inputs; …` |
| 拒绝未排除牌面的范围 | 引擎行为，原文引用 | `InputError: is_capped: range 0 still holds 7c7s, a card on the board. …`；实现 `src/pokergto/theory/range_advantage.py#_assert_board_excluded` |
| 容量份额（24/18/27、3/0/9、2/4/2 等） | `derived`，无独立性假设，但需牌面排除 | `python -c`：先 `Range.with_removed(*board)`，再调 `pokergto.theory.multiway.who_can_win / value_and_air_combos` |
| 坚果占比与封顶判定（0.068182、0.076923、True/False） | `derived` | `python -c` 调 `pokergto.theory.range_advantage.nut_advantage / is_capped`（排除牌面后） |
| 单挑三行的胜率（0.715272、0.368154、0.610233）与坚果占比（0.068182、0.047619、0.103448） | `derived` | `python -c` 调 `pokergto.theory.range_advantage.advantage(..., mode="exact")`；胜率列与产物 `table.03-01.equity-vs-nut-advantage` 逐位一致 |
| 空气:价值（0.833333、2.222222、0.444444；4.444444、4.0、0.740741） | `derived` | `python -c` 调 `pokergto.theory.multiway.bluff_value_ratio`（排除牌面后） |
| EV（−0.635757、−8.320008、−6.51648、+5.0、+1.5）、0.9375、0.75 | `derived` | `python -c` 调 `pokergto.ev.ev_call / ev_pure_bluff`、`pokergto.odds.at_least_one_defense / equity_needed_to_call` |
| 产物 `table.03-01.equity-vs-nut-advantage` 的**坚果占比列**（11.5385%、9.0909%、16.6667%） | **UNVERIFIED / 与本节命令不一致** | 本节的命令给出 6.8182%、4.7619%、10.3448%。差异来自引擎现在要求范围先排除牌面（见上面两条拒绝），而该产物的这两列是排除规则之前生成的读数。本节的句子一律采用可复算的那一组；这条差异属于 `data/gen` 与 `src/` 的协调问题，本节只记录、不修改。 |
| 三个"声明范围"（CO/BB/BTN 的 spec 字符串） | `reference` + **UNVERIFIED** | 讲解用输入：不是求解结果，也不是任何人群的开池/跟注范围。换成求解决策需要 `data/src` 的 spot 产物 + `tools/gen_tables.py`。 |
| 独立防守假设本身 | `reference` + **UNVERIFIED** | 移除效应使其不成立；产物把这条写进 `provenance.assumptions`。本仓库尚无量化该偏差的产物（多人摊牌胜率函数不存在，`range_equity` 只接两家）。 |
| "三人池里至少一人成对的概率"这类句子 | **UNVERIFIED**，本节拒绝给出 | 没有产生它的函数；本节任何这类百分比都不是本仓库的结论。 |

本节没有商业求解器输出、没有抄来的范围表、没有截图。

## 术语 / Terms

<!-- terms: multiway, range-advantage, nut-advantage, capacity, the-nuts, heads-up, independent-defender-assumption, removal-effect, minimum-defense-frequency, equity-advantage, bluff-to-value-ratio, required-equity, combos, range, board, equity, call, fold, bet, pot, bluff, unverified-claim, generated-artifact, derivation-ref -->

| 缩写 | 中文 | English | 本节里的含义 |
|---|---|---|---|
| — | 多人底池 | multiway | 两名或以上防守者仍在决策的环境，不是"翻前人多" |
| — | 单挑 | heads-up | 两人结构，`N = 1` 的回退点 |
| — | 范围优势 | range advantage | 单挑里是一个句子，多人里是一份份额表 |
| — | 胜率优势 | equity advantage | 分布对分布的平均胜率差，来自具体行（例 5） |
| — | 坚果优势 | nut advantage | 谁持有当前牌面的顶端组合，会被人数稀释 |
| — | 坚果 | the nuts | 该牌面当前可达的最强手，不是"很大的牌" |
| — | 牌型容量 | capacity | 一个范围能装下多少强成牌，本节以组合数计数 |
| — | 独立防守假设 | independent defender assumption | 频率公式的前提，写在产物假设字段里 |
| — | 移除效应 | removal effects | 使上一条不成立的原因，也是本节排除牌面的理由 |
| MDF | 最低防守频率 | minimum defense frequency | `P/(P+B)`，整桌的地板；每人地板见例 1 |
| B:V | 诈唬与价值比 | bluff-to-value ratio | 无差别配比，例 6 的对照列 |
| — | 所需胜率 | required equity | 单街门槛 `equity_needed_to_call` |
| — | 组合数 | combos | 份额的分子与分母，本节唯一加权单位 |
| — | 未核验声明 | unverified claim | 声明范围与概率型多人句子所属的类别 |
| — | 生成物 | generated artifact | `data/gen` 下的表与图 |
| — | 推导指针 | derivation reference | 产物里的 `provenance.derivation_ref` |
