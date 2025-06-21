import subprocess
import sys

import girokmoji


def test_cli_version():
    result = subprocess.run(
        [sys.executable, '-m', 'girokmoji', '--version'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert girokmoji.__version__ in result.stdout
