# 2026-11-20 20:59 (+08:00) — 受控 GitHub Release 工作流 / Gated release workflow

## 中文

### 修改
- 新增 `release.yml`，仅在发布标记文件变更或人工触发时启动，且限制仓库身份。
- 创建 Release 前检查版本、预发布标识、编译、单元测试、离线路由、双语文档、Skill ZIP 内容和 SHA-256。
- 发行资产包括独立 Skill ZIP 和 `.sha256`；Release Notes 为中英文，并标记预发布，不覆盖已有同名 Release。
- 不会调用供应商模型、购买 API、部署执行器或将私有日志打包发布。

### 验证与下一步
- 工作流语法/步骤完整性将在 CI 和首次发布时验证。正式 Release 只有发布工作流成功后才可声称已创建。
- 下一步完成完整 CI，提交受控发行标记并核实 GitHub Release URL 与附件。

## English

### Changes
- Added a repository-scoped release workflow triggered only by a controlled publish-marker change or manual dispatch.
- Gates publication on version checks, compilation, unit and routing tests, bilingual docs, a reproducible ZIP and SHA-256 validation.
- Publishes bilingual prerelease notes and two Skill assets, without replacing an existing release.
- No model API calls, purchases, deployment or private traces are included.

### Verification and next steps
- Validate workflow behavior in Actions; claim release creation only after the publication run succeeds.
- Next: verify regular CI, add the controlled marker, then inspect release URL and attached assets.
