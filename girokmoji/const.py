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
CATEGORY_SUBTEXTS: dict[CATEGORY, str] = {
    "Critical Changes": "*These are the changes that might keep you up at night.*",
    "Feature and Functional Changes": '*New features that make you go "Wow!"*',
    "Bug Fixes": "*Stubborn bugs have been squashed!*",
    "Performance Improvements": "*Our code is now as energetic as a fresh cup of coffee!*",
    "Lint": "*Polishing code style and eliminating lint warnings!*",
    "Documentation and Comment": "*Documentation and comments are the developer’s conscience.*",
    "Test": "*Tests provide our code with the stability it deserves.*",
    "Code Maintenance and Refactoring": "*Time to tidy up the code and say goodbye to technical debt.*",
    "Dependency, Build, and Configuration": "*From dependency management to build scripts, everything has been updated!*",
    "File and Project Management": "*Managing file moves, removals, and project documentation.*",
    "Internalization, Accessibility, and UI/UX": "*Making the project accessible and appealing to everyone worldwide!*",
    "Miscellaneous / Other Changes": "*A catch-all for changes that don’t quite fit elsewhere.*",
    "Hmm...": "*These changes might seem odd, but somehow they’re endearing.*",
}
SEMVER = Literal["major", "minor", "patch", None]
