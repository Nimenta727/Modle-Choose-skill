#!/usr/bin/env python3
"""Deterministic policy-contract evals. NOT a comparison of real model quality."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/model-router/scripts"))
import route as router  # noqa: E402

DEFAULT_SUITE = Path(__file__).with_name("routing_cases.json")
DEFAULT_REGISTRY = ROOT / "skills/model-router/references/model-registry.json"
DEFAULT_TIME = "2026-11-19T14:00:00+00:00"


def check_scenario(scenario: dict, registry: dict, now: datetime) -> dict:
    """Return per-check evidence so a failure isn't hidden behind one scalar score."""
    case_id = scenario["id"]
    task = scenario["task"]
    result = router.route(task, registry, scenario.get("access"), set(scenario.get("available", [])), now=now)
    requirements = scenario["expect"]
    checks: list[dict] = []

    def verify(name: str, actual: object, expected: object) -> None:
        checks.append({"name": name, "passed": actual == expected,
                       "actual": actual, "expected": expected})

    verify("stage_count", len(result["stages"]), len(requirements["stages"]))
    verify("execution_mode", result["mode"], "execution-gated" if task.get("execution") else "recommendation-only")
    for i, (stage, expectation) in enumerate(zip(result["stages"], requirements["stages"])):
        prefix = f"stage{i + 1}"
        primary = stage["primary"]
        verify(prefix + ".primary_exists", primary is not None, expectation["primary"])
        if primary:
            model = next(m for m in registry["models"] if m["id"] == primary["id"])
            verify(prefix + ".minimum_fit", model["task_fitness"][stage["type"]] >= stage["min_fitness"], True)
            verify(prefix + ".permitted_provider", "allowed_providers" not in task or model["provider"] in task["allowed_providers"], True)
            verify(prefix + ".surface_gate", task.get("surface", "api") in model["channels"] or
                   primary["availability"] in {"user-reported", "call-verified"}, True)
            if task.get("execution"):
                verify(prefix + ".execution_access", primary["availability"], "call-verified")
            if "availability" in expectation:
                verify(prefix + ".availability", primary["availability"], expectation["availability"])
            if "provider" in expectation:
                verify(prefix + ".provider", primary["provider"], expectation["provider"])
            if "primary_id" in expectation:
                verify(prefix + ".primary_id", primary["id"], expectation["primary_id"])
            if "effort" in expectation:
                verify(prefix + ".effort", primary["effort"], expectation["effort"])
        if "external_advisory" in expectation:
            verify(prefix + ".external_advisory", stage["external_advisory"] is not None, expectation["external_advisory"])
        if "backup" in expectation:
            verify(prefix + ".backup", stage["backup"] is not None, expectation["backup"])
        if "excluded_reason" in expectation:
            verify(prefix + ".excluded_reason", expectation["excluded_reason"] in stage["excluded"], True)
    markdown = router.render_markdown(result)
    verify("plan_allocation_heading", "Model allocation / 模型分配" in markdown, True)
    verify("plan_timestamp", result["registry_verified_at"] in markdown, True)
    if "warning_contains" in requirements:
        verify("warning_contains", any(requirements["warning_contains"] in w for w in result["warnings"]), True)
    return {"id": case_id, "category": scenario["category"], "passed": all(c["passed"] for c in checks),
            "checks": checks, "selected": [s["primary"]["id"] if s["primary"] else None for s in result["stages"]]}


def evaluate(suite: dict, registry: dict) -> dict:
    if suite.get("schema_version") != 1 or not isinstance(suite.get("cases"), list) or not suite["cases"]:
        raise ValueError("suite must declare schema_version=1 with nonempty cases")
    ids = [c["id"] for c in suite["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("suite contains duplicate case IDs")
    now = datetime.fromisoformat(suite.get("fixed_time", DEFAULT_TIME).replace("Z", "+00:00"))
    if now.tzinfo is None:
        raise ValueError("fixed_time must include timezone")
    cases = [check_scenario(c, registry, now) for c in suite["cases"]]
    total_checks = sum(len(c["checks"]) for c in cases)
    successful_checks = sum(sum(bool(x["passed"]) for x in c["checks"]) for c in cases)
    categories = {}
    for c in cases:
        bucket = categories.setdefault(c["category"], {"passed": 0, "total": 0})
        bucket["total"] += 1
        bucket["passed"] += int(c["passed"])
    return {"evaluation_kind": "offline-policy-contract-not-model-quality", "fixed_time": now.isoformat(),
            "registry_verified_at": registry["verified_at"], "case_total": len(cases),
            "case_passed": sum(c["passed"] for c in cases), "checks_passed": successful_checks,
            "checks_total": total_checks, "categories": categories, "cases": cases}


def as_markdown(report: dict) -> str:
    lines = ["# Model Router — Offline policy evaluation", "",
             "> Measures deterministic routing/plan invariants only. Does NOT measure model intelligence or real Agent Skill activation.", "",
             f"- Cases passed: **{report['case_passed']}/{report['case_total']}**",
             f"- Assertions passed: **{report['checks_passed']}/{report['checks_total']}**",
             f"- Frozen evaluation clock: `{report['fixed_time']}`", "",
             "| Category | Passed | Total |", "|---|---:|---:|"]
    for name, value in sorted(report["categories"].items()):
        lines.append(f"| {name} | {value['passed']} | {value['total']} |")
    failures = [(case["id"], c) for case in report["cases"] for c in case["checks"] if not c["passed"]]
    if failures:
        lines.extend(["", "## Failed assertions", ""])
        for case_id, check in failures:
            lines.append(f"- `{case_id}` / `{check['name']}`: expected `{check['expected']}`, received `{check['actual']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    p.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    p.add_argument("--json-out", type=Path)
    p.add_argument("--md-out", type=Path)
    args = p.parse_args()
    try:
        source = args.suite.read_bytes()
        report = evaluate(json.loads(source), router.load_json(args.registry))
        report["suite_sha256"] = hashlib.sha256(source).hexdigest()
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.md_out:
            args.md_out.parent.mkdir(parents=True, exist_ok=True)
            args.md_out.write_text(as_markdown(report), encoding="utf-8")
        print(as_markdown(report), end="")
        return 0 if report["case_passed"] == report["case_total"] else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        print(f"eval error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
