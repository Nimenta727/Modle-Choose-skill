# 2026-11-20 21:05 (+08:00) — 双语历史归档与发行 CI / Bilingual archives and release CI

## 中文

### 修改
- 为第一批九份历史 routine 记录添加统一的中英文发行归档说明和最新版文档链接；保留原始日志内容。
- 在 CI 中新增双语标题、Markdown 本地链接、可重复 ZIP、压缩包内容和 SHA-256 校验。
- 更新结构测试检查发行脚本与文档，新增加入 dist/ 忽略规则。

### 验证与下一步
- 本次脚本对文件存在及修改锚点完成检查。CI 仍须以 GitHub Actions 的实际结果为准。
- 下一步：更新剩余历史日志，检查完整 CI，发布 v2.3.0-rc.1 候选版。

## English

### Changes
- Added bilingual release archive notices and current-document links to the first nine historical routine entries, preserving original content.
- Added bilingual/link, reproducible ZIP and SHA-256 checks to routine CI; updated layout tests and ignored local dist/.
- No old test claims were modified.

### Verification and next steps
- Path/patch anchors were checked. Full validation depends on the corresponding GitHub Actions run.
- Next: annotate the remaining historical logs, verify CI, publish the v2.3.0-rc.1 release candidate.
