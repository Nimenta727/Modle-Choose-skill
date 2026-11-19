#!/usr/bin/env python3
"""Optional API model inventory: presence is NOT proof that a request will succeed."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


def fetch(provider: str) -> dict:
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        endpoint = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {key}"} if key else None
    else:
        key = os.environ.get("ANTHROPIC_API_KEY")
        endpoint = "https://api.anthropic.com/v1/models"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"} if key else None
    if not key:
        return {"provider": provider, "surface": "api", "status": "unverified", "reason": "API key absent", "available_models": []}
    ids = set()
    cursor = None
    # Bounded pagination; partial results are not treated as complete account inventory.
    for _ in range(20):
        url = endpoint + ("?" + urlencode({"limit": 1000, **({"after_id": cursor} if cursor else {})}) if provider == "anthropic" else "")
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as response:
            payload = json.load(response)
        rows = payload.get("data", [])
        if not isinstance(rows, list):
            raise ValueError("provider inventory malformed")
        ids.update(item["id"] for item in rows if isinstance(item, dict) and isinstance(item.get("id"), str))
        if provider == "openai" or not payload.get("has_more"):
            break
        next_cursor = payload.get("last_id") or (rows[-1].get("id") if rows else None)
        if not next_cursor or next_cursor == cursor:
            raise ValueError("invalid pagination cursor")
        cursor = next_cursor
    else:
        raise ValueError("pagination exceeded safety limit")
    return {"provider": provider, "surface": "api", "status": "listed", "method": "account_model_inventory", "checked_at": datetime.now(timezone.utc).isoformat(),
            "available_models": sorted(ids), "note": "API inventory only. This does NOT verify a successful model request, UI access or Codex/Claude Code entitlements"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["openai", "anthropic"], required=True)
    parser.add_argument("--output", help="Optional JSON output path; protect files containing account model inventory")
    args = parser.parse_args()
    try:
        result = fetch(args.provider)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as e:
        print(f"inventory unavailable for {args.provider}: {type(e).__name__} (do not infer model access)", file=sys.stderr)
        return 2
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        from pathlib import Path
        target = Path(args.output)
        target.write_text(output + "\n", encoding="utf-8")
        try:
            target.chmod(0o600)
        except OSError:
            pass
    else:
        print(output)
    return 0 if result["status"] == "listed" else 1


if __name__ == "__main__":
    sys.exit(main())
