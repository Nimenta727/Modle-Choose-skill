import importlib.util
import json
from datetime import datetime, timedelta, timezone
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
NOW = datetime(2026, 11, 19, 14, 0, tzinfo=timezone.utc)


def plan(task_type="coding", complexity="medium", **kwargs):
    return {"priority": "balanced", "surface": "api", "stages": [dict(
        {"name": "Phase", "type": task_type, "complexity": complexity, "deliverable": "Working deliverable"}, **kwargs)]}


def inventory(provider="openai", models=None, status="listed", when=NOW, surface="api", method=None):
    r = {"provider": provider, "status": status, "surface": surface, "checked_at": when.isoformat(),
         "available_models": models or ["gpt-6.2-sol"]}
    if method:
        r["method"] = method
    return r


class RouterTests(unittest.TestCase):
    def test_registry_valid_ids_and_prices(self):
        router.validate_registry(REGISTRY)
        self.assertEqual(len(REGISTRY["models"]), 8)
        self.assertTrue(next(x for x in REGISTRY["models"] if x["id"] == "claude-haiku-5-5")["price_floor_only"])

    def test_default_plan_is_conditional_not_verified(self):
        result = router.route(plan(), REGISTRY, now=NOW)
        self.assertEqual(result["mode"], "recommendation-only")
        self.assertEqual(result["stages"][0]["primary"]["availability"], "conditional")
        self.assertIn("Model allocation", router.render_markdown(result))

    def test_user_report_does_not_equal_request_verification(self):
        result = router.route(plan(), REGISTRY, available={"gpt-6-luna", "claude-sonnet-5-5"}, now=NOW)
        self.assertEqual(result["stages"][0]["primary"]["id"], "claude-sonnet-5-5")
        self.assertEqual(result["stages"][0]["primary"]["availability"], "user-reported")

    def test_inventory_is_listed_not_call_verified(self):
        task = plan()
        access = inventory()
        rec = router.route(task, REGISTRY, access=access, now=NOW)
        self.assertEqual(rec["stages"][0]["primary"]["id"], "gpt-6.2-sol")
        self.assertEqual(rec["stages"][0]["primary"]["availability"], "listed")
        task["execution"] = True
        self.assertIsNone(router.route(task, REGISTRY, access=access, now=NOW)["stages"][0]["primary"])

    def test_legacy_verified_inventory_downgraded(self):
        task = plan()
        task["execution"] = True
        self.assertIsNone(router.route(task, REGISTRY, access=inventory(status="verified"), now=NOW)["stages"][0]["primary"])

    def test_call_verified_access_requires_proof_and_freshness(self):
        task = plan()
        task["execution"] = True
        proof = inventory(status="call_verified", method="successful_model_request")
        result = router.route(task, REGISTRY, access=proof, now=NOW)
        self.assertEqual(result["stages"][0]["primary"]["id"], "gpt-6.2-sol")
        self.assertEqual(result["stages"][0]["primary"]["availability"], "call-verified")
        proof["method"] = "account_model_inventory"
        self.assertIsNone(router.route(task, REGISTRY, access=proof, now=NOW)["stages"][0]["primary"])
        proof["method"] = "successful_model_request"
        self.assertIsNone(router.route(task, REGISTRY, access=proof, now=NOW + timedelta(hours=25))["stages"][0]["primary"])

    def test_provider_scoping_cannot_verify_other_provider(self):
        task = plan()
        task["execution"] = True
        bogus = inventory(models=["claude-opus-5-5"], status="call_verified", method="successful_model_request")
        result = router.route(task, REGISTRY, access=bogus, now=NOW)
        self.assertIsNone(result["stages"][0]["primary"])

    def test_multiple_inventory_files_supported(self):
        proof_openai = inventory(status="call_verified", method="successful_model_request")
        proof_claude = inventory(provider="anthropic", models=["claude-sonnet-5-5"], status="call_verified", method="successful_model_request")
        task = plan()
        task["execution"] = True
        result = router.route(task, REGISTRY, access=[proof_openai, proof_claude], now=NOW)
        self.assertIn(result["stages"][0]["primary"]["id"], {"gpt-6.2-sol", "claude-sonnet-5-5"})

    def test_non_api_surface_requires_explicit_native_access(self):
        task = plan()
        task["surface"] = "claude_code"
        result = router.route(task, REGISTRY, now=NOW)
        self.assertIsNone(result["stages"][0]["primary"])
        result = router.route(task, REGISTRY, available={"claude-sonnet-5-5"}, now=NOW)
        self.assertEqual(result["stages"][0]["primary"]["id"], "claude-sonnet-5-5")
        self.assertEqual(result["stages"][0]["primary"]["availability"], "user-reported")
        task["execution"] = True
        self.assertIsNone(router.route(task, REGISTRY, available={"claude-sonnet-5-5"}, now=NOW)["stages"][0]["primary"])

    def test_api_inventory_does_not_verify_claude_code(self):
        task = plan()
        task["surface"] = "claude_code"
        task["execution"] = True
        result = router.route(task, REGISTRY, access=inventory(status="call_verified", method="successful_model_request"), now=NOW)
        self.assertIsNone(result["stages"][0]["primary"])
        self.assertTrue(any("mismatched" in w for w in result["warnings"]))

    def test_critical_architecture_requires_heavy_models(self):
        result = router.route(plan("architecture", "high", risk="critical"), REGISTRY, now=NOW)
        self.assertIn(result["stages"][0]["primary"]["id"], {"gpt-6.2-astra", "claude-opus-5-5", "claude-fable-5-2"})
        self.assertEqual(result["stages"][0]["min_fitness"], 5)

    def test_medium_implicit_equals_explicit(self):
        t1 = plan("architecture")
        t2 = plan("architecture")
        del t1["stages"][0]["complexity"]
        r1, r2 = router.route(t1, REGISTRY, now=NOW), router.route(t2, REGISTRY, now=NOW)
        self.assertEqual(r1["stages"][0]["min_fitness"], r2["stages"][0]["min_fitness"])
        self.assertEqual(r1["stages"][0]["primary"]["id"], r2["stages"][0]["primary"]["id"])

    def test_cost_mode_favors_economy_for_extraction(self):
        task = plan("extraction", "low")
        task["priority"] = "cost"
        result = router.route(task, REGISTRY, now=NOW)
        self.assertIn(result["stages"][0]["primary"]["id"], {"gpt-6-luna", "claude-haiku-5-5"})

    def test_capability_budget_context_and_provider_hard_gates(self):
        task = plan("architecture", "high", required_capabilities=["web_search"], context_tokens=1000001)
        task["allowed_providers"] = ["anthropic"]
        self.assertIsNone(router.route(task, REGISTRY, now=NOW)["stages"][0]["primary"])
        task = plan("coding", "medium")
        task["max_blended_cost_usd_per_mtok"] = .01
        self.assertIsNone(router.route(task, REGISTRY, now=NOW)["stages"][0]["primary"])

    def test_lower_bound_price_cannot_meet_hard_budget(self):
        task = plan("extraction", "low")
        task["max_blended_cost_usd_per_mtok"] = 5
        result = router.route(task, REGISTRY, now=NOW)
        ids = [c["id"] for c in [result["stages"][0]["primary"], result["stages"][0]["backup"]] if c]
        self.assertNotIn("claude-haiku-5-5", ids)
        self.assertIn("price is only a lower bound; budget cannot be guaranteed", result["stages"][0]["excluded"])

    def test_invalid_types_and_unknown_surface(self):
        for broken in [plan("unsupported"), plan("coding", context_tokens=True), plan("coding", output_tokens=-1)]:
            with self.assertRaises(ValueError):
                router.route(broken, REGISTRY, now=NOW)
        task = plan()
        task["surface"] = "fake_surface"
        with self.assertRaises(ValueError):
            router.route(task, REGISTRY, now=NOW)
        task = plan()
        task["max_blended_cost_usd_per_mtok"] = float("nan")
        with self.assertRaises(ValueError):
            router.route(task, REGISTRY, now=NOW)

    def test_registry_duplicate_rejected(self):
        broken = json.loads(json.dumps(REGISTRY))
        broken["models"][1]["id"] = broken["models"][0]["id"]
        with self.assertRaises(ValueError):
            router.route(plan(), broken, now=NOW)

    def test_no_eligible_model_cli_nonzero(self):
        import tempfile
        task = plan()
        task["execution"] = True
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "task.json"
            path.write_text(json.dumps(task), encoding="utf-8")
            p = subprocess.run([sys.executable, str(SKILL / "scripts/route.py"), "--task-file", str(path)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 3)
            self.assertIn("无合格原生模型", p.stdout)


if __name__ == "__main__":
    unittest.main()
