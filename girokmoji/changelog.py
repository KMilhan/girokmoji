import json
from pathlib import Path
from typing import Iterable

from pygit2 import Commit

from girokmoji.catgitmoji import by_gitmoji, any_to_catmoji
from girokmoji.const import CATEGORY, category_order, CATEGORY_SUBTEXTS
from girokmoji.exception import (
    NoGitmojiInMessageError,
    MessageDoesNotStartWithGitmojiError,
    NoSuchGitmojiSupportedError,
)
from girokmoji.git import get_tag_to_tag_commits
from girokmoji.template import ENTRY_GROUP_HEADER, ENTRY_SUBITEM
from girokmoji.template import SEPARATOR, HEAD, CATEGORY_SECTION


def commit_message(commit: Commit) -> str:
    if isinstance(commit.message, str):
        return commit.message

    return commit.raw_message.decode(commit.message_encoding)


def get_category(msg: str, *, fallback_to_includes: bool = True) -> CATEGORY:
    for gitmoji in by_gitmoji():
        if msg.startswith(gitmoji):
            return by_gitmoji()[gitmoji].category
    if fallback_to_includes:
        for gitmoji in by_gitmoji():
            if gitmoji in msg:
                return by_gitmoji()[gitmoji].category
    raise NoGitmojiInMessageError("No Gitmoji found in the message")


def sep_gitmoji_msg_title(msg: str, *, strict: bool = False) -> tuple[str, str]:
    """Return gitmoji and message from commit message. Strict mode raises exception MessageDoesNotStartWithGitmojiError"""
    msg = msg.split("\n")[0]
    for gitmoji in by_gitmoji().keys():
        if msg.startswith(gitmoji):
            return gitmoji, msg.removeprefix(gitmoji).strip()

    if not strict:
        return "", msg.split("\n")[0]

    raise MessageDoesNotStartWithGitmojiError


def structured_changelog(commits: Iterable[Commit]) -> dict[CATEGORY, list[Commit]]:
    # prepare structured changelog with importance order
    structured_changelog: dict[CATEGORY, list[Commit]] = {}
    for cat in category_order:
        structured_changelog[cat] = []

    for commit in commits:
        msg = commit_message(commit)
        try:
            cat: CATEGORY = get_category(msg)
        except NoGitmojiInMessageError:
            cat = "Hmm..."
        structured_changelog[cat].append(commit)

    return structured_changelog


def gen_markdown(
    project_name: str,
    version: str,
    release_date: str,
    change: dict[CATEGORY, list[Commit]],
):
    changelog_markdown = ""

    separator = SEPARATOR().markdown
    head_md = HEAD(
        project_name=project_name,
        version=version,
        subtext="""
_"Change is always thrilling!"_  
_(And sometimes a little confusing.)_
    """,
        release_date=release_date,
    ).markdown

    changelog_markdown += head_md
    changelog_markdown += separator

    for cat in change:
        category_md = ""
        subcats: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for commit in change[cat]:
            gitmoji, title = sep_gitmoji_msg_title(commit_message(commit))
            if not gitmoji:
                # Ignore commits without a recognizable gitmoji
                continue
            try:
                catmoji = any_to_catmoji(gitmoji)
            except NoSuchGitmojiSupportedError:
                # Skip unsupported gitmoji rather than error out
                continue
            key = (catmoji.emoji, catmoji.description)
            subcats.setdefault(key, []).append((title, str(commit.id)))

        for (emoji, description), items in subcats.items():
            header = ENTRY_GROUP_HEADER(
                emoji=emoji,
                gitmoji_description=description,
            ).markdown
            category_md += header
            for title, commit_hash in items:
                item = ENTRY_SUBITEM(
                    commit_description=title,
                    commit_hash=commit_hash,
                ).markdown
                category_md += item
        if category_md:
            changelog_markdown += CATEGORY_SECTION(cat, CATEGORY_SUBTEXTS[cat]).markdown
            changelog_markdown += category_md
            changelog_markdown += separator

    return changelog_markdown


def change_log(
    project_name: str,
    release_date: str,
    repo_dir: Path,
    tail_tag: str,
    head_tag: str,
    version: str | None = None,
) -> str:
    if version is None:
        version = head_tag

    return gen_markdown(
        project_name,
        version,
        release_date,
        structured_changelog(get_tag_to_tag_commits(repo_dir, tail_tag, head_tag)),
    ).strip()


def github_release_payload(
    project_name: str,
    release_date: str,
    repo_dir: Path,
    tail_tag: str,
    head_tag: str,
    version: str | None = None,
    *,
    draft: bool = False,
    prerelease: bool = False,
) -> str:
    """Return GitHub release payload as JSON string."""
    changelog = change_log(
        project_name=project_name,
        release_date=release_date,
        repo_dir=repo_dir,
        tail_tag=tail_tag,
        head_tag=head_tag,
        version=version,
    )
    payload = {
        "tag_name": head_tag,
        "name": version or head_tag,
        "body": changelog,
        "draft": draft,
        "prerelease": prerelease,
    }
    return json.dumps(payload)
