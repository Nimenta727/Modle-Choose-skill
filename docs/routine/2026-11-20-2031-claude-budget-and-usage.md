# 2026-11-20 20:31 (+08:00) — 可选费用保护与真实用量字段 / Optional cost guard and observed usage fields

## 中文
- 为单阶段 token_budget 新增可选 max_claude_cost_usd（$0.01–$500），校验数值后透传官方 Claude Code --max-budget-usd 参数。
- 它是客户端估算费用的停止条件，可超额，**不是账单硬上限**；不适用于 Codex，也不保证不同版本的一致行为。
- 仅从真实 Claude CLI JSON 结果提取非负、有限的输入/输出/缓存 Token 字段与总费用估算，不保存原始调试内容，不填造缺失数据。
- 增加费用参数、无效值、Codex 不继承和 CLI 字段白名单测试；更新双语文档。

**验证：** 以本次 GitHub Actions CI 结果为准；当前未运行真实账号模型，也没有真实 Token 节省比例。

**下一步：** 使用相同任务、同等验收要求进行真实用量对比；根据质量与实际费用决定预算默认值。

## English
- Added an optional per-stage max_claude_cost_usd setting ($0.01–$500) that passes Claude Code's documented --max-budget-usd flag.
- This limits **client-estimated** spend and may overshoot; it is not a guaranteed bill ceiling and does not apply to Codex.
- Extracts only numeric usage fields actually returned in Claude CLI JSON without storing raw debug traces or filling missing data.
- Added unit tests and bilingual operational documentation.

**Verification:** Refer to this commit's GitHub Actions. No authenticated real-task costs or savings have been measured.

**Next:** Compare repeated matched tasks with acceptance evidence and actual reported usage before tuning defaults.
