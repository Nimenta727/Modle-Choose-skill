# 安全执行 / Supervised Execution and Safety

## 中文

### 默认仅预览

执行器只用于用户另行授权的本地操作。先生成未批准清单，再预览：

~~~bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format json > routing-result.json
python3 tools/orchestrator/prepare.py --task-file skills/model-router/examples/project-plan.json --route-file routing-result.json --output local-execution.json
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace . --all
~~~

清单初始每阶段 approved=false、cli_model 为空、mode=read-only。默认运行**不会调用模型**。要运行真实阶段，需安装并登录对应 CLI，核对本机实际支持的模型别名、权限和费用，编辑清单并逐阶段批准。

~~~bash
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace /path/to/project --stage s01-requirements --execute --confirm-stage s01-requirements
~~~

真实调用可能消耗账号额度。写入阶段须额外设置 mode=write、显式 --allow-write，并且 Git 工作区干净；只读权限不构成完整系统隔离。CLI 可能读取代码并发送必要上下文给供应商，务必确认披露许可。完成时只得到**未经人工验收**的结果，不代表测试通过。

### 跨模型交接

下一供应商的交接必须由用户审核、单独提供安全内容，并显式采用 --handoff-file 与 --allow-handoff-share。不会自动传输完整日志、自动提交 Git、推送或部署。

## English


This is a **local execution adapter**, not a hosted multi-agent service or a guarantee of API/model availability. All commands below require Python 3.10+, an existing local checkout of the project, and *separately installed and authenticated* Claude Code or Codex CLI for **live** execution. The Model Router Skill remains recommendation-only; execution is a separate and opt-in workflow.

## 1. Generate a candidate model allocation

From the Model Router repository root:

```bash
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json \
  --format json > routing-result.json
```

API model IDs in `routing-result.json` are **not** automatically CLI model IDs or proof of subscription access. Even when your model is listed as `call-verified` for an API, it is not a CLI execution entitlement.

## 2. Convert to a safe, unapproved manifest

```bash
python3 tools/orchestrator/prepare.py \
  --task-file skills/model-router/examples/project-plan.json \
  --route-file routing-result.json \
  --output local-execution.json
```

The generated manifest has `approved: false`, `cli_model: ""`, and `mode: "read-only"` on every stage. This is intentional. Review the prompts, provider, source availability, model choices, data sensitivity and expected deliverables. Then **manually edit each stage you intend to run**, set its `cli_model` to a model ID/alias accepted by the *installed* Claude Code or Codex, set `approved: true`, and optionally set `mode: "write"` only for a phase that genuinely needs to change code. Avoid putting secrets or personal data into prompts or handoffs.

For example, a manually approved **read-only** Claude stage (example only):

```json
{
  "id": "s01-requirements",
  "name": "Requirements",
  "agent": "claude",
  "provider": "anthropic",
  "model_id": "claude-sonnet-5-5",
  "cli_model": "sonnet",
  "approved": true,
  "mode": "read-only",
  "prompt": "Review the repository and identify high-level requirements without editing files."
}
```

The alias in this example is illustrative and must be checked against your local CLI; it is not a promise of access. `model_id` records the decision, while `cli_model` is the actual argument passed to your locally installed agent.

**Do not check `routing-result.json`, `local-execution.json`, or real task transcripts into a public repository if they contain private project information.** Prefer a separate private directory.

## 3. Inspect what would run (free, no CLI invocation)

```bash
python3 tools/orchestrator/run.py --manifest local-execution.json \
  --workspace /path/to/your-project --all
```

`--all` without `--execute` is a dry run. It does not check login status or execute the stages.

## 4. Execute exactly one approved stage

```bash
python3 tools/orchestrator/run.py --manifest local-execution.json \
  --workspace /path/to/your-project \
  --stage s01-requirements --execute --confirm-stage s01-requirements
```

