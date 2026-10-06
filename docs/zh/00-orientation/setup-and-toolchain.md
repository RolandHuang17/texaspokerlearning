# 装好工具链：命令行、随机种子与确定性输出

<!-- hands: 3 -->
<!-- terms: solver, determinism, generated-artifact, single-source-of-truth, rng-seed, monte-carlo-simulation, standard-error, sample-size, equity, spr, required-equity, minimum-defense-frequency, icm, combos, expected-value -->

## 本节目标 / Objectives

- 把引擎在本机跑起来，并且说清你现在用的是哪一种调用形式（`PYTHONPATH=src python -m pokergto ...` 还是装好之后的 `poker ...`）。
- 复述工具链的两条硬规矩：一律 `python -m <tool>`，以及模拟类结果必须带随机种子。
- 解释为什么同一条命令在两台机器上必须产出逐字节相同的结果，以及这条性质被哪五个实现约定撑着。
- 读得懂标准误与 95% 区间，并能说出什么时候该把样本量往上抬。

## 前置知识 / Prerequisites

- `00-01`：三件东西（教材 / 引擎 / 训练器）的分工，AUTO 表块的来路。
- `00-02`：为什么数字必须能被重算。本节就是把"重算"这件事装到你机器上的那一课。

## 核心原理 / The principle

三条，全部来自实测：

1. **一律 `python -m <tool>`。** `python -m ruff`、`python -m mkdocs`、`python -m pytest`、
   `python -m mypy`、`python -m pre_commit`、`python -m pokergto`。裸名字在这台机器上不存在。
2. **随机种子是数字的一部分。** 报一个模拟出来的胜率，必须同时报 `iterations` 和 `seed`；
   只有前者，那个数就无法被第二个人复现。
3. **确定性输出是门禁的前提。** `tools/gen_all.py --check` 做的事是"重算一遍，逐字节比"。
   只有当输出必然逐字节相同，这条比较才有意义；否则它每天都在红，三天后没人再看。

<!-- provenance: kind=derived verified=true -->
> !!! note "来源 / Provenance"
>     第 1、3 条来自 `docs/development/local-dev.md` 与 `adr/0001`；第 2 条来自 `adr/0001` 的
>     determinism 清单与本仓库 `pokergto.equity` 的实现。三条都在本节算例里被当场跑过。

## 推导 / Derivation

从"我们要让读者自己复核"推到"实现必须做到哪几件事"，中间没有审美。

设一门课引用了 `n` 张表，两种语言就是 `2n` 份副本。复核的方式有两种：读者信我们，或者读者跑一次
生成器对比。第二种要成立，必须满足：**同一份代码 + 同一份输入 ⇒ 同一串字节**。

只要这条性质成立，`--check` 就能当门禁；一旦不成立，`--check` 就退化成每日噪声。
逐字节相同会被四类东西破坏，每一类都有对应的工程约定：

| 破坏源 | 症状 | 本仓库的约定 |
|---|---|---|
| 字典序不稳定 | 同一份数据两次输出键顺序不同 | `json.dump(..., sort_keys=True)` |
| 中文转义 | zh 内容变成 `\uXXXX`，diff 面目全非 | `ensure_ascii=False`，所有文件按 UTF-8 显式读写 |
| 浮点排版漂移 | `0.6666666666666666` 与 `0.667` 混用 | 固定小数位的格式化，`digits` 写在 artifact 里 |
| 时间戳进正文 | 每次生成都全文件变红 | artifact 体内不放时间；只有 `manifest.json` 允许变 |
| 采样随机 | 模拟胜率每次都不同 | 把 seed 存进 artifact，`--check` 连 seed 一起比 |

再加两条不属于数学但会咬人的：`.gitattributes` 强制 `eol=lf`（CRLF 漂移会让逐字节比较当场失败），
以及 Windows 控制台默认用遗留代码页，所以 `pokergto.cli.main` 在打印之前对 stdout/stderr 做
`stream.reconfigure(encoding="utf-8")`——不是让你去改系统设置，是让它自己说对中文。

