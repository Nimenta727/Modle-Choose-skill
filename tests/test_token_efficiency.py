"""Offline-only token budget and model-continuity regression tests."""
from __future__ import annotations

import contextlib
import importlib.util
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.orchestrator import prepare, run, token_budget

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("router_for_token_tests", ROOT / "skills/model-router/scripts/route.py")
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)
REGISTRY = router.load_json(ROOT / "skills/model-router/references/model-registry.json")


def stage(**extra):
    return {"id": "s01-check", "name": "Check", "agent": "claude", "provider": "anthropic",
            "model_id": "claude-example", "cli_model": "sonnet", "approved": True,
            "mode": "read-only", "prompt": "Inspect the project", "depends_on": [], **extra}


class TokenBudgetTests(unittest.TestCase):
    def test_default_caps(self):
        x = token_budget.policy_for(stage())
        self.assertEqual((x["max_prompt_chars"], x["max_handoff_chars"], x["max_claude_turns"]), (6000, 1500, 6))

    def test_invalid_budget_fails(self):
        for item in ({"max_prompt_chars": True}, {"max_prompt_chars": 12},
                     {"max_handoff_chars": -1}, {"max_claude_turns": 20}, {"unknown": 1}):
            with self.subTest(item=item), self.assertRaises(ValueError):
                token_budget.policy_for(stage(token_budget=item))

    def test_path_hints_refuse_traversal_secrets_and_absolute(self):
        for path in ("../secret", "/root/file", "C:/windows/file", ".git/config", "node_modules/x",
                     ".env.production", "docs//bad", "./bad", "folder/../bad", "a\\b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                token_budget.validate_context_files([path])
        self.assertEqual(token_budget.validate_context_files(["src/a.py", "src/a.py"]), ["src/a.py"])

    def test_too_many_files(self):
        with self.assertRaises(ValueError):
            token_budget.validate_context_files([f"src/{n}.py" for n in range(9)])

    def test_only_path_hints_in_prompt(self):
        x = run.prepare_prompt(stage(context_files=["src/one.py"]))
        self.assertIn("src/one.py", x)
        self.assertIn("paths only", x)

    def test_input_over_cap_not_silently_truncated(self):
        row = stage(prompt="Z" * 7000)
        with self.assertRaisesRegex(ValueError, "max_prompt_chars"):
            token_budget.budget_report(row, run.prepare_prompt(row))

    def test_handoff_over_cap_rejected(self):
        row = stage()
        with self.assertRaisesRegex(ValueError, "max_handoff_chars"):
            token_budget.budget_report(row, run.prepare_prompt(row, "X" * 1600), "X" * 1600)

    def test_explicit_cap_override(self):
        row = stage(prompt="Z" * 6500, token_budget={"max_prompt_chars": 7000})
        self.assertLess(token_budget.budget_report(row, run.prepare_prompt(row))["prompt_chars"], 7000)

    def test_approximate_not_exact_billing(self):
        report = token_budget.budget_report(stage(), run.prepare_prompt(stage()))
        self.assertGreater(report["estimated_prompt_tokens"], 0)
        self.assertIn("not tokenizer", report["estimate_method"])

    def test_claude_max_turns_is_configurable(self):
        cmd = run.make_command(stage(token_budget={"max_claude_turns": 4}), Path("/tmp/out"), "claude")
        self.assertEqual(cmd[cmd.index("--max-turns") + 1], "4")

    def test_prepare_preserves_paths_and_approvals(self):
        task = {"stages": [{"name": "Review", "context_files": ["README.md"]}]}
        routing = {"stages": [{"name": "Review", "primary": {"id": "claude-test", "provider": "anthropic"}}]}
        row = prepare.build_manifest(task, routing)["stages"][0]
        self.assertEqual(row["context_files"], ["README.md"])
        self.assertFalse(row["approved"])
        self.assertEqual(row["token_budget"]["max_prompt_chars"], 6000)

    def test_dry_run_budget_report_zero_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.json"
            path.write_text(json.dumps({"schema_version": 1, "stages": [stage()]}))
            with patch.object(run, "invoke_stage", side_effect=AssertionError("unexpected model call")), contextlib.redirect_stdout(StringIO()) as output:
                rc = run.main(["--manifest", str(path), "--workspace", tmp, "--stage", "s01-check"])
            self.assertEqual(rc, 0)
            self.assertIn("PROMPT BUDGET:", output.getvalue())

    def test_live_over_cap_blocked_before_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.json"
            path.write_text(json.dumps({"schema_version": 1, "stages": [stage(prompt="X" * 7000)]}))
            with patch.object(run, "invoke_stage", side_effect=AssertionError("unexpected model call")), contextlib.redirect_stderr(StringIO()):
                rc = run.main(["--manifest", str(path), "--workspace", tmp, "--stage", "s01-check",
                               "--execute", "--confirm-stage", "s01-check"])
            self.assertEqual(rc, 2)


class ContinuityTests(unittest.TestCase):
    def test_invalid_parameters_fail_closed(self):
        task = {"stages": [{"name": "A", "type": "analysis"}], "minimize_switches": True}
        for bad in (True, -1, 11, float("inf"), "3"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                router.validate_task({**task, "max_continuity_score_gap": bad})
        with self.assertRaises(ValueError):
            router.validate_task({**task, "minimize_switches": "yes"})

    def test_hard_filters_still_enforced(self):
        task = {"surface": "api", "minimize_switches": True, "max_continuity_score_gap": 10,
                "stages": [{"name": "Docs", "type": "documentation", "complexity": "low"},
                           {"name": "Review", "type": "review", "complexity": "high", "risk": "critical"}]}
        result = router.route(task, REGISTRY)
        self.assertEqual(result["stages"][1]["min_fitness"], 5)
        self.assertIn(result["stages"][1]["primary"]["id"], {"gpt-6.2-astra", "claude-opus-5-5", "claude-fable-5-2"})

    def test_report_switches_and_backward_compat(self):
        task = {"surface": "api", "stages": [
            {"name": "A", "type": "analysis", "complexity": "low"},
            {"name": "B", "type": "documentation", "complexity": "low"}]}
        default = router.route(task, REGISTRY)
        preferred = router.route({**task, "minimize_switches": True, "max_continuity_score_gap": 10}, REGISTRY)
        self.assertFalse(default["minimize_switches"])
        self.assertTrue(preferred["minimize_switches"])
        self.assertLessEqual(preferred["model_switches"], default["model_switches"])
        self.assertIn("Model transitions", router.render_markdown(preferred))


if __name__ == "__main__":
    unittest.main()
