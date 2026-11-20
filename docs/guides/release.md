# 发行、安装与验证 / Release, Installation and Verification

## 中文

### 当前发行状态

`v2.3.0-rc.2` 是**候选版**。当前可验证的是 Python 离线功能、策略契约和打包产物；真实 Claude Code/Codex 登录环境的 Plan Mode 激活、Token 节省率与跨模型执行尚需独立测试。不要将候选版称为生产稳定版。

### 从源码生成独立 Skill ZIP

```bash
python3 -m unittest discover -s tests -v
python3 tools/evals/evaluate_routes.py
python3 tools/check_docs.py
python3 tools/package_release.py --output-dir dist
python3 tools/package_release.py --verify dist/model-router-skill-v2.3.0-rc.2.zip
```

打包器只包含 `skills/model-router/` 中的文件，并在 ZIP 内增加 `model-router/RELEASE.json`。不会包含仓库执行器、测试记录、本地凭据或缓存；不接受符号链接与隐藏文件。重复构建应产出相同的二进制内容与 SHA-256。

### 从 GitHub Release 安装

1. 在 [GitHub Releases](https://github.com/Nimenta727/Modle-Choose-skill/releases) 选择 `v2.3.0-rc.2`，下载 ZIP 和 `.sha256`。
2. 对照 SHA-256 验证下载文件；解压后确认顶层文件夹为 `model-router/`，其中包含 `SKILL.md`。
3. 将该目录复制到目标项目的 `.claude/skills/model-router/` 或 `.agents/skills/model-router/`。独立 ZIP 不会注入项目指令文件；需要自动引导时可用克隆源码后的 `tools/install.py`。
4. 用真实客户端测试自动发现；AI 文字上的“已加载 Skill”并不能替代可观察的加载证据。

### 发布门槛与限制

- GitHub Release 通过独立工作流，在**完整离线测试、文档检查和可复现打包全部成功后**创建。
- 发行工作流仅由受控版本标记文件变更触发，不因平时提交而自动发布新版本。
- 使用 `--prerelease` 标注，保留源码、哈希文件和双语发行说明；不会自动购买模型额度、调用供应商或提交到用户其他项目。
- 项目现采用 **Apache License 2.0**；根目录和独立 Skill 均附带完整英文 LICENSE，rc.2 ZIP 内同样包含许可证。许可证英文原文为准，使用与再分发需遵守保留通知和标明修改等条款。之前的 rc.1 发行附件是旧快照，不会自动更新为 rc.2。

## English

### Release status

`v2.3.0-rc.2` is a **release candidate**. Offline Python behavior, policy contracts and ZIP packaging are testable. Authenticated Claude Code/Codex activation, savings percentages and production cross-model execution remain unverified.

### Build from source

```bash
python3 -m unittest discover -s tests -v
python3 tools/evals/evaluate_routes.py
python3 tools/check_docs.py
python3 tools/package_release.py --output-dir dist
python3 tools/package_release.py --verify dist/model-router-skill-v2.3.0-rc.2.zip
```

The release archive contains only the portable Skill and a `model-router/RELEASE.json` file. It excludes the orchestrator, test records, local secrets and caches, and rejects symlinks or hidden files. Builds should be byte-for-byte reproducible with a SHA-256 checksum.

### Install from GitHub Release

1. Open [Releases](https://github.com/Nimenta727/Modle-Choose-skill/releases) and download the ZIP and its `.sha256` file.
2. Verify SHA-256, extract the `model-router/` directory, and confirm that it contains `SKILL.md`.
3. Copy this directory to `.claude/skills/model-router/` or `.agents/skills/model-router/` in the target project. The ZIP does not automatically alter agent instructions; the source installer can do so with explicit options.
4. Validate actual skill discovery in your authenticated client; a model's claim that it loaded the Skill is not sufficient evidence.

### Publication gates and limits

- Release publication is gated on offline tests, bilingual doc checks and reproducible packaging.
- A deliberate version marker change triggers the release; regular commits do not publish automatically.
- The workflow labels the release as a prerelease, attaches the ZIP, checksum and bilingual notes, and never invokes paid model providers.
- The project is licensed under **Apache-2.0**. Both the repository root and standalone Skill carry the authoritative English LICENSE; the rc.2 ZIP includes it. Redistribution must comply with its notice and modification requirements. The earlier rc.1 asset remains an unchanged historical snapshot.