种子那条同理。模拟的估计量是 `ê = (1/N)ΣXᵢ`，标准误约 `√(ê(1−ê)/N)`，95% 区间大约 `ê ± 1.96 × 标准误`。
下面例 5 会把这三个数当场对给你看。N 翻 4 倍，区间宽度才减半：想要小数点后第三位，代价是样本量。

## 直觉 / Intuition

`python -m` 的意思不是"更正式"，是"用我现在这个解释器去导入那个模块"。它绕开了 PATH 上那堆
谁都能装、谁都不认的脚本目录。你在 Anaconda 里、在 venv 里、在 CI 里，打的都是同一句话，
跑的也都是同一个 Python 真正 import 得到的那份代码。

随机种子的直觉是这样的：模拟不是一个数，是一个随机过程的**一次实现**。种子就是那次实现的名字。
不说名字的模拟结果，跟不写来源的断言一样，只能被相信，不能被检查。

## 算例 / Worked examples

**例 1 — 裸命令在这台机器上不存在。** 实测（Git Bash，仓库根目录）：

```bash
ruff --version
mkdocs --version
poker --version
```

三条都是 `command not found`。换成模块形式：

```bash
python -m ruff --version        # ruff 0.16.10
python -m mkdocs --version      # python -m mkdocs, version 1.6.1 from ...site-packages\mkdocs (Python 3.12)
python -m pytest --version      # pytest 7.4.4
python -m mypy --version        # mypy 1.10.0 (compiled: yes)
```

原因写在 `docs/development/local-dev.md`：`pip` 把控制台脚本装进了
`...\AppData\Roaming\Python\Python312\Scripts`，而这个目录不在 `PATH` 上。
`python setup/doctor.py` 会把这条直接写成一轮 WARN：
`WARN console scripts on PATH ... is NOT on PATH -- use python -m ruff, python -m mkdocs, python -m pytest`。

**例 2 — 装之前，先确认引擎能不能被导入。** 实测：

```bash
python -c "import pokergto"        # ModuleNotFoundError: No module named 'pokergto'
python -m pip show pokergto        # WARNING: Package(s) not found: pokergto
```

也就是这台机器上还没有做过 editable 安装。两条能走的路：

```bash
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2   # 现在就能跑
python -m pip install -e ".[dev,docs]"                                 # 装好后 poker / python -m pokergto 才可用
```

第二种路今天会被一个纯机械问题挡住：`pyproject.toml` 写了 `readme = "README.md"`，而仓库根目录
没有 `README.md`，`python setup/doctor.py` 报的就是
`FAIL pyproject readme ... pip install -e . will fail while building metadata`。
绕过它、并且不动仓库的办法是把元数据构建整个跳过：
`python -m pip install -r requirements-dev.txt`（`requirements-dev.txt` 就是为这条路准备的镜像，
`ci.yml` 里有 job 盯着这两份清单不许分叉）。装好之后 `poker xxx` 才成为 `python -m pokergto xxx`
的缩写。

正确的安装顺序照 `docs/development/local-dev.md` 抄，一条都不许自己发明：

```bash
python -m venv .venv
source .venv/Scripts/activate            # Git Bash；PowerShell 用 .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
python setup/doctor.py                   # 只读体检，失败时非零退出
```

`.python-version` 钉 3.12，`pyproject.toml` 要求 `>=3.11`；本机实测 `python --version` 是 3.12.13。

**例 3 — 输出会把过程打给你看。** 不是只给答案：

```bash
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2
```

```text
bet = 0.500 pot
MDF  = pot/(pot+bet) = 10.000/(10.000+5.000) = 0.6667
     with 2 opponents: d = 1-((bet/(pot+bet))^(1/2)) = 0.4227 each, joint 0.6667 (equals the heads-up MDF)
```

