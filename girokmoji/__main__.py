import argparse
import sys
from pathlib import Path

from girokmoji.changelog import change_log


def main():
    parser = argparse.ArgumentParser(
        description="Generate a changelog from gitmoji-based commits between two tags."
    )
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("release_date", help="Release date (YYYY-MM-DD)")
    parser.add_argument("repo_dir", type=Path, help="Path to the git repository")
    parser.add_argument("tail_tag", help="Older git tag (tail tag)")
    parser.add_argument("head_tag", help="Newer git tag (head tag)")
    parser.add_argument(
        "--version",
        help="Optional version string (defaults to head_tag if not provided)",
        default=None,
    )

    args = parser.parse_args()

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
    main()
