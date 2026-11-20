# 2026-11-20 11:30 (+08:00) — 迁移仓库级工具 / Move repository utilities

## 中文
将仓库级安装器由 scripts/install.py 迁入 tools/install.py；评测代码和数据迁入 tools/evals/；受控执行器迁入 tools/orchestrator/。Skill 内的 scripts/ 不移动，以保持独立安装兼容。旧路径已移除；仅修改代码中的相对根目录与安装器位置。

**验证：** 此提交仅完成文件路径迁移，尚未运行更新后的完整测试；下一提交立即同步修改 tests/、CI 以及文档。此记录不宣称 CI 通过。

**下一步：** 更新所有导入与 CLI 路径、运行 CI、合并双语文档。

## English
Relocated the repository installer to tools/install.py, evaluation code and fixtures to tools/evals/, and the supervised CLI runner to tools/orchestrator/. Standalone Skill scripts stay at their existing paths. The old source paths were removed; runtime root and installer references were updated.

**Verification:** This is a staged path migration. Tests and workflow paths have **not** yet been updated in this commit; no CI success is claimed.

**Next:** Update test imports, CI commands and bilingual docs; run the complete pipeline.