同一句话的中文版：`--lang zh`。它不需要任何系统设置就能打出正确中文，因为 CLI 自己 reconfigure 了
stdout；这一点在 Windows 上是真会咬人的地方，`local-dev` 里记了维护者踩过。

**例 4 — 引擎会拒绝，并告诉你为什么。** 想精确算翻前一个范围对范围的胜率：

```bash
PYTHONPATH=src python -m pokergto equity AA --range-villain "88+,AKs,AQs" --mode exact
```

它不给数，给一条错误：`exact equity needs about 176,729,280 evaluations (2598960 runouts x 68 combos)`，
然后告诉你改走 `mode='mc'` 并接受一个带误差棒的数。**知道工具在什么时候拒绝你，比多用一个子命令重要。**
翻前不是完全不能精确：一手牌对一手牌只要穷举 1,712,304 个 runout（见例 5）。

**例 5 — 逐字节相同，以及误差棒有多大。** 同一条命令跑三次，比较摘要：

```bash
for i in 1 2 3; do PYTHONPATH=src python -m pokergto odds --json | sha256sum; done
```

三次摘要一字不差，都以 `1cbfa6b7456e28ad9d813a338296736b` 开头（完整值以你机器上跑出来的为准）。
带种子的模拟也一样：`equity AhAs 7d2s --iterations 60000 --seed 1 --json` 连跑两次，
摘要完全相同；把 `--seed 1` 换成 `--seed 2`，摘要立刻变了，估计值从 88.43% 变 88.22%。

同一副底牌的精确值：`--mode exact` 给 `equity = 0.881937`，`iterations = 1712304`，`stderr = 0.0`。
对照三次模拟：

| 命令要点 | 点估计 | 标准误 | 95% 区间 |
|---|---|---|---|
| `--iterations 20000 --seed 0`（默认） | 88.04% | ±0.45% | 覆盖 88.19% |
| `--iterations 60000 --seed 1` | 88.4258% | 0.00130605 | [88.1699%, 88.6818%]，覆盖 88.19% |
| `--iterations 60000 --seed 2` | 88.22% | ±0.26% | 覆盖 88.19% |
| `--mode exact` | 88.1937% | 0 | 一个点 |

60,000 次那次偏离精确值 0.2321 个百分点，等于 1.78 个标准误——区间包住真值，点估计却不等于真值。
这就是为什么报数要带区间：默认那 20,000 次的点估计已经偏到 0.15 个百分点，而它自己并不知情。

## 生成表 / Generated tables

三张表都用来支撑上面那句"能重算的都重算"。第一张把口诀和精确值摆在同一行，误差看得见；
第二张是 SPR 那条曲线，第三张是求解器与代数互相核对的结果。

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

<!-- BEGIN AUTO:table.03-07.spr-commitment -->
|  SPR | 全下所需胜率 |
|---:|---:|
| 0.25 |       16.67% |
|  0.5 |       25.00% |
|    1 |       33.33% |
|  1.5 |       37.50% |
|    2 |       40.00% |
|    3 |       42.86% |
|    4 |       44.44% |
|    6 |       46.15% |
|   13 |       48.15% |
|   20 |       48.78% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "来源：本仓库推导 · 已核验 · 置信度 high"
    推导位置：`pokergto.spr#all_in_equity_needed_from_spr`

<!-- generated by: tools/gen_tables.py from pokergto.spr::spr_commitment_table -->
<!-- END AUTO:table.03-07.spr-commitment -->

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

第三张是本节论点的最好证据：左边那一列是 CFR 迭代出来、不知道答案的防守频率与诈唬占比，
右边一列是一行代数给出的同一个量，最后一列是可剥削度。0.5 倍池底那一行里，求解器给 0.666668，
代数给 0.666667，可剥削度 9.3e-07 筹码/手。两个互不知情的过程咬到小数点后第五位，
这才叫"确定性 + 证明"当门禁的样子（`adr/0002`）。

