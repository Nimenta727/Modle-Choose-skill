# 贡献指南 / Contributing

## 中文

本项目重视**低 Token 开销、明确权限和可重复验证**。贡献前请先阅读 [架构](docs/architecture.md)、[安全说明](SECURITY.md) 与 [发行指南](docs/guides/release.md)。

- Skill 保持独立可安装，依赖 Python 标准库，不让普通推荐任务必须安装仓库级执行器。
- 所有模型可用性声明、价格、排名、权限证据需标明来源、核实时间和验证范围。离线规则测试不能当成真实模型表现测试。
- 真实 CLI 调用必须显式授权；不要提交 API Key、私有项目、敏感日志或完整模型会话。
- 提交前运行：`python3 -m unittest discover -s tests -v`、`python3 tools/evals/evaluate_routes.py` 和 `python3 tools/check_docs.py`。
- 新增/修改使用说明须有中英双语；每次 GitHub 修改在同一提交新增 `docs/routine/YYYY-MM-DD-HHMM-summary.md`，说明改动、测试和下一步。
- 本仓库采用 [Apache License 2.0](LICENSE)。提交代码前请确认拥有必要授权、保留第三方版权和许可声明，并在修改文件时按许可证要求标记变更。

## English

This project prioritizes **low token overhead, explicit permissions and reproducible verification**. Read [architecture](docs/architecture.md), [security](SECURITY.md) and [release guide](docs/guides/release.md) before contributing.

- Keep the Skill standalone and standard-library-only; host orchestration is optional.
- Ground model access, pricing, ranking and permissions in dated evidence. Offline routing assertions are not empirical model benchmarks.
- Live CLI requests require authorization. Never commit API keys, private projects, sensitive traces or full model transcripts.
- Run `python3 -m unittest discover -s tests -v`, `python3 tools/evals/evaluate_routes.py` and `python3 tools/check_docs.py` before submitting changes.
- Document user-facing changes bilingually, and add a dated `docs/routine/` log with changes, observed tests and next steps in the same commit.
- This project uses the [Apache License 2.0](LICENSE). Contributors should ensure they have the rights to contribute, preserve applicable third-party notices, and prominently mark changes as required by the license.
