# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Bilingual note: entries carry both languages because the changelog is part of the public
contract surface (lesson ids and artifact schemas are versioned; see CONTRIBUTING.md).
Le résumé est en chinois sous chaque entrée.

## [Unreleased]

### Added / 新增
- `pokergto.preflop` answers the question `adr/0006` left priced but unsolved: how to get a preflop all-in
  matrix at all. It samples **boards** rather than deals, scoring all 1,326 holes against each board in one
  `evaluate7_many` pass and enumerating every dealable combo pair on it, so each cell is exact conditional on
  the board set and the only noise left is board variance. Measured: 22 ms per board, so the full 169x169
  grid is 7.3 minutes at 20,000 boards with a 0.0030 mean standard error (worst cell 0.0053), against three
  cells computed exactly at 142-178 s each -- `AA` v `KK` 0.8194605047, `AKo` v `QQ` 0.4324233606, `72o` v
  `22` 0.3258923844 -- where the sampled deviations are 0.5 to 1.9 of the matrix's own sigmas. Sampling a
  *deal* per cell, which is the obvious implementation, measures 8,900 samples/s and prices the same grid at
  17.9 hours: it pays for two noises at once, and combo choice is not the expensive one.
  `pokergto.preflop` 回答的是 `adr/0006` 只标了价却没解决的那个问题：翻前全下的矩阵到底怎么拿。它采的是**牌面**而不是发牌：
  每个牌面用一次 `evaluate7_many` 给 1,326 个组合打分，再在该牌面上枚举所有发得出的组合对，所以在给定的牌面集合上每个格子是
  精确的，剩下的只有牌面方差。实测每个牌面 22 毫秒，即整个 169×169 网格在 20,000 个牌面下 7.3 分钟，平均标准误 0.0030（最差格
  0.0053）；与三个精确算出的格（各 142-178 秒：`AA` 对 `KK` 0.8194605047、`AKo` 对 `QQ` 0.4324233606、`72o` 对 `22`
  0.3258923844）相比，偏差落在自身 sigmas 的 0.5 到 1.9 倍内。显而易见的实现——按格采样整副发牌——实测 8,900 样本/秒，同一张
  网格要 17.9 小时：那是一次付两种噪声，而组合选择并不是更贵的那种。
- `adr/0007` closes `adr/0006`'s open question as option A and pins the boundary that choice forces: ADR-0002
  cut Monte-Carlo sampling of private cards *in the CFR inner loop* without saying what a preflop solve may do
  about the payoff table underneath it. Terminal utilities may come from a declared board sample; regret sums,
  strategy sums and exploitability stay exact over whatever table they are given. Two cautions are recorded
  rather than footnoted. A binomial error bar on the comparison count understates the truth by about 3.2x,
  because pairs sharing a board are correlated -- the first version of the validation test made exactly that
  mistake and called a real 1.6-sigma deviation "6.2 sigma", so the test now checks the empirical sigma against
  a closed-form hypergeometric one. And "sampled" is not "usable": a range boundary compares an equity to a
  threshold, so the number of classes whose verdict flips between two independent seeds has to be measured
  before chapters 05, 10, 11 and 12 print a range. That measurement, and the `data/gen/preflop/**` artifact
  itself, are outstanding, and both are prerequisites rather than follow-ups.
  `adr/0007` 把 `adr/0006` 的开放问题按 A 关闭，并钉住这个选择逼出来的边界：ADR-0002 当年禁止"CFR 内循环里采样私有牌"，
  但没说翻前求解依赖的支付表怎么办。现在的规则是：全下的终结效用可以来自声明过的牌面样本；遗憾和、策略和与可剥削度仍须在拿到手
  的表上精确计算。两条告诫写进正文：牌面共享的比较相关，按二项式算误差会小约 3.2 倍（校验测试第一版就犯了这错，把真实的 1.6
  sigma 说成"6.2 sigma"，因此现在拿超几何闭式解去校经验 sigma）；"被采样"不等于"能用"——范围边界是拿胜率与门槛比较，所以在
  05/10/11/12 印范围之前必须量两个独立种子之间有多少类判定会翻转。该测量与 `data/gen/preflop/**` 生成物都还没做，而且是前置
  条件不是后续工作。
