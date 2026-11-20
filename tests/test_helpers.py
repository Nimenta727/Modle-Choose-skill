import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/model-router"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


updater = module("model_updater", SKILL / "scripts/update_models.py")
availability = module("model_availability", SKILL / "scripts/check_availability.py")
installer = module("model_installer", ROOT / "tools/install.py")
registry = __import__("json").loads((SKILL / "references/model-registry.json").read_text())


class HelperTests(unittest.TestCase):
    def test_offline_snapshot_stale_after_time(self):
        audit = updater.audit(registry, None, now=datetime(2026, 11, 22, tzinfo=timezone.utc))
        self.assertTrue(audit["stale"])
        self.assertFalse(audit["official_ids_checked"])

    def test_official_html_detects_new_ids_without_mutating(self):
        check = updater.audit(registry, {"openai": "gpt-6.2-astra gpt-6.2-sol gpt-6.3-astra"},
                              now=datetime(2026, 11, 19, tzinfo=timezone.utc))
        self.assertEqual(check["providers"]["openai"]["new_candidate_ids"], ["gpt-6.3-astra"])
        self.assertEqual(len(registry["models"]), 8)

    def test_broad_version_detection_and_inventory_review(self):
        from datetime import timedelta
        new = updater.audit(registry, {"openai": "gpt-7-nova gpt-6.2-sol", "anthropic": "claude-zenith-6-1 claude-sonnet-5-5"},
                            now=datetime(2026, 11, 19, tzinfo=timezone.utc),
                            inventories=[{"provider": "openai", "surface": "api", "status": "listed",
                                          "checked_at": datetime(2026, 11, 19, tzinfo=timezone.utc).isoformat(),
                                          "available_models": ["gpt-7-nova", "gpt-6.2-sol"]}])
        self.assertEqual(new["providers"]["openai"]["new_candidate_ids"], ["gpt-7-nova"])
        self.assertEqual(new["providers"]["anthropic"]["new_candidate_ids"], ["claude-zenith-6-1"])
        self.assertEqual(new["providers"]["openai"]["account_inventory_candidates"], ["gpt-7-nova"])
        self.assertIn("openai", new["metadata_review_required"])
        self.assertEqual(len(registry["models"]), 8)

    def test_stale_inventory_is_ignored(self):
        inv = {"provider": "openai", "surface": "api", "status": "listed",
               "checked_at": datetime(2026, 11, 17, tzinfo=timezone.utc).isoformat(),
               "available_models": ["gpt-7-nova"]}
        new = updater.audit(registry, now=datetime(2026, 11, 19, tzinfo=timezone.utc), inventories=[inv])
        self.assertEqual(new["providers"]["openai"]["inventory_status"], "stale")
        self.assertEqual(new["providers"]["openai"]["account_inventory_candidates"], [])

    def test_no_api_key_does_not_claim_unavailable(self):
        from unittest.mock import patch
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            result = availability.fetch("openai")
        self.assertEqual(result["status"], "unverified")

    def test_installer_copies_standalone_and_preserves_existing_agent_doc(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            (dest / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
            output = installer.install(dest, ["claude", "codex"], force=False, include_instructions=True)
            self.assertTrue((dest / ".claude/skills/model-router/SKILL.md").exists())
            self.assertTrue((dest / ".agents/skills/model-router/references/model-registry.json").exists())
            self.assertTrue((dest / ".agents/skills/model-router/scripts/route.py").exists())
            self.assertTrue((dest / "AGENTS.md").read_text().startswith("# Existing"))
            self.assertIn(installer.MARK_BEGIN, (dest / "CLAUDE.md").read_text())
            with self.assertRaises(ValueError):
                installer.install(dest, ["claude"], force=False, include_instructions=True)

    def test_installer_marker_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "AGENTS.md"
            self.assertEqual(installer.append_instruction(file), "configured")
            self.assertEqual(installer.append_instruction(file), "already configured")
            self.assertEqual(file.read_text().count(installer.MARK_BEGIN), 1)


if __name__ == "__main__":
    unittest.main()
