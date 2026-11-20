#!/usr/bin/env python3
"""Opt-in, isolated Claude Code / Codex CLI Plan Mode smoke evaluation.

Default is dry-run: NO remote model requests. Live mode requires --execute.
Plan-section compliance is NOT proof of Agent Skill activation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUITE = Path(__file__).with_name("trigger_cases.json")
INSTALLER = ROOT / "tools/install.py"


def command_for(agent: str, prompt: str) -> list[str]:
    if agent == "claude":
        # Plan Mode avoids changing the sandbox's source files.
        return ["claude", "-p", prompt, "--permission-mode", "plan", "--output-format", "stream-json", "--verbose"]
    if agent == "codex":
        # Explicit read-only sandbox; never request --full-auto or bypass permissions.
        return ["codex", "exec", "--json", "--sandbox", "read-only", prompt]
    raise ValueError(f"unknown agent: {agent}")


def load_cases(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or not isinstance(value.get("cases"), list):
        raise ValueError("invalid trigger-case suite")
    cases = value["cases"]
    ids = [c["id"] for c in cases]
    if any(not isinstance(item, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", item) for item in ids):
        raise ValueError("case IDs must be safe lowercase slugs")
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("empty/duplicate trigger cases")
    for case in cases:
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError("missing prompt")
        if type(case.get("expects_allocation")) is not bool:
            raise ValueError("expects_allocation must be a boolean")
    return cases


def _json_events(trace: str) -> list[dict]:
    result = []
    for line in trace.splitlines():
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                result.append(item)
        except json.JSONDecodeError:
            continue
    return result


def extract_result(agent: str, trace: str) -> dict:
    """Read final answer independently from observed SKILL.md file reads.

    A mention of a Skill in the response is NOT counted as activation evidence.
    """
    events = _json_events(trace)
    final_parts = []
    tool_inputs = []
    for event in events:
        if agent == "codex":
            item = event.get("item") or {}
            if not isinstance(item, dict):
                continue
            if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                final_parts.append(str(item.get("text", "")))
            if item.get("type") in {"command_execution", "tool_call"}:
                tool_inputs.append(str(item.get("command") or item.get("arguments") or ""))
        else:
            if event.get("type") == "result" and isinstance(event.get("result"), str):
                final_parts.append(event["result"])
            message = event.get("message") or {}
            if not isinstance(message, dict):
                continue
            for item in message.get("content", []) if isinstance(message.get("content", []), list) else []:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_inputs.append(json.dumps(item.get("input", {}), ensure_ascii=False))
    final = final_parts[-1] if final_parts else ""
    # Check tool inputs only, never prompts, narration, or natural-language responses.
    skill_read_observed = any(
        re.search(r"(?:^|[\\/])(?:model-router[\\/])?SKILL\.md\b", inp, re.I)
        and "model-router" in inp.lower() for inp in tool_inputs
    )
    allocation_heading = bool(re.search(r"(?:Model allocation\s*/\s*模型分配|模型分配|^#{1,4}\s*Model allocation)", final, re.I | re.M))
    # An isolated heading is not enough: require at least one tabular stage entry
    # with primary and backup signals (Chinese or English).
    has_table = len([line for line in final.splitlines() if line.strip().startswith("|")]) >= 3
    has_primary_backup = bool(re.search(r"(?:主选|primary)", final, re.I)) and bool(re.search(r"(?:备用|backup)", final, re.I))
    plan_contract = allocation_heading and has_table and has_primary_backup
    return {"events": len(events), "final_chars": len(final), "final_sha256": hashlib.sha256(final.encode()).hexdigest(),
            "allocation_heading": allocation_heading, "allocation_contract": plan_contract,
            "skill_file_read_observed": skill_read_observed}


def prepare_workspace(path: Path, agent: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "sample.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True, timeout=10)
    install = subprocess.run([sys.executable, str(INSTALLER), "--target", str(path), "--agents", agent],
                             cwd=ROOT, check=False, capture_output=True, text=True, timeout=15)
    if install.returncode != 0:
        raise RuntimeError("installer failed in isolated workspace")


def evaluate_case(case: dict, agent: str, timeout: int, trace_dir: Path | None) -> dict:
    with tempfile.TemporaryDirectory(prefix="model-router-live-") as directory:
        sandbox = Path(directory)
        prepare_workspace(sandbox, agent)
        cmd = command_for(agent, case["prompt"])
        try:
            run = subprocess.run(cmd, cwd=sandbox, capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {"id": case["id"], "status": "inconclusive", "reason": "timeout"}
        except FileNotFoundError:
            return {"id": case["id"], "status": "inconclusive", "reason": "CLI missing"}
        if trace_dir is not None:
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_path = trace_dir / f"{agent}-{case['id']}.jsonl"
            trace_path.write_text(run.stdout, encoding="utf-8")
            trace_path.chmod(0o600)
        if run.returncode:
            # Do not expose raw stderr: may contain account paths or credentials.
            return {"id": case["id"], "status": "inconclusive", "reason": "nonzero CLI exit", "exit_code": run.returncode}
        detail = extract_result(agent, run.stdout)
        if not detail["final_chars"]:
            return {"id": case["id"], "status": "inconclusive", "reason": "no parseable final text", **detail}
        passed = (detail["allocation_contract"] if case["expects_allocation"] else not detail["allocation_heading"])
        return {"id": case["id"], "status": "passed" if passed else "failed", "expected_allocation": case["expects_allocation"], **detail}


def summarize(agent: str, results: list[dict], mode: str) -> dict:
    # A measurable output contract, not a claim of a 100% activation rate.
    executed = [r for r in results if r["status"] in {"passed", "failed"}]
    positives = [r for r in executed if r.get("expected_allocation") is True]
    negatives = [r for r in executed if r.get("expected_allocation") is False]
    return {"kind": "CLI-output-contract-smoke-not-model-benchmark",
            "agent": agent, "mode": mode, "created_at": datetime.now(timezone.utc).isoformat(),
            "total": len(results), "evaluated": len(executed), "passed": sum(r["status"] == "passed" for r in executed),
            "inconclusive": sum(r["status"] == "inconclusive" for r in results),
            "positive_with_allocation": sum(r["allocation_contract"] for r in positives), "positive_total": len(positives),
            "negative_without_allocation": sum(not r["allocation_heading"] for r in negatives), "negative_total": len(negatives),
            "observable_skill_file_reads": sum(r.get("skill_file_read_observed", False) for r in executed),
            "results": results,
            "caveat": "Output compliance is not proof of Skill activation. Missing tool-read evidence does not prove a Skill was not loaded. Account-based execution is opt-in."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--agent", choices=["claude", "codex"], required=True)
    p.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    p.add_argument("--case-id", action="append", help="Repeat to select specific cases")
    p.add_argument("--max-runs", type=int, default=5, help="Limit opt-in account calls, default 5")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--execute", action="store_true", help="Explicitly authorize real CLI model calls")
    p.add_argument("--report", type=Path, help="Write metadata-only JSON report")
    p.add_argument("--trace-dir", type=Path, help="Opt-in raw trace files; handle as sensitive private data")
    args = p.parse_args()
    try:
        if not (1 <= args.max_runs <= 20) or not (30 <= args.timeout <= 1800):
            raise ValueError("max-runs must be 1..20; timeout 30..1800 seconds")
        cases = load_cases(args.suite)
        if args.case_id:
            selected = set(args.case_id)
            unknown = selected - {c["id"] for c in cases}
            if unknown:
                raise ValueError(f"unknown case IDs: {sorted(unknown)}")
            cases = [c for c in cases if c["id"] in selected]
        cases = cases[:args.max_runs]
        if args.execute and shutil.which(args.agent if args.agent == "claude" else "codex") is None:
            raise ValueError(f"{args.agent} CLI not installed; no live tests performed")
        if args.trace_dir and not args.execute:
            raise ValueError("--trace-dir requires --execute")
        if args.execute:
            rows = [evaluate_case(c, args.agent, args.timeout, args.trace_dir) for c in cases]
        else:
            rows = [{"id": c["id"], "status": "skipped", "reason": "dry-run: no model call",
                     "command": command_for(args.agent, "<test prompt>")}
                    for c in cases]
        result = summarize(args.agent, rows, "live" if args.execute else "dry-run")
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not args.execute or (result["evaluated"] == len(rows) and result["passed"] == len(rows)) else 1
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"live evaluator error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
