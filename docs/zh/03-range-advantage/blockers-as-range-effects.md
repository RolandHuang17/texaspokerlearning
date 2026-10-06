# 把阻断牌读成范围效应：谁的手里不可能有那手牌

<!-- hands: 2 -->
<!-- terms: blocker, removal-effect, range, combos, minimum-defense-frequency, bluff-range, value-range, the-nuts, showdown, capacity, hand-class, board -->

## 本节目标 / Objectives

- 能对任意"类别 + 可见牌"的组合，用 `Range.with_removed` 跑出剩余组合数，并说清同花两张与异花两张为什么删掉的数量不同。
- 能用包含–排除式子（`命中第一张 + 命中第二张 − 同时命中两张`）预先算出删除数，而不必逐个列举。
- 能把一个阻断牌写回一份完整范围：算出对手防守侧、弃牌侧各自的剩余组合，以及半池下注要求的最小防守组合数（`MDF × 剩余组合`）。
- 能说出一个具体 bluff 候选在两种物理牌面下的期望差，并指出差别来自哪个类的哪几个组合。

## 前置知识 / Prerequisites

- `01-02` 阻断牌与移除效应：一张牌如何改掉对手的组合计数；本节把那条算子用到整份范围上。
- `03-01` 胜率优势与坚果优势：坚果份额是一个比值，因此移除会同时改分子和分母。
- `02-03` MDF：`pot/(pot+bet)`，以及"防守义务是总量约束，不指定用哪些组合去满足"。

## 核心原理 / The principle

阻断牌不是"这手牌看起来安全"这个形容词，而是一个可以逐项执行的算子：从一份范围里删掉所有含某张牌的具体组合。删掉的**数量**由那两张牌的物理花色决定，不由它们的点数决定。

同一句话的具体版本：`AKo` 在 `As` 与 `Ks` 可见时剩 **6** 个组合，在 `As` 与 `Kh` 可见时剩 **7** 个。两组可见牌的点数完全一样（一张 A、一张 K），删除数差 1，因为 `(As,Kh)` 本身是 `AKo` 的一个组合、而 `(As,Ks)` 属于 `AKs`。本节的全部推理建立在这一个事实上。

由此得到"把阻断牌读成范围效应"的方法：不要说"他不太可能有坚果"，要说"他的范围里那一档的组合数从 X 变成 Y，因此他的防守配额、我的诈唬期望各自变成多少"。

<!-- provenance: kind=derived verified=true -->
> !!! note "来源 / Provenance"
>     所有组合计数：`pokergto.ranges.Range.with_removed`（derived，见 `table.03-05.removal-effect-by-class`）。
>     期望与门槛：`pokergto.evaluator.best_score` 逐组合判胜负 + `pokergto.odds`（derived）。
>     范围本身是本仓库为讲解写死的示例（`reference`）。

## 推导 / Derivation

### 一条式子：包含–排除

设 `R` 是一份范围（1326 维的组合权重向量），可见牌集合 `V`。引擎的定义是：

```
R.with_removed(*V)[i] = 0   当 ALL_COMBOS[i] 的任一张牌 ∈ V
                        = R.weights[i]   其余
```

对单个 169 类 `C`，删掉的数量满足包含–排除：

```
removed(C, {c1, c2}) = hits(c1) + hits(c2) − hits(c1 且 c2 同在一个组合里)
```

`hits(c)` 在类里等于"含这张牌的组合数"：对子类里是 3（`AA` 的 6 个组合里含 `As` 的是 `Ah/Ad/Ac` 三种），同花类里是 1，不同花类里是 3。第三项只有当 `(c1, c2)` 本身就是 `C` 的一个组合时才非零。

### 为什么同花的两张删得更多

