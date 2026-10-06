# 自己范围里的移除效应：我的底牌删掉了我的坚果

<!-- hands: 2 -->
<!-- terms: removal-effect, blocker, range, combos, capacity, nut-advantage, hand-class, hole-cards, the-nuts, capped-range, minimum-defense-frequency, showdown -->

## 本节目标 / Objectives

- 能对"我自己的范围"逐类列出基线组合数与条件化后的剩余组合数（牌面 + 我的两张底牌），并说清被删掉的是哪几个具体组合。
- 能说明用真实底牌条件化范围为什么会**同时**改变胜率与坚果计数，并指出改变的方向：删掉自己最强的一档，其余部分的胜率下降；删掉自己最弱的一档，胜率上升。
- 能举出"我的两张牌一次删掉我自己三个坚果组合"这种例子，并解释它为什么删得比 1 个多。
- 能算出条件化之后价值:诈唬的配比能不能落在整数个组合上，并说出这个约束由哪条式子给出。

## 前置知识 / Prerequisites

- `03-05` 把阻断牌读成范围效应：`Range.with_removed` 与包含–排除；本节把同一把刀转向自己。
- `01-07` 读 13×13 网格：一格与一个具体组合不是一回事，`AKs` 的四张里只有一张是 `AdKd`。
- `01-01` 组合与类别：`6 / 4 / 12` 是无信息时的基线，条件化之后不是常数。
- `03-01` 坚果优势：份额是个比，分子和分母都是组合计数。

## 核心原理 / The principle

移除效应不偏袒任何一方。`03-05` 用它删对手的范围，本节用它删**我自己的**范围：我低头看见的两张牌，同时也是我这份范围里最具体的两条约束——它们先删掉我"还能持有别的牌"的那些可能，再改掉我自己每一档的计数。

由此有三件事必须分开算：

1. **范围原样（authored）**：`parse(spec)`，例如 46 个组合。它是"我在这一格里可能持有的所有牌"的清单，里面包含物理上不存在的组合。
2. **条件化范围**：`parse(spec).with_removed(*board, *my_cards)`。这才是"我拿着这一手时，我这份范围的其余部分"。
3. **我这一手本身**：`Range.from_cards(my_cards)`，恰好 1 个组合。

第 2 与第 3 之间的差，就是本节的全部教学内容：同一个动作（对手全下、我该不该跟）在第 3 个对象上算是对的，在第 1 个对象上算会给出相反的答案——这不是舍入问题，本节会给出两个方向的实例。

<!-- provenance: kind=derived verified=true -->
> !!! note "来源 / Provenance"
>     计数与胜率：`pokergto.ranges.Range.with_removed`、`pokergto.equity.range_equity`（精确穷举）、
>     `pokergto.theory.range_advantage`（derived）。范围原样是本仓库写死的示例（`reference`）。

## 推导 / Derivation

### 三个对象，三种分母

设牌面 `B`（3–5 张）、我的底牌 `H = {h1, h2}`、我的范围原样 `R`。

```
R                     分母 = R.total_combos()                     # 含不可能的组合
R.with_removed(*B)    分母 = |R 里不含 B 任一张的组合|              # 只条件化牌面
R.with_removed(*B, *H) 分母 = 上式再删掉含 h1 或 h2 的组合          # "其余的我"
Range.from_cards(H)   分母 = 1                                    # "我这一手"
```

坚果份额 `nut_share = 坚果档组合 / 分母`，所以四个对象给出四个不同的数，**其中没有一个是"四舍五入的误差"**：它们回答的是四个不同的问题。`advantage()` 走第二个（内部先 `with_removed(*board)`，`hero_combos` 因此报 33 而不是 46）；`is_capped()` 与 `nut_advantage()` 都拒绝第一个（收到没条件化的范围就抛 `InputError`）；第三个和第四个必须由我自己传。

### 为什么一次删掉的不止一个组合

`H` 的两张牌各自命中若干组合，删掉的是它们的**并集**：

```
deleted = {组合 ∈ R : 组合 ∩ {h1, h2} ≠ ∅}
        = |含 h1 的| + |含 h2 的| − |同时含 h1 与 h2 的|
```

关键在于"含 `h1` 的"跨越了**多个类**。我的 `Ad` 不只出现在 `AKs` 那一格：`AdKd`、`AdQd`、`AdJd`、`Ad5d`…… 只要范围里写了某个类、而它有一个组合含 `Ad`，那个组合就一起消失。所以"我拿着两张牌"删掉自己范围的组合数可以远大于 1。

