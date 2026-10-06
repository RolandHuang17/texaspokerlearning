# 怎么读这套教材：底牌、牌面、四条街与位置名称

<!-- hands: 3 -->
<!-- terms: hole-cards, board, street, preflop, flop, turn, river, pot, bet, raise, call, fold, check, hero, villain, six-max, position, button, small-blind, big-blind -->

## 本节目标 / Objectives

- 拿到任意一课，30 秒内说清三件事：这一节的数字是哪条命令算的、每条结论标的是哪种来源、该课的前置课是哪几节。
- 复述课节的 15 个固定分节各自负责什么，并说清少一节或多一节为什么会把构建弄红。
- 用本仓库唯一认可的写法说底牌、牌面、四条街与座位名称；不再把"手牌""公牌""轮"当成同义词。
- 按自己的局型选出路线：现金 100 个大盲、锦标赛、单挑与按钮位对抗、群体剥削，各自从哪一章进门，共用哪一条主干。

## 前置知识 / Prerequisites

- 无。`data/src/curriculum.yaml` 给 `00-01` 记的 `prereq` 是空列表，它是整棵依赖图的根。
- 会打开终端、`cd` 到仓库根目录即可。命令跑不通是 `00-03` 要解决的问题，本课先讲读法。

## 核心原理 / The principle

这套仓库有三件东西，各管一件事，混用就出事：

| 件 | 位置 | 负责 | 你该怎么对待它 |
|---|---|---|---|
| 教材 | `docs/en/**`、`docs/zh/**` | 讲清一件事为什么成立 | 读它，但不要在它里面抄数字 |
| 引擎 | `src/pokergto/**` | 算出每一个数字 | 自己跑一遍，跑出来的就是答案 |
| 训练器 | `trainer/**` | 把同一批数字变成反复练习 | 已有三块屏：尺度滑尺、13×13 范围图、求解器观察台；范围打分要等 M4 的 EV 基准 |

引擎和教材之间隔着一次生成：`tools/gen_all.py` 把引擎的结果写成 `data/gen/**` 下的 JSON，
`tools/inject_doc_tables.py` 再把这些 JSON 渲染进课节的 AUTO 区块。方向是单向的，所以正文里的数字
只有两种出身：要么被 AUTO 区块生成，要么就是能从生成物手算出来的算术。

读任何一课，只需要盯住两条线：**数字的来路**（AUTO 区块 + 它下面的 `<!-- provenance: ... -->` 行）
和**结论的来路**（`derived` / `reference` / `external`，缺一项就构建失败）。

<!-- provenance: kind=derived verified=true -->
> !!! note "来源 / Provenance"
>     本节不复述任何外部范围表。结构规则来自 `adr/0001`、`adr/0005`、`NOTICE`、`data/README.md`。

## 推导 / Derivation

"为什么要固定分节、为什么表要生成"不是审美问题，从三条前提就能推出来。

前提 1：两种语言同时给同一批结论。`data/gen/index.zh.json` 的 `totals` 记着 `lessons: 92`，
一课两个语言文件，92 × 2 = 184 个课节文件。

前提 2：绝大多数读者不读引擎源码，他们读 markdown。

前提 3：免费、离线、不注册是承诺，所以不能把"这个数字对不对"外包给一个在线服务。

由前提 1：一个数字一旦手抄就有至少 2 份副本，副本数随引用次数增长。两份副本是否一致只能靠人记住，
而人记住的东西一定漂——漂出来的样子就是第 02 章写 66.67%、第 07 章写 67%，再各自漂一次语言。
由前提 2：读者发现不了漂移，因为他手上没有第二个来源可比。
由前提 3：唯一能被读者自己复核的东西，是一条在他机器上也能跑出同样字节的命令。

三条合起来就是本仓库的三条结构规则：

1. 数字只在 `src/pokergto/**` 算一次，落进 `data/gen/**`，正文只嵌 AUTO 区块（`adr/0001`）。
2. 每条策略结论带 `provenance`，字段缺失就让构建失败，不指望审阅（`adr/0005`）。
3. 两种语言的课节必须机器可比：分节数、H1/H2/H3 总数、AUTO id 序列、声明的术语，逐项相等。

