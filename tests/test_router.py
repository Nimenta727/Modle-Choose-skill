import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/model-router"
spec = importlib.util.spec_from_file_location("model_route", SKILL / "scripts/route.py")
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)
REGISTRY = router.load_json(SKILL / "references/model-registry.json")


def plan(task_type="coding", complexity="medium", **kwargs):
    return {"priority": "balanced", "surface": "api", "stages": [dict(
        {"name": "Phase", "type": task_type, "complexity": complexity, "deliverable": "Working deliverable"}, **kwargs)]}


class RouterTests(unittest.TestCase):
    def test_registry_valid_ids_and_prices(self):
        router.validate_registry(REGISTRY)
        self.assertEqual(len(REGISTRY["models"]), 8)
        self.assertEqual(len({x["id"] for x in REGISTRY["models"]}), 8)
        self.assertTrue(next(x for x in REGISTRY["models"] if x["id"] == "claude-haiku-5-5")["price_floor_only"])

    def test_default_plan_is_conditional_not_verified(self):
        result = router.route(plan(), REGISTRY)
        self.assertEqual(result["mode"], "recommendation-only")
        self.assertEqual(result["stages"][0]["primary"]["availability"], "conditional")
        self.assertIn("No account-specific", " ".join(result["warnings"]))
        self.assertIn("Model allocation", router.render_markdown(result))

    def test_user_report_does_not_equal_verification(self):
        result = router.route(plan(), REGISTRY, available={"gpt-6-luna", "claude-sonnet-5-5"})
        self.assertEqual(result["stages"][0]["primary"]["id"], "claude-sonnet-5-5")
        self.assertEqual(result["stages"][0]["primary"]["availability"], "user-reported")

    def test_execution_gates_unverified(self):
        task = plan()
        task["execution"] = True
        no_access = router.route(task, REGISTRY, available={"gpt-6.2-sol"})
        self.assertIsNone(no_access["stages"][0]["primary"])
        verified_access = {"status": "verified", "surface": "api", "available_models": ["gpt-6.2-sol"]}
        with_access = router.route(task, REGISTRY, access=verified_access)
        self.assertEqual(with_access["stages"][0]["primary"]["id"], "gpt-6.2-sol")
        self.assertEqual(with_access["stages"][0]["primary"]["availability"], "verified")

    def test_wrong_surface_cannot_verify(self):
        task = plan()
        task["surface"] = "claude_code"
        task["execution"] = True
        result = router.route(task, REGISTRY, access={"status": "verified", "surface": "api", "available_models": ["claude-opus-5-5"]})
        self.assertIsNone(result["stages"][0]["primary"])
        self.assertTrue(any("product surface" in warning for warning in result["warnings"]))

    def test_critical_architecture_has_no_lightweight_candidates(self):
        result = router.route(plan("architecture", "high", risk="critical"), REGISTRY)
        primary = result["stages"][0]["primary"]
        self.assertIn(primary["id"], {"gpt-6.2-astra", "claude-opus-5-5", "claude-fable-5-2"})
        self.assertEqual(result["stages"][0]["min_fitness"], 5)

    def test_cost_mode_favors_economy_for_extraction(self):
        task = plan("extraction", "low")
        task["priority"] = "cost"
        result = router.route(task, REGISTRY)
        self.assertIn(result["stages"][0]["primary"]["id"], {"gpt-6-luna", "claude-haiku-5-5"})

    def test_capability_budget_context_and_provider_hard_gates(self):
        task = plan("architecture", "high", required_capabilities=["web_search"], context_tokens=1000001)
        task["allowed_providers"] = ["anthropic"]
        self.assertIsNone(router.route(task, REGISTRY)["stages"][0]["primary"])
        task = plan("coding", "medium")
        task["max_blended_cost_usd_per_mtok"] = 0.01
        self.assertIsNone(router.route(task, REGISTRY)["stages"][0]["primary"])

    def test_invalid_types_are_errors_not_hallucinated_plans(self):
        with self.assertRaises(ValueError):
            router.route(plan("unsupported"), REGISTRY)
        broken = json.loads(json.dumps(REGISTRY))
        broken["models"][1]["id"] = broken["models"][0]["id"]
        with self.assertRaises(ValueError):
            router.route(plan(), broken)

    def test_no_eligible_model_cli_nonzero(self):
        import tempfile
        task = plan()
        task["execution"] = True
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "task.json"
            path.write_text(json.dumps(task), encoding="utf-8")
            p = subprocess.run([sys.executable, str(SKILL / "scripts/route.py"), "--task-file", str(path)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 3)
            self.assertIn("无合格模型", p.stdout)


if __name__ == "__main__":
    unittest.main()
