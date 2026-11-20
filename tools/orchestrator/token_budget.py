#!/usr/bin/env python3
"""Prompt size guardrails for supervised CLI stages (zero API calls).

Character caps are enforceable; token estimates are *rough* and not billing
measurements. We never truncate user instructions or reviewed handoffs silently.
"""
from __future__ import annotations

import math
from pathlib import PurePosixPath
import re

DEFAULT_PROMPT_CHARS = 6000
DEFAULT_HANDOFF_CHARS = 1500
DEFAULT_CLAUDE_TURNS = 6
MAX_PROMPT_CHARS = 40000
MAX_HANDOFF_CHARS = 12000
MAX_CLAUDE_TURNS = 12
MAX_CONTEXT_FILES = 8
BLOCKED_PARTS = {".git", ".env", ".ssh", "node_modules", ".venv", "__pycache__", "secrets"}
_WINDOWS_DRIVE = re.compile(r"^[a-zA-Z]:")


def validate_context_files(paths: object) -> list[str]:
    """Accept a small list of repo-relative *path hints*, not file contents."""
    if not isinstance(paths, list) or len(paths) > MAX_CONTEXT_FILES:
        raise ValueError(f"context_files must be a list of at most {MAX_CONTEXT_FILES} paths")
    checked = []
    for path in paths:
        if not isinstance(path, str) or not path or len(path) > 240 or "\x00" in path:
            raise ValueError("context_files entries must be short nonempty paths")
        if "\\" in path or path.startswith("/") or _WINDOWS_DRIVE.match(path):
            raise ValueError("context_files paths must be relative POSIX paths")
        pure = PurePosixPath(path)
        if any(part in {"..", "."} or part.lower() in BLOCKED_PARTS or part.startswith(".env") for part in path.split("/")):
            raise ValueError("context_files may not traverse directories or point at secret/tool folders")
        if len(pure.parts) > 10 or not pure.parts or str(pure) != path:
            raise ValueError("context_files paths must be normalized relative references")
        if path not in checked:
            checked.append(path)
    return checked


def policy_for(row: dict) -> dict:
    policy = row.get("token_budget", {})
    if not isinstance(policy, dict):
        raise ValueError("token_budget must be a JSON object")
    settings = {
        "max_prompt_chars": (DEFAULT_PROMPT_CHARS, 512, MAX_PROMPT_CHARS),
        "max_handoff_chars": (DEFAULT_HANDOFF_CHARS, 0, MAX_HANDOFF_CHARS),
        "max_claude_turns": (DEFAULT_CLAUDE_TURNS, 1, MAX_CLAUDE_TURNS),
    }
    result = {}
    if set(policy) - set(settings):
        raise ValueError(f"unsupported token_budget keys: {sorted(set(policy) - set(settings))}")
    for key, (default, minimum, maximum) in settings.items():
        number = policy.get(key, default)
        if type(number) is not int or not minimum <= number <= maximum:
            raise ValueError(f"{key} must be an integer between {minimum} and {maximum}")
        result[key] = number
    validate_context_files(row.get("context_files", []))
    return result


def estimated_tokens(text: str) -> int:
    """Conservative-ish character heuristic only; not an actual tokenizer."""
    ascii_count = sum(ord(char) < 128 for char in text)
    non_ascii_count = len(text) - ascii_count
    return math.ceil(ascii_count / 3) + non_ascii_count


def budget_report(row: dict, prompt: str, handoff: str | None = None) -> dict:
    policy = policy_for(row)
    handoff = handoff or ""
    if len(handoff) > policy["max_handoff_chars"]:
        raise ValueError(f"handoff length {len(handoff)} exceeds stage max_handoff_chars {policy['max_handoff_chars']}; summarize and approve a smaller handoff")
    if len(prompt) > policy["max_prompt_chars"]:
        raise ValueError(f"prompt length {len(prompt)} exceeds stage max_prompt_chars {policy['max_prompt_chars']}; narrow context or explicitly increase the cap")
    return {
        "prompt_chars": len(prompt),
        "handoff_chars": len(handoff),
        "prompt_char_cap": policy["max_prompt_chars"],
        "handoff_char_cap": policy["max_handoff_chars"],
        "estimated_prompt_tokens": estimated_tokens(prompt),
        "estimate_method": "unicode_chars_plus_ascii_divided_by_3; not tokenizer or billable usage",
        "max_claude_turns": policy["max_claude_turns"],
        "context_files_count": len(validate_context_files(row.get("context_files", []))),
    }
