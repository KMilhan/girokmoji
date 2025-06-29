from pathlib import Path

import pytest
from pygit2 import init_repository, Signature
from pygit2.enums import ObjectType

from girokmoji.semver import SemVer
from girokmoji.release import auto_release


def test_parse_and_str():
    v = SemVer.parse("1.2.3-alpha.1+5")
    assert v.major == 1
    assert str(v) == "1.2.3-alpha.1+5"

    with pytest.raises(ValueError):
        SemVer.parse("1.2")


def test_precedence_examples():
    order = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
    ]
    versions = [SemVer.parse(v) for v in order]
    assert versions == sorted(versions)


def test_bump_logic():
    v = SemVer.parse("0.1.2")
    assert str(v.bump("patch")) == "0.1.3"
    assert str(v.bump("minor")) == "0.2.0"
    assert str(v.bump("major")) == "1.0.0"


def test_auto_release_with_semver(tmp_path: Path):
    repo = init_repository(tmp_path)
    sig = Signature("t", "t@example.com")
    f = tmp_path / "f.txt"
    f.write_text("a")
    repo.index.add_all()
    commit1 = repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":tada: init",
        repo.index.write_tree(),
        [],
    )
    repo.create_tag("v1.0.0", commit1, ObjectType.COMMIT, sig, "t1")
    f.write_text("b")
    repo.index.add_all()
    commit2 = repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":bug: fix",
        repo.index.write_tree(),
        [commit1],
    )
    note = auto_release("proj", repo_dir=tmp_path, bump="patch")
    tags = [r for r in repo.references if r.startswith("refs/tags/")]
    assert "refs/tags/v1.0.1" in tags
    assert "proj" in note


def test_auto_release_without_user_config(tmp_path: Path):
    repo = init_repository(tmp_path)
    sig = Signature("t", "t@example.com")
    f = tmp_path / "f.txt"
    f.write_text("a")
    repo.index.add_all()
    commit1 = repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":tada: init",
        repo.index.write_tree(),
        [],
    )
    repo.create_tag("v1.0.0", commit1, ObjectType.COMMIT, sig, "t1")
    f.write_text("b")
    repo.index.add_all()
    repo.create_commit(
        "HEAD",
        sig,
        sig,
        ":sparkles: update",
        repo.index.write_tree(),
        [commit1],
    )
    try:
        repo.config.delete_multivar("user.name", ".*")
    except KeyError:
        pass
    try:
        repo.config.delete_multivar("user.email", ".*")
    except KeyError:
        pass
    note = auto_release("proj", repo_dir=tmp_path, bump="patch")
    tags = [r for r in repo.references if r.startswith("refs/tags/")]
    assert "refs/tags/v1.0.1" in tags
    assert "proj" in note