顺带一条本节自己的交叉核对：`spr --stack 78 --pot 13` 命令行给 0.4615，
第二张表 SPR 6.00 那一行也给 46.15%。同一个函数、两条独立通路，对上才是好消息。

## 实战牌局 / Live hands

三局都按"命令行了哪条、拿到什么数、决定是什么、错的打法值多少钱"来写。
EV 用单街近似：全下跟注的期望 = 胜率 ×（底池 + 2 × 风险额）− 风险额。

**牌局 1（`hand.00-03-spr-commitment-fold`）— 现金 6 人桌，3-bet 底池翻牌圈。**
CO 开池 2.2bb，我方 BTN 3-bet 到 6.5bb，CO 补齐；小盲弃牌，底池 13bb。翻牌 `Jd8h4c`，
双方有效筹码 95bb。CO 直接全下。

- 先算深度：`spr --stack 95 --pot 13` → `SPR = 95.0/13.0 = 7.308`，
  `全下所需胜率 = SPR/(1+2*SPR) = 0.4680`。
- 再算手里的：`equity AQo --range-villain "KK+,AKs" --iterations 60000 --seed 1` → 22.00%
  （`wins` 21.21%、`ties` 1.60%，标准误 0.00169127，95% 区间 [21.67%, 22.34%]）。
- 判据：22.00% 对 46.80%。差得不是一点。
- 算术：跟注后的池是 `13 + 95 + 95 = 203`；`0.4680 × 203 = 95.00`，正好等于风险额，
  说明门槛和 EV 式子是同一件事。用 22.00% 代：`0.22 × 203 − 95 = −50.34bb`。
- 决策：弃牌。代价（记忆派："AQ 面对全下总得跟"）：一次性 −50.34bb，半个多买入。
- 种子这条规矩在这里为什么重要：`AQo` 对 `"KK+,AKs"` 翻前不能精确算（例 4 的拒绝），
  所以这个 22.00% 是抽样来的，报出来必须带上 `--iterations 60000 --seed 1`。

**牌局 2（`hand.00-03-icm-chips-versus-money`）— 锦标赛三人剩牌桌。**
筹码 5000 / 3000 / 2000，奖金 6000 / 3000 / 1500。我方是 5000 那个座位，短码 2000 全下，
底池（含 300 盲注）2300，我方要跟 2000，输赢之外还有 3000 留在桌上。我方底牌 `QcJs`（类别 `QJs`）。

- 筹码口径：需要 `2000/4300 = 46.51%`。
- 手里的：`equity QJs --range-villain "22+,A9s+,KTs+,QTs+,AJo+,KQo" --iterations 200000 --seed 1`
  → `equity 0.464533`，`stderr 0.00111522`，95% 区间 [46.2347%, 46.6718%]，`ties` 1.30%。
  同一句用默认 60,000 次跑是 0.466758、区间 [46.2766%, 47.0750%]。
- 第一次读：点估计 46.45% 略低于 46.51%，区间上沿 46.67% 略高于它。也就是说
  **筹码口径下这手牌到底赚不赚，60,000 次和 200,000 次会给不同结论，样本量不够就是不给答案。**
- 钱口径：`icm --chips 5000,3000,2000 --payouts 6000,3000,1500` 给我方 4258.93；
  跟注并且拿下之后 `icm --chips 7000,3000 --payouts 6000,3000` 给 5100.00；
  跟注然后被打掉之后 `icm --chips 3000,3000,4000 --payouts 6000,3000,1500` 给我方 3342.86。
  门槛 `e = (4258.93 − 3342.86)/(5100 − 3342.86) = 916.07/1757.14 = 52.13%`。
- 算术：`0.464533 × 5100 + 0.535467 × 3342.86 = 4159.11`，比弃牌的 4258.93 少 99.82。
  用 60,000 次那个点估计算也是同一个方向（−95.91）。
