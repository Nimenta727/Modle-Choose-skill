---
name: model-router
description: >-
  Run when entering Plan Mode or drafting a software plan; route stages to current
  OpenAI and Anthropic models with primary, backup, availability and evidence.
---

This repository maintains the canonical skill at `skills/model-router/SKILL.md`.
**Read and follow that file**, then its referenced `references/*` and scripts within
`skills/model-router/` before preparing the plan. Do not use this wrapper alone
as the entire routing policy. For reuse in another project, run `tools/install.py`,
which copies a complete standalone skill into `.claude/skills/model-router/`.

## 中文说明 / Chinese instructions

这里是本仓库中的轻量发现入口。独立安装的完整 Skill 在 skills/model-router/SKILL.md。请在计划中列出模型分工和权限证据；真实 CLI 执行需要独立许可。其他项目使用 tools/install.py 安装。

## English guidance

This is only a lightweight discovery wrapper. The full portable Skill lives at skills/model-router/SKILL.md. Plans must show allocation and access confidence; live CLI runs need separate user approval. Install into another project using tools/install.py.

