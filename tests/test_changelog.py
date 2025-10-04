import json
from pathlib import Path

import pytest

from girokmoji import catgitmoji
from girokmoji import changelog


class FakeCommit:
    def __init__(self, message: str | None, commit_id: str = "deadbeef"):
        self.message: str | None = message
        _m = message or ""
        self.raw_message = _m.encode()
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


def test_get_category_no_fallback():
    msg = "Text with :bug: inside"
    with pytest.raises(changelog.NoGitmojiInMessageError):
        changelog.get_category(msg, fallback_to_includes=False)
    assert (
        changelog.get_category(msg, fallback_to_includes=True)
        == catgitmoji.by_code()[":bug:"].category
    )


def test_gen_markdown_skips_unknown_and_gitmojiless():
    commits = [
        FakeCommit(":sparkles: ok", "c1"),
        FakeCommit(":nonexistent: nope", "c2"),
        FakeCommit("just text", "c3"),
    ]
    structured = changelog.structured_changelog(commits)
    md = changelog.gen_markdown("proj", "v1", "2024-01-01", structured)
    assert "ok" in md
    assert "nope" not in md
    assert "just text" not in md


def test_change_log_non_default_options(monkeypatch):
    commits = [FakeCommit(":bug: fix1")]
    captured: dict[str, object] = {}

    def fake_get_tag_to_tag_commits(repo_dir, tail_tag, head_tag, **kwargs):
        captured.update(kwargs)
        return commits

    monkeypatch.setattr(
        changelog, "get_tag_to_tag_commits", fake_get_tag_to_tag_commits
    )

    changelog.change_log(
        "proj",
        "2024-01-01",
        Path("."),
        "v0",
        "v1",
        range_mode="direct",
        strict_ancestor=True,
        quiet=True,
        verbose=True,
        sorting=1,
    )
    assert captured == {
        "range_mode": "direct",
        "strict_ancestor": True,
        "quiet": True,
        "verbose": True,
        "sorting": 1,
    }


def test_github_release_payload_flags(monkeypatch):
    monkeypatch.setattr(changelog, "change_log", lambda **kwargs: "log")
    payload = json.loads(
        changelog.github_release_payload(
            "proj",
            "2024-01-01",
            Path("."),
            "v0",
            "v1",
            draft=True,
            prerelease=True,
        )
    )
    assert payload["draft"] is True
    assert payload["prerelease"] is True
