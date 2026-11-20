# 2026-11-20 11:32 (+08:00) — 测试与 CI 路径同步 / Align tests and CI paths

## 中文
调整测试脚本的模块导入、安装器引用及 tools/evals/ 数据路径；将 CI 的 compileall、离线评测、受控执行预览命令改用 tools/；更新 .gitignore 和路由策略中的评测路径。

**验证：** 已检查 CI 文件包含新的评测与执行入口。本提交之后等待 GitHub Actions 的实际测试结果，未宣称单元测试已经通过。

**下一步：** 验证远程 CI；完成 README 和 docs 的中英文主题化重构，清除过时文档并加入自动结构校验。

## English
Updated test imports, evaluation fixture paths, installer references, CI compile and smoke commands, .gitignore, and routing-policy links to the new tools/ layout.

**Verification:** Checked workflow text for the new evaluation and runner entrypoints. No unit-test success is claimed before GitHub Actions finishes.

**Next:** Verify CI; replace outdated release-specific guides with bilingual topic docs and add a repository layout test.

---

### 发行归档提示 / Release archive notice (2026-11-20)

中文：这是对应日期的历史记录，保留原始内容和当时的验证边界。当前安装、目录结构与安全要求，请查看 [项目首页](../../README.md)、[最新文档](../README.md) 和 [发行指南](../guides/release.md)。新版本不改变本记录在当时所述事实。

English: This is a preserved historical record, including the evidence available at its original date. For supported paths, current safety requirements and packaging, see the [README](../../README.md), [documentation index](../README.md) and [release guide](../guides/release.md). This notice does not retroactively change historical test claims.
