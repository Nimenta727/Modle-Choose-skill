#!/usr/bin/env python3
"""Opt-in, crash-conscious human-review checkpoints for the local orchestrator.

Only metadata is persisted. No model call, raw prompt, credentials, or transcript is stored.
A file lock prevents simultaneous updates; an abandoned lock requires operator inspection.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys

VERSION = 1
MAX_ATTEMPTS = 2
STATES = frozenset({"pending", "running", "cli_completed_unreviewed", "accepted", "failed"})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def manifest_digest(manifest: dict) -> str:
    encoded = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def ensure_stage_ids(manifest: dict) -> list[dict]:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("invalid execution manifest schema")
    stages = manifest.get("stages")
    if not isinstance(stages, list) or not 1 <= len(stages) <= 30:
        raise ValueError("execution manifest requires 1..30 stages")
    ids = [s.get("id") if isinstance(s, dict) else None for s in stages]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("stage IDs must be unique nonempty strings")
    for index, stage in enumerate(stages):
        deps = stage.get("depends_on", [])
        if not isinstance(deps, list) or len(deps) != len(set(deps)) or any(x not in ids[:index] for x in deps):
            raise ValueError(f"invalid dependency in stage {ids[index]}")
    return stages


@contextmanager
def locked(path: Path):
    lock = path.with_name(path.name + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError(f"checkpoint locked: {lock}; inspect the active process before manually clearing a stale lock") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(f"pid={os.getpid()} utc={utc_now()}\n")
        yield
    finally:
        lock.unlink(missing_ok=True)


def atomic_save(path: Path, document: dict, *, create_only: bool = False) -> None:
    if create_only and path.exists():
        raise ValueError(f"checkpoint already exists: {path}")
    temp = path.with_name(path.name + ".tmp-" + secrets.token_hex(6))
    raw = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    try:
        fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if create_only and path.exists():
            raise ValueError(f"checkpoint already exists: {path}")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def initialize(path: Path, manifest: dict) -> dict:
    rows = ensure_stage_ids(manifest)
    state = {"schema_version": VERSION, "manifest_sha256": manifest_digest(manifest),
             "created_at": utc_now(), "stages": {
                r["id"]: {"status": "pending", "attempts": 0, "updated_at": utc_now()} for r in rows
             }}
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with locked(path):
        atomic_save(path, state, create_only=True)
    return state


def load_state(path: Path, manifest: dict) -> dict:
    ensure_stage_ids(manifest)
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("schema_version") != VERSION or state.get("manifest_sha256") != manifest_digest(manifest):
        raise ValueError("checkpoint/manifest mismatch; review changed tasks and initialize a NEW checkpoint")
    if set(state.get("stages", {})) != {r["id"] for r in manifest["stages"]}:
        raise ValueError("checkpoint stage IDs differ from manifest")
    if any(not isinstance(s, dict) or s.get("status") not in STATES or type(s.get("attempts")) is not int
           or s["attempts"] < 0 or s["attempts"] > MAX_ATTEMPTS for s in state["stages"].values()):
        raise ValueError("invalid checkpoint state")
    return state


def status(path: Path, manifest: dict) -> dict:
    return load_state(path, manifest)


def begin(path: Path, manifest: dict, stage_id: str, *, retry_failed: bool = False) -> dict:
    with locked(path):
        state = load_state(path, manifest)
        if stage_id not in state["stages"]:
            raise ValueError("unknown stage")
        current = state["stages"][stage_id]
        if current["status"] not in ({"pending", "failed"} if retry_failed else {"pending"}):
            raise ValueError(f"stage {stage_id} is {current['status']}; no silent re-execution")
        if current["attempts"] >= MAX_ATTEMPTS:
            raise ValueError("maximum explicit attempts reached; revise the plan before further requests")
        row = next(s for s in manifest["stages"] if s["id"] == stage_id)
        for dep in row.get("depends_on", []):
            if state["stages"][dep]["status"] != "accepted":
                raise ValueError(f"dependency {dep} must be explicitly accepted before {stage_id}")
        current.update(status="running", attempts=current["attempts"] + 1, updated_at=utc_now())
        atomic_save(path, state)
        return current.copy()


def complete(path: Path, manifest: dict, stage_id: str, record: dict) -> dict:
    with locked(path):
        state = load_state(path, manifest)
        current = state["stages"][stage_id]
        if current["status"] != "running":
            raise ValueError("only an active stage can record a CLI completion")
        new_status = "cli_completed_unreviewed" if record.get("state") == "cli_completed_unreviewed" else "failed"
        current.update(status=new_status, updated_at=utc_now(),
                       exit_code=record.get("exit_code"),
                       last_run_dir=record.get("run_dir"))
        if new_status == "failed":
            current["failure_kind"] = "timeout_or_cli_failure"
        atomic_save(path, state)
        return current.copy()


def accept(path: Path, manifest: dict, stage_id: str, evidence: str) -> dict:
    if not isinstance(evidence, str) or not 12 <= len(evidence.strip()) <= 1000:
        raise ValueError("human acceptance needs a 12..1000 character evidence note")
    with locked(path):
        state = load_state(path, manifest)
        current = state["stages"].get(stage_id)
        if current is None:
            raise ValueError("unknown stage")
        if current["status"] != "cli_completed_unreviewed":
            raise ValueError("only completed but unreviewed CLI output may be human-accepted")
        current.update(status="accepted", updated_at=utc_now(),
                       reviewer_evidence_sha256=hashlib.sha256(evidence.encode("utf-8")).hexdigest())
        atomic_save(path, state)
        return current.copy()


def reject(path: Path, manifest: dict, stage_id: str, reason: str) -> dict:
    if not isinstance(reason, str) or not 8 <= len(reason.strip()) <= 500:
        raise ValueError("rejection requires a meaningful 8..500 character reason")
    with locked(path):
        state = load_state(path, manifest)
        current = state["stages"].get(stage_id)
        if current is None or current["status"] != "cli_completed_unreviewed":
            raise ValueError("only an unreviewed result can be rejected")
        current.update(status="failed", updated_at=utc_now(), failure_kind="human_rejected",
                       reviewer_reason_sha256=hashlib.sha256(reason.encode("utf-8")).hexdigest())
        atomic_save(path, state)
        return current.copy()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True, help="Private checkpoint outside the workspace")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--init", action="store_true")
    action.add_argument("--status", action="store_true")
    action.add_argument("--accept-stage")
    action.add_argument("--reject-stage")
    parser.add_argument("--confirm-stage", help="Must match acceptance/rejection stage ID")
    parser.add_argument("--evidence", help="Human-reviewed acceptance evidence; persisted as SHA-256 only")
    parser.add_argument("--reason", help="Human rejection reason; persisted as SHA-256 only")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if args.init:
            result = initialize(args.state, manifest)
        elif args.status:
            result = status(args.state, manifest)
        elif args.accept_stage:
            if args.confirm_stage != args.accept_stage:
                raise ValueError("--confirm-stage must exactly match --accept-stage")
            result = accept(args.state, manifest, args.accept_stage, args.evidence or "")
        else:
            if args.confirm_stage != args.reject_stage:
                raise ValueError("--confirm-stage must exactly match --reject-stage")
            result = reject(args.state, manifest, args.reject_stage, args.reason or "")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"checkpoint error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
