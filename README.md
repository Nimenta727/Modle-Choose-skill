# Model Router — Plan Mode 模型选择 Skill

跨 Claude Code / Codex 项目可安装的 **Agent Skill**，在开发计划内分配 OpenAI 和 Anthropic 模型，同时展示证据、执行平台、备用方案、模型目录的核实时间和切换条件。

**当前版本 V1.4：在 V1.3 基础上增加可审查的配对真实任务评测、人工批准校准、项目 API 参考成本估算和阶段交接模板。它不自动执行模型调用、不切换供应商、不擅自上传项目代码。** `evals/trials.json` 当前为空，未产生真实模型质量排名；策略启发式分数不代表独立实测。

## 项目安装

要求 Python 3.10+，仅使用标准库。从克隆仓库根目录运行：

```bash
python3 scripts/install.py --target /path/to/your-project
# 只安装 Claude Code:
python3 scripts/install.py --target /path/to/your-project --agents claude
# 只安装 Codex:
python3 scripts/install.py --target /path/to/your-project --agents codex
# 不修改项目级 AGENTS.md/CLAUDE.md:
python3 scripts/install.py --target /path/to/your-project --no-plan-instructions
```

安装程序复制完整 `skills/model-router/` 到项目 `.claude/skills/model-router/` 与/或 `.agents/skills/model-router/`，并以明确标记块追加最小 Plan Mode 指令。已有同名 Skill 默认拒绝覆盖；`--force` 可显式覆盖（覆盖前请备份自己的更改）。不改动全局用户设置。可手动调用 Claude Code `/model-router` 或在 Codex 中提示 `$model-router`；**Plan Mode 是否主动触发仍取决于运行工具的 Agent 指令支持**，本仓库没有实际运行两个客户端的触发率评测。

## 推荐如何工作

路由流程：任务分阶段 → 检查模型目录与元数据日期 → 确认当前 `surface` 的模型访问情况 → 筛除不符合硬约束的模型 → 按质量/成本/速度评分 → 在计划内显示主选、备用、理由、可用性及外部条件性建议。

| 访问状态 | 含义 | 可直接执行？ |
|---|---|---|
| `call-verified` | 外部调用方提供近期成功请求证据（需单独信任来源） | 仅代表通过推荐门槛，依然要有实际调度器 |
| `listed` | API 模型清单返回该 ID，未执行模型请求 | **否** |
| `user-reported` | 用户表示这个 ID 可在当前产品中选择 | **否** |
| `conditional` | 官方模型目录中存在，但账号访问未知 | **否** |
| `external-conditional` | 当前平台无原生候选时给出的跨平台参考 | **否** |

注意：`api`、`claude_code`、`codex`、`chatgpt`、`claude_app` 是**不同运行环境**，ChatGPT/Claude 订阅不等同于 API 账号可用性。`--available` 是用户自报，而不是调用验证；官方 API 模型 ID 也不必等于产品界面展示名或别名。

## 在仓库中运行

```bash
# 例子默认 surface=api，因此会显示条件性的 API 推荐
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json --format markdown

# 为 Claude Code 编写任务输入时，将 JSON 的 surface 改为 claude_code
# 没有确认的原生可用模型时，显示「无合格原生模型」及明确标注的外部建议
# 如果你已确认当前平台的模型可用，传入该平台的原生 ID（用户自报）
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json \
  --available claude-sonnet-5-5

# 仅检查 OpenAI API 模型清单；不实际发起付费模型请求
OPENAI_API_KEY=... python3 skills/model-router/scripts/check_availability.py \
  --provider openai --output /tmp/openai-inventory.json
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json \
  --availability-file /tmp/openai-inventory.json

# Anthropic 同理，使用 ANTHROPIC_API_KEY
# 可以为多个提供商重复 --availability-file 参数
```

`check_availability.py` 不保存 API Key；模型清单只证明 API 列表包含该模型，不证明请求成功。即便使用 `execution: true`，这里也只检查是否存在外部调用方提供的 `call_verified` 证据，**不会实际执行**。此 Skill 不会为了获取证据偷偷发起付费 API 请求。

## 模型目录与更新