`AKo` 的 12 个组合是"两张不同花色的 A 与 K"。可见牌给 `As`：命中 3 个（`AdKs? ` 不——含 `As` 的 `AKo` 组合是 `(Ah,Kd)`…，即 `(Ah,As?)` 不对；准确地说，含 `As` 的 `AKo` 组合是 `As` 配任一张非黑桃的 K，共 3 个）。可见牌再给 `Kh`：命中另外 3 个（`Ah Kh`、`As Kh`、`Ac Kh`）。两组的交是 `(As,Kh)` 这一个组合，且 `(As,Kh)` 确实属于 `AKo`（两张不同花色），所以 `removed = 3 + 3 − 1 = 5` → 剩 **7**。

换成 `As` 与 `Ks`：`As` 命中 3 个、`Ks` 命中 3 个，但 `(As,Ks)` 是同花的，属于 `AKs`，不在 `AKo` 的 12 个里 → 交集为空 → `removed = 3 + 3 − 0 = 6` → 剩 **6**。

**同一句话反过来也成立，而且方向相反。** 对同花类 `AKs`（4 个组合），`As+Ks` 命中 1+1−1 = 1 → 剩 3；`As+Kh` 命中 1+1−0 = 2 → 剩 2。规则是：**你的两张牌从"它们自己不可能是的那一类"里删得最多。** 拿着两张同花牌，你删不掉自己那类的一个组合、却能删光对手不同花类里的六个。

### 范围上的移除 vs 图上的移除

`with_removed` 作用在 1326 维向量上，所以它知道物理组合。一张 13×13 的频率图（每格一个 0–1 的数）不知道：格子里存的是频率，不是哪些花色。后果是——

- 对**按类填的**范围（例如 `parse("AKo,AQo,KQs,99")`），删掉 `Kd` 与删掉 `Kh` 得到的总数相同，因为类里四个/十二个花色是对称的；差别只在类内部哪几个组合被删。
- 对**真实的一手牌 vs 一份范围**（`Range.from_cards` 的对手侧），花色才第一次变得要紧：牌局 1 里三个"同为 `AJ`"的候选，删掉的同花组合数是 0、1、2 个，期望差 11.76 个筹码。
- 频率非整数的格子（`0.333333`）删除后仍是小数：`12 × 0.333333 = 3.999996`。这是 `01-01` 讲过的记法代价，别把它当成计数错误。

## 直觉 / Intuition

把一份范围想成仓库里的一排抽屉，每个抽屉 4、6 或 12 个具体的盒子。**阻断牌不是"某个抽屉概率变小"，而是从抽屉里拿走几个盒子。** 拿走的个数取决于你手上那两张牌的形状，不取决于它们的点数有多响。

三句可以直接带去牌桌的话：

1. **同花的两张牌是"净"阻断牌。** 它们不可能同属一个不同花类，所以删除不重叠，把那个类删得更狠（`AKo` 6 个 vs 5 个）。
2. **一张牌同时动三档。** `Ad` 删对手的坚果同花（少一个跟注），也删对手 `AJo` 里含 `Ad` 的组合（少若干个**平分**）。只数一条边就会得出错的正负号。
3. **牌面两张同花时，同花这一档不存在。** 河牌才有第三张同花，阻断它才有意义（`03-04` 例 4）。

## 算例 / Worked examples

### 例 1 — 复现生成表里的每一行

```bash
PYTHONPATH=src python -c "
from pokergto.notation import parse
from pokergto.cards import Card
for spec, cards in [('AKo',('As',)),('AKo',('As','Kh')),('AKo',('As','Ks')),
                    ('AA',('As',)),('AA',('As','Ah')),('99',('9d',)),
                    ('KQs',('Ks',)),('KQs',('Kh','Qh')),('KJs',('As','Ks'))]:
    full=parse(spec); rem=full.with_removed(*[Card.parse(c) for c in cards])
    print(spec, cards, full.total_combos(), rem.total_combos())
"
```

