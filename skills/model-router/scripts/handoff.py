#!/usr/bin/env python3
"""Create reviewable stage-to-stage handoff templates; never claim tasks are done."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def compact(value: object) -> str:
    return " ".join(str(value).split()).replace("|", "/")


def templates(task: dict, allocation: dict | None = None) -> list[tuple[str, str]]:
    if not isinstance(task, dict) or not isinstance(task.get("stages"), list) or not task["stages"]:
        raise ValueError("task JSON must contain a nonempty stages array")
    stages = task["stages"]
    allocations = allocation.get("stages") if allocation is not None and isinstance(allocation, dict) else None
    if allocation is not None and (not isinstance(allocations, list) or len(allocations) != len(stages)):
        raise ValueError("route result must contain the same number of stages as task file")
    files = []
    for i, stage in enumerate(stages):
        if not isinstance(stage, dict) or not isinstance(stage.get("name"), str) or not stage["name"].strip():
            raise ValueError("invalid task stage")
        name = compact(stage["name"])
        if allocations is not None and allocations[i].get("name") != stage["name"]:
            raise ValueError("route-result stage names/order must match the task file")
        assigned = allocations[i].get("primary") if allocations else None
        model = compact(assigned["id"]) if assigned else "TBD — no confirmed model assignment"
        availability = compact(assigned["availability"]) if assigned else "unverified"
        previous = compact(stages[i - 1]["name"]) if i else "None (initial stage)"
        following = compact(stages[i + 1]["name"]) if i + 1 < len(stages) else "Release / final acceptance"
        deliverable = compact(stage.get("deliverable", "Not specified; confirm before execution"))
        body = f"""# Stage {i + 1:02d}: {name} — Handoff template

> **UNFILLED TEMPLATE**. This file is a planning aid, not proof that any work ran, passed, or was approved.
> Never insert credentials, confidential code or user data in a public report.

- Project: {compact(task.get('name', 'Unnamed plan'))}
- Stage: {name}
- Expected deliverable: {deliverable}
- Upstream: {previous}
- Downstream: {following}
- Recommended model ID: `{model}` ({availability}; not a model switch)

## 1. Input artifacts and constraints

- [ ] Link to reviewed input specification / ADR / code commit: **TODO**
- [ ] Required files / interfaces and expected versions: **TODO**
- [ ] Privacy, budget and provider-transfer constraints verified: **TODO**

## 2. Decisions and implementation evidence

- [ ] Decisions made, with rationale: **TODO**
- [ ] Files / commits actually changed (or `none`): **TODO**
- [ ] Open questions, assumptions and incompatibilities: **TODO**

## 3. Objective acceptance and regression checks

- [ ] Acceptance tests / commands and exact observed results: **TODO — NOT RUN**
- [ ] Review required by next stage (where high risk): **TODO**
- [ ] Known failures and repro steps: **TODO**

## 4. Handoff / continuation

- [ ] Next-stage inputs to carry forward: **TODO**
- [ ] Non-negotiable architecture/security constraints: **TODO**
- [ ] Who verified this handoff and when: **TODO — NOT VERIFIED**

**Escalation:** Reroute before continuing when evidence conflicts, tool permissions change, or two attempts fail without progress. Cross-provider execution requires independent authorization.
"""
        files.append((f"handoff-{i + 1:02d}.md", body))
    return files


def write_templates(target: Path, files: list[tuple[str, str]], force: bool = False) -> list[Path]:
    if target.exists() and not target.is_dir():
        raise ValueError("--output-dir is not a directory")
    # Preflight all names. The generated filename is derived ONLY from index.
    paths = [target / name for name, _ in files]
    if any(p.exists() for p in paths) and not force:
        raise ValueError("handoff file already exists; explicitly pass --force to overwrite")
    target.mkdir(parents=True, exist_ok=True)
    for (name, body), path in zip(files, paths):
        path.write_text(body, encoding="utf-8")
    return paths


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task-file", required=True, type=Path)
    p.add_argument("--route-result", type=Path, help="Optional JSON result from route.py --format json")
    p.add_argument("--output-dir", type=Path, help="Explicit destination; without it print templates to stdout")
    p.add_argument("--force", action="store_true", help="Overwrite existing handoff files")
    args = p.parse_args()
    try:
        task = json.loads(args.task_file.read_text(encoding="utf-8"))
        allocation = json.loads(args.route_result.read_text(encoding="utf-8")) if args.route_result else None
        files = templates(task, allocation)
        if args.output_dir:
            for path in write_templates(args.output_dir, files, args.force):
                print(path)
        else:
            for name, body in files:
                print(f"<!-- {name} -->\n{body}")
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
        print(f"handoff error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
