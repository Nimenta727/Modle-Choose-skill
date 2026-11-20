# Routing policy — V1.4 (reliability, evidence and cost)

## 1. Hard filters before any score

1. Require an active, published model ID, approved provider, task capability, context and output capacity, and a cost below the declared hard budget.
2. **Respect the execution surface.** The API model catalog is not a Claude Code, Codex, ChatGPT or Claude-app model picker. Models whose registry `channels` do not contain the selected surface need explicit **surface-specific** model reporting (`--available`) or fresh successful-request evidence. Otherwise they cannot be a native primary/backup.
3. An API inventory (`check_availability.py`) proves only a model is **listed** for those API credentials at the time checked. It does **not** prove a successful invocation. Legacy `status: verified` inventory records are downgraded to `listed`.
4. `execution: true` is a **gate** on a proposed route (not actual orchestration) requiring a `call_verified` record from an external trusted caller, with `method: successful_model_request`, valid provider, matching surface, and a `checked_at` timestamp no older than 24 hours. **This repository cannot produce call-verified evidence itself.** An external orchestrator must still enforce tokens, consent and access before issuing requests.
5. If the user's provider, region, privacy, policy or deployment restrictions preclude a model, exclude it. For `allowed_providers: []` exclude every provider; do not treat it as no restriction.
6. If a hard maximum price is declared and the provider only publishes a **price floor**, the model is excluded: a floor cannot establish that actual cost will fit a cap.
7. If no native candidates qualify, keep the technical plan intact, show `无合格原生模型`, and optionally show a separately labeled `external-conditional` **informational** candidate. Never silently treat that as native, callable or approved for use.

## 2. Availability evidence, in decreasing order of confidence

| Label | Meaning | Native primary without extra data? | May pass execution gate? |
|---|---|---|---|
| `call-verified` | Recent successful request from a trusted external source, on this provider and surface | Yes | Yes, but router does not run models |
| `listed` | Provider's API model-list endpoint returned this ID | For `api` recommendations only | **No** |
| `user-reported` | User explicitly stated model is available on the selected surface | In **recommendation** mode | **No** |
| `conditional` | Listed in official model docs, but not verified for this account | For `api` recommendations only | **No** |
| `external-conditional` | Informational API alternative for a non-API surface | **No** | **No** |

A stale, missing, future-dated or provider-mismatched inventory is ignored (24-hour TTL). An explicit `--available` is never proof of successful invocation. The caller's file must be treated as untrusted input unless the caller separately authenticated it.

## 3. Scoring

The Python router uses editable 1–5 **heuristic** capability priors, not a published benchmark. `quality` / `balanced` / `cost` adjust quality/cost/speed weights. Context, risk, tool support, provider, hard budget, lifecycle and surface are gates **before** scoring. A default/omitted complexity of `medium` uses the same thresholds as explicit `medium`.

Blended price is an approximate 80% input / 20% output token rate **only for ranking**. For a separate optional stage cost illustration, `estimated_input_tokens` and `estimated_output_tokens` are **total stage Token estimates across requests**, and cost is `(input*input_list_price + output*output_list_price) / 1,000,000`. If either is missing, report `unknown`, not zero; if the catalog price is a lower bound, report `lower-bound`. Total only the estimated stages and mark partial coverage. This is an uncached **API-only reference**, not a real bill for Claude Code, Codex, ChatGPT or subscriptions. It ignores caching, tool costs, batches, regional/tier charges and actual work volume. An optional `max_stage_api_reference_usd` is a hard stage cap only when tokens and a non-floor API price are known and `surface=api`; never silently relax it. Latency tiers are qualitative; do not interpret them as wall-clock measurements.

| Phase | Minimum fit by complexity (low / medium / high) |
|---|---|
| Requirements, docs, coding, testing, UI, extraction | 2 / 3 / 4 |
| Architecture, debugging, review | 2 / 4 / 5 |

High risk raises minimum fit to at least 4; critical risk requires 5. A separate review step is recommended for high-risk code, but not automatically fabricated in the user's requested task list.

## 4. Re-routing

Reroute when tests fail twice without progress, context or tools change, the selected model becomes unavailable, or pricing/lifecycle review invalidates a constraint. Review permissions before switching providers. Keep the main implementation plan separate from the advisory model-allocation section.

## 5. Model discovery, provenance and review

`update_models.py` is **read-only**, including its `--check` and `--inventory-file` modes. It recognizes broader new model ID patterns, combines official page candidates with optionally supplied API inventories, and produces a review report. Missing IDs from rendered HTML are *not proof of retirement*. A reviewer must confirm provider documentation, lifecycle, price, tool support and context limits **before** editing the canonical registry and its per-field review timestamps.

The scheduled weekly audit uploads a review report; it does **not** create API charges, change the registry, commit automatically, grant tool permissions or verify UI entitlement. Only report data changes can be automated safely without provenance validation. Preserve the original `verified_at` until all relevant model facts have been reviewed.

## 6. Real-data calibration (explicit opt-in, V1.4)

`tools/evals/compare_trials.py` produces a **proposal only**, requiring same-task fixture, rubric, execution harness fingerprint and surface, repeated outcomes and independent human assessment. A raw proposal is never accepted by the router.

A user may explicitly provide a locally reviewed `--calibration-file` with `schema_version:1`, `status:user_reviewed`, timezone-aware `reviewed_at` and `adjustments` entries `{model_id, task_type, score_delta, evidence}`. Maximum absolute delta: 8 score points; expires after 90 days. Only affects eligible-candidate ranking, **not hard task/surface/access/price filters or minimum capability gates**. This is not independently authenticated evidence; the user must verify provenance. No automatic edits to `model-registry.json`.

## 7. Stage handoff integrity

For stage transitions list input artifact, decisions, constraints, tests actually run and unresolved issues. `scripts/handoff.py` prints blank templates unless `--output-dir` is explicitly provided; no model invocation or project editing. Require verified evidence before marking a handoff complete; do not manufacture approval or tests.

## 中文摘要 / Chinese summary

平台、权限、预算、风险和能力限制必须先于任何评分。API 模型清单不证明成功调用，外部条件性候选不等于本地可执行模型。参考价格不是账单，人工审核后的校准只能有限调整已合格模型排序，不得放宽硬性条件。

## English summary

Apply hard constraints before ranking. API inventory is not successful-call evidence, external recommendations are not native executors, list-price costs are not bills, and reviewed calibration never bypasses safety, access or budget gates.

