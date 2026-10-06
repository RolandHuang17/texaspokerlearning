# 牌面质地分类：单色、双色、成对与连张各自偏向谁

<!-- hands: 2 -->
<!-- terms: board-texture, monochrome-board, two-tone-board, rainbow-board, paired-board, connected-board, static-board, dynamic-board, wet-board, dry-board, broadway-board, backdoor-draw, flush-draw, range-advantage, equity-advantage, nut-advantage, capacity, range, combos -->

## 本节目标 / Objectives

- 能用 `pokergto.board.classify` 给任意 3–5 张的牌面打出组合 id（例如 `dynamic.two-tone.connected`），并说出每一个词由哪一条谓词决定。
- 能对同一副示例范围，在质地不同的牌面上跑出 `advantage` 的三个数：胜率优势、坚果优势、以及"谁能常下注 / 谁能下大注"。
- 能用数字说明"分类"与"测量"的差别：本课会算出两个标签相反（`dynamic` 与 `static`）、但优势只差 0.40 个百分点的牌面对。
- 能指出引擎的分类与口头惯例不一致的两处——`Kh7s3d` 被判为 dynamic、成对牌面上"至少一对"的比例恒为 100%——并解释规则为什么会这样判。

## 前置知识 / Prerequisites

- `03-01` 胜率优势与坚果优势：两个数各自回答什么问题，为什么不能合并成一个结论。
- `01-07` 读 13×13 网格：一格是 4、6 还是 12 个组合。
- `01-01` 组合与类别：`6 / 4 / 12` 与 1326。
- `01-03` 穷举胜率：补牌数换成概率的那张表，本课在算例 4 里直接引用。

## 核心原理 / The principle

质地（board texture）是一套**分类规则**，范围优势是一次**测量**。两者不是同一件事，也不能互相代用。

本仓库把分类写成三条轴上的谓词，全部在 `pokergto.board`：花色结构（`monochrome` / `two-tone` / `rainbow`）、点数结构（`paired` / `connected` / `broadway` / `low` / `max_gap`）、以及由前两条合成的 `dynamic` / `static`。每一条都能对一个具体牌面跑出真或假。

"这种牌面偏向谁"没有谓词。它只能由 `pokergto.theory.range_advantage.advantage(hero, villain, board)` 在**一个具体牌面 + 两份具体范围**上算出来，返回胜率优势、坚果份额，以及 `who_can_bet_often` / `who_can_bet_big` 两个分开的结论。

所以本课的句式是固定的：**分类给名字，`advantage` 给数字。** 一句不带牌面也不带范围的"这种面偏向加注方"，在本教材里不允许出现。

<!-- provenance: kind=derived verified=true -->
> !!! note "来源 / Provenance"
>     分类谓词：`pokergto.board#classify`（derived）。优势数字：`pokergto.theory.range_advantage#advantage`（derived，精确穷举）。
>     两处 `hero` / `villain` 范围是本仓库为讲解设定的示例（`reference`），不是任何求解器的输出，也不是任何人的实战范围。

## 推导 / Derivation

### 三条轴，七条谓词

设牌面为 `board`，`values` 是牌面上去重后的点数序列，`suits` 是花色集合。引擎的规则逐条写成可检查的形式：

```
monochrome  = len({suit}) == 1
two_tone    = len({suit}) == 2
rainbow     = len({suit}) >= 3
paired      = len({rank}) < len(board)
connected   = values 里存在相邻两点差 1（并把 A-2-3 视为连着，即 wheel）
max_gap     = max(相邻不同点数之差)，单点数牌面记 0
flush_draw  = 某个花色在牌面出现 >= 2 次
straight_draw = 存在一个宽度为 5 的点数窗口，窗口内含牌面点数 >= 2（A 同时按 14 与 1 参与）
dynamic     = connected or (flush_draw and not monochrome) or straight_draw
```

`class_id` 按固定顺序拼出来：先 `dynamic`/`static`，再花色结构，然后才是 `paired`、`connected`、`broadway`、`low`。拼串是稳定的，所以一张表能给同一个牌面打上同一个标签。

三条花色轴互斥且穷尽（5 张牌的牌面，`len({suit})` 只能是 1、2、3、4，而 `rainbow` 收下了 3 和 4），点数轴互相独立：`Kh7s7d` 同时是 `paired` 且 `rainbow`。

### 为什么 `dynamic` 几乎总是真

