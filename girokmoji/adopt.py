"""Helper utilities for the `girokmoji adopt` command."""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable

from girokmoji.native.git2 import (
    Commit,
    FetchPrune,
    GitError,
    GIT_CHECKOUT_FORCE,
    ObjectType,
    Remote,
    Repository,
    Tag,
    clone_repository,
    discover_repository,
)

from .git import global_max_semver_tag, last_reachable_semver_tag
from .release import auto_release
from .semver import SemVer


ERROR_CATALOG = {
    "CLONE_FAILED": {"exit_code": 10, "retryable": True},
    "FETCH_TAGS_FAILED": {"exit_code": 11, "retryable": True},
    "CHECKOUT_FAILED": {"exit_code": 12, "retryable": False},
    "AUTH_FAILED": {"exit_code": 13, "retryable": True},
    "INVALID_REPO": {"exit_code": 14, "retryable": False},
    "DIRTY_WORKDIR": {"exit_code": 15, "retryable": False},
    "RELEASE_FAILED": {"exit_code": 20, "retryable": False},
    "UNKNOWN": {"exit_code": 99, "retryable": False},
}


@dataclass(frozen=True)
class AdoptOptions:
    """Normalized inputs for running the adopt flow."""

    repo: str
    project_name: str | None
    bump: str
    ref: str | None
    range_mode: str
    strict_ancestor: bool
    quiet: bool
    verbose: bool
    dry_run: bool
    workdir: Path | None
    keep_workdir: bool
    push_remote: str
    depth: int
    changelog_out: Path | None


@dataclass(frozen=True)
class AdoptResult:
    """Structured outcome from running adopt."""

    repo: str
    project_name: str
    workdir: Path
    workdir_persisted: bool
    ref: str
    commit: str
    default_branch: str | None
    previous_tag: str | None
    new_version: str
    new_tag: str
    release_type: str
    dry_run: bool
    tag_created: bool
    pushed: bool
    changelog: str
    changelog_path: Path | None
    next_steps: list[str]
    duration_ms: int


class AdoptError(RuntimeError):
    """Raised when adopt cannot complete successfully."""

    def __init__(self, code: str, message: str, *, hint: str | None = None):
        super().__init__(message)
        meta = ERROR_CATALOG.get(code, ERROR_CATALOG["UNKNOWN"])
        self.code = code
        self.exit_code = meta["exit_code"]
        self.retryable = meta["retryable"]
        self.hint = hint


