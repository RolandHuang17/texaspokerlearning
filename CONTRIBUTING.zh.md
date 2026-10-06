# 贡献指南

谢谢你愿意把扑克教学做成"可核验"的，而不是"要相信"的。

本仓库从可推导的原理出发教无限注德州扑克。这一个前提决定了下面几乎所有约定：一篇贡献能被读者复算，它就是强的；一篇贡献要求读者相信它，它就是弱的。

- 站点：<https://rolandhuang17.github.io/texaspokerlearning/>
- 训练器：<https://rolandhuang17.github.io/texaspokerlearning/trainer/>（M3 起）
- 英文版：[CONTRIBUTING.md](CONTRIBUTING.md)
- 决策与其理由：[adr/](adr/)
- 行为准则：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## 30 秒，从一次干净的 clone 开始

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -e ".[dev,docs]"

python -m pytest -q -m "not slow"     # 快速回路，两万次以上断言
python -m ruff check .                # 控制台脚本不在 PATH 上时，用 python -m 前缀
python -m mkdocs build --strict
```

Windows 注意：`pip` 可能把控制台脚本装进不在 `PATH` 上的用户 `Scripts` 目录，所以优先写
`python -m ruff`、`python -m mkdocs`、`python -m pytest`。`setup/install.ps1` 负责整套初始化，
`setup/doctor.py` 只读地诊断环境。

## 四个公共面，以及"破坏性变更"到底指什么

版本号承诺的是下面四样东西的形状保持不变，除此之外都不算公共面：

1. **引擎签名** —— `src/pokergto/**` 里的函数。
2. **产物契约** —— `data/schema/**` 里的 JSON Schema。
3. **课程编号** —— `data/src/curriculum.yaml` 里的 id。**永远不重新编号。** 一处引用、一条深链、
   另一节课的前置列表，都不该因为一次编辑而断掉。新增是可以的。
4. **CLI 报告形状** —— `poker --json` 与 `--report` 的输出结构。

| 变更 | 版本位 |
|---|---|
| Schema 破坏性变更、删除或重命名课程 id、删除引擎函数 | MAJOR |
| 新增课程、章节、引擎模块、产物类型、求解器博弈 | MINOR |
| 文本、保持含义的改写、翻译、契约内部的 bug 修复 | PATCH |

会提升版本号的 PR 必须在 `CHANGELOG.md` 的 `[Unreleased]` 下写 `### Added` / `### Fixed` 块。
`tools/check_release_notes.py` 与 `release.yml` 会检查这件事。

## 两条不是"风格偏好"的规则

### 1. 每个数字都是生成的

`tools/gen_all.py` 计算 `data/gen/**`，课文通过 AUTO 标记引用这些产物。
`tools/gen_all.py --check` 是一次字节级比对：拿已提交的产物和一次干净重建的结果比。它失败，
就说明仓库里提交的数字已经不再描述引擎现在算出来的东西。

所以：**改生成器，不要改产物。** 也不要往课文里手打任何生成器本可以产出的数字——当你发现自己在
手工填一张表，那说明 `tools/gen_tables.py` 里缺一个 builder。

### 2. 每节课从诞生起就是双语的

`docs/en/<章>/<节>.md` 与 `docs/zh/<章>/<节>.md`：同一路径、同样 15 个小节、同样的 AUTO id，
而且**在同一个 PR 里**。`tools/check_bilingual.py` 证明的是结构；译文是否忠实而不是机器腔，是人工
评审项——PR 模板会问你在哪几段没把握。

中文先写，因为术语决策（`data/src/glossary.yaml`）本身就是教学发生的地方。细节见
`docs/development/bilingual-style.md`。

## 三条贡献路径

### 修或写一篇课文

```bash
# 1. 新课程先登记：id、slug、双语标题、前置知识、两种语言各自的状态
$EDITOR data/src/curriculum.yaml
python tools/gen_curriculum_index.py --allow-unauthored

# 2. 复制模板。模板里的 H2 文本必须与 15 条 lesson_template 完全一致。
cp docs/_template/lesson.md.tmpl docs/zh/<章-slug>/<节-slug>.md
cp docs/_template/lesson.md.tmpl docs/en/<章-slug>/<节-slug>.md

# 3. 先算出你打算引用的每一个数字，再写包含它的句子
PYTHONPATH=src python -m pokergto odds
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2
PYTHONPATH=src python -m pokergto equity AhAs 7d2s --mode auto

# 4. 填充 AUTO 块，然后跑闸门
python tools/inject_doc_tables.py --file docs/zh/<章-slug>/<节-slug>.md
python tools/inject_doc_tables.py --file docs/en/<章-slug>/<节-slug>.md
python tools/check_bilingual.py && python -m mkdocs build --strict
```

一节课不是"你写完了"就 `ready`。它 `ready`，是因为 `python tools/check_bilingual.py` 报告零缺配对、
零小节漂移、零"一种语言有 AUTO id 而另一种没有"——并且因为它里面每个数字都能落到一个产物上。

### 增或改引擎代码

```bash
python -m pytest tests/test_<module>.py          # 从这里开始；tests/ 镜像 src/
python -m pytest -q --cov=pokergto --cov-report=term-missing
python -m mypy                                    # src/pokergto 是 strict
python -m ruff check . && python -m ruff format .
```

两条不变量不许倒退，而它们存在都是因为曾经真的坏过：

- `evaluate7` 是一条*被证明过*的快路径，不是定义。游戏的定义——七张牌里最好的五张——是
  `evaluate7_reference`，它单独保留，好在两万块随机牌面上和快路径对账。
- 蒙特卡洛结果自带误差条。一个没有 `stderr` 的数字不是一次测量。

### 增或改求解器结果

在这里，求解器的工作不是普通的代码工作。**一个来自未验证求解器的数字比没有数字更糟**：它是错的，
而且伪装成了数学。`adr/0002` 是完整论证，操作上是：

1. 在 `src/pokergto/solver/games.py` 里加博弈。
2. 在 `src/pokergto/solver/proofs.py` 里登记它，并给出验证锚点——一个闭合形式、一个已发表基准，
   或者一次与独立计算的交叉验证。
3. `python tools/run_solver.py --game <name>` 必须通过全部关卡。`PUBLISHED_PROOFS` 里没有登记的博弈
   不产生产物；引用了未登记博弈的课文不可能到达 `status: ready`。

`python tools/cost_probe.py` 会在一次求解超过运行时或内存预算时让构建失败，这条线阻止"再加一条街"
把项目变成笔记本上跑不动的东西。完整的 6 人桌翻后求解是明确排除的；`adr/0002` 写了代替它算什么、
以及为什么。

## 声明一个范围的来源

在添加任何范围、图表或数字型策略主张之前：**不许使用属于他人的求解器输出或课程内容。** 不抄、不重打、
不从截图描——`NOTICE` 列出了那些工具。这条禁令是机械的而不是客气的：一个写不出合规 `provenance` 的产物
会被 `tools/check_provenance.py` 拒绝，而 `data/src/**` 需要人工签署。

把 `provenance` 块写进 `data/src/` 下的 YAML，然后重新生成。如果诚实的答案是"这是作者为练习自建的一张
参照图，不是一次求解"，就照这么说——`provenance.kind` 有为它准备的取值。如果答案是"我不知道这个数字从哪
来"，那这是你能报告的最有用的事：开一个 **Range provenance** issue，在解决之前，该产物在两种语言里都带
一个可见的 `UNVERIFIED` / 未核验 徽章。一个读者看得见的徽章，比我们谁都守不住的自信数字更有价值。

## 你可以问的问题

> "我大概知道这个局面怎么打，但不知道为什么。教我为。"

这就是 **Derivation request** issue 模板，它是本仓库价值最高的 issue 类型，也永远不会"太基础"。
如果一节课读起来顺但没有说服你，那是一份缺陷报告，不是你的问题。

## 风格，简短版

- 中英文行文遵循 `docs/development/bilingual-style.md`。标识符用英文；人名和缩写不音译。
- 注释解释"为什么"。不要在注释里描述语法，不要复述下一行显然在做什么。
- 提交、代码、文档里不用 emoji。
- Conventional Commits（`feat:`、`fix:`、`docs:`、`test:`、`refactor:`、`chore:`），祈使语气，约 72 字符。

## 开一个 pull request

从 `main` 分叉，保持聚焦，推送前跑完快速回路：

```bash
python -m pytest -q -m "not slow"
python -m ruff check . && python -m mypy
python tools/check_bilingual.py
python tools/inject_doc_tables.py --check
python tools/gen_all.py --check
python -m mkdocs build --strict
```

`pre-commit run --all-files` 在本地镜像这些命令；CI 跑同一批命令作为兜底。

如果某个闸门现在还过不去，在 PR 里写清楚原因，而不是加 `|| true`。一条不可能失败的断言不是断言——
同一条规则既阻止课文引用无法验证的数字，也阻止 CI 引用为了通过而写死的检查。

## 署名

贡献按发布记录在 `CHANGELOG.md` 里署名。
