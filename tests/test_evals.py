"""V1.3 regression suite for deterministic eval harnesses."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


policy = module("policy_eval", ROOT / "evals/evaluate_routes.py")
live = module("live_eval", ROOT / "evals/live_triggers.py")
trials = module("trial_eval", ROOT / "evals/score_trials.py")
registry = json.loads((ROOT / "skills/model-router/references/model-registry.json").read_text(encoding="utf-8"))
suite = json.loads((ROOT / "evals/routing_cases.json").read_text(encoding="utf-8"))


class EvaluationTests(unittest.TestCase):
    def test_offline_eval_cases_all_pass(self):
        report = policy.evaluate(suite, registry)
        self.assertEqual(report["case_total"], 24)
        self.assertEqual(report["case_passed"], 24)
        self.assertGreaterEqual(report["checks_total"], 180)
        self.assertEqual(report["checks_passed"], report["checks_total"])
        self.assertEqual(report["evaluation_kind"], "offline-policy-contract-not-model-quality")

    def test_failure_is_explainable_and_nonzero(self):
        broken = json.loads(json.dumps(suite))
        broken["cases"][0]["expect"]["stages"][0]["primary"] = False
        report = policy.evaluate(broken, registry)
        self.assertEqual(report["case_passed"], report["case_total"] - 1)
        failures = [c for c in report["cases"][0]["checks"] if not c["passed"]]
        self.assertEqual(failures[0]["name"], "stage1.primary_exists")
        self.assertIn("Failed assertions", policy.as_markdown(report))

    def test_duplicate_cases_rejected(self):
        broken = json.loads(json.dumps(suite))
        broken["cases"].append(broken["cases"][0])
        with self.assertRaises(ValueError):
            policy.evaluate(broken, registry)

    def test_cli_output_reports_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            result = subprocess.run([sys.executable, str(ROOT / "evals/evaluate_routes.py"),
                                     "--json-out", str(dest / "report.json"),
                                     "--md-out", str(dest / "report.md")],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads((dest / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["case_total"], 24)
            self.assertEqual(len(payload["suite_sha256"]), 64)
            self.assertIn("24/24", (dest / "report.md").read_text(encoding="utf-8"))

    def test_case_ids_cannot_escape_trace_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            path.write_text(json.dumps({"schema_version": 1, "cases": [
                {"id": "../../other", "prompt": "hello", "expects_allocation": False}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                live.load_cases(path)

    def test_codex_trace_final_and_actual_tool_read(self):
        trace = "\n".join(json.dumps(v) for v in [
            {"type": "item.completed", "item": {"type": "command_execution", "command": "cat .agents/skills/model-router/SKILL.md"}},
            {"type": "item.completed", "item": {"type": "agent_message", "text":
             "## Model allocation / 模型分配\n| 阶段 | 主选 | 备用 |\n|---|---|---|\n| build | Sol | Sonnet |"}}
        ])
        output = live.extract_result("codex", trace)
        self.assertTrue(output["skill_file_read_observed"])
        self.assertTrue(output["allocation_heading"])
        self.assertTrue(output["allocation_contract"])

    def test_mentions_in_messages_are_not_skill_read_evidence(self):
        trace = json.dumps({"type": "item.completed", "item": {"type": "agent_message",
                           "text": "Read .agents/skills/model-router/SKILL.md. Model allocation only."}})
        output = live.extract_result("codex", trace)
        self.assertFalse(output["skill_file_read_observed"])
        self.assertFalse(output["allocation_contract"])

    def test_claude_trace_plan_and_tool_evidence(self):
        trace = "\n".join(json.dumps(v) for v in [
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read",
             "input": {"file_path": ".claude/skills/model-router/SKILL.md"}}]}},
            {"type": "result", "result": "## 模型分配\n| 阶段 | 主选 | 备用 |\n|---|---|---|\n| build | Opus | Sonnet |"},
        ])
        output = live.extract_result("claude", trace)
        self.assertTrue(output["allocation_contract"])
        self.assertTrue(output["skill_file_read_observed"])

    def test_negative_control_trace(self):
        trace = json.dumps({"type": "result", "result": "The function adds two numbers."})
        output = live.extract_result("claude", trace)
        self.assertFalse(output["allocation_heading"])
        self.assertFalse(output["skill_file_read_observed"])

    def test_live_commands_are_read_only_plan_mode(self):
        codex = live.command_for("codex", "PLAN")
        claude = live.command_for("claude", "PLAN")
        self.assertIn("read-only", codex)
        self.assertNotIn("--full-auto", codex)
        self.assertIn("plan", claude)
        self.assertIn("stream-json", claude)
        self.assertNotIn("--dangerously-skip-permissions", claude)

    def test_dry_run_does_not_call_client(self):
        result = subprocess.run([sys.executable, str(ROOT / "evals/live_triggers.py"),
                                 "--agent", "codex", "--max-runs", "2"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["mode"], "dry-run")
        self.assertEqual(data["evaluated"], 0)
        self.assertTrue(all(x["status"] == "skipped" for x in data["results"]))

    def test_isolated_project_writes_only_temp_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            live.prepare_workspace(path, "codex")
            self.assertTrue((path / "AGENTS.md").exists())
            self.assertTrue((path / ".agents/skills/model-router/SKILL.md").exists())
            self.assertTrue((path / "sample.py").exists())
            self.assertFalse((path / "CLAUDE.md").exists())

    def test_zero_trial_summary_cannot_claim_measured_quality(self):
        report = trials.compute_report({"schema_version": 1, "trials": []})
        self.assertEqual(report["status"], "no_empirical_trials")
        self.assertEqual(report["groups"], [])

    def test_trial_summary_marks_small_samples_unreliable(self):
        data = {"schema_version": 1, "trials": [
            {"run_id": "r1", "task_id": "task-1", "task_type": "coding", "model_id": "m1",
             "passed": True, "cost_usd": 1.0, "elapsed_seconds": 20},
            {"run_id": "r2", "task_id": "task-2", "task_type": "coding", "model_id": "m1",
             "passed": False, "cost_usd": 2.0, "elapsed_seconds": 40},
        ]}
        report = trials.compute_report(data)
        self.assertEqual(report["groups"][0]["acceptance_rate"], 0.5)
        self.assertFalse(report["groups"][0]["sample_sufficient"])
        self.assertEqual(report["groups"][0]["median_elapsed_seconds"], 30.0)

    def test_trial_validation_rejects_bad_values(self):
        row = {"run_id": "r1", "task_id": "task", "task_type": "coding", "model_id": "m",
               "passed": True, "cost_usd": -1, "elapsed_seconds": 10}
        with self.assertRaises(ValueError):
            trials.compute_report({"schema_version": 1, "trials": [row]})

    def test_summarize_does_not_conflate_compliance_and_activation(self):
        summary = live.summarize("codex", [
            {"id": "p", "status": "passed", "expected_allocation": True,
             "allocation_heading": True, "allocation_contract": True, "skill_file_read_observed": False},
            {"id": "n", "status": "passed", "expected_allocation": False,
             "allocation_heading": False, "allocation_contract": False, "skill_file_read_observed": False}], "live")
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["observable_skill_file_reads"], 0)
        self.assertEqual(summary["negative_without_allocation"], 1)


if __name__ == "__main__":
    unittest.main()
