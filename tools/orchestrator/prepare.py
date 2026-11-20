#!/usr/bin/env python3
"""Convert a Model Router result into an UNAPPROVED execution manifest.

This is a local data transformation. It never calls a model or grants permission.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

try:
    from . import token_budget
except ImportError:
    import token_budget


def stage_id(name: str, index: int) -> str:
    stem = re.sub(r"[^a-z0-9-]+", "-", name.lower().replace("_", "-" )).strip("-")[:40]
    return f"s{index + 1:02d}-{stem or 'stage'}"


def provider_for(candidate: dict) -> str:
    if candidate.get("provider") in ("openai", "anthropic"):
        return candidate["provider"]
    identifier = candidate.get("id", "")
    if identifier.startswith("claude-"):
        return "anthropic"
    if identifier.startswith("gpt-"):
        return "openai"
    raise ValueError(f"unknown candidate provider: {identifier!r}")


def build_manifest(task: dict, routing: dict) -> dict:
    stages = task.get("stages")
    allocations = routing.get("stages")
    if not isinstance(stages, list) or not stages or len(stages) > 30:
        raise ValueError("task.stages must contain 1-30 items")
    if not isinstance(allocations, list) or len(allocations) != len(stages):
        raise ValueError("routing stages do not match task stages")
    result = []
    for n, (stage, assigned) in enumerate(zip(stages, allocations)):
        if stage.get("name") != assigned.get("name"):
            raise ValueError(f"stage order mismatch at {n + 1}")
        primary = assigned.get("primary")
        advisory = assigned.get("external_advisory")
        candidate = primary or advisory
        if not candidate or not isinstance(candidate.get("id"), str):
            raise ValueError(f"stage {n + 1} lacks even a conditional candidate; reroute first")
        provider = provider_for(candidate)
        deliverable = stage.get("deliverable", "Deliverable described in the technical plan")
        user_prompt = stage.get("prompt")
        if user_prompt is not None and (not isinstance(user_prompt, str) or not user_prompt.strip()):
            raise ValueError("a custom prompt must be a nonempty string")
        prompt = user_prompt or f"Work on phase: {stage['name']}\nDeliverable: {deliverable}\n"
        if len(prompt) > 30000:
            raise ValueError("stage prompt is too long")
        context_files = token_budget.validate_context_files(stage.get("context_files", []))
        result.append({
            "id": stage_id(stage["name"], n),
            "name": stage["name"],
            "agent": "codex" if provider == "openai" else "claude",
            "provider": provider,
            "model_id": candidate["id"],
            "cli_model": "",  # Explicit local alias/ID is required; API IDs are not portable.
            "source_availability": candidate.get("availability", candidate.get("status", "conditional")),
            "approved": False,
            "mode": "read-only",
            "prompt": prompt,
            "deliverable": deliverable,
            "context_files": context_files,
            "token_budget": {"max_prompt_chars": token_budget.DEFAULT_PROMPT_CHARS,
                             "max_handoff_chars": token_budget.DEFAULT_HANDOFF_CHARS,
                             "max_claude_turns": token_budget.DEFAULT_CLAUDE_TURNS},
            # Sequential by default. Review dependencies before approving stages.
            "depends_on": [result[-1]["id"]] if result else [],
        })
    return {"schema_version": 1,
            "description": "Review every stage, set cli_model and approved=true before any live execution.",
            "source_registry_verified_at": routing.get("registry_verified_at"),
            "stages": result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-file", type=Path, required=True)
    parser.add_argument("--route-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Explicit destination; stdout by default")
    parser.add_argument("--force", action="store_true", help="Replace an existing output manifest")
    args = parser.parse_args(argv)
    try:
        task = json.loads(args.task_file.read_text(encoding="utf-8"))
        route = json.loads(args.route_file.read_text(encoding="utf-8"))
        value = json.dumps(build_manifest(task, route), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("w" if args.force else "x", encoding="utf-8") as f:
                f.write(value)
            print(f"Unapproved manifest saved to {args.output}")
        else:
            print(value, end="")
        return 0
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"prepare error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