`straight_draw` 只要求牌面里**有两个点数落在同一个 5 张窗口内**。`Kh7s3d`：窗口 `[3..7]` 同时含 3 和 7 → 真。于是这张教科书级的"干面"在引擎里是 `dynamic.rainbow`。要拿到 `static`，牌面点数必须两两相距至少 5：`Kd 8h 3s`（差 5、5、10）→ `static.rainbow`；`Kh7s3d`（差 4、6、10）→ `dynamic.rainbow`。差一张牌，标签相反。

这是规则本身的后果，不是 bug：`dynamic` 的定义是"有人拿着听牌"，而 K-7-3 上确实有人拿 8-6、5-6 这类卡张顺。它测的不是"这张面通常被叫做 wet"。

### 数字从哪一条式子来

`advantage` 只做三件事：

```
hero_equity, villain_equity = range_equity(hero, villain, board, mode="exact")   # 全下胜率，和为 1
equity_edge   = hero_equity - villain_equity
nut_share(X)  = X 里牌力等于"两份范围当前最高分"的组合数 / X 的组合数
nut_edge      = hero_nut_share - villain_nut_share
who_can_bet_often = 由 equity_edge 的符号决定；who_can_bet_big = 由 nut_edge 的符号决定
```

分母是本节的关键：坚果份额是一个**比**，所以它的分子和分母都是组合计数。任何删掉分子或分母的东西——牌面、我自己的底牌——都会改这个数。这一条正是 `03-06` 的主题。

还有一个门槛：`range_equity` 拒绝五张牌面（`a board of five cards has no equity left to compute`）。河牌之后没有胜率，只有摊牌；算例与牌局里凡是在河牌上的比较，都用 `pokergto.evaluator.best_score` 逐组合判胜负，而不是算胜率。

## 直觉 / Intuition

把质地标签想成**给箱子贴的标签**，把 `advantage` 想成**秤上的读数**。贴标签不改变重量。本课最该带走的是三个具体的因果：

1. **花色结构改变的是"同花这一类成牌存不存在"。** 牌面上只有两张同花时，任何人手上两张同花也只凑出四张，同花数为 0；牌面有三张同花时，`C(10,2) = 45` 个起手组合当场成花，占 1326 的 3.3937%。这一条会直接改写坚果份额。
2. **成对牌面改变的是每个人的下限。** 牌面自带一对，于是"至少一对"的比例恒为 100%（本课实测：hero 50/50、villain 32/32）。这个数不再携带任何信息，能携带信息的是"三条与葫芦在谁手里"。
3. **连张改变的是顺子是否已经在范围里。** `Kh7s3d4c`（转牌把 3 和 4 连上）之后，示例跟注方范围里出现了 4 个顺子组合；同样的人在同一色的 `Kh7s3d` 上一个顺子都没有。

## 算例 / Worked examples

### 例 1 — 同一副范围、同一组点数，三种花色结构

范围（示例，`reference`）：hero = `AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT`（54 个组合），villain = `KQs,QJs,KJs,JTs,98s,76s,99,55`（36 个组合）。点数都取 A-9-5，只换花色：

```bash
PYTHONPATH=src python -c "
from pokergto.cards import parse_cards
from pokergto.notation import parse
from pokergto.theory.range_advantage import advantage
H='AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT'; V='KQs,QJs,KJs,JTs,98s,76s,99,55'
for b in ('Ah9c5d','As9s5d','As9s5s'):
    a=advantage(parse(H),parse(V),parse_cards(b),mode='exact')
    print(b, '%.6f %+.6f %.6f %.6f %+.6f'%(a.hero_equity,a.equity_edge,a.hero_nut_share,a.villain_nut_share,a.nut_edge))
"
```

| 牌面 | `classify` 给的 id | hero 胜率 | 胜率优势 | 坚果份额 hero / villain | 坚果优势 | 参与计算的组合 |
|---|---|---|---|---|---|---|
| `Ah9c5d` | `dynamic.rainbow` | 0.638385 | +0.276769 | 0.000000 / 0.103448 | −0.103448 | 46 / 29 |
| `As9s5d` | `dynamic.two-tone` | 0.610233 | +0.220466 | 0.000000 / 0.103448 | −0.103448 | 46 / 29 |
| `As9s5s` | `dynamic.monochrome` | 0.569199 | +0.138398 | 0.000000 / 0.034483 | −0.034483 | 46 / 29 |

