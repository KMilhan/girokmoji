from __future__ import annotations

from datetime import date
from pathlib import Path

from pygit2 import Repository, discover_repository, Signature, GitError
from pygit2.enums import ObjectType

from .changelog import change_log, github_release_payload
from .semver import SemVer
from .git import last_reachable_semver_tag, global_max_semver_tag


SUPPORTED_BUMPS = {"patch", "minor", "major"}


def auto_release(
    project_name: str,
    repo_dir: Path = Path("."),
    *,
    bump: str = "patch",
    release_date: str | None = None,
    github_payload: bool = False,
    on_tag_exists: str = "error",
    # threading options for commit range selection
    range_mode: str = "auto",
    strict_ancestor: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    sorting: int | None = None,
    version_floor_scope: str = "global",
) -> str:
    """Bump version using SemVer and return release notes.

    Parameters are similar to the GitHub Actions workflow. ``bump`` can be
    ``patch``, ``minor`` or ``major``.
    """
    if bump not in SUPPORTED_BUMPS:
        raise ValueError(f"Unsupported bump value: {bump}")

    if release_date is None:
        release_date = date.today().isoformat()

    repo = Repository(discover_repository(str(repo_dir)))
    # Determine head commit as Commit object
    head_commit = repo.head.peel(ObjectType.COMMIT)

    # Determine last reachable SemVer tag from HEAD
    lr = last_reachable_semver_tag(repo, head_commit)
    if lr is not None:
        last_tag_name, last_reachable_version = lr[0], lr[1]
        # Normalize last_tag to have leading 'v'
        last_tag = f"v{last_reachable_version}"
    else:
        last_reachable_version = SemVer(0, 0, 0)
        last_tag = "v0.0.0"

    # Determine global maximum SemVer tag (for hotpatch floor)
    gm = global_max_semver_tag(repo)
    global_max_version = gm[1] if gm is not None else SemVer(0, 0, 0)

    # Compute base for bump
    if version_floor_scope not in {"global", "reachable"}:
        raise ValueError(f"Unsupported version_floor_scope: {version_floor_scope}")
    base_for_bump = (
        global_max_version if version_floor_scope == "global" and global_max_version > last_reachable_version
        else last_reachable_version
    )

    new_version = base_for_bump.bump(bump)
    new_tag = f"v{new_version}"

    try:
        sig = repo.default_signature
    except KeyError:
        sig = None
    sig = sig or Signature("girokmoji", "release@girokmoji")
    try:
        repo.create_tag(new_tag, repo.head.target, ObjectType.COMMIT, sig, new_tag)
    except (GitError, ValueError) as e:
        if on_tag_exists == "skip":
            # Proceed without creating the tag again
            pass
        elif on_tag_exists == "overwrite":
            # Delete and recreate the tag
            try:
                repo.references.delete(f"refs/tags/{new_tag}")
            except Exception:
                # If deletion fails, re-raise original error
                raise e
            repo.create_tag(new_tag, repo.head.target, ObjectType.COMMIT, sig, new_tag)
        else:
            # Default strict behavior
            raise

    if github_payload:
        return github_release_payload(
            project_name=project_name,
            release_date=release_date,
            repo_dir=repo_dir,
            tail_tag=last_tag,
            head_tag=new_tag,
            version=new_tag,
            range_mode=range_mode,
            strict_ancestor=strict_ancestor,
            quiet=quiet,
            verbose=verbose,
            sorting=sorting,
        )
    return change_log(
        project_name=project_name,
        release_date=release_date,
        repo_dir=repo_dir,
        tail_tag=last_tag,
        head_tag=new_tag,
        version=new_tag,
        range_mode=range_mode,
        strict_ancestor=strict_ancestor,
        quiet=quiet,
        verbose=verbose,
        sorting=sorting,
    )