- `tests/test_preflop.py` holds nine checks: a class against itself is exactly 0.5 with zero dispersion,
  `equity[i,j] + equity[j,i] == 1` to the last bit, all 28,561 ordered cells populated including the diagonal,
  determinism under a fixed seed and movement under a different one, refusal of sample sizes too small to
  disperse, the closed-form pair-count check, the `1/sqrt(boards)` behaviour of the error bar, and agreement
  with the exact cells (marked `slow`). `tools/cost_probe.py` gains a per-board ceiling for the matrix pass --
  80 ms against 22 ms measured -- because the whole budget is stated in that unit and a refactor could multiply
  it without changing a single number. `tests/test_preflop.py` 的九条检查：同类对同类恰为 0.5 且无离散、
  `equity[i,j] + equity[j,i] == 1` 到位、28,561 个有序格全都有值（含对角线）、固定种子可复现且换种子必须变、样本太小直接拒绝、
  组合数对闭式解、误差棒按 `1/sqrt(boards)` 收缩、与精确格的一致性（标 `slow`）。`tools/cost_probe.py` 新增矩阵扫描的每牌面
  上限（实测 22 毫秒，预算 80 毫秒），因为整条预算就是以这个单位表述的，重构可以在不改任何数字的情况下把它放大。
- Leduc hold'em is solved and gated, which is the first solver claim in this repository that has no
  closed form behind it. 360 deals, 36 decision nodes, 3,780 information sets, and the rules are written
  out in `src/pokergto/solver/games.py#leduc` rather than borrowed: the artifact's value is
  `-0.0436612219` chips per hand at exploitability `2.25e-6`, inside the bracket `[-0.0436636,
  -0.0436591]` that its own two exact best responses imply. The gates are that bracket, plus dominance
  (nobody folds the nuts, nobody calls with a hand losing to everything) restricted to information sets the
  solved strategy actually reaches -- 3,780 rows include hundreds the equilibrium never plays, and an
  average strategy is free to be wrong there, so the reach floor is stated rather than assumed.
  Leduc 扑克现在被解出来并登记进门禁，这是本仓库第一个没有闭式解背书的求解器结论。360 个发牌、36 个决策
  节点、3,780 个信息集，规则完整写在 `games.py#leduc` 里而不是引用外部定义：生成物给出的博弈值是每手
  `-0.0436612219`，可剥削度 `2.25e-6`，落在它自己两条精确最佳响应推出的区间 `[-0.0436636, -0.0436591]`
  之内。门禁就是这个区间，加上占优关系（坚果牌不弃牌、必输牌不跟注）——但只限制在解出的策略真正会走到的
  信息集上：3,780 行里有几百行均衡根本不走到，而平均策略在那些地方"是错的"并不计入可剥削度，所以那个可达
  阈值是写出来的，不是猜出来的。
- `solver/vector.py` is a producer now, for Leduc only. The per-deal recursion spends 0.23 s per
  iteration on that tree against the vector form's 0.003 s -- 68x at 50 iterations, 77x at 200, 35 s
  versus about 38 minutes for the 10,000 the gate registers -- and it earned the job by clearing every
  registered gate on its own (`tests/test_solver_vector.py`), where under plain regret matching the two
  implementations are bit-identical. Kuhn and the one-street toys are still written by `cfr.py`.
  `solver/vector.py` 现在可以产出生成物了，但只负责 Leduc。同一棵树上逐牌递归每轮 0.23 秒、公共树形式
  每轮 0.003 秒——50 轮时 68 倍、200 轮时 77 倍，登记的那 10,000 轮从约三十八分钟变成 35 秒；它能接手，
  是因为自己独立通过了每一条已登记的门（`tests/test_solver_vector.py`），而在朴素遗憾匹配下两种实现是
  逐位相同的。Kuhn 与单街玩具仍然由 `cfr.py` 产出。
