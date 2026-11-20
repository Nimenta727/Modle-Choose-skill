# 2026-11-19 23:43 (+08:00) — V2.0 受控跨模型 CLI 执行器 MVP

## 中文原始记录 / Chinese original

## 本次做了什么

- 增加 `orchestrator/prepare.py`，把现有 `route.py --format json` 的阶段推荐转换为**待审核、未授权**的执行清单。源于 `external-conditional` 的跨平台建议也必须人工确认后才能运行。
- 增加 `orchestrator/run.py`，以无 shell 注入的参数数组，在本机分阶段调用已安装的 Claude Code 或 Codex CLI。支持单阶段确认和批量逐阶段交互式审批。
- 为 Claude 设置 Plan/acceptEdits 权限及工具限制；为 Codex 设置 read-only/workspace-write 沙箱；禁止在执行器内使用 bypass / danger-full-access 模式。
- 默认 dry-run；只有 `--execute`、阶段自身的 `approved: true`、明确的 `cli_model`、单阶段 `--confirm-stage` 或批量 TTY 逐阶段确认同时满足时才可能调用模型。写模式额外要求 `--allow-write` 和干净 Git 工作区。
- 结果输出到独立的私有目录，保留最小成功/失败状态与待审核的模型回复，不持久化原始 CLI 事件轨迹。任何先前阶段的交接内容必须经人工审核并以 `--allow-handoff-share` 显式允许，不能自动跨供应商传送。
- 更新 `README.md`、核心 `SKILL.md`、`.gitignore` 和 GitHub CI；新增完整说明 `docs/v2.0-execution.md`。

## 验证结果

- `python -m unittest discover -s tests -q`：**88/88 通过**（既有 69 项 + 本次 19 项）。
- `python -m compileall -q skills/model-router/scripts scripts evals orchestrator`：**通过**。
- `python evals/evaluate_routes.py --json-out ...`：**24/24 场景、186/186 断言通过**。
- `route.py --format json` → `prepare.py --output` → `run.py --all`：**离线 dry-run 通过**；五阶段均显示未获授权、未配置 CLI 模型，未实际调用任何提供商。
- 新增伪造 CLI 输出的正/负测试（包括超时、拒绝、无权限和敏感日志不写入），不需要真实用户凭据。
- **尚未测试真实已登录 Claude Code/Codex 的执行成功率、费用或 Agent 沙箱边界**。不能将离线测试解读为实际跨模型任务成功。

## 使用限制和设计决策

- 此版是**受控本地执行 MVP**，不是全自动跨供应商 Agent 网络；Skill 规划模式不会自动执行付费模型调用。
- 它不会自动给代码打验收通过标记、执行 Git push/commit、部署服务、自动批准修改或发送未经审核的上一阶段日志。
- 将项目交给某个 CLI 本身可能使该供应商接触项目内容，必须由用户先确认授权和隐私要求。
- CLI flags 和模型别名会随着供应商版本变化，实际使用前必须在目标电脑检查。

## 下一步规划

1. 在用户已登录的 Windows 机器分别运行 Claude Code/Codex，只对非机密示例项目执行首个只读阶段，收集成功/失败与版本差异。
2. 为本地执行添加更严格的实际任务验收钩子、受限代码工作树、明确的成本/时间限额和中断恢复机制；不要绕过供应商原生沙箱。
3. 基于真实实验结果修正阶段路由与 CLI 模型名映射；继续保留需要审批的跨供应商交接机制。
4. 如用户希望无人值守全自动执行，再单独设计权限策略、费用封顶、审计与更强的运行环境隔离，经过验证后再推出。

## English summary (historical record)

Added a supervised local Claude Code/Codex execution bridge. New manifests are unapproved, preview-only by default; real stages, writes, and cross-provider handoffs require explicit consent. Offline adapter tests were recorded; authenticated end-to-end testing remained pending.

**Context:** This is a historical log, not the current installation guide. Paths and commands may have been superseded by tools/ and docs/guides/. The original Chinese text preserves the checks reported at the time.

---

### 发行归档提示 / Release archive notice (2026-11-20)

中文：这是对应日期的历史记录，保留原始内容和当时的验证边界。当前安装、目录结构与安全要求，请查看 [项目首页](../../README.md)、[最新文档](../README.md) 和 [发行指南](../guides/release.md)。新版本不改变本记录在当时所述事实。

English: This is a preserved historical record, including the evidence available at its original date. For supported paths, current safety requirements and packaging, see the [README](../../README.md), [documentation index](../README.md) and [release guide](../guides/release.md). This notice does not retroactively change historical test claims.