同一条式子给出方向：**如果你拿的是坚果，你的范围就没有坚果。** 坚果档常常只有一个组合（单色牌面上的最大同花），删掉 1 个之后分子是 0，份额从 `1/n` 变成 `0/(n-3)`；同时对手的坚果档从 0 变成 `1/m`，坚果优势整体翻到对面去。

### 配比能不能落在整数上

`02-04` 的无差别条件是"价值:诈唬 = 一个由尺度决定的比"（半池 3:1、底池 2:1，见 `python -m pokergto odds --pot 12`）。把它写成组合数：

```
需要的诈唬组合 = 价值组合 / (value_to_bluff)
```

`value_to_bluff` 是分数的比，而组合数是整数，所以**大部分价值组合数在任何尺度下都配不出整数个诈唬**。条件化改变"价值组合数"这个输入，于是"哪个尺度在这里可执行"这个问题也跟着改。这是移除效应打进我自己范围的第二条路：不是改变我强不强，而是改变我**能不能把计划写成具体的牌**。

## 直觉 / Intuition

牌桌上你唯一确定知道的两张牌是自己的，但教练话里的"我的范围"通常是那张没条件化的清单。于是有一个可以随身携带的说法：

**"我的范围"在我看牌之前是 46 个组合，在我看牌之后是"46 减去我手上这一对的可能"，而"我这一手"永远是 1 个。** 三者都真，但只有第二个和第三个能用来做决定：第二个决定"我这条线还剩什么可以吓唬人"，第三个决定"我这手牌该怎么做"。

三句可迁移的话：

1. **拿着坚果，你的范围就没有坚果。** 你的这一手是整个范围里唯一的那张，你把它从"我的范围"里删掉之后，范围里剩下的是能被大注抓的东西。
2. **删掉弱的那手反而让范围变强。** 拿着 `AhKh`（没同花、没顺子、只有高牌）时，我其余部分的胜率**上升**——因为被删掉的正是拖后腿的组合。方向取决于你删的是哪一档，不是"条件化"这个动作本身。
3. **一张牌同时打穿好几格。** 我的 `Ad` 在 `AKs`、`AQs`、`ATs`、`A2s` 里都有对应组合，所以一次低头看牌，改动的是清单上的多行。

## 算例 / Worked examples

### 例 1 — 基线 vs 剩余，逐类列出来

牌面：单色翻牌 `Td 9d 5d`。我的范围原样 `R = AKs,AQs,KQs,ATs,KTs,QTs,JTs,TT,99,55`（`python -c` 里 `parse(R).total_combos()` = **46**）。三张牌面先做移除（`parse(R).with_removed(*board)` = **33**），然后按我实际拿的牌再删：

| 类 | 基线（原样） | 牌面移除后 | 我拿 `AdKd` | 我拿 `AhKh` | 我拿 `AdKh` |
|---|---|---|---|---|---|
| `AKs` | 4 | 4 | **3**（少 `AdKd`） | **3**（少 `AhKh`） | **2**（少 `AdKd`、`AhKh`） |
| `AQs` | 4 | 4 | **3**（少 `AdQd`） | **3**（少 `AhQh`） | **3**（少 `AdQd`） |
| `KQs` | 4 | 4 | **3**（少 `KdQd`） | **3**（少 `KhQh`） | **3**（少 `KhQh`） |
| `ATs` | 4 | 3 | 3 | **2**（少 `AhTh`） | 3 |
| `KTs` | 4 | 3 | 3 | **2**（少 `KhTh`） | **2**（少 `KhTh`） |
| `QTs` | 4 | 3 | 3 | 3 | 3 |
| `JTs` | 4 | 3 | 3 | 3 | 3 |
| `TT` | 6 | 3 | 3 | 3 | 3 |
| `99` | 6 | 3 | 3 | 3 | 3 |
| `55` | 6 | 3 | 3 | 3 | 3 |
| **合计** | **46** | **33** | **30** | **28** | **28** |