三行的每一个数——胜率、坚果份额、参与计算的组合数——与 `table.03-01.equity-vs-nut-advantage` 第三行同值（那张表渲染成百分数：61.0233% / 22.0466% / 0.0000% / −10.3448%，组合 46.0 / 29.0），所以这三行是同一条式子的三个取值，不是三个来源。

值得注意的是**分母那一列**：`As9s5d` 上 villain 的坚果份额是 `3/29 = 0.103448`，不是 `6/36 = 0.166667`。分子里 `99` 从 6 个掉到 3 个（牌面上那张 `9s` 让含它的三个组合不可能存在），分母从 36 掉到 29（`98s` 的 `9s8s` 与 `55` 的三个含 `5d` 组合也一起消失）。引擎现在不允许两套分母混着用：把没条件化的范围递给 `nut_advantage` 会被拒绝——

```
error: nut_advantage: range 0 still holds TsAs, a card on the board. Narrow it with
Range.with_removed(*board) or notation.parse(spec, exclude=board); nut shares and combo
counts divide by what the range contains.
```

（`advantage()` 不必你操心：它内部先 `with_removed(*board)` 再取坚果档。）分子和分母同时被条件化，这正是本节所有"份额"能对上 artifact 的原因，也是 `03-06` 整节的入口。

读法：从 rainbow 到 two-tone，hero 的胜率优势掉了 `0.276769 − 0.220466 = 0.056303`，也就是 **5.63 个百分点**；再到 monochrome 又掉 **8.21 个百分点**（0.220466 → 0.138398）。掉的原因是同一件事：第三张同花牌一落地同花就当场成立，而这两副范围里"两张同花"的组合分布极不均——做牌面移除后 villain 29 个组合里 23 个是同花对子（79.3%），hero 46 个里只有 10 个（21.7%）。坚果档也跟着换人：两张牌面上坚果是 `99` 的 3 个三条（3/29 = 0.103448）；三色牌面上坚果是"最大那个同花"，即 villain 的 `KsQs` 一个组合（1/29 = 0.034483）——注意份额反而变小，因为坚果档只数**并列最高分**，不数所有同花（villain 一共有 5 个同花组合，见例 4）。

### 例 2 — 标签相反，数字几乎相同

`PYTHONPATH=src python -c "from pokergto.board import classify, parse_board; print(classify(parse_board('Kh7s3d')).class_id, classify(parse_board('Kd8h3s')).class_id)"` 给出 `dynamic.rainbow` 与 `static.rainbow`。用同一副范围跑优势：

| 牌面 | 引擎标签 | `max_gap` | hero 胜率 | 胜率优势 | 坚果优势 | `who_can_bet_often` / `big` |
|---|---|---|---|---|---|---|
| `Kh7s3d` | dynamic | 6 | 0.638489 | +0.276978 | +0.180000 | hero / hero |
| `Kd8h3s` | static | 5 | 0.640480 | +0.280959 | +0.180000 | hero / hero |

两个标签相反，胜率优势只差 `0.003981`（0.40 个百分点），坚果优势**完全相同**（两侧都是 hero 0.180000 / villain 0.000000，分母 50 / 33）。这一对就是本课的核心反例：**质地标签不是优势的量度**。谁能常下注、谁能下大注，来自范围里装了什么，而不是来自这张面被叫做 wet 还是 dry。

### 例 3 — 成对牌面把坚果交给跟注方

`Kh7s7d`（`static.rainbow.paired`，`max_gap` = 6，`connected` = 假，因为 7 与 K 差 6、两张 7 不算相邻）：hero 胜率 0.621990、胜率优势 +0.243981，但坚果份额是 hero 0.000000 / villain 0.062500，坚果优势 **−0.062500**（分母是牌面移除后的 50 / 32 个组合），于是 `who_can_bet_often = hero`、`who_can_bet_big = villain`。逐组合看：hero 范围里最高的一档是两对 `K 7` 带 A 踢脚，9 个组合（`AKo` 的 12 个里含 `Kh` 的 3 个已被牌面删掉）；villain 最高的一档是三条 7（`6c7c`、`6h7h` 两个组合，`7s`、`7d` 已在牌面上）。牌面成对之后，比两对更高的一档只出现在拿着第 4 张 7 的那一侧。