固定 15 节是第 3 条的实现手段：机器能比的东西必须一眼能定位。所以分节名是双语一对、整行写死的
（`## 推导 / Derivation` 这一行在中文课和英文课里是同一串字节），比较时根本不需要翻译。
`tools/check_bilingual.py` 今天真正比的是**分节数、标题总数、AUTO id 的有序序列**；分节顺序目前靠人审，
`docs/development/bilingual-style.md` 把这条弱点写在明面上，没有假装自动化。

## 直觉 / Intuition

把这套东西想成一家只有一本账的店。引擎是收银机，`data/gen` 是那本账，
中文教材、英文教材、训练器是三块菜单。菜单上不写价格，价格是收银机打出来贴上去的。
你在菜单上手写一个价格，就出现了第四个数字，而它跟谁都不一致。

于是阅读习惯只有一条：**看到数字先问它是哪条命令的结果**。问不出来的地方，课节会主动告诉你它是
`reference` 或者 `UNVERIFIED`——那也是一种答案，比没有答案好。

## 算例 / Worked examples

走一遍完整的读法，选 `02-03` 最低防守频率。跟着敲，几分钟就能把这一课的数字全部自己重算出来。
本仓库的文档把命令写作 `poker xxx`，那是 `python -m pokergto xxx` 的缩写；缩写形式要等 editable
安装成功才可用，`00-03` 会把这件事讲清楚，所以下面全用不依赖安装的写法。

**例 1 — 从课时号走到文件。** 在 `data/src/curriculum.yaml` 搜 `id: "02-03"`，读到
`slug: deriving-minimum-defense-frequency`、`prereq: ["02-01", "02-02"]`、`status_zh: draft`。
slug 就是文件名，章节 slug 就是目录名，所以路径唯一确定：
`docs/zh/02-the-math-of-one-decision/deriving-minimum-defense-frequency.md`。
课时号 `02-03` 不出现在路径里，它是永久 id；文件名可以改，id 不能改。

**例 2 — 让尺度表自己算出来，而不是读它。** 在仓库根目录跑：

```bash
PYTHONPATH=src python -m pokergto odds --lang zh
```

八行，八档尺度，其中 `1/3 pot` 那一行给出 MDF 75.00%、跟注所需胜率 20.00%、诈唬占比 20.00%、
`价值:诈唬` 为 4 : 1。这一行就是 `02-03` 里 `table.02-03.mdf-vs-sizing` 那块表的同一次计算的另一副面孔。

**例 3 — 把正文里那句话变成一条命令。** 正文说"底池 4.4 面对 1.4667 的 1/3 池下注要防守 75%"，就验：

```bash
PYTHONPATH=src python -m pokergto mdf --pot 4.4 --bet 1.4667
```

引擎回 `MDF = pot/(pot+bet) = 4.400/(4.400+1.467) = 0.7500`。它把公式和代入的数一起打出来，
所以你能检查的不是结果，是过程。

**例 4 — 范围记法与组合数。** 别按类别数估范围宽度：

```bash
PYTHONPATH=src python -m pokergto range "22+,ATs+" --lang zh
```

输出 `114.0 combos = 8.60% of 1326`，`classes` 是 22。114 ÷ 22 ≈ 5.2 组合/类，听起来每类都差不多，
可 `data/gen/tables/table.01-01.combo-decomposition.json` 里写死了：对子 13 类每类 6 个组合共 78，
同花 78 类每类 4 个共 312，不同花 78 类每类 12 个共 936；78 + 312 + 936 = 1326。同一类里 4 和 12 差三倍，
按类别平均就是在拿一个牌堆里不存在的"平均组合数"去数范围。

**例 5 — 一手牌的胜率，注意穷举的边界。**

```bash
PYTHONPATH=src python -m pokergto equity J9o --range-villain "88+,ATs+" --board "Kh7s3d" --mode exact
```

