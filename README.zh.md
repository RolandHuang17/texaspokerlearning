# texaspokerlearning —— 双语、可运行的 GTO 第一性原理学院

**别再凭感觉。开始推导。**

一套面向无限注德州扑克的中英双语开放课程，用可推导的原理教现代打法，而不靠背范围表。仓库带一个
Python 引擎（课程里每个数字都由它算出）、一个输出受解析锚点把关的 CFR 求解器，以及一个只读取同一批
数据产物的静态训练器。

[![CI](https://github.com/RolandHuang17/texaspokerlearning/actions/workflows/ci.yml/badge.svg)](https://github.com/RolandHuang17/texaspokerlearning/actions/workflows/ci.yml)
[![Docs](https://github.com/RolandHuang17/texaspokerlearning/actions/workflows/pages.yml/badge.svg)](https://rolandhuang17.github.io/texaspokerlearning/)
[![代码许可：MIT](https://img.shields.io/badge/code-MIT-green)](LICENSE)
[![内容许可：CC BY--SA--4.0](https://img.shields.io/badge/content-CC_BY--SA--4.0-blue)](LICENSE-docs.md)
[![Python：3.11+](https://img.shields.io/badge/python-3.11%2B-informational)](pyproject.toml)

English：[README.md](README.md) · 在线阅读：
<https://rolandhuang17.github.io/texaspokerlearning/>

---

## 这套课程是给谁写的

你懂规则，也打过不少。你知道什么是持续下注、什么是 3-bet，同时心里也清楚：自己的决定多半靠感觉——
这个面"看着"湿润，那个人"像是"封顶了，这波全下"大概"偏薄。你和下一级之间隔着同一件事：这些"看着、
像是、大概"每个都是一个数字，而数字是可以推出来的，不是可以引用的。

本仓库就是为这个转折做的。它不是入门课，也不是技巧清单。

## 整个仓库建立在一条主张上

**这里没有任何断言。这里的一切都可以重算。**

```
src/pokergto/** 算出 -> data/gen/**.json（提交进仓库）-> docs/{en,zh} 与训练器只消费它
```

三条结论你不必相信，可以自己去验：

- **课文里没有一个手打的数字。**所有表格都在 `<!-- BEGIN AUTO:id -->` 标记之间，由
  `tools/inject_doc_tables.py` 填入。`tools/gen_all.py --check` 会重算整棵树，只要有一个字节不同就
  判失败——所以课文里的数字和产出它的代码不可能各说各话。
- **求解器输出必须先被证明，才允许被引用。** Kuhn 扑克的游戏价值解析解是 `-ante/18`；本仓库跑出来是
  `-0.055556`，可剥削度 `1.08e-05` 筹码/手。凡是在 `src/pokergto/solver/proofs.py` 里没有登记的博弈，
  不许生成产物，引用它的课文也不能标 `ready`。这不是形式主义：本求解器真出过一个 bug（把行动概率既折进
  reach 又在外面乘一次），它收敛到可剥削度 `0.89` 且看起来稳得很，只有解析锚点把它抓出来。
- **每条策略主张都写明出处。** `provenance` 是 schema 必填字段，`kind ∈ {derived, reference,
  external}`，`external` 只接受四种许可证。PioSolver、GTO Wizard、GTO+、Upswing 或任何付费课程的
  范围表——抄、手打、截图描摹——全部由校验器拒绝，不靠自觉。既没推导也没许可证的说法，会在页面上以两种
  语言渲染 `未核验` 徽章，而不是塞进脚注。

### 让这套东西不止是"公式合集"的那个闭环

第 02 章从一条等式推出两个闭合形式：你必须防守 `pot/(pot+bet)`，且诈唬必须占下注范围的
`bet/(pot+2bet)`。第 08 章把同一个局面交给 CFR——它并不知道答案。两者在每个尺度上精确吻合：

| 尺度 | 求解器解出的防守 | `pot/(pot+bet)` | 解出的诈唬占比 | `bet/(pot+2bet)` | 可剥削度 |
|---|---|---|---|---|---|
| 1/3 池 | 75.01% | 75.00% | 20.003% | 20.000% | 1.41e-05 |
| 1/2 池 | 66.667% | 66.67% | 25.000% | 25.000% | 9.34e-07 |
| 底池 | 50.01% | 50.00% | 33.337% | 33.333% | 4.33e-05 |

*由 `tools/gen_tables.py` 从 `data/gen/solver/*.json` 生成；同样这张表就是
`table.08-04.solver-vs-algebra`。*

**意义在于**：课程的两半互相验证。代数错，求解器不答应；求解器错，代数不答应。两边都不必被信任。

## 快速上手

```bash
python -m venv .venv && source .venv/bin/activate   # Windows：.venv\Scripts\Activate.ps1
pip install -e ".[dev,docs]"

# 课程里的每个数字，都能在你自己的命令行上复现
PYTHONPATH=src python -m pokergto odds
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2
PYTHONPATH=src python -m pokergto equity AhAs 7d2s --mode exact      # 约 3 分钟：1,712,304 种发牌
PYTHONPATH=src python -m pokergto range "22+,ATs+,KJs+" --lang zh
PYTHONPATH=src python -m pokergto icm --chips 5000,3000,2000 --payouts 6000,3000,1500

python -m pytest -q                                  # 含 2,598,960 手全枚举
python -m mkdocs serve                               # http://127.0.0.1:8000

# 训练器读的就是同一批产物，所以它是被"同步"出来的，不是被配置出来的
python tools/sync_trainer_data.py
cd trainer && npm ci && npm run dev                  # http://localhost:5173/trainer/
```

Windows 与 Anaconda 是一等公民：`setup/install.ps1` 负责引导，`setup/doctor.py` 只读诊断。命令行统一
写 `python -m <工具>`，因为那台机器上 pip 的脚本目录常常不在 `PATH` 里。CLI 会把标准输出重设为
UTF-8，中文课文不会变成乱码。

## 教什么，进度到哪

**15 章、92 节，中英同步成文。**脊柱与每一节的 id 都在 `data/src/curriculum.yaml`，里程碑计划写在
`ROADMAP.md`。下面这张表是结构性的（章节数不会变），可以放心引用：

| 章 | 赛道 | 节数 | 内容 |
|---|---|---|---|
| 00 导论 | 共享 | 3 | 怎么用一套可推导的课程、推导优先于记忆、工具链 |
| 01 组合数学与胜率 | 共享 | 7 | 1326 组合 → 169 类、阻断牌与移除效应、精确胜率与蒙特卡洛、牌型评估器、读 13×13 |
| **02 单次决策的数学** | 共享 | 8 | **推导核心**：回本百分比、底池赔率、MDF、诈唬与价值比例、弃牌赢率、统一 EV 模板、薄价值、尺度不对称 |
| **03 范围优势** | 共享 | 9 | 胜率优势与**坚果优势**之别、封顶范围、牌面结构、SPR 与承诺 |
| **04 下注尺度** | 共享 | 7 | 尺度治理：为什么存在 1/3 池、为什么存在超池、极化与合并、保护与价值之争 |
| 05 翻前（现金） | 现金 | 6 | 开池、大盲防守、3-/4-bet 范围、squeeze、100bb 的后果 |
| 06 翻后（现金） | 现金 | 9 | 按牌面结构定的持续下注频率、过牌加注、float 与 probe、双条、河牌价值与诈唬 |
| 07 多人底池 | 共享、剥削 | 4 | 人数如何改变代数——推导出来的，不是抄来的 |
| 08 简化求解器 | 共享 | 7 | 博弈树与消息集、遗憾匹配、Kuhn 上的 CFR、收敛与可剥削度、CFR+ |
| 09 现金实战与复盘 | 现金、剥削 | 5 | 节点锁定、要计划不要表、复盘流程、漏点审计 |
| 10 单挑 / 按钮位对抗 | 单挑 | 5 | 两人代数、超宽范围、按钮位动力学、如何迁移回满员桌 |
| 11 锦标赛基础 | MTT | 6 | 锦标赛改变了什么、筹码区间、前注、泡沫动力学 |
| 12 ICM 与短码推倒 | MTT | 6 | 两动作模型、Nash 范围、ICM 与筹码 EV、泡沫系数、决赛桌 |
| 13 群体读牌与剥削 | 剥削 | 6 | GTO 在哪里不再正确：如何测量群体、如何偏离而不自毁 |
| 14 综合实战 | 共享 | 4 | 完整闭环、你自己的训练计划、GTO 不会告诉你的部分 |

里程碑 M0–M2 已完成（引擎、数据产物、双语闸门、CI、带证明登记表的求解器）；M3 已完成训练器三块屏与成本预算门，
未完成 Leduc 与 Pages 上线；M4–M5 正在进行。`ROADMAP.md` 记录每章目前写到什么程度。一节课被标成 `ready` 的唯一理由是两种语言都存在且通过配对闸门
——状态是机器判的，不是作者自己说的。

## 这个仓库不会假装是什么

对范围的诚实，本身就是方法的一部分，所以：

- **不做 6 人桌翻后求解器。** 真正能做的是 C++ 加 GPU；一个无法验证的 Python 版本会用代码的权威教错
  东西。能在精确范围内求解的翻前就精确求解，翻后用推导教——这比给你一张无法质疑的表更能教会人。
  见 `adr/0002`。
- **不搬 solver 截图、不抓表、不转录课程。** 见 `NOTICE`。
- **民间说法里那些自信的数字**（持续下注频率从约 65% 塌到个位数、多人价值与诈唬收到 1:6）在本仓库里
  记为 `reference` + 未核验，直到多人模型能从算术里把它们复现出来。`07-01` 会先把独立性假设与牌力移除
  讲清楚，再去碰这类数字。
- **不做实时辅助。** 不接任何牌桌、不解析手牌历史、不在牌局中给建议。用外部工具对付真人对手就是作弊，
  也违反所有牌站条款；本仓库把它排除在外是原则，不是疏漏——见 `SECURITY.md`。

## 目录结构

```
src/pokergto/   引擎：牌、评估器、胜率、范围、赔率、EV、SPR、方差、ICM
  theory/       课文直接引用的可推导原理（胜率优势 vs 坚果优势、频率平衡、多人）
  solver/       博弈树、CFR 与 CFR+、最佳应对与可剥削度、证明登记表
docs/en|zh/     92 节课的骨架，路径与章节逐节镜像；写到几节看 ROADMAP.md，机器口径的计数在
                data/gen/index.zh.json 的 totals 里
data/schema/    JSON Schema —— 所有产物的冻结契约
data/src/       人工编写、需人工签署的 YAML：目前只有 glossary.yaml 与 curriculum.yaml；
                spot / 牌局 / 题库三块要到 M6，不提前伪造
data/gen/       生成、提交、字节确定的数据产物
tools/          生成器与 CI 闸门，含"证明闸门真的会失败"的负向测试
trainer/        静态 Vue 3 + Vite，只消费 data/gen：尺度滑尺、13×13 范围图、求解器观察台
.github/        CI 矩阵、Pages、发布、issue/PR 模板、dependabot
adr/            五条难以逆转的决策，以及它们各自否决掉的方案
```

## 参与

从 [CONTRIBUTING.zh.md](CONTRIBUTING.zh.md) 开始（English：[CONTRIBUTING.md](CONTRIBUTING.md)）。
两条不是"风格偏好"的规则：**数字必须生成**，**课文必须同一 PR 内双语**。你能提的最有用的 issue 是
**求推导**——"这个数字在某处被断言，我看不出它为什么成立"。

三类贡献特别缺：你没被说服的那一步推导；一个可以接上 `theory/*` 从 `reference` 升级成 `derived` 的
产物；一手带决策点与错误代价的实战牌局。

## 许可

- **代码**（`src/**`、`tools/**`、`trainer/**`、`setup/**`、`.github/**`）：[MIT](LICENSE)
- **课程与数据**（`docs/**`、`data/**` 及根目录叙述性文件）：[CC BY-SA 4.0](LICENSE-docs.md)
- **为什么这么拆，以及来源声明的承诺**：[NOTICE](NOTICE)

复用课程内容时请保留 `provenance` 块并写明你改了什么。一个被剥掉来源信息的 derived 或 reference
图表，不构成合规的再分发。

## 点赞固然好，但纠错更有用

发现算术或逻辑错误，请开 issue 或直接提 PR——引擎是权威，所以课文里的错数字就是代码 bug，会按 bug
修。开发过程中已经抓到两个并写进了 `CHANGELOG.md` 和现在的测试：一张被填错了列的 bluff-to-value 表
（把 MDF 那列当成比例列），以及多人防守公式里写成 `N−1` 的指数（推导给出 `1/N`）。

这是一个关于不完全信息游戏的的教学内容。它不构成任何赌博建议，也不承诺任何胜率——它的价值在方法。
