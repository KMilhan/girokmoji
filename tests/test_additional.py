from pathlib import Path

import pytest
from pygit2 import init_repository, Signature
from pygit2.enums import ObjectType

from girokmoji import changelog, catgitmoji
from girokmoji.exception import NoGitmojiInMessageError, NoSuchTagFoundError
from girokmoji.git import get_tag_to_tag_commits
from girokmoji.template import SupportTemplate


class FakeCommit:
    def __init__(self, message: str, commit_id: str = "deadbeef"):
        self.message = message
        self.raw_message = message.encode()
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
    with pytest.raises(NoSuchTagFoundError):
        list(get_tag_to_tag_commits(tmp_path, "v1", "v3"))
    with pytest.raises(NoSuchTagFoundError):
        list(get_tag_to_tag_commits(tmp_path, "v9", "v2"))


def test_support_template_markdown_not_implemented():
    with pytest.raises(NotImplementedError):
        _ = SupportTemplate().markdown
