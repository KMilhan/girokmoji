from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator
from uuid import uuid4

import pytest
from pygit2 import (
    init_repository,
    Repository,
    GitError,
    Signature,
    GIT_SORT_TOPOLOGICAL,
    Oid,
)
from pygit2.enums import ObjectType

person = Signature("milhan", "milhan@milhan.kim")


@pytest.fixture(scope="function")
def inited_dir() -> Generator[str, None, None]:
    """Get inited git dir"""
    with TemporaryDirectory() as repo_dir:
        init_repository(repo_dir)
        yield repo_dir


@pytest.fixture(scope="function")
def initial_commit_dir(inited_dir) -> Generator[str, None, None]:
    new_f = Path(inited_dir) / "new.txt"
    new_f.write_text("new\n")
    repo = Repository(inited_dir)
    index = repo.index
    index.add_all()
    tree = index.write_tree()
    parents = []
    repo.create_commit("HEAD", person, person, ":boom: init", tree, parents)
    yield inited_dir


@pytest.fixture(scope="function")
def initial_release_dir(initial_commit_dir) -> Generator[str, None, None]:
    repo = Repository(initial_commit_dir)
    repo.create_tag(
        "v0.1.0", repo.head.resolve().target, ObjectType.COMMIT, person, "release1"
    )
    yield initial_commit_dir


def random_file_commit(
    repo_dir: str, gitmoji_no_colon: str, parents: list | None = None
) -> Oid:
    new_f = Path(repo_dir) / str(uuid4())
    new_f.write_text(str(uuid4))
    repo = Repository(repo_dir)
    new_f.write_text(str(uuid4))
    repo.index.add_all()
    if parents is None:
        parents = [repo.head.target]

    return repo.create_commit(
        "HEAD",
        person,
        person,
        f":{gitmoji_no_colon}: {uuid4()}",
        repo.index.write_tree(),
        parents,
    )


@pytest.fixture(scope="function")
def second_release_dir(initial_release_dir) -> Generator[str, None, None]:
    random_file_commit(initial_release_dir, "art")
    repo = Repository(initial_release_dir)
    repo.create_tag(
        "v0.2.0", repo.head.resolve().target, ObjectType.COMMIT, person, "release2"
    )
    yield initial_release_dir


def test_no_release_yet(inited_dir):
    assert Repository(inited_dir).head_is_unborn


def test_has_single_commit(initial_commit_dir):
    assert not Repository(initial_commit_dir).head_is_unborn
    assert Repository(initial_commit_dir).head is not None


def test_has_initial_release(initial_release_dir):
    assert Repository(initial_release_dir).references.get("refs/tags/v0.1.0")


def test_has_second_release(second_release_dir):
    assert Repository(second_release_dir).references.get("refs/tags/v0.2.0")


def test_get_commit_logs(second_release_dir):
    repo = Repository(second_release_dir)
    head_tag = "v0.2.0"
    tail_tag = "v0.1.0"

    rev_walk = repo.walk(
        repo.references.get(f"refs/tags/{head_tag}").target, GIT_SORT_TOPOLOGICAL
    )
    rev_walk.hide(repo.references.get(f"refs/tags/{tail_tag}").target)
    for commit in rev_walk:
        print(commit.message)


def test_empty_dir():
    with TemporaryDirectory() as tmp_dir:
        with pytest.raises(GitError):
            _ = Repository(tmp_dir)