三行读三件事。`AdKd` 那一列删掉 **3** 个组合，分布在 3 个不同的类里（`AdKd`、`AdQd`、`KdQd`）——两张牌一次删掉我自己三个同花，其中包含唯一的那个坚果同花。`AhKh` 那一列删掉 5 个组合，但**一个同花都没删**（红桃两张与方块档无关）。`AdKh` 混合两者：一红一蓝，删 5 个、其中 2 个是同花。`TT/99/55` 三行从 6 掉到 3，是因为牌面已经占了 `Td`、`9d`、`5d`——这就是"基线 6"不是常数的地方（`01-01` 的 `6 / 4 / 12` 是无信息时的上界）。

复现：

```bash
PYTHONPATH=src python -c "
from pokergto.cards import parse_cards, Card
from pokergto.notation import parse
R='AKs,AQs,KQs,ATs,KTs,QTs,JTs,TT,99,55'; b=parse_cards('Td9d5d')
full=parse(R); bc=full.with_removed(*b)
print(full.total_combos(), bc.total_combos())
for mine in ('AdKd','AhKh','AdKh'):
    h=[Card.parse(mine[:2]),Card.parse(mine[2:])]
    r=bc.with_removed(*h)
    print(mine, r.total_combos(), {k:round(v,1) for k,v in sorted(r.classes().items())})
"
```

### 例 2 — 条件化怎么改胜率：同一个范围，三个对象

对同一副对手范围 `V = KJs,QJs,T9s,98s,87s,66,65s,A2s`（34 个原样组合 / 牌面移除后 31 个），`advantage` 与 `equity` 给：

| 对象 | 组合（分母） | hero 胜率 | hero 坚果份额 | villain 坚果份额 | 封顶？ |
|---|---|---|---|---|---|
| 原样范围 `parse(R)`（`advantage` 内部先做牌面移除） | 33 / 31 | 0.603938 | 0.030303（1/33） | 0.000000 | 否（`is_capped` = False） |
| 其余的我：`R − AdKd` | 30 / 31 | 0.568338 | **0.000000** | **0.032258**（1/31） | **是**（True） |
| 其余的我：`R − AhKh` | 28 / 31 | **0.634024** | 0.035714（1/28） | 0.000000 | 否 |
| 其余的我：`R − AdKh` | 28 / 31 | 0.596833 | 0.000000 | 0.032258 | 是 |
| 我这一手 `AdKd` | 1 / 31 | 0.965587 | — | — | — |
| 我这一手 `AhKh` | 1 / 31 | 0.317659 | — | — | — |

方向是清楚的：删掉坚果（`AdKd`）让我的**其余部分**从 0.603938 掉到 0.568338（−3.56 个百分点），并且把坚果档整个交给对手——我的份额从 `1/33` 归零，对手从 0 升到 `1/31`，我的 `is_capped` 由否变**是**。删掉一个拖累的组合（`AhKh`）则相反：其余部分升到 0.634024（+3.01 个百分点），坚果档还在自己手里。而"我这一手"的胜率是另一个数量级的信息：`AdKd` 96.5587%、`AhKh` 31.7659%——**范围的那个 0.603938 对这两手都不成立。**

```bash
PYTHONPATH=src python -m pokergto equity "AdKd" "KJs,QJs,T9s,98s,87s,66,65s,A2s" --board "Td9d5d" --mode exact --json
PYTHONPATH=src python -m pokergto equity "AhKh" "KJs,QJs,T9s,98s,87s,66,65s,A2s" --board "Td9d5d" --mode exact --json
```

两条命令都是 `exact: true, iterations: 1176`（穷举 `C(47,2) = 1176` 张转牌+河牌的组合，无抽样误差）。

### 例 3 — 一次低头看牌改掉 5 个数

固定 `R`、`V`、`board`，把 `H` 从 `AdKd` 换成 `AhKh`，逐个看本节用到的量：

| 量 | `H = AdKd` | `H = AhKh` | 差 |
|---|---|---|---|
| 我其余部分的组合数 | 30 | 28 | 2 |
| 我删掉的自己组合数 | 3 | 5 | −2 |
| 我删掉的坚果组合数 | 1（`AdKd` 本身）+2 个别的同花 | 0 | — |
| 其余部分的胜率 | 0.568338 | 0.634024 | −0.065686 |
| 其余部分的坚果份额 | 0.000000 | 0.035714 | — |
| `is_capped`（其余部分） | True | False | 翻转 |
| 我这一手的胜率 | 0.965587 | 0.317659 | +0.647928 |

同一张牌面、同一副对手范围、同一个"我在 CO"的身份，七个数全变了。变的原因只有一个：条件化选了不同的组合被删。