- 决策：弃牌。这里没有种子之争、没有样本量之争，两个口径的差距（46.51% 对 52.13%）比误差棒大一个量级。
  这条近似要说清：模型把 1.30% 的平分折进胜率里（引擎的胜率定义就是 `P(赢) + ½ · P(平分)`），
  没有为"双方都活着"单独建第三个分支。

**牌局 3（`hand.00-03-rule-of-four-flip`）— 现金局，翻牌圈，深度刚好 SPR = 6。**
底池 13bb，双方各剩 78bb，我方在翻牌圈拿到 12 张干净补牌（同花听牌 + 卡张顺）。

- 深度：`spr --stack 78 --pot 13` → `SPR = 6.000`，全下所需胜率 `0.4615`。
  `table.03-07.spr-commitment` 的 SPR 6.00 那一行同样给 46.15%。
- 近似：口诀"补牌 × 4"给 12 × 4 = 48.00%。
- 精确：`table.01-03.draw-probability-exact-vs-rule` 的 12 补牌那一行给两张之内命中 44.96%
  （同表 9 补牌那一行：精确 34.97% 对 口诀 36.00%；6 补牌：24.14% 对 24.00%）。
- 判据在这里翻面：44.96% < 46.15% < 48.00%。**口诀说可以全下，精确值说不可以。**
- 算术：跟注/全下后的池是 `13 + 78 + 78 = 169`。真值 44.96% → `0.4496 × 169 − 78 = −2.02bb`；
  口诀承诺的是 `0.48 × 169 − 78 = +3.12bb`。误差不是四舍五入的问题，是符号的问题。
- 决策：不要拿近似值去做接近门槛的决定。近似只在离门槛很远的时候够用——本节例 5 那张表
  给出的正是"多远"的量化办法。

## 范围图 / Range chart

导论课不发范围图；这一课的产出是一条能跑的命令，不是一张范围。策略课里 `tools/gen_ranges.py`
会生成 `range.*` 图，而工具链在这里的角色是：**每张图都自带它的可复现信息**。
例如 `data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json` 里有 `orientation` 字段
（`akqjt98765432-desc-diagonal-pairs-upper-suited`）和 `checks` 数组
（两条都 `pass: true`：每格组合数只能是 4/6/12；频率落在 [0,1] 内）。
也就是说一张图不光有数字，还有"数字必须满足什么"的自检记录。想自己在终端看一张网格，
用 `PYTHONPATH=src python -m pokergto range "22+,ATs+" --lang zh`（`00-01` 例 4 干过这件事）。

## 为何成立、何时失效 / Why it works, when it breaks

**`python -m` 这条路失效的时候**：你在一个连解释器都没激活的 shell 里。
先 `python -c "import sys; print(sys.executable)"` 确认自己站在哪个 Python 上，再谈其他。

**确定性这条性质失效的时候**，也都是可指出的：

1. 采样类结论本来就不该逐字节相同——除非带上 seed。`--seed` 缺省是 0，写进 artifact 才有意义。
2. 精确翻前不可行（例 4 的那条错误）。这时你拿到的是估计量，必须连带区间一起报。
3. `python tools/gen_all.py --check` 现在是逐字节比对、且不改工作区——这两点它以前都做不到。
   manifest 曾经记录生成它所在的 commit、Python 版本与 numpy 版本，于是"被比对的文件"里写着"它来自哪次
   提交"：任何一次提交之后再做比对都只能失败。现在这些信息打到构建日志里
   （`built by python 3.12.13, numpy 1.26, git …`），已提交的 manifest 只装内容。第 01-04 节讲的是同一件
   事（种子要写进产物，采样口径不要）：来源该放在能被读到的地方，而不是塞进被哈希的东西里。
4. 本机状态会漂。本节写这一课时实测 `python -m ruff check . --no-cache` 剩 2 条 N817，
   而 `local-dev` 记的历史快照是 335 条——数字属于快照，命令不属于。想知道现在什么样，跑它。
