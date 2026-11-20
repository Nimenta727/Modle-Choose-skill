# 模型目录与时效性 / Model Catalog and Freshness

## 中文

唯一权威的本地快照在 skills/model-router/references/model-registry.json。以下信息**不能混为一谈**：官方模型文档里存在、API 列表显示、真实调用成功、某个 Claude Code/Codex/ChatGPT 界面可选择。

~~~bash
python3 skills/model-router/scripts/update_models.py --offline
python3 skills/model-router/scripts/update_models.py --check --report-file model-review.json
~~~

检查工具只生成只读审核报告，不自动修改模型价格、参数、发布时间或可用性。网页可能动态渲染，未匹配某 ID 不能证明其已退役。正式更新目录时，必须核对官方详情页、字段来源、核实日期与退役信息。每周 GitHub Actions 仅上传待审报告，不自动应用。

官方资料：[OpenAI Models](https://developers.openai.com/api/docs/models)、[Anthropic Models](https://platform.claude.com/docs/en/models/overview)、[OpenAI Deprecations](https://developers.openai.com/api/docs/deprecations)、[Anthropic Deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)。

## English

The single canonical local registry is skills/model-router/references/model-registry.json. Do **not** conflate documented existence, API-list visibility, an actually successful request, or model selection in Claude Code/Codex/ChatGPT.

~~~bash
python3 skills/model-router/scripts/update_models.py --offline
python3 skills/model-router/scripts/update_models.py --check --report-file model-review.json
~~~

The checker produces **read-only** review reports. It never silently updates pricing, context, lifecycle or account permissions. Dynamically rendered pages may omit IDs; absence in scraped HTML does not prove retirement. Review official model details and field provenance before modifying the registry. Scheduled GitHub Actions only uploads an audit artifact.

Official sources: [OpenAI Models](https://developers.openai.com/api/docs/models), [Anthropic Models](https://platform.claude.com/docs/en/models/overview), [OpenAI Deprecations](https://developers.openai.com/api/docs/deprecations), [Anthropic Deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations).
