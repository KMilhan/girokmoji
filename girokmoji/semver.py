from __future__ import annotations

from dataclasses import dataclass
import re

__all__ = ["SemVer"]

# Regular expression from https://semver.org/
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

@dataclass(frozen=True)
class SemVer:
    """Semantic Version 2.0.0."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    @classmethod
    def parse(cls, text: str) -> "SemVer":
        match = _SEMVER_RE.fullmatch(text)
        if not match:
            raise ValueError(f"Invalid semver string: {text}")
        major, minor, patch, pre, build = match.groups()
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=tuple(pre.split(".")) if pre else (),
            build=tuple(build.split(".")) if build else (),
        )

    def bump(self, part: str) -> "SemVer":
        if part == "major":
            return SemVer(self.major + 1, 0, 0)
        if part == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        if part == "patch":
            return SemVer(self.major, self.minor, self.patch + 1)
        raise ValueError(f"Unknown bump part: {part}")

    def __str__(self) -> str:  # pragma: no cover - trivial
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += "-" + ".".join(self.prerelease)
        if self.build:
            base += "+" + ".".join(self.build)
        return base

    def _compare_pre(self, other: "SemVer") -> int:
        if not self.prerelease and not other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
        for a, b in zip(self.prerelease, other.prerelease):
            if a == b:
                continue
            a_num = a.isdigit()
            b_num = b.isdigit()
            if a_num and b_num:
                return -1 if int(a) < int(b) else 1
            if a_num:
                return -1
            if b_num:
                return 1
            return -1 if a < b else 1
        if len(self.prerelease) == len(other.prerelease):
            return 0
        return -1 if len(self.prerelease) < len(other.prerelease) else 1

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        if (self.major, self.minor, self.patch) != (
            other.major,
            other.minor,
            other.patch,
        ):
            return (self.major, self.minor, self.patch) < (
                other.major,
                other.minor,
                other.patch,
            )
        return self._compare_pre(other) < 0

    def __eq__(self, other: object) -> bool:  # pragma: no cover - trivial
        if not isinstance(other, SemVer):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
            and self.build == other.build
        )

    def __hash__(self) -> int:  # pragma: no cover - trivial
        return hash((self.major, self.minor, self.patch, self.prerelease, self.build))
