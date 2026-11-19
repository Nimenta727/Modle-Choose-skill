#!/usr/bin/env python3
"""Explainable deterministic *recommendation* router. No remote calls or model switching."""
from __future__ import annotations

import argparse
from datetime import date
import json
import math
from pathlib import Path
import sys

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "references" / "model-registry.json"
TASK_TYPES = {"analysis", "architecture", "coding", "debugging", "testing", "review", "documentation", "extraction", "ui"}
PRIORITIES = {
    "quality": {"quality": 0.70, "cost": 0.10, "speed": 0.20},
    "balanced": {"quality": 0.55, "cost": 0.30, "speed": 0.15},
    "cost": {"quality": 0.35, "cost": 0.55, "speed": 0.10},
}
COMPLEXITY = {"low", "medium", "high"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate_registry(registry: dict) -> None:
    if registry.get("schema_version") != 1:
        raise ValueError("unsupported registry schema_version")
    date.fromisoformat(registry["verified_at"])
    ids = set()
    if not registry.get("models"):
        raise ValueError("empty model registry")
    for m in registry["models"]:
        required = ["id", "provider", "lifecycle", "channels", "context_tokens", "max_output_tokens",
                    "capabilities", "task_fitness", "effort_levels", "latency_tier",
                    "input_usd_per_mtok", "output_usd_per_mtok"]
        missing = [field for field in required if field not in m]
        if missing:
            raise ValueError(f"missing model fields {missing}: {m.get('id')}")
        if m["id"] in ids:
            raise ValueError(f"duplicate model ID: {m['id']}")
        ids.add(m["id"])
        if not 1 <= m["latency_tier"] <= 5 or any(
            not 1 <= m["task_fitness"].get(t, 0) <= 5 for t in TASK_TYPES
        ):
            raise ValueError(f"invalid heuristic rating: {m['id']}")
        if any(m[k] < 0 for k in ("input_usd_per_mtok", "output_usd_per_mtok")):
            raise ValueError(f"negative price: {m['id']}")
        if m["context_tokens"] <= 0 or m["max_output_tokens"] <= 0:
            raise ValueError(f"invalid token limit: {m['id']}")


def validate_task(task: dict) -> None:
    if task.get("priority", "balanced") not in PRIORITIES:
        raise ValueError("priority must be quality, balanced or cost")
    if not isinstance(task.get("stages"), list) or not task["stages"]:
        raise ValueError("task requires a nonempty stages array")
    for s in task["stages"]:
        if not isinstance(s, dict) or not isinstance(s.get("name"), str) or not s["name"].strip():
            raise ValueError("each stage needs a nonempty name")
        if s.get("type") not in TASK_TYPES:
            raise ValueError(f"invalid task type for {s['name']}")
        if s.get("complexity", "medium") not in COMPLEXITY:
            raise ValueError(f"invalid complexity for {s['name']}")
        if s.get("risk", "normal") not in {"normal", "high", "critical"}:
            raise ValueError(f"invalid risk for {s['name']}")
        for k in ("context_tokens", "output_tokens"):
            if not isinstance(s.get(k, 0), int) or s.get(k, 0) < 0:
                raise ValueError(f"invalid {k} for {s['name']}")
        if not isinstance(s.get("required_capabilities", []), list):
            raise ValueError("required_capabilities must be an array")
    if "allowed_providers" in task and not isinstance(task["allowed_providers"], list):
        raise ValueError("allowed_providers must be an array")
    if "max_blended_cost_usd_per_mtok" in task and task["max_blended_cost_usd_per_mtok"] < 0:
        raise ValueError("max cost cannot be negative")


def blended_price(m: dict) -> float:
    return 0.8 * m["input_usd_per_mtok"] + 0.2 * m["output_usd_per_mtok"]


def min_fitness(stage: dict) -> int:
    base = {"low": 2, "medium": 3, "high": 4}[stage.get("complexity", "medium")]
    if stage["type"] in {"architecture", "debugging", "review"} and stage.get("complexity") in {"medium", "high"}:
        base += 1 if base < 5 else 0
    if stage.get("risk") == "high":
        base = max(base, 4)
    if stage.get("risk") == "critical":
        base = 5
    return base


def reason_for(m: dict, stage: dict, priority: str) -> str:
    fit = m["task_fitness"][stage["type"]]
    label = {"quality": "质量优先", "balanced": "质量/成本均衡", "cost": "成本优先"}[priority]
    return f"{label}；{stage['type']} 适配等级 {fit}/5（策略估计，非基准测试）"


def effective_effort(m: dict, stage: dict) -> str:
    requested = {"low": "low", "medium": "medium", "high": "high"}[stage.get("complexity", "medium")]
    if stage.get("risk") in {"high", "critical"}:
        requested = "high"
    if requested in m["effort_levels"]:
        return requested
    return "default (consult provider)"


def eligible(m: dict, s: dict, task: dict, verified_access: bool) -> tuple[bool, str]:
    if m["lifecycle"] != "active":
        return False, "inactive"
    if task.get("allowed_providers") and m["provider"] not in task["allowed_providers"]:
        return False, "provider restricted"
    if task.get("execution") and not verified_access:
        return False, "access unverified for execution"
    if s.get("context_tokens", 0) > m["context_tokens"] or s.get("output_tokens", 0) > m["max_output_tokens"]:
        return False, "context/output limit"
    if not set(s.get("required_capabilities", [])).issubset(set(m["capabilities"])):
        return False, "required capability missing"
    if m["task_fitness"][s["type"]] < min_fitness(s):
        return False, "below minimum task fit"
    if blended_price(m) > task.get("max_blended_cost_usd_per_mtok", float("inf")):
        return False, "budget cap exceeded"
    return True, "eligible"


def rate(m: dict, s: dict, priority: str, max_price: float) -> float:
    fit = m["task_fitness"][s["type"]] / 5 * 100
    price = blended_price(m)
    cost = (1 - math.log1p(price) / math.log1p(max_price)) * 100 if max_price else 100
    speed = m["latency_tier"] / 5 * 100
    weights = PRIORITIES[priority]
    return round(weights["quality"] * fit + weights["cost"] * cost + weights["speed"] * speed, 2)


def route(task: dict, registry: dict, access: dict | None = None, available: set[str] | None = None) -> dict:
    validate_task(task)
    validate_registry(registry)
    available = available or set()
    access = access or {}
    verified = set(access.get("available_models", [])) if access.get("status") == "verified" and access.get("surface") == task.get("surface", "api") else set()
    known = {m["id"] for m in registry["models"]}
    if unknown := (verified | available) - known:
        # Unknown models are never silently invented, even when an account lists them.
        unknown_warning = f"Unknown IDs excluded pending registry review: {', '.join(sorted(unknown))}"
    else:
        unknown_warning = None
    price_max = max(blended_price(m) for m in registry["models"])
    output = []
    priority = task.get("priority", "balanced")
    for s in task["stages"]:
        candidates = []
        excluded = {}
        for m in registry["models"]:
            ok, why = eligible(m, s, task, m["id"] in verified)
            if not ok:
                excluded[why] = excluded.get(why, 0) + 1
                continue
            status = "verified" if m["id"] in verified else ("user-reported" if m["id"] in available else "conditional")
            score = rate(m, s, priority, price_max)
            candidates.append({"id": m["id"], "name": m["name"], "provider": m["provider"], "score": score,
                               "availability": status, "effort": effective_effort(m, s),
                               "reason": reason_for(m, s, priority),
                               "blended_price_usd_per_mtok": round(blended_price(m), 3),
                               "price_floor_only": m.get("price_floor_only", False)})
        # Prefer confirmed / user-reported access for planning, even if a conditional model has a better score.
        candidates.sort(key=lambda c: (-{"verified": 2, "user-reported": 1, "conditional": 0}[c["availability"]], -c["score"], c["id"]))
        primary = candidates[0] if candidates else None
        backup = next((c for c in candidates[1:] if c["id"] != primary["id"]), None) if primary else None
        output.append({"name": s["name"], "type": s["type"], "complexity": s.get("complexity", "medium"),
                       "deliverable": s.get("deliverable", "见实施计划"), "min_fitness": min_fitness(s),
                       "primary": primary, "backup": backup, "excluded": excluded})
    try:
        age = (date.today() - date.fromisoformat(registry["verified_at"])).days
    except ValueError:
        age = None
    warnings = []
    if unknown_warning:
        warnings.append(unknown_warning)
    if age is not None and age > 1:
        warnings.append(f"Registry last verified {registry['verified_at']} ({age} days ago); check official sources before relying on prices/IDs.")
    if task.get("surface", "api") != "api":
        warnings.append("API model IDs are not guaranteed to be selectable in this product surface; confirm locally.")
    if any(row["primary"] is None for row in output):
        warnings.append("At least one stage has no eligible model; investigate constraints and access.")
    if not verified:
        warnings.append("No account-specific API availability verified; recommendations are not confirmed executable.")
    return {"mode": "execution-gated" if task.get("execution") else "recommendation-only",
            "surface": task.get("surface", "api"), "priority": priority, "registry_verified_at": registry["verified_at"],
            "registry_freshness": "stale" if age is None or age > 1 else "cached <= 24-48h (not live-checked)",
            "scoring": "policy heuristic, not benchmark", "stages": output, "warnings": warnings}


def render_markdown(result: dict) -> str:
    esc = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["## Model allocation / 模型分配", "",
             f"- **Mode**: {result['mode']} | **Surface**: {result['surface']} | **Policy**: {result['priority']}",
             f"- **Registry verified**: {result['registry_verified_at']} ({result['registry_freshness']}); scoring = heuristic, not a benchmark", "",
             "| 阶段 | 交付物 | 主选模型（ID） | 推理等级 | 原因 | 备用模型（ID） | 访问状态 |",
             "|---|---|---|---|---|---|---|"]
    for s in result["stages"]:
        p, b = s["primary"], s["backup"]
        if p:
            fields = [s["name"], s["deliverable"], f"{p['name']} (`{p['id']}`)", p["effort"], p["reason"],
                      f"{b['name']} (`{b['id']}`; {b['availability']})" if b else "无合格备用模型", p["availability"]]
        else:
            fields = [s["name"], s["deliverable"], "无合格模型", "—", "未满足硬性约束", "—", "unavailable"]
        lines.append("| " + " | ".join(map(esc, fields)) + " |")
    lines += ["", "**Switch / escalation:** If validation fails twice without progress, constraints change, or model access expires, rerun routing. Do not switch vendors without authorized tooling.",
              "", "**Warnings / 注意事项:**"]
    lines += [f"- {w}" for w in result["warnings"]] or ["- None reported (still verify access before execution)."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-file", required=True, type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--available", help="Comma-separated user-reported available IDs (NOT access verification)")
    parser.add_argument("--availability-file", type=Path, help="JSON from check_availability.py (API-only)")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()
    try:
        task, registry = load_json(args.task_file), load_json(args.registry)
        access = load_json(args.availability_file) if args.availability_file else None
        available = set(filter(None, (x.strip() for x in args.available.split(",")))) if args.available else None
        result = route(task, registry, access, available)
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(result))
    return 0 if all(s["primary"] for s in result["stages"]) else 3


if __name__ == "__main__":
    sys.exit(main())
