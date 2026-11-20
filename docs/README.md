# 文档导航 / Documentation Index

## 中文

本目录存放当前有效的**中英文双语**文档，按主题维护，避免多个版本的重复说明。以下链接均从本文件所在目录出发。

| 文档 | 内容 |
|---|---|
| [架构](architecture.md) | 源码职责、目录边界、数据流 |
| [安装与模型路由](guides/setup.md) | 安装、配置、推荐命令 |
| [执行与安全](guides/execution.md) | CLI 调度、审批、写入与交接 |
| [评测](guides/evaluation.md) | 离线契约、真实触发和真实任务验证 |
| [校准与成本](guides/calibration.md) | 配对证据、API 成本、交接模板 |
| [目录维护](guides/catalog.md) | 来源、数据时效与只读审计 |
| [变更历史](routine/README.md) | 保留每次修改的日志与下一步规划 |

旧的 docs/v1.4.md、docs/v2.0-execution.md、docs/evaluation.md 已并入主题指南并删除。历史日志中的旧命令仅供追溯。

## English

Current **bilingual** documentation is organized by topic rather than release number.

| Guide | Purpose |
|---|---|
| [Architecture](architecture.md) | Source boundaries and data flow |
| [Setup and routing](guides/setup.md) | Install, configure and route |
| [Execution and safety](guides/execution.md) | CLI approvals, writes and handoffs |
| [Evaluation](guides/evaluation.md) | Policy tests, live activation and task outcomes |
| [Calibration and cost](guides/calibration.md) | Matched evidence, API references and handoffs |
| [Catalog maintenance](guides/catalog.md) | Model provenance and read-only audits |
| [Change history](routine/README.md) | Dated change records and next steps |

Former docs/v1.4.md, docs/v2.0-execution.md and docs/evaluation.md have been consolidated and removed. Historical commands are archival.


## 新增专题 / New research guide

- [开源方案对照与设计取舍 / Open-source patterns and tradeoffs](guides/open-source-patterns.md) — LiteLLM、LangGraph、Aider、AutoGen、Claude Code、OpenHands：哪些设计已采纳、哪些还不应引入。 / What was adopted and deliberately left out.
