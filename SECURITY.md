# 安全政策 / Security Policy

## 中文

### 安全边界

- Model Router Skill **只做推荐**。仓库级执行器默认 dry-run；真实 Claude Code/Codex CLI 执行需逐阶段授权，写入与跨供应商交接需额外许可。
- 只读 CLI 模式不是操作系统安全沙箱；真实模型可能读取项目文件并将必要上下文发给供应商。使用者负责确认可共享的数据范围。
- 不要将凭据、个人信息、私有模型输出、含敏感信息的执行清单、检查点或日志提交到公共仓库。
- 发行压缩包仅收录经过检查的独立 Skill，不包含用户状态、原始执行记录或环境变量。

### 漏洞反馈

请优先使用仓库支持的 GitHub 私密漏洞报告功能（如已启用）。如未启用，请联系仓库维护者选择私密反馈渠道；不要在公开 Issue 中提交可利用漏洞细节或密钥。没有 SLA 保证；正在审阅的风险会通过后续例行记录跟踪。

### 当前已知限制

尚未在真实登录的 Claude Code/Codex 环境完成全面集成或安全边界测试；发行候选版不能视为正式的隔离执行平台。Token 字符估算不是严格的计费上限，CLI 费用保护也不保证账单绝对不超限。

## English

### Security boundaries

- The Model Router Skill provides **recommendations only**. The optional host-side runner defaults to dry-run and requires stage approval for live calls, with additional consent for file writes and cross-provider handoffs.
- A read-only CLI mode is not an OS sandbox. Model providers may receive relevant project context. Operators must verify authorization to share it.
- Do not upload credentials, personal information, private model output, sensitive manifests, checkpoints or transcripts to public repositories.
- Release ZIPs contain only vetted portable Skill files, not user run records or environment secrets.

### Reporting vulnerabilities

Prefer GitHub private vulnerability reporting when enabled. Otherwise contact the maintainers privately to arrange a safe disclosure channel. Do not expose secrets or exploit details in public issues. No response-time SLA is promised.

### Known limitations

Authenticated Claude Code/Codex end-to-end and security-boundary validation remain incomplete. This release candidate is not a full sandbox. Character-based token estimates are not exact billing limits, and CLI-side cost guards may be exceeded.
