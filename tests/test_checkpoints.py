"""Offline checkpoint, review, and concise handoff regression tests; no model calls."""
from __future__ import annotations

import contextlib
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.orchestrator import checkpoints, handoff_packet, prepare, run


def manifest() -> dict:
    return {"schema_version": 1, "stages": [
        {"id": "s01-analyze", "name": "Analyze", "agent": "claude", "provider": "anthropic",
         "model_id": "claude-example", "cli_model": "local-claude", "approved": True,
         "mode": "read-only", "prompt": "Inspect the code", "depends_on": []},
        {"id": "s02-implement", "name": "Implement", "agent": "codex", "provider": "openai",
         "model_id": "gpt-example", "cli_model": "local-codex", "approved": True,
         "mode": "read-only", "prompt": "Implement the plan", "depends_on": ["s01-analyze"]},
    ]}


class CheckpointTests(unittest.TestCase):
    def test_prepare_defaults_to_sequential_dependencies(self):
        t = {"stages": [{"name": "Design"}, {"name": "Implement"}]}
        r = {"stages": [{"name": "Design", "primary": {"id": "claude-test", "provider": "anthropic"}},
                         {"name": "Implement", "primary": {"id": "gpt-test", "provider": "openai"}}]}
        result = prepare.build_manifest(t, r)
        self.assertEqual(result["stages"][0]["depends_on"], [])
        self.assertEqual(result["stages"][1]["depends_on"], [result["stages"][0]["id"]])
        self.assertFalse(result["stages"][1]["approved"])

    def test_new_checkpoint_is_private_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            x = checkpoints.initialize(state, manifest())
            self.assertEqual(x["stages"]["s01-analyze"]["status"], "pending")
            if os.name == "posix":
                self.assertEqual(state.stat().st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(ValueError, "already exists"):
                checkpoints.initialize(state, manifest())

    def test_dependency_requires_human_acceptance_not_cli_exit(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            m = manifest()
            checkpoints.initialize(state, m)
            with self.assertRaisesRegex(ValueError, "dependency"):
                checkpoints.begin(state, m, "s02-implement")
            checkpoints.begin(state, m, "s01-analyze")
            checkpoints.complete(state, m, "s01-analyze", {"state": "cli_completed_unreviewed"})
            with self.assertRaisesRegex(ValueError, "dependency"):
                checkpoints.begin(state, m, "s02-implement")
            checkpoints.accept(state, m, "s01-analyze", "Tests examined; no code was changed.")
            self.assertEqual(checkpoints.begin(state, m, "s02-implement")["status"], "running")

    def test_repeated_call_does_not_duplicate_accepted_stage(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            m = manifest()
            checkpoints.initialize(state, m)
            checkpoints.begin(state, m, "s01-analyze")
            checkpoints.complete(state, m, "s01-analyze", {"state": "cli_completed_unreviewed"})
            with self.assertRaisesRegex(ValueError, "no silent re-execution"):
                checkpoints.begin(state, m, "s01-analyze")
            checkpoints.accept(state, m, "s01-analyze", "Human reviewer read CLI result and accepted it.")
            with self.assertRaisesRegex(ValueError, "no silent re-execution"):
                checkpoints.begin(state, m, "s01-analyze", retry_failed=True)

    def test_failure_requires_explicit_retry_and_is_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            m = manifest()
            checkpoints.initialize(state, m)
            checkpoints.begin(state, m, "s01-analyze")
            checkpoints.complete(state, m, "s01-analyze", {"state": "failed", "exit_code": 2})
            with self.assertRaises(ValueError):
                checkpoints.begin(state, m, "s01-analyze")
            checkpoints.begin(state, m, "s01-analyze", retry_failed=True)
            checkpoints.complete(state, m, "s01-analyze", {"state": "failed"})
            with self.assertRaisesRegex(ValueError, "maximum explicit attempts"):
                checkpoints.begin(state, m, "s01-analyze", retry_failed=True)

    def test_human_rejection_then_retry_and_accept_requires_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            m = manifest()
            checkpoints.initialize(state, m)
            checkpoints.begin(state, m, "s01-analyze")
            checkpoints.complete(state, m, "s01-analyze", {"state": "cli_completed_unreviewed"})
            with self.assertRaises(ValueError):
                checkpoints.accept(state, m, "s01-analyze", "no")
            checkpoints.reject(state, m, "s01-analyze", "Missing required evidence")
            self.assertEqual(checkpoints.begin(state, m, "s01-analyze", retry_failed=True)["attempts"], 2)

    def test_changed_manifest_invalidates_old_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            m = manifest()
            checkpoints.initialize(state, m)
            m["stages"][0]["prompt"] = "Changed prompt!"
            with self.assertRaisesRegex(ValueError, "mismatch"):
                checkpoints.load_state(state, m)

    def test_invalid_dependency_cycles_rejected(self):
        m = manifest()
        m["stages"][0]["depends_on"] = ["s02-implement"]
        with self.assertRaisesRegex(ValueError, "invalid dependency"):
            checkpoints.ensure_stage_ids(m)
        with self.assertRaises(ValueError):
            run.validate_manifest(m)

    def test_concurrent_lock_refuses_second_writer(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            checkpoints.initialize(state, manifest())
            with checkpoints.locked(state), self.assertRaisesRegex(ValueError, "locked"):
                checkpoints.begin(state, manifest(), "s01-analyze")

    def test_metadata_does_not_store_human_evidence_or_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            m = manifest()
            checkpoints.initialize(state, m)
            checkpoints.begin(state, m, "s01-analyze")
            checkpoints.complete(state, m, "s01-analyze", {"state": "cli_completed_unreviewed"})
            checkpoints.accept(state, m, "s01-analyze", "PRIVATE acceptance detail that must not persist")
            raw = state.read_text()
            self.assertNotIn("PRIVATE acceptance detail", raw)
            self.assertNotIn("Inspect the code", raw)
            self.assertIn("reviewer_evidence_sha256", raw)

    def test_checkpoint_cli_accept_needs_matching_confirmation(self):
        with tempfile.TemporaryDirectory() as td:
            m = manifest()
            path = Path(td) / "manifest.json"
            state = Path(td) / "checkpoint.json"
            path.write_text(json.dumps(m))
            checkpoints.initialize(state, m)
            with contextlib.redirect_stderr(StringIO()):
                rc = checkpoints.main(["--manifest", str(path), "--state", str(state),
                                       "--accept-stage", "s01-analyze", "--evidence", "Enough evidence to accept"])
            self.assertEqual(rc, 2)

    def test_compact_handoff_only_after_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            m = manifest()
            p = Path(td) / "s.json"
            checkpoints.initialize(p, m)
            state = checkpoints.load_state(p, m)
            summary = "Reviewed architecture and API decisions; implementation may proceed after approval."
            with self.assertRaises(ValueError):
                handoff_packet.build_packet(m, state, "s01-analyze", summary)
            checkpoints.begin(p, m, "s01-analyze")
            checkpoints.complete(p, m, "s01-analyze", {"state": "cli_completed_unreviewed"})
            checkpoints.accept(p, m, "s01-analyze", "Reviewer checked the requirements with tests")
            packet = handoff_packet.build_packet(m, checkpoints.load_state(p, m), "s01-analyze", summary)
            self.assertEqual(packet["status"], "human_reviewed_packet_not_transmitted")
            self.assertIn("summary_sha256", packet)
            self.assertNotIn("response_file", packet)
            self.assertNotIn("cli_events", packet)
            self.assertFalse("prompt" in packet)
            with self.assertRaises(ValueError):
                handoff_packet.build_packet(m, checkpoints.load_state(p, m), "s01-analyze", "x" * 3001)

    def test_runner_main_checkpointed_mock_call(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            workspace = base / "workspace"
            workspace.mkdir()
            row = manifest()["stages"][0]
            m = {"schema_version": 1, "stages": [row]}
            manifest_path = base / "manifest.json"
            manifest_path.write_text(json.dumps(m))
            state = base / "checkpoint.json"
            checkpoints.initialize(state, m)
            mock = {"stage_id": row["id"], "state": "cli_completed_unreviewed", "run_dir": str(base / "runs"), "exit_code": 0}
            with patch.object(run, "invoke_stage", return_value=mock) as fake, contextlib.redirect_stdout(StringIO()):
                rc = run.main(["--manifest", str(manifest_path), "--workspace", str(workspace),
                               "--stage", row["id"], "--execute", "--confirm-stage", row["id"],
                               "--checkpoint-file", str(state), "--output-dir", str(base / "runs")])
            self.assertEqual(rc, 0)
            fake.assert_called_once()
            self.assertEqual(checkpoints.load_state(state, m)["stages"][row["id"]]["status"], "cli_completed_unreviewed")
            with patch.object(run, "invoke_stage", side_effect=AssertionError("duplicate model call")), contextlib.redirect_stderr(StringIO()), contextlib.redirect_stdout(StringIO()):
                self.assertEqual(run.main(["--manifest", str(manifest_path), "--workspace", str(workspace),
                                           "--stage", row["id"], "--execute", "--confirm-stage", row["id"],
                                           "--checkpoint-file", str(state), "--output-dir", str(base / "runs")]), 2)

    def test_runner_rejects_checkpoint_inside_project(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            workspace.mkdir()
            m = {"schema_version": 1, "stages": [manifest()["stages"][0]]}
            mp = Path(td) / "manifest.json"
            mp.write_text(json.dumps(m))
            cp = workspace / "private.json"
            checkpoints.initialize(cp, m)
            with patch.object(run, "invoke_stage", side_effect=AssertionError("call")), contextlib.redirect_stderr(StringIO()):
                self.assertEqual(run.main(["--manifest", str(mp), "--workspace", str(workspace),
                                           "--stage", "s01-analyze", "--checkpoint-file", str(cp)]), 2)


if __name__ == "__main__":
    unittest.main()
