# GTO 学堂 / GTO Academy

**中文：[从这里开始](zh/index.md)** · **English: [start here](en/index.md)**

一门双语德州扑克 GTO 课程，其中每一个数字都由仓库里的代码算出来，并带着它的出处。
不抄范围表，不背结论：一个结论如果不能被重新推导，它在这里就被标成 `UNVERIFIED / 未核验`，
两种语言都看得见。

A bilingual Texas Hold'em GTO course in which every number is computed by code in this repository and
carries its provenance. Ranges are not copied and conclusions are not memorised: a claim that cannot be
re-derived is labelled `UNVERIFIED` in both languages, visibly.

## 三条入口 / Three ways in

| | |
|---|---|
| **课程 / Curriculum** | [中文](zh/index.md) · [English](en/index.md) — 15 章 / 92 节，两种语言逐节对齐 |
| **训练器 / Trainer** | <https://rolandhuang17.github.io/texaspokerlearning/trainer/> — 纯静态，只读提交出去的产物，前端不复算扑克数学 |
| **怎么贡献 / Contributing** | [`CONTRIBUTING.md`](https://github.com/RolandHuang17/texaspokerlearning/blob/main/CONTRIBUTING.md) · 决策记录在 [`adr/`](https://github.com/RolandHuang17/texaspokerlearning/tree/main/adr) |

## 这里的东西是怎么来的 / How a number gets here

`src/pokergto/**` 计算，`tools/gen_all.py` 把结果写成 `data/gen/**` 里字节确定的 JSON，**那棵树是提交进仓库的**。
课文里的每个表格都由 `tools/inject_doc_tables.py` 从这些产物渲染进 AUTO 块；手写数字进门禁就红。
采样出来的数（比如翻前全下矩阵）必须自己声明种子、牌面数量、批次和逐格误差棒，
并带着一个批次的摘要，好让每次 push 都能在不重跑全部八分钟的前提下证明引擎没变。

`src/pokergto/**` computes; `tools/gen_all.py` writes the results into byte-deterministic JSON under
`data/gen/**`, and **that tree is committed**. Every table in a lesson is rendered from those artifacts into
an AUTO block, so a hand-typed number fails the build. A sampled number (the preflop all-in matrix, for
instance) has to declare its seed, board count, batches and per-cell standard error, and carries a batch
digest so every push can prove the engine still produces it without re-running all eight minutes of it.

代码 MIT、课程内容 CC BY-SA 4.0；两件事分得开是刻意的，理由见
[`NOTICE`](https://github.com/RolandHuang17/texaspokerlearning/blob/main/NOTICE)。

Code is MIT, curriculum and data are CC BY-SA 4.0, and the split is deliberate — see
[`NOTICE`](https://github.com/RolandHuang17/texaspokerlearning/blob/main/NOTICE).
