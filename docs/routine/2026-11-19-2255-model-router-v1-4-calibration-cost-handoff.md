# 2026-11-19 22:55 (+08:00) — V1.4 真实任务证据校准、成本参考及阶段交接

## 本次完成了什么

1. `skills/model-router/scripts/route.py` 新增项目分阶段的输入/输出 Token **预计总量**、未缓存 API 标价参考与项目小计；缺失估算时显示 unknown，部分覆盖时不伪报总预算，价格起价模型标注 lower-bound。
2. 新增可选的 `max_stage_api_reference_usd` 阶段预算硬条件；对没有估计、只有价格下限、非 API 订阅环境的情况采取保守失败策略。硬预算检查使用未舍入值，避免极小差额误判。
3. 新增可选 `--calibration-file`，仅接受最近 90 天、明确人工审核、符合 schema 的每模型/任务类别 ±8 分偏移。偏移只能影响**已通过硬约束**的候选排序，不能突破账号、权限、预算、能力或安全门槛；原模型目录不被修改。路由器不能独立鉴别人工审核声明的真伪。
4. `evals/compare_trials.py` 新增配对真实试验的候选校准建议：按冻结任务、验收标准、环境工具指纹及平台匹配，至少 6 个不同任务、每个模型每任务 2 次，输出未批准的建议和探索性统计，不自动套用。原始数据仍为空；没有实际比较模型质量。
5. `evals/score_trials.py` 支持真实计费和耗时不明时置空，不再将未知费用当成 $0，也不据此计算伪造的总成本。
6. `skills/model-router/scripts/handoff.py` 新增跨阶段交接文档模板，标记待执行/待审核；默认 stdout，不会悄悄写文件，需要 `--output-dir`，已有文件默认禁止覆盖。
7. 更新 Skill、路由政策、Plan Mode 输出模板、README、评测指南与 GitHub CI；添加可复现预算示例和 V1.4 回归测试。

## 修改文件及目的

- `skills/model-router/scripts/route.py`：预算估算、硬限额精度、校准加载与解释性输出。
- `evals/compare_trials.py`、`evals/score_trials.py`：配对证据审核与真实记录聚合。
- `skills/model-router/scripts/handoff.py`：阶段交接模板生成。
- `tests/test_v14.py`、`.github/workflows/tests.yml`：单测及 CI 烟雾测试。
- `skills/model-router/examples/budget-plan.json`：预算示例任务。
- `skills/model-router/SKILL.md`、`skills/model-router/references/{routing-policy.md,plan-template.md}`、`README.md`、`docs/evaluation.md`、`docs/v1.4.md`：用法与数据质量边界。

## 验证结果（本地，提交前）

- `python -m unittest discover -s tests -q`：**69/69 通过**。
- `python -m compileall -q scripts skills/model-router/scripts evals`：**通过**。
- `python evals/evaluate_routes.py`：**24/24 场景、186/186 规则断言通过**。
- `python evals/score_trials.py --trials evals/trials.json`：**0 条真实试验**，正确输出 `no_empirical_trials`。
- `python evals/compare_trials.py --trials evals/trials.json`：**0 条真实试验**，正确输出未审核的空建议；没有自动校准。
- `python skills/model-router/scripts/route.py --task-file skills/model-router/examples/budget-plan.json`：包含阶段 API 参考成本，3 阶段中仅 2 阶段具有 Token 估算，显示 partial。
- **GitHub CI 将在推送后核对**；此记录不提前宣称远程已通过。

## 仍然存在的限制和风险

- 没有获得用户已登录 Claude Code/Codex 的授权测试环境，**尚未实测 GUI Plan Mode 触发率或真实模型能力**；本轮所有质量校准均以真实输入数据为前提，没有伪造结果。
- 实际 API 帐单和订阅额度、缓存策略、工具附加费、超额重试不在成本估算内。
- 配对统计为探索性、未进行多重比较校正；须由独立人员检查实验可比性，不能凭一个 p 值宣布普适模型优劣。
- V1.4 不包含全局项目预算最优搜索、跨供应商权限调度或自动替用户切换模型。

## 下一步规划

1. 在用户授权的 Windows Hyper-V 测试环境中以独立测试账户执行 Claude Code/Codex Plan Mode 正负例，采集可观察 Skill 加载事件及计划表完整性；区分 CLI 与交互式 GUI。
2. 建立公开、冻结、可复现的同任务代码修复/重构/评审基准，至少六个独立任务并对每个模型重复运行，人工验证 SHA-256 工件/测试环境、权限与计费来源。
3. 由用户独立审核比较建议，发布单独的局部校准文件和评测说明，再观察对推荐的一致性和失败率影响。
4. 如有真实预算数据，研究 API 费用范围、缓存与重试修正以及跨阶段总预算优化；保持价格不确定性的明确标注。
