"""Offline-only numeric-usage reporting tests."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.evals import usage_report


class NumericSummaryTests(unittest.TestCase):
    def test_missing_cost_unknown_without_savings_claim(self):
        rows = [{"agent": "codex", "reported_usage": {"fields": {"input_tokens": 5, "cached_input_tokens": 3}}},
                {"agent": "codex", "state": "failed"},
                {"agent": "claude", "reported_usage": {"fields": {"input_tokens": 7,
                    "claude_cli_estimated_cost_usd": 0.2}}}]
        summary = usage_report.aggregate(rows)
        self.assertEqual(summary["groups"]["codex"]["runs_without_usage"], 1)
        self.assertIsNone(summary["groups"]["codex"]["client_estimated_cost_usd"])
        self.assertFalse(summary["groups"]["codex"]["cost_coverage_complete"])
        self.assertIsNone(summary["measured_savings"])

    def test_only_numeric_fields_are_aggregated(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "run1"
            path.mkdir()
            (path / "response.md").write_text("PRIVATE MODEL OUTPUT")
            record = {"agent": "claude", "reported_usage": {"fields": {
                "input_tokens": 4, "cache_read_input_tokens": 2,
                "debug": "PRIVATE SECRET"}}}
            (path / "result.json").write_text(json.dumps(record))
            outcome = usage_report.aggregate([json.loads((path / "result.json").read_text())])
            self.assertEqual(outcome["groups"]["claude"]["tokens"]["input_tokens"], 4)
            self.assertNotIn("PRIVATE", str(outcome))


if __name__ == "__main__":
    unittest.main()