- The trainer's solver screen can filter Leduc's 3,780 information sets and re-points its picker when a
  different artifact is loaded, instead of leaving a stale key looking up an empty strategy -- which is a
  blank panel that renders like a solved one. Verified in a browser on `solver/leduc.json`, in both
  locales, with the pass and the filter branch both clicked.
  训练器的求解器观察台现在可以过滤 Leduc 的 3,780 个信息集，并且在换产物时重设选择框，而不是留着旧的键
  去查一个空策略——那是一块看起来"已经解好"的空白面板。已在浏览器里对 `solver/leduc.json` 实测，中英两版、
  过滤与命中两条分支都点过。
- Quiz pipeline: `data/src/quizzes/quizzes.yaml` authors *domains* (which quantity, over which inputs),
  `tools/gen_quizzes.py` instantiates 19 items and asks `pokergto` for each answer, and
  `tools/check_quiz_answers.py` recomputes every stored answer in CI and in a pre-commit hook. There is
  no field anywhere in the authored YAML where an answer may be written, so there is no answer key to go
  stale. A negative test tampers one number and requires the gate to name it.
  题库流水线：`data/src/quizzes/quizzes.yaml` 只写"考哪个量、取值域是什么"，`tools/gen_quizzes.py`
  生成 19 题并向 `pokergto` 要答案，`tools/check_quiz_answers.py` 在 CI 与 pre-commit 里逐题重算。
  作者侧 YAML 里根本没有"答案"这个字段，所以不存在会过期的答案键；负向测试改一个数字，闸门必须点出来。
- Trainer: a fourth screen, 题库速算 / Quick drill. The learner's number is compared to the artifact's
  computed answer with the artifact's own tolerance; both the pass and the fail branch were clicked in a
  browser, because a drill whose correct-answer path never ran is only half tested.
  训练器加第四块屏（题库速算）：学员输入与产物里"算出来的答案"按产物自带的容差比对；判对与判错两条
  分支都在浏览器里真点过——没跑过"答对"的练习只算测了一半。
- `trainer/`: a static Vue 3 + Vite trainer at `/trainer/` with three screens -- a sizing/MDF scale over
  the generated tables, a 13x13 range viewer over the generated charts, and a solver deck that plays the
  recorded exploitability curve and prints the proof ledger. It implements no poker mathematics: the
  artifact list comes from the synced manifest and every fetched file is sha256-checked against it.
  新增 `trainer/`（Vue 3 + Vite 静态训练器，发布在 `/trainer/`）：尺度/MDF 滑尺读生成的表格、13×13
  范围图读生成的图表、求解器观察台播放录好的收敛曲线并打印证明登记表。它不实现任何扑克数学：可用产物
  清单来自同步后的清单文件，每个抓取到的文件都要与它对 sha256。
- `tools/sync_trainer_data.py`: the only bridge from `data/gen` to the trainer, with a `--check` mode
  that CI runs so a bundle built against stale artifacts cannot deploy quietly.
  `tools/sync_trainer_data.py` 是 `data/gen` 通往训练器的唯一通道，带 CI 用的 `--check`，让"拿旧产物
  构建出来的包"无法悄悄上线。
- Chapters 00, 01 and 02 authored bilingual and marked `ready`: 18 lessons, 36 files, every numeric
  claim injected from `data/gen` rather than typed.
  第 00、01、02 章完成双语并已翻到 `ready`：18 节课、36 个文件，课文里的每个数字都由 `data/gen`
  注入，没有一个是手打的。
- Chapter 08 lessons 01–04 (game trees, regret matching, a hand-traced Kuhn iteration, and
  convergence-vs-average strategy) bilingual, with the solver's own exploitability curves as AUTO
  tables. 第 08 章前四节完成双语，并把求解器自己的收敛曲线作为 AUTO 表嵌入课文。
- `tools/cost_probe.py`: a per-family wall-clock and memory budget for the solver, enforced in CI, with
  the measured baseline written next to the numbers. `mkdocs_nav.py`: the site navigation is generated
  from `data/src/curriculum.yaml`, so a lesson registered is a lesson reachable.
  新增 `tools/cost_probe.py`（按博弈族设定运行时与内存预算，进 CI，预算旁边写着实测基线）与
  `mkdocs_nav.py`（站点导航由课程骨架生成，登记即到达）。
