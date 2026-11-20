# 2026-11-20 2130 — Apache-2.0 开源授权与候选版更新 / Apache-2.0 licensing and prerelease update

## 中文

### 修改内容

- 根据项目所有者明确选择，采用 **Apache License Version 2.0, January 2004**；将完整英文许可证放到仓库根目录 `LICENSE` 和可移植 Skill 的 `skills/model-router/LICENSE`。
- 更新 README、CHANGELOG、贡献说明、文档导航和发行说明，把旧的“暂无许可证”描述改为 Apache-2.0。原有历史日志保持原样，归档索引解释此前的时间背景。
- 扩展发行打包器与测试，确保独立安装包必须包含许可证且与根目录一致，不因 LICENSE 无扩展名而打包失败。
- 更新预发布版本至 **v2.3.0-rc.2**、发行工作流和显式触发标记。旧的 rc.1 tag 与 Release 附件保留，不覆盖旧版。

### 验证与下一步

- 提交后由 GitHub Actions 执行 Python 单元测试、离线路由评测、双语/链接预检与 ZIP 校验；成功状态须以工作流真实结果为准，不能事先宣称通过。
- 下一步检查 GitHub 的许可证识别与 rc.2 Release 附件，再在已登录的 Claude Code/Codex 中进行授权端到端测试。

## English

### Changes

- Adopted **Apache License, Version 2.0 (January 2004)** at the owner's explicit request, with the complete English text in root LICENSE and skills/model-router/LICENSE.
- Updated README, CHANGELOG, contributing guide, docs index and release notes. Historical statements are retained as historical context.
- Hardened ZIP packaging/tests to require and verify identical license texts in the portable archive.
- Advanced the prerelease to **v2.3.0-rc.2** with a new publication marker, leaving the rc.1 tag and assets unchanged.

### Verification and next steps

- GitHub Actions must independently verify unit tests, offline routing cases, bilingual links, ZIP reproducibility and checksum; no success is claimed before the run finishes.
- Next verify repository license detection and rc.2 assets, then conduct explicitly authorized client integration.
