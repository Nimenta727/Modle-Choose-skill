"""Static and CLI integration checks; not real Claude Code/Codex E2E tests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/model-router"


class ContractsTests(unittest.TestCase):
    def test_both_agent_entrypoints_and_canonical_skill(self):
        for path in ["AGENTS.md", "CLAUDE.md", ".agents/skills/model-router/SKILL.md", ".claude/skills/model-router/SKILL.md"]:
            self.assertIn("model-router", (ROOT / path).read_text(encoding="utf-8"))
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: model-router\n"))
        self.assertIn("Model allocation", skill)

    def test_route_cli_non_api_conditional_is_not_native(self):
        task = {"surface": "claude_code", "stages": [{"name": "API design", "type": "architecture", "complexity": "high"}]}
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "t.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SKILL / "scripts/route.py"), "--task-file", str(task_path), "--format", "json"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 3)
            data = json.loads(result.stdout)
            stage = data["stages"][0]
            self.assertIsNone(stage["primary"])
            self.assertEqual(stage["external_advisory"]["status"], "external-conditional")
            result = subprocess.run([sys.executable, str(SKILL / "scripts/route.py"), "--task-file", str(task_path),
                                     "--available", "claude-opus-5-5", "--format", "json"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            self.assertEqual(data["stages"][0]["primary"]["availability"], "user-reported")

    def test_audit_offline_is_not_live_verification(self):
        result = subprocess.run([sys.executable, str(SKILL / "scripts/update_models.py"), "--offline"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertFalse(data["official_ids_checked"])
        self.assertIn("metadata_review_required", data)

    def test_model_registry_has_field_provenance(self):
        data = json.loads((SKILL / "references/model-registry.json").read_text(encoding="utf-8"))
        self.assertIn("pricing", data["field_provenance"])
        self.assertEqual(data["field_provenance"]["task_fitness"]["status"], "not benchmarked")

    def test_scheduled_audit_is_read_only_no_secret_calls(self):
        text = (ROOT / ".github/workflows/model-audit.yml").read_text(encoding="utf-8")
        self.assertIn("schedule:", text)
        self.assertIn("--report-file model-audit.json", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("secrets.", text)


if __name__ == "__main__":
    unittest.main()
