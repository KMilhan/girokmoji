from typing import Literal

CATEGORY = Literal[
    "Critical Changes",
    "Feature and Functional Changes",
    "Bug Fixes",
    "Performance Improvements",
    "Lint",
    "Documentation and Comment",
    "Test",
    "Code Maintenance and Refactoring",
    "Dependency, Build, and Configuration",
    "File and Project Management",
    "Internalization, Accessibility, and UI/UX",
    "Miscellaneous / Other Changes",
    "Hmm...",
]
category_order: list[CATEGORY] = [
    "Critical Changes",
    "Feature and Functional Changes",
    "Bug Fixes",
    "Performance Improvements",
    "Lint",
    "Documentation and Comment",
    "Test",
    "Code Maintenance and Refactoring",
    "Dependency, Build, and Configuration",
    "File and Project Management",
    "Internalization, Accessibility, and UI/UX",
    "Miscellaneous / Other Changes",
    "Hmm...",
]
SEMVER = Literal["major", "minor", "patch", None]
