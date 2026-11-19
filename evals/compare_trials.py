#!/usr/bin/env python3
"""Conservative paired-trial analysis; proposals are NEVER automatically applied."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
import json
import math
from pathlib import Path
import re
import sys

DEFAULT_TRIALS = Path(__file__).with_name("trials.json")
# Require frozen fixture/rubric fingerprints for comparison. IDs are not proof by
# themselves: experiment owners must verify and document the actual artifacts.
HEX64 = re.compile(r"^[a-fA-F0-9]{64}$")


def sign_tail(wins: int, n: int) -> float:
    """One-sided exact binomial p-value under exchangeable 50/50 wins."""
    return sum(math.comb(n, k) for k in range(wins, n + 1)) / (2 ** n)


def compare_trials(data: dict, min_tasks: int = 6, min_repeats: int = 2) -> dict:
    if type(min_tasks) is not int or min_tasks < 6 or type(min_repeats) is not int or min_repeats < 2:
        raise ValueError("comparison requires min_tasks >= 6 and min_repeats >= 2")
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("trials"), list):
        raise ValueError("expected schema_version=1 with trials array")
    runs = set()
    groups: dict[tuple, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    incomplete = 0
    for row in data["trials"]:
        if not isinstance(row, dict):
            raise ValueError("trial must be an object")
        run_id = row.get("run_id")
        if not isinstance(run_id, str) or not run_id or run_id in runs:
            raise ValueError("missing or duplicated run_id")
        runs.add(run_id)
        for field in ("task_type", "task_id", "model_id"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"missing {field}")
        if type(row.get("passed")) is not bool:
            raise ValueError("passed must come from real objective acceptance checks")
        if not all(isinstance(row.get(field), str) and HEX64.fullmatch(row[field]) for field in ("fixture_sha256", "rubric_sha256", "harness_sha256")):
            incomplete += 1
            continue
        surface = row.get("surface")
        if not isinstance(surface, str) or not surface:
            incomplete += 1
            continue
        key = (row["task_type"], row["task_id"], row["fixture_sha256"].lower(),
               row["rubric_sha256"].lower(), row["harness_sha256"].lower(), surface)
        groups[key][row["model_id"]].append(row["passed"])
    # Each frozen (task, fixture, rubric, surface) contributes once per pair.
    pairs: dict[tuple[str, str, str], list[tuple[str, float, float]]] = defaultdict(list)
    seen_task_keys: set[tuple[str, str]] = set()
    for (task_type, task_id, _fixture, _rubric, _harness, _surface), per_model in sorted(groups.items()):
        for a, b in combinations(sorted(per_model), 2):
            if min(len(per_model[a]), len(per_model[b])) < min_repeats:
                continue
            # Count any one task_id at most once per task_type and pair, even if
            # an experimenter duplicated that task under multiple fixture hashes.
            task_dedupe_key = (f"{task_type}:{a}:{b}", task_id)
            if task_dedupe_key in seen_task_keys:
                continue
            seen_task_keys.add(task_dedupe_key)
            a_rate = sum(per_model[a]) / len(per_model[a])
            b_rate = sum(per_model[b]) / len(per_model[b])
            pairs[(task_type, a, b)].append((task_id, a_rate, b_rate))
    comparisons = []
    suggested = defaultdict(float)
    evidence = defaultdict(list)
    for (task_type, a, b), entries in sorted(pairs.items()):
        wins_a = sum(x > y for _, x, y in entries)
        wins_b = sum(x < y for _, x, y in entries)
        ties = len(entries) - wins_a - wins_b
        decisive = wins_a + wins_b
        p = sign_tail(max(wins_a, wins_b), decisive) if decisive else 1.0
        statistically_relevant = (len(entries) >= min_tasks and decisive >= min_tasks
                                  and p <= 0.05 and wins_a != wins_b)
        verdict = "insufficient" if not statistically_relevant else ("a_better" if wins_a > wins_b else "b_better")
        comparisons.append({"task_type": task_type, "model_a": a, "model_b": b,
                            "matched_distinct_tasks": len(entries), "decisive_tasks": decisive,
                            "a_wins": wins_a, "b_wins": wins_b, "ties": ties,
                            "one_sided_sign_test_p": round(p, 6),
                            "status": verdict,
                            "caution": "Exploratory unadjusted sign test; multiple comparisons, setup bias, effect sizes and missing data require human review"})
        if statistically_relevant:
            winner, loser = (a, b) if wins_a > wins_b else (b, a)
            suggested[(winner, task_type)] += 4.0
            suggested[(loser, task_type)] -= 4.0
            label = f"paired {task_type} {a} vs {b}: {len(entries)} tasks; exact p={p:.4g}"
            evidence[(winner, task_type)].append(label)
            evidence[(loser, task_type)].append(label)
    proposal = []
    for (model_id, task_type), delta in sorted(suggested.items()):
        proposal.append({"model_id": model_id, "task_type": task_type,
                         "score_delta": max(-8.0, min(8.0, delta)),
                         "evidence": "; ".join(evidence[(model_id, task_type)])})
    return {"schema_version": 1, "status": "proposal_unreviewed",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "user_supplied_paired_trials_not_independently_audited",
            "run_count": len(runs), "incomplete_comparison_metadata": incomplete,
            "minimum_distinct_paired_tasks": min_tasks, "minimum_repeats_per_model_per_task": min_repeats,
            "comparisons": comparisons, "suggested_adjustments": proposal,
            "note": "Proposal is NOT an approved calibration. One-sided p-values are exploratory and NOT corrected for testing multiple model pairs. Independently review trial provenance, harness identity and confounders, then manually create status=user_reviewed, reviewed_at, adjustments. Route never auto-applies this report."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trials", type=Path, default=DEFAULT_TRIALS)
    p.add_argument("--min-tasks", type=int, default=6)
    p.add_argument("--min-repeats", type=int, default=2)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args()
    try:
        report = compare_trials(json.loads(args.trials.read_text(encoding="utf-8")), args.min_tasks, args.min_repeats)
        body = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(body, encoding="utf-8")
        print(body, end="")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        print(f"pair comparison error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
