"""girokmoji package."""

from importlib import metadata

from .changelog import change_log as change_log
from .changelog import github_release_payload as github_release_payload
from .release import auto_release as auto_release

try:  # pragma: no cover - package might not be installed in tests
    __version__ = metadata.version(__package__ or "girokmoji")
except metadata.PackageNotFoundError:  # pragma: no cover - fallback version
    __version__ = "0.5.15"

__all__ = ["change_log", "github_release_payload", "auto_release", "__version__"]