得 `17.49%`，`iterations` 那一栏报的是引擎枚举过的 runout 数，这次是 1,176，标准误 0——精确模式没有抽样误差。
对照例 2 的 20.00%：这手牌在 1/3 池下注面前过不了线。

## 生成表 / Generated tables

课节正文只留一对 HTML 注释，中间是空的。块的形状是（下面两行各自要套在一对 `<!--` 与 `-->` 里才算
真块；本课故意不写成真的，因为 `tools/check_provenance.py` 会数遍 `docs/**` 里每一个 `BEGIN AUTO`
并向它索要一枚 provenance 徽章，一个纯说明用的示例块会把构建弄红）：

```text
BEGIN AUTO:table.02-03.mdf-vs-sizing     ← 开块
END AUTO:table.02-03.mdf-vs-sizing       ← 闭块，id 必须一模一样
```

`tools/inject_doc_tables.py` 读 `data/gen/tables/table.02-03.mdf-vs-sizing.json`，按文件路径决定语言
（`docs/zh/**` 拿中文表头），填进表体、`<!-- provenance: kind=... verified=... -->` 一行、来源徽章，
以及最底下那条 `<!-- source: 模块::函数 via 生成器 -->`。中文课和英文课嵌的是同一个 id，
所以两张表在任何一次提交里都不可能给出不同的数——它们来自同一个 JSON。

本节把 `02-03` 那两张表调进来，你可以跟例 2 的命令逐格对照：

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

读这两张表的三条注意事项，都是真会绊人的地方：

1. **两张表是同一架尺度梯子的两种标签。** 上面那张写成 `1/4 pot`、`2x pot`，下面那张写成
   `0.25x pot`、`0.333333x pot`。行数一样、顺序一样，都是 `PYTHONPATH=src python -m pokergto sizes`
   打出来的 0.2500、0.3333、0.5000、0.6667、0.7500、1.0000、1.5000、2.0000。对不上号就逐行编号，
   别拿标签字符串去匹配。
2. **徽章那一行的类型名固定是 `unverified`**，`verified=true` 时它照样出现，只是标题里写着"已核验"。
   读 `kind` 和 `verified` 两个字段，别读样式。
3. **列名不等于问题。** 上面那张的 `诈唬所需弃牌率` 是下注方的门槛，`MDF` 是防守方范围的配额；
   下面那张的 `所需胜率` 是防守方单手牌的门槛。三个数回答三个问题，第 02 章专门把它们拆开。

课节开头还有两枚机器读的注释标记，渲染后看不见：一行声明 hands，写这一课共有几局实战牌局
（`check_bilingual.py` 要求 `ready` 的课至少 2 局）；另一行声明 terms，列出的每个 id 都必须在
`data/src/glossary.yaml` 里存在，写一个没注册的术语就是 CI 红灯。

## 实战牌局 / Live hands

下面三局用的是同一个读法：先把决策点写清楚，再把能算的都算出来，最后说错的打法值多少钱。
所有 EV 都按"这一街就当全下算"的单街近似：`EV(跟注) = 胜率 × (底池 + 2 × 跟注额) − 跟注额`，
弃牌记 0。后续街的隐含赔率、胜率实现这类修正属于 `01-06` 与第 06 章，这里不偷。

**牌局 1（`hand.00-01-bb-defense-call`）— 现金 6 人桌，双方 100 个大盲。**
按钮位开池 2.2bb，小盲弃牌，大盲跟到底。底池 4.4bb。翻牌 `Kd7d3h`，按钮位持续下注 1.4667bb（1/3 池）。
我方在大盲，底牌 `Ad5d`。

