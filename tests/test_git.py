from pathlib import Path

import pytest
from pygit2 import Signature, init_repository
from pygit2.enums import ObjectType, SortMode

from girokmoji.exception import NoSuchTagFoundError, NotAncestorError
from girokmoji.git import (
    _resolve_to_commit,
    get_tag_to_tag_commits,
    iter_semver_tags,
    last_reachable_semver_tag,
    global_max_semver_tag,
)
from girokmoji.semver import SemVer


def _make_initial(repo_dir: Path) -> tuple:
    repo = init_repository(repo_dir)
    person = Signature("t", "t@example.com")
    f = repo_dir / "f.txt"
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
    return repo, person, f, c1


def test_resolve_to_commit_variants(tmp_path):
    repo, person, f, c1 = _make_initial(tmp_path)
    # Additional commit tagged v2
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

    # Resolve by tag name
    assert _resolve_to_commit(repo, "v1").id == c1
    # Resolve by fully-qualified ref
    assert _resolve_to_commit(repo, "refs/tags/v2").id == c2
    # Resolve by hex OID
    assert _resolve_to_commit(repo, str(c1)).id == c1
    # Missing reference
    with pytest.raises(NoSuchTagFoundError):
        _resolve_to_commit(repo, "missing")


def test_resolve_to_commit_missing_ref_prefix(tmp_path):
    repo, *_ = _make_initial(tmp_path)
    with pytest.raises(NoSuchTagFoundError):
        _resolve_to_commit(repo, "refs/tags/missing")


def test_get_tag_to_tag_commits_success_and_error(tmp_path):
    repo, person, f, c1 = _make_initial(tmp_path)
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
    commits = list(get_tag_to_tag_commits(tmp_path, "v1", "v2"))
    assert [c.id for c in commits] == [c2]
    # Accept fully-qualified ref names as well
    commits_ref = list(get_tag_to_tag_commits(tmp_path, "refs/tags/v1", "refs/tags/v2"))
    assert [c.id for c in commits_ref] == [c2]
    # Accept raw hex OIDs or names resolvable by revparse
    commits_oid = list(get_tag_to_tag_commits(tmp_path, str(c1), str(c2)))
    assert [c.id for c in commits_oid] == [c2]
    with pytest.raises(NoSuchTagFoundError):
        list(get_tag_to_tag_commits(tmp_path, "v1", "v3"))
    with pytest.raises(NoSuchTagFoundError):
        list(get_tag_to_tag_commits(tmp_path, "v9", "v2"))


def test_range_mode_auto_linear_equals_direct(tmp_path):
    repo, person, f, c1 = _make_initial(tmp_path)
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
    auto_commits = list(get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="auto"))
    direct_commits = list(
        get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="direct")
    )
    assert [c.id for c in auto_commits] == [c2]
    assert [c.id for c in auto_commits] == [c.id for c in direct_commits]


def test_range_mode_auto_linear_verbose(capsys, tmp_path):
    repo, person, f, c1 = _make_initial(tmp_path)
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
    list(
        get_tag_to_tag_commits(
            tmp_path,
            "v1",
            "v2",
            range_mode="auto",
            verbose=True,
        )
    )
    captured = capsys.readouterr()
    assert "auto: using direct (linear history)" in captured.err


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
    commits = list(get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="auto"))
    assert [c.id for c in commits] == [b1]


def test_range_mode_auto_diverged_messages(capsys, tmp_path):
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
    list(
        get_tag_to_tag_commits(
            tmp_path,
            "v1",
            "v2",
            range_mode="auto",
            verbose=True,
        )
    )
    captured = capsys.readouterr()
    assert "auto: using common-base (merge-base" in captured.err
    capsys.readouterr()
    list(get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="auto"))
    captured = capsys.readouterr()
    assert captured.err.strip() == "[girokmoji] auto: using common-base"


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
    commits = list(get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="auto"))
    assert [c.id for c in commits] == [r2]