输出与 `table.03-05.removal-effect-by-class` 的十行逐位相同：`AKo` 12 → 9 → 7 → 6；`AA` 6 → 3 → 1；`99` 6 → 3；`KQs` 4 → 3（可见 `Ks`）、4 → 3（可见 `Kh+Qh`：两张牌命中的是同一个组合 `KhQh`，所以 `1+1−1 = 1`，只删一个）；`KJs` 4 → 3（可见 `As+Ks`）。

### 例 2 — 类形状决定删除方向

同一组点数，换类的花色（全部由 `Range.with_removed` 现算）：

| 类 | 基线 | 可见 `As+Ks`（同花） | 可见 `As+Kh`（异花） | 说明 |
|---|---|---|---|---|
| `AKo` | 12 | **6**（删 6） | **7**（删 5） | 同花两张删得更多，因为删除不重叠 |
| `AKs` | 4 | **3**（删 1） | **2**（删 2） | 方向相反：异花两张删得更多 |
| `AJo` | 12 | 9 | **7**（`Ah+Jc`，删 5）/ `Ah+Jh` **6**（删 6） | 决定因素是"两张牌是否同花" |
| `QJs` | 4 | 4（`As+Ks` 与它无关） | **3**（`Qh+Jh`）/ **2**（`Qh+Jc`） | 同一点数对，1 个还是 2 个的组合差 |

表里 `AJo` 一行值得停一下：`Ah+Jh`（同花，`(Ah,Jh)` 属 `AJs`）删 6 → 剩 6；`Ah+Jc`（异花，`(Ah,Jc)` 属 `AJo`）删 5 → 剩 7。这与 `AKo` 那一行是同一条包含–排除式子的两次应用。

### 例 3 — 整份范围：牌面移除后每类剩多少

牌面 `Kd 9d 6d 4s 2h`（三张方块，同花当场成立），对手范围写成 `AQs,KQs,QJs,JTs,T8s,AJo,99,44`（44 个组合）。跑 `parse(spec).with_removed(*board)`：

| 类 | 原组合 | 剩余 | 被删的是谁 |
|---|---|---|---|
| `AQs` | 4 | 4 | 无（`AdQd` 两张方块都还在牌外） |
| `KQs` | 4 | 3 | `KdQd`（`Kd` 在牌面） |
| `QJs` | 4 | 4 | 无 |
| `JTs` | 4 | 4 | 无 |
| `T8s` | 4 | 4 | 无 |
| `AJo` | 12 | 12 | 无 |
| `99` | 6 | 3 | 含 `9d` 的 3 个 |
| `44` | 6 | 3 | 含 `4s` 的 3 个 |
| 合计 | 44 | **37** | 7 个 |

同花档一共 4 个组合：`AdQd`、`QdJd`、`JdTd`、`Td8d`（用 `category_of(best_score(...)) == Category.FLUSH` 逐组合筛出来）。这 4 个数字后面每一步都要用到：它们是这份范围的"坚果容量"，而容量是可以用花色改掉的。

### 例 4 — 把 MDF 换成组合数

`PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5` → MDF 0.6667（两人桌）。防守义务的绝对数是 `0.6667 × 剩余组合`：

| 剩余组合 | 来源 | 需要防守的组合 |
|---|---|---|
| 1326 | 全空间（`22+` 之类不算） | 884.000000 |
| 37 | 例 3，牌面移除后 | 24.666667 |
| 29 | 牌面 + hero 的 `AhJd` | 19.333333 |
| 28 | 牌面 + hero 的 `AhJh` | 18.666667 |

同一份范围、同一个尺度，只因为 hero 拿着的两张牌不同，对手的防守配额就从 18.666667 个组合变成 19.333333 个。**MDF 是比例，配额是组合；只有后者能核对。** 半池的弃牌率门槛由同一条式子给出：`50/150 = 33.3333%`（`pokergto.odds#required_fold_frequency`）。

## 生成表 / Generated tables

第一张是本节的骨架。注意最后两行与第三行的对照：`AKo` 的两张同花可见牌删 6、两张异花删 5；`KQs` 的两张同花只删 1。**这张表不对称，是设计出来的**，因为对称的说法（"有 A 有 K 就少 5 个"）正是被到处引用却经不起重算的那一句。

