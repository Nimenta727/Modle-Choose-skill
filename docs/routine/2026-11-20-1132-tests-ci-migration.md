# 2026-11-20 11:32 (+08:00) — 测试与 CI 路径同步 / Align tests and CI paths

## 中文
调整测试脚本的模块导入、安装器引用及 tools/evals/ 数据路径；将 CI 的 compileall、离线评测、受控执行预览命令改用 tools/；更新 .gitignore 和路由策略中的评测路径。

**验证：** 已检查 CI 文件包含新的评测与执行入口。本提交之后等待 GitHub Actions 的实际测试结果，未宣称单元测试已经通过。

**下一步：** 验证远程 CI；完成 README 和 docs 的中英文主题化重构，清除过时文档并加入自动结构校验。

## English
Updated test imports, evaluation fixture paths, installer references, CI compile and smoke commands, .gitignore, and routing-policy links to the new tools/ layout.

**Verification:** Checked workflow text for the new evaluation and runner entrypoints. No unit-test success is claimed before GitHub Actions finishes.

**Next:** Verify CI; replace outdated release-specific guides with bilingual topic docs and add a repository layout test.
