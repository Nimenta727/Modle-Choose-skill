# 安装与模型推荐 / Installation and Routing

## 中文

要求 Python 3.10+，只使用标准库。仓库根目录执行：

~~~bash
python3 tools/install.py --target /path/to/project
python3 tools/install.py --target /path/to/project --agents claude
python3 tools/install.py --target /path/to/project --agents codex
python3 tools/install.py --target /path/to/project --no-plan-instructions
~~~

安装器复制完整 Skill 到 .claude/skills/model-router/ 与/或 .agents/skills/model-router/，可在 CLAUDE.md/AGENTS.md 追加明确标记的 Plan Mode 指令。已有 Skill 默认不覆盖；--force 仅在你明确同意并备份修改后使用。不会更改全局设置。在 Windows PowerShell 使用 py -3。

~~~bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format markdown
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/budget-plan.json --format json
python3 skills/model-router/scripts/update_models.py --offline
~~~

任务 JSON 中 surface 必须匹配实际环境（api、claude_code、codex 等）。--available 仅是用户声明，API 模型列表不能证明实际调用成功或界面可用。路由分数是启发式参考，模型信息过期会明确提示；建议不执行模型。

## English

Python 3.10+ and the standard library suffice. From the repository root:

~~~bash
python3 tools/install.py --target /path/to/project
python3 tools/install.py --target /path/to/project --agents claude
python3 tools/install.py --target /path/to/project --agents codex
python3 tools/install.py --target /path/to/project --no-plan-instructions
~~~

The installer copies the complete Skill to .claude/skills/model-router/ and/or .agents/skills/model-router/, optionally appending marked Plan Mode instructions to CLAUDE.md / AGENTS.md. Existing Skills are not overwritten unless --force is explicit; back up custom changes. No global settings are modified. On Windows use py -3.

~~~bash
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/project-plan.json --format markdown
python3 skills/model-router/scripts/route.py --task-file skills/model-router/examples/budget-plan.json --format json
python3 skills/model-router/scripts/update_models.py --offline
~~~

Set task.surface to the actual execution environment: api, claude_code, codex, etc. --available is user-reported availability; API inventory does not prove successful requests or UI access. Ranking is heuristic, stale snapshots are labeled, and recommendations do not execute models.