- `evaluate5_many`, `evaluate7_many`, `evaluate7_many_reference` and `best_scores_many` in
  `pokergto.evaluator`: the same rules as the scalar evaluator over blocks of 52-card indices, returning
  the **identical integers** rather than an order-equivalent re-encoding. Measured on the author's laptop
  (py3.12, Windows, 2026-10-07): 1,028,474 five-card hands/s against 62,118 scalar (16.6x) and 313,984
  seven-card hands/s against 46,296 (6.8x). The proof is the same shape the module already used: all
  2,598,960 five-card hands compared element-wise against `evaluate5` (`slow`), plus every hand of five
  structurally chosen subdecks -- single-suit, 6 ranks x 4 suits, 8 x 2, 9 x 3, 9 x 4 -- and 9.6 million
  seven-card hands checked against the literal best-of-21 definition. That sweep found a real bug: on
  seven cards `A-2-3-4-5-6-7` contains a wheel *and* a seven-high run, and the first version scored it
  five-high. No category changes, so every category-count assertion in the repository stays green through
  it; it is invisible on five cards, which is why five-card-only testing is not a proof.
  `pokergto.evaluator` 新增 `evaluate5_many` / `evaluate7_many` / `evaluate7_many_reference` /
  `best_scores_many`：对 52 张牌索引的整块牌做与标量版本同样的规则，且返回**完全相同的整数**，不是"顺序
  等价"的另一种编码。作者本机实测（py3.12、Windows、2026-10-07）：五张牌 1,028,474 手/秒对比标量 62,118
  （16.6 倍），七张牌 313,984 手/秒对比 46,296（6.8 倍）。证明沿用本模块已有的口径：全部 2,598,960 个五张
  牌牌型逐元素对比 `evaluate5`（`slow`），外加五个按结构挑选的子牌堆的**每一个**牌型，以及 960 万个七张牌
  牌型对比字面定义（21 选最优）。正是这个全枚举扫出一个真 bug：七张牌时 `A-2-3-4-5-6-7` 同时含轮子和
  七高顺，第一版把它算成五高。类别不变，所以仓库里所有类别计数的断言都发现不了它；五张牌上也不可能看见——
  这就是只用五张牌测试不算证明。

### Changed / 变更
- `equity.py`'s two enumeration primitives are public now: `score_matrix` (was `_score_matrix`) and
  `conflict_mask` (was `_conflict_mask`). `pokergto.preflop` is their second caller, and importing a sibling's
  underscore name across a package boundary is how a "private" helper becomes load-bearing without anyone
  deciding that. Their docstrings already explained the invariants that matter; nothing about their behaviour
  changed.
  `equity.py` 的两个枚举原语转为公开：`score_matrix`（原 `_score_matrix`）与 `conflict_mask`（原 `_conflict_mask`）。
  `pokergto.preflop` 是它们的第二个调用方——跨模块边界引用带下划线的名字，正是"私有"辅助函数在没人拍板的情况下变成关键依赖的
  方式。行为没有任何变化。
- Lesson `01-05`'s cost paragraph is now a four-way table measured in one process (definition, direct
  algorithm, and both vectorised: 3,212 / 51,507 / 40,325 / 331,714 seven-card hands per second), its
  "what proves this" list gained the vectorised layer as a fifth route, and its closing claim moved: the
  wall between exact and Monte Carlo is no longer one preflop matchup (that is 17.3 s now) but the matrix
  `adr/0006` priced. Both languages, same numbers, same table shape. 课文 `01-05` 的成本段落改成一次进程内
  四路实测表（定义、直接算法、以及两者的向量化版本：3,212 / 51,507 / 40,325 / 331,714 手七张牌每秒），
  "用什么证明"一栏新增向量化路径作为第五条路，结论也换了：把精确枚举推回蒙特卡洛的那堵墙不再是一手翻前对位
  （现在那是 17.3 秒），而是 `adr/0006` 量过的那张矩阵。中英同数、同表形。
