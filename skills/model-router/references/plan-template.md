# Required Plan Mode section

Add this section to the existing development plan without replacing its technical content.

## Model allocation / 模型分配

- **Policy / policy version**: balanced / V1
- **Registry last verified**: YYYY-MM-DD; **freshness**: fresh / stale / unverified
- **Current execution surface**: Claude Code / Codex / ChatGPT / API / other
- **Availability verification**: confirmed by <tool/user> / not verified
- **Mode**: recommendation-only / orchestrator-backed

| Stage / 阶段 | Deliverable / 交付物 | Primary model + ID / 主选 | Effort / 推理级别 | Why / 原因 | Backup + ID / 备用 | Availability / 可用性 |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | confirmed / conditional |

**Transitions:** Explain phase handoffs, shared context artifacts, and the exact trigger for escalating or changing models.

**Risks:** Note any stale catalog, unverified access, uncertainty in price assumptions, or provider restrictions. An empty or unavailable candidate pool must be reported explicitly, not obscured.

**Verification:** List objective per-stage acceptance criteria/tests. The model assignment is not an acceptance test for the implementation itself.

If the task is a one-step fix, a single-row table is appropriate. If no confirmed models exist, mark output as **conditional recommendations only**.