<!-- BEGIN AUTO:table.03-05.removal-effect-by-class -->
| 类别 | 可见牌 |  原本组合数 | 剩余组合数 | 被删组合数 |
|---:|---:|---:|---:|---:|
|  AKo |     As | 12.0 combos | 9.0 combos | 3.0 combos |
|  AKo |  As+Kh | 12.0 combos | 7.0 combos | 5.0 combos |
|  AKo |  As+Ks | 12.0 combos | 6.0 combos | 6.0 combos |
|   AA |     As |  6.0 combos | 3.0 combos | 3.0 combos |
|   AA |  As+Ah |  6.0 combos | 1.0 combos | 5.0 combos |
|   99 |     9d |  6.0 combos | 3.0 combos | 3.0 combos |
|  KQs |     Ks |  4.0 combos | 3.0 combos | 1.0 combos |
|  KQs |     Qh |  4.0 combos | 3.0 combos | 1.0 combos |
|  KQs |  Kh+Qh |  4.0 combos | 3.0 combos | 1.0 combos |
|  KJs |  As+Ks |  4.0 combos | 3.0 combos | 1.0 combos |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.ranges#Range.with_removed`

<!-- generated by: tools/gen_tables.py from pokergto.ranges::Range.with_removed -->
<!-- END AUTO:table.03-05.removal-effect-by-class -->

第二张表把"防守义务"随尺度变化的曲线放在同一个地方，好让例 4 的配额换算有一个来源：`MDF` 那一列乘上剩余组合就是配额，`fold_frequency_needed` 那一列就是诈唬的门槛。

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

## 实战牌局 / Live hands

### 牌局 1（`hand.03-05-flush-combo-blocker`）— 三个"同一类"的 bluff 候选，期望差 11.76

6 人桌现金局。CO 开池 2.5x，BB 跟注。翻牌 `Kd 9d 6d`，转牌 `4s`，河牌 `2h`。底池 100，hero 在 CO 下注 50 诈唬。对手范围写成 `AQs,KQs,QJs,JTs,T8s,AJo,99,44`（44 个组合，牌面移除后 37 个）。hero 的三个候选在 169 记法里都是 `AJ`，摊牌分数都是 `high card A-K-J-9-6`：

| hero 的底牌 | 类别 | 对手的剩余组合 | 击败 hero | 与 hero 平分 | hero 赢下 | 对手防守率 | hero 这手的期望 |
|---|---|---|---|---|---|---|---|
| `AhJh` | `AJs` | 28 | 15 | 6 | 7 | 75.00% | **+8.93** |
| `AdJh` | `AJo` | 29 | 15 | 7 | 7 | 75.86% | **+10.34** |
| `AhJd` | `AJo` | 29 | 13 | 7 | 9 | 68.97% | **+20.69** |

差别在哪：牌面移除后对手的 37 个组合里，**跟注档 16 个、平分档 12 个（`AJo` 全部）、弃牌档 9 个**，其中同花档恰好 4 个：`AdQd`、`QdJd`、`JdTd`、`Td8d`。三个候选删掉的东西完全不同：

- `AhJh`：一个同花都没删。它删掉 9 个组合 = 6 个平分（`AJo` 12 → 6）+ `AhQh`（跟注）+ `JhTh`、`QhJh`（弃牌）。跟注档仍是 15 个，弃牌档掉到 7 个。
- `AdJh`：`Ad` 杀掉坚果同花 `AdQd`（跟注 −1），`Jh` 杀掉 `JhTh`（弃牌 −1），`AJo` 12 → 7（删 5，正是"异花两张命中同一个组合"的那条包含–排除）。
- `AhJd`：`Jd` 一次杀掉 **两个** 同花（`JdTd` 与 `QdJd`，跟注 −2），另外删 `AhQh`（跟注）与 5 个 `AJo` 平分；对手的弃牌档 9 个**一个没动**，所以 hero 的赢档是三者里最高的 9 个。

