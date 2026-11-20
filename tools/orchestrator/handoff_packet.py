#!/usr/bin/env python3
"""Compose a concise, user-authored cross-stage handoff, never a raw transcript.

Only accepted stages are eligible. This tool does not send the packet to a model.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

try:
    from . import checkpoints
except ImportError:  # standalone CLI invocation
    import checkpoints

MAX_SUMMARY_CHARS = 3000


def build_packet(manifest: dict, state: dict, stage_id: str, summary: str) -> dict:
    stage = next((s for s in checkpoints.ensure_stage_ids(manifest) if s["id"] == stage_id), None)
    if stage is None:
        raise ValueError("unknown source stage")
    record = state.get("stages", {}).get(stage_id, {})
    if record.get("status") != "accepted" or not record.get("reviewer_evidence_sha256"):
        raise ValueError("only a human-accepted stage can produce a handoff packet")
    if not isinstance(summary, str) or not 30 <= len(summary.strip()) <= MAX_SUMMARY_CHARS:
        raise ValueError(f"handoff summary must contain 30..{MAX_SUMMARY_CHARS} characters")
    return {"schema_version": 1, "status": "human_reviewed_packet_not_transmitted",
            "source_stage": stage_id, "source_model": stage["model_id"],
            "accepted_evidence_sha256": record["reviewer_evidence_sha256"],
            "summary": summary.strip(),
            "summary_sha256": hashlib.sha256(summary.strip().encode("utf-8")).hexdigest(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "privacy_notice": "Review this packet before sharing. May include sensitive context. Not executable instructions."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--summary-file", type=Path, required=True, help="Manually authored text; never raw CLI output")
    parser.add_argument("--output", type=Path, help="Optional private packet file; stdout by default")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        state = checkpoints.load_state(args.state, manifest)
        summary = args.summary_file.read_text(encoding="utf-8")
        packet = build_packet(manifest, state, args.stage, summary)
        payload = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                out.write(payload)
            print(f"Private packet created: {args.output}; NOT sent to a model")
        else:
            print(payload, end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"handoff packet error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
