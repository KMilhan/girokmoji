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
        "--range",
        "--range-mode",
        dest="range_mode",
        choices=["auto", "direct", "common-base"],
        default="auto",
        help="Commit range mode: auto (default), direct, common-base",
    )
    generate.add_argument(
        "--strict-ancestor",
        action="store_true",
        help="Require tail to be an ancestor of head",
    )
    generate.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational notices on stderr",
    )
    generate.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose notices to stderr",
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
    release.add_argument(
        "--range",
        "--range-mode",
        dest="range_mode",
        choices=["auto", "direct", "common-base"],
        default="auto",
        help="Commit range mode: auto (default), direct, common-base",
    )
    release.add_argument(
        "--strict-ancestor",
        action="store_true",
        help="Require tail to be an ancestor of head",
    )
    release.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational notices on stderr",
    )
    release.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose notices to stderr",
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
        # Preserve backward-compatibility for tests monkeypatching auto_release
        release_kwargs = dict(
            repo_dir=args.repo_dir,
            bump=args.bump,
            release_date=args.release_date,
            github_payload=args.github_payload,
        )
        if (
            args.range_mode != "auto"
            or args.strict_ancestor
            or args.quiet
            or args.verbose
        ):
            release_kwargs.update(
                range_mode=args.range_mode,
                strict_ancestor=args.strict_ancestor,
                quiet=args.quiet,
                verbose=args.verbose,
            )
        note = auto_release(
            args.project_name,
            **release_kwargs,
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
                range_mode=args.range_mode,
                strict_ancestor=args.strict_ancestor,
                quiet=args.quiet,
                verbose=args.verbose,
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
                range_mode=args.range_mode,
                strict_ancestor=args.strict_ancestor,
                quiet=args.quiet,
                verbose=args.verbose,
            )
            print(changelog, file=sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - top level entry
        print(exc, file=sys.stderr)
        sys.exit(1)
