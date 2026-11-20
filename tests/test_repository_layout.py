"""Offline regression checks for the portable Skill and bilingual repository layout."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LayoutTests(unittest.TestCase):
    def test_portable_skill_and_host_tools_present(self):
        for path in (
            "skills/model-router/SKILL.md",
            "skills/model-router/scripts/route.py",
            "tools/install.py", "tools/evals/evaluate_routes.py",
            "tools/evals/trials.json",
            "tools/package_release.py", "tools/check_docs.py",
            "release/version.json", "release/notes.md",
            "docs/guides/release.md", "CHANGELOG.md",
            "CONTRIBUTING.md", "SECURITY.md", "tools/orchestrator/prepare.py",
            "tools/orchestrator/run.py",
        ):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())

    def test_obsolete_paths_removed(self):
        for path in (
            "scripts/install.py", "evals/score_trials.py",
            "orchestrator/run.py", "docs/evaluation.md",
            "docs/v1.4.md", "docs/v2.0-execution.md",
            "evals/quality_rubric.md",
        ):
            with self.subTest(path=path):
                self.assertFalse((ROOT / path).exists())

    def test_all_user_docs_contain_both_languages(self):
        public_docs = [
            ROOT / "README.md", ROOT / "AGENTS.md",
            ROOT / "CLAUDE.md",
            *sorted((ROOT / "docs").rglob("*.md")),
            ROOT / "skills/model-router/SKILL.md",
            *sorted((ROOT / "skills/model-router/references").glob("*.md")),
            ROOT / ".agents/skills/model-router/SKILL.md",
            ROOT / ".claude/skills/model-router/SKILL.md",
        ]
        self.assertGreaterEqual(len(public_docs), 15)
        for file in public_docs:
            with self.subTest(path=file.relative_to(ROOT)):
                text = file.read_text(encoding="utf-8")
                self.assertRegex(text, r"[\u4e00-\u9fff]")
                self.assertRegex(text, r"[A-Za-z]{4}")
                self.assertTrue(
                    "## English" in text or "## 中文" in text,
                    f"missing bilingual section in {file}",
                )

    def test_consolidated_guides_and_history_exist(self):
        for path in (
            "docs/README.md", "docs/architecture.md",
            "docs/guides/setup.md", "docs/guides/execution.md",
            "docs/guides/evaluation.md", "docs/guides/calibration.md",
            "docs/guides/catalog.md", "docs/routine/README.md",
        ):
            self.assertTrue((ROOT / path).is_file(), path)
        logs = list((ROOT / "docs/routine").glob("20??-??-??-*.md"))
        self.assertGreaterEqual(len(logs), 9)

    def test_workflow_uses_new_tool_paths(self):
        text = (ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
        self.assertIn("tools/evals/evaluate_routes.py", text)
        self.assertIn("tools/evals/trials.json", text)
        self.assertIn("tools/orchestrator/run.py", text)
        self.assertNotIn("--trials evals/trials.json", text)


if __name__ == "__main__":
    unittest.main()