This **may consume model credits or subscription usage**. A `read-only` stage is executed using Claude's `plan` permission mode with only file-reading tools, or Codex's `read-only` sandbox. It cannot be considered a full operating-system security boundary. The CLI can read project files and send relevant context to its model provider. Ensure you have permission to share the repository with the selected provider. Model availability, regional controls and organization policies still apply.

For an explicitly approved `"mode": "write"` stage:

```bash
python3 tools/orchestrator/run.py --manifest local-execution.json \
  --workspace /path/to/your-project \
  --stage s02-implementation --execute --confirm-stage s02-implementation --allow-write
```

Write mode requires a **clean Git worktree** and explicit `--allow-write`. Claude Code uses `acceptEdits` with `Read,Glob,Grep,Edit,Write` only and denies MCP tools; Codex uses `workspace-write` sandbox with approvals disabled. Neither adapter grants unrestricted `danger-full-access`, disables sandboxing, runs shell commands on behalf of the scheduler, or grants automatic push/deploy rights. However, the installed agents have their own configuration and security boundaries. Always review changes and run tests yourself before accepting them. The scheduler deliberately does not commit, push, deploy, merge, or run tests. The exit code means only the CLI finished, not that the code is correct.

On Windows PowerShell, replace `python3` with `py -3` and supply Windows paths. There are no Bash-specific commands in the runner itself.

## 5. Review the result and hand off manually

Results are saved outside the workspace by default in `~/.model-router/runs/<timestamp>-<stage-id>-<random>/` with private-directory permissions where supported. The main files are `result.json` and, on successful CLI completion, `response.md`. The latter is **unreviewed model output**. A run with `state: cli_completed_unreviewed` is **not** a verified acceptance test. On CLI failures, secrets or raw CLI traces are not deliberately persisted.

If the next stage belongs to another provider, write a **new, concise, human-reviewed handoff** with only the necessary safe content. Then explicitly allow its transmission:

```bash
python3 tools/orchestrator/run.py --manifest local-execution.json \
  --workspace /path/to/your-project \
  --stage s03-review --execute --confirm-stage s03-review \
  --handoff-file /path/to/reviewed-handoff.md --allow-handoff-share
```

The handoff is wrapped as **untrusted data**, not executable instructions. The scheduler enforces a 12,000-character handoff cap, and does **not** forward full transcripts, credentials, or prior outputs by default. Nevertheless, prompt injection cannot be fully neutralized by delimiters—review all handoff content yourself. Choose not to transfer if a project's confidentiality rules forbid it.

You can also run sequential stages with `--all --execute --interactive-review` **on a real terminal**. Each stage requires the operator to type its exact stage ID. This mode does not automatically transmit one stage's output to the next, and write stages may require a new clean-worktree checkpoint before proceeding. For reliable production work, explicit one-stage-at-a-time execution is recommended.

## Permissions and constraints

- Default `run.py` = **dry-run**. No model call or file modifications.
- A manifest produced by `prepare.py` = **unapproved**, every stage read-only.
- `--execute` = **explicit user authorization** to call the local CLI, potentially incurring usage costs.
- Single-stage live execution additionally requires `--confirm-stage` matching the chosen stage ID, and `approved: true` with a nonempty `cli_model` in the manifest.
- Write mode additionally requires `--allow-write` and clean Git worktree; outputs must be outside the workspace.
- A handoff additionally requires `--allow-handoff-share`; cannot be used with automatic `--all`.
- Do not pass credentials in arguments, manifests, handoff files or plan documents. The child process inherits a narrow allowlist of environment variables, including the two provider API key variables if you deliberately configured them.
- No silent fallback to another vendor if the selected CLI/model fails. Fix the setup and approve a new stage explicitly.
- The stages only execute prompts. There is no task-level verifier, automatic acceptance, cost reconciliation, resumable job queue, or full-fledged isolation guarantee.

## Source documentation verified on 2026-11-19

- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference): noninteractive `-p`, `--output-format json`, `--permission-mode plan` / `acceptEdits`, `--tools`, `--disallowedTools`, `--model`.
- [Codex CLI developer commands](https://developers.openai.com/codex/cli/reference): `codex exec`, `--model`, `--sandbox read-only|workspace-write`, `--output-last-message`, `--ephemeral`.

Versions, flags, identities and product availability can change. Review `claude --help` and `codex exec --help` on the **actual** machine before authorizing calls.


## V2.2：带人工验收的断点恢复 / Human-reviewed Checkpoints

### 中文

在已经审核并**手动设置 cli_model 和 approved=true** 的执行清单上，创建私有 checkpoint。以下示例中的状态路径位于项目目录之外；Windows 可以使用 `py -3` 并将路径换为自己的私有目录。

~~~bash
python3 tools/orchestrator/checkpoints.py --manifest local-execution.json --state /private/checkpoint.json --init
python3 tools/orchestrator/checkpoints.py --manifest local-execution.json --state /private/checkpoint.json --status
~~~

只有用户明确要求真实执行，并在本机安装登录 CLI 后，才能增加下面的执行参数（**可能消耗模型额度**）：

~~~bash
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace /path/to/project --stage s01-requirements --execute --confirm-stage s01-requirements --checkpoint-file /private/checkpoint.json
~~~

CLI 执行成功只产生 cli_completed_unreviewed。请查看执行目录、核对交付物、运行实际验收检查，然后手动记录审核。以下 evidence 只是人工声明，系统不会自行证明测试已运行：

~~~bash
python3 tools/orchestrator/checkpoints.py --manifest local-execution.json --state /private/checkpoint.json --accept-stage s01-requirements --confirm-stage s01-requirements --evidence "Reviewed deliverables and verified acceptance conditions"
~~~

若人工检查不通过，可改用 --reject-stage 配合 --reason、--confirm-stage；失败后只有额外使用 --retry-failed 才可重试，每个 checkpoint 最多两次尝试。运行期间崩溃留下的 running 需要先人工排查副作用，不能自动重放。改变 manifest 后必须重新初始化独立的 checkpoint，不能沿用旧状态。

人工另外撰写一个简短、无机密的摘要文件后，可用下面命令生成交接包，**这不会上传或传输文件**：

~~~bash
python3 tools/orchestrator/handoff_packet.py --manifest local-execution.json --state /private/checkpoint.json --stage s01-requirements --summary-file /private/reviewed-summary.md --output /private/handoff.json
~~~

如确实需要向另一家模型发送，仍须分别审核内容及使用 run.py 的 --handoff-file 与 --allow-handoff-share。状态哈希不是身份认证；模型是否真实可用、任务是否通过验收，仍需独立证据。

### English

Initialize a **private checkpoint outside your project** only after reviewing the execution manifest and manually setting the relevant stage's cli_model and approved=true:

~~~bash
python3 tools/orchestrator/checkpoints.py --manifest local-execution.json --state /private/checkpoint.json --init
python3 tools/orchestrator/checkpoints.py --manifest local-execution.json --state /private/checkpoint.json --status
~~~

For a real model call, you must have an authenticated local CLI and explicitly use --execute plus an exact stage confirmation (may consume credits):

~~~bash
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace /path/to/project --stage s01-requirements --execute --confirm-stage s01-requirements --checkpoint-file /private/checkpoint.json
~~~

CLI completion is *unreviewed*. Inspect output and independently validate acceptance before using --accept-stage, --confirm-stage and a human --evidence note. Reject incomplete output with --reject-stage and --reason. Only --retry-failed permits another attempted run, limited to two total attempts. An interrupted running stage requires manual side-effect review before a new plan; changed manifests invalidate old checkpoints.

Generate a compact handoff using a **separately human-authored** safe summary via handoff_packet.py, as in the Chinese example. Packet creation does not send it to another provider. Cross-provider transfer still requires --handoff-file and --allow-handoff-share. State hashes are not authenticated proof of review.
