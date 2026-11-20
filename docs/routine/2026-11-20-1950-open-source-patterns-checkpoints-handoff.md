# 2026-11-20 19:50 (+08:00) — 开源经验借鉴与状态恢复 / Open-source-inspired checkpoints and concise handoffs

## 中文

### 修改内容
- 调研 LiteLLM、LangGraph、Aider、AutoGen、Claude Code Subagents 和 OpenHands，整理路由、人工中断、任务分工、终止条件及上下文隔离模式，记录来源和不引入完整框架的理由。
- 新增 tools/orchestrator/checkpoints.py：manifest 指纹、私有状态文件、原子更新、独占锁、阶段依赖、人工验收/拒绝、最多两次显式尝试。
- tools/orchestrator/prepare.py 增加顺序依赖；tools/orchestrator/run.py 增加可选 --checkpoint-file 与 --retry-failed。CLI 成功仅标记“待审核”，中断后不自动重放。
- 新增 tools/orchestrator/handoff_packet.py：从已接受阶段和人工摘要生成紧凑 JSON 交接包，默认不写文件也不传输数据。
- 新增回归测试，更新 README、执行指南、架构及双语调研文档，扩展 CI 的无模型调用烟雾检查。

### 验证
- 本地 33 项调度器离线模拟测试通过（原有 19 项 + 新增 14 项）；完整仓库的最终 CI 结果需以远程工作流为准。
- 没有使用真实 Claude Code/Codex 账号进行 CLI 调用，也没有真实 Token 节省或模型质量数据。
- SHA-256 仅用于数据关联而非签名认证；中断阶段可能有副作用，不能盲目重试。

### 下一步规划
1. Windows 环境只读阶段的真实 CLI 测试，记录版本、权限和正确性。
2. 对比精简交接与完整历史的 Token、延迟和任务验收结果。
3. 如有必要，增加手动审核的模型健康与冷却策略，绝不默认跨厂商自动回退。

## English

### Changes
- Researched LiteLLM, LangGraph, Aider, AutoGen, Claude Code Subagents and OpenHands for routing reliability, durable state, human interrupts, specialist roles, termination and context isolation. Documented sources and why heavyweight frameworks were not imported.
- Added tools/orchestrator/checkpoints.py for manifest fingerprinting, atomic private state, single-writer locks, dependency checks, human acceptance/rejection and a two-attempt cap.
- Updated prepare.py with sequential dependencies and run.py with optional checkpoint and retry gates. CLI success remains unreviewed and interrupted side effects are not replayed.
- Added handoff_packet.py for human-authored concise handoffs; no automatic data transfer.
- Added offline tests, bilingual docs and CI no-call smoke checks.

### Verification
- Local offline orchestrator suite: 33 passing tests (19 existing plus 14 new). Full-repository validation depends on the final remote CI.
- No actual authenticated CLI execution or real usage/model-quality measurement was conducted.
- SHA-256 is artifact linkage, not authenticated or tamper-proof review.

### Next steps
1. Validate an approved read-only stage with installed Windows CLIs.
2. Measure context, latency and acceptance for concise handoffs.
3. Consider explicitly approved cooldown rules only after real observations.

---

### 发行归档提示 / Release archive notice (2026-11-20)

中文：这是对应日期的历史记录，原始变更及当时的测试结论继续保留。当前使用方法、安全说明与候选发行信息请查看 [项目首页](../../README.md)、[文档导航](../README.md) 和 [发行指南](../guides/release.md)。模型、价格和客户端支持以各自的最新核实证据为准。

English: This is a preserved historical entry. Original changes and observed checks remain unchanged. Refer to the [README](../../README.md), [documentation](../README.md) and [release guide](../guides/release.md) for the current supported paths and release status. Model data and live client support require separately dated evidence.
