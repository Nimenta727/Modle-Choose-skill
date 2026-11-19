---
name: model-router
description: >-
  Run when entering Plan Mode or drafting a software plan; route stages to current
  OpenAI and Anthropic models with primary, backup, availability and evidence.
---

This repository maintains the canonical skill at `skills/model-router/SKILL.md`.
**Read and follow that file**, then its referenced `references/*` and scripts within
`skills/model-router/` before preparing the plan. Do not use this wrapper alone
as the entire routing policy. For reuse in another project, run `scripts/install.py`,
which copies a complete standalone skill into `.claude/skills/model-router/`.
