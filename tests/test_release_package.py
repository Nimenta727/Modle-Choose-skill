"""Offline tests for portable, reproducible release packages."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from tools import package_release

ROOT = Path(__file__).resolve().parents[1]


class ReleasePackageTests(unittest.TestCase):
    def test_version_metadata(self):
        metadata = package_release.release_info()
        self.assertEqual(metadata["tag"], "v" + metadata["version"])
        self.assertEqual(metadata["channel"], "prerelease")
        self.assertFalse(metadata["live_clients_verified"])

    def test_archive_contains_only_standalone_skill(self):
        source = package_release.collect_sources()
        self.assertGreaterEqual(len(source), 9)
        self.assertTrue(all(path.startswith("model-router/") for path, _ in source))
        self.assertTrue(any(path == "model-router/SKILL.md" for path, _ in source))
        self.assertEqual(dict(source)["model-router/LICENSE"], (ROOT / "LICENSE").read_bytes())
        self.assertFalse(any("orchestrator" in path or "/evals/" in path for path, _ in source))

    def test_deterministic_archive_and_checksum(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            first = package_release.build(a)
            second = package_release.build(b)
            archive = Path(first["archive"])
            self.assertEqual(archive.read_bytes(), Path(second["archive"]).read_bytes())
            self.assertEqual(first["sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertTrue(Path(first["checksum"]).read_text().startswith(first["sha256"]))
            self.assertTrue(package_release.verify(archive)["verified"])
            with ZipFile(archive) as zf:
                self.assertIn("model-router/RELEASE.json", zf.namelist())
                self.assertIn("model-router/SKILL.md", zf.namelist())
                self.assertEqual(zf.read("model-router/LICENSE"), (ROOT / "LICENSE").read_bytes())

    def test_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            package_release.build(Path(td))
            with self.assertRaises(ValueError):
                package_release.build(Path(td))

    def test_hidden_files_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "skills/model-router"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("# skill\n")
            (source / ".env").write_text("PRIVATE\n")
            with self.assertRaises(ValueError):
                package_release.collect_sources(root)


if __name__ == "__main__":
    unittest.main()
