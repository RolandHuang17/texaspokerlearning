# GTO 学堂 — 简体中文

这是双语课程中文部分的入口页。英文部分在 [`en/index.md`](../en/index.md)；每一课在两种语言里都占
同一个路径，`docs/zh/<chapter>/<lesson>.md` 与 `docs/en/<chapter>/<lesson>.md` 成对存在。

## 课时导航是生成的，不是手写的

章节与课时清单由 `tools/gen_curriculum_index.py` 从 `data/src/curriculum.yaml` 生成，写入
`data/gen/index.zh.json` 与 `data/gen/nav.yml`（后者由构建钩子 `mkdocs_nav.py` 交给 mkdocs），因此网站的目录与课程骨架不可能
不一致。这一页不手写课时清单：在这里手写一份清单，正是
[adr/0001](https://github.com/RolandHuang17/texaspokerlearning/blob/main/adr/0001-generated-data-artifacts-as-single-source-of-truth.md)
要禁止的那种"凭断言给出的数字"。页面上出现的任何数字——频率、比例、手数——都来自 `data/gen/`，由
`tools/inject_doc_tables.py` 写进 AUTO 区块。

## 读任何一条策略结论之前

每条策略结论都带一个 `provenance` 块，三种来源之一：本仓库推导（`derived`）、本仓库自建且可独立
校验的参考内容（`reference`）、外部来源且已登记许可证（`external`）。三者都不是的内容，会在两种
语言里同时渲染 `UNVERIFIED / 未核验` 标记。规则本身，以及当前仍带标记的结论清单，见
[数据来源与许可](../development/data-provenance.md)。

solver 的输出以证明为门槛，而不是以"看起来合理"为门槛；哪些结论已被验证、以及本项目为何刻意不做
6-max 翻后 solver，见 [solver 证明政策](../development/solver-proof-policy.md)。

## 面向贡献者的工程文档

| 文档 | 解决的问题 |
|---|---|
| [本地开发](../development/local-dev.md) | Windows 上哪些命令真的能跑，哪些会静默失败 |
| [双语规范](../development/bilingual-style.md) | 文件镜像、课时模板、AUTO 区块规则、中英文混排标点 |
| [数据来源与许可](../development/data-provenance.md) | 加一张范围图，但不交付无来源结论的做法 |
| [solver 证明政策](../development/solver-proof-policy.md) | `status: ready` 的依据是什么 |
| [架构决策](../development/adr.md) | ADR-0001 到 ADR-0005，每条一段 |

准备提交之前先看拉取请求检查清单：
[.github/PULL_REQUEST_TEMPLATE.md](https://github.com/RolandHuang17/texaspokerlearning/blob/main/.github/PULL_REQUEST_TEMPLATE.md)。