`is_capped` 对两侧都返回真，这一点要说清楚三件事。第一，牌面可达上限是**四条 7**（拿着 `7c7h` 的人，`ALL_COMBOS` 里合法存在），这两副范围里既没有 `77` 也没有 `KK`，所以两侧都封顶。第二，今天的 `is_capped` 拒绝收到没做移除的范围：直接传原范围会得到 `is_capped: range 0 still holds 7c7s, a card on the board. Narrow it with Range.with_removed(*board) or notation.parse(spec, exclude=board)`——引擎把"分母必须先条件化"写成了硬错误。第三，成对牌面把"我有一对"变成人人都有的下限（下节例 4：hero 50/50、villain 32/32），把真正区分强弱的那一档推到了范围的角落里。

### 例 4 — 同花到底几张牌才算

对同一副范围跑逐组合牌型计数（`best_score` + `category_of`）：

| 牌面 | 牌面同花张数 | hero 同花组合 | villain 同花组合 | hero 至少一对 | villain 至少一对 |
|---|---|---|---|---|---|
| `As9s5d` | 2 张黑桃 | 0 | 0 | 42 / 46 | 9 / 29 |
| `As9s5d2s` | 3 张黑桃 | 1 | 5 | 43 / 46 | 14 / 29 |
| `Kh7s3d` | 0 | 0 | 0 | 30 / 50 | 21 / 33 |
| `Kh7s7d` | 0 | 0 | 0 | 50 / 50 | 32 / 32 |

第一、二行说明花色轴的真正后果：**两张同花的牌面上不存在同花**（手牌两张 + 牌面两张 = 四张），第三张同花牌一落地，villain 立刻多出 5 个同花组合、hero 多出 1 个。全局计数也能算：牌面已有 3 张同花时，剩下 10 张该花色，`C(10,2) = 45` 个起手组合当场成花 = 1326 的 3.3937%；牌面只有 2 张时，`C(11,2) = 55` 个组合拿着"同花听牌"（`backdoor` 都不算，四张不成花）= 1326 的 4.1478%。第三、四行说明点数轴的后果：不连接的三张不同点数牌面上，hero 范围里 50 个组合只有 30 个已经成对；牌面一成对，50 个组合全部"至少一对"。

`table.01-03.draw-probability-exact-vs-rule` 给的是把这些听牌换算成概率的那一步：9 个补牌在转牌河两张之内成的精确概率是 34.9676%，而"4 法则"给 36%，高估 1.0324 个百分点。分类与概率之间没有捷径，两步都得算。

### 例 5 — 连张把成牌类别换掉

`Kh7s3d` 的转牌若落到 `4c`，`classify(parse_board('Kh7s3d4c'))` = `dynamic.rainbow.connected`（3 与 4 相邻）。committed 表里这一行（`table.03-01.equity-vs-nut-advantage` 第四行）给出 hero 胜率 76.9775%、胜率优势 +53.9550%、坚果份额 7.5000%（= `3/40`，分子分母都已经条件化）、组合 40 / 44。换成本课这对范围：转牌 `Kh7s3d4c` 给 hero 胜率 0.644791、胜率优势 +0.289582、坚果优势 +0.180000；转牌 `Kh7s3dQh` 给 0.704721、+0.409442、+0.068182（hero 范围里 `QQ` 的 3 个组合成三条 Q，分母 44）。数字随牌面变，标签只随规则变；而分母随条件化变——它是唯一一个同时挪动分子和分母的东西，`03-06` 整节都在算这笔账。

## 生成表 / Generated tables

第一张是本课所有优势数字的来源。注意 `lesson` 字段写的是 `03-01`：这是本章内部复用，同一张表、同一批范围、同一批数字，不重新发明第五种质地分类。

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

第二张表把"质地改变听牌的价值"这件事变成概率。它按补牌数给出转牌/河牌的精确成牌率与 2/4 法则的偏差：牌面从两张同花变三张同花，多的不是"感觉湿了"，是当场成花的 45 个起手组合；而拿着 9 个补牌的人在两张牌内成的精确概率是 34.9676%，法则给 36%。

<!-- BEGIN AUTO:table.01-03.draw-probability-exact-vs-rule -->
| 补牌数 | 转牌精确 | x2 法则 | 两张精确 | x4 法则 |
|---:|---:|---:|---:|---:|
|      3 |    6.38% |   6.00% |   12.49% |  12.00% |
|      4 |    8.51% |   8.00% |   16.47% |  16.00% |
|      5 |   10.64% |  10.00% |   20.35% |  20.00% |
|      6 |   12.77% |  12.00% |   24.14% |  24.00% |
|      8 |   17.02% |  16.00% |   31.45% |  32.00% |
|      9 |   19.15% |  18.00% |   34.97% |  36.00% |
|     10 |   21.28% |  20.00% |   38.39% |  40.00% |
|     12 |   25.53% |  24.00% |   44.96% |  48.00% |
|     15 |   31.91% |  30.00% |   54.12% |  60.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.equity#draw_probability`

