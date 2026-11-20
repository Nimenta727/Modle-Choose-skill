# 评测与验收 / Evaluation and Quality Rubric

## 中文

### 三种证据不能混淆

| 类型 | 可验证 | 不代表 |
|---|---|---|
| 离线路由规则 | 硬性条件筛选、模型备选、计划格式 | 模型真实开发能力 |
| 可选真实 CLI 触发 | 客户端返回内容、可观察的 Skill 文件读取 | 无法观察的客户端内部加载、GUI 完整行为 |
| 同条件真实任务验收 | 真实测试、成本、耗时和失败记录 | 普遍适用的模型排名 |

~~~bash
python3 tools/evals/evaluate_routes.py
python3 tools/evals/live_triggers.py --agent claude
python3 tools/evals/live_triggers.py --agent codex
python3 -m unittest discover -s tests -v
~~~

默认 dry-run 不产生模型调用。只有在你明确使用 --execute、安装登录 CLI 后，才会发起真实请求并可能消耗额度。建议使用无机密的临时测试项目。仓库尚无经真实账号验证的触发率数据或通用模型质量排名。

真实任务对比必须固定代码快照、任务、验收标准、工具版本和测试环境；保留失败与返工记录；成本未知就省略而不能伪造零。配对模型比较的提议必须经过独立人工审核，不得自动改变硬性约束。

## English


V1.3 has **three distinct evidence tiers**. Never collapse them into one “accuracy” percentage.

| Evidence tier | Command | Measures | Does NOT prove |
|---|---|---|---|
| Offline policy contract | `python3 tools/evals/evaluate_routes.py` | Hard gates, risk tiers, fallback, deterministic plan format | Any vendor model's actual quality |
| CLI integration smoke | `python3 tools/evals/live_triggers.py --agent claude\|codex --execute` | CLI responses and visible traces on a disposable sample project | Skill loaded internally if no file read event was observable; GUI Plan Mode behavior |
| Actual task trials | `python3 tools/evals/score_trials.py --trials <JSON>` | Observed acceptance results, cost and runtime on **provided measurements** | Controlled cross-model ranking without same-task repeats |

## 1. Offline policy regression (safe, free, CI-enabled)

```bash
python3 tools/evals/evaluate_routes.py \
  --json-out /tmp/model-router-policy.json \
  --md-out /tmp/model-router-policy.md
python3 -m unittest discover -s tests -v
```

`tools/evals/routing_cases.json` contains 24 synthetic, reproducible boundary cases (not 24 real-world coding trials). It pins the evaluation clock to `2026-11-19T14:00:00+00:00` to keep proof-expiry checks deterministic. Do **not** use the frozen date to claim current API availability. Reports include every assertion and its actual/expected value. Exit code `1` means at least one policy assertion failed; `2` means invalid input/error.

## 2. Real CLI smoke tests (optional; may use your account limits)

You need the **Claude Code** and/or **OpenAI Codex CLI** installed, authenticated and available in PATH. The CLI may change; check its `--help` and the official documentation before executing. This repository cannot sign in on your behalf. `--execute` must be supplied explicitly; there is no live execution in GitHub CI.

```bash
# Default: safe dry run, no model calls
python3 tools/evals/live_triggers.py --agent claude
python3 tools/evals/live_triggers.py --agent codex

# Only after choosing to spend account usage; start with one case
python3 tools/evals/live_triggers.py --agent claude \
  --execute --case-id implicit-plan-web --max-runs 1 \
  --report ./local-eval-reports/claude.json
python3 tools/evals/live_triggers.py --agent codex \
  --execute --case-id implicit-plan-web --max-runs 1 \
  --report ./local-eval-reports/codex.json

# Larger sampling, including negative controls
python3 tools/evals/live_triggers.py --agent codex --execute --max-runs 5
```

The runner initializes a fresh, disposable Git project containing only `sample.py` and an installed Skill, invokes Claude with `--permission-mode plan` or Codex with `--sandbox read-only`, and deletes that temporary workspace afterward. **CLI commands do make remote requests on `--execute` and may incur subscription/usage costs.** No private project files are deliberately supplied. Native CLI configuration and policies may still access user-level settings or remote services; run in a separate test OS account/VM if strict isolation is required. Never use `--dangerously-skip-permissions` or `--full-auto` for this benchmark.

Five prompt cases include implicit planning, explicit invocation and two unrelated negative controls. By default, reports contain only metadata and hashes (no response text). Raw CLI streams are **not saved** unless `--trace-dir` is explicitly supplied. Treat raw traces as sensitive; they may contain model output and local context. The grader distinguishes:

- **Plan output contract**: positives have a model allocation heading, a table, and primary/backup columns; negatives omit the heading. This measures response compliance, **not actual Skill invocation**.
- **Observed Skill-file read**: tool events show a read of `model-router/SKILL.md`. This is stronger evidence when present, but absence is not proof the Skill was never loaded (instructions can be preloaded or abbreviated).
- **Inconclusive**: CLI not installed, nonzero exit, timeout or response could not be parsed. Exclude from accuracy denominators; never record as a pass.