### 例 4 — 价值档是"类"还是"组合"：本节最容易算错的一处

我的下注范围写成 `AKs,AQs,KQs,JTs,87s,ATs,KTs`（`python -m pokergto range "AKs,AQs,KQs,JTs,87s,ATs,KTs" --json` → **28 个组合 / 7 个类**）。在单色翻牌 `Td9d5d` 上，"坚果档"= 最大同花。逐组合筛（`category_of(best_score(...)) == Category.FLUSH`）：牌面移除后 25 个组合里，同花只有 **4** 个：`AdKd`、`AdQd`、`KdQd`、`7d8d`。

| 我拿的牌 | 我删掉的自己组合 | 剩余总组合 | 剩余同花（价值档） | 半池需要的诈唬组合 `价值/3` | 1 倍底池需要的 `价值/2` |
|---|---|---|---|---|---|
| 无条件化 | — | 25 | 4 | 1.3333 | 2.0000 |
| `AhKh` | 5 | 20 | 4 | 1.3333 | 2.0000 |
| `JsTh` | 4 | 21 | 4 | 1.3333 | 2.0000 |
| `QdJd` | 2 | 23 | **2**（`AdKd`、`7d8d`） | 0.6667 | 1.0000 |
| `AdKd` | **3** | 22 | **1**（`7d8d`） | 0.3333 | 0.5000 |
| `KdQd` | **3** | 22 | **1**（`7d8d`） | 0.3333 | 0.5000 |

表里有两个反直觉的点。第一，`AdKd` 只**是**一个坚果，但它删掉**三个**同花组合（`AdKd`、`AdQd`、`KdQd`）——因为我的 `Ad` 和 `Kd` 分别还出现在别的格子里。第二，`AhKh` 删掉 5 个组合却不删任何同花：那 5 个是红桃对，与方块档无关。所以"我拿着某一类里的牌"不等于"那一类的计数减 1"。

## 生成表 / Generated tables

第一张表给出本节反复使用的基线：`6 / 4 / 12`。它是**没有可见牌时**的每类组合数；例 1 那张表每一行都是它被减过之后的样子（`TT` 从 6 掉到 3，`AKs` 从 4 掉到 2）。

<!-- BEGIN AUTO:table.01-01.combo-decomposition -->
|    形态 | 类数 | 每类组合数 |      总组合数 |
|---:|---:|---:|---:|
|   pairs |   13 |          6 |  78.00 combos |
|  suited |   78 |          4 | 312.00 combos |
| offsuit |   78 |         12 | 936.00 combos |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.cards#combos_for_class`

<!-- generated by: tools/gen_tables.py from pokergto.cards::combos_for_class -->
<!-- END AUTO:table.01-01.combo-decomposition -->

第二张表是 `03-02` 的封顶检查，这里借来是因为它的 `Combos` 列正是本节反复要审的那个量：那一列已经是**条件化之后**的组合数（`Kh7s3d` 上 hero 44、villain 58），而同样的 spec 字符串递给 `parse(spec).total_combos()` 给的是原样的 52 与 64。四个数都算得出来，本节要的永远是前者：`is_capped`、`nut_advantage` 现在都会拒绝未收窄的范围（错误文本见下），三行判定也确实是拿收窄后的范围复现的（hero 在 `Kh7s3d` 封顶、在 `AsKsQh` 不封顶；villain 在两处都封顶）。直接把没收窄的范围递进去，引擎会拒绝：

```
error: is_capped: range 0 still holds 7c7s, a card on the board. Narrow it with
Range.with_removed(*board) or notation.parse(spec, exclude=board); nut shares and combo
counts divide by what the range contains.
```

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

### 牌局 1（`hand.03-06-nut-flush-is-my-own-hand`）— 同一条线，三个对象给出三种答案

6 人桌现金局。CO 开池 2.5x，BB 跟注。翻牌 `Td 9d 5d`（单色），底池 12，有效筹码 24。BB 全下 24。hero 在 CO 要么跟 24 赢 36。

门槛：`PYTHONPATH=src python -m pokergto spr --stack 24 --pot 12` → SPR 2.000，全下所需胜率 `SPR/(1+2·SPR)` = **0.4000**；同一条结果也出现在 `python -m pokergto odds --pot 12` 的 2x pot 那一行（MDF 33.33%、跟注所需胜率 40.00%）。