5. 测试数量同样是快照。写这一节时 `python -m pytest -q -m "not slow"` 报 87 passed、约 19 秒；
   别信正文，问机器：`python -m pytest --collect-only -q | tail -1`。课文里引用的计数和引用一个耗时
   是同一类东西——写下来那一刻为真，而且从来不是重点。

## 陷阱 / Common mistakes

1. **照着别的平台的文档敲裸命令。** `mkdocs build`、`pytest`、`ruff check .` 在这里全部找不到。
   *代价*：一个下午花在"为什么我装了却不能用"上，最后发现脚本目录不在 `PATH`。
   先跑 `python setup/doctor.py`，它会明说。
2. **报模拟结果不带 `iterations` 和 `seed`。** *代价*：例 5 里 60,000 次 seed 1 得 88.43%，
   seed 2 得 88.22%，两者都自称 88% 量级；不带种子，下一位读者重跑得到一个"不一样但都对"的数，
   然后开始怀疑整套工具。而 `--check` 之所以能当门禁，全靠种子被钉住。
3. **拿小数点后第三位的模拟值去判一个边际决定。** *代价*：牌局 2 里 60,000 与 200,000 次的点估计
   跨过 46.51% 的门槛给了不同脸色，而真实答案（离 52.13% 的钱口径门槛还远）根本没在问这个问题。
   样本量 ×4，区间宽度才 ÷2；要精度就加样本，或者改走 `--mode exact`。
4. **把近似口诀用在门槛附近。** *代价*：牌局 3 的 +3.12bb 变 −2.02bb。
   `table.01-03.draw-probability-exact-vs-rule` 存在的理由就是把 3.04 个百分点的差标出来
   （12 补牌：精确 44.96% 对 口诀 48.00%）。

## 练习 / Drills

- 从零开始：`python -m venv .venv` → 激活 → `python -m pip install -r requirements-dev.txt` →
  `python setup/doctor.py`，把报告里的每一条 WARN/FAIL 抄下来，并说出各自的原因。
- 跑三次 `PYTHONPATH=src python -m pokergto range "22+,ATs+" --json | sha256sum`，
  再改 `--iterations`（例如 `equity` 那条）跑一次，比较摘要变化与不变化各说明什么。
- 用 `equity AhAs 7d2s` 分别在 20,000 / 60,000 / 200,000 次下取点估计与区间，
  再跑 `--mode exact` 拿真值，检查真值落在几个区间里、点估计偏了几个标准误。
- 跑 `spr --stack 78 --pot 13` 与 `python -m pokergto equity QJs --range-villain ...` 那两条牌局命令，
  把牌局 3 的 −2.02bb 自己重算一遍。
- 打开 `data/gen/manifest.json`，说明它为什么只装*内容*（文件摘要与版本号），而生成它的 python、numpy 与 commit sha 被写进了构建日志。这两类信息里，哪一类会让 `gen_all --check` 出问题？在什么情况下出问题？

## 自测清单 / Self-check

- [ ] 我知道这台机器上要用 `python -m <tool>`，并能说出为什么。
- [ ] 我能在没做 editable 安装时，用 `PYTHONPATH=src` 把引擎跑起来。
- [ ] 我能解释 `--lang zh` 为什么不需要改系统编码设置就能出正确中文。
- [ ] 我能说出确定性输出的五个实现约定，以及它和 `--check` 门禁的因果关系。
- [ ] 我报模拟数时会带上样本量和随机种子，并能用标准误判断该不该加样本。
- [ ] 我知道引擎会在什么时候拒绝我（翻前精确、五张牌面），以及拒绝信息该怎么读。

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
本节所有数字与命令输出都是我在仓库根目录（Windows 11 + Git Bash，Python 3.12.13）实测得到的。
全课未引用任何商业求解器或付费课程的内容。

