# Model Router v2.3.0-rc.2 — Bilingual Release Candidate / 双语候选发行版

## 中文

### 发行内容

本次以结构整理和可安装性交付为目标。独立 Skill ZIP 包含 `SKILL.md`、路由脚本、模型目录与参考策略；仓库级执行器、测试夹具和历史数据**不包含在 ZIP 中**，仍可从源码获得。

- 统一的中英文 README、架构、安装、执行、评测与 Token 优化指南。
- 可重复构建的发行 ZIP 与 SHA-256 校验文件，发行前进行完整离线测试、文档链接检查和包内容校验。
- 保留历次 `docs/routine/` 日志，附新版文档入口及版本说明。
- 已有的模型连续性、上下文预算、最小化交接和受控执行功能继续保留。

### 本次新增

- Apache-2.0 开源许可证已纳入仓库与 Skill 包；发行包增加许可内容检查。

### 安装

从本页 Assets 下载 `model-router-skill-v2.3.0-rc.2.zip` 和配套 `.sha256` 文件，核对校验和，解压并复制 `model-router/` 到目标项目的 `.claude/skills/` 或 `.agents/skills/`。也可克隆源码执行 `python3 tools/install.py --target /path/to/project`。

### 重要限制

这是**预发布候选版**。远程 CI 只证明仓库代码在离线环境通过对应测试，不证明真实 Claude Code/Codex 账号可用、自动触发成功或实际节省固定比例 Token。模型价格与版本元数据有各自核实日期。项目现已由所有者选择 **Apache License 2.0**。发行 ZIP 内包含完整 LICENSE；旧的 rc.1 附件不会自动变更。

## English

### Included

This release candidate focuses on consistent structure and installable distribution. The standalone Skill ZIP contains `SKILL.md`, routing scripts, the model snapshot and reference policies. It **does not** include host-side orchestrators, test fixtures or historical run data; those remain in the source repository.

- Bilingual README, architecture, setup, execution, evaluation and token-efficiency guides.
- Reproducible Skill ZIP plus SHA-256 and gated offline tests, link checks and packaging validation.
- Preserved historical `docs/routine/` files with current documentation pointers.
- Existing model-continuity, context-budget, compact handoff and supervised-execution capabilities remain available.

### New in rc.2

- Added Apache-2.0 licensing to the repository and portable Skill ZIP, with packaging verification.

### Install

Download `model-router-skill-v2.3.0-rc.2.zip` and its `.sha256` file from Release assets, verify the checksum, then extract and copy `model-router/` into your project's `.claude/skills/` or `.agents/skills/`. Alternatively, clone and run `python3 tools/install.py --target /path/to/project`.

### Limitations

This is a **prerelease**. CI passing demonstrates only its specified offline checks, not authenticated Claude Code/Codex availability, automatic Skill activation or measurable token savings. Vendor metadata keeps its own review dates. The owner selected **Apache License 2.0**. The standalone ZIP now contains the complete LICENSE; rc.1 assets remain unchanged.