三个对象给三个答案：

| 拿来算胜率的对象 | 胜率 | 期望（`胜率 × 60 − 24`） | 决定 | 与"范围那一行"的差 |
|---|---|---|---|---|
| 我的范围原样（46 → 条件化 33） | 0.603938 | **+12.2363** | 跟 | — |
| 我拿着 `AdKd`，我这一手 | 0.965587 | **+33.9352** | 跟 | +21.70 |
| 我拿着 `AhKh`，我这一手 | 0.317659 | **−4.9404** | 弃 | −17.18 |
| 我拿着 `AdKh`，我这一手 | 0.577377 | +10.6426 | 跟 | −1.59 |

`AhKh` 那一行是本节的存在理由：**用范围的平均数做决定，会在一手只有 31.7659% 胜率的牌上多付 24 个筹码**——两个答案差 `+12.2363 − (−4.9404) = 17.18` 个筹码/次，全部来自"平均"这个词。

还有一层：当我拿的正是 `AdKd` 时，我的**其余**范围（30 个组合）坚果份额归零、`is_capped` 翻成 True、胜率掉到 0.568338。也就是说，我的坚果被我自己拿走了之后，这条线上"我"只剩下能被 24 个筹码逼弃牌的东西——下一手该由 `AhKh` 那一类去跟，而不是让整条线按 `AdKd` 的标准来打。

复现（胜率、份额、封顶三处都要条件化）：

```bash
PYTHONPATH=src python -m pokergto equity "AhKh" "KJs,QJs,T9s,98s,87s,66,65s,A2s" --board "Td9d5d" --mode exact --json
PYTHONPATH=src python -c "
from pokergto.cards import parse_cards, Card
from pokergto.notation import parse
from pokergto.ranges import Range
from pokergto.theory.range_advantage import advantage, is_capped
b=parse_cards('Td9d5d'); H='AKs,AQs,KQs,ATs,KTs,QTs,JTs,TT,99,55'
V=parse('KJs,QJs,T9s,98s,87s,66,65s,A2s').with_removed(*b)
for mine in ('AdKd','AhKh','AdKh'):
    h=[Card.parse(mine[:2]),Card.parse(mine[2:])]
    a=advantage(parse(H).with_removed(*b,*h), V, b, mode='exact')
    s=advantage(Range.from_cards(h), V, b, mode='exact')
    print(mine, round(a.hero_combos,1), '%.6f'%a.hero_equity, '%.6f'%a.hero_nut_share,
          '%.6f'%a.villain_nut_share, is_capped(parse(H).with_removed(*b,*h), b), '%.6f'%s.hero_equity)
"
```

### 牌局 2（`hand.03-06-value-bucket-three-combos`）— 我的两张牌决定哪个尺度还能写成整手

还是 `Td 9d 5d`，底池 12。hero（CO）打算用"同花档"作价值、其余作诈唬，下一个半池（6 进 12）。`python -m pokergto odds --pot 12` 给出 1/2 pot 的价值:诈唬 = **3 : 1**，1 倍底池 = **2 : 1**。价值档按例 4 的逐组合筛法（`AKs,AQs,KQs,JTs,87s,ATs,KTs` 牌面移除后 25 个组合，同花 4 个）：

| 我拿的牌 | 价值档（同花组合） | 半池需要的诈唬组合 | 是不是整数 | 1 倍底池需要的诈唬组合 | 是不是整数 |
|---|---|---|---|---|---|
| `AhKh` | 4 | 1.3333 | 否 | 2.0000 | **是** |
| `QdJd` | 2 | 0.6667 | 否 | 1.0000 | **是** |
| `AdKd` | 1 | 0.3333 | 否 | 0.5000 | 否 |

于是决定是具体的：拿着 `AhKh` 时，半池那个"3:1"在我的范围里**配不出整手牌**（需要 1.3333 个诈唬组合），能配出来的是 1 倍底池那档（正好 2 个）。换成 `QdJd` 也同样落在 1 倍底池（正好 1 个）。拿着 `AdKd` 时两档都配不出——价值档只剩 1 个组合，任何尺度都要求分数个诈唬。

错配的代价能算。把对手那侧当成"一手只赢诈唬、输给全部价值的抓诈唬牌"（跟 6 进 `12 + 6 = 18` 的底池：赢拿 18，输付 6），期望是 `(诈唬 × 18 − 价值 × 6) / 总数`：

