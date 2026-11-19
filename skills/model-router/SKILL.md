---
name: model-router
description: >-
  Use when creating or revising a software implementation plan, particularly Plan Mode:
  break work into stages and recommend OpenAI GPT or Anthropic Claude models based on
  verified surface access, quality/cost/speed constraints, current documented models,
  and explicitly labeled primary/backup/external advisory allocations.
---

# Model Router — Plan Mode skill (V1.3)

## Required workflow

1. Read this file and `references/routing-policy.md`, `references/plan-template.md`, `references/model-registry.json`, and `references/providers.md` from **this installed skill directory**.
2. Identify the user's phases and deliverables, requirements, risks, budget, tool needs, surface (`api`, `claude_code`, `codex`, `chatgpt`, `claude_app`, `other`) and explicitly available native model IDs. Use `balanced` defaults when uncertain, rather than interrogating the user for optional preferences.
3. When the registry is older than 24 hours and network access is permitted, run `scripts/update_models.py --check` to **audit** official public model pages. If inaccessible, keep the dated cache and label it stale. A successful check never silently refreshes `verified_at`, model pricing or other metadata. Consult the relevant official detail page before changing the canonical registry.
4. For API, `scripts/check_availability.py` optionally returns `status: listed` with a timestamp and **provider**; this is not proof a model request will succeed. It never validates a subscription to ChatGPT/Codex/Claude Code. For a non-API surface, use only explicitly observed or user-reported native model IDs for primary/backup recommendations; no implicit cross-platform mapping is allowed.
5. Apply hard filters (surface, lifecycle, allowed providers, privacy, required capabilities, context/output, hard price cap, risk threshold) before heuristic scoring. Use `scripts/route.py` when shell access exists; otherwise follow `references/routing-policy.md`. Heuristic scores are **not** external benchmark measurements.
6. Add `Model allocation / 模型分配` from `references/plan-template.md` **inside** the technical plan, with primary/backup, effort, evidence, registry date, stage outcomes and switch triggers. When there is no known native model, output `无合格原生模型` with an explicitly non-executable `external-conditional` suggestion if useful; do not omit the user's technical plan.
7. Reroute when tests fail twice without progress or confirmed constraints change. The Skill does **not** call models, switch accounts, purchase API credits or send code to another vendor. A separate authorized orchestrator must handle actual execution and prove access.

## CLI examples (Python 3.10+, standard library only)

```bash
# From the installed skill root (not the consuming project root):
python3 scripts/route.py --task-file examples/project-plan.json --format markdown
# Explicitly reported native models on the task.surface; NOT an access proof:
python3 scripts/route.py --task-file examples/project-plan.json --available claude-sonnet-5-5
# API model-list checks, not a successful model request:
python3 scripts/check_availability.py --provider openai --output /tmp/openai-inventory.json
python3 scripts/route.py --task-file examples/project-plan.json --availability-file /tmp/openai-inventory.json
# Discovery and maintenance (no registry mutation):
python3 scripts/update_models.py --check --report-file /tmp/model-review.json
python3 scripts/update_models.py --offline --inventory-file /tmp/openai-inventory.json
```

For a repository checkout use `skills/model-router/scripts/route.py`, etc. Input examples default to `surface: api`, but a real Claude Code/Codex plan must explicitly set its own surface. `execution: true` only activates **route gating** and needs trusted `call_verified` evidence from a separately authorized caller. There is no actual model invocation in this project.

## Never

- Equate API model inventory with a successful paid request or with UI/product access.
- Report an external conditional suggestion as a native primary or auto-selected model.
- Claim that a documentation check updates official prices, lifecycle, or verified timestamps.
- Use a price-floor-only estimate to satisfy a hard budget constraint.
- Change the user's technical deliverables, silently transmit private code across vendors, or make an unauthorized API call.

## Validation & evidence policy

When reporting whether this Skill works, distinguish policy unit/eval results from real Claude Code / Codex activation. The repository's `evals/evaluate_routes.py` validates deterministic routing contracts; `evals/live_triggers.py` is an optional **explicitly authorized** account-backed smoke runner and defaults to no model calls. Its Plan Mode table checks are not proof of internal Skill activation. Read `docs/evaluation.md` in the repository for the rubric; do not invent live invocation or empirical model-quality metrics. Never auto-tune `model-registry.json` from synthetic route cases.
