from girokmoji import template


def test_templates():
    head = template.HEAD(
        project_name="p",
        version="1",
        subtext="s",
        release_date="today",
    )
    assert "p" in head.markdown
    section = template.CATEGORY_SECTION("Bug Fixes", "sub")
    assert "Bug Fixes" in section.markdown
    entry = template.ENTRY(
        emoji="🐛",
        gitmoji_description="bug",
        commit_description="fix",
        commit_hash="abc",
    )
    assert "abc" in entry.markdown
    header = template.ENTRY_GROUP_HEADER(
        emoji="🐛",
        gitmoji_description="bug",
    )
    assert "bug" in header.markdown
    sub = template.ENTRY_SUBITEM(commit_description="fix", commit_hash="abc")
    assert "fix" in sub.markdown
    sep = template.SEPARATOR()
    assert "---" in sep.markdown
