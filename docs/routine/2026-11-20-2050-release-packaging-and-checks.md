# 2026-11-20 20:50 (+08:00) — 发行打包及静态审核 / Release packaging and static checks

## 中文

### 修改内容
- 新增 `tools/package_release.py`：构建可重复的独立 Skill ZIP，附带 SHA-256，拒绝隐藏文件、符号链接、缺少核心文件、覆盖已有发行包。
- 新增 `tools/check_docs.py`：检查中英文文档章节、相对 Markdown 链接、历史日志数量，仅读取文件。
- 增加 `tests/test_release_package.py` 发行包回归测试和 `release/version.json` 版本元数据。
- 将发行通道标为 `v2.3.0-rc.1` 候选版，真实 Claude Code/Codex 客户端仍待联调。

### 验证和下一步
- Python 语法检查在本地通过。远程完整单测与打包测试结果以该提交 GitHub Actions 为准。
- 下一步更新中英文 README、CHANGELOG、历史索引与发行操作指南，然后通过发布工作流生成 GitHub Release。

## English

### Changes
- Added deterministic standalone Skill ZIP packaging with SHA-256 and strict source validation.
- Added offline bilingual documentation/link preflight, historical log count checks, and release package tests.
- Added release version metadata for v2.3.0-rc.1, marked as a candidate rather than an authenticated-client-verified stable version.

### Verification and next steps
- Local Python syntax check passed. Remote full CI and package checks must be read from GitHub Actions.
- Next: update bilingual README, changelog, archive navigation, and publishing documentation; publish only after CI validation.