Codex `exec`'s read-only, non-interactive CLI is **not identical to the graphical/interactive Plan Mode**. For full Plan Mode validation, independently open both clients, start a planning session, test the five prompts, and record the version, plan mode and observed output in a real trial log.

## 3. Real task-quality measurement (requires manual/authorized test runs)

`tools/evals/trials.json` deliberately starts empty. Fill it **only with real measured outcomes** verified by acceptance tests. Example record shape:

```json
{
  "run_id": "unique-local-run-id",
  "task_id": "same-task-across-models",
  "task_type": "coding",
  "model_id": "actual-model-id",
  "passed": true,
  "cost_usd": 0.0,
  "elapsed_seconds": 30.0
}
```

Record `cost_usd` from actual billing where possible; if cost is not measurable, **do not fabricate a zero or another value to fill the field**. Only aggregate complete verified records and explicitly disclose missing data. For robust cross-model comparisons: use identical repo snapshot and acceptance criteria, repeat each model/task combination, randomize order where feasible, preserve tool versions, and note failed invocations rather than hiding them. Keep personal code, account details, keys and traces out of this public repository.

```bash
python3 tools/evals/score_trials.py --trials tools/evals/trials.json
```

The scorer groups by task type and model ID and summarizes acceptance rate, cost and latency; it labels small sample groups insufficient and **never automatically changes** `model-registry.json` fitness heuristics. See `tools/evals/quality_rubric.md`.

## 4. CI, acceptance and interpretation

GitHub Actions runs unit tests + offline evaluation, then uploads machine-readable and Markdown reports. No vendor credentials are present in this workflow; true invocation rates and model quality remain **unmeasured** until someone runs the account-backed experiments.

V1.3 acceptance: all offline policy cases pass, test suite passes, CLI dry runs perform zero requests, positive/negative prompts are covered, and optional live runs distinguish errors from passes. Success is **implementation of a measurement apparatus**, not demonstration of high model-selection accuracy.

Official implementation references: [Claude Code settings and Plan Mode](https://code.claude.com/docs/en/settings), [Claude Code CLI](https://code.claude.com/docs/en/cli-reference), [Codex agent skill evaluation](https://developers.openai.com/blog/eval-skills).

## 5. V1.4: paired evidence, optional review and cost forecasting

See [V1.4 methodology and use](calibration.md). `tools/evals/compare_trials.py` examines task-matched real pass/fail trials with 6 distinct paired tasks and at least 2 runs for each model on each task. Hashes are identifiers, not a guarantee that fixtures are real or equivalent. Results are unapproved proposals; the router refuses to apply them until the user performs an independent review and supplies a separate bounded, recent calibration file. An unadjusted one-sided sign-test p-value is exploratory and subject to multiple-comparison bias.

The route's optional `estimated_input_tokens`/`estimated_output_tokens` produce only uncached API reference estimates; missing cost or timing data in trial summaries are displayed as missing, never zero. Stage handoffs are intentionally incomplete templates, not completed work products. As of the initial V1.4 release, `tools/evals/trials.json` remains empty and no live comparative results exist.


### Quality review rubric


Use the **same frozen repository and task specification** for every tested model. Plan tasks need separate execution/acceptance tests; the policy router can recommend models but does not run them. Suggested starter set: simple Python bug fix, multi-file refactor, API contract migration, accessibility UI review, test generation, security-focused architecture, and documentation update. Avoid confidential code.

1. **Task completed**: Did independently defined unit/integration/acceptance checks pass? Record `passed` true/false and exact test command + commit/fixture identity outside the public dataset when sensitive.
2. **Correctness and regressions**: Tests should detect wrong behavior, not reward length or persuasive explanations. A plan-only task requires explicit checklist-based human review; do not mark it as code tested.
3. **Rework**: Count correction iterations and failed tool/model requests; do not silently omit failed runs.
4. **Cost/time**: Record actual provider usage, token/caching conditions if available and wall-clock seconds. Subscription flat-fee work cannot be treated as zero marginal API spend; report cost as unavailable instead.
5. **Reproducibility**: Record model ID, execution surface, client version, inference effort, exact task ID, project fixture SHA and run timestamp in a private raw log.
6. **Independent review**: Prefer blind review on identical task outputs. Aggregate by task ID before comparing models; require multiple distinct tasks and repeated observations per group.

**Decision gates:** Do not change registry fit scores from a single run, fabricated estimate or mere task routing policy pass. Propose updated fit priors only when enough paired tasks and objective checks show a stable difference; require explicit review, changelog, and documented uncertainty. A policy evaluation's 100% is not a model quality benchmark.