def test_range_mode_auto_no_merge_base_verbose_and_quiet(capsys, tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = Path(tmp_path) / "f.txt"
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
    list(
        get_tag_to_tag_commits(
            tmp_path,
            "v1",
            "v2",
            range_mode="auto",
            verbose=True,
        )
    )
    captured = capsys.readouterr()
    assert "no merge-base; falling back to head-only" in captured.err
    capsys.readouterr()
    list(
        get_tag_to_tag_commits(
            tmp_path,
            "v1",
            "v2",
            range_mode="auto",
            verbose=True,
            quiet=True,
        )
    )
    captured = capsys.readouterr()
    assert captured.err == ""


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


def test_range_mode_direct_strict_ancestor_raises(tmp_path):
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
                tmp_path, "v1", "v2", range_mode="direct", strict_ancestor=True
            )
        )


def test_common_base_no_merge_base_falls_back(capsys, tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = Path(tmp_path) / "f.txt"
    # Create two unrelated roots
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
        get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="common-base")
    )
    captured = capsys.readouterr()
    assert "common-base requested but no merge-base" in captured.err
    assert [c.id for c in commits] == [r2]


def test_common_base_quiet_suppresses_message(capsys, tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = Path(tmp_path) / "f.txt"
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
    list(
        get_tag_to_tag_commits(
            tmp_path,
            "v1",
            "v2",
            range_mode="common-base",
            quiet=True,
        )
    )
    captured = capsys.readouterr()
    assert captured.err == ""


def test_unknown_mode_defaults_to_direct(tmp_path):
    repo, person, f, c1 = _make_initial(tmp_path)
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
    unknown_commits = list(
        get_tag_to_tag_commits(tmp_path, "v1", "v2", range_mode="unknown")
    )
    assert [c.id for c in unknown_commits] == [c2]


def test_custom_sorting_argument(tmp_path):
    repo, person, f, c1 = _make_initial(tmp_path)
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
    commits = list(
        get_tag_to_tag_commits(
            tmp_path,
            "v1",
            "v2",
            range_mode="direct",
            sorting=int(SortMode.TIME),
        )
    )
    assert [c.id for c in commits] == [c2]


def test_iter_semver_tags_handles_uppercase_and_invalid(tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = tmp_path / "f.txt"
    f.write_text("base")
    repo.index.add_all()
    base = repo.create_commit(
        "HEAD", person, person, ":tada: base", repo.index.write_tree(), []
    )
    repo.create_tag("v1.0.0", base, ObjectType.COMMIT, person, "v1")
    repo.create_tag("V2.0.0", base, ObjectType.COMMIT, person, "v2")
    repo.create_tag("not-semver", base, ObjectType.COMMIT, person, "bad")
    tags = list(iter_semver_tags(repo))
    names = [name for name, _, _ in tags]
    assert "v1.0.0" in names
    assert "V2.0.0" in names
    assert "not-semver" not in names
    versions = {name: ver for name, ver, _ in tags}
    assert versions["V2.0.0"] == SemVer.parse("2.0.0")


def test_last_reachable_semver_tag_skips_unreachable(tmp_path):
    repo = init_repository(tmp_path)
    person = Signature("t", "t@example.com")
    f = tmp_path / "f.txt"
    f.write_text("base")
    repo.index.add_all()
    base = repo.create_commit(
        "HEAD", person, person, ":tada: base", repo.index.write_tree(), []
    )
    repo.create_tag("v1.0.0", base, ObjectType.COMMIT, person, "v1")
    f.write_text("other")
    repo.index.add_all()
    other = repo.create_commit(
        "refs/heads/other",
        person,
        person,
        ":sparkles: other",
        repo.index.write_tree(),
        [base],
    )
    repo.create_tag("v2.0.0", other, ObjectType.COMMIT, person, "v2")
    head = repo[repo.head.target].peel(ObjectType.COMMIT)
    assert last_reachable_semver_tag(repo, head) == (
        "v1.0.0",
        SemVer.parse("1.0.0"),
    )


def test_global_max_semver_tag_returns_highest(tmp_path):
    repo, person, f, c1 = _make_initial(tmp_path)
    repo.create_tag("V2.0.0", c1, ObjectType.COMMIT, person, "v2")
    assert global_max_semver_tag(repo) == (
        "V2.0.0",
        SemVer.parse("2.0.0"),
    )
