import argparse
import sys
from pathlib import Path

from girokmoji.changelog import change_log, github_release_payload
from girokmoji.release import auto_release
from girokmoji import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate release notes from gitmoji commits"
    )
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser(
        "generate", help="Generate notes between two tags"
    )
    generate.add_argument("project_name", help="Name of the project")
    generate.add_argument("release_date", help="Release date (YYYY-MM-DD)")
    generate.add_argument("repo_dir", type=Path, help="Path to the git repository")
    generate.add_argument("tail_tag", help="Older git tag (tail tag)")
    generate.add_argument("head_tag", help="Newer git tag (head tag)")
    generate.add_argument(
        "--release-version",
        dest="version",
        help="Optional release version string (defaults to head_tag)",
        default=None,
    )
    generate.add_argument(
        "--github-payload",
        action="store_true",
        help="Output GitHub Release payload JSON instead of markdown",
    )

    release = subparsers.add_parser(
        "release", help="Run semantic-release and output new release notes"
    )
    release.add_argument("project_name", help="Name of the project")
    release.add_argument(
        "--repo-dir", type=Path, default=Path("."), help="Path to the git repository"
    )
    release.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Version part to bump",
    )
    release.add_argument(
        "--release-date",
        help="Release date (YYYY-MM-DD). Defaults to today",
        default=None,
    )
    release.add_argument(
        "--github-payload",
        action="store_true",
        help="Output GitHub Release payload JSON instead of markdown",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit",
    )

    parser.set_defaults(command="generate")
    args = parser.parse_args()

    if args.command == "release":
        note = auto_release(
            args.project_name,
            repo_dir=args.repo_dir,
            bump=args.bump,
            release_date=args.release_date,
            github_payload=args.github_payload,
        )
        print(note, file=sys.stdout)
    else:
        if args.github_payload:
            payload = github_release_payload(
                project_name=args.project_name,
                release_date=args.release_date,
                repo_dir=args.repo_dir,
                tail_tag=args.tail_tag,
                head_tag=args.head_tag,
                version=args.version,
            )
            print(payload, file=sys.stdout)
        else:
            changelog = change_log(
                project_name=args.project_name,
                release_date=args.release_date,
                repo_dir=args.repo_dir,
                tail_tag=args.tail_tag,
                head_tag=args.head_tag,
                version=args.version,
            )
            print(changelog, file=sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - top level entry
        print(exc, file=sys.stderr)
        sys.exit(1)