<!-- generated by: tools/gen_tables.py from pokergto.equity::draw_probability -->
<!-- END AUTO:table.01-03.draw-probability-exact-vs-rule -->

## 实战牌局 / Live hands

### 牌局 1（`hand.03-04-monochrome-river-flush-count`）— 花色结构改掉三个数，河牌上没有胜率可算

6 人桌现金局。CO 开池 2.5x，BB 跟注；底池 12。翻牌 `As 9s 5d`，转牌 `2s`（第三张黑桃落地），河牌 `4h`。hero 在 CO 拿着 `AdKc`（一对 A，K 踢脚）。

两份示例范围（hero `AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT`、villain `KQs,QJs,KJs,JTs,98s,76s,99,55`）；villain 那一侧先做牌面移除、再做 hero 两张底牌的移除，剩 27 个组合。hero 下注 6 进底池 12：

- 有三张黑桃的河牌 `As9s5d2s4h`：27 个组合里 **16 个弃牌、11 个跟注**。跟注的 11 个里 5 个是同花（`KsQs`、`KsJs`、`QsJs`、`JsTs`、`7s6s`）、3 个是三条 9、3 个是三条 5。弃牌率 **59.2593%**，这一注的期望 **+4.6667**。
- 换成同点数、但没有第三张同花的 `Ad9c5d2h4s`（四门花色）：**21 个弃牌、6 个跟注**（只剩 3 个三条 9 + 3 个三条 5），弃牌率 **77.7778%**，期望 **+8.0000**。
- 关键点在这里：`PYTHONPATH=src python -c "from pokergto.board import classify, parse_board; print(classify(parse_board('As9s5d2s4h')).class_id, classify(parse_board('Ad9c5d2h4s')).class_id)"` 给的是**同一个标签** `dynamic.rainbow.connected`。因为 `is_rainbow` 的定义是"至少三种花色"，而三黑桃 + 5d + 4h 已经是三种。标签一样，期望差 **3.3333 个筹码/次**。
- 门槛来自同一条代数：`PYTHONPATH=src python -m pokergto mdf --pot 12 --bet 6` → MDF 0.6667，hero 需要 33.3333% 的弃牌率。两种质地都越线，所以决定"下多大、值不值得"的不是标签，是那 5 个只在三同花牌面上存在的组合。

如果先跑胜率而不是数摊牌，引擎会拒绝：`PYTHONPATH=src python -m pokergto equity "AdKc" "KQs,QJs,KJs,JTs,98s,76s,99,55" --board "As9s5d2s4c"` → `error: a board of five cards has no equity left to compute`。河牌之后只剩摊牌，这不是限制而是事实：没有下一张牌，就没有"胜率"这个量。

复现：

```python
from pokergto.cards import parse_cards, Card
from pokergto.notation import parse
from pokergto.evaluator import best_score, describe
board = parse_cards("As9s5d2s4h")          # 换成 Ad9c5d2h4s 即无第三张同花的版本
hero  = [Card.parse("Ad"), Card.parse("Kc")]
hs = best_score(hero, board)
v = parse("KQs,QJs,KJs,JTs,98s,76s,99,55").with_removed(*board, *hero)
fold = sum(w for a, b, w in v if best_score([a, b], board) < hs)
call = sum(w for a, b, w in v if best_score([a, b], board) > hs)
print(v.total_combos(), fold, call, 100 * fold / v.total_combos(),
      (fold * 12 - call * 6) / v.total_combos(), describe(hs, lang="en"))
```

### 牌局 2（`hand.03-04-paired-vs-connected-size`）— 成对与连张改掉的是"能被跟注的组合数"，于是尺度变贵

同一局，另一种发法。BB 的示例范围写成 `KQs,QJs,JTs,T9s,98s,76s,65s,55`（34 个组合）。hero 手里仍是 `AcKd`，底池 12；villain 的组合同样先删牌面、再删 hero 的两张。比较两个河牌面：

