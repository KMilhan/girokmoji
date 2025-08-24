from pathlib import Path
from typing import Iterable
import sys
from pygit2 import Commit, Repository, discover_repository
from pygit2.enums import ObjectType
from pygit2 import GIT_SORT_TOPOLOGICAL, GIT_SORT_TIME

from girokmoji.exception import NoSuchTagFoundError, NotAncestorError
from girokmoji.semver import SemVer


def _resolve_to_commit(repo: Repository, name: str) -> Commit:
    """Resolve a reference, tag name, or hex OID to a Commit.

    Tries in order:
    - Exact ref name (when name starts with 'refs/'), e.g., 'refs/tags/v1'
    - Tag under refs/tags/<name>
    - Revision parse via `revparse_single` (accepts tag names, shas, etc.)
    """
    obj = None
    ref = None
    if name.startswith("refs/"):
        ref = repo.references.get(name)
    else:
        ref = repo.references.get(f"refs/tags/{name}")
    if ref is not None:
        obj = repo[ref.target]
    else:
        try:
            obj = repo.revparse_single(name)
        except Exception:
            obj = None
    if obj is None:
        raise NoSuchTagFoundError(f"{name} can't be found")
    return obj.peel(ObjectType.COMMIT)


def get_tag_to_tag_commits(
    repo_dir: Path,
    tail_tag: str,
    head_tag: str,
    *,
    range_mode: str = "auto",
    strict_ancestor: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    sorting: int | None = None,
) -> Iterable[Commit]:
    """Yield commits from tail->head based on range mode.

    range_mode options:
    - 'direct': hide tail, walk from head
    - 'common-base': hide merge-base(head, tail), walk from head
    - 'auto' (default): if head is descendant of tail use direct, else use
      common-base when available; if no merge-base, walk head-only.

    When strict_ancestor is True and head is not descendant of tail, raise
    NotAncestorError.
    """
    repo = Repository(discover_repository(str(repo_dir)))
    head_commit = _resolve_to_commit(repo, head_tag)
    tail_commit = _resolve_to_commit(repo, tail_tag)

    # Decide effective mode
    effective_mode = range_mode
    if range_mode == "auto":
        is_desc = repo.descendant_of(head_commit.id, tail_commit.id)
        if strict_ancestor and not is_desc:
            raise NotAncestorError(
                f"{tail_tag} is not an ancestor of {head_tag}"
            )
        if is_desc:
            effective_mode = "direct"
            if verbose and not quiet:
                sys.stderr.write("[girokmoji] auto: using direct (linear history)\n")
        else:
            mb = repo.merge_base(head_commit.id, tail_commit.id)
            if mb is not None:
                effective_mode = "common-base"
                if not quiet:
                    if verbose:
                        sys.stderr.write(
                            f"[girokmoji] auto: using common-base (merge-base {mb})\n"
                        )
                    else:
                        sys.stderr.write("[girokmoji] auto: using common-base\n")
            else:
                effective_mode = "head-only"
                if not quiet:
                    if verbose:
                        sys.stderr.write(
                            "[girokmoji] auto: no merge-base; falling back to head-only\n"
                        )
                    else:
                        sys.stderr.write(
                            "[girokmoji] auto: falling back to head-only\n"
                        )
    elif strict_ancestor:
        # Respect strict check even for explicit mode selections
        if not repo.descendant_of(head_commit.id, tail_commit.id):
            raise NotAncestorError(
                f"{tail_tag} is not an ancestor of {head_tag}"
            )

    # Prepare walker
    rev_walk = repo.walk(head_commit.id)
    # Default sorting if unspecified
    if sorting is None:
        sorting = int(GIT_SORT_TOPOLOGICAL) | int(GIT_SORT_TIME)
    sort_fn = getattr(rev_walk, "sorting", None)
    if callable(sort_fn):
        sort_fn(sorting)

    # Apply hiding logic by mode
    if effective_mode == "direct":
        rev_walk.hide(tail_commit.id)
    elif effective_mode == "common-base":
        mb = repo.merge_base(head_commit.id, tail_commit.id)
        if mb is not None:
            rev_walk.hide(mb)
        else:
            # Fallback to head-only if no merge-base despite request
            if not quiet:
                sys.stderr.write(
                    "[girokmoji] common-base requested but no merge-base; head-only\n"
                )
    elif effective_mode == "head-only":
        # Do not hide anything; enumerate from head
        pass
    else:
        # For safety, treat unknown as direct
        rev_walk.hide(tail_commit.id)

    for rev in rev_walk:
        if isinstance(rev, Commit):
            yield rev


def iter_semver_tags(repo: Repository) -> Iterable[tuple[str, SemVer, Commit]]:
    """Iterate SemVer tags in the repository with their target commit.

    - Accepts both annotated and lightweight tags (peels to Commit).
    - Accepts optional leading 'v' in tag names.
    - Ignores tags that are not valid SemVer.
    """
    for refname in repo.references:
        if not refname.startswith("refs/tags/"):
            continue
        tag_name = refname.rsplit("/", 1)[-1]
        text = tag_name[1:] if tag_name.startswith("v") else tag_name
        try:
            ver = SemVer.parse(text)
        except ValueError:
            continue
        ref = repo.references.get(refname)
        if ref is None:
            continue
        obj = repo[ref.target]
        commit = obj.peel(ObjectType.COMMIT)
        yield (tag_name, ver, commit)


def last_reachable_semver_tag(
    repo: Repository, head: Commit
) -> tuple[str, SemVer] | None:
    """Return the SemVer-tag (name, version) with the largest version that is
    reachable from the given HEAD commit. Returns None if none is reachable.
    """
    best: tuple[str, SemVer] | None = None
    for name, ver, commit in iter_semver_tags(repo):
        # Treat the tag at HEAD as reachable as well
        if commit.id == head.id or repo.descendant_of(head.id, commit.id):
            if best is None or ver > best[1]:
                best = (name, ver)
    return best


def global_max_semver_tag(repo: Repository) -> tuple[str, SemVer] | None:
    """Return the global maximum SemVer tag (name, version) across all tags.
    Returns None if there is no SemVer tag.
    """
    best: tuple[str, SemVer] | None = None
    for name, ver, _ in iter_semver_tags(repo):
        if best is None or ver > best[1]:
            best = (name, ver)
    return best
