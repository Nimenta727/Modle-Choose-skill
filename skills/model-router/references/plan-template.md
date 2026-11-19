# Required Plan Mode section

Add this section to the user's original technical development plan; do not replace deliverables or acceptance criteria.

## Model allocation / 模型分配

- **Policy/version**: balanced / V1.2
- **Registry metadata last reviewed**: YYYY-MM-DD; **freshness**: fresh / stale / unverified
- **Current surface**: API / Claude Code / Codex / ChatGPT / other
- **Access evidence**: successful-request verified / API-listed / user-reported / conditional / none
- **Mode**: recommendation-only / execution-gated (a route gate, not real orchestration)

| 阶段 | 交付物 | 当前平台主选（ID） | 推理等级 | 选择原因 | 备用模型（ID） | 访问状态 | 仅供参考的外部候选 |
|---|---|---|---|---|---|---|---|
| ... | ... | ... or no native model | ... | ... | ... | ... | ... |

If surface access has not been established, display `无合格原生模型` and a separate `external-conditional` candidate when useful; this is **not** a direct execution recommendation. Never copy an API ID into a local tool's model selector unless that tool confirms the mapping.

### API reference cost / 参考成本（仅在存在 Token 估计时）

| 阶段 | 估算输入 Token 总量 | 估算输出 Token 总量 | API 参考标价 (USD) | 限制说明 |
|---|---:|---:|---:|---|
| ... | ... / 未估算 | ... / 未估算 | ... / 未估算 | 未缓存参考；订阅费用不可推断 |

Report full/partial/no estimate coverage, clearly label lower-bound-only models and unestimated stages, and never present this as a bill. Do not invent Token estimates or set unknown to zero.

### Handoff contract / 阶段交接

For each transition, record expected input artifact, previous decisions and constraints, acceptance evidence **not yet executed**, and unresolved items. `scripts/handoff.py` creates optional unfilled Markdown templates; only write files on explicit request.

**Transitions:** State the artifact handed to the next phase (e.g., ADR, schema, test criteria) and triggers for rerouting. **Risks:** Show stale metadata, price uncertainty, unverified access, and cross-platform restrictions. **Verification:** List objective acceptance tests; assigning a model is not proof of correctness.
