# 2026-11-19 22:29 (+08:00) — Model Router V1.1 / V1.2 可靠性与模型目录审计

## 中文原始记录 / Chinese original

## 本次修改

### V1.1 — 路由可靠性

- 将模型 API 列表信息标记为 `listed`，与外部成功调用证据 `call-verified` 区分；旧版 `verified` 清单只能降级为列表证据。
- 对调用证据检查 `provider`、`surface` 和 `checked_at`（24 小时有效期）；支持多个供应商清单，拒绝过期、未来日期或缺失来源的记录。
- 在模型筛选中强制使用运行环境 (`api`、`claude_code`、`codex` 等)；非 API 平台缺少明确原生权限时不输出可执行的主模型，而仅给出 `external-conditional` 外部参考。
- 修复省略 `complexity` 与显式 `medium` 产生不同最低能力阈值的问题；增强价格、输入类型、token 等边界检查。只有价格下界的模型不得满足硬性预算上限。
- CLI 支持重复 `--availability-file`、保留结构化审计提示，Plan Mode 表格可显示跨平台非执行建议。

### V1.2 — 数据更新与维护

- 扩展模型 ID 发现规则，支持未来新的 GPT 和 Claude 系列名称（候选需要独立人工审核）。
- 模型目录更新脚本支持 `--inventory-file`、`--report-file`，合并官方网页与账号模型清单的候选，不改写已核实的价格、能力及版本。
- 在模型目录增加字段级来源/核对日期，明确任务适配分是启发式评分。
- 新增每周一模型目录审核 GitHub Actions 工作流；公开文档检查失败时输出离线过期状态，上传审核结果 Artifact，不使用私密 API Key。
- 更新 SKILL、路由策略、计划模板、提供商说明和 README。

## 执行的验证

- `python3 -m unittest discover -s tests -v`：**30 个测试通过**；新增了不同产品 Surface、API 清单与成功调用分离、身份/时效、价格下界、未知模型 ID、Plan Mode 输出格式和工作流契约等测试。
- `python3 -m compileall -q skills/model-router/scripts scripts`：通过。
- `python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format markdown`：生成 5 阶段模型分配示例。
- **尚未验证** Claude Code/Codex 真正 Plan Mode 的自动触发率，也未使用任何 API Key 执行付费模型请求；相关能力不应视为已验证。

## 下一步规划

1. 在真实 Claude Code 与 Codex 项目中分别进行显式触发、隐式 Plan Mode 触发与无关任务不触发的端到端评测。
2. 构建至少 30 个真实任务的基准集，用功能测试、返工次数、成本和延迟修正启发式模型评分。
3. 为 Claude Code/Codex 的模型别名建立显式、可验证的映射配置，不擅自把 API ID 当作 UI 模型 ID。
4. 逐步增加 API 账单/缓存/上下文的成本预测；仅在用户授权并配置独立 Orchestrator 后考虑跨模型自动执行。

## English summary (historical record)

Hardened environment-specific routing, separated API inventory visibility from successful model calls, and improved hard-budget and default-complexity handling. Broadened read-only model discovery and added tests. Next: client activation and empirical evaluation.

**Context:** This is a historical log, not the current installation guide. Paths and commands may have been superseded by tools/ and docs/guides/. The original Chinese text preserves the checks reported at the time.
