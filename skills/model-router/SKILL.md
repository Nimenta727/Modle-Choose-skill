---
name: model-router
description: >-
  Use before software implementation plans or Plan Mode to recommend current
  OpenAI GPT and Anthropic Claude models for each task stage. Apply hard
  constraints, cost and availability, explain primary/backup selection,
  and reduce needless model switching. Recommendation is not execution.
---

# Model Router — 计划模式模型分配 / Plan Mode Allocation

## 中文：轻量执行流程

1. 确认目标、开发阶段、实际运行环境（API / Claude Code / Codex）、任务风险、预算和账号可用权限。公开 API 模型 ID 不等于当前客户端可选模型。
2. **优先调用本 Skill 的 scripts/route.py**，让 Python 读取模型目录和策略数据；不要每次在模型上下文中全部展开 JSON、路由策略、供应商说明。只有无法运行脚本，或需要解释特殊约束时，才按需读取 references/routing-policy.md 与 references/model-registry.json。
3. 先过滤能力、上下文、平台、权限、安全和预算等硬条件，再按质量/成本/速度启发式排序。成本优先可设置 priority: cost；可选 minimize_switches: true 降低跨阶段模型切换，但不放宽任何硬条件。
4. 在技术开发计划中加入**紧凑的 Model allocation / 模型分配**：阶段、交付物、主选 ID、备用 ID、推理等级、理由、访问状态、模型目录核实时间、失败切换条件。没有验证的原生模型应注明不可直接执行，不要复述整个模型注册表。
5. 阶段交接只保留已确认决策、必要输入、验收证据和未解决问题，不重复传输全量对话、源码或工具日志。成本估算与 Token 粗估都不是实际账单。
6. **边界**：本 Skill 不调用模型、不擅自切换供应商或花费额度。真实执行必须另行由用户批准并使用仓库级 tools/orchestrator/。没有实测配对数据不得宣称 Token 节省率或模型质量排名。

## English: Progressive Disclosure

1. Identify actual execution surface, planned deliverables, risk, budget and verified native model access. Published API IDs do not prove client entitlements.
2. **Prefer scripts/route.py** to inspect policy/registry in Python. **Do not preload every large reference into the agent context.** Read references/routing-policy.md and references/model-registry.json only when scripts cannot run or a constraint needs manual interpretation.
3. Apply hard gates first, then heuristic quality/cost/speed ranking. Optional priority: cost and minimize_switches: true may reduce excess expense or handoffs; never bypass platform, risk or access restrictions.
4. Add a **compact Model allocation / 模型分配** section to the original technical plan, with primary/backup IDs, effort, rationale, access confidence, catalog date and rerouting criteria.
5. Handoff only reviewed decisions, artifacts, validation and unresolved risks. Avoid transcripts, repetitive source dumps and fabricated usage numbers.
6. This Skill gives recommendations, not execution permission. Live CLI runs require separate user approval. No unmeasured savings or benchmark claims.

## Portable CLI / 独立运行

~~~bash
# Paths relative to the installed Skill directory
python3 scripts/route.py --task-file examples/project-plan.json --format markdown
python3 scripts/route.py --task-file examples/project-plan.json --format json
python3 scripts/update_models.py --offline
python3 scripts/handoff.py --task-file examples/project-plan.json
~~~

**按需参考 / On-demand references:** references/routing-policy.md, references/plan-template.md, references/model-registry.json, references/providers.md. Additional bilingual guidance in the source repository: docs/guides/token-efficiency.md and docs/guides/execution.md. Model metadata can become stale; availability must be checked on the actual execution surface. / 目录数据与账号权限必须分别核实。
