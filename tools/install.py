#!/usr/bin/env python3
"""Install the portable model-router skill into a target local project's agent skill folders."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "model-router"
MARK_BEGIN = "<!-- model-router:plan-instructions:start -->"
MARK_END = "<!-- model-router:plan-instructions:end -->"
INSTRUCTION = (
    f"{MARK_BEGIN}\n"
    "Before producing or revising a software implementation plan or Plan Mode output, "
    "load and apply the project `model-router` skill. Include its Model allocation / 模型分配 "
    "section with primary and backup models per stage, explicit availability status, "
    "verification date and re-routing criteria. This is recommendation-only unless a "
    "separately authorized orchestrator performs the switch.\n"
    "中文：制定开发计划前，请加载 model-router Skill；推荐不代表执行授权。\n"
    f"{MARK_END}\n"
)


def append_instruction(file: Path) -> str:
    if file.is_dir():
        raise ValueError(f"expected a file: {file}")
    if file.exists():
        original = file.read_text(encoding="utf-8")
        if MARK_BEGIN in original:
            if MARK_END not in original:
                raise ValueError(f"unbalanced model-router markers in {file}")
            return "already configured"
        file.write_text(original.rstrip() + "\n\n" + INSTRUCTION, encoding="utf-8")
    else:
        file.write_text(INSTRUCTION, encoding="utf-8")
    return "configured"


def install(target: Path, agents: list[str], force: bool, include_instructions: bool) -> list[str]:
    if not target.is_dir():
        raise ValueError(f"target directory does not exist: {target}")
    # Preflight every target before writing to avoid partially installing to one agent.
    for agent in agents:
        dest = target / (".claude/skills/model-router" if agent == "claude" else ".agents/skills/model-router")
        if dest.exists() and (not dest.is_dir() or not force):
            raise ValueError(f"refusing to overwrite existing skill: {dest}; pass --force to replace")
        if include_instructions:
            instruction_file = target / ("CLAUDE.md" if agent == "claude" else "AGENTS.md")
            if instruction_file.exists():
                if instruction_file.is_dir():
                    raise ValueError(f"expected file: {instruction_file}")
                existing = instruction_file.read_text(encoding="utf-8")
                if MARK_BEGIN in existing and MARK_END not in existing:
                    raise ValueError(f"unbalanced model-router markers: {instruction_file}")
    messages = []
    for agent in agents:
        dest = target / (".claude/skills/model-router" if agent == "claude" else ".agents/skills/model-router")
        if dest.exists():
            if not dest.is_dir():
                raise ValueError(f"destination is not a directory: {dest}")
            if not force:
                raise ValueError(f"refusing to overwrite existing skill: {dest}; pass --force to replace")
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SOURCE, dest)
        messages.append(f"installed: {dest}")
        if include_instructions:
            instructions = target / ("CLAUDE.md" if agent == "claude" else "AGENTS.md")
            messages.append(f"{instructions}: {append_instruction(instructions)}")
    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path, help="existing project directory")
    parser.add_argument("--agents", choices=["both", "claude", "codex"], default="both")
    parser.add_argument("--force", action="store_true", help="replace existing model-router skill folder")
    parser.add_argument("--no-plan-instructions", action="store_true", help="leave AGENTS.md / CLAUDE.md unchanged")
    args = parser.parse_args()
    agents = ["claude", "codex"] if args.agents == "both" else [args.agents]
    try:
        for line in install(args.target.resolve(), agents, args.force, not args.no_plan_instructions):
            print(line)
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
