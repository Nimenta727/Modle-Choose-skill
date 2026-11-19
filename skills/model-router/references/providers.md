# Official sources and runtime boundaries

- OpenAI API models: https://developers.openai.com/api/docs/models
- OpenAI model selection: https://developers.openai.com/api/docs/guides/model-selection
- OpenAI model retirement: https://developers.openai.com/api/docs/deprecations
- Anthropic models: https://platform.claude.com/docs/en/models/overview
- Anthropic API list models: https://platform.claude.com/docs/en/api/models/list
- Anthropic retirement: https://platform.claude.com/docs/en/about-claude/model-deprecations
- Claude Code Skills: https://code.claude.com/docs/en/skills
- Codex Skills: https://developers.openai.com/codex/skills

## Separate concerns

1. **Documented API ID**: an official source states that a model exists; metadata must be reviewed independently.
2. **Listed in account inventory**: API model-list endpoint returned the ID. Listing alone is not proof a particular model request works. Only useful for the matching API provider and current time window.
3. **Successful API request**: a trusted external caller provides fresh evidence that this exact model worked under the intended credential/surface. The Skill does not issue probe requests, and cannot cryptographically authenticate an arbitrary evidence JSON file.
4. **Tool-specific entitlement**: Claude Code, Codex, ChatGPT and Claude web/app each have independent selection rules, aliases and subscription conditions. No API catalog proves native access to them.

This repository never silently changes published model metadata based on scraped HTML or an account inventory. Official page string matching may miss rendered content or find misleading text. Review a candidate's detail page before editing context, capabilities, lifecycle, prices or ratings. Distinguish confirmed observations from heuristic assumptions.