| 内容 | 来源类型 | 位置 |
|---|---|---|
| `python -m` 约定、PATH 与 Scripts 目录、UTF-8 故事 | 已验证的工程记录 | `docs/development/local-dev.md`，以及本节的 `ruff`/`poker` 实测输出 |
| 工具版本（ruff 0.16.10、mypy 1.10.0、pytest 7.4.4、mkdocs 1.6.1、node v20.15.1、pre-commit 4.6.2） | 实测 | `python -m <tool> --version`，`python setup/doctor.py` |
| `pip install -e .` 今天会失败（缺 `README.md`） | 实测 FAIL | `python setup/doctor.py` 里那条 `FAIL pyproject readme`；`pyproject.toml` 的 `readme` 字段 |
| 确定性（同命令同摘要） | 实测 | `odds --json` 三次摘要一致；`equity ... --seed 1` 两次一致、`--seed 2` 不同 |
| 88.1937% 精确值，1,712,304 个 runout | `derived` | `equity AhAs 7d2s --mode exact`；`src/pokergto/equity.py` |
| 22.00%、0.464533、0.466758 及其区间 | `derived` | `equity ... --iterations N --seed 1`，摘要见上表 |
| SPR 7.308 / 6.000 与门槛 0.4680 / 0.4615 | `derived` | `pokergto spr`；`src/pokergto/spr.py#all_in_equity_needed_from_spr` |
| ICM 4258.93 / 5100.00 / 3342.86 | `derived` | `pokergto icm` 三次调用；`src/pokergto/icm.py#icm` |
| 求解器 0.666668 对代数 0.666667、可剥削度 9.3e-07 | `derived` | `data/gen/tables/table.08-04.solver-vs-algebra.json`；门禁在 `src/pokergto/solver/proofs.py` |
| `gen_all.py --check` 的两处已知问题 | 已验证状态（工程侧） | `docs/development/local-dev.md`；本节只做复述，未修改那个文件 |
| CFR 与证明作为门禁的必要性 | 决策 | `adr/0002`；数字来自本仓库自己的求解器 |

## 术语 / Terms

<!-- terms: solver, determinism, generated-artifact, single-source-of-truth, rng-seed, monte-carlo-simulation, standard-error, sample-size, equity, spr, required-equity, minimum-defense-frequency, icm, combos, expected-value -->

| 缩写 | 中文 | English | 本课里的意思 |
|---|---|---|---|
| — | 求解器 | solver | 本仓库自己实现的 CFR，不是牌桌辅助工具 |
| — | 确定性输出 | determinism | 同输入必同字节，比"可重复"更强 |
| — | 生成物 | generated artifact | `data/gen/**` 下的 JSON，机器所有，不许手改 |
| — | 唯一数据源 | single source of truth | 每个数字只在一处计算，其他地方引用 |
| — | 随机种子 | random seed | 那次抽样实现的名称，必须与结果同报 |
| — | 蒙特卡洛模拟 | Monte Carlo simulation | 抽样估出来的数，带误差棒 |
| — | 标准误 | standard error | 估计量的散布，本课用它判断样本量够不够 |
| — | 样本量 | sample size | 次数；×4 才让区间宽度 ÷2 |
| — | 胜率 | equity | `P(赢) + ½ · P(平分)`，不是纯赢率 |
| SPR | 筹码底池比 | stack-to-pot ratio | 全下门槛式里的 `S/P` |
| — | 所需胜率 | equity needed to call | 跟注那条线的另一副面孔 |
| MDF | 最低防守频率 | minimum defense frequency | 由同一条等式推出的范围配额 |
| ICM | 独立筹码模型 | independent chip model | 把筹码折成钱的那个模型 |
| — | 组合数 | combos | 加权单位，本课用它核对 `checks` 自检 |
| EV | 期望值 | expected value | 牌局里"错的打法值多少钱"的那个单位 |
