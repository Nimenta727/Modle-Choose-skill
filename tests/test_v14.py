"""V1.4 regression: API cost reference, reviewed calibration, paired trials and handoff templates."""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/model-router"
NOW = datetime(2026, 11, 19, 14, 0, tzinfo=timezone.utc)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


router = module("router_v14", SKILL / "scripts/route.py")
compare = module("compare_v14", ROOT / "evals/compare_trials.py")
handoff = module("handoff_v14", SKILL / "scripts/handoff.py")
score = module("score_v14", ROOT / "evals/score_trials.py")
REGISTRY = router.load_json(SKILL / "references/model-registry.json")


def task(**stage):
    s = {"name": "Build", "type": "coding", "complexity": "medium", "deliverable": "Compiled files"}
    s.update(stage)
    return {"surface": "api", "stages": [s]}


def reviewed(**changes):
    d = {"schema_version": 1, "status": "user_reviewed", "reviewed_at": NOW.isoformat(),
         "adjustments": [{"model_id": "gpt-6.2-sol", "task_type": "coding", "score_delta": 4,
                          "evidence": "paired task study report 2026-11-19"}]}
    d.update(changes)
    return d


def synthetic_trials(n=6):
    rows = []
    for t in range(n):
        for model in ("gpt-6.2-sol", "claude-sonnet-5-5"):
            for repeat in range(2):
                rows.append({"run_id": f"t{t}-{model}-{repeat}", "task_id": f"task-{t}",
                             "task_type": "coding", "model_id": model,
                             "passed": model == "gpt-6.2-sol", "surface": "api",
                             "fixture_sha256": f"{t+1:064x}", "rubric_sha256": "a" * 64,
                             "harness_sha256": "b" * 64})
    return {"schema_version": 1, "trials": rows}


class CostEstimatorTests(unittest.TestCase):
    def test_without_estimates_no_fabricated_zero(self):
        result = router.route(task(), REGISTRY, now=NOW)
        self.assertEqual(result["project_cost"]["status"], "unestimated")
        self.assertIsNone(result["project_cost"]["api_reference_total_usd"])
        self.assertIn("unestimated", router.render_markdown(result))

    def test_estimate_is_per_stage_total_not_context_window(self):
        result = router.route(task(estimated_input_tokens=200000, estimated_output_tokens=50000),
                              REGISTRY, now=NOW, available={"gpt-6.2-sol"})
        self.assertEqual(result["stages"][0]["primary"]["id"], "gpt-6.2-sol")
        self.assertEqual(result["project_cost"]["api_reference_total_usd"], 0.9)
        self.assertEqual(result["project_cost"]["status"], "api-list-reference")
        self.assertIn("$0.900000", router.render_markdown(result))

    def test_partial_estimates_are_explicit(self):
        x = task(estimated_input_tokens=200000, estimated_output_tokens=50000)
        x["stages"].append({"name": "Review", "type": "review", "complexity": "high"})
        result = router.route(x, REGISTRY, now=NOW)
        self.assertEqual(result["project_cost"]["status"], "partial")
        self.assertEqual(result["project_cost"]["stages_estimated"], 1)
        self.assertTrue(any("unestimated stages" in w for w in result["warnings"]))

    def test_price_floor_label(self):
        m = next(m for m in REGISTRY["models"] if m["id"] == "claude-haiku-5-5")
        e = router.api_cost_estimate(m, {"estimated_input_tokens": 1000000, "estimated_output_tokens": 1000000})
        self.assertEqual(e["status"], "lower-bound")
        self.assertEqual(e["api_reference_usd"], 0.6)

    def test_nonapi_subscription_not_zero_bill(self):
        x = task(estimated_input_tokens=50000, estimated_output_tokens=20000)
        x["surface"] = "claude_code"
        result = router.route(x, REGISTRY, now=NOW, available={"claude-sonnet-5-5"})
        self.assertEqual(result["project_cost"]["billing_surface"], "claude_code")
        self.assertTrue(any("NOT the actual cost" in w for w in result["warnings"]))

    def test_stage_budget_requires_estimates_and_known_price(self):
        x = task(max_stage_api_reference_usd=0.9)
        result = router.route(x, REGISTRY, now=NOW)
        self.assertIsNone(result["stages"][0]["primary"])
        x["stages"][0].update(estimated_input_tokens=100000, estimated_output_tokens=100000)
        result = router.route(x, REGISTRY, now=NOW)
        self.assertIsNotNone(result["stages"][0]["primary"])
        self.assertTrue(all((r["api_cost_estimate"]["api_reference_usd"] <= 0.9)
                            for r in [result["stages"][0]["primary"]]))
        x["stages"][0]["max_stage_api_reference_usd"] = 0.0
        self.assertIsNone(router.route(x, REGISTRY, now=NOW)["stages"][0]["primary"])

    def test_hard_budget_uses_unrounded_price(self):
        # 1 input token costs more than zero but would round to $0.000000.
        x = task(estimated_input_tokens=1, estimated_output_tokens=0,
                 max_stage_api_reference_usd=0.0)
        self.assertIsNone(router.route(x, REGISTRY, now=NOW)["stages"][0]["primary"])

    def test_invalid_estimates_and_budget_rejected(self):
        for bad in [task(estimated_input_tokens=1),
                    task(estimated_input_tokens=0, estimated_output_tokens=0),
                    task(estimated_input_tokens=10, estimated_output_tokens=-1),
                    task(estimated_input_tokens=True, estimated_output_tokens=10),
                    task(max_stage_api_reference_usd=float("nan"))]:
            with self.subTest(stage=bad["stages"][0]):
                with self.assertRaises(ValueError):
                    router.route(bad, REGISTRY, now=NOW)


