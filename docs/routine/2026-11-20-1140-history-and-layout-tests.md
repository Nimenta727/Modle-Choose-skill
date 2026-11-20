# 2026-11-20 11:40 (+08:00) — 补全双语历史与结构校验 / Bilingual history and layout checks

## 中文

### 修改
- 保留 2026-11-19 的全部六份历史 routine 原始中文记录，并逐份补充英文摘要与过时路径说明。
- 更新 Claude Code / Codex 的轻量 Skill 发现入口，增加中英文使用提示与新的安装器路径。
- 补充 tests/test_repository_layout.py，验证新工具结构、旧路径删除、主要文档的双语章节及 CI 配置。
- 修复远程 CI 报告的一处遗漏：试验数据参数由 evals/trials.json 改为 tools/evals/trials.json。

### 验证
- 上一轮远程 CI 显示 Python 单元测试、离线路由评测与 CLI dry-run 通过，但试验汇总因旧路径失败；本轮已定位并修复，最终结果须以本提交触发的 CI 为准。
- 本地无已登录的 Claude Code / Codex CLI，不宣称完成真实账号任务。

### 下一步
1. 确认完整 CI 通过，再检查主要双语文档的链接和路径。
2. 在 Windows 主机进行授权的 CLI 端到端运行，收集真实触发数据。
3. 按实际反馈继续完善多模型阶段验收与恢复策略。

## English

### Changes
- Preserved six historical Chinese routine records and appended individual English summaries and migration caveats.
- Updated repository-level Claude Code / Codex discovery wrappers with bilingual usage notes and the relocated installer path.
- Added offline layout tests for the new tools structure, removed paths, bilingual docs and CI command locations.
- Fixed an observed CI regression: the real-trial data argument now uses tools/evals/trials.json.

### Verification
- The prior CI run passed unit tests, offline policy checks and CLI dry-run, but failed the trial-score step due to that stale path. This commit fixes the cause; final status depends on this commit's GitHub Actions result.
- Authenticated Claude Code/Codex end-to-end execution was not available and is **not** claimed.

### Next steps
1. Verify full CI and current documentation links.
2. Run explicitly authorized tests on Windows clients and gather observed activation data.
3. Improve stage-level acceptance and recovery based on measured experience.

---

### 发行归档提示 / Release archive notice (2026-11-20)

中文：这是对应日期的历史记录，原始变更及当时的测试结论继续保留。当前使用方法、安全说明与候选发行信息请查看 [项目首页](../../README.md)、[文档导航](../README.md) 和 [发行指南](../guides/release.md)。模型、价格和客户端支持以各自的最新核实证据为准。

English: This is a preserved historical entry. Original changes and observed checks remain unchanged. Refer to the [README](../../README.md), [documentation](../README.md) and [release guide](../guides/release.md) for the current supported paths and release status. Model data and live client support require separately dated evidence.
