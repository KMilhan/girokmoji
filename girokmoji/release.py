from __future__ import annotations

from datetime import date
from pathlib import Path

from pygit2 import Repository, discover_repository, Signature
from pygit2.enums import ObjectType

from .changelog import change_log, github_release_payload
from .semver import SemVer


SUPPORTED_BUMPS = {"patch", "minor", "major"}


def auto_release(
    project_name: str,
    repo_dir: Path = Path("."),
    *,
    bump: str = "patch",
    release_date: str | None = None,
    github_payload: bool = False,
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
    tags = [r for r in repo.references if r.startswith("refs/tags/")]
    versions: list[SemVer] = []
    for t in tags:
        name = t.rsplit("/", 1)[-1]
        if name.startswith("v"):
            name = name[1:]
        try:
            versions.append(SemVer.parse(name))
        except ValueError:
            continue
    if versions:
        versions.sort()
        last_version = versions[-1]
        last_tag = f"v{last_version}"
    else:
        last_version = SemVer(0, 0, 0)
        last_tag = "v0.0.0"
    new_version = last_version.bump(bump)
    new_tag = f"v{new_version}"

    try:
        sig = repo.default_signature
    except KeyError:
        sig = None
    sig = sig or Signature("girokmoji", "release@girokmoji")
    repo.create_tag(new_tag, repo.head.target, ObjectType.COMMIT, sig, new_tag)

    if github_payload:
        return github_release_payload(
            project_name=project_name,
            release_date=release_date,
            repo_dir=repo_dir,
            tail_tag=last_tag,
            head_tag=new_tag,
            version=new_tag,
        )
    return change_log(
        project_name=project_name,
        release_date=release_date,
        repo_dir=repo_dir,
        tail_tag=last_tag,
        head_tag=new_tag,
        version=new_tag,
    )
