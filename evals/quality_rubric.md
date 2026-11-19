# Quality evaluation rubric (human-reviewed, real runs only)

Use the **same frozen repository and task specification** for every tested model. Plan tasks need separate execution/acceptance tests; the policy router can recommend models but does not run them. Suggested starter set: simple Python bug fix, multi-file refactor, API contract migration, accessibility UI review, test generation, security-focused architecture, and documentation update. Avoid confidential code.

1. **Task completed**: Did independently defined unit/integration/acceptance checks pass? Record `passed` true/false and exact test command + commit/fixture identity outside the public dataset when sensitive.
2. **Correctness and regressions**: Tests should detect wrong behavior, not reward length or persuasive explanations. A plan-only task requires explicit checklist-based human review; do not mark it as code tested.
3. **Rework**: Count correction iterations and failed tool/model requests; do not silently omit failed runs.
4. **Cost/time**: Record actual provider usage, token/caching conditions if available and wall-clock seconds. Subscription flat-fee work cannot be treated as zero marginal API spend; report cost as unavailable instead.
5. **Reproducibility**: Record model ID, execution surface, client version, inference effort, exact task ID, project fixture SHA and run timestamp in a private raw log.
6. **Independent review**: Prefer blind review on identical task outputs. Aggregate by task ID before comparing models; require multiple distinct tasks and repeated observations per group.

**Decision gates:** Do not change registry fit scores from a single run, fabricated estimate or mere task routing policy pass. Propose updated fit priors only when enough paired tasks and objective checks show a stable difference; require explicit review, changelog, and documented uncertainty. A policy evaluation's 100% is not a model quality benchmark.