也就是说，"阻断坚果"这个直觉给三个候选画了同一张像，而账上分别是：删 0 个跟注、删 1 个跟注、删 2 个跟注——同时 `AhJh` 还多删了 2 个弃牌。

模型：最坏情形——凡是牌面分数**不低于** hero 的组合都算对手跟注（平分的记作 `+100/2 − 50 = +50`），严格低于的才算弃牌。期望式 `EV = (赢 × 100 + 平分 × 50 − 被跟 × 50) / 剩余组合`。门槛：`PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5` → 需要 `50/150 = 33.3333%` 的弃牌率。三个候选都过线，但**最坏与最好之间差 11.76 个筹码/次**——同一个"阻断坚果"的直觉，给出三种不同的账。

复现：

```python
from pokergto.cards import Card, class_key
from pokergto.notation import parse
from pokergto.evaluator import best_score
board = [Card.parse(c) for c in ("Kd","9d","6d","4s","2h")]
v = parse("AQs,KQs,QJs,JTs,T8s,AJo,99,44").with_removed(*board)   # 37.0
for hand in ("AhJh","AdJh","AhJd"):
    h = [Card.parse(hand[:2]), Card.parse(hand[2:])]
    hs = best_score(h, board)
    rest = v.with_removed(*h)
    win = sum(w for a,b,w in rest if best_score([a,b],board) < hs)
    tie = sum(w for a,b,w in rest if best_score([a,b],board) == hs)
    lose = rest.total_combos() - win - tie
    print(hand, class_key(*h), rest.total_combos(), lose, tie, win,
          100*(lose+tie)/rest.total_combos(), (win*100+tie*50-lose*50)/rest.total_combos())
```

### 牌局 2（`hand.03-05-same-class-different-suit`）— 同一格、同一摊牌分数，一个是 0 另一个是 −1.79

同一局，另一种发法：河牌 `Kd 9d 6c 4s 2h`（只有两张方块，同花这一档**不存在**，见 `03-04` 例 4）。底池 100，hero 在 CO 下 50。对手范围 `AQo,KQs,99,66,QJs,JTs,T8s`：牌面移除后 33 个组合（`KQs` 剩 3，`99`、`66` 各剩 3）。hero 的两个候选都在 `QJs` 这一格，摊牌分数都是 `high card K-Q-J-9-6`：

| hero 的底牌 | 对手剩余 | 击败 hero 的 | 平分 | hero 赢下 | 弃牌率 | 需要防守的组合（2/3） | 期望 |
|---|---|---|---|---|---|---|---|
| `QhJh` | 27 | 17 | 3 | 7 | 25.93% | 18.000000 | **+0.00** |
| `QdJd` | 28 | 18 | 3 | 7 | 25.00% | 18.666667 | **−1.79** |

机制只有一处。牌面移除后对手的 33 个组合分成三档：跟注 21（`AQo` 12 + `KQs` 3 + `99` 3 + `66` 3）、弃牌 8（`JTs` 4 + `T8s` 4）、平分 4（`QJs`，与 hero 同为 `K-Q-J-9-6`）。`Qh` 与 `Qd` 同样删掉 3 个 `AQo`（跟注），同样删掉自己那一格里的 1 个 `QJs`（平分），差别在第三刀落在哪：

- `QhJh` 删掉 `KhQh`——`KQs` 的三个剩余组合是 `KsQs`、`KhQh`、`KcQc`（`KdQd` 已被牌面删），那是对手的**跟注**档。跟注掉到 17。
- `QdJd` 删掉 `JdTd`——`JTs` 的高牌，是对手的**弃牌**档。跟注仍是 18。

于是同样两块的牌力，一个把最硬的那档删薄 1 个，另一个把最软的那档删薄 1 个。决策因此分开：`QhJh` 恰好保本（期望 **0.00**），`QdJd` 每手亏 **1.79**。

