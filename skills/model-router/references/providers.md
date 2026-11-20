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

## 中文说明 / Chinese guidance

请将官方模型发布信息、API 目录可见、一次实际请求成功和客户端/订阅模型权限严格区分。网页匹配有可能漏掉动态内容，新模型需要官方详情复核，不能未经授权发起付费请求或上传项目数据。

## English reminder

Distinguish published API IDs, account API inventory, successful calls and tool-specific entitlements. Scraped HTML is incomplete evidence. New candidates require manual review, never unauthorized paid probes or data transmission.

