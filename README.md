# Model Router — Plan Mode 模型选择 Skill

一个可移植的 **Agent Skill**：把项目计划拆分成任务阶段，在计划正文里写出 OpenAI GPT / Anthropic Claude 的**主选模型、备用模型、推理等级、选择依据和可用性**。它不会偷偷调用模型，不会因为模型写在官方目录里就假设你的 ChatGPT、Codex 或 Claude Code 账号能够使用它。

> V1.0 = 推荐/规划层；真正跨平台模型切换需额外的受授权 Orchestrator。适配 Claude Code 与 Codex 的项目级 Skill；其他支持 Agent Skills 的工具需要自行检查是否支持。

## 快速安装到另一个项目

克隆本仓库后，使用 Python 3.10+（无需第三方依赖）：

```bash
python3 scripts/install.py --target /path/to/your-project
# 只安装给 Claude Code:
python3 scripts/install.py --target /path/to/your-project --agents claude
# 需要重新覆盖已安装的 Skill 时:
python3 scripts/install.py --target /path/to/your-project --force
```

安装器复制 **完整可移植 Skill** 到 `.claude/skills/model-router/` 和 `.agents/skills/model-router/`，并在目标项目 `CLAUDE.md` / `AGENTS.md` 追加最小 Plan Mode 指令。只对你指定的目录生效；不会修改用户级全局设置。已有同名 Skill 时默认拒绝覆盖，避免丢失用户修改。若不想改动 Agent 指令，使用 `--no-plan-instructions`。

**手动安装**：复制 `skills/model-router/` 文件夹到 `~/.claude/skills/model-router/`（Claude Code）或 `.agents/skills/model-router/`（Codex 项目级）；在相应 Agent 指令中注明“生成计划前调用 model-router”。

**自动触发边界**：Agent Skills 可按描述自动发现，但不同版本和产品的 Plan Mode 不提供统一、绝对可靠的强制触发钩子。因此我们同时使用项目级 Agent 指令，并建议必要时显式调用 `/model-router`（Claude Code）或在 Codex 提示中指定 `$model-router`。

## 使用

以常规自然语言要求 AI 规划项目。计划应出现 `Model allocation / 模型分配`，逐阶段交付物、主选/备用、可用性和切换条件。

在本仓库目录中，无需任何 API Key 也可演示路由：

```bash
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json \
  --format markdown

# 仅对你声明可用的模型优先推荐（声明 != 已验证权限）
python3 skills/model-router/scripts/route.py \
  --task-file skills/model-router/examples/project-plan.json \
  --available gpt-6.2-sol,claude-sonnet-5-5

# 检查缓存是否过期（离线）
python3 skills/model-router/scripts/update_models.py --offline

# 联网比对官方模型 ID（只读；不会覆盖缓存或价格）
python3 skills/model-router/scripts/update_models.py --check

# 可选：通过自己账号的 API Key 读取 API 模型清单
OPENAI_API_KEY=... python3 skills/model-router/scripts/check_availability.py \
  --provider openai --output /tmp/openai-models.json
```

运行脚本结果并非实测模型排行榜。`--available` 是用户自报的可用列表；`--availability-file` 只有 `check_availability.py` 生成的对应 API surface 清单可作为已验证 API ID。`execution: true` 模式只有**已验证**访问才会产生候选，仍然**不会执行或切换模型**。官方 API 清单不证明 ChatGPT UI/Codex/Claude Code 的套餐权益。

## 维护模型目录

`skills/model-router/references/model-registry.json` 是唯一权威的本地快照。初版来源和日期见其中 `sources`、`verified_at`。脚本 `update_models.py --check` 只比对官方网页是否仍含现有 ID、是否可能有新 ID。**不能仅凭 HTML 自动修改价格、模型上下文或弃用状态**：这些字段需要从对应官方文档人工核对并更新 `verified_at`。网络不通时要标记快照过期，不能假装已刷新。

- 官方 OpenAI 模型：[OpenAI Models](https://developers.openai.com/api/docs/models)
- 官方 Anthropic 模型：[Claude Models overview](https://platform.claude.com/docs/en/models/overview)
- Claude Code Skill：[Skills](https://code.claude.com/docs/en/skills)
- Codex Skill：[Skills](https://developers.openai.com/codex/skills)

Anthropic Haiku 5.5 的目录价格为 **From**（起价），因此在数据文件中以 `price_floor_only: true` 区别于确定价格。正式核算以所在平台和用量计费为准。

## 测试

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q skills/model-router/scripts scripts
```

目录说明：`skills/model-router/` 为独立可安装技能；`.claude/skills/`、`.agents/skills/` 是本仓库的发现入口（轻量包装）；`scripts/install.py` 安装器；`tests/` 单元测试；`docs/routine/` 变更记录与下一步计划。

## 路线图

- V1：确定性推荐、已核实模型快照、Plan Mode 格式、API 可用性检查、安装器和测试。
- V1.1：增加评测集并支持用户的自定义模型质量权重；自动提醒官方模型弃用/价格差异（不自动改值）。
- V2：在用户明确授权、接入具体供应商 API 后实现可审计的跨模型 Agent 调度。