| 实际端出去的比例 | 对手抓诈唬牌跟注的期望 | 读法 |
|---|---|---|
| 价值 4 : 诈唬 1（欠诈唬） | **−1.2000** | 对手该弃掉全部抓诈唬牌 → 我的价值下注一个跟注都拿不到 |
| 价值 3 : 诈唬 1（半池的平衡比） | **0.0000** | 无差别点，正是 `odds` 里 3:1 那一行的含义 |
| 价值 4 : 诈唬 2（超诈唬） | +2.0000 | 对手任意两张牌跟注，每次赚 2.00 |
| 价值 1 : 诈唬 1（我拿着 `AdKd`，却仍按"4 个同花"的清单配 1 个诈唬） | **+6.0000** | 对手跟注赚 6.00 —— 这是"没做移除"的直接价钱 |

最后一行是本节要说的事：价值档从 4 变成 1，是因为我自己的两张牌删掉了三个同花组合。如果我照原样清单去端牌，实际进池的比例就成了 1:1，对手随便一张抓诈唬牌都能赚 6.00，而我以为自己在打 3:1。条件化不是为了算得漂亮，是为了别把自己写的计划执行成另一个。

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

这张来自 `04-02` 的图是"面对 1/3 底池时必须防守的那部分范围"：`total_combos = 994.5`（`1326 × 3/4`，`range_percentage = 75.0%`），128 个非空格子。它在本节的用法是当**反例**——一张按类填的图，看不见我自己的底牌：

1. 图上的格子是频率，不是具体组合。它无法表达"我这手是 `AKs` 四张里的 `AdKd`"这件事：那需要落到组合级，也就是例 1 那张表。
2. 防守配额本身会被条件化改掉。把这张图的 994.5 个组合（`threshold = 0.75`，配额 `994.5 × 0.75 = 745.875`）先按牌面 `Td 9d 5d` 筛，剩 **868.5** 个组合、配额 **651.375**；再删掉我的两张牌，剩 **781.5** 个。注意最后一步：无论我拿的是 `AdKd` 还是 `AhKh`，这张图给的都是 781.5——**类级图看不见花色**，所以它永远画不出例 1 那张表里"3 个 vs 5 个"的区别。同一张图、三个数（994.5 / 868.5 / 781.5），差别全部来自"可见牌"这一件事，而它最要紧的那一半恰好是图表达不出来的那一半。
3. 图不含任何"对手会因此改频率"的信息。本节所有关于对手的说法都只是我写下的那份范围（`reference`），任何"他因为被阻断而调整"的句子都必须带 UNVERIFIED 标记（见下一节）。

## 为何成立、何时失效 / Why it works, when it breaks

**为什么成立。** 三件事都只用到"组合是两张具体的牌"这一条：`with_removed` 清零含可见牌的组合；包含–排除给出删掉的个数；坚果份额是除法，所以分子分母都得是条件化后的计数。没有一处用到牌力、对手或尺度。

**什么时候不能这样用：**

1. **单色牌面上的同花档很脆。** 例 4 里"价值档"是 4 个具体组合中的 1 个。把范围写成 `AKs` 就以为有 4 个价值组合，是本节第 2 号错误——同一格里四张牌只有 `AdKd` 是同花。
2. **记法到"类"为止。** `parse` 不接受 `KsQs`（`error: cannot parse range token 'KsQs'`）。想做"只剩这一张"必须用 `Range.from_cards` 或组合级权重。另外本节实测：`python -m pokergto range "AKs,AQs,KQs,ATs,KTs,QTs,JTs,TT,99,55" --json` 会抛 `error: strict round-trip failed: 'TT-55' re-parses to a different range (differing classes: ['66','77','88'] ...)`——不连续的多个对子在 `to_spec()` 被渲染成一段 run，重新解析时会多出中间的对子。这是记法层的一个缺陷，本节因此一律用 `python -c` + `total_combos()` 给数，而不是那条命令。
3. **`range_equity` 拒绝五张牌面。** 河牌之后没有胜率，只有摊牌：`error: a board of five cards has no equity left to compute`。条件化到河牌时，改用 `best_score` 逐组合比较（`03-05` 的两个牌局就是这么算的）。
4. **精确穷举有预算。** 例 2 的两次单手感各 1176 个 runout、`mode="exact"` 无误差；把对手换成真实的大范围（几百组合）就会撞 `BudgetExceeded`，那时只能 `--mode mc` 并带上误差条（`01-04`）。
5. **我的两张牌删的是"我的可能"，不是"他的可能"。** 同一张 `Ad` 在对手范围里删的是另一批组合（`03-05`）。两侧要分开算，然后才能放进同一个期望式；本节所有单侧数字都注明了对象是哪一份范围。

