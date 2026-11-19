# Providers, sources, and surface boundaries

- OpenAI model catalog: https://developers.openai.com/api/docs/models
- OpenAI model selection: https://developers.openai.com/api/docs/guides/model-selection
- OpenAI model deprecations: https://developers.openai.com/api/docs/deprecations
- Anthropic models: https://platform.claude.com/docs/en/models/overview
- Anthropic model deprecations: https://platform.claude.com/docs/en/about-claude/model-deprecations
- Claude Code skills: https://code.claude.com/docs/en/skills
- Codex skills: https://developers.openai.com/codex/skills

## Reliability hierarchy

1. Explicit account-specific, surface-specific model inventory or provider tool confirmation (for execution).
2. Official vendor catalog for model existence, IDs, limits, and published base pricing.
3. Model evaluations from a representative workload (recommended to override heuristic task_fit priors).
4. Local cache (display timestamp and stale warning).

Do not scrape unofficial ranking sites to silently rewrite the catalog. If an official page lists new models, `update_models.py` only reports them as possible new IDs; a human or reviewed PR must explicitly add abilities, availability, and pricing. Pricing, deprecations and context may change separately from IDs. Read official model detail pages when updating.

`api` in the bundled registry is a vendor-documentation channel, not an account-level entitlement. Codex, ChatGPT, Claude Code and Claude app model lists must be verified separately. Claude Code may use aliases (e.g. `opus`), which are product settings rather than guaranteed raw API IDs. Do not assert that a ChatGPT subscription includes API credits or that Claude Code can transparently run an OpenAI model.