class CalibrationTests(unittest.TestCase):
    def test_calibration_is_opt_in_bounded_and_explained(self):
        raw = router.route(task(), REGISTRY, now=NOW, available={"gpt-6.2-sol"})
        tuned = router.route(task(), REGISTRY, now=NOW, available={"gpt-6.2-sol"}, calibration=reviewed())
        self.assertFalse(raw["calibration_applied"])
        self.assertTrue(tuned["calibration_applied"])
        self.assertEqual(tuned["stages"][0]["primary"]["score_adjustment"], 4.0)
        self.assertEqual(raw["stages"][0]["primary"]["score_adjustment"], 0.0)
        self.assertTrue(any("NOT independently verified" in w for w in tuned["warnings"]))

    def test_raw_proposal_cannot_apply(self):
        proposal = compare.compare_trials(synthetic_trials())
        with self.assertRaises(ValueError):
            router.route(task(), REGISTRY, now=NOW, calibration=proposal)

    def test_invalid_overlarge_duplicate_unknown_calibrations_fail(self):
        for broken in [reviewed(adjustments=[{**reviewed()["adjustments"][0], "score_delta": 9}]),
                       reviewed(adjustments=reviewed()["adjustments"] * 2),
                       reviewed(adjustments=[{**reviewed()["adjustments"][0], "model_id": "future-mystery"}]),
                       reviewed(reviewed_at="invalid"),
                       reviewed(reviewed_at=(NOW + timedelta(days=2)).isoformat())]:
            with self.assertRaises(ValueError):
                router.route(task(), REGISTRY, now=NOW, calibration=broken)

    def test_stale_calibration_ignored_not_applied(self):
        old = reviewed(reviewed_at=(NOW - timedelta(days=91)).isoformat())
        result = router.route(task(), REGISTRY, now=NOW, calibration=old)
        self.assertFalse(result["calibration_applied"])
        self.assertTrue(any("older than 90 days" in w for w in result["warnings"]))


