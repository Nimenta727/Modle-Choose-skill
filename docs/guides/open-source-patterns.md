# 开源设计借鉴与技术选择 / Open-Source Design Patterns

## 中文：2026-11-20 调研

我们研究了公开文档及 GitHub 实现中的成熟做法，优先**借鉴设计理念而不是引入整个框架**。本项目仍只依赖 Python 标准库；原有可安装 Skill 和模型推荐脚本保持独立。

| 项目 | 成熟实践 | Model Router 的具体改进 | 暂不采用 |
|---|---|---|---|
| [LiteLLM](https://docs.litellm.ai/docs/router/learn/reliability) | 按错误类型处理重试、回退、冷却，考虑预算 | 失败后显式批准重试，并限制尝试次数 | 未授权的自动跨厂商回退、Redis 网关 |
| [LangGraph](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/interrupts.mdx) | Checkpoint、人工 interrupt 和断点恢复 | 本地阶段状态、人工接受后解锁依赖 | 自动重放可能已产生副作用的步骤 |
| [Aider](https://aider.chat/docs/usage/modes.html) | Architect 与 Editor 的模型职责分离 | 原有分阶段模型选择和职责约束 | 复制完整编辑器或其代码 |
| [AutoGen](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html) | 明确的交接与终止条件 | 上游验收门槛、有界重试 | 无限制 Agent 群聊 |
| [Claude Code Subagents](https://claude.com/resources/articles/steering-claude-code-skills-hooks-rules-subagents-and-more) | 独立上下文、只传递所需摘要 | 人工编写的简短交接包 | 自动传输跨厂商原始日志 |
| [OpenHands](https://github.com/OpenHands/docs/blob/main/sdk/arch/agent.mdx) | 按步骤推进与事件驱动可观测性 | 最少量阶段元数据，不保留原始轨迹 | 常驻服务器、数据库或事件总线 |

### 已实现

**阶段 Checkpoint**：新增 tools/orchestrator/checkpoints.py，管理 pending → running → cli_completed_unreviewed → accepted（或 failed）。只有人工审核后的 accepted 才满足依赖条件。状态文件关联 manifest SHA-256，不保存原始提示和完整响应，采用原子替换与独占锁，避免并发写入。中断后出现 running 时，需要**人工核实副作用**，程序不会自动重新执行。

**受控调度**：prepare.py 默认生成顺序 depends_on；run.py 新增可选 --checkpoint-file 和 --retry-failed。已完成但未验收的阶段不能重复执行或直接解锁下一阶段；失败只有在明确重试时继续，每个 Checkpoint 最多两次尝试。不会自动切供应商，也不自动消费模型额度。

**最小化交接**：handoff_packet.py 只接受人工确认的阶段和单独撰写、上限 3000 字符的摘要；产生独立 JSON 交接包，默认 stdout，不会自动发给下一厂商。共享时仍需要 run.py 的 --handoff-file 和 --allow-handoff-share。

### 安全及验证边界

- 这次只借鉴公开架构思路，不直接复制第三方源码，不添加上述框架作为依赖。
- SHA-256 用于关联文件和审核备注，**不构成身份认证、防篡改证明或自动验收**。
- 一次 CLI 退出成功不等于业务需求已经通过测试；人工批准只是操作者声明。
- 目前没有真实 Claude Code/Codex 账号调用、实测 Token 节省率或可信模型质量排名。
- 本功能为**可选的受控执行增强**；默认 dry-run、独立 Skill 以及原有路由命令仍保持兼容。

## English: research and implementation (2026-11-20)

We compared public documentation and open-source design patterns, then adopted **small auditable ideas rather than wholesale framework dependencies**. The project remains stdlib-only and keeps its portable routing Skill intact.

| Project | Inspiration | Applied here | Deferred |
|---|---|---|---|
| [LiteLLM](https://docs.litellm.ai/docs/router/learn/reliability) | Retries, fallback, cooldown and budget awareness | Explicit bounded retries | Proxy, Redis, automatic vendor switching |
| [LangGraph](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/interrupts.mdx) | Durable checkpoints and human interrupts | Manifest-bound stage state and acceptance gates | Replay of potentially side-effecting steps |
| [Aider](https://aider.chat/docs/usage/modes.html) | Architect/editor model separation | Stage-level model specialization | Reimplementing the editing engine |
| [AutoGen](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html) | Explicit termination and handoff rules | Dependency acceptance and bounded retries | Unbounded group chat |
| [Claude Code](https://claude.com/resources/articles/steering-claude-code-skills-hooks-rules-subagents-and-more) | Isolated subagents returning concise summaries | Human-authored compact handoffs | Silent cross-provider raw transcript transfer |
| [OpenHands](https://github.com/OpenHands/docs/blob/main/sdk/arch/agent.mdx) | Step-driven event observability | Minimal checkpoint metadata | Database-backed event infrastructure |

### Delivered

- tools/orchestrator/checkpoints.py: pending, running, cli_completed_unreviewed, accepted and failed states; SHA-256 manifest binding, atomically replaced private metadata, exclusive writer lock and explicit human acceptance. A running stage after a crash is **not** blindly replayed.
- tools/orchestrator/prepare.py adds sequential depends_on by default. tools/orchestrator/run.py supports optional --checkpoint-file and --retry-failed. Unreviewed CLI completion does not unlock a dependent stage; retries need operator consent and stop after two attempts.
- tools/orchestrator/handoff_packet.py builds a compact, independent JSON packet from a human-accepted stage and a **separately human-authored** summary. It does not transmit that packet; cross-provider sharing still requires explicit approval.

### Limits

No third-party source was copied and no new runtime dependency was introduced. SHA-256 is an artifact linkage mechanism, **not** proof of authenticated review or tamper resistance. CLI completion does not prove task acceptance. Actual authenticated client operation, measured token savings and model-quality rankings remain unverified. Default dry-run and older routing commands remain compatible.
