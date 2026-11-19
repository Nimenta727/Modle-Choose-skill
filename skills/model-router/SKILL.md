---
name: model-router
description: >-
  Use when creating or revising a software implementation plan, especially in Plan Mode:
  break work into phases, compare current OpenAI GPT and Anthropic Claude models,
  choose primary/backup models by quality, cost, access and constraints, and include
  a clearly labeled model-allocation table in the plan. Also use when asked which
  model should handle a development stage or when model availability changes.
---

# Model Router — Plan Mode skill

## Required workflow

1. Read this file. Then consult `references/routing-policy.md`, `references/plan-template.md`, and `references/model-registry.json` within **this skill directory**. If installed via a project wrapper, resolve paths from the repository root.
2. Identify task goal, planned phases and deliverables, repository context, risks, deadline, budget, required features, context size, permitted providers, and current execution surface. Do not ask unnecessary setup questions; use `balanced` defaults while flagging uncertainty.
3. If network is permitted and the registry is over 24 hours old, use `scripts/update_models.py` to check official model IDs. Check vendor changes/deprecations before treating cached data as current. If offline or verification fails, keep the cache and **show its date**. Never manufacture a "verified today" status.
4. Determine which models the **current account and execution surface** can actually call. `scripts/check_availability.py` optionally checks API keys. Absence of a key is not a negative result. A provider API catalog does not prove ChatGPT or Claude Code access. For recommendation-only planning, list unverified models as **conditional**; do not present them as executable choices.
5. Apply hard filters first (features, context, platform, lifecycle, provider/region/privacy restrictions, budget, confirmed access if executing). Then choose minimum acceptable capability for each task's complexity and risk. Use `scripts/route.py` if shell execution is available; otherwise follow `references/routing-policy.md` manually. The script's fitness values are **heuristic priors**, not benchmark scores.
6. In the plan itself, include **Model allocation / 模型分配** following `references/plan-template.md`: primary model and explicit ID, reasoning effort, rationale, backup with ID, account availability confidence, registry timestamp, expected stage deliverables, escalation triggers, and validation. Keep one row for a one-stage task.
7. When a model cannot satisfy a new constraint or verified tests fail repeatedly, reroute **before** proceeding. Do not make an actual model switch, remote call, API purchase, or cross-provider transfer without authorized orchestration and the user's applicable permissions.

## CLI reference (Python 3.10+, no third-party dependencies)

```bash
python3 scripts/route.py --task-file examples/project-plan.json --format markdown
python3 scripts/route.py --task-file examples/project-plan.json --available gpt-6.2-sol,claude-sonnet-5-5
python3 scripts/update_models.py --check  # requires network; read-only
python3 scripts/check_availability.py --provider openai  # needs OPENAI_API_KEY
```

Scripts above are relative to this skill directory. An actual installation uses `skills/model-router/scripts/*` if launched at repository root. No credentials are stored in the registry. Provider model IDs are separate from UI model names and product access.

## Do not

- Treat recommendation text as a real execution or background operation.
- Assert all named models are available in ChatGPT, Codex, Claude Code, or a specific account.
- Invent a newly announced model, price, context limit or benchmark.
- Automatically use a high-cost model for every planning or coding stage.
- Strip the user's technical milestones from a plan to make room for model recommendations.
