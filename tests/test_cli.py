import subprocess
import sys
from pathlib import Path

import girokmoji


def test_cli_version():
    result = subprocess.run(
        [sys.executable, '-m', 'girokmoji', '--version'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert girokmoji.__version__ in result.stdout


def test_cli_release(monkeypatch):
    called = {}

    def fake_auto_release(project_name, repo_dir, bump, release_date, github_payload):
        called["args"] = (project_name, repo_dir, bump, github_payload)
        return "note"

    monkeypatch.setattr("girokmoji.release.auto_release", fake_auto_release)
    import girokmoji.__main__ as giromain
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "girokmoji",
            "release",
            "proj",
            "--bump",
            "minor",
            "--repo-dir",
            ".",
            "--github-payload",
        ],
    )
    giromain.main()
    assert called["args"] == ("proj", Path("."), "minor", True)