- 决策点：弃、跟、还是加注。三个动作都合法，所以这是一次真正的决策点。
- 配额：`mdf --pot 4.4 --bet 1.4667` → 0.7500。大盲这个范围里至少 75% 的组合数要继续。
- 门槛：`odds --lang zh` 的 `1/3 pot` 行 → 跟 1.4667 进 7.3334 需要 20.00% 胜率。
- 手里的：`equity A5s --range-villain "KQs+,ATs+,QJs+,AJo,TT-22,98s,87s" --board "Kd7d3h" --mode exact`
  → 37.26%。这里的 `A5s` 是**类别**，含 4 个组合；本仓库的记法（`src/pokergto/notation.py`）表达不了
  "只要方块那一组"，而 `Ad5d` 恰好是 4 个里带坚果同花听牌的那一个，所以 37.26% 把这手牌低估了。
  逐点核对：`equity Ad5d KsQc --board "Kd7d3h" --mode exact` → 46.77%。
- 算术：`0.3726 × 7.3334 − 1.4667 = +1.27bb`。
- 决策：跟注。弃掉的代价是一次 +1.27bb 的机会，而且它属于配额里必须留下的那一档。

**牌局 2（`hand.00-01-bb-defense-fold`）— 同一条线，另一副底牌。**
翻牌换成 `Kh7s3c`，按钮位仍下 1/3 池 1.4667bb。我方大盲拿 `Tc9h`（类别 `T9o`）。

- 配额与门槛不变：MDF 75%，需要 20.00%。
- 手里的：`equity T9o --range-villain "KQs+,AJs+,KJo+,QQ,77,66" --board "Kh7s3c" --mode exact` → 10.72%。
- 算术：`0.1072 × 7.3334 − 1.4667 = −0.68bb`。跟一次亏 0.68bb。
- 决策：弃牌。这不是"听牌不好看"的品味判断，是差 9.28 个百分点。
- 关键理解：弃这手牌**不违反** MDF。MDF 管的是范围里继续的组合数总量，
  10.72% 胜率的牌正好属于允许弃掉的那 25%。把 MDF 读成"每一副底牌都得防守 75%"是最贵的一种误读。

**牌局 3（`hand.00-01-river-bluffcatch`）— 单挑，河牌圈。**
牌面 `AsKd7h5c2s` 五张全出。底池 20，对手下 10（1/2 池）。我方是一副只赢空气的抓诈唬牌。

- 门槛：`odds --lang zh` 的 `1/2 pot` 行 → MDF 66.67%，跟注所需胜率 25.00%，诈唬占比 25.00%。
- 这里没有"胜率"可算。跑 `equity ... --board "AsKd7h5c2s"` 会被引擎拒绝：
  `error: a board of five cards has no equity left to compute`——五张牌面已经把牌定死，
  剩下的是比大小，不是概率。所以**河牌的判据是对手下注范围里空气的比例**，不是你这手牌还有多少成算。
- 算术：若对手这个尺度里的范围恰好 25% 是诈唬，跟注 EV = `0.25 × (20 + 2 × 10) − 10 = 0`。
  超过 25% 才值得跟，低于 25% 就弃。
- 配额：对手在 1/2 池尺度上要有 33.33% 的弃牌率才平衡（同表 `诈唬所需弃牌率` 列），
  所以我方范围里必须留 66.67% 继续，而抓诈唬牌是这 66.67% 里的主力。

## 范围图 / Range chart

导论课不给范围图，因为没有"要防守哪个范围"这个具体问题；这一节在第 01 章之后才开始有内容。
策略课里它放一张由 `tools/gen_ranges.py` 生成的 `range.*` 图，读法都一样：**图是配额，不是计划**。
比如 `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` 记的 `threshold` 是 0.66666667，
`total_combos` 是 884，`range_percentage` 是 66.67%——它只回答"半池下注必须防守多少个组合数"，
不回答"具体用哪几张牌"。

真正的 13×13 网格先由命令行看一眼（`PYTHONPATH=src python -m pokergto range "22+,ATs+" --lang zh`）：

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

三条读法：对角线是对子，上半三角是同花、下半三角是不同花（本仓库的轴向由
`pokergto.matrix13.Grid13` 定死，上面提到的 `range.02-03.mdf-floor-vs-half-pot` 把同一条约定写进了它的
`orientation` 字段）；
每格颜色是**这一格里有几个组合被包含**，不是"这手牌打多重"；`@@` 满格的对角线 13 格是 13 × 6 = 78 个组合，
跟例 4 的分解表严丝合缝。

