from pathlib import Path

import pytest
from pygit2 import init_repository, Signature
from pygit2.enums import ObjectType

from girokmoji import changelog, catgitmoji
from girokmoji.exception import (
    NoGitmojiInMessageError,
    NoSuchTagFoundError,
    NotAncestorError,
)
from girokmoji.git import get_tag_to_tag_commits
from girokmoji.template import SupportTemplate


class FakeCommit:
    def __init__(self, message: str | None, commit_id: str = "deadbeef"):
        self.message: str | None = message
        _m = message or ""
        self.raw_message = _m.encode()
        self.message_encoding = "utf-8"
        self.id = commit_id


def test_get_category_fallback_and_error():
    msg = f"prefix {catgitmoji.RAW[0].code} something"
    assert (
        changelog.get_category(msg)
        == catgitmoji.by_code()[catgitmoji.RAW[0].code].category
    )
    with pytest.raises(NoGitmojiInMessageError):
        changelog.get_category("no gitmoji here")


def test_structured_changelog_hmm_category():
    commit = FakeCommit("no gitmoji here")
    res = changelog.structured_changelog([commit])
    assert commit in res["Hmm..."]


def test_get_tag_to_tag_commits_success_and_error(tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = Path(tmp_path) / "f.txt"
    f.write_text("a")
    repo.index.add_all()
    commit1 = repo.create_commit(
        "HEAD",
        person,
        person,
        ":tada: init",
        repo.index.write_tree(),
        [],
    )
    repo.create_tag("v1", commit1, ObjectType.COMMIT, person, "t1")
    f.write_text("b")
    repo.index.add_all()
    commit2 = repo.create_commit(
        "HEAD",
        person,
        person,
        ":art: change",
        repo.index.write_tree(),
        [commit1],
    )
    repo.create_tag("v2", commit2, ObjectType.COMMIT, person, "t2")
    commits = list(get_tag_to_tag_commits(tmp_path, "v1", "v2"))
    assert [c.id for c in commits] == [commit2]
    # Accept fully-qualified ref names as well
    commits_ref = list(
        get_tag_to_tag_commits(tmp_path, "refs/tags/v1", "refs/tags/v2")
    )
    assert [c.id for c in commits_ref] == [commit2]
    # Accept raw hex OIDs or names resolvable by revparse
    commits_oid = list(
        get_tag_to_tag_commits(tmp_path, str(commit1), str(commit2))
    )
    assert [c.id for c in commits_oid] == [commit2]
    with pytest.raises(NoSuchTagFoundError):
        list(get_tag_to_tag_commits(tmp_path, "v1", "v3"))
    with pytest.raises(NoSuchTagFoundError):
        list(get_tag_to_tag_commits(tmp_path, "v9", "v2"))


def test_range_mode_auto_linear_equals_direct(tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = Path(tmp_path) / "f.txt"
    f.write_text("a")
    repo.index.add_all()
    c1 = repo.create_commit(
        "HEAD",
        person,
        person,
        ":tada: init",
        repo.index.write_tree(),
        [],
    )
    repo.create_tag("v1", c1, ObjectType.COMMIT, person, "t1")
    f.write_text("b")
    repo.index.add_all()
    c2 = repo.create_commit(
        "HEAD",
        person,
        person,
        ":art: change",
        repo.index.write_tree(),
        [c1],
    )
    repo.create_tag("v2", c2, ObjectType.COMMIT, person, "t2")
    auto_commits = list(
        get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="auto")
    )
    direct_commits = list(
        get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="direct")
    )
    assert [c.id for c in auto_commits] == [c2]
    assert [c.id for c in auto_commits] == [c.id for c in direct_commits]


def test_range_mode_auto_diverged_uses_common_base(tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = Path(tmp_path) / "f.txt"
    f.write_text("base")
    repo.index.add_all()
    base = repo.create_commit(
        "HEAD",
        person,
        person,
        ":tada: base",
        repo.index.write_tree(),
        [],
    )
    # Branch A from base
    f.write_text("a1")
    repo.index.add_all()
    a1 = repo.create_commit(
        "refs/heads/a",
        person,
        person,
        ":sparkles: a1",
        repo.index.write_tree(),
        [base],
    )
    repo.create_tag("v1", a1, ObjectType.COMMIT, person, "a1")
    # Branch B from base
    f.write_text("b1")
    repo.index.add_all()
    b1 = repo.create_commit(
        "refs/heads/b",
        person,
        person,
        ":sparkles: b1",
        repo.index.write_tree(),
        [base],
    )
    repo.create_tag("v2", b1, ObjectType.COMMIT, person, "b1")
    commits = list(
        get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="auto")
    )
    assert [c.id for c in commits] == [b1]


def test_range_mode_auto_no_merge_base_head_only(tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = Path(tmp_path) / "f.txt"
    # Root 1
    f.write_text("r1")
    repo.index.add_all()
    r1 = repo.create_commit(
        "HEAD",
        person,
        person,
        ":tada: r1",
        repo.index.write_tree(),
        [],
    )
    repo.create_tag("v1", r1, ObjectType.COMMIT, person, "r1")
    # Orphan root 2 on another branch
    f.write_text("r2")
    repo.index.add_all()
    r2 = repo.create_commit(
        "refs/heads/other",
        person,
        person,
        ":sparkles: r2",
        repo.index.write_tree(),
        [],
    )
    repo.create_tag("v2", r2, ObjectType.COMMIT, person, "r2")
    commits = list(
        get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="auto")
    )
    assert [c.id for c in commits] == [r2]


def test_range_mode_strict_ancestor_raises_on_diverged(tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = Path(tmp_path) / "f.txt"
    f.write_text("base")
    repo.index.add_all()
    base = repo.create_commit(
        "HEAD",
        person,
        person,
        ":tada: base",
        repo.index.write_tree(),
        [],
    )
    f.write_text("a1")
    repo.index.add_all()
    a1 = repo.create_commit(
        "refs/heads/a",
        person,
        person,
        ":sparkles: a1",
        repo.index.write_tree(),
        [base],
    )
    repo.create_tag("v1", a1, ObjectType.COMMIT, person, "a1")
    f.write_text("b1")
    repo.index.add_all()
    b1 = repo.create_commit(
        "refs/heads/b",
        person,
        person,
        ":sparkles: b1",
        repo.index.write_tree(),
        [base],
    )
    repo.create_tag("v2", b1, ObjectType.COMMIT, person, "b1")
    with pytest.raises(NotAncestorError):
        list(
            get_tag_to_tag_commits(
                tmp_path, "v1", "v2", range_mode="auto", strict_ancestor=True
            )
        )


def test_support_template_markdown_not_implemented():
    with pytest.raises(NotImplementedError):
        _ = SupportTemplate().markdown