| 河牌面 | `classify` | hero 的最好牌 | villain 剩余组合 | 弃牌 | 跟注 | 下 6 需弃牌率 | 下 24 需弃牌率 | 下 6 期望 | 下 24 期望 |
|---|---|---|---|---|---|---|---|---|---|
| `Kh7s7d4c2s` | `dynamic.rainbow.paired` | 两对 `K 7`（A 踢脚） | 30 | 28 | 2 | 33.3333% | 66.6667% | **+10.8000** | +9.6000 |
| `Kh7s3d4c2s` | `dynamic.rainbow.connected` | 一对 K（A 踢脚） | 31 | 27 | 4 | 33.3333% | 66.6667% | +9.6774 | +7.3548 |

两行读的是同一个事实：**尺度越大，需要的弃牌率越高，而牌面不改变对手能跟注的那部分。** 成对面上 villain 只剩 2 个跟注组合（`6c7c`、`6h7h`：牌面已有 `7s7d`，拿着第三张 7 就是三条，大过 hero 的两对 `K 7`），所以从 6 加到 24 少赚 1.2000；连张面上 villain 有 4 个 `65s` 的顺子（7-6-5-4-3），少赚 2.3226。两个面上超池都亏于半池，亏的额度等于"跟注组合数 × 多押的钱 / 总组合数"，与这张面看起来多凶无关。

同一张成对面上跑 `PYTHONPATH=src python -m pokergto mdf --pot 12 --bet 24` → MDF 0.3333：villain 只要防守 30 个组合里的 10.000 个就达到底线，而这份范围里只有 2 个组合压过 hero 的两对。防守不足不是 villain 打错了，是范围里**没有东西可守**——这正是下面那张超池图要说的事。

## 范围图 / Range chart

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

这张图来自 `04-02`，借来说明质地的后果而不是质地的名字：它画的是**面对 2 倍底池超池时，防守方必须覆盖的那 442 个组合**（`1326 × 1/3`，artifact 里 `total_combos = 442.0`、`range_percentage = 33.3333%`、`threshold = 0.33333333`，57 个非空格子）。

三层读法：

1. 半池那一版（`range.02-03.mdf-floor-vs-half-pot`）要 884 个组合，2 倍底池只要 442 个。**尺度把防守义务除以 2**，这就是牌局 2 里"超池把跟注组合数放大"的另一面。
2. 图上这 442 个组合是本仓库按牌力从高到低填出来的一个可行解；MDF 只约束总量，不规定用哪些组合去凑。谁的组合能填进去，取决于牌面：`Kh7s7d` 上 hero 的范围里没有任何三条（例 3），所以那一格里 hero 拿不出"坚果那一档"去支撑超池，这是 `03-02` 的封顶论证，而不是这张图的性质。
3. 图里没有移除。牌面一旦出现某张 A 或 K，对应的格子就少掉相应组合——`03-05` 与 `03-06` 分别处理对手和自己。

## 为何成立、何时失效 / Why it works, when it breaks

**为什么成立。** 分类谓词只用牌面本身的花色与点数，是定义；优势数字只用组合计数与七张评估器，也是定义。两者各自闭合，所以本课的每一行都能重算。

**什么时候不能这样用：**

1. **范围换成真人就不成立。** 本课所有"偏向谁"的主语都是那两份写死的示例范围。真实玩家的翻前范围由位置、尺度、对手决定，本仓库没有这套模型；把上面的数字当成"CO 在双色面上有 0.220466 的优势"是越界。这一类说法必须是 `reference` / 未核验。
2. **坚果份额的分母必须是条件化之后的分母。** `advantage` 内部先 `with_removed(*board)` 再取坚果档；`nut_advantage` 与 `is_capped` 更直接——递进去没收窄的范围会被拒绝：`nut_advantage: range 0 still holds TsAs, a card on the board. Narrow it with Range.with_removed(*board) or notation.parse(spec, exclude=board)`。所以 committed 的 `table.03-01.equity-vs-nut-advantage` 与 `table.03-02.capped-range-check` 里的份额和组合列都是条件化后的（3/29 = 10.3448%、40 / 44、44 / 58），而 `parse(spec).total_combos()` 给的是没窄过的 54 与 52——两个数都真，答的是两个问题，本课在正文里说明用哪一个。
3. **五张牌面没有胜率。** `range_equity` 抛 `a board of five cards has no equity left to compute`。河牌上的比较只能是摊牌计数。
4. **`dynamic` 不是 `wet`。** 引擎没有 `is_wet` 谓词，`wet-board` / `dry-board` 在本教材里只是词条；能跑的只有 `dynamic` / `static`，其定义见推导第一节。用"这张面很 dry"当论据，等于用一个没有实现的谓词当论据。
5. **精确穷举有预算。** 例 1 的三次 `advantage` 各约 1176 × 90 ≈ 10.6 万次评估，`mode="exact"` 跑得动；把范围放宽到真实的开池范围（几百个组合）就会撞上 `BudgetExceeded`，那时只能 `mode="mc"` 并接受误差条（`01-04`）。

