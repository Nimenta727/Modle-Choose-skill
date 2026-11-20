# 架构 / Architecture

## 中文

Model Router 分为三个边界：

1. **独立 Skill（skills/model-router/）**：完整的 SKILL.md、references/ 与 scripts/，可以直接复制到目标项目。该目录**不依赖** tools/，因此在目标项目中仍能运行自身路由脚本。
2. **仓库工具（tools/）**：install.py 负责安装；evals/ 负责离线与可选真实测试；orchestrator/ 负责需要单独许可的本地 CLI 分阶段执行。
3. **测试与文档（tests/、docs/）**：测试保证路径迁移与核心行为；文档按主题双语编写，routine/ 保存不可抹去的历史变更记录。

### 数据流

~~~text
项目任务 JSON → Skill 路由 → 模型分工 JSON / 计划表
                                   ↓ (用户主动选择)
                          tools/orchestrator/prepare.py
                                   ↓ (所有阶段未批准)
                                执行清单
                                   ↓ (默认 dry-run)
                          tools/orchestrator/run.py
                                   ↓ (显式 --execute + 阶段确认)
                         本机 Claude Code / Codex CLI
                                   ↓
                         未验收的阶段结果
                                   ↓ (人工审核)
                               安全交接
~~~

模型目录中的 API ID 不是客户端 CLI 的可用模型别名。路由结果不产生调用权限；真实执行需确认平台、模型和数据共享许可。写入需要单独批准并检查 Git 工作区。CLI 完成不等于验收通过。

### 迁移

此前的 scripts/install.py、evals/ 和 orchestrator/ 已迁移到 tools/。Skill 内的 scripts/ 不变，以维持可移植性；旧的版本文档合并为 docs/guides/。

## English

Model Router has three explicit boundaries:

1. **Standalone Skill (skills/model-router/):** SKILL.md, references/ and scripts/ form a fully portable unit. The installed Skill must **not** depend on tools/ in this repository.
2. **Repository tools (tools/):** install.py copies the Skill; evals/ runs offline and optional client tests; orchestrator/ is a separately authorized local CLI bridge.
3. **Tests and docs (tests/, docs/):** Tests protect behavior and new paths. Topic guides are bilingual; routine/ records historical changes.

### Data flow

~~~text
Task JSON -> portable Skill router -> Allocation JSON / plan
                                         |
                                         v (explicit user choice)
                               tools/orchestrator/prepare.py
                                         |
                                unapproved manifest
                                         |
                                 dry-run (default)
                                         |
                                tools/orchestrator/run.py
                                         |
                              --execute + stage approval
                                         |
                                local Claude / Codex CLI
                                         |
                               unreviewed result
                                         |
                                human-reviewed handoff
~~~

A published API model ID does not guarantee a CLI alias or subscription access. Routing does not grant execution permission; transmitting project context requires authorization. Write stages need extra approval and a clean Git worktree. CLI completion is not acceptance.

### Migration

Host utilities moved from scripts/install.py, evals/ and orchestrator/ to tools/. The portable Skill's scripts/ paths are unchanged. Release-numbered manuals were consolidated into docs/guides/.


## V2.2：状态流与恢复 / Checkpointed State Flow

**中文：** 可选 checkpoint 将 pending → running → cli_completed_unreviewed → accepted/failed 记录在项目目录之外。默认 prepare.py 创建相邻阶段依赖，上游必须由人工接受才允许继续。状态不包含完整提示与模型输出；异常中断保留 running 状态供人工检查，禁止自动重复可能产生副作用的任务。精简交接包只使用人工撰写摘要。

**English:** An optional private checkpoint tracks pending → running → cli_completed_unreviewed → accepted/failed. prepare.py creates sequential dependencies by default; only explicit human acceptance unlocks downstream stages. Interrupted stages stay running pending review, preventing blind replay of side effects. Handoffs use human-authored summaries instead of raw transcripts.

[详细开源方案对照 / Research and design decisions](guides/open-source-patterns.md)
