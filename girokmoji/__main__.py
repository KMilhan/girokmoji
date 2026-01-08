import argparse
import sys
from pathlib import Path

from girokmoji.adopt import (
    AdoptError,
    AdoptOptions,
    render_error,
    render_result,
    run_adopt,
)
from girokmoji.changelog import change_log, github_release_payload
from girokmoji.release import auto_release
from girokmoji import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate release notes from gitmoji commits"
    )
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser("generate", help="Generate notes between two tags")
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

    adopt = subparsers.add_parser(
        "adopt",
        help="Adopt a repo, run release logic, and emit agent-friendly output",
    )
    adopt.add_argument("repo", help="Repository URL or path to adopt")
    adopt.add_argument(
        "--project-name",
        help="Override the inferred project name (defaults to repo folder)",
    )
    adopt.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Version part to bump (defaults to patch)",
    )
    adopt.add_argument(
        "--ref", help="Branch, tag, or commit to checkout before releasing"
    )
    adopt.add_argument(
        "--range",
        "--range-mode",
        dest="range_mode",
        choices=["auto", "direct", "common-base"],
        default="auto",
        help="Commit range mode forwarded to the release engine",
    )
    adopt.add_argument(
        "--strict-ancestor",
        action="store_true",
        help="Require the previous tag to be an ancestor of head",
    )
    adopt.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational notices on stderr",
    )
    adopt.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose notices to stderr",
    )
    mode_group = adopt.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Simulate tagging/pushing (default)",
    )
    mode_group.add_argument(
        "--apply",
        dest="dry_run",
        action="store_false",
        help="Create and push the computed tag",
    )
    adopt.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (text or json)",
    )
    adopt.add_argument(
        "--json",
        dest="format",
        action="store_const",
        const="json",
        help="Shortcut for --format json",
    )
    adopt.add_argument(
        "--workdir",
        type=Path,
        help="Reuse an existing checkout or clone into this directory",
    )
    adopt.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Keep the temporary clone on disk after finishing",
    )
    adopt.add_argument(
        "--push-remote",
        default="origin",
        help="Remote name or URL used when pushing during --apply",
    )
    adopt.add_argument(
        "--depth",
        type=int,
        default=0,
        help="Clone depth for remote fetches (0 = full history)",
    )
    adopt.add_argument(
        "--changelog-out",
        type=Path,
        help="Also write the changelog to this path",
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
    elif args.command == "adopt":
        options = AdoptOptions(
            repo=args.repo,
            project_name=args.project_name,
            bump=args.bump,
            ref=args.ref,
            range_mode=args.range_mode,
            strict_ancestor=args.strict_ancestor,
            quiet=args.quiet,
            verbose=args.verbose,
            dry_run=args.dry_run,
            workdir=args.workdir,
            keep_workdir=args.keep_workdir,
            push_remote=args.push_remote,
            depth=args.depth,
            changelog_out=args.changelog_out,
        )
        try:
            result = run_adopt(options)
        except AdoptError as error:
            rendered = render_error(error, args.format)
            stream = sys.stdout if args.format == "json" else sys.stderr
            print(rendered, file=stream)
            sys.exit(error.exit_code)
        print(render_result(result, args.format), file=sys.stdout)
        sys.exit(0)
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
        print(exc, file=sys.stderr)  # pragma: no cover - trivial exit
        sys.exit(1)  # pragma: no cover - trivial exit
