#!/usr/bin/env python3
"""Read-only official-page ID/freshness checker; never silently mutates pricing or registry."""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError

REGISTRY = Path(__file__).resolve().parents[1] / "references" / "model-registry.json"
# Narrow expressions; candidate IDs must be reviewed, NOT auto-written.
ID_PATTERNS = {
    "openai": re.compile(r"\bgpt-6(?:\.\d+)?-(?:astra|sol|terra|luna)\b"),
    "anthropic": re.compile(r"\bclaude-(?:fable|opus|sonnet|haiku)-\d+(?:-\d+)?\b"),
}


def audit(registry: dict, html_by_provider: dict[str, str] | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    verified = datetime.fromisoformat(registry["verified_at"]).replace(tzinfo=timezone.utc)
    stale = now - verified > timedelta(hours=registry.get("refresh_after_hours", 24))
    report = {"registry_verified_at": registry["verified_at"], "check_at": now.isoformat(), "stale": stale,
              "official_ids_checked": html_by_provider is not None, "providers": {}, "note": "Read-only audit; page checks do not refresh pricing, lifecycle, or account access."}
    if html_by_provider is not None:
        for provider, page in html_by_provider.items():
            found = set(ID_PATTERNS[provider].findall(page))
            known = {m["id"] for m in registry["models"] if m["provider"] == provider}
            report["providers"][provider] = {"known_ids_present": sorted(found & known),
                "missing_from_official_page": sorted(known - found), "new_candidate_ids": sorted(found - known)}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fetch public official documentation, no API credentials")
    parser.add_argument("--offline", action="store_true", help="Only assess local snapshot age")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    args = parser.parse_args()
    if args.check and args.offline:
        parser.error("choose --check or --offline")
    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        pages = None
        if args.check:
            pages = {}
            for provider, url in registry["sources"].items():
                req = Request(url, headers={"User-Agent": "model-router/1.0 (documentation check)"})
                with urlopen(req, timeout=15) as response:
                    pages[provider] = response.read(6_000_000).decode("utf-8", errors="replace")
        report = audit(registry, pages)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if pages and any(v["missing_from_official_page"] for v in report["providers"].values()):
            print("warning: some known IDs absent from downloaded HTML; possible rendering or lifecycle change; review manually", file=sys.stderr)
        return 0
    except (OSError, URLError, KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"verification unavailable: {e} (keep dated cache; do not mark freshly verified)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
