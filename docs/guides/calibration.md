# 成本、校准与交接 / Cost, Calibration and Handoffs

## 中文

### API 价格只是估算

在任务阶段提供 estimated_input_tokens 与 estimated_output_tokens（整个阶段累积值），才可以计算对应 API 的未缓存标价参考费用；缺失字段标记“未估算”，不当作零。max_stage_api_reference_usd 只适用于 API 环境、已估算且非“起价”模型。它不是订阅账单或对真实成本的承诺，也不涵盖工具收费、缓存、批次、失败重试、地区附加费等。

~~~bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/budget-plan.json
~~~

### 配对真实任务与人工校准

tools/evals/trials.json 初始为空。比较至少需要六个独立匹配任务，每个任务每个模型至少两次，并记录代码快照、验收规则、工具环境的哈希。计算结果只是 proposal_unreviewed，不会被路由器自动采用。评审者需要独立审阅真实证据并创建 user_reviewed 校准文件；有限的评分修正不能突破模型权限、预算、任务风险和平台限制。

~~~bash
python3 tools/evals/score_trials.py --trials tools/evals/trials.json
python3 tools/evals/compare_trials.py --trials tools/evals/trials.json --json-out proposal.json
~~~

### 交接文档

~~~bash
python3 skills/model-router/scripts/handoff.py --task-file skills/model-router/examples/project-plan.json
~~~

默认只打印待填写模板；不能把模板当成已经执行或验收过的结果。跨供应商共享前必须人工筛选信息并另行许可。

## English


## Scope and limits

Three *separate* objectives: estimate list-price API spend from user-supplied Token budgets; propose quality adjustments based on **matched real task** outcomes; create unfilled cross-stage handoff templates. No cross-model agent execution, API calls or automatic subscriptions are part of this release. None of these features has independently measured the claimed quality of any model yet.

## 1. Optional API list-price cost planning

Supply both `estimated_input_tokens` and `estimated_output_tokens` on each stage in the task JSON. These are cumulative estimated tokens **for the full stage**, not context-window maxima. The router computes input+output list-price values using the cached vendor model snapshot. Missing estimates yield `unestimated` (not $0), and `price_floor_only` yields lower-bound labels. Optional `max_stage_api_reference_usd` applies only to `surface: api` with known non-floor prices and explicit token estimates; there is **no global project budget optimizer** in V1.4. The reported project total is a sum of estimated selected stages, not a subscription cost, quote, or guaranteed upper bound. It excludes caching, batch, regional pricing, tool charges, prompt growth, failed/duplicate requests and changes in model pricing. Use a separate contingency margin and check current official pricing before using hard budgets.

```bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/budget-plan.json
```

## 2. Real-data paired evaluation

Source dataset: `tools/evals/trials.json` (intentionally EMPTY until genuine results exist). Use `tools/evals/score_trials.py` for descriptive aggregates, `tools/evals/compare_trials.py` for conservative matched comparisons.

Each paired trial row must include these existing fields: `run_id`, `task_id`, `task_type`, `model_id`, `passed` (observed objective outcome). For pair inclusion also supply `surface`, `fixture_sha256`, `rubric_sha256`, `harness_sha256` (64 hexadecimal characters each). The harness fingerprint must describe the **same tool policies/environment** across models, not a model-specific configuration. Record elapsed seconds, billed USD and retry counts only if actually measured; omit unknown amounts rather than using zero. Keep full raw experiment logs private.

At least six **distinct matched task IDs**, with two repeat runs **per model per task**, are required for an evidence proposal; otherwise `suggested_adjustments` is empty. The tool uses an exploratory exact one-sided sign test on per-task acceptance differences. Ties do not count as decisive. Current p-values are **not corrected for multiple testing** and may be unreliable with task selection bias, experiment drift, reviewer dependence or uneven tool setup; independent review is mandatory. Correlated tasks, repeated seeds and same-task near duplicates are not independent evidence, even when IDs differ. These limitations matter more than passing a numeric significance threshold.

```bash
python3 tools/evals/score_trials.py --trials tools/evals/trials.json
python3 tools/evals/compare_trials.py --trials tools/evals/trials.json --json-out /tmp/proposal.json
```

The comparison result is always `status: proposal_unreviewed`. It **cannot** be passed to `route.py --calibration-file`. To apply a proposed adjustment you must separately review the raw trials and create a *different user-owned file* like:

```json
{
  "schema_version": 1,
  "status": "user_reviewed",
  "reviewed_at": "2026-11-19T14:00:00+00:00",
  "adjustments": [
    {"model_id": "ACTUAL_ID_FROM_REGISTRY", "task_type": "coding", "score_delta": 4,
     "evidence": "private matched-trial dataset ID and review notes"}
  ]
}
```

The displayed timestamp is **only an example**, not a claim that calibration has actually happened. For real use set the true current review time and a real known model ID. Limit to ±8 per task-type/model, with 90-day expiry; invalid or unapproved files fail closed. The router does not authenticate an author's manual review, so the reviewer remains responsible for data provenance. Offsets only alter **ranking of already eligible candidates**, never budget, risk, access, context, provider or execution constraints, and never mutate the model registry.

```bash
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json \
  --calibration-file /path/to/user-reviewed.json
```

## 3. Stage handoff templates (explicit output)

```bash
# stdout only (default)
python3 skills/model-router/scripts/handoff.py \
  --task-file skills/model-router/examples/project-plan.json
# write to a new directory; refuses overwrite unless --force
python3 skills/model-router/scripts/handoff.py \
  --task-file skills/model-router/examples/project-plan.json \
  --output-dir /path/to/private-handoffs
```

Each template has intentional TODOs for upstream constraints, artifacts, code changes, acceptance test results and approval. It is NOT evidence of execution. Do not upload private code or model traces to a public repository.

## 4. Validation tiers and acceptance criteria

- Policy/unit tests: deterministic checks only; **not model quality**.
- Empty real trials: report no empirical comparisons and no score adjustments.
- User-supplied matched trials: proposal-only with provenance warnings; any adjustment requires fresh separate manual review.
- Real CLI Plan Mode: still needs an authorized, logged-in Claude Code/Codex environment and independent verification; cannot be claimed by a CI dry run.

For real work, review cost metadata from official vendor pricing and never use illustrative cost numbers as an API bill or a subscription price. V1.4 ships the measurement/calibration and handoff infrastructure, not a vendor capability ranking.
