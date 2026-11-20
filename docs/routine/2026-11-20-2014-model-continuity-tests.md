# 2026-11-20 20:14 (+08:00) — 连续性策略与回归测试 / Model continuity and token tests

## 中文

### 修改
- 增加可选 `minimize_switches` 连续性偏好；前一模型仅在满足全部原有硬约束、同一权限等级、评分不落后超过 0–10 分容差的情况下继续使用。
- 路由结果增加模型切换计数与策略状态；不开启选项时维持原路由排序。
- 调度器在创建输出目录和检查 CLI 之前检查提示词预算，超额拒绝执行。
- 增加 16 项离线测试覆盖提示词、交接、敏感路径、Claude 最大轮次及连续性风险门槛。

### 验证与限制
- 本提交完成后，CI 实测结果应从对应 GitHub Actions 检查；未实测真实模型账单，不宣称节省固定比例。

### 下一步
- 发布中英文 Token 优化指南、示例任务与更新后的 Skill 说明。
- 测量真实任务的 Token 计量和任务质量，优化上下文预算。

## English

### Changes
- Added opt-in model continuity bounded by the original hard filters, identical access confidence and a small adjustable score gap.
- Added reported model-switch count with unchanged default routing behavior.
- Moved prompt budget preflight ahead of run directory creation and CLI lookup.
- Added 16 offline tests for budget caps, path hints, Claude turn limit and continuity safety.

### Verification and limits
- Check the corresponding GitHub Actions run for observed CI results. No real provider billing or savings percentage was measured.

### Next
- Publish bilingual token-efficiency documentation and sample tasks.
- Collect matched model usage and acceptance evidence before tuning policy.

---

### 发行归档提示 / Release archive notice (2026-11-20)

中文：这是对应日期的历史记录，原始变更及当时的测试结论继续保留。当前使用方法、安全说明与候选发行信息请查看 [项目首页](../../README.md)、[文档导航](../README.md) 和 [发行指南](../guides/release.md)。模型、价格和客户端支持以各自的最新核实证据为准。

English: This is a preserved historical entry. Original changes and observed checks remain unchanged. Refer to the [README](../../README.md), [documentation](../README.md) and [release guide](../guides/release.md) for the current supported paths and release status. Model data and live client support require separately dated evidence.
