# 2026-11-19 22:39 (+08:00) — Model Router V1.3 评测与客户端测试工具

## 中文原始记录 / Chinese original

## 做了什么

- 增加 24 个带固定时钟的离线路由契约案例，覆盖 API/客户端 Surface、授权证据、平台回退、预算、风险/复杂度、工具能力、上下文限制和多阶段计划。
- 新增 `evals/evaluate_routes.py`：对每条规则输出 actual/expected 和失败明细，导出 JSON/Markdown、返回非零状态供 CI 阻断。
- 新增 `evals/live_triggers.py`、`evals/trigger_cases.json`：模拟真实 Claude Code Plan Mode 与 Codex 只读 CLI 的隔离测试；默认 dry-run，必须使用 `--execute` 才会发起账号请求。
- 同时评估模型分配表完整性、无关任务不触发和可观察到的 SKILL 文件读取；明确表格出现不是 Skill 被调用的证明。
- 新增 `evals/score_trials.py`、空数据 `evals/trials.json` 与评测手册，为以后收集真实通过率、延迟和成本提供严格入口，当前不伪造模型性能测评。
- 将离线路由评测和 dry-run smoke 加入 GitHub Actions；测试报告上传 artifacts；修改 README、Skill 和 `.gitignore`。

## 验证

- 本地 `python3 -m unittest discover -s tests -v`：46 个测试通过（提交前最终复测）。
- 本地路由评测：24/24 场景、186/186 规则断言通过（固定日期数据，不代表实时模型权限）。
- CLI dry-run：无模型请求；真实 Claude Code/Codex CLI 在此环境未安装，因此**没有进行收费调用或测得真实触发率**。
- GitHub CI：推送后检查运行结果并如实更新交付说明。

## 下一步

1. 在用户安装并登录的 Claude Code 和 Codex 中运行真实 CLI smoke，并分别验证 GUI/交互式 Plan Mode；记录客户端版本与成功/失败日志。
2. 选择同一套公开可复现的任务，重复测试不同可用模型，收集通过率、成本、用时、上下文及返工次数。
3. 对照独立验收标准，在样本量充分后校准任务适配权重，严禁用合成边界测试分数冒充模型能力。
4. 继续提高跨平台别名映射、输出解析鲁棒性和项目级预算估算。

## English summary (historical record)

Added offline policy scenarios, an opt-in Claude Code/Codex Plan Mode activation harness, and real-task score aggregation conventions. Offline passing tests do not establish authenticated CLI activation or model quality. Next: measured outcomes and cost calibration.

**Context:** This is a historical log, not the current installation guide. Paths and commands may have been superseded by tools/ and docs/guides/. The original Chinese text preserves the checks reported at the time.
