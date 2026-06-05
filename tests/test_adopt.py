from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from girokmoji.native.git2 import (
    ObjectType,
    Repository,
    Signature,
    discover_repository,
    init_repository,
)

from girokmoji.adopt import AdoptError, AdoptOptions, run_adopt


def _seed_repository(path: Path) -> None:
    repo = init_repository(path)
    sig = Signature("tester", "tester@example.com")
    tracked = path / "CHANGELOG.md"
    tracked.write_text("alpha")
    repo.index.add_all()
    repo.index.write()
    first_tree = repo.index.write_tree()
    first_commit = repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":tada: init",
        first_tree,
        [],
    )
    repo.create_tag("v0.1.0", first_commit, ObjectType.COMMIT, sig, "init")
    tracked.write_text("beta")
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


@pytest.mark.cli
def test_cli_adopt_dry_run_json(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _seed_repository(repo_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "girokmoji",
            "adopt",
            str(repo_dir),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["repo_url"] == str(repo_dir)
    assert payload["previous_tag"] == "v0.1.0"
    assert payload["dry_run"] is True
    assert payload["tag_created"] is False
    assert payload["pushed"] is False
    assert payload["next_steps"], "expected next steps in payload"
    git_dir = discover_repository(str(repo_dir))
    assert git_dir is not None
    repo = Repository(git_dir)
    with pytest.raises(KeyError):
        repo.lookup_reference(f"refs/tags/{payload['new_tag']}")


@pytest.mark.cli
def test_cli_adopt_dirty_workdir_fails(tmp_path: Path) -> None:
    repo_dir = tmp_path / "dirty"
    repo_dir.mkdir()
    _seed_repository(repo_dir)
    (repo_dir / "untracked.txt").write_text("wip")

    result = subprocess.run(
        [sys.executable, "-m", "girokmoji", "adopt", str(repo_dir)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 15
    assert "DIRTY_WORKDIR" in result.stderr


@pytest.mark.cli
def test_cli_adopt_invalid_ref(tmp_path: Path) -> None:
    repo_dir = tmp_path / "badref"
    repo_dir.mkdir()
    _seed_repository(repo_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "girokmoji",
            "adopt",
            str(repo_dir),
            "--ref",
            "missing-branch",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 12
    assert "CHECKOUT_FAILED" in result.stderr


def test_run_adopt_handles_release_failure(monkeypatch, tmp_path: Path) -> None:
    repo_dir = tmp_path / "unit"
    repo_dir.mkdir()
    _seed_repository(repo_dir)

    def _boom(*args, **kwargs):  # noqa: ANN001 - signature mirrors auto_release
        raise RuntimeError("boom")

    monkeypatch.setattr("girokmoji.adopt.auto_release", _boom)

    options = AdoptOptions(
        repo=str(repo_dir),
        project_name="demo",
        bump="patch",
        ref=None,
        range_mode="auto",
        strict_ancestor=False,
        quiet=False,
        verbose=False,
        dry_run=True,
        workdir=None,
        keep_workdir=False,
        push_remote="origin",
        depth=0,
        changelog_out=None,
    )

    with pytest.raises(AdoptError) as excinfo:
        run_adopt(options)

    assert excinfo.value.code == "RELEASE_FAILED"


def test_run_adopt_keeps_temp_clone_when_requested(tmp_path: Path) -> None:
    repo_dir = tmp_path / "origin"
    repo_dir.mkdir()
    _seed_repository(repo_dir)

    options = AdoptOptions(
        repo=repo_dir.as_uri(),
        project_name="demo",
        bump="patch",
        ref=None,
        range_mode="auto",
        strict_ancestor=False,
        quiet=False,
        verbose=False,
        dry_run=True,
        workdir=None,
        keep_workdir=True,
        push_remote="origin",
        depth=0,
        changelog_out=None,
    )

    result = run_adopt(options)

    try:
        assert result.workdir.exists()
        assert result.workdir_persisted is True
    finally:
        shutil.rmtree(result.workdir, ignore_errors=True)


def test_run_adopt_cleans_temp_clone_after_release_failure(
    monkeypatch, tmp_path: Path
) -> None:
    repo_dir = tmp_path / "origin"
    repo_dir.mkdir()
    _seed_repository(repo_dir)
    cloned_workdirs: list[Path] = []

    def _boom(*args, **kwargs):  # noqa: ANN001 - signature mirrors auto_release
        cloned_workdirs.append(kwargs["repo_dir"])
        raise RuntimeError("boom")

    monkeypatch.setattr("girokmoji.adopt.auto_release", _boom)

    options = AdoptOptions(
        repo=repo_dir.as_uri(),
        project_name="demo",
        bump="patch",
        ref=None,
        range_mode="auto",
        strict_ancestor=False,
        quiet=False,
        verbose=False,
        dry_run=True,
        workdir=None,
        keep_workdir=False,
        push_remote="origin",
        depth=0,
        changelog_out=None,
    )

    with pytest.raises(AdoptError) as excinfo:
        run_adopt(options)

    assert excinfo.value.code == "RELEASE_FAILED"
    assert cloned_workdirs
    assert not cloned_workdirs[0].exists()
