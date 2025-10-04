import pytest

from girokmoji import changelog, catgitmoji
from girokmoji.exception import NoGitmojiInMessageError
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


def test_support_template_markdown_not_implemented():
    with pytest.raises(NotImplementedError):
        _ = SupportTemplate().markdown
