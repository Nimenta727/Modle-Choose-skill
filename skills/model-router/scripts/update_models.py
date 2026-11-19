#!/usr/bin/env python3
"""Auditable read-only model discovery. Reports candidates; NEVER edits the registry."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

REGISTRY = Path(__file__).resolve().parents[1] / "references" / "model-registry.json"
# Broad family patterns, not hardcoded to current version/variant. Every discovery
# result is untrusted metadata to be independently reviewed before adding a model.
ID_PATTERNS = {
    "openai": re.compile(r"\bgpt-[a-z0-9]+(?:[.\-][a-z0-9]+)*\b", re.IGNORECASE),
    "anthropic": re.compile(r"\bclaude-[a-z0-9]+(?:-[a-z0-9]+)+\b", re.IGNORECASE),
}


def IDs(provider: str, page: str) -> set[str]:
    return {m.lower() for m in ID_PATTERNS[provider].findall(page)}


def audit(registry: dict, html_by_provider: dict[str, str] | None = None,
          now: datetime | None = None, inventories: list[dict] | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    verified = datetime.fromisoformat(registry["verified_at"])
    if verified.tzinfo is None:
        verified = verified.replace(tzinfo=timezone.utc)
    else:
        verified = verified.astimezone(timezone.utc)
    stale = now - verified > timedelta(hours=registry.get("refresh_after_hours", 24))
    known = {provider: {m["id"] for m in registry["models"] if m["provider"] == provider}
             for provider in ("openai", "anthropic")}
    report = {"registry_verified_at": registry["verified_at"], "check_at": now.isoformat(),
              "stale": stale, "official_ids_checked": bool(html_by_provider), "providers": {},
              "metadata_review_required": [],
              "note": "Discovery is NOT full metadata verification. Prices, capabilities and lifecycle remain unchanged."}
    for provider in ("openai", "anthropic"):
        entry = {"known_ids_present": [], "missing_from_official_page": [], "new_candidate_ids": [],
                 "account_inventory_candidates": [], "inventory_status": "not supplied"}
        if html_by_provider is not None and provider in html_by_provider:
            found = IDs(provider, html_by_provider[provider])
            entry.update({"known_ids_present": sorted(found & known[provider]),
                          "missing_from_official_page": sorted(known[provider] - found),
                          "new_candidate_ids": sorted(found - known[provider])})
            # IDs missing from HTML might be client-rendered or elsewhere in docs.
            if entry["missing_from_official_page"] or entry["new_candidate_ids"]:
                report["metadata_review_required"].append(provider)
        for inv in inventories or []:
            if inv.get("provider") != provider or inv.get("surface") != "api":
                continue
            if inv.get("status") not in ("listed", "verified"):
                entry["inventory_status"] = "unverified"
                continue
            checked = inv.get("checked_at")
            try:
                timestamp = datetime.fromisoformat(checked.replace("Z", "+00:00"))
            except (AttributeError, ValueError):
                entry["inventory_status"] = "invalid timestamp"
                continue
            if timestamp.tzinfo is None or now - timestamp.astimezone(timezone.utc) > timedelta(hours=24) or timestamp.astimezone(timezone.utc) > now + timedelta(minutes=5):
                entry["inventory_status"] = "stale"
                continue
            model_ids = inv.get("available_models", [])
            if not isinstance(model_ids, list):
                entry["inventory_status"] = "malformed"
                continue
            candidates = {name for name in model_ids if isinstance(name, str) and name not in known[provider]}
            entry["account_inventory_candidates"] = sorted(set(entry["account_inventory_candidates"]) | candidates)
            entry["inventory_status"] = "account listed (not call verified)"
            if candidates and provider not in report["metadata_review_required"]:
                report["metadata_review_required"].append(provider)
        report["providers"][provider] = entry
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fetch official docs HTML; no API credentials")
    parser.add_argument("--offline", action="store_true", help="Only audit local freshness/inventory files")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--inventory-file", action="append", type=Path,
                        help="Optional read-only account inventory JSON; repeat for multiple providers")
    parser.add_argument("--report-file", type=Path, help="Write candidate review JSON without changing model registry")
    args = parser.parse_args()
    if args.check and args.offline:
        parser.error("choose --check or --offline")
    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        inventories = [json.loads(p.read_text(encoding="utf-8")) for p in args.inventory_file or []]
        pages = None
        if args.check:
            pages = {}
            for provider, url in registry["sources"].items():
                req = Request(url, headers={"User-Agent": "model-router/1.2 (official-docs read-only audit)"})
                with urlopen(req, timeout=15) as response:
                    pages[provider] = response.read(6_000_000).decode("utf-8", errors="replace")
        report = audit(registry, pages, inventories=inventories)
        output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.report_file:
            args.report_file.write_text(output, encoding="utf-8")
        print(output, end="")
        if report["metadata_review_required"]:
            print("warning: model candidates or documentation differences require manual verification", file=sys.stderr)
        return 0
    except (OSError, HTTPError, URLError, KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"verification unavailable: {type(e).__name__} (keep dated cache; never refresh metadata silently)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