## 陷阱 / Common mistakes

1. **用范围的平均胜率给某一手做决定。** 牌局 1：范围给 0.603938（期望 +12.2363），而我拿 `AhKh` 时这一手只有 0.317659（期望 **−4.9404**）。
   *代价*：17.18 个筹码/次，而且方向是反的——平均说"跟"，这手该"弃"。凡是"我这手该怎么做"的问题，主语必须是 `Range.from_cards`，或者干脆用 `equity "AhKh" ...` 那条命令。
2. **以为"我拿着某一类，那一类就少 1 个"。** 例 1：`AdKd` 一次删掉 **3** 个组合，跨 `AKs`、`AQs`、`KQs` 三格；`AhKh` 删 5 个。例 4 的 4 个同花里，拿 `KdQd` 也是删 3 个。
   *代价*：牌局 2 里价值档从 4 被当成 3（或反过来），半池的 3:1 配比就算不出、或者算出一个假整数——`4/3 = 1.3333` 配不出整手，而 `3/3 = 1` 看起来"正好"。真实数字要逐类相减。
3. **拿没条件化的范围去碰 `is_capped` 或 `nut_advantage`。** 两个都会拒绝：`is_capped: range 0 still holds 7c7s, a card on the board.`、`nut_advantage: range 0 still holds TsAs, a card on the board.`，并要求 `Range.with_removed(*board)` 或 `notation.parse(spec, exclude=board)`。这不是刁难：`table.03-02.capped-range-check` 的 `Combos` 列（44、58）与 `parse(spec).total_combos()`（52、64）是两个不同的问题，只有一个能当份额的分母。
   *代价*：份额被系统性低估。例 2 里 `1/33 = 0.030303` 与 `1/46 = 0.021739` 相差 39.4%（46/33 − 1）——同一手牌、同一个牌面，两个都"算得出"，只有一个能当份额的分母（`advantage` 报出的 `hero_combos` 是 33 那一侧）。

## 练习 / Drills

- 用例 1 的脚本换成 `H = AKo,AQs,KQs,TT`、我的牌 `AdQd`，逐类列出基线 / 牌面后 / 底牌后。哪一列在 `AKo` 上动了，动了几个？
- 牌局 1 变式：BB 全下的尺度从 24 改成 12（1 倍底池）。用 `python -m pokergto odds --pot 12` 读门槛（33.33%），再用 `equity` 给的四手感重算四种决定。
- 例 4 变式：把牌面换成 `Td 9d 5d 2d`（四张方块）。先猜价值档变成多少，再跑逐组合筛选。为什么它不一定变大？
- 自己验一遍包含–排除：`R = ATs,A2s`，我拿 `Ad2d`。我删掉自己几个组合？写出它们的牌面记号。

## 自测清单 / Self-check

- [ ] 我能区分四个对象：原样范围、牌面条件化范围、"牌面 + 我"条件化范围、我这一手（1 个组合），并说清每个的分母。
- [ ] 我能举一个"两张牌删掉三个自己的同花组合"的例子（`Td9d5d` 上拿 `AdKd`）。
- [ ] 我知道条件化能改方向：删坚果 → 其余部分胜率降、坚果份额归零、`is_capped` 可能翻真；删弱手 → 胜率升。
- [ ] 我能算出条件化之后 `价值/3`、`价值/2` 是不是整数，并说出这决定了哪些尺度"可执行"。
- [ ] 我知道 `is_capped` 与 `nut_advantage` 都会拒绝未条件化的范围，而 `parse(spec).total_combos()` 仍然给得出原样分母——它是另一个问题的分母，不是份额的分母。

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
本节全部数字来自本仓库现算；没有任何商业求解器输出或付费课程内容：

