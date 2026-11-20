#!/usr/bin/env python3
"""Summarize numeric CLI results without reading prompts or response.md."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

FIELDS = ("input_tokens", "output_tokens", "cached_input_tokens",
          "cache_read_input_tokens", "cache_creation_input_tokens", "reasoning_output_tokens")


def aggregate(records: list[dict]) -> dict:
    groups = {}
    for item in records:
        if not isinstance(item, dict) or item.get("agent") not in ("claude", "codex"):
            raise ValueError("invalid run record")
        group = groups.setdefault(item["agent"], {
            "runs": 0, "usage_reported_runs": 0, "cost_reported_runs": 0,
            "client_estimated_cost_usd": 0.0, "tokens": {}})
        group["runs"] += 1
        record = item.get("reported_usage")
        if not isinstance(record, dict) or not isinstance(record.get("fields"), dict):
            continue
        group["usage_reported_runs"] += 1
        for name in FIELDS:
            value = record["fields"].get(name)
            if type(value) is int and 0 <= value <= 10**15:
                group["tokens"][name] = group["tokens"].get(name, 0) + value
        dollars = record["fields"].get("claude_cli_estimated_cost_usd")
        if type(dollars) in (int, float) and 0 <= dollars <= 1_000_000:
            group["cost_reported_runs"] += 1
            group["client_estimated_cost_usd"] += dollars
    for group in groups.values():
        group["runs_without_usage"] = group["runs"] - group["usage_reported_runs"]
        group["cost_coverage_complete"] = group["cost_reported_runs"] == group["runs"]
        group["client_estimated_cost_usd"] = (round(group["client_estimated_cost_usd"], 8)
                                               if group["cost_reported_runs"] else None)
    return {"schema_version": 1, "groups": groups, "measured_savings": None,
            "note": "Usage is CLI-reported, not a billing invoice. Missing cost or tokens are unknown, not zero."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path.home() / ".model-router" / "runs")
    args = parser.parse_args(argv)
    try:
        if not args.runs_dir.is_dir():
            raise ValueError("runs directory missing")
        items = []
        for path in sorted(args.runs_dir.glob("*/result.json")):
            if path.is_symlink():
                raise ValueError("symlinked run metadata refused")
            items.append(json.loads(path.read_text(encoding="utf-8")))
        print(json.dumps(aggregate(items), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError):
        print("usage report error: missing or invalid private run metadata", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