class PairedEvaluationTests(unittest.TestCase):
    def test_empty_dataset_is_no_empirical_evidence(self):
        out = compare.compare_trials({"schema_version": 1, "trials": []})
        self.assertEqual(out["suggested_adjustments"], [])
        self.assertEqual(out["comparisons"], [])
        self.assertEqual(out["status"], "proposal_unreviewed")

    def test_repeated_matched_success_proposes_review_not_autotune(self):
        out = compare.compare_trials(synthetic_trials())
        self.assertEqual(out["run_count"], 24)
        self.assertEqual(out["comparisons"][0]["matched_distinct_tasks"], 6)
        self.assertEqual(out["comparisons"][0]["status"], "b_better")  # a=Claude, b=GPT
        self.assertLess(out["comparisons"][0]["one_sided_sign_test_p"], 0.05)
        suggestions = {r["model_id"]: r["score_delta"] for r in out["suggested_adjustments"]}
        self.assertEqual(suggestions["gpt-6.2-sol"], 4.0)
        self.assertEqual(suggestions["claude-sonnet-5-5"], -4.0)
        self.assertNotIn("adjustments", out)

    def test_unmatched_fixture_and_surface_not_compared(self):
        data = synthetic_trials()
        for r in data["trials"]:
            if r["model_id"] == "gpt-6.2-sol":
                r["surface"] = "codex"
        out = compare.compare_trials(data)
        self.assertEqual(out["comparisons"], [])
        self.assertEqual(out["suggested_adjustments"], [])

    def test_below_sample_threshold_suppressed(self):
        out = compare.compare_trials(synthetic_trials(5))
        self.assertEqual(out["comparisons"][0]["status"], "insufficient")
        self.assertEqual(out["suggested_adjustments"], [])

    def test_missing_metadata_cannot_count_as_paired(self):
        data = synthetic_trials()
        for r in data["trials"]:
            r.pop("rubric_sha256")
        out = compare.compare_trials(data)
        self.assertEqual(out["incomplete_comparison_metadata"], 24)
        self.assertEqual(out["comparisons"], [])

    def test_no_fabricated_billing_or_runtime_on_missing_values(self):
        data = {"schema_version": 1, "trials": [
            {"run_id": "a", "task_id": "1", "task_type": "coding", "model_id": "m", "passed": True},
            {"run_id": "b", "task_id": "2", "task_type": "coding", "model_id": "m", "passed": False,
             "cost_usd": 1.2, "elapsed_seconds": 20.0}]}
        entry = score.compute_report(data)["groups"][0]
        self.assertEqual(entry["cost_samples"], 1)
        self.assertEqual(entry["time_samples"], 1)
        self.assertIsNone(entry["cost_per_accepted_usd"])
        self.assertEqual(entry["mean_cost_usd"], 1.2)
        entry2 = score.compute_report({"schema_version": 1, "trials": [data["trials"][0]]})["groups"][0]
        self.assertIsNone(entry2["mean_cost_usd"])

    def test_reject_duplicate_runs_or_invalid_minimum(self):
        data = synthetic_trials()
        data["trials"].append(data["trials"][0])
        with self.assertRaises(ValueError):
            compare.compare_trials(data)
        with self.assertRaises(ValueError):
            compare.compare_trials(synthetic_trials(), min_tasks=2)


class HandoffTests(unittest.TestCase):
    def test_templates_are_unfilled_and_correct_order(self):
        x = task()
        x["stages"].append({"name": "Review", "type": "review"})
        files = handoff.templates(x)
        self.assertEqual([name for name, _ in files], ["handoff-01.md", "handoff-02.md"])
        self.assertIn("UNFILLED TEMPLATE", files[0][1])
        self.assertIn("TODO — NOT RUN", files[0][1])
        self.assertIn("Downstream: Review", files[0][1])
        self.assertIn("Upstream: Build", files[1][1])

    def test_writes_requires_explicit_target_and_refuses_overwrite(self):
        files = handoff.templates(task())
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "handoffs"
            handoff.write_templates(target, files)
            self.assertTrue((target / "handoff-01.md").exists())
            with self.assertRaises(ValueError):
                handoff.write_templates(target, files)
            handoff.write_templates(target, files, force=True)

    def test_route_result_stage_order_guard(self):
        routed = router.route(task(), REGISTRY, now=NOW)
        handoff.templates(task(), routed)
        routed["stages"][0]["name"] = "changed"
        with self.assertRaises(ValueError):
            handoff.templates(task(), routed)

    def test_handoff_cli_stdout_does_not_write(self):
        result = subprocess.run([sys.executable, str(SKILL / "scripts/handoff.py"), "--task-file",
                                 str(SKILL / "examples/project-plan.json")], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("TODO — NOT VERIFIED", result.stdout)


if __name__ == "__main__":
    unittest.main()