def run_adopt(options: AdoptOptions) -> AdoptResult:
    """Run the adopt workflow and return a structured result."""

    if options.depth < 0:
        raise AdoptError("INVALID_REPO", "--depth must be >= 0")

    start = perf_counter()
    prep = _prepare_repository(options.repo, options.workdir, options.depth)
    repo = prep.repo

    if prep.uses_existing and _is_dirty(repo):
        raise AdoptError(
            "DIRTY_WORKDIR",
            f"Repository at {prep.workdir} has uncommitted changes",
            hint="Commit, stash, or use a fresh checkout before running adopt",
        )

    if prep.remote_like:
        _fetch_all_refs(repo, options.depth)

    if options.ref:
        _checkout_ref(repo, options.ref)
        active_ref = options.ref
    else:
        head = repo.head
        if head is None or repo.head_is_unborn:
            raise AdoptError("INVALID_REPO", "Repository has no commits to adopt")
        active_ref = head.shorthand or "HEAD"
        repo.checkout_head(strategy=GIT_CHECKOUT_FORCE)

    head = repo.head
    if head is None or repo.head_is_unborn:
        raise AdoptError("INVALID_REPO", "Repository has no commits to adopt")
    commit_obj = head.peel(ObjectType.COMMIT)
    if not isinstance(commit_obj, Commit):
        raise AdoptError("INVALID_REPO", "HEAD is not a commit")
    commit = commit_obj

    previous_tag, new_version, new_tag = _compute_version(repo, commit, options.bump)

    project_name = _infer_project_name(options.project_name, prep.workdir, options.repo)

    try:
        changelog = auto_release(
            project_name,
            repo_dir=prep.workdir,
            bump=options.bump,
            range_mode=options.range_mode,
            strict_ancestor=options.strict_ancestor,
            quiet=options.quiet,
            verbose=options.verbose,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise AdoptError(
            "RELEASE_FAILED", str(exc), hint="See stderr for details"
        ) from exc

    tag_created = True
    pushed = False

    if options.dry_run:
        _delete_tag(repo, new_tag)
        tag_created = False
    else:
        pushed = _maybe_push_tag(repo, new_tag, options.push_remote)

    workdir_persisted = prep.cleanup is None

    if options.changelog_out:
        options.changelog_out.parent.mkdir(parents=True, exist_ok=True)
        options.changelog_out.write_text(changelog)

    next_steps = _next_steps(
        repo_spec=options.repo,
        workdir=prep.workdir,
        workdir_persisted=workdir_persisted,
        new_tag=new_tag,
        push_remote=options.push_remote,
        dry_run=options.dry_run,
        pushed=pushed,
    )

    duration_ms = int((perf_counter() - start) * 1000)

    result = AdoptResult(
        repo=options.repo,
        project_name=project_name,
        workdir=prep.workdir,
        workdir_persisted=workdir_persisted,
        ref=active_ref,
        commit=str(commit.id),
        default_branch=head.shorthand or None,
        previous_tag=previous_tag,
        new_version=new_version,
        new_tag=new_tag,
        release_type=options.bump,
        dry_run=options.dry_run,
        tag_created=tag_created,
        pushed=pushed,
        changelog=changelog,
        changelog_path=options.changelog_out,
        next_steps=next_steps,
        duration_ms=duration_ms,
    )

    if prep.cleanup is not None:
        prep.cleanup()

    return result


def render_result(result: AdoptResult, output_format: str) -> str:
    if output_format == "json":
        payload = {
            "repo_url": result.repo,
            "project_name": result.project_name,
            "workdir": str(result.workdir),
            "workdir_persisted": result.workdir_persisted,
            "ref": result.ref,
            "commit": result.commit,
            "default_branch": result.default_branch,
            "previous_tag": result.previous_tag,
            "new_version": result.new_version,
            "new_tag": result.new_tag,
            "release_type": result.release_type,
            "dry_run": result.dry_run,
            "tag_created": result.tag_created,
            "pushed": result.pushed,
            "changelog": result.changelog,
            "changelog_path": str(result.changelog_path)
            if result.changelog_path
            else None,
            "next_steps": result.next_steps,
            "duration_ms": result.duration_ms,
        }
        return json.dumps(payload, separators=(",", ":"))

    lines = [
        (
            "girokmoji:adopt "
            f"repo={result.repo} ref={result.ref} "
            f"previous={result.previous_tag or 'none'} next={result.new_tag} "
            f"type={result.release_type} dry_run={'true' if result.dry_run else 'false'}"
        ),
        f"workdir={result.workdir}",
        "next_steps:",
    ]
    for idx, step in enumerate(result.next_steps, start=1):
        lines.append(f"  {idx}) {step}")
    lines.append("---- changelog start ----")
    lines.append(result.changelog.rstrip())
    lines.append("---- changelog end ----")
    return "\n".join(lines)


def render_error(error: AdoptError, output_format: str) -> str:
    if output_format == "json":
        payload = {
            "error": {
                "code": error.code,
                "message": str(error),
                "retryable": error.retryable,
            }
        }
        if error.hint:
            payload["error"]["hint"] = error.hint
        return json.dumps(payload, separators=(",", ":"))

    base = f"ERROR[{error.code}]: {error}"
    if error.hint:
        base += f" (hint: {error.hint})"
    return base


# Internal helpers -----------------------------------------------------------------


@dataclass
class PreparedRepo:
    repo: Repository
    workdir: Path
    uses_existing: bool
    remote_like: bool
    cleanup: Callable[[], None] | None


def _prepare_repository(
    repo_spec: str, workdir_arg: Path | None, depth: int
) -> PreparedRepo:
    remote_like = _looks_like_remote(repo_spec)

    if workdir_arg is not None:
        workdir = workdir_arg.expanduser().resolve()
        if workdir.exists():
            git_dir = discover_repository(str(workdir))
            if git_dir:
                repo = Repository(git_dir)
                return PreparedRepo(
                    repo=repo,
                    workdir=Path(git_dir).parent,
                    uses_existing=True,
                    remote_like=remote_like,
                    cleanup=None,
                )
            if any(workdir.iterdir()):
                raise AdoptError(
                    "INVALID_REPO",
                    f"{workdir} exists but is not a git repository",
                    hint="Point --workdir to an existing repo or an empty directory",
                )
        else:
            workdir.parent.mkdir(parents=True, exist_ok=True)
        repo = _clone(repo_spec, workdir, depth)
        return PreparedRepo(
            repo=repo,
            workdir=Path(repo.workdir),
            uses_existing=False,
            remote_like=True,
            cleanup=None,
        )

    if not remote_like and Path(repo_spec).expanduser().resolve().exists():
        git_dir = discover_repository(repo_spec)
        if not git_dir:
            raise AdoptError(
                "INVALID_REPO",
                f"{repo_spec} is not a git repository",
                hint="Pass a repo URL or path containing .git",
            )
        repo = Repository(git_dir)
        return PreparedRepo(
            repo=repo,
            workdir=Path(git_dir).parent,
            uses_existing=True,
            remote_like=False,
            cleanup=None,
        )

    temp_dir = Path(tempfile.mkdtemp(prefix="girokmoji-adopt-"))
    repo = _clone(repo_spec, temp_dir, depth)

    def _cleanup() -> None:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return PreparedRepo(
        repo=repo,
        workdir=Path(repo.workdir),
        uses_existing=False,
        remote_like=True,
        cleanup=_cleanup,
    )


def _clone(repo_spec: str, destination: Path, depth: int) -> Repository:
    try:
        return clone_repository(
            repo_spec,
            str(destination),
            checkout_branch=None,
            depth=depth,
        )
    except GitError as exc:  # pragma: no cover - network/auth errors
        code = "AUTH_FAILED" if _looks_like_auth_error(exc) else "CLONE_FAILED"
        raise AdoptError(code, f"Failed to clone {repo_spec}", hint=str(exc)) from exc


def _fetch_all_refs(repo: Repository, depth: int) -> None:
    remote = _remote_by_name(repo, "origin")
    if remote is None:
        return
    try:
        remote.fetch(
            refspecs=[
                "+refs/heads/*:refs/remotes/origin/*",
                "+refs/tags/*:refs/tags/*",
            ],
            prune=FetchPrune.PRUNE,
            depth=depth or 0,
        )
    except GitError as exc:
        code = "AUTH_FAILED" if _looks_like_auth_error(exc) else "FETCH_TAGS_FAILED"
        raise AdoptError(
            code, "Failed to fetch refs from origin", hint=str(exc)
        ) from exc


def _checkout_ref(repo: Repository, ref: str) -> None:
    try:
        target = repo.revparse_single(ref)
    except Exception as exc:  # pragma: no cover - invalid refs
        raise AdoptError(
            "CHECKOUT_FAILED",
            f"Ref '{ref}' was not found",
            hint="Provide a branch, tag, or commit reachable in the repo",
        ) from exc
    repo.checkout_tree(target, strategy=GIT_CHECKOUT_FORCE)
    if isinstance(target, Commit):
        repo.set_head(target.id)
    elif isinstance(target, Tag):
        obj = target.peel(ObjectType.COMMIT)
        repo.set_head(obj.id)
    else:
        repo.set_head(ref)


def _compute_version(
    repo: Repository, commit: Commit, bump: str
) -> tuple[str | None, str, str]:
    last = last_reachable_semver_tag(repo, commit)
    last_version = last[1] if last else SemVer(0, 0, 0)
    previous_tag = last[0] if last else None

    global_max = global_max_semver_tag(repo)
    global_version = global_max[1] if global_max else SemVer(0, 0, 0)
    base = global_version if global_version > last_version else last_version
    new_version = base.bump(bump)
    return previous_tag, str(new_version), f"v{new_version}"


def _delete_tag(repo: Repository, tag_name: str) -> None:
    try:
        repo.references.delete(f"refs/tags/{tag_name}")
    except KeyError:  # pragma: no cover - already absent
        return


def _maybe_push_tag(repo: Repository, tag_name: str, push_remote: str) -> bool:
    remote = _remote_by_name(repo, push_remote)
    if remote is None and _looks_like_remote(push_remote):
        remote = repo.remotes.create_anonymous(push_remote)
    if remote is None:
        raise AdoptError(
            "RELEASE_FAILED",
            f"Remote '{push_remote}' not found",
            hint="Use --push-remote with an existing remote name or URL",
        )
    try:
        remote.push([f"refs/tags/{tag_name}"])
        return True
    except GitError as exc:  # pragma: no cover - network/auth errors
        code = "AUTH_FAILED" if _looks_like_auth_error(exc) else "RELEASE_FAILED"
        raise AdoptError(code, f"Failed to push tag {tag_name}", hint=str(exc)) from exc


def _next_steps(
    *,
    repo_spec: str,
    workdir: Path,
    workdir_persisted: bool,
    new_tag: str,
    push_remote: str,
    dry_run: bool,
    pushed: bool,
) -> list[str]:
    steps: list[str] = []
    if dry_run:
        if workdir_persisted:
            steps.append(f"cd {workdir}")
            steps.append(f'git tag -a {new_tag} -m "release: {new_tag}"')
            steps.append(f"git push {push_remote} {new_tag}")
        else:
            steps.append(
                "Re-run with --keep-workdir or --workdir <path> to inspect the checkout"
            )
        steps.append(f"girokmoji adopt {repo_spec} --apply --push-remote {push_remote}")
    else:
        if not pushed:
            steps.append(f"git push {push_remote} {new_tag}")
        steps.append(f"girokmoji adopt {repo_spec} --format text --dry-run")
    return steps


def _infer_project_name(override: str | None, workdir: Path, repo_spec: str) -> str:
    if override:
        return override
    if workdir.name:
        return workdir.name
    candidate = repo_spec.rstrip("/").split("/")[-1]
    return candidate.removesuffix(".git") or "project"


def _looks_like_remote(text: str) -> bool:
    lowered = text.lower()
    return lowered.startswith(("https://", "http://", "ssh://", "git@", "file://"))


def _looks_like_auth_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(token in message for token in ("auth", "permission", "denied"))


def _is_dirty(repo: Repository) -> bool:
    return bool(repo.status())


def _remote_by_name(repo: Repository, name: str) -> "Remote | None":
    try:
        return repo.remotes[name]
    except KeyError:
        return None


__all__ = [
    "AdoptError",
    "AdoptOptions",
    "AdoptResult",
    "render_error",
    "render_result",
    "run_adopt",
]
