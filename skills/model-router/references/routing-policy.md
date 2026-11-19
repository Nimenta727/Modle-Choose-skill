# Routing policy (V1)

## Hard filters before scores

1. Require a published model ID, active lifecycle, permitted provider, appropriate input/tool features, enough context and output tokens.
2. For execution, require **confirmed account+surface availability**. `api` merely says a vendor documents an API ID; it does not prove access. If no confirmation exists, output a clearly **conditional recommendation** and never claim it can execute.
3. Do not treat ChatGPT UI subscriptions, Claude web subscriptions, API entitlements, Codex or Claude Code aliases as interchangeable.
4. If security, privacy, compliance, regional restrictions, budget ceilings or deployment restrictions exclude a provider, hard-exclude that provider. Never upload private project data merely to probe availability.
5. A model marked deprecated or retired is never a preferred candidate. Expired/unchecked registry data must be visibly marked stale.
6. If there are no eligible models, say "no eligible model" with the failed constraints; do not silently remove constraints.

## Scoring

`route.py` computes policy-heuristic scores; they are **not benchmark measurements**. Suggested priorities: `quality`, `balanced` (default), `cost`.

- Quality fit is an editable 1-5 prior for the task type and complexity. For high/critical-risk work, apply an additional minimum fit threshold and have a separate check/review stage.
- Cost is based on listed USD per million input/output tokens using a stated 80% input / 20% output token blend; all price estimates ignore caching, tool fees, tiered prices, and variable API billing. `price_floor_only` marks a lower bound.
- Speed is the vendor qualitative latency tier, not a measured ms value.
- Fit to platform is a hard gate rather than an unverified bonus.
- Tie-breaking is deterministic by model ID. A candidate lacking verified availability is eligible only for provisional planning.

## Recommended phase constraints

| Phase | Minimum task fit for low / medium / high | Typical effort |
|---|---|---|
| Requirements and documentation | 2 / 3 / 4 | low / medium / high |
| Architecture, complex debugging, security reviews | 2 / 4 / 5 | low / high / high |
| Coding, tests, UI, extraction | 2 / 3 / 4 | low / medium / high |

Use task breakdown and explicit context to set phase complexity; never infer a need for the largest model solely because a task says "plan".

## Re-route triggers

Reevaluate after failing tests twice without progress, repeated hallucinated API features, unexpected context/tool requirements, changed budget, model retirement/availability changes or a new security constraint. Prefer reducing scope or asking for permission before increasing cost. For high-risk modifications, include independent validation even if the same model performs the work.

## What the skill actually controls

In `recommendation` mode, only adds text to the plan; no model switch is performed. In `execution` mode, an external orchestrator must enforce selection and permissions. Claude Code, Codex and ChatGPT do not automatically grant cross-vendor execution rights just because a skill recommends another provider.