## 陷阱 / Common mistakes

1. **把 `dynamic` 读成"这张面很湿，所以要小尺度"。** 本课实测：`Kh7s3d`（`dynamic.rainbow`）与 `Kd8h3s`（`static.rainbow`）在同一副范围上的胜率优势分别是 +0.276978 与 +0.280959，差 **0.40 个百分点**，坚果优势完全相同；反过来，牌局 1 的两张牌面标签**一模一样**，期望却差 3.3333。
   *代价*：尺度选择错一档。牌局 2 里从半池换到 2 倍底池，成对面上少赚 1.2000、连张面上少赚 2.3226——决定金额的是对手跟注的组合数，不是标签。要用标签下结论，就得把标签和数字一起跑出来。
2. **在两张同花的牌面上算"同花容量"。** 例 4 第一行：`As9s5d` 上 hero 与 villain 的同花组合数都是 **0**（手牌 2 张 + 牌面 2 张 = 4 张，四张不是同花）。
   *代价*：你会给对手记上 5 个此刻并不存在的同花组合，把 `who_can_bet_big` 指给错误的一侧——牌面 1 里两侧标签相同、期望差 3.3333，差别就全在这 5 个组合上，而它们需要第三张同花牌才存在。双色面给的是**听牌**（`flush-draw` / `backdoor-draw`），三色面给的才是**成牌**。
3. **在河牌上调用胜率。** `equity ... --board "As9s5d2s4c"` 直接报 `error: a board of five cards has no equity left to compute`。
   *代价*：写不下去的算式，或者更糟——用一个翻牌面的胜率去解释河牌决定。河牌只有 `best_score` 的大小关系，牌局 1 用的就是这个。

## 练习 / Drills

- 用 `PYTHONPATH=src python -c "from pokergto.board import classify, parse_board; print(classify(parse_board(b)).class_id)"` 逐个打出 `Td8s6h`、`KsQs7h`、`8s7s2d`、`Tc9d4h`、`AdKc7s` 的标签，先猜 `paired` 与 `connected` 的真假再看答案。哪一个的 `connected` 与你的直觉相反？
- 用例 1 的脚本把牌面换成 `Ah9c5d`、`Ad9h5c`、`Ac9d5h`（都是 rainbow，只是把花色挪一挪），确认三行胜率相同。再换成 `Ah9s5d`（two-tone，无同花听牌方？），第几列开始变？
- 例 3 复算：把 villain 范围改成 `KQs,QJs,KJs,JTs,98s,76s,99`（去掉 `55`）后重跑 `advantage`。坚果份额、`who_can_bet_big` 变不变？
- 牌局 2 变式：把下注尺度改成 12 进 12（1 倍底池，需弃牌率 50.00%）。用同一段脚本重算两个面上的期望，哪个面掉得多？

## 自测清单 / Self-check

- [ ] 我能写出 `dynamic` 的三条析取式，并举出一张"教科书干面但引擎判 dynamic"的牌面及原因（`Kh7s3d`，因为 `[3..7]` 窗口里含 3 和 7）。
- [ ] 我能对任意牌面跑 `classify` 并解释 `class_id` 里每个词的顺序。
- [ ] 我记得 `Kh7s3d` 与 `Kd8h3s` 的胜率优势只差 0.40 个百分点，并知道这说明标签不是量度。
- [ ] 我能在两张同花的牌面上说出"同花组合数为 0"，在单色牌面上说出 45 个起手组合当场成花。
- [ ] 我知道河牌面上该用 `best_score` 比较而不是 `range_equity`，也知道坚果份额必须除以条件化之后的组合数（3/29 = 0.103448），而未收窄的 `parse(spec).total_combos()` 是另一个问题的分母。

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
本节所有数字都由本仓库计算，未引用任何商业求解器或付费课程：

