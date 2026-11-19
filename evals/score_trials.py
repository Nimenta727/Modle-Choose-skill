#!/usr/bin/env python3
"""Summarize real, externally collected task outcomes; never invent benchmark scores."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import median
import sys

DEFAULT_TRIALS = Path(__file__).with_name("trials.json")


def compute_report(data: dict, min_samples: int = 5) -> dict:
    if data.get("schema_version") != 1 or not isinstance(data.get("trials"), list):
        raise ValueError("expected schema_version=1 and a trials array")
    if min_samples < 2:
        raise ValueError("minimum sample size must be >= 2")
    groups = defaultdict(list)
    run_ids = set()
    for row in data["trials"]:
        if not isinstance(row, dict):
            raise ValueError("trial must be an object")
        for key in ("run_id", "task_id", "task_type", "model_id"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"missing required trial field {key}")
        if row["run_id"] in run_ids:
            raise ValueError("duplicate run_id")
        run_ids.add(row["run_id"])
        if type(row.get("passed")) is not bool:
            raise ValueError("passed must be a boolean from objective acceptance checks")
        for field in ("cost_usd", "elapsed_seconds"):
            value = row.get(field)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{field} must be a finite nonnegative number")
        groups[(row["task_type"], row["model_id"])].append(row)
    entries = []
    for (task_type, model_id), rows in sorted(groups.items()):
        n = len(rows)
        successful = sum(r["passed"] for r in rows)
        cost = sum(r["cost_usd"] for r in rows)
        unique_tasks = len({r["task_id"] for r in rows})
        entries.append({"task_type": task_type, "model_id": model_id,
                        "samples": n, "unique_tasks": unique_tasks,
                        "accepted": successful, "acceptance_rate": round(successful / n, 4),
                        "mean_cost_usd": round(cost / n, 4),
                        "median_elapsed_seconds": round(median(r["elapsed_seconds"] for r in rows), 2),
                        "cost_per_accepted_usd": round(cost / successful, 4) if successful else None,
                        "sample_sufficient": n >= min_samples and unique_tasks >= 2})
    return {"kind": "observed-task-outcomes-not-controlled-benchmark",
            "trial_count": len(run_ids), "min_samples": min_samples,
            "status": "no_empirical_trials" if not run_ids else "uncontrolled-observations",
            "groups": entries,
            "caveat": "No cross-model ranking: compare only same tasks, equivalent environment, accepted test rubric and repeated trials. Never auto-write registry priors from these aggregates."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trials", type=Path, default=DEFAULT_TRIALS)
    p.add_argument("--min-samples", type=int, default=5)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        report = compute_report(json.loads(args.trials.read_text(encoding="utf-8")), args.min_samples)
        output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        print(output, end="")
        return 0
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as e:
        print(f"trial scoring error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
