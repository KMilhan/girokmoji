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


def _setup_unreachable_tag_repo(tmp_path: Path):
    repo, sig, f, commit = _setup_repo(tmp_path)
    f.write_text("b")
    repo.index.add_all()
    other_commit = repo.create_commit(
        "refs/heads/other",
        sig,
        sig,
        ":sparkles: other",
        repo.index.write_tree(),
        [commit],
    )
    repo.create_tag("v0.1.1", other_commit, ObjectType.COMMIT, sig, "t2")
    f.write_text("c")
    repo.index.add_all()
    head_commit = repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":bug: fix",
        repo.index.write_tree(),
        [commit],
    )
    return repo, sig, f, commit, other_commit, head_commit


def test_on_tag_exists_skip(tmp_path: Path):
    repo, sig, f, commit, other_commit, head_commit = _setup_unreachable_tag_repo(
        tmp_path
    )
    auto_release(
        "proj",
        repo_dir=tmp_path,
        bump="patch",
        on_tag_exists="skip",
        version_floor_scope="reachable",
    )
    ref = repo.lookup_reference("refs/tags/v0.1.1")
    assert repo[ref.target].peel(ObjectType.COMMIT).id == other_commit


def test_on_tag_exists_overwrite(tmp_path: Path):
    repo, sig, f, commit, other_commit, head_commit = _setup_unreachable_tag_repo(
        tmp_path
    )
    auto_release(
        "proj",
        repo_dir=tmp_path,
        bump="patch",
        on_tag_exists="overwrite",
        version_floor_scope="reachable",
    )
    ref = repo.lookup_reference("refs/tags/v0.1.1")
    assert repo[ref.target].peel(ObjectType.COMMIT).id == head_commit


def test_auto_release_uses_global_max(tmp_path: Path):
    repo, sig, f, commit = _setup_repo(tmp_path)
    f.write_text("b")
    repo.index.add_all()
    other_commit = repo.create_commit(
        "refs/heads/other",
        sig,
        sig,
        ":sparkles: other",
        repo.index.write_tree(),
        [commit],
    )
    repo.create_tag("v0.2.0", other_commit, ObjectType.COMMIT, sig, "t2")
    f.write_text("c")
    repo.index.add_all()
    repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":bug: fix",
        repo.index.write_tree(),
        [commit],
    )
    note = auto_release("proj", repo_dir=tmp_path, bump="patch")
    assert "v0.2.1" in note
