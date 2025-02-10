from pathlib import Path
from typing import Iterable

from pygit2 import Commit, Repository, GIT_SORT_TOPOLOGICAL

from girokmoji.exception import NoSuchTagFoundError


def get_tag_to_tag_commits(
    repo_dir: Path, tail_tag: str, head_tag: str
) -> Iterable[Commit]:
    repo = Repository(str(repo_dir))
    head = repo.references.get(f"refs/tags/{head_tag}")
    tail = repo.references.get(f"refs/tags/{tail_tag}")
    if head is None:
        raise NoSuchTagFoundError(f"{head_tag} can't be found")
    if tail is None:
        raise NoSuchTagFoundError(f"{tail_tag} can't be found")
    rev_walk = repo.walk(head.target, GIT_SORT_TOPOLOGICAL)
    rev_walk.hide(tail.target)
    for rev in rev_walk:
        if isinstance(rev, Commit):
            yield rev