把候选换成 `AhQh` 与 `AhQd`（同为 `AQ` 家族）看得更清楚，也正是生成表那两行的范围版本：

| hero 的底牌 | 对手的 `AQo` 剩余 | 对手剩余总数 | 击败 hero | 平分 | hero 赢下 | 期望 |
|---|---|---|---|---|---|---|
| `AhQh`（两张同花） | 12 → **6** | 25 | 8 | 6 | 11 | **+40.00** |
| `AhQd`（两张异花） | 12 → **7** | 27 | 9 | 7 | 11 | **+37.04** |

`AhQh` 删 6 个 `AQo`（`3+3−0`：`(Ah,Qh)` 属 `AQs`，两次命中不重叠），`AhQd` 只删 5 个（`3+3−1`）。这正是生成表里 `As+Ks → 6` 与 `As+Kh → 7` 那两行的范围版本，只是这里的 12 个 `AQo` 对 hero 来说是**平分档**：`AhQh` 把平分从 12 砍到 6，`AhQd` 只砍到 7。两手的弃牌档都是 11 个，分子同为 `11×100 + 平分×50 − 跟注×50 = 1000`，于是分母小的一手期望更大：`1000/25 = +40.00` 对 `1000/27 = +37.04`，差 **2.96**。同一个"我拿着 AQ"的直觉，在两类不同的对手范围上给出方向相反的结论——这正是不许凭直觉、必须逐类相减的理由。

## 范围图 / Range chart

<!-- BEGIN AUTO:range.02-03.mdf-floor-vs-half-pot -->
|   | A  | K  | Q  | J  | T  | 9  | 8  | 7  | 6  | 5  | 4  | 3  | 2  |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| K | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| Q | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| J | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| T | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 9 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 8 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· |
| 7 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· |
| 6 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· |
| 5 | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | @@ | ·· | ·· | ·· |
| 4 | @@ | @@ | @@ | @@ | @@ | @@ | :: | ·· | ·· | ·· | ·· | ·· | ·· |
| 3 | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |
| 2 | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· | ·· |

覆盖 884.0 组合 = 全 1326 的 66.67%

图例：`··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%；对角线为对子，上三角同花，下三角不同花。

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.odds#minimum_defense_frequency`

<!-- generated by: tools/gen_ranges.py (schema: range_chart) -->
<!-- END AUTO:range.02-03.mdf-floor-vs-half-pot -->

这张图是 `02-03` 的半池 MDF 底线，覆盖 884 个组合（`1326 × 2/3`，artifact 记 `total_combos = 883.999996`）。本节用它说明一件容易被跳过的事：**频率图看不见阻断牌。**

1. 图上每格存的是**频率**，不是哪几张花色。所以从这张图上删掉 `Kd` 和删掉 `Kh` 得到同一个答案：`884 → 737.999997`（丢掉 145.999999 个组合，`with_removed` 逐个组合筛）。防守配额跟着从 `883.999996 × 2/3 = 589.333331` 掉到 `737.999997 × 2/3 = 491.999998`。花色不对称——也就是本节的全部论点——在类级图上**表达不出来**。
2. 要让阻断牌起作用，范围必须落到具体组合：`Range.from_cards`（我自己这一手）对上一份类级范围（对手），就像牌局 1 和牌局 2 那样。那时删掉哪几个组合才会改变比值。
3. 图不含任何对手调整。"对手因为这张面 / 因为他的阻断牌少守一点"这句话不是这张图能支持的：图只是一个 MDF 可行解。此类说法的处理办法见"来源与置信度"的 UNVERIFIED 段。

## 为何成立、何时失效 / Why it works, when it breaks

**为什么成立。** `with_removed` 只做一件事：把含可见牌的组合权重清零。它的正确性来自 `ALL_COMBOS` 是全部 1326 个物理组合这一点（`pokergto.cards` 有 `InvariantError` 断言），不涉及任何牌力、玩家或尺度。包含–排除式子则只用到"一个组合恰好由两张牌组成"。

