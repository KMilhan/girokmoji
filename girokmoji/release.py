from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from .changelog import change_log, github_release_payload


SUPPORTED_BUMPS = {"patch", "minor", "major"}


def auto_release(
    project_name: str,
    repo_dir: Path = Path("."),
    *,
    bump: str = "patch",
    release_date: str | None = None,
    github_payload: bool = False,
) -> str:
    """Run semantic-release and return generated release note.

    Parameters are similar to the GitHub Actions workflow.
    ``bump`` can be ``patch``, ``minor`` or ``major``.
    """
    if bump not in SUPPORTED_BUMPS:
        raise ValueError(f"Unsupported bump value: {bump}")

    if release_date is None:
        release_date = date.today().isoformat()

    last_tag = subprocess.check_output(
        ["semantic-release", "version", "--print-last-released-tag"],
        text=True,
        cwd=repo_dir,
    ).strip()
    new_tag = subprocess.check_output(
        ["semantic-release", "version", f"--{bump}", "--print-tag"],
        text=True,
        cwd=repo_dir,
    ).strip()
    subprocess.run(
        ["semantic-release", "version", f"--{bump}"],
        check=True,
        cwd=repo_dir,
    )

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
