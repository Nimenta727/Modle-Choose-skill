# Model Router — 智能模型路由 / Intelligent Model Routing

> **v2.3.0-rc.1 — Release Candidate / 候选发行版**  
> 一个轻量、可独立安装的 Agent Skill：为软件开发计划分配模型，并提供需单独授权的 Claude Code / Codex 执行工具。  
> A lightweight, standalone Agent Skill for assigning models to software-development stages, with a separately authorized Claude Code / Codex execution bridge.

**状态 / Status:** 离线单元测试和策略评测是当前验证范围；真实登录客户端的跨模型执行、触发率和 Token 节省百分比**尚无实测证明**。 / Offline tests and routing contracts are the verified scope; authenticated cross-model execution, activation rates and percentage token savings remain **unmeasured**.

## 中文

### 主要能力

- **分阶段路由**：先检查运行平台、可用性、功能、上下文、风险和预算，再选择主选/备用模型。能力分数属于启发式策略，并非第三方基准测试。
- **Token 节省策略**：Skill 精简、按需读取参考、路径提示而不是重复粘贴全文、阶段提示词与交接字符限制、可选模型连续性、可观察的 CLI 用量统计。
- **人工监督执行**：`tools/orchestrator/` 可选；生成的执行清单默认未批准，运行器默认仅预览。调用真实模型需要逐阶段批准、指定当前 CLI 可用模型和 `--execute`。写入与跨供应商交接需要额外授权。
- **评测与审计**：离线策略契约、可选真实客户端测试、阶段状态记录、最小化交接、参考成本估算和只读模型目录审计。

### 安装（克隆源码）

要求 **Python 3.10+**，本仓库工具仅使用标准库。在仓库根目录执行：

```bash
python3 tools/install.py --target /path/to/your-project
# 只安装 Claude Code / Claude Code only
python3 tools/install.py --target /path/to/your-project --agents claude
# 只安装 Codex / Codex only
python3 tools/install.py --target /path/to/your-project --agents codex
```

安装器默认不会覆盖已有 Skill。Windows PowerShell 可使用 `py -3` 替换 `python3`。如果使用 GitHub Release 的独立 ZIP，解压后将 `model-router/` 复制到项目 `.agents/skills/` 或 `.claude/skills/`；ZIP **不含**仓库级执行器。

### 快速体验（不消费模型额度）

```bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/token-efficient-plan.json --format markdown
python3 tools/evals/evaluate_routes.py
python3 -m unittest discover -s tests -v
```

默认执行器预览：

```bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format json > routing-result.json
python3 tools/orchestrator/prepare.py --task-file skills/model-router/examples/project-plan.json --route-file routing-result.json --output local-execution.json
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace . --all
```

**这三条命令只规划和预览，不会调用模型。** 不要把账号密钥、私有模型对话或包含私密代码的任务清单提交到公开仓库。

### 文档与发行

[文档索引](docs/README.md) · [架构](docs/architecture.md) · [安装指南](docs/guides/setup.md) · [执行与安全](docs/guides/execution.md) · [Token 优化](docs/guides/token-efficiency.md) · [评测](docs/guides/evaluation.md) · [发行说明](docs/guides/release.md) · [修改历史](docs/routine/README.md)

**发行资产**：`model-router-skill-v2.3.0-rc.1.zip`、同名 `.sha256` 校验文件和中英文 Release Notes。建议先试用候选版，再根据真实 Claude Code/Codex 运行结果决定正式稳定版。

## English

### Capabilities

- **Stage-aware routing:** Apply hard execution-surface, entitlement, feature, context, risk and budget constraints before proposing primary/backup models. Scores are heuristics, **not empirical benchmarks**.
- **Token efficiency:** Compact Skill instructions, progressive reference loading, file-path hints instead of full source reposting, prompt/handoff character caps, opt-in model continuity and numeric CLI usage reports.
- **Supervised execution:** Optional `tools/orchestrator/` bridge. Manifests are unapproved by default; the runner previews without model calls. Live stages require explicit model choice, approval and `--execute`. Writes and cross-provider handoffs need further consent.
- **Evaluation:** Offline policy tests, optional authenticated-client probes, checkpoints, reviewed handoffs, reference cost estimates and read-only model catalog audits.

### Install from source

Requires **Python 3.10+**, using only the standard library. From the checkout root:

```bash
python3 tools/install.py --target /path/to/your-project
python3 tools/install.py --target /path/to/your-project --agents claude
python3 tools/install.py --target /path/to/your-project --agents codex
```

Existing Skills are not silently overwritten. On Windows use `py -3`. Alternatively, extract the standalone Release ZIP and copy `model-router/` to a consuming project's `.agents/skills/` or `.claude/skills/`. The ZIP deliberately excludes host-side orchestration tools.

### Zero-cost offline quick start

```bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/token-efficient-plan.json --format markdown
python3 tools/evals/evaluate_routes.py
python3 -m unittest discover -s tests -v
```

For an unapproved **dry-run-only** execution preview:

```bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format json > routing-result.json
python3 tools/orchestrator/prepare.py --task-file skills/model-router/examples/project-plan.json --route-file routing-result.json --output local-execution.json
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace . --all
```

These commands do **not** call paid models. Never commit credentials, private chat traces or sensitive project manifests to a public repository.

### Documentation and releases

[Documentation index](docs/README.md) · [Architecture](docs/architecture.md) · [Setup](docs/guides/setup.md) · [Execution and safety](docs/guides/execution.md) · [Token efficiency](docs/guides/token-efficiency.md) · [Evaluation](docs/guides/evaluation.md) · [Release guide](docs/guides/release.md) · [History](docs/routine/README.md)

**Release assets:** `model-router-skill-v2.3.0-rc.1.zip` with a separate SHA-256 checksum and bilingual notes. This is a **release candidate**, not a claim of production-proven authenticated CLI integration.

## 代码结构 / Repository Layout

```text
skills/model-router/       Portable Skill, routing scripts and model snapshot
tools/install.py           Local project installer
tools/orchestrator/        Optional supervised CLI and checkpoints
tools/evals/               Offline and opt-in live evaluation tools
tools/package_release.py  Reproducible standalone Skill ZIP
tools/check_docs.py        Bilingual/link preflight
release/                   Version metadata and release notes
docs/guides/               Bilingual topic guides
docs/routine/              Historical records, preserved and indexed
tests/                     Unit and release tests
.github/workflows/         CI, audit and gated release publication
```

## 版权与使用 / Licensing and Use

本项目现采用 **Apache License 2.0（2004 年 1 月）** 开源。允许在遵守许可证条件的情况下使用、修改和再分发；分发时请保留许可证和适用的版权/归属声明，并标明修改。完整英文原文见 [LICENSE](LICENSE)，SPDX 标识为 `Apache-2.0`。中文说明不是官方法律文本。 / This project is licensed under the **Apache License, Version 2.0 (January 2004)**. Use, modification and redistribution are permitted subject to its conditions, including license and applicable notice retention and marking changed files. See the authoritative English [LICENSE](LICENSE); SPDX: `Apache-2.0`.

供应商模型与价格快照有独立核实日期；本次发行不会将其自动刷新为当前事实。 / Provider model and pricing snapshots retain their own review dates; publishing a new release does not refresh those facts.
