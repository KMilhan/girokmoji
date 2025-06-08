from pathlib import Path
from typing import Iterable

from pygit2 import Commit, Repository, GIT_SORT_TOPOLOGICAL, discover_repository
from pygit2.enums import ObjectType

from girokmoji.exception import NoSuchTagFoundError


def get_tag_to_tag_commits(
    repo_dir: Path, tail_tag: str, head_tag: str
) -> Iterable[Commit]:
    repo = Repository(discover_repository(str(repo_dir)))
    head_ref = repo.references.get(f"refs/tags/{head_tag}")
    tail_ref = repo.references.get(f"refs/tags/{tail_tag}")
    if head_ref is None:
        raise NoSuchTagFoundError(f"{head_tag} can't be found")
    if tail_ref is None:
        raise NoSuchTagFoundError(f"{tail_tag} can't be found")

    head_commit = repo[head_ref.target].peel(ObjectType.COMMIT)
    tail_commit = repo[tail_ref.target].peel(ObjectType.COMMIT)

    rev_walk = repo.walk(head_commit.id, GIT_SORT_TOPOLOGICAL)
    rev_walk.hide(tail_commit.id)
    for rev in rev_walk:
        if isinstance(rev, Commit):
            yield rev