## 为何成立、何时失效 / Why it works, when it breaks

这套读法成立的前提是：**`data/gen` 与代码同时代**。它在这几种情况下会失效，而且都是当下就会踩到的：

1. `data/gen/**` 落后于 `src/pokergto/**`。表还是那张表，公式已经改了。识别方法是跑
   `python tools/gen_all.py --check`，它会把整棵树重算一遍并逐字节比；这条命令只读，不会把工作区弄脏。
2. 你读的是缓存的网页而不是仓库文件。生成物会随提交变，`manifest.json` 里记着每个文件的 sha256。
3. 课节状态是 `draft`。骨架到底写了多少，去看 `data/gen/index.zh.json` 的 `totals`，
   别信任何散文里引用的计数；草稿的分节可能是骨架，数字可能还没接上 AUTO 块。
4. 有人手改了 AUTO 区块里的数字。这是本仓库定义的类别错误，`inject_doc_tables.py --check` 会说。
5. 你按课时号去找文件。路径里只有 slug。

## 陷阱 / Common mistakes

1. **在 AUTO 区块里改一个数字"让它更准"。** 你改的是一份副本，不是来源。
   *代价*：`python tools/inject_doc_tables.py --check` 立刻报 `AUTO block ... is stale`；
   更糟的是没跑这条命令的人，在 184 个文件里读到两个不同的数，而机制不会告诉他哪一个是真的。
2. **把课节 id 当文件路径。** `02-03` 是永久编号，文件名是 slug。
   *代价*：`check_bilingual.py` 靠 `stem_to_id()` 从文件名反查 id，路径猜错就等于凭空多出一个
   orphan 文件、少了一个已注册课节，两个错误一起报。
3. **把 `reference` 当 `derived` 读。** `adr/0005` 里 `reference` 只允许用在"能独立校验"的自建内容上。
   *代价*：例如被广为引用的那条"持续下注频率从单挑 65% 一路塌到五人 8%"，本仓库现在把它记成
   `reference` + 未核验（见 `NOTICE`）。把它当引擎结论用，就会拿一个没人推过的数去排范围。
   正确处置：读 `unverified_claims` 数组、顺着 `derivation_ref` 看有没有可跑的符号，然后自己跑
   `mdf --pot 10 --bet 5 --opponents 2`（引擎给的 42.27% 每人、合并 66.67% 才是推导出来的）。
4. **按类别估范围宽度。** 例 4 里 114 ÷ 22 ≈ 5.2，真实每类在 4、6、12 之间。
   *代价*：同一份"22 类"范围，按类别估会差到 3 倍（12 ÷ 4），MDF 配额直接算错。

## 练习 / Drills

- 只看 `data/src/curriculum.yaml`，说出 `07-01` 的文件路径与它的前置课，再打开文件核对分节数是不是 15。
- 跑 `PYTHONPATH=src python -m pokergto mdf --pot 12 --bet 12 --opponents 2`，
  把每人防守频率与 `data/gen/tables/table.07-01.multiway-defense.json` 里 1x 池那一组对照。
- 跑 `PYTHONPATH=src python -m pokergto range "88+,AKs,AQs" --json`，说出 `50.0` 组合、
  `3.7707%` 与 `9` 类，并解释为什么 `canonical_spec` 被打成 `88+,AKs-AQs`。
- 手改一个 AUTO 块里的某个数字，跑 `python tools/inject_doc_tables.py --check`，读完整句话，再改回来。
- 说出为什么中文课和英文课的 AUTO id 序列必须逐项相等，而不是"集合相等"。

## 自测清单 / Self-check

