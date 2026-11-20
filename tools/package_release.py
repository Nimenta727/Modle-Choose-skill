#!/usr/bin/env python3
"""Build and verify a deterministic, standalone Model Router Skill ZIP.

No network calls, third-party dependencies or model requests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, BadZipFile

ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIME = (2020, 1, 1, 0, 0, 0)
REQUIRED = {
    "SKILL.md", "references/model-registry.json",
    "references/routing-policy.md", "references/plan-template.md",
    "references/providers.md", "scripts/route.py",
    "scripts/update_models.py", "scripts/check_availability.py",
    "scripts/handoff.py",
}
ALLOWED_SUFFIXES = {".md", ".json", ".py"}


def release_info(root: Path = ROOT) -> dict:
    data = json.loads((root / "release/version.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("skill") != "model-router":
        raise ValueError("invalid release metadata")
    version, tag = data.get("version"), data.get("tag")
    if not isinstance(version, str) or not version or tag != "v" + version:
        raise ValueError("release version/tag mismatch")
    if data.get("channel") not in ("prerelease", "stable"):
        raise ValueError("release channel must be prerelease or stable")
    return data


def collect_sources(root: Path = ROOT) -> list[tuple[str, bytes]]:
    source = root / "skills/model-router"
    if not source.is_dir() or source.is_symlink():
        raise ValueError("missing or symlinked portable Skill root")
    files = []
    seen = set()
    for path in sorted(source.rglob("*")):
        if "__pycache__" in path.relative_to(source).parts or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_symlink():
            raise ValueError(f"symlinks are excluded from releases: {path}")
        if path.is_dir():
            continue
        relative = path.relative_to(source).as_posix()
        if (any(part.startswith(".") for part in path.relative_to(source).parts)
                or "__pycache__" in path.parts or path.suffix not in ALLOWED_SUFFIXES):
            raise ValueError(f"unsupported file in portable Skill: {relative}")
        if path.stat().st_size > 1_000_000:
            raise ValueError(f"file exceeds 1 MB release limit: {relative}")
        if relative in seen:
            raise ValueError("duplicate skill path")
        seen.add(relative)
        files.append((f"model-router/{relative}", path.read_bytes()))
    missing = REQUIRED - seen
    if missing:
        raise ValueError(f"portable Skill is incomplete: {sorted(missing)}")
    return files


def _entry(name: str, content: bytes, archive: ZipFile) -> None:
    info = ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content, compress_type=ZIP_DEFLATED, compresslevel=9)


def verify(archive_path: Path, root: Path = ROOT) -> dict:
    metadata = release_info(root)
    expected = dict(collect_sources(root))
    expected["model-router/RELEASE.json"] = (
        json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    with ZipFile(archive_path) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("archive differs from the canonical portable Skill")
        for name in names:
            if name.startswith("/") or ".." in Path(name).parts or zf.read(name) != expected[name]:
                raise ValueError(f"archive file differs from source: {name}")
    return {"verified": True, "version": metadata["version"], "files": len(names)}


def build(output_dir: Path, root: Path = ROOT) -> dict:
    metadata = release_info(root)
    entries = collect_sources(root)
    output_dir = output_dir.expanduser().resolve()
    source_root = (root / "skills/model-router").resolve()
    if output_dir == source_root or source_root in output_dir.parents:
        raise ValueError("release output must be outside the portable Skill")
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"model-router-skill-v{metadata['version']}.zip"
    archive_path = output_dir / archive_name
    checksum_path = output_dir / (archive_name + ".sha256")
    if archive_path.exists() or checksum_path.exists():
        raise ValueError("release output already exists; use a clean directory")
    manifest_bytes = (json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    try:
        with ZipFile(archive_path, "x") as zf:
            for name, content in entries:
                _entry(name, content, zf)
            _entry("model-router/RELEASE.json", manifest_bytes, zf)
        verify(archive_path, root)
        digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        checksum_path.write_text(f"{digest}  {archive_name}\n", encoding="utf-8")
    except Exception:
        archive_path.unlink(missing_ok=True)
        checksum_path.unlink(missing_ok=True)
        raise
    return {"version": metadata["version"], "archive": str(archive_path),
            "checksum": str(checksum_path), "sha256": digest, "source_files": len(entries)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    try:
        if (args.output_dir is None) == (args.verify is None):
            parser.error("choose exactly one of --output-dir or --verify")
        result = verify(args.verify) if args.verify else build(args.output_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, BadZipFile, json.JSONDecodeError) as exc:
        print(f"release package error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
