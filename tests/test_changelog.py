import json
from pathlib import Path

import pytest

from girokmoji import catgitmoji
from girokmoji import changelog


class FakeCommit:
    def __init__(self, message: str, commit_id: str = "deadbeef"):
        self.message = message
        self.raw_message = message.encode()
        self.message_encoding = "utf-8"
        self.id = commit_id


def test_commit_message_str_bytes():
    commit = FakeCommit(":sparkles: feat")
    assert changelog.commit_message(commit) == ":sparkles: feat"
    commit.raw_message = b":bug: fix"
    commit.message = None
    assert changelog.commit_message(commit) == ":bug: fix"


def test_get_category_and_sep_title():
    msg = ":art: refactor"
    assert changelog.get_category(msg) == catgitmoji.by_code()[":art:"].category
    emoji, title = changelog.sep_gitmoji_msg_title(msg, strict=True)
    assert emoji == ":art:"
    assert title == "refactor"
    assert changelog.sep_gitmoji_msg_title("no gitmoji", strict=False) == (
        "",
        "no gitmoji",
    )
    with pytest.raises(changelog.MessageDoesNotStartWithGitmojiError):
        changelog.sep_gitmoji_msg_title("no gitmoji", strict=True)


def test_structured_and_markdown(monkeypatch):
    commits = [FakeCommit(":sparkles: first"), FakeCommit(":sparkles: second")]
    structured = changelog.structured_changelog(commits)
    assert structured[catgitmoji.by_code()[":sparkles:"].category][0] is commits[0]

    def fake_get_tag_to_tag_commits(repo_dir, tail_tag, head_tag):
        return commits

    monkeypatch.setattr(
        changelog, "get_tag_to_tag_commits", fake_get_tag_to_tag_commits
    )

    md = changelog.change_log("proj", "2024-01-01", Path("."), "v0", "v1")
    assert md.count("Introduce new features.") == 1
    assert "first" in md and "second" in md
    payload = json.loads(
        changelog.github_release_payload("proj", "2024-01-01", Path("."), "v0", "v1")
    )
    assert payload["tag_name"] == "v1"