**什么时候不能这样用：**

1. **类的写法限制了删除的粒度。** `notation.parse` 只吃 169 类记法：`PYTHONPATH=src python -m pokergto range "KsQs" --json` → `error: cannot parse range token 'KsQs'`。想指定"对手只剩 `KsQs` 这一张"必须换成组合级向量，或用 `Range.from_cards`，而不是往 spec 里塞花色。
2. **移除只保证"已列出的组合"是精确的。** 本节每一张表都是把范围逐字写成类清单之后再删组合。对手范围一旦是"我猜他大概有这些"，你算的就不是移除效应而是猜测。
3. **对手的应对不在本仓库里。** "他被阻断之后会多用另一档去防守"属于对手模型。本仓库没有任何东西计算它；要说这句话，只能标 `reference`/UNVERIFIED（路径见下一节）。
4. **平分不是弃牌。** 牌局 1、2 用的是最坏情形：平分算对手跟注、hero 拿回半个底池（`+50`）。把平分算成弃牌会把期望抬高 `平分×50/剩余组合`——牌局 1 的 `AhJh` 会从 +8.93 变成 +19.64（`6×50/28 = 10.71`）。两种模型必须说清用了哪一个。
5. **牌面不足三张同花时同花档为空。** 那时无从"阻断同花"，任何此类论证先回到 `03-04` 的例 4。

## 陷阱 / Common mistakes

1. **把"两个 A、K 阻断"当成"少 5 个 `AKo`"到处用。** 生成表第 2、3 行：可见 `As+Kh` 剩 **7**（删 5），可见 `As+Ks` 剩 **6**（删 6）。
   *代价*：1 个组合。听上去不大，但牌局 2 里 1 个跟注组合就把期望从 `0.00` 推到 `−1.79`；在 `AKo` 只剩 6 个的河牌面上，这 1 个组合是 16.7% 的那一档。
2. **只数阻断牌删掉的坚果，不数它删掉的其它档。** `Ad` 杀对手的 `AdQd`（跟注）同时也杀 5 个 `AJo`（平分）。牌局 1 里 `AhJh` 与 `AdJh` 的期望差 1.42、`AhJh` 与 `AhJd` 差 11.76，全部来自三档被删数量的**净**差。
   *代价*：正负号弄反——按"我阻断坚果所以诈唬更好"选出来的候选（`AhJh`）恰好是三个里最差的那个（+8.93 对 +20.69）。
3. **在类级频率图上做阻断牌推理。** 第 1 条失效场景已经给出命令与错误文本；图层的粒度到"类"为止。
   *代价*：算不出任何差别，因为图上删 `Kd` 和删 `Kh` 都是 `884 → 737.999997`。此时你会以为"阻断牌不影响防守配额"，而真实的配额是 27 个组合里的 18.000000 对 28 个组合里的 18.666667。

## 练习 / Drills

- 手算再用 `Range.with_removed` 核对：`QJs` 在可见 `Qh+Js` 时剩几个？可见 `Qh+Jh` 时呢？可见 `Qd+Jd` 时呢？（提示：包含–排除的第三项。）
- 用例 3 的范围与牌面，把 `AJo` 换成 `AJs`，重算剩余组合与同花档的组合数。哪一列变了？
- 牌局 1 变式：把 hero 换成 `AdJd`（两张方块）。先猜期望，再跑同一段脚本。为什么这一手已经不是诈唬而是坚果？
- 用 `python -m pokergto mdf --pot 10 --bet 5` 与 `--bet 3.3333`，把 37 个组合的对手换成两种尺度下的防守配额，说出各自多少。

## 自测清单 / Self-check