- `range_equity`'s exact path enumerates in blocks now: every legal (board, combo) pair is scored in one
  vector call, and the runout loop no longer carries the evaluation. Measured on the same machine: the
  widest exact enumeration any lesson cites (884 combos against 442 on `Kh7h2d`) 37.9 s -> 7.84 s, and
  exact preflop `AhAs` versus `7d2s` over 1,712,304 runouts 353.8 s -> 17.3 s. Every equity in the
  committed artifacts is unchanged to the last stored digit -- which is the assertion, not an aside: a
  speed-only difference must not be observable in `data/gen`.
  `range_equity` 的精确路径改为分块枚举：每个合法的（牌面，组合）对一次向量评估，遍历里不再顺手算牌。
  同一台机器实测：课文引用最宽的那次精确枚举（`Kh7h2d` 上 884 组合对 442 组合）从 37.9 秒到 7.84 秒；翻前
  `AhAs` 对 `7d2s` 的 1,712,304 个摊面从 353.8 秒到 17.3 秒。已提交生成物里的每一个胜率末位不变——这句是
  断言而不是旁白：只关速度的差异不该在 `data/gen` 里留痕。
- **`adr/0006` supersedes part of `adr/0002`: preflop is not "tractable exactly".** The premise was that
  removing future *decisions* removes the cost, but a preflop all-in still runs five cards to the board,
  so the full exact 169x169 class matrix is `2,598,960 x 225,780 = 5.87e11` evaluations, about 740 hours at
  the measured throughput. Vectorising the evaluator bought 4.8x to 20.4x where three orders of magnitude
  were needed, and the honest output of this change is a measured negative result: `EXACT_EVAL_BUDGET`
  stays where it is, `tools/cost_probe.py` now guards the evaluator's throughput floor and the exact
  enumeration's wall-clock ceiling, and chapters 05/10/11/12 stay unauthored until the open question in
  `adr/0006` (three costed options) is decided. Two findings shaped the code and are recorded because they
  were not obvious: batching the *definition* (best-of-21 in one vector call, 39,305 hands/s) is slower
  than the scalar seven-card algorithm (46,296), and batching one board at a time made hand-vs-hand exact
  equity eight times **slower** (0.81 s against 0.11 s) than the loop it replaced.
  **`adr/0006` 部分取代 `adr/0002`：翻前并不"可以精确求解"。** 当初的前提是"没有后续决策所以可精确处理"，
  但翻前全下仍然要把五张公共牌摊完：完整的精确 169×169 类别矩阵是 `2,598,960 × 225,780 = 5.87e11` 次评估，
  按实测吞吐约 740 小时。向量化评估器带来的是 4.8 到 20.4 倍，而这里需要的是三到四个数量级。于是这次变更的
  诚实产出是一个实测的否定结论：`EXACT_EVAL_BUDGET` 保持不变，`tools/cost_probe.py` 开始守评估器吞吐下限与
  精确枚举的运行时上限，第 05/10/11/12 章在 `adr/0006` 里那个开放问题（三条已标价的路）定下来之前不写。有
  两个发现改变了写法，因为它们在事前都不显然：把"定义"向量化（一次算 21 个五张牌子牌型，39,305 手/秒）比
  标量的七张牌直接算法（46,296）还慢；而"一张牌面一次批量"让一手对一手的精确胜率比它替换掉的循环**慢了八倍**
  （0.81 秒对 0.11 秒）。

