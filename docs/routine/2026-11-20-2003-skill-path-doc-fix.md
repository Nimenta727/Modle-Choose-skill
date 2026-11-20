# 2026-11-20 20:03 (+08:00) — 修复 Skill 文档路径 / Correct Skill evaluation paths

## 中文
- 在可独立安装的 SKILL.md 中，将仓库级评测工具引用从旧 evals/ 改为 tools/evals/，与 V2.1 目录结构保持一致。
- 本次仅修改文字路径；路由算法、执行权限与模型目录均未改变。

**验证：** 已检查新的 SKILL.md 引用指向 tools/evals/。完整结果以本提交 GitHub Actions 为准，不声称真实登录客户端测试。

**下一步：** Windows 上验证实际客户端 Plan Mode、checkpoint 审批及跨阶段交接的可用性。

## English
- Corrected stale evaluation links in the portable SKILL.md to the current tools/evals/ host paths.
- Documentation-only change; routing logic, execution permissions, and model registry remain unchanged.

**Verification:** Checked text references; final regression status depends on this commit's GitHub Actions. No authenticated client run is claimed.

**Next:** Validate Plan Mode activation, checkpoint review and stage handoffs on authorized Windows CLIs.

---

### 发行归档提示 / Release archive notice (2026-11-20)

中文：这是对应日期的历史记录，原始变更及当时的测试结论继续保留。当前使用方法、安全说明与候选发行信息请查看 [项目首页](../../README.md)、[文档导航](../README.md) 和 [发行指南](../guides/release.md)。模型、价格和客户端支持以各自的最新核实证据为准。

English: This is a preserved historical entry. Original changes and observed checks remain unchanged. Refer to the [README](../../README.md), [documentation](../README.md) and [release guide](../guides/release.md) for the current supported paths and release status. Model data and live client support require separately dated evidence.
