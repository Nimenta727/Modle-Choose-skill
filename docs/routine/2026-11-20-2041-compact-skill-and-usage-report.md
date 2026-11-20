# 2026-11-20 20:41 (+08:00) — 渐进式 Skill 与 Token 报告 / Compact Skill and token usage report

## 中文
- 压缩唯一可移植 SKILL.md 为轻量工作流，优先使用 Python 路由脚本、按需读取 references；保留硬过滤、权限证据与执行审批要求。
- 新增 tools/evals/usage_report.py，从私有 result.json 汇总 CLI 报告的 Token/缓存/可选估算费用，不读取模型回答与原始日志。
- 增加汇总数据缺失与敏感信息剔除测试；更新双语 README、docs 索引及 Token 优化指南。
### 验证
- 本次远程单元/评测结果以 GitHub Actions 为准。没有真实账号 Token A/B 数据，因此不宣称节省百分比。
### 下一步
- 收集同任务真实用量与验收结果，再评估降低成本是否有效。
- 根据真实客户端表现调整交接上限与默认路由模式。

## English
- Slimmed the portable Skill for progressive reference loading; keep hard constraints, access proof and execution authorization.
- Added a numeric-only report reader for private result.json token/cache/client-estimated cost records, never response text.
- Added tests for unknown costs and sensitive data, and updated bilingual README, index and guide.
### Verification
- Consult GitHub CI for this commit. No authenticated matched-task savings data exists yet.
### Next
- Measure real matched tasks and acceptance evidence before declaring savings.
- Tune defaults only after quality and usage observations.

---

### 发行归档提示 / Release archive notice (2026-11-20)

中文：这是对应日期的历史记录，原始变更及当时的测试结论继续保留。当前使用方法、安全说明与候选发行信息请查看 [项目首页](../../README.md)、[文档导航](../README.md) 和 [发行指南](../guides/release.md)。模型、价格和客户端支持以各自的最新核实证据为准。

English: This is a preserved historical entry. Original changes and observed checks remain unchanged. Refer to the [README](../../README.md), [documentation](../README.md) and [release guide](../guides/release.md) for the current supported paths and release status. Model data and live client support require separately dated evidence.