| 内容 | 来源类型 | 位置 |
|---|---|---|
| 例 1 的 46 / 33 / 30 / 28 / 28 与逐类表 | `derived` | `python -c` 调 `pokergto.notation.parse` + `Range.with_removed` + `Range.classes()`；命令在例 1 |
| 例 2 的胜率 0.603938 / 0.568338 / 0.634024 / 0.596833 | `derived` | `advantage(parse(R).with_removed(*board, *H), V.with_removed(*board), board, mode="exact")`（精确穷举，1176 runouts） |
| 例 2 的坚果份额 0.030303 / 0.000000 / 0.035714 / 0.032258 与 `is_capped` 翻转 | `derived` | 同上调用返回的 `hero_nut_share` / `villain_nut_share`，加上 `pokergto.theory.range_advantage#is_capped` |
| 例 2、牌局 1 的单手感 0.965587 / 0.317659 / 0.577377 | `derived` | `PYTHONPATH=src python -m pokergto equity "AdKd" "KJs,QJs,T9s,98s,87s,66,65s,A2s" --board "Td9d5d" --mode exact --json`（另两手指名 `AhKh`、`AdKh`，同一条命令） |
| 牌局 1 的门槛 SPR 2.000 / 0.4000 / 2x pot 那一行 | `derived` | `python -m pokergto spr --stack 24 --pot 12`；`python -m pokergto odds --pot 12` |
| 牌局 1、2 的期望 +12.2363 / +33.9352 / −4.9404 / +10.6426、`(胜率 × 60 − 24)` | `derived` | 上面两行的胜率 × 门槛式子；抓诈唬期望 `(诈唬×18 − 价值×6)/总数` |
| 例 4 与牌局 2 的同花档（4 / 2 / 1 个）与 28 / 25 的组合数 | `derived` | `best_score` + `category_of == Category.FLUSH` 逐组合筛；`python -m pokergto range "AKs,AQs,KQs,JTs,87s,ATs,KTs" --json` → 28 combos / 7 classes |
| 图上 `994.5`（75.0%）与条件化后 `853.5` | `derived` | 对 committed artifact `range.04-02.mdf-floor-vs-third-pot` 的 `weights` 逐组合筛 + `with_removed(*board)` |
| 所有范围（hero / villain 的 spec 字符串）与我的底牌选择 | `reference` | 本仓库为讲解写死的示例；判定只依赖代数与计数 |

<!-- provenance: kind=reference verified=false -->
!!! unverified "未核验 / UNVERIFIED"
    "对手会因为你的范围被条件化而改变频率"、"真实玩家的 CO 单色面频率"、"他知道你拿着 `AdKd` 所以少跟"：这些都是对手模型，本仓库没有任何代码计算它们。要变成 `derived`，路径是先在 `src/pokergto/solver` 里解这个 spot（牌面、两份范围、尺度集都要写死），再由 `tools/run_solver.py` 产出带 `solver_run` 的 artifact，最后由 `tools/inject_doc_tables.py` 注入 AUTO 块。在那之前，这类句子只能以 UNVERIFIED 出现，且不能带数字。

## 术语 / Terms

<!-- terms: removal-effect, blocker, range, combos, capacity, nut-advantage, hand-class, hole-cards, the-nuts, capped-range, minimum-defense-frequency, showdown -->

| 缩写 | 中文 | English | 本节里的含义 |
|---|---|---|---|
| — | 移除效应 | removal effect | 同一个算子两次作用：一次在对手范围（`03-05`），一次在我自己范围（本节） |
| — | 阻断牌 | blocker | 我自己的两张牌，是我这份范围最硬的两条约束 |
| — | 底牌 | hole cards | 1 个具体组合；`Range.from_cards` 是唯一诚实的表示 |
| — | 范围 | range | 1326 维向量；"我的范围"在条件化前后是两个不同的对象 |
| — | 手牌类别 | hand class | 一格 4 / 6 / 12 个组合，格数不等于组合数 |
| — | 组合数 | combos | 本节所有表格的单位；基线是 6/4/12，条件化后不是常数 |
| — | 成牌容量 | capacity | 某一档（4 个同花）在我范围内的组合数 |
| — | 坚果优势 | nut advantage | 份额之差；我拿走坚果之后，它翻到对手那侧 |
| — | 坚果 | the nuts | 当前牌面上两份范围都能达到的最高分 |
| — | 封顶范围 | capped range | 拿不到上限的那一侧，`is_capped` 要求先做移除 |
| — | 最低防守频率 | minimum defense frequency | 乘剩余组合才是配额；配额随条件化变化 |
| — | 摊牌 | showdown | 河牌之后唯一存在的比较 |
