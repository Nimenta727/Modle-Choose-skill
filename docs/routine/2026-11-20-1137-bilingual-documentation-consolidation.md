# 2026-11-20 11:37 (+08:00) — 合并双语文档 / Consolidate bilingual documentation

## 中文

### 修改
- 重写 README.md，以中英文说明产品定位、可用功能、限制、快速使用和新目录。
- 新增 docs/README.md、docs/architecture.md 与 docs/guides/{setup,execution,evaluation,calibration,catalog}.md。
- 将旧的版本说明及评测 rubric 中的有效内容迁移到双语主题指南，删除 docs/v1.4.md、docs/v2.0-execution.md、docs/evaluation.md、evals/quality_rubric.md 的旧副本。
- 同步更新 AGENTS.md、CLAUDE.md、Skill 主入口及参考文档；保留所有历史 routine 日志。

### 验证
- 文档使用相对链接指向当前指南；本提交尚未在真实登录的 Claude Code/Codex 运行代码，离线/CI 结果以 GitHub Actions 为准。

### 下一步
- 为历史日志补齐英文摘要；增加自动检查，避免未来出现旧路径和单语文档。
- 检查 GitHub Actions 全部测试与模拟执行结果。

## English

### Changes
- Rewrote README.md in Chinese and English with product scope, limitations, setup, and the new repository layout.
- Added bilingual docs index, architecture, setup, execution, evaluation, calibration and catalog guides.
- Migrated useful content from older version-numbered guides and the evaluation rubric, then deleted their obsolete copies.
- Updated AGENTS.md, CLAUDE.md and canonical Skill references; preserved dated routine history.

### Verification
- Documentation uses relative links to current guides. No authenticated Claude Code/Codex client was executed here; offline and CI checks must be confirmed on GitHub Actions.

### Next
- Add English summaries to historical routine logs; enforce bilingual documentation and current paths in automated tests.
- Verify the full GitHub Actions suite.
