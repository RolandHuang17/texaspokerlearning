# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Bilingual note: entries carry both languages because the changelog is part of the public
contract surface (lesson ids and artifact schemas are versioned; see CONTRIBUTING.md).
Le résumé est en chinois sous chaque entrée.

## [Unreleased]

### Added / 新增
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