- [ ] 我能说出 `AKo` 在两张同花可见牌后剩 6、在两张异花可见牌后剩 7，并写出 `3+3−0` 与 `3+3−1`。
- [ ] 我能说明同花类上的方向为什么相反（`AKs`：4 → 3 对 4 → 2）。
- [ ] 我会把 MDF 从比例换算成组合数，并对"牌面 + 我的底牌"之后的剩余范围重算配额。
- [ ] 我知道类级频率图看不见花色，删 `Kd` 与删 `Kh` 在它眼里相同（`884 → 737.999997`）。
- [ ] 我能说出本节里哪些说法是对手模型（必须标 UNVERIFIED），以及要走通它需要哪条路径。

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
本节所有组合数与期望都由本仓库现算；没有任何商业求解器输出：

| 内容 | 来源类型 | 位置 |
|---|---|---|
| 例 1 的十行、例 2 的表 | `derived` | `PYTHONPATH=src python -c` 调 `pokergto.notation.parse` + `Range.with_removed`；与 `table.03-05.removal-effect-by-class` 逐位一致 |
| 例 3 的 44 → 37、每类剩余、4 个同花组合 | `derived` | `Range.with_removed(*board)` + `Range.classes()` + `category_of(best_score(...))` |
| 例 4 与牌局的门槛（0.6667、33.3333%） | `derived` | `PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5`；`pokergto.odds#required_fold_frequency` |
| 牌局 1、牌局 2 的所有期望与计数 | `derived` | 正文 Python 片段：`best_score` 逐组合三分（赢/平分/输），`EV = (赢×100 + 平分×50 − 被跟×50)/总数`（最坏情形：平分记为对手跟注） |
| 图上 `884 → 737.999997`、配额 `589.333331 → 491.999998` | `derived` | 对 committed artifact `range.02-03.mdf-floor-vs-half-pot` 的 `weights` 逐组合筛（`Range.from_classes` + `with_removed`） |
| 三份对手范围、hero 候选清单 | `reference` | 本仓库为讲解写死的示例；每一条都能逐项检查；牌局结论只依赖代数与计数 |

<!-- provenance: kind=reference verified=false -->
!!! unverified "未核验 / UNVERIFIED"
    以下说法在本节**没有**出现，因为它们不属于本仓库能力：对手因被阻断而**改变频率**（"他没同花就会多弃几个"）、对手范围的真实构成、以及据此调整诈唬频率的策略结论。要把这类句子变成 `derived`，需要的路径是：先在 `src/pokergto/solver` 里对该河牌面与范围求解（`tools/run_solver.py` 产出带 `solver_run` 的 artifact），再由 `tools/inject_doc_tables.py` 把结果注入 AUTO 块。在此之前，此类句子只能带 UNVERIFIED 标记出现。

## 术语 / Terms

<!-- terms: blocker, removal-effect, range, combos, minimum-defense-frequency, bluff-range, value-range, the-nuts, showdown, capacity, hand-class, board -->

| 缩写 | 中文 | English | 本节里的含义 |
|---|---|---|---|
| — | 阻断牌 | blocker | 一张使某些具体组合不可能存在的可见牌 |
| — | 移除效应 | removal effect | `Range.with_removed`：把含可见牌的组合权重清零 |
| — | 组合数 | combos | 删除的单位；对子 6、同花 4、不同花 12 只是无上界信息时的基线 |
| — | 范围 | range | 1326 维组合向量；类级图是它的一个投影，不含花色信息 |
| — | 手牌类别 | hand class | 169 个格子之一，`parse` 能写到这一层为止 |
| — | 最低防守频率 | minimum defense frequency | `pot/(pot+bet)`；乘剩余组合才是可核对的配额 |
| — | 价值范围 | value range | 逐组合判定"击败 hero"的那部分，牌局里现算而非声称 |
| — | 诈唬范围 | bluff range | 逐组合判定"输给 hero"的那部分 |
| — | 坚果 | the nuts | 两份范围在当前牌面上的最高分档 |
| — | 成牌容量 | capacity | 某一档（如 4 个同花组合）在范围里的组合数 |
| — | 摊牌 | showdown | 五张牌面之后唯一存在的比较；没有胜率可算 |
