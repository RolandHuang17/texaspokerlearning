# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Bilingual note: entries carry both languages because the changelog is part of the public
contract surface (lesson ids and artifact schemas are versioned; see CONTRIBUTING.md).
Le résumé est en chinois sous chaque entrée.

## [Unreleased]

### Added / 新增
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

### Fixed / 修复
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