### Fixed / 修复
- `range_advantage.board_ceiling()` (new, and now shared with the table generator) takes its maximum over
  the combos that **can still be dealt** on the board. Before this, a combo holding a card the board already
  shows was counted, and the evaluator reads such a hand as containing that rank twice: on `5cKh3sTh4h` the
  undealable `Kh Ah` scores `flush A-K-K-T-4`, which beats the real ceiling `flush A-K-Q-T-4`, so an
  unfiltered ceiling can call a range capped that owns the board's best dealable hand. Measured over 4,000
  random boards of three to five cards, 100 have a strictly higher unfiltered ceiling; none of the three
  boards in `table.03-02` is one of them, which is why the fix is a named function with a test rather than
  a changed number. `table.03-02`'s caption states the new universe in both languages and
  `tests/test_range_advantage.py` pins the phantom case.
  `range_advantage.board_ceiling()`（新增，并与表格生成器共用同一个函数）现在只在**这张牌面上还发得出来**的组合里取
  最大值。此前，用到牌面已有牌的组合也被算进去，而评估器会把那张点数读成两张：`5cKh3sTh4h` 上发不出来的 `Kh Ah` 得
  `同花 A-K-K-T-4`，比真正的上限 `同花 A-K-Q-T-4` 还高——于是"没坚果"的判定能判错。4,000 个随机牌面实测有 100 个出现这
  种幻影压过真上限；`table.03-02` 的三个点面都不在其中，所以这次改动的产物是一个带测试的具名函数，而不是被改动的数字。
  `table.03-02` 的说明文字已用两种语言写明新的取值范围，幻影牌型由 `tests/test_range_advantage.py` 钉住。
- Chapter 03's theory module had **no test file at all**: `nut_advantage`, `is_capped` and `advantage` were
  executed only indirectly, through the generator that writes the tables, which is how a ceiling definition,
  a per-combo weight convention and a scoring rewrite could each live in that module unexamined.
  `tests/test_range_advantage.py` adds seven: batched scores equal the scalar definition combo by combo,
  nut shares equal a hand-recomputed share including the `near_nuts` knob, the phantom ceiling case, ceiling
  and verdict computed from one function, the board-narrowing refusal, `tolerance`'s direction (raising it
  makes "capped" harder to claim, with the margin measured rather than assumed), and `advantage()`'s
  identities. 第 03 章的理论模块此前**一个测试文件都没有**：`nut_advantage`、`is_capped`、`advantage` 只是被写表格的生成器
  间接跑过——上限的定义、每组合权重的口径、评分改写的等价，全都可以在没人检查的情况下待在那个模块里。新增七个测试：批量评分逐
  组合等于标量定义、坚果占比等于手算复核（含 `near_nuts` 旋钮）、幻影上限、上限与判定共用同一函数、未收缩范围的拒绝、
  `tolerance` 的方向（调大只会让"封顶"更难成立，差值是量出来的）、以及 `advantage()` 的恒等关系。
- `ranges.from_chart()` multiplied each chart cell's frequency by that class's combo count, producing

  per-combo weights up to twelve against `Range`'s documented invariant that a weight is a probability in
  `[0, 1]`. It therefore raised on **any** fully-included class, which is to say on every committed chart:
  the reproduce command lesson `01-04` prints for its 55.92% range matchup could not have run as written.
  The number itself was never wrong (re-derived after the fix: `0.5591717398`, and `tools/cost_probe.py`
  now re-derives it in CI), and no artifact was affected because no generator called this function -- which
  is exactly the gap this fixes: `from_chart` had no test. Two now cover it, a round-trip against the
  committed chart and a refusal check on a mis-declared `cell_combos` table.
  `ranges.from_chart()` 把表格里每格的频率又乘了一遍该类的组合数，于是每组合权重最高到 12，直接违反 `Range`
  写明的"权重是 [0,1] 的概率"。结果是它对**任何**整格包含的类都会抛错——也就是对所有已提交的图表：`01-04`
  为 55.92% 那个范围对局印出来的复现命令按原文根本跑不起来。数字本身没错（修好后重新算出 `0.5591717398`，
  现在 `tools/cost_probe.py` 每次构建都会重算它），也没有任何生成物被牵连，因为没有生成器调用这个函数——而这
  正是要补的洞：`from_chart` 一个测试都没有。现在有两个：一个拿已提交图表做往返校验，一个检查 `cell_combos`
  被写错时必须拒绝。
