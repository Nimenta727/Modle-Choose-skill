#!/usr/bin/env python3
"""Deterministic, explainable model recommendations. Never invokes a model."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import sys

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "references" / "model-registry.json"
TASK_TYPES = {"analysis", "architecture", "coding", "debugging", "testing", "review", "documentation", "extraction", "ui"}
SURFACES = {"api", "claude_code", "codex", "chatgpt", "claude_app", "other"}
PRIORITIES = {
    "quality": {"quality": 0.70, "cost": 0.10, "speed": 0.20},
    "balanced": {"quality": 0.55, "cost": 0.30, "speed": 0.15},
    "cost": {"quality": 0.35, "cost": 0.55, "speed": 0.10},
}
COMPLEXITY = {"low", "medium", "high"}
ACCESS_TTL_HOURS = 24
CALIBRATION_TTL_DAYS = 90
MAX_CALIBRATION_DELTA = 8.0


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def nonnegative_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def validate_registry(registry: dict) -> None:
    if registry.get("schema_version") != 1:
        raise ValueError("unsupported registry schema_version")
    datetime.fromisoformat(registry["verified_at"])
    ids = set()
    models = registry.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("empty model registry")
    for m in models:
        required = ["id", "provider", "lifecycle", "channels", "context_tokens", "max_output_tokens",
                    "capabilities", "task_fitness", "effort_levels", "latency_tier",
                    "input_usd_per_mtok", "output_usd_per_mtok"]
        missing = [field for field in required if field not in m]
        if missing:
            raise ValueError(f"missing model fields {missing}: {m.get('id')}")
        if not isinstance(m["id"], str) or not m["id"] or m["id"] in ids:
            raise ValueError(f"invalid or duplicate model ID: {m['id']}")
        ids.add(m["id"])
        if m["provider"] not in ("openai", "anthropic") or not isinstance(m["channels"], list) or not m["channels"]:
            raise ValueError(f"invalid provider/channels: {m['id']}")
        if any(channel not in SURFACES for channel in m["channels"]):
            raise ValueError(f"unknown surface in model registry: {m['id']}")
        if type(m["latency_tier"]) is not int or not 1 <= m["latency_tier"] <= 5 or any(
            type(m["task_fitness"].get(t)) is not int or not 1 <= m["task_fitness"][t] <= 5 for t in TASK_TYPES
        ):
            raise ValueError(f"invalid heuristic rating: {m['id']}")
        if any(not nonnegative_number(m[k]) for k in ("input_usd_per_mtok", "output_usd_per_mtok")):
            raise ValueError(f"invalid price: {m['id']}")
        if any(type(m[k]) is not int or m[k] <= 0 for k in ("context_tokens", "max_output_tokens")):
            raise ValueError(f"invalid token limit: {m['id']}")
        if not isinstance(m["capabilities"], list) or not isinstance(m["effort_levels"], list):
            raise ValueError(f"invalid capabilities/effort: {m['id']}")


def validate_task(task: dict) -> None:
    if task.get("priority", "balanced") not in PRIORITIES:
        raise ValueError("priority must be quality, balanced or cost")
    if task.get("surface", "api") not in SURFACES:
        raise ValueError(f"unsupported execution surface: {task.get('surface')}")
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
        for k in ("context_tokens", "output_tokens", "estimated_input_tokens", "estimated_output_tokens"):
            if type(s.get(k, 0)) is not int or s.get(k, 0) < 0:
                raise ValueError(f"invalid {k} for {s['name']}")
        if ("estimated_input_tokens" in s) != ("estimated_output_tokens" in s):
            raise ValueError("estimated_input_tokens and estimated_output_tokens must be supplied together")
        if "estimated_input_tokens" in s and s["estimated_input_tokens"] + s["estimated_output_tokens"] == 0:
            raise ValueError("estimated token volume must be positive; omit both fields when unknown")
        if "max_stage_api_reference_usd" in s and not nonnegative_number(s["max_stage_api_reference_usd"]):
            raise ValueError("max_stage_api_reference_usd must be finite and nonnegative")
        capabilities = s.get("required_capabilities", [])
        if not isinstance(capabilities, list) or any(not isinstance(c, str) or not c for c in capabilities):
            raise ValueError("required_capabilities must be an array of strings")
    if "allowed_providers" in task and (not isinstance(task["allowed_providers"], list) or any(
        p not in ("openai", "anthropic") for p in task["allowed_providers"]
    )):
        raise ValueError("allowed_providers must be an array of valid provider names")
    if "max_blended_cost_usd_per_mtok" in task and not nonnegative_number(task["max_blended_cost_usd_per_mtok"]):
        raise ValueError("max cost must be a finite nonnegative number")
    if "execution" in task and type(task["execution"]) is not bool:
        raise ValueError("execution must be boolean")


def blended_price(m: dict) -> float:
    return .8 * m["input_usd_per_mtok"] + .2 * m["output_usd_per_mtok"]


def api_cost_unrounded(model: dict, stage: dict) -> float:
    """The unrounded reference is used to enforce hard budget limits."""
    return (stage["estimated_input_tokens"] * model["input_usd_per_mtok"]
            + stage["estimated_output_tokens"] * model["output_usd_per_mtok"]) / 1_000_000


def api_cost_estimate(model: dict, stage: dict) -> dict:
    """Illustrative *uncached API list-price* estimate, NOT a bill or subscription price."""
    if "estimated_input_tokens" not in stage:
        return {"status": "unknown", "api_reference_usd": None}
    total = api_cost_unrounded(model, stage)
    return {"status": "lower-bound" if model.get("price_floor_only") else "api-list-reference",
            "api_reference_usd": round(total, 6),
            "estimated_input_tokens": stage["estimated_input_tokens"],
            "estimated_output_tokens": stage["estimated_output_tokens"]}


def calibration_offsets(calibration: dict | None, registry: dict, now: datetime) -> tuple[dict[tuple[str, str], float], list[str]]:
    """Accept only an explicitly reviewed, recent user-controlled adjustment file.

    This does NOT authenticate real trial measurements. A report/proposal never
    auto-applies as an adjustment, and baseline priors remain unchanged.
    """
    if calibration is None:
        return {}, []
    if not isinstance(calibration, dict) or calibration.get("schema_version") != 1 or calibration.get("status") != "user_reviewed":
        raise ValueError("calibration must be schema_version=1 and status=user_reviewed; proposals cannot be applied")
    date_checked = parsed_time(calibration.get("reviewed_at"))
    if date_checked is None or date_checked > now + timedelta(minutes=5):
        raise ValueError("calibration requires a valid non-future reviewed_at timestamp")
    rows = calibration.get("adjustments")
    if not isinstance(rows, list):
        raise ValueError("calibration adjustments must be a list")
    offsets: dict[tuple[str, str], float] = {}
    known = {m["id"] for m in registry["models"]}
    for row in rows:
        if not isinstance(row, dict) or row.get("model_id") not in known or row.get("task_type") not in TASK_TYPES:
            raise ValueError("calibration references unknown model ID or task type")
        value = row.get("score_delta")
        if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > MAX_CALIBRATION_DELTA:
            raise ValueError("calibration score_delta must be within [-8,8]")
        if not isinstance(row.get("evidence"), str) or len(row["evidence"].strip()) < 8:
            raise ValueError("calibration adjustment requires descriptive evidence reference")
        key = (row["model_id"], row["task_type"])
        if key in offsets:
            raise ValueError("duplicate calibration adjustment")
        offsets[key] = float(value)
    if now - date_checked > timedelta(days=CALIBRATION_TTL_DAYS):
        return {}, ["Reviewed calibration is older than 90 days: ignored; renew the review before applying"]
    return offsets, ["User-reviewed score offsets applied; underlying empirical evidence was NOT independently verified by the router"] if offsets else []


def min_fitness(stage: dict) -> int:
    complexity = stage.get("complexity", "medium")
    base = {"low": 2, "medium": 3, "high": 4}[complexity]
    if stage["type"] in {"architecture", "debugging", "review"} and complexity in {"medium", "high"}:
        base = min(base + 1, 5)
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
    requested = stage.get("complexity", "medium")
    if stage.get("risk") in {"high", "critical"}:
        requested = "high"
    return requested if requested in m["effort_levels"] else "default (consult provider)"


def parsed_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d.astimezone(timezone.utc) if d.tzinfo else None


def access_lookup(access: dict | list[dict] | None, surface: str, now: datetime) -> tuple[dict[str, str], list[str]]:
    """Model IDs on provider-scoped records are either 'listed' or 'call-verified'.

    A model inventory is NOT a successful request. A legacy 'verified' inventory is
    downgraded, not trusted as a proof of callability.
    """
    states: dict[str, str] = {}
    warnings = []
    documents = access if isinstance(access, list) else ([access] if isinstance(access, dict) else [])
    for record in documents:
        if not isinstance(record, dict) or record.get("surface") != surface:
            warnings.append("Ignored inventory with mismatched execution surface")
            continue
        provider = record.get("provider")
        if provider not in {"openai", "anthropic"}:
            warnings.append("Ignored inventory without valid provider scope")
            continue
        checked = parsed_time(record.get("checked_at"))
        if checked is None or checked > now + timedelta(minutes=5) or now - checked > timedelta(hours=ACCESS_TTL_HOURS):
            warnings.append(f"Ignored missing, stale or future-dated {provider} access evidence")
            continue
        status = record.get("status")
        level = None
        if status in {"listed", "verified"}:  # legacy V1 inventory used 'verified'
            level = "listed"
        elif status == "call_verified" and record.get("method") == "successful_model_request":
            level = "call-verified"
        if level is None:
            continue
        if not isinstance(record.get("available_models"), list):
            warnings.append(f"Ignored malformed {provider} inventory")
            continue
        for model_id in record["available_models"]:
            if not isinstance(model_id, str):
                continue
            # Provider-scoped model IDs are verified against registry in route().
            key = f"{provider}:{model_id}"
            if {"listed": 1, "call-verified": 2}[level] > {"listed": 1, "call-verified": 2}.get(states.get(key), 0):
                states[key] = level
    return states, warnings


def eligible(m: dict, s: dict, task: dict, access_level: str, user_reported: bool) -> tuple[bool, str]:
    if m["lifecycle"] != "active":
        return False, "inactive"
    if "allowed_providers" in task and m["provider"] not in task["allowed_providers"]:
        return False, "provider restricted"
    surface = task.get("surface", "api")
    # Documented API channels do NOT imply entitlement on Claude Code, Codex, or ChatGPT.
    if surface not in m["channels"] and not (user_reported or access_level == "call-verified"):
        return False, "unconfirmed surface compatibility"
    if task.get("execution") and access_level != "call-verified":
        return False, "successful model request not verified"
    if s.get("context_tokens", 0) > m["context_tokens"] or s.get("output_tokens", 0) > m["max_output_tokens"]:
        return False, "context/output limit"
    if not set(s.get("required_capabilities", [])).issubset(m["capabilities"]):
        return False, "required capability missing"
    if m["task_fitness"][s["type"]] < min_fitness(s):
        return False, "below minimum task fit"
    if "max_stage_api_reference_usd" in s:
        if task.get("surface", "api") != "api":
            return False, "API price cap cannot gate non-API billing"
        estimate = api_cost_estimate(m, s)
        if estimate["api_reference_usd"] is None:
            return False, "stage budget requires explicit token estimates"
        if m.get("price_floor_only"):
            return False, "lower-bound API price cannot satisfy hard stage budget"
        if api_cost_unrounded(m, s) > s["max_stage_api_reference_usd"]:
            return False, "stage API budget cap exceeded"
    if "max_blended_cost_usd_per_mtok" in task:
        if m.get("price_floor_only"):
            return False, "price is only a lower bound; budget cannot be guaranteed"
        if blended_price(m) > task["max_blended_cost_usd_per_mtok"]:
            return False, "budget cap exceeded"
    return True, "eligible"


def rate(m: dict, s: dict, priority: str, max_price: float) -> float:
    fit = m["task_fitness"][s["type"]] / 5 * 100
    price = blended_price(m)
    cost = (1 - math.log1p(price) / math.log1p(max_price)) * 100 if max_price else 100
    speed = m["latency_tier"] / 5 * 100
    weights = PRIORITIES[priority]
    return round(weights["quality"] * fit + weights["cost"] * cost + weights["speed"] * speed, 2)


def route(task: dict, registry: dict, access: dict | list[dict] | None = None,
          available: set[str] | None = None, now: datetime | None = None,
          calibration: dict | None = None) -> dict:
    validate_task(task)
    validate_registry(registry)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    surface = task.get("surface", "api")
    available = available or set()
    states, warnings = access_lookup(access, surface, now)
    offsets, calibration_warnings = calibration_offsets(calibration, registry, now)
    warnings.extend(calibration_warnings)
    models = registry["models"]
    known = {m["id"] for m in models}
    unknown = (set(available) | {key.split(":", 1)[1] for key in states}) - known
    if unknown:
        warnings.append(f"Unknown IDs excluded pending registry review: {', '.join(sorted(unknown))}")
    if surface != "api":
        warnings.append(f"Surface '{surface}' has no implicit API model access; only explicitly reported/probed native models are eligible")
    price_max = max(blended_price(m) for m in models)
    priority = task.get("priority", "balanced")
    output = []
    for s in task["stages"]:
        candidates, excluded = [], {}
        for m in models:
            evidence = states.get(f"{m['provider']}:{m['id']}", "conditional")
            reported = m["id"] in available
            ok, why = eligible(m, s, task, evidence, reported)
            if not ok:
                excluded[why] = excluded.get(why, 0) + 1
                continue
            status = evidence if evidence != "conditional" else ("user-reported" if reported else "conditional")
            offset = offsets.get((m["id"], s["type"]), 0.0)
            candidates.append({"id": m["id"], "name": m["name"], "provider": m["provider"],
                "score": round(max(0, min(100, rate(m, s, priority, price_max) + offset)), 2),
                "score_adjustment": offset, "availability": status,
                "effort": effective_effort(m, s),
                "reason": reason_for(m, s, priority) + (f"；人工审核校准 {offset:+.1f} 分（未由路由器独立复核）" if offset else ""),
                "blended_price_usd_per_mtok": round(blended_price(m), 3),
                "price_floor_only": m.get("price_floor_only", False),
                "api_cost_estimate": api_cost_estimate(m, s)})
        # A surface-specific recommendation must never silently assign a foreign API model.
        ranks = {"call-verified": 3, "listed": 2, "user-reported": 1, "conditional": 0}
        candidates.sort(key=lambda c: (-ranks[c["availability"]], -c["score"], c["id"]))
        primary = candidates[0] if candidates else None
        backup = next((c for c in candidates[1:] if c["id"] != primary["id"]), None) if primary else None
        # Keep useful planning advice even if current product has no demonstrated native
        # model. This is informational only, NEVER an executable assignment.
        advisory = None
        if not primary and surface != "api":
            advisory_pool = []
            recommendation_task = {**task, "surface": "api", "execution": False}
            for m in models:
                ok, _ = eligible(m, s, recommendation_task, "conditional", False)
                if ok:
                    advisory_pool.append((round(rate(m, s, priority, price_max) + offsets.get((m["id"], s["type"]), 0), 2), m["id"], m["name"]))
            advisory_pool.sort(key=lambda item: (-item[0], item[1]))
            if advisory_pool:
                _, model_id, name = advisory_pool[0]
                advisory = {"id": model_id, "name": name, "status": "external-conditional",
                            "reason": "API candidate only; requires explicit local verification or authorized orchestrator"}
        output.append({"name": s["name"], "type": s["type"], "complexity": s.get("complexity", "medium"),
                       "deliverable": s.get("deliverable", "见实施计划"), "min_fitness": min_fitness(s),
                       "primary": primary, "backup": backup, "external_advisory": advisory, "excluded": excluded,
                       "cost_estimate": primary["api_cost_estimate"] if primary else {"status": "unknown", "api_reference_usd": None}})
    covered = [x["cost_estimate"] for x in output if x["cost_estimate"]["api_reference_usd"] is not None]
    lower_bound = any(e["status"] == "lower-bound" for e in covered)
    full_coverage = len(covered) == len(output)
    project_cost = {"status": "unestimated" if not covered else (
        "partial" if not full_coverage else "lower-bound" if lower_bound else "api-list-reference"),
        "api_reference_total_usd": round(sum(e["api_reference_usd"] for e in covered), 6) if covered else None,
        "stages_estimated": len(covered), "stages_total": len(output),
        "billing_surface": surface,
        "disclaimer": "Uncached vendor API list-price illustration only; excludes cache discounts, tools, taxes, regional/tier charges and subscription allocation."}
    if surface != "api" and covered:
        warnings.append("API list-price estimates are NOT the actual cost of subscriptions or this execution surface")
    if covered and not full_coverage:
        warnings.append("Only some stages have token estimates; reported API reference subtotal excludes unestimated stages")
    if lower_bound:
        warnings.append("Some cost estimates are price floors, so totals are lower bounds, not budget guarantees")
    verified_date = datetime.fromisoformat(registry["verified_at"]).date()
    if (now.date() - verified_date).days > 1:
        warnings.append(f"Registry last verified {registry['verified_at']}; recheck official sources for models, prices and lifecycle")
    if any(row["primary"] is None for row in output):
        warnings.append("Some stages have no eligible native model; external advisory candidates are NOT executable without authorization")
    if any(row["primary"] and row["primary"].get("price_floor_only") for row in output):
        warnings.append("At least one chosen model has price-floor-only metadata; projected token cost is NOT a quote")
    if not any(status == "call-verified" for status in states.values()):
        warnings.append("No recently successful per-model API request proven; inventory/listing is not execution verification")
    return {"mode": "execution-gated" if task.get("execution") else "recommendation-only", "surface": surface,
            "priority": priority, "registry_verified_at": registry["verified_at"],
            "registry_freshness": "stale" if (now.date() - verified_date).days > 1 else "cached (not live-checked)",
            "scoring": "policy heuristic with optional user-reviewed offsets, not benchmark", "stages": output,
            "project_cost": project_cost, "calibration_applied": bool(offsets), "warnings": list(dict.fromkeys(warnings))}


def render_markdown(result: dict) -> str:
    esc = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["## Model allocation / 模型分配", "",
             f"- **Mode**: {result['mode']} | **Surface**: {result['surface']} | **Policy**: {result['priority']}",
             f"- **Registry verified**: {result['registry_verified_at']} ({result['registry_freshness']}); scoring = heuristic, not a benchmark", "",
             "| 阶段 | 交付物 | 当前平台主选（ID） | 推理等级 | 原因 | 备用模型（ID） | 访问状态 | 仅供参考的外部候选 |",
             "|---|---|---|---|---|---|---|---|"]
    for s in result["stages"]:
        p, b = s["primary"], s["backup"]
        if p:
            fields = [s["name"], s["deliverable"], f"{p['name']} (`{p['id']}`)", p["effort"], p["reason"],
                      f"{b['name']} (`{b['id']}`; {b['availability']})" if b else "无合格备用模型", p["availability"], "—"]
        else:
            external = s.get("external_advisory")
            advisory = f"{external['name']} (`{external['id']}`; external-conditional)" if external else "—"
            fields = [s["name"], s["deliverable"], "无合格原生模型", "—", "未满足平台/权限或其他硬性约束", "—", "unavailable", advisory]
        lines.append("| " + " | ".join(map(esc, fields)) + " |")
    project_cost = result.get("project_cost", {})
    total = project_cost.get("api_reference_total_usd")
    lines += ["", "### Project API list-price illustration / 项目 API 参考成本",
              f"- **Known-stage subtotal:** ${total:.6f} USD" if total is not None else "- **Cost:** unestimated (token estimates not supplied)",
              f"- **Coverage:** {project_cost.get('stages_estimated', 0)}/{project_cost.get('stages_total', 0)} stages; status: {project_cost.get('status', 'unknown')}",
              "- **Important:** uncached API reference pricing only, not an actual bill; other surfaces/subscriptions differ.", "",
              "| 阶段 | API 参考成本 (USD) | 状态 |",
              "|---|---:|---|"]
    for stage in result["stages"]:
        e = stage.get("cost_estimate", {})
        usd = e.get("api_reference_usd")
        lines.append(f"| {esc(stage['name'])} | {f'${usd:.6f}' if usd is not None else '—'} | {esc(e.get('status', 'unknown'))} |")
    lines += ["", "**Switch / escalation:** Reroute if tests fail twice without progress, constraints change, or model access changes. A model recommendation never performs a provider switch.",
              "", "**Warnings / 注意事项:**"]
    lines += [f"- {w}" for w in result["warnings"]] or ["- None reported (verify account access before execution)."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-file", required=True, type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--available", help="Comma-separated USER-REPORTED models on the task's native surface")
    parser.add_argument("--availability-file", action="append", type=Path,
                        help="Repeatable API inventory or external successful-request evidence JSON")
    parser.add_argument("--calibration-file", type=Path, help="Explicitly user-reviewed bounded score offsets; never auto-applies trial proposals")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()
    try:
        task, registry = load_json(args.task_file), load_json(args.registry)
        access = [load_json(p) for p in args.availability_file] if args.availability_file else None
        available = set(filter(None, (x.strip() for x in args.available.split(",")))) if args.available else None
        calibration = load_json(args.calibration_file) if args.calibration_file else None
        result = route(task, registry, access, available, calibration=calibration)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(result))
    return 0 if all(s["primary"] for s in result["stages"]) else 3


if __name__ == "__main__":
    sys.exit(main())
