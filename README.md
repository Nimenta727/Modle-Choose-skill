# Model Router — 智能模型选择与受控执行 / Intelligent Model Routing

> 中文：一个用于 Claude Code / Codex 的可移植 Agent Skill，为开发计划分配合适的模型，并提供**可选、需逐阶段授权**的本地执行器。  
> English: A portable Agent Skill that assigns appropriate models in software plans, with an **optional, explicitly approved** local Claude Code / Codex runner.

**状态 / Status:** V2.1 repository consolidation. Offline policy tests and dry-run tools are implemented. Actual authenticated cross-provider runs, activation rates and empirical model rankings remain **unverified**. / 已实现离线路由与预览工具，真实登录客户端的执行、自动触发率与实测模型排名仍待验证。

## 中文

### 功能及边界

- **智能推荐**：按当前平台、权限证据、任务复杂度、成本和工具能力筛选主选与备用模型，给出推荐原因与模型目录时间。
- **计划集成**：安装 Skill 后，引导 AI 在 Plan Mode 中添加模型分工；是否真正自动触发取决于具体工具，尚无真实客户端数据。
- **受控执行**：将路由结果转为默认未批准的分阶段清单。默认只预览；真实执行必须先安装登录 CLI、确认实际模型名称并明确批准每个阶段。
- **评测与交接**：支持离线策略测试、真实任务记录、人工审核校准、API 标价成本估算和待填写的交接文档。
- **限制**：路由建议不等于执行许可；API 模型列表不等于成功调用；仅有模拟测试不能证明真实 CLI 可用。不会自动推送、部署或跨供应商传输完整日志。

### 项目结构

~~~text
skills/model-router/       可独立安装的 Skill、规则、模型目录及脚本
tools/install.py           项目 Skill 安装器
tools/evals/               离线评测与可选 CLI 实测工具
tools/orchestrator/        需要人工授权的本地执行调度器
tests/                     单元、结构和文档验证
docs/                      双语索引、架构说明和按主题分类的指南
docs/routine/              按时间记录的修改日志，保留历史
.github/workflows/         CI 和只读目录审计
~~~

### 快速开始

要求 Python 3.10+；本仓库代码仅使用 Python 标准库。在仓库根目录执行：

~~~bash
# 安装到你的项目
python3 tools/install.py --target /path/to/project

# 模型建议（不调用模型）
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format markdown

# 离线测试
python3 tools/evals/evaluate_routes.py
python3 -m unittest discover -s tests -v

# 创建未批准执行清单，随后仅预览
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format json > routing-result.json
python3 tools/orchestrator/prepare.py --task-file skills/model-router/examples/project-plan.json --route-file routing-result.json --output local-execution.json
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace . --all
~~~

在 Windows PowerShell 中可把 python3 换成 py -3。执行真实模型任务必须遵循 [执行指南](docs/guides/execution.md)，可能消耗 API 额度或订阅用量。**默认预览命令不会发起模型请求。**

### 当前有效文档

[文档索引](docs/README.md) · [架构说明](docs/architecture.md) · [安装与使用](docs/guides/setup.md) · [执行与安全](docs/guides/execution.md) · [模型评测](docs/guides/evaluation.md) · [成本与校准](docs/guides/calibration.md) · [模型目录维护](docs/guides/catalog.md) · [修改日志](docs/routine/README.md)

**迁移说明**：旧的 scripts/install.py、evals/、orchestrator/ 入口已迁移到 tools/；docs/v1.4.md、docs/v2.0-execution.md、docs/evaluation.md 已合并为主题指南并删除。独立 Skill 内的 scripts/ **保留原路径**，历史 routine 日志保留。

## English

### Capabilities and boundaries

- **Recommendations:** Filter by execution surface, model access evidence, complexity, budget and capabilities. Show primary/backup choices, rationale and registry verification age.
- **Plan integration:** Installed Skills can instruct Plan Mode to include a model allocation table. Automatic activation has not been measured on authenticated clients.
- **Supervised execution:** Convert a routing result into an initially unapproved stage manifest. Preview is the default. A live stage requires a locally installed/authenticated CLI, an explicit CLI model and per-stage approval.
- **Evaluation and handoff:** Offline policy contracts, opt-in real-task records, human-reviewed calibration, list-price API reference estimates and blank handoff templates.
- **Limitations:** Recommendations are not permissions. API inventory is not a successful request, and simulated adapter tests do not prove client availability. No automatic git push, deployment or unrestricted cross-provider transcript sharing.

### Layout

~~~text
skills/model-router/       Standalone installable Skill and model registry
tools/install.py           Installer for consuming projects
tools/evals/               Policy evaluation and optional real CLI probes
tools/orchestrator/        Supervised local stage runner
tests/                     Unit, layout and documentation checks
docs/                      Bilingual index, architecture and topic guides
docs/routine/              Preserved dated change history
.github/workflows/         CI and read-only catalog review
~~~

### Quick start

Python 3.10+ and the standard library suffice. From the repository root:

~~~bash
python3 tools/install.py --target /path/to/project
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format markdown
python3 tools/evals/evaluate_routes.py
python3 -m unittest discover -s tests -v

# Generate an unapproved manifest, then preview with zero model calls
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format json > routing-result.json
python3 tools/orchestrator/prepare.py --task-file skills/model-router/examples/project-plan.json --route-file routing-result.json --output local-execution.json
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace . --all
~~~

On Windows use py -3 in place of python3. Live execution may consume credits or subscription usage and requires [explicit approval](docs/guides/execution.md).

### Documentation

[Documentation index](docs/README.md) · [Architecture](docs/architecture.md) · [Setup](docs/guides/setup.md) · [Execution & safety](docs/guides/execution.md) · [Evaluation](docs/guides/evaluation.md) · [Calibration & costs](docs/guides/calibration.md) · [Catalog](docs/guides/catalog.md) · [Change history](docs/routine/README.md)

**Migration:** Repository utilities moved from scripts/install.py, evals/ and orchestrator/ into tools/. Former version-numbered docs were consolidated under docs/guides/ and deleted. Portable Skill scripts remain at the same paths; historical routine logs are retained.

## 官方来源 / Official Sources

[OpenAI model docs](https://developers.openai.com/api/docs/models) · [Anthropic model docs](https://platform.claude.com/docs/en/models/overview) · [Claude Code Skills](https://code.claude.com/docs/en/skills) · [Codex Skills](https://developers.openai.com/codex/skills)

The model registry has its own verification date; editing these docs does not refresh model metadata. / 文档更新时间并不代表模型数据已实时核实。


## V2.2：开源设计改进 / Open-source-inspired Improvements

**中文：** 已参考 LiteLLM、LangGraph、Aider、AutoGen、Claude Code Subagents 和 OpenHands 的公开设计，为可选执行器增加了阶段 checkpoint、依赖人工验收、显式重试上限与人工精简交接包。保持默认 dry-run 和逐阶段批准；不会因为 CLI 返回成功就自动把阶段当作验收通过。完整比较见 [开源设计对照](docs/guides/open-source-patterns.md)，使用方法见 [受控执行指南](docs/guides/execution.md)。

**English:** Drawing on public patterns from LiteLLM, LangGraph, Aider, AutoGen, Claude Code and OpenHands, the optional runner now supports manifest-bound checkpoints, acceptance-gated dependencies, bounded explicitly approved retries and human-authored compact handoffs. Dry-run remains the default; a successful CLI exit is never automatic acceptance. See [research and tradeoffs](docs/guides/open-source-patterns.md) and the [supervised execution guide](docs/guides/execution.md).
