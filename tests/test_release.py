from pathlib import Path

import pytest
from pygit2 import Signature, init_repository
from pygit2.enums import ObjectType

from girokmoji.release import auto_release


def _setup_repo(tmp_path: Path):
    repo = init_repository(tmp_path)
    sig = Signature("t", "t@example.com")
    f = tmp_path / "f.txt"
    f.write_text("a")
    repo.index.add_all()
    commit = repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":tada: init",
        repo.index.write_tree(),
        [],
    )
    repo.create_tag("v0.1.0", commit, ObjectType.COMMIT, sig, "t1")
    return repo, sig, f, commit


def test_invalid_bump_raises(tmp_path: Path):
    _setup_repo(tmp_path)
    with pytest.raises(ValueError):
        auto_release("proj", repo_dir=tmp_path, bump="invalid")


def test_invalid_version_floor_scope(tmp_path: Path):
    _setup_repo(tmp_path)
    with pytest.raises(ValueError):
        auto_release("proj", repo_dir=tmp_path, version_floor_scope="bad")


def test_accepts_explicit_release_date(tmp_path: Path):
    repo, sig, f, commit = _setup_repo(tmp_path)
    f.write_text("b")
    repo.index.add_all()
    repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":bug: fix",
        repo.index.write_tree(),
        [commit],
    )
    note = auto_release(
        "proj",
        repo_dir=tmp_path,
        release_date="2000-01-01",
        bump="patch",
    )
    assert "2000-01-01" in note


def test_github_payload_branch(tmp_path: Path):
    repo, sig, f, commit = _setup_repo(tmp_path)
    f.write_text("b")
    repo.index.add_all()
    repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":bug: fix",
        repo.index.write_tree(),
        [commit],
    )
    payload = auto_release(
        "proj",
        repo_dir=tmp_path,
        bump="patch",
        github_payload=True,
    )
    assert '"tag_name": "v0.1.1"' in payload