- `solver/vector.py` floored *every* regret row after touching a few, which also erases the opponent's
  negative regrets during our own traversal: a different CFR+ trajectory from `solver/cfr.py`, and one no
  gate detected. Every registered gate passed with the wrong scope -- the two forms still agreed on each
  frequency the registry looks at -- while the solved strategy tables drifted up to `1.1e-2` apart. Only
  the rows a node touched are floored now, which is what lets "the same algorithm, faster" be said of it.
  `solver/vector.py` 过去在碰到几个信息集之后会把**整个**遗憾矩阵都做一次下限截断，于是连对手那一侧的负
  遗憾也在我们这次遍历里被抹掉：这与 `solver/cfr.py` 走的是不同的 CFR+ 轨迹，而且没有任何一道门能发现。
  用错的截断范围跑，所有已登记的门照样通过——两种实现在门禁看的那几个频率上仍然一致——但整张策略表会差到
  `1.1e-2`。现在只截断这个节点真正碰到的那些行，"同一算法、只是更快"这句话才说得出口。
- `data/gen/manifest.json` recorded the commit sha, the Python version and the numpy version of the
  machine that built it. A byte-compared file that names its own commit can never agree with a later
  checkout, so `gen_all --check` was guaranteed to fail after every commit and on every CI Python other
  than the author's. The manifest now holds content only and that provenance is printed to the build log.
  `data/gen/manifest.json` 以前会记录生成它的 commit sha、Python 版本与 numpy 版本。一个要被逐字节比对的
  文件如果写着自己来自哪次提交，就永远和后来的 checkout 对不上：`gen_all --check` 必然在每次提交之后失败，
  也必然在除作者机器之外的 CI Python 上失败。现在 manifest 只装内容，那三类信息来源打进构建日志。
- `tools/check_bilingual.py`'s live-hand rule could never fire: its regex required two spaces after
  `<!--`, so a lesson could claim examples it had not written. The declaration is now counted against
  the `hand.*` ids actually present, and both languages must teach the *same* hands.
  `check_bilingual.py` 的"每节课至少两手实战"这条规则原本永远不触发：正则要求 `<!--` 后有两个空格，
  于是课文可以声称它并没有写的例子。现在声明数要与文中真实出现的 `hand.*` 数量对账，且两种语言必须讲
  同一批牌局。
- Table cells written as `{zh, en}` render in the requested locale; the five-card category counts were
  showing Chinese labels under English headers. An unknown cell shape now raises instead of stringifying
  into a lesson. 表格单元支持 `{zh, en}` 双语值：五张牌型计数表原本在英文标题下显示中文标签。无法识别的
  单元格现在会直接报错，而不是把一个字典印进课文。
- `poker equity` accepts a hand *or* a range in either position; the documented two-positional-range form
  previously raised. `Registry.find_orphans` compared repo-relative paths against docs-relative ones, so
  every authored file looked unregistered and every registered lesson looked missing -- and drafts no
  longer count as missing files.
  `poker equity` 现在两个位置都可以写单一手或一个范围（此前文档里那种"两边都是范围"的写法会报错）；
  `Registry.find_orphans` 拿仓库相对路径和 docs 相对路径相比，导致每个真实文件都被判成未登记、每节登记过的
  课都被判成缺文件，且 `draft` 不再被算作缺文件。

## [0.1.0]

### Added / 新增
- Project inception: architecture (ADR-0001…0005), the 15-chapter / 92-lesson bilingual curriculum
  spine registered in `data/src/curriculum.yaml`, the `pokergto` math engine, and a CFR solver whose
  output is gated by `solver/proofs.py`.
  项目立项：五项承重决策（ADR-0001…0005）、登记在 `data/src/curriculum.yaml` 的 15 章 92 节双语骨架、
  `pokergto` 数学引擎，以及一个结论必须过 `solver/proofs.py` 闸门才允许发布的 CFR 求解器。
- The static Vue trainer is planned for M3 and is not part of this release; the roadmap says so rather
  than the changelog promising it. 训练器（Vue，静态）属于 M3，不在本次发布内；这一点写在路线图里，
  而不是在变更日志里预先许诺。