- [ ] 我能从一个课节 id 走到它的真实文件路径，并说清 slug 与 id 的分工。
- [ ] 我能在任意一课里指出：哪些数字来自 AUTO 块，哪些是手算的算术。
- [ ] 我能读懂 `<!-- provenance: kind=... verified=... -->` 这一行，并说出三种 kind 的差别。
- [ ] 我知道 `UNVERIFIED` 该怎么做：读 `unverified_claims`，找 `derivation_ref`，自己重跑一条命令。
- [ ] 我能按局型排出自己的阅读路线，并说出哪几章是四条路共用的主干。
- [ ] 我能说出四条街的名字与本仓库对"底牌 / 牌面"的强制写法，以及被拒用的同义词在哪个字段里。

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
本节所有数字要么来自下面列出的命令，要么来自 `data/gen/` 里已提交的生成物。全课未引用任何商业
求解器或付费课程的范围表。

| 内容 | 来源类型 | 位置 |
|---|---|---|
| 15 节模板、课节 id、prereq | 授权来源 | `data/src/curriculum.yaml` 的 `lesson_template` 与 `chapters` |
| 92 课 / 184 文件，以及其中多少节 `ready` | 生成物 | `data/gen/index.zh.json` 的 `totals`——计数去那里读；本节课故意不抄一份数字进正文 |
| MDF、所需胜率、诈唬占比 | `derived` | `src/pokergto/odds.py`；`pokergto mdf`、`pokergto odds` |
| 114 组合 / 8.60% / 22 类 | `derived` | `pokergto range "22+,ATs+"`；`data/gen/tables/table.01-01.combo-decomposition.json` |
| 37.26%、46.77%、10.72%、17.49% | `derived` | `pokergto equity ... --mode exact`，穷举 1,176 个 runout，标准误 0 |
| 半池防守配额 884 / 66.67% | `derived` | `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` |
| 多人持续下注频率塌缩那组数 | `reference` + **UNVERIFIED** | 见 `NOTICE` 与 `adr/0005`；未由 `theory/multiway.py` 复现前不得当结论用 |
| 13×13 网格轴向与图例 | 实现约定 | `src/pokergto/matrix13.py#Grid13`、`src/pokergto/render.py` |

## 术语 / Terms

<!-- terms: hole-cards, board, street, preflop, flop, turn, river, pot, bet, raise, call, fold, check, hero, villain, six-max, position, button, small-blind, big-blind -->

下表用词全部取自 `data/src/glossary.yaml`。括号里是这一课里它的具体含义，"不写"那一列是同一个字段
`avoid` 里被明令拒绝的同义词——中文扑克没有行业标准词表，这份文件就是标准。

| 缩写 | 中文 | English | 本课里的意思 | 不写 |
|---|---|---|---|---|
| — | 底牌 | hole cards | 发给自己的那两张 | 私牌、手牌 |
| — | 公共牌面 | board | 桌面公共的那几张，简称牌面 | 公牌、桌面 |
| — | 街 | street | 一次发牌后的下注回合 | 轮、下注轮次 |
| — | 翻前 | preflop | 前三张公共牌发出之前 | — |
| — | 翻牌圈 | flop | 前 3 张公共牌 | 翻牌面 |
| — | 转牌圈 | turn | 第 4 张公共牌 | 转牌面 |
| — | 河牌圈 | river | 第 5 张公共牌，牌已定死 | 河牌面 |
| — | 底池 | pot | 已经有人在里面的钱 | — |
| — | 下注 | bet | 新增的那笔钱 | — |
| — | 加注 | raise | 在别人已下的钱上再加 | 加 |
| — | 跟注 | call | 补齐到同一档 | — |
| — | 弃牌 | fold | 放弃底池 | — |
| — | 过牌 | check | 不下注也不弃牌 | 让牌 |
| — | 我方 | hero | 被分析视角的这一方 | 主角 |
| — | 对手 | villain | 被分析的另一方，不评判 | 坏人 |
| — | 六人桌 | six-max | 满员现金局的座位数 | 6 人桌 |
| — | 位置 | position | 行动顺序带来的信息优势 | 座位 |
| BTN | 按钮位 | button | 每街最后行动的人 | — |
| SB | 小盲注 | small blind | 提前塞进底池的一半 | — |
| BB | 大盲注 | big blind | 提前塞进底池的整注 | — |
