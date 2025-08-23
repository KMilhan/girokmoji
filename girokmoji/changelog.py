import json
from pathlib import Path
from typing import Iterable, Protocol, runtime_checkable, Any

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


@runtime_checkable
class CommitLike(Protocol):
    @property
    def message(self) -> str | None: ...

    @property
    def raw_message(self) -> bytes: ...

    @property
    def message_encoding(self) -> str: ...

    @property
    def id(self) -> Any: ...


def commit_message(commit: CommitLike) -> str:
    if isinstance(commit.message, str):
        return commit.message

    return commit.raw_message.decode(commit.message_encoding)


def get_category(msg: str, *, fallback_to_includes: bool = True) -> CATEGORY:
    mapping = by_gitmoji()
    for gitmoji, info in mapping.items():
        cat: CATEGORY = info.category
        if msg.startswith(gitmoji):
            return cat
    if fallback_to_includes:
        for gitmoji, info in mapping.items():
            cat: CATEGORY = info.category
            if gitmoji in msg:
                return cat
    raise NoGitmojiInMessageError("No Gitmoji found in the message")


def sep_gitmoji_msg_title(msg: str, *, strict: bool = False) -> tuple[str, str]:
    """Return gitmoji and message from commit message. Strict mode raises exception MessageDoesNotStartWithGitmojiError"""
    msg = msg.split("\n")[0]
    for gitmoji in by_gitmoji():
        if msg.startswith(gitmoji):
            return gitmoji, msg.removeprefix(gitmoji).strip()

    if not strict:
        return "", msg.split("\n")[0]

    raise MessageDoesNotStartWithGitmojiError


def structured_changelog(
    commits: Iterable[CommitLike],
) -> dict[CATEGORY, list[CommitLike]]:
    # prepare structured changelog with importance order
    structured_changelog: dict[CATEGORY, list[CommitLike]] = {}
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
    change: dict[CATEGORY, list[CommitLike]],
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

    # Iterate categories in a deterministic, user-facing priority order
    for cat in category_order:
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
    *,
    range_mode: str = "auto",
    strict_ancestor: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    sorting: int | None = None,
) -> str:
    if version is None:
        version = head_tag

    # Preserve backward-compat: only pass extra kwargs when they differ
    # from defaults, so monkeypatched tests with simpler signatures work.
    if (
        range_mode == "auto"
        and not strict_ancestor
        and not quiet
        and not verbose
        and sorting is None
    ):
        commits = get_tag_to_tag_commits(repo_dir, tail_tag, head_tag)
    else:
        commits = get_tag_to_tag_commits(
            repo_dir,
            tail_tag,
            head_tag,
            range_mode=range_mode,
            strict_ancestor=strict_ancestor,
            quiet=quiet,
            verbose=verbose,
            sorting=sorting,
        )

    return gen_markdown(
        project_name,
        version,
        release_date,
        structured_changelog(commits),
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
    range_mode: str = "auto",
    strict_ancestor: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    sorting: int | None = None,
) -> str:
    """Return GitHub release payload as JSON string."""
    changelog = change_log(
        project_name=project_name,
        release_date=release_date,
        repo_dir=repo_dir,
        tail_tag=tail_tag,
        head_tag=head_tag,
        version=version,
        range_mode=range_mode,
        strict_ancestor=strict_ancestor,
        quiet=quiet,
        verbose=verbose,
        sorting=sorting,
    )
    payload = {
        "tag_name": head_tag,
        "name": version or head_tag,
        "body": changelog,
        "draft": draft,
        "prerelease": prerelease,
    }
    # Preserve unicode characters (e.g., emoji) in output for readability
    return json.dumps(payload, ensure_ascii=False)
