# 版本变更 / Changelog

## 中文

### v2.3.0-rc.2 — Apache-2.0 开源许可

- 正式采用 Apache License 2.0（2004 年 1 月），添加根目录及可移植 Skill 的完整英文 LICENSE。
- 更新 README、贡献指南、发行说明与校验测试；新的 rc.2 发行包内附许可证。
- 旧的 rc.1 Release 和历史 routine 记录不改写。


### v2.3.0-rc.1 — 整理与候选发行

- 采用稳定的 `skills/`、`tools/`、`docs/` 和 `tests/` 结构，保留独立可安装的 Skill。
- 增加可复现 ZIP、SHA-256、发行元数据、文档链接/双语检查和 GitHub Release 自动化发布门槛。
- 整理中英文 README、安装、执行、Token 优化和发行指南，保留并索引所有历史 routine 日志。
- 发行范围依然是离线测试验证；真实跨模型客户端没有被认证为生产可用。

### 历史概览

- **V2.2**：检查点与人工审核状态、最小化交接包和 Token 预算/模型连续性。
- **V2.0**：受控的本机 Claude Code/Codex 执行工具；默认 dry-run，需逐阶段批准。
- **V1.4**：基于真实任务的校准提议、API 参考成本、阶段交接模板。
- **V1.3**：离线路由策略评测与可选真实客户端触发测试工具。
- **V1.1–V1.2**：运行平台可用性区分与模型目录只读维护。
- **V1.0**：基础 Model Router Skill、模型目录和确定性分工建议。

原始变更证据保存在 [docs/routine/](docs/routine/README.md)；历史记录不代表当前代码路径和客户端可用性。

## English

### v2.3.0-rc.2 — Apache-2.0 licensing

- Adopted the Apache License, Version 2.0 (January 2004), with the full English LICENSE at the repository root and in the standalone Skill.
- Updated README, contributor guidance, release notes and archive tests; the rc.2 ZIP includes the license.
- Preserved the prior rc.1 Release and dated historical records without rewriting them.


### v2.3.0-rc.1 — Consolidation and release candidate

- Stabilized the `skills/`, `tools/`, `docs/` and `tests/` layout while preserving a standalone installable Skill.
- Added reproducible ZIP packaging, SHA-256, version metadata, bilingual link checks and gated GitHub Release publishing.
- Consolidated bilingual README and guides and preserved/indexed historical routine logs.
- The release remains validated for offline functionality only; authenticated cross-model production behavior is not claimed.

### Earlier milestones

- **V2.2:** Checkpoints, human acceptance, compact handoffs, token budgets and model continuity.
- **V2.0:** Supervised Claude Code/Codex runner, dry-run by default and staged approvals.
- **V1.4:** Real-trial calibration proposals, reference API costs and blank handoff templates.
- **V1.3:** Offline routing contracts and optional client activation test harness.
- **V1.1–V1.2:** Surface-aware access evidence and read-only catalog maintenance.
- **V1.0:** Portable Skill, model snapshot and deterministic model recommendations.

The original change records remain under [docs/routine/](docs/routine/README.md). Historical claims and paths are not equivalent to current client support.
