# Token 成本与上下文优化 / Token Efficiency and Context Budgeting

## 中文

### 目标：降低真实消耗，不牺牲任务完成质量

1. **按需加载文件**：任务阶段可指定 `context_files`（最多 8 个仓库相对路径）。执行器只向模型发送路径，不重复粘贴文件正文或完整聊天历史。它不是访问控制，客户端仍可以读取其他有权限的文件。
2. **提示词/交接字符上限**：每阶段默认初始提示词 6000 字符，已审核交接 1500 字符。超限拒绝，**不会悄悄截断**。如果复杂任务需要更多信息，可明确调高上限（最多 40000 / 12000 字符）。
3. **控制 Claude Code 轮次**：默认最多 6 轮，按阶段可设置为 1–12。`--max-turns` 是轮次限制，不是总 Token 预算；Codex CLI 尚无相同跨版本保障。任务过早中断可能增加返工，不能一味降低轮次。
4. **连续模型优先**：在任务中设置 `minimize_switches: true` 与 `max_continuity_score_gap: 3`（允许 0–10）。上一阶段的模型必须仍满足所有原有硬性约束，且可用性等级相同、启发式得分没有明显落后，才会保留。默认关闭，避免旧任务行为变化。
5. **轻量交接与验收**：传递人工审核后的必要结论，不自动传播完整日志。模型切换仍需要额外权限；测试通过和实际费用才是最终评价依据。

### 如何使用

```bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/token-efficient-plan.json --format json > routing-result.json
python3 tools/orchestrator/prepare.py --task-file skills/model-router/examples/token-efficient-plan.json --route-file routing-result.json --output local-execution.json
python3 tools/orchestrator/run.py --manifest local-execution.json --workspace . --all
```

执行清单示例：

```json
"token_budget": {
  "max_prompt_chars": 6000,
  "max_handoff_chars": 1500,
  "max_claude_turns": 6
}
```

上述命令默认只生成和预览计划，**不会调用模型**。dry-run 显示的 Token 估算是字符启发式，**不是供应商真实 Tokenizer 或账单**。未计入模型后续文件读取、工具输出、隐藏推理、额外轮次和缓存。要评估节省比例，需要对同一任务、相同模型和质量验收要求做真实对照试验。

### 缓存不是自动节省保证

OpenAI API 有不同的缓存输入计价，Claude Code 也可能利用提示词缓存。但是本项目**不控制**各 CLI 的底层缓存实现，不能保证缓存命中；重复发送更多文本有时反而增加费用。

## English

### Optimize end-to-end usage, not merely prompt length

1. **Progressive context:** Up to eight `context_files` paths per stage. The orchestrator sends path references, not duplicated source files or whole conversations. Paths are hints, not sandbox permissions.
2. **Input guards:** Initial prompt default 6,000 characters and reviewed handoff default 1,500. Oversized inputs fail closed, without silently discarding user requirements. Operators can explicitly raise caps to 40,000 and 12,000.
3. **Turn policy:** Claude Code defaults to six turns, configurable from one to twelve. A turn limit is *not* a billable token cap, and Codex has no equivalent enforced limit in this adapter. Too-low caps can increase retries.
4. **Optional model affinity:** `minimize_switches: true` with `max_continuity_score_gap` (default 3, allowed 0–10) only favors the previous model when it still passes all hard gates, has identical availability confidence, and remains close in heuristic score. It is off by default.
5. **Reviewed handoffs:** Share concise, user-approved summaries, not raw transcripts. Keep objective task acceptance criteria.

### Measuring costs

Use the commands above for **dry-run previews with no model calls**. Heuristic token counts are not measured provider tokens or total bills. Downstream tool reads, additional turns, reasoning and caching can dominate real costs. Real savings must be established using matched authenticated tasks with equivalent acceptance results.

### Official references / 官方参考

- [Anthropic guidance on reducing Claude Code usage](https://claude.com/resources/articles/maximizing-the-value-of-your-claude-code-sessions)
- [Claude Code usage and limits](https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code)
- [OpenAI API pricing and cached input](https://platform.openai.com/pricing/)
- [LiteLLM session-affinity routing](https://docs.litellm.ai/docs/routing)