唯一主目录：`skills/model-router/references/model-registry.json`。快照包含官方来源、`verified_at`、字段级来源说明和人工评估分数。维护命令：

```bash
# 检查缓存是否过期：不联网
python3 skills/model-router/scripts/update_models.py --offline

# 联网审核官方文档里的模型 ID：只生成审核报告，不修改目录
python3 skills/model-router/scripts/update_models.py --check \
  --report-file /tmp/model-review.json

# 合并 API 清单中可能出现的新模型，生成待审核候选列表（无自动改价）
python3 skills/model-router/scripts/update_models.py --offline \
  --inventory-file /tmp/openai-inventory.json --report-file /tmp/model-review.json
```

**V1.2 的自动更新能力是发现与审计，不是自动信任和写入新参数**。公共网页可能是客户端渲染的，缺失的字符串不代表模型退役；新模型、价格、生命周期、功能和上下文必须由官方详情页核对后才能修改模型目录。每周一的只读 GitHub Actions 审计会生成一个 `model-catalog-review` artifact。网络失败时改用离线报告，并保留过期标记；不会使用任何私有 API Key。

官方数据来源：
- OpenAI：https://developers.openai.com/api/docs/models
- Anthropic：https://platform.claude.com/docs/en/models/overview
- API 模型清单：https://platform.claude.com/docs/en/api/models/list

详见 [`references/routing-policy.md`](skills/model-router/references/routing-policy.md) 和 [`references/providers.md`](skills/model-router/references/providers.md)。

## V1.3 评测与真实 Plan Mode 验证

新增 `evals/routing_cases.json`（24 个离线策略场景）与 `evals/evaluate_routes.py`，在 CI 中验证平台/可用性/成本/风险约束和模型分配表；所有断言是**策略契约**，不代表模型性能分数。

```bash
# 离线评测，完全免费
python3 evals/evaluate_routes.py --json-out /tmp/router-eval.json

# 默认 dry-run：不会连接 Claude/Codex，也不消费额度
python3 evals/live_triggers.py --agent claude
python3 evals/live_triggers.py --agent codex

# 可选：在安装且登录 CLI 的电脑上，显式运行真实测试（可能消耗账号额度）
python3 evals/live_triggers.py --agent claude --execute --max-runs 1
python3 evals/live_triggers.py --agent codex --execute --max-runs 1
```

真实触发评测在临时空项目中安装 Skill，使用 Claude 的 Plan Mode 或 Codex 的只读非交互 CLI，覆盖隐式/显式触发及负例。**输出包含模型分配表 ≠ 能证明 Skill 一定被调用**；因此还单独统计轨迹中可观察到的 Skill 文件读取。由于 CI 没有 CLI 凭据，也没有进入交互式 Plan Mode，本仓库目前没有真实客户端触发率数据。

`evals/score_trials.py` 支持汇总真实任务的验收通过率、用时和成本；`evals/trials.json` 初始为空，**没有伪造任何实测数据**。完整方法、风险和说明见 [`docs/evaluation.md`](docs/evaluation.md) 和 [`evals/quality_rubric.md`](evals/quality_rubric.md)。