| 内容 | 来源类型 | 位置 |
|---|---|---|
| 七个谓词与 `class_id` 拼法 | `derived` | `src/pokergto/board.py`（`is_monochrome` … `classify`），本文推导节 |
| 例 1 三行优势数字（0.638385 / 0.610233 / 0.569199 等） | `derived` | `advantage(parse(H), parse(V), parse_cards(b), mode="exact")`，命令见例 1；`As9s5d` 行与 `table.03-01.equity-vs-nut-advantage` 第三行一致 |
| 例 1 的坚果份额（0.103448、0.034483）与参与计算的组合数（46 / 29） | `derived` | `advantage(...)`（内部先 `with_removed(*board)`）；与 `table.03-01.equity-vs-nut-advantage` 第三行同值。直接把没收窄的范围递给 `nut_advantage` 现在会被 `InputError` 拒绝 |
| 例 2、例 3、例 5 的数字 | `derived` | 同上，牌面分别取 `Kh7s3d`、`Kd8h3s`、`Kh7s7d`、`Kh7s3d4c`、`Kh7s3dQh`；例 3 的上限由 `pokergto.theory.range_advantage#is_capped` 在 `ALL_COMBOS` 上取最大，且必须传已做移除的范围（未移除时抛 `InputError`） |
| 例 4 的成牌计数与 45 / 55 两个组合数 | `derived` | `best_score` + `category_of` 逐组合；`math.comb(10,2)`、`math.comb(11,2)` 与 1326 |
| 牌局 1 的 16/11、21/6、+4.6667、+8.0000 | `derived`（摊牌计数） | 正文 Python 片段，`with_removed(*board, *hero)` |
| 牌局 1、牌局 2 的门槛（33.3333%、66.6667%、MDF 0.6667 / 0.3333） | `derived` | `PYTHONPATH=src python -m pokergto mdf --pot 12 --bet 6` / `--bet 24` |
| 牌局 2 的四行期望（+10.8000、+9.6000、+9.6774、+7.3548） | `derived` | 同一脚本，尺度改 6 / 24，villain 范围同样做 `with_removed(*board, *hero)` |
| 两张范围（hero / villain 的 spec 字符串） | `reference` | 本仓库为讲解写死的示例；`table.03-01` 的 `provenance.assumptions` 已声明这一点 |

<!-- provenance: kind=reference verified=false -->
!!! unverified "未核验 / UNVERIFIED"
    "某类质地偏向某类玩家"、"真实 CO 范围在某质地上的频率"、"对手会因为这张面改变防守"——这些都是对手模型的说法，本仓库没有实现，因此不以任何数字形式出现在正文。要走通这条路，需要先在 `src/pokergto/solver` 里解出该质地的策略，再由 `tools/run_solver.py` 生成带 `solver_run` 的 artifact；在那之前，任何此类句子都必须写成 UNVERIFIED。

## 术语 / Terms

<!-- terms: board-texture, monochrome-board, two-tone-board, rainbow-board, paired-board, connected-board, static-board, dynamic-board, wet-board, dry-board, broadway-board, backdoor-draw, flush-draw, range-advantage, equity-advantage, nut-advantage, capacity, range, combos -->

| 缩写 | 中文 | English | 本节里的含义 |
|---|---|---|---|
| — | 牌面质地 | board texture | 三条轴上的分类结果，不是量度 |
| — | 单色牌面 | monochrome board | `len({suit}) == 1`，同花当场可成 |
| — | 双色牌面 | two-tone board | `len({suit}) == 2`，同花**尚未**可成 |
| — | 彩虹牌面 | rainbow board | `len({suit}) >= 3`，本节的对照组 |
| — | 成对牌面 | paired board | `len({rank}) < len(board)`，人人至少一对 |
| — | 连张牌面 | connected board | 存在相邻两点数差 1（含 wheel） |
| — | 宽面 / 干面 | wet board / dry board | 口语标签；引擎没有对应谓词，能跑的只有下面两个 |
| — | 动态牌面 | dynamic board | `connected or (flush_draw and not monochrome) or straight_draw` |
| — | 静态牌面 | static board | `dynamic` 为假 |
| — | 成牌容量 | capacity | 某类成牌在范围里的组合数，例 4 那张表 |
| — | 坚果优势 | nut advantage | 坚果档份额之差，决定谁能下大注 |
| — | 胜率优势 | equity advantage | 胜率之差，决定谁能常下注 |
