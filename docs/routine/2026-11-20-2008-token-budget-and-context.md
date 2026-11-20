# 2026-11-20 20:08 (+08:00) — Token 预算与上下文按需加载 / Prompt budgets and context-on-demand

## 中文

### 代码修改
- 引入 tools/orchestrator/token_budget.py：默认阶段提示词上限 6000 字符、交接上限 1500 字符、Claude 最多 6 轮；支持逐阶段显式调高，但禁止无限制值。
- 调度器生成和执行前统一检查真实提示词大小。超额**直接阻止执行**，绝不默默删掉用户要求或人工审核过的交接内容。
- 可选 context_files 提供最多 8 个仓库相对文件路径提示，避免把整个文件内容重复塞给多个模型；拒绝目录穿越、环境文件和明显的敏感目录。
- dry-run 输出提示词长度及粗略 Token 估算，记录预算元数据。该估算不是供应商 Tokenizer 或真实账单。
- Claude Code 的最大轮次从固定 8 改为按阶段配置（默认 6）；Codex CLI 不具备统一的该标志，**不宣称 Codex 轮次上限**。
- 未改变默认不执行、阶段审批、写权限与跨供应商共享许可。

### 验证
- 代码提交时以 GitHub Actions 的远程结果为准；真实 Claude/Codex 模型调用和费用对比尚未开展。

### 下一步
1. 为 budgets、路径白名单、超限阻断和 CLI 参数增加测试并跑 CI。
2. 增加可选的模型连续性路由与跳转次数报告。
3. 在真实环境记录用量指标，客观验证节省而不是声称固定百分比。

## English

### Changes
- Introduced an enforceable per-stage prompt character budget (default 6,000), handoff cap (1,500), and Claude Code max-turns setting (default 6).
- Budget checks fail closed before execution; user instructions and approved handoffs are **never silently truncated**.
- Optional context_files passes up to eight repo-relative path hints instead of copying whole source files; path traversal and obvious secret locations are blocked.
- Dry-run reports a labeled heuristic token estimate, not provider tokenizer usage or billed costs.
- Claude Code turn cap is configurable; no unsupported Codex turn-limit guarantee is claimed.
- Existing explicit execution approvals and provider-sharing controls remain intact.

### Verification
- Await GitHub Actions; no real authenticated model calls or measured cost savings are claimed.

### Next steps
1. Add safety/CLI regression tests and verify CI.
2. Implement opt-in model continuity to reduce unnecessary vendor/model handoffs.
3. Collect real usage and billing metrics on approved tasks.
