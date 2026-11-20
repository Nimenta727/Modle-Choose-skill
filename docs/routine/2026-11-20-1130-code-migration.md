# 2026-11-20 11:30 (+08:00) — 迁移仓库级工具 / Move repository utilities

## 中文
将仓库级安装器由 scripts/install.py 迁入 tools/install.py；评测代码和数据迁入 tools/evals/；受控执行器迁入 tools/orchestrator/。Skill 内的 scripts/ 不移动，以保持独立安装兼容。旧路径已移除；仅修改代码中的相对根目录与安装器位置。

**验证：** 此提交仅完成文件路径迁移，尚未运行更新后的完整测试；下一提交立即同步修改 tests/、CI 以及文档。此记录不宣称 CI 通过。

**下一步：** 更新所有导入与 CLI 路径、运行 CI、合并双语文档。

## English
Relocated the repository installer to tools/install.py, evaluation code and fixtures to tools/evals/, and the supervised CLI runner to tools/orchestrator/. Standalone Skill scripts stay at their existing paths. The old source paths were removed; runtime root and installer references were updated.

**Verification:** This is a staged path migration. Tests and workflow paths have **not** yet been updated in this commit; no CI success is claimed.

**Next:** Update test imports, CI commands and bilingual docs; run the complete pipeline.

---

### 发行归档提示 / Release archive notice (2026-11-20)

中文：这是对应日期的历史记录，保留原始内容和当时的验证边界。当前安装、目录结构与安全要求，请查看 [项目首页](../../README.md)、[最新文档](../README.md) 和 [发行指南](../guides/release.md)。新版本不改变本记录在当时所述事实。

English: This is a preserved historical record, including the evidence available at its original date. For supported paths, current safety requirements and packaging, see the [README](../../README.md), [documentation index](../README.md) and [release guide](../guides/release.md). This notice does not retroactively change historical test claims.
