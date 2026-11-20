# 2026-11-20 20:55 (+08:00) — 发行文档统一与缓存排除 / Bilingual release docs and cache exclusion

## 中文

### 修改内容
- 双语重写 README，新增 CHANGELOG、CONTRIBUTING、SECURITY 与发行指南；更新 docs/、routine/ 双语索引。
- 增加双语发行说明，解释离线验证范围、独立 ZIP 的内容和真实 CLI 联调限制。
- 发行打包器忽略编译产生的 `__pycache__` 和 `.pyc`，但继续拒绝敏感隐藏文件及不受支持的源文件。
- 保持既有 Skill 命令与结构兼容，不增加第三方运行时依赖。

### 验证与下一步
- 本地已对新增 Python 文件进行语法检查；完整 CI 和文档链接检查以 GitHub Actions 为准。
- 下一步设置自动发布工作流，仅在受控的版本发布标记触发后、通过测试时生成候选发行版。

## English

### Changes
- Rewrote the bilingual README; added CHANGELOG, CONTRIBUTING, SECURITY and release guidance; refreshed documentation and routine indexes.
- Added bilingual release notes explaining ZIP scope, offline validation and pending authenticated CLI checks.
- The packager now ignores generated Python caches while still rejecting hidden secrets and unsupported source files.
- Preserved existing routing/Skill interfaces and introduced no third-party runtime dependency.

### Verification and next steps
- New Python files passed local syntax checks; GitHub Actions must verify full tests and links.
- Next: add a narrowly triggered release workflow; publish the candidate only after CI gates pass.