## 测试

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q skills/model-router/scripts scripts evals
```

`tests/` 包含硬性过滤、模型目录与权限状态、不同运行环境、默认值、预算、工具安装和 Plan Mode 输出契约等测试；GitHub Actions 在提交/PR 时运行。**自动化单测不能替代在真实 Claude Code/Codex 中的端到端触发测试。**

## 结构与路线图

- `skills/model-router/SKILL.md`：可复制 Skill 入口；`references/`：目录、策略和计划模板；`scripts/route.py`：确定性推荐算法。
- `.claude/skills/` 与 `.agents/skills/`：本仓库自身的轻量发现入口；`scripts/install.py`：项目安装器。
- `docs/routine/`：每次 GitHub 变更对应的时间戳、修改内容、验证和下一步计划。
- V1.1（已完成）：运行环境门槛、API 列表与成功调用分离、预算/默认值一致性。
- V1.2（已完成）：跨版本 ID 候选发现、API 清单审计、字段来源和只读定期报告。
- V1.3（已完成评测基础设施）：24 个离线边界案例、CLI 隐式/显式/负例测试工具、真实任务结果聚合器；尚未测得真实客户端触发率或模型实际能力排名。
- V1.4（本轮已实现工具，真实结果待采集）：配对验收结果比较、人工审核后可选校准、API 参考成本估算与阶段交接模板。
- V2：用户明确授权后可审计的跨平台模型调度；不通过 Skill 文本偷渡权限。

## V1.4：项目成本预算与阶段交接

可选地在任务 JSON 的每个 `stage` 中填写**该阶段所有请求预计的 Token 总量**（不是单次 context window，也不是实际已测用量）：

```json
{
  "name": "Implementation",
  "type": "coding",
  "estimated_input_tokens": 200000,
  "estimated_output_tokens": 50000,
  "max_stage_api_reference_usd": 1.5
}
```

必须同时提供两个估计字段；不确定时**两个字段都省略**，报告将显示 `unestimated`，不会填假零。`max_stage_api_reference_usd` 是**可选的、仅适用于 API 标价参考的阶段硬上限**：没有 Token 估计、只有价格下限或运行平台不是 `api` 时，不会假设已满足上限。总项目金额只是已估算阶段的 API **未缓存标价参考小计**，**不是预算承诺或 Claude/ChatGPT 订阅实际费用**。默认不包含工具收费、缓存政策、区域附加费等。输入/输出 Tokens 是估计，不是计费记录。

```bash
# 路由结果包含 API 参考成本小计，缺失预计 Token 时显式显示 unknown
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/budget-plan.json --format markdown

# 默认输出到 stdout（无文件写入）；显式指定目录后创建待填写交接文档
python3 skills/model-router/scripts/handoff.py \
  --task-file skills/model-router/examples/project-plan.json
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json \
  --format json > /tmp/model-router-route.json
python3 skills/model-router/scripts/handoff.py \
  --task-file skills/model-router/examples/project-plan.json \
  --route-result /tmp/model-router-route.json \
  --output-dir /tmp/model-router-handoffs
```

交接模板保留待确认约束、成果证据、验收标准和后续输入，**不会推断已完成代码修改或测试**。已有同名文件默认拒绝覆盖；明确指定 `--force` 才允许覆盖。不要将含敏感上下文的交接文件提交至公开仓库。

## V1.4：真实任务配对比较与审核校准

`evals/trials.json` 仍为空；**离线策略测试 100% 不代表任何模型质量评测成绩**。录入真实任务结果时，在 `run_id`、`task_id`、`task_type`、`model_id`、`passed` 外，还需要 `surface`、固定任务代码快照 `fixture_sha256`、固定验收标准 `rubric_sha256` 和同条件测试工具环境指纹 `harness_sha256`，后 3 个为 SHA-256 64 位十六进制文本。比较至少要求 **6 个不同匹配任务、每个任务每个模型至少 2 次运行**，并使用探索性单侧符号检验。这里的检验不自动纠正多组比较，不能替代独立审核，不能用来宣称模型具备普遍优势。

```bash
python3 evals/score_trials.py --trials evals/trials.json
python3 evals/compare_trials.py --trials evals/trials.json --json-out /tmp/model-router-proposal.json
```

比较器输出的 `proposal_unreviewed` **不能**被 `route.py` 应用。必须由人核对测试场景、接受标准、不同模型调用方式、偏差、结论及证据后，再另行创建 `status: user_reviewed`、`reviewed_at` (ISO8601 UTC 带时区) 和 `adjustments` 的 JSON。人工通过的偏移每个模型/任务类型最多 ±8 个评分点、90 天过期；只影响第二阶段**候选排序**，不绕开硬约束、风险门槛或权限验证。审核文件为用户本地资产，不随仓库默认发布；即使标记审核通过，路由器也不会独立证明证据真实性。

```bash
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json \
  --calibration-file /path/to/reviewed-calibration.json
```

本版本**没有**运行任何真实 Claude Code/Codex 账号任务，因此尚不能给出真实触发成功率、任务通过率或成本节省百分比。更多要求与人工审核样例请见 [V1.4 评测说明](docs/v1.4.md)。
