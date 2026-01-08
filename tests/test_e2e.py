from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from girokmoji.native.git2 import ObjectType, Repository, Signature, init_repository


def _seed_repo(path: Path) -> None:
    repo = init_repository(path)
    sig = Signature("tester", "tester@example.com")
    changelog = path / "CHANGELOG.md"
    changelog.write_text("alpha")
    repo.index.add_all()
    repo.index.write()
    first_commit = repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":tada: init",
        repo.index.write_tree(),
        [],
    )
    repo.create_tag("v0.1.0", first_commit, ObjectType.COMMIT, sig, "init")
    changelog.write_text("beta")
    repo.index.add_all()
    repo.index.write()
    repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":sparkles: change",
        repo.index.write_tree(),
        [first_commit],
    )


@pytest.mark.e2e
def test_release_cli_end_to_end(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _seed_repo(repo_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "girokmoji",
            "release",
            "demo",
            "--repo-dir",
            str(repo_dir),
            "--bump",
            "patch",
            "--release-date",
            "2024-01-01",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Release Changelog v0.1.1" in result.stdout
    assert "**Release Date:** 2024-01-01" in result.stdout

    repo = Repository(str(repo_dir))
    repo.lookup_reference("refs/tags/v0.1.1")
