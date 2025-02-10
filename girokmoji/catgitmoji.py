"""
Gitmoji feature parser and data structure.

Gitmoji license is provided in GITMOJI_LICENSE file. All copyright belongs to Carlos Cuesta and provided by MIT license.
"""

from dataclasses import dataclass
from functools import lru_cache

from girokmoji.const import SEMVER, CATEGORY
from girokmoji.exception import NoSuchGitmojiSupportedError


@dataclass
class CatGitmoji:
    emoji: str
    entity: str
    code: str
    description: str
    category: CATEGORY
    semver: SEMVER


RAW = [
    CatGitmoji(
        "🎨",
        "&#x1f3a8;",
        ":art:",
        "Improve structure / format of the code.",
        "Code Maintenance and Refactoring",
        None,
    ),
    CatGitmoji(
        "⚡️",
        "&#x26a1;",
        ":zap:",
        "Improve performance.",
        "Performance Improvements",
        "patch",
    ),
    CatGitmoji(
        "🔥",
        "&#x1f525;",
        ":fire:",
        "Remove code or files.",
        "File and Project Management",
        None,
    ),
    CatGitmoji("🐛", "&#x1f41b;", ":bug:", "Fix a bug.", "Bug Fixes", "patch"),
    CatGitmoji(
        "🚑️",
        "&#128657;",
        ":ambulance:",
        "Critical hotfix.",
        "Critical Changes",
        "patch",
    ),
    CatGitmoji(
        "✨",
        "&#x2728;",
        ":sparkles:",
        "Introduce new features.",
        "Feature and Functional Changes",
        "minor",
    ),
    CatGitmoji(
        "📝",
        "&#x1f4dd;",
        ":memo:",
        "Add or update documentation.",
        "Documentation and Comment",
        None,
    ),
    CatGitmoji(
        "🚀",
        "&#x1f680;",
        ":rocket:",
        "Deploy stuff.",
        "Feature and Functional Changes",
        None,
    ),
    CatGitmoji(
        "💄",
        "&#ff99cc;",
        ":lipstick:",
        "Add or update the UI and style files.",
        "Internalization, Accessibility, and UI/UX",
        "patch",
    ),
    CatGitmoji(
        "🎉",
        "&#127881;",
        ":tada:",
        "Begin a project.",
        "Feature and Functional Changes",
        None,
    ),
    CatGitmoji(
        "✅",
        "&#x2705;",
        ":white_check_mark:",
        "Add, update, or pass tests.",
        "Test",
        None,
    ),
    CatGitmoji(
        "🔒️",
        "&#x1f512;",
        ":lock:",
        "Fix security or privacy issues.",
        "Critical Changes",
        "patch",
    ),
    CatGitmoji(
        "🔐",
        "&#x1f510;",
        ":closed_lock_with_key:",
        "Add or update secrets.",
        "Critical Changes",
        None,
    ),
    CatGitmoji(
        "🔖",
        "&#x1f516;",
        ":bookmark:",
        "Release / Version tags.",
        "Feature and Functional Changes",
        None,
    ),
    CatGitmoji(
        "🚨",
        "&#x1f6a8;",
        ":rotating_light:",
        "Fix compiler / linter warnings.",
        "Lint",
        None,
    ),
    CatGitmoji(
        "🚧",
        "&#x1f6a7;",
        ":construction:",
        "Work in progress.",
        "Miscellaneous / Other Changes",
        None,
    ),
    CatGitmoji(
        "💚",
        "&#x1f49a;",
        ":green_heart:",
        "Fix CI Build.",
        "Dependency, Build, and Configuration",
        None,
    ),
    CatGitmoji(
        "⬇️",
        "⬇️",
        ":arrow_down:",
        "Downgrade dependencies.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "⬆️",
        "⬆️",
        ":arrow_up:",
        "Upgrade dependencies.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "📌",
        "&#x1F4CC;",
        ":pushpin:",
        "Pin dependencies to specific versions.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "👷",
        "&#x1f477;",
        ":construction_worker:",
        "Add or update CI build system.",
        "Dependency, Build, and Configuration",
        None,
    ),
    CatGitmoji(
        "📈",
        "&#x1F4C8;",
        ":chart_with_upwards_trend:",
        "Add or update analytics or track code.",
        "Miscellaneous / Other Changes",
        None,
    ),
    CatGitmoji(
        "♻️",
        "&#x267b;",
        ":recycle:",
        "Refactor code.",
        "Code Maintenance and Refactoring",
        None,
    ),
    CatGitmoji(
        "➕",
        "&#10133;",
        ":heavy_plus_sign:",
        "Add a dependency.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "➖",
        "&#10134;",
        ":heavy_minus_sign:",
        "Remove a dependency.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "🔧",
        "&#x1f527;",
        ":wrench:",
        "Add or update configuration files.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "🔨",
        "&#128296;",
        ":hammer:",
        "Add or update development scripts.",
        "Dependency, Build, and Configuration",
        None,
    ),
    CatGitmoji(
        "🌐",
        "&#127760;",
        ":globe_with_meridians:",
        "Internationalization and localization.",
        "Internalization, Accessibility, and UI/UX",
        "patch",
    ),
    CatGitmoji(
        "✏️", "&#59161;", ":pencil2:", "Fix typos.", "Documentation and Comment", "patch"
    ),
    CatGitmoji(
        "💩",
        "&#58613;",
        ":poop:",
        "Write bad code that needs to be improved.",
        "Code Maintenance and Refactoring",
        None,
    ),
    CatGitmoji(
        "⏪️",
        "&#9194;",
        ":rewind:",
        "Revert changes.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "🔀",
        "&#128256;",
        ":twisted_rightwards_arrows:",
        "Merge branches.",
        "Miscellaneous / Other Changes",
        None,
    ),
    CatGitmoji(
        "📦️",
        "&#1F4E6;",
        ":package:",
        "Add or update compiled files or packages.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "👽️",
        "&#1F47D;",
        ":alien:",
        "Update code due to external API changes.",
        "Dependency, Build, and Configuration",
        "patch",
    ),
    CatGitmoji(
        "🚚",
        "&#1F69A;",
        ":truck:",
        "Move or rename resources (e.g.: files, paths, routes).",
        "File and Project Management",
        None,
    ),
    CatGitmoji(
        "📄",
        "&#1F4C4;",
        ":page_facing_up:",
        "Add or update license.",
        "File and Project Management",
        None,
    ),
    CatGitmoji(
        "💥",
        "&#x1f4a5;",
        ":boom:",
        "Introduce breaking changes.",
        "Critical Changes",
        "major",
    ),
    CatGitmoji(
        "🍱",
        "&#1F371",
        ":bento:",
        "Add or update assets.",
        "Miscellaneous / Other Changes",
        "patch",
    ),
    CatGitmoji(
        "♿️",
        "&#9855;",
        ":wheelchair:",
        "Improve accessibility.",
        "Internalization, Accessibility, and UI/UX",
        "patch",
    ),
    CatGitmoji(
        "💡",
        "&#128161;",
        ":bulb:",
        "Add or update comments in source code.",
        "Internalization, Accessibility, and UI/UX",
        "patch",
    ),
    CatGitmoji("🍻", "&#x1f37b;", ":beers:", "Write code drunkenly.", "Hmm...", None),
    CatGitmoji(
        "💬",
        "&#128172;",
        ":speech_balloon:",
        "Add or update text and literals.",
        "Miscellaneous / Other Changes",
        "patch",
    ),
    CatGitmoji(
        "🗃️",
        "&#128451;",
        ":card_file_box:",
        "Perform database related changes.",
        "Miscellaneous / Other Changes",
        "patch",
    ),
    CatGitmoji(
        "🔊",
        "&#128266;",
        ":loud_sound:",
        "Add or update logs.",
        "Miscellaneous / Other Changes",
        None,
    ),
    CatGitmoji(
        "🔇",
        "&#128263;",
        ":mute:",
        "Remove logs.",
        "Miscellaneous / Other Changes",
        None,
    ),
    CatGitmoji(
        "👥",
        "&#128101;",
        ":busts_in_silhouette:",
        "Add or update contributor(s).",
        "File and Project Management",
        None,
    ),
    CatGitmoji(
        "🚸",
        "&#128696;",
        ":children_crossing:",
        "Improve user experience / usability.",
        "Internalization, Accessibility, and UI/UX",
        "patch",
    ),
    CatGitmoji(
        "🏗️",
        "&#1f3d7;",
        ":building_construction:",
        "Make architectural changes.",
        "Dependency, Build, and Configuration",
        None,
    ),
    CatGitmoji(
        "📱",
        "&#128241;",
        ":iphone:",
        "Work on responsive design.",
        "Miscellaneous / Other Changes",
        "patch",
    ),
    CatGitmoji("🤡", "&#129313;", ":clown_face:", "Mock things.", "Hmm...", None),
    CatGitmoji(
        "🥚", "&#129370;", ":egg:", "Add or update an easter egg.", "Hmm...", "patch"
    ),
    CatGitmoji(
        "🙈",
        "&#8bdfe7;",
        ":see_no_evil:",
        "Add or update a .gitignore file.",
        "File and Project Management",
        None,
    ),
    CatGitmoji(
        "📸",
        "&#128248;",
        ":camera_flash:",
        "Add or update snapshots.",
        "Dependency, Build, and Configuration",
        None,
    ),
    CatGitmoji("⚗️", "&#x2697;", ":alembic:", "Perform experiments.", "Hmm...", "patch"),
    CatGitmoji(
        "🔍️", "&#128269;", ":mag:", "Improve SEO.", "Performance Improvements", "patch"
    ),
    CatGitmoji(
        "🏷️",
        "&#127991;",
        ":label:",
        "Add or update types.",
        "Code Maintenance and Refactoring",
        "patch",
    ),
    CatGitmoji(
        "🌱",
        "&#127793;",
        ":seedling:",
        "Add or update seed files.",
        "Critical Changes",
        None,
    ),
    CatGitmoji(
        "🚩",
        "&#x1F6A9;",
        ":triangular_flag_on_post:",
        "Add, update, or remove feature flags.",
        "Feature and Functional Changes",
        "patch",
    ),
    CatGitmoji("🥅", "&#x1F945;", ":goal_net:", "Catch errors.", "Bug Fixes", "patch"),
    CatGitmoji(
        "💫",
        "&#x1f4ab;",
        ":dizzy:",
        "Add or update animations and transitions.",
        "Bug Fixes",
        "patch",
    ),
    CatGitmoji(
        "🗑️",
        "&#x1F5D1;",
        ":wastebasket:",
        "Deprecate code that needs to be cleaned up.",
        "Code Maintenance and Refactoring",
        "patch",
    ),
    CatGitmoji(
        "🛂",
        "&#x1F6C2;",
        ":passport_control:",
        "Work on code related to authorization, roles and permissions.",
        "Miscellaneous / Other Changes",
        "patch",
    ),
    CatGitmoji(
        "🩹",
        "&#x1FA79;",
        ":adhesive_bandage:",
        "Simple fix for a non-critical issue.",
        "Bug Fixes",
        "patch",
    ),
    CatGitmoji(
        "🧐",
        "&#x1F9D0;",
        ":monocle_face:",
        "Data exploration/inspection.",
        "Miscellaneous / Other Changes",
        "patch",
    ),
    CatGitmoji(
        "⚰️",
        "&#x26B0;",
        ":coffin:",
        "Remove dead code.",
        "Code Maintenance and Refactoring",
        None,
    ),
    CatGitmoji("🧪", "&#x1F9EA;", ":test_tube:", "Add a failing test.", "Test", None),
    CatGitmoji(
        "👔",
        "&#128084;",
        ":necktie:",
        "Add or update business logic.",
        "Feature and Functional Changes",
        "minor",
    ),
    CatGitmoji(
        "🩺",
        "&#x1FA7A;",
        ":stethoscope:",
        "Add or update healthcheck.",
        "Feature and Functional Changes",
        "patch",
    ),
    CatGitmoji(
        "🧱",
        "&#x1f9f1;",
        ":bricks:",
        "Infrastructure related changes.",
        "Performance Improvements",
        "patch",
    ),
    CatGitmoji(
        "🧑‍💻",
        "&#129489;&#8205;&#128187;",
        ":technologist:",
        "Improve developer experience.",
        "Code Maintenance and Refactoring",
        None,
    ),
    CatGitmoji(
        "💸",
        "&#x1F4B8;",
        ":money_with_wings:",
        "Add sponsorships or money related infrastructure.",
        "File and Project Management",
        None,
    ),
    CatGitmoji(
        "🧵",
        "&#x1F9F5;",
        ":thread:",
        "Add or update code related to multithreading or concurrency.",
        "Performance Improvements",
        "patch",
    ),
    CatGitmoji(
        "🦺",
        "&#x1F9BA;",
        ":safety_vest:",
        "Add or update code related to validation.",
        "Bug Fixes",
        "minor",
    ),
]


@lru_cache(maxsize=1)
def by_code() -> dict[str, CatGitmoji]:
    res = {}
    for gitmoji in RAW:
        res[gitmoji.code] = gitmoji

    return res


@lru_cache(maxsize=1)
def by_entity() -> dict[str, CatGitmoji]:
    res = {}
    for gitmoji in RAW:
        res[gitmoji.entity] = gitmoji

    return res


@lru_cache(maxsize=1)
def by_emoji() -> dict[str, CatGitmoji]:
    res = {}
    for gitmoji in RAW:
        res[gitmoji.emoji] = gitmoji

    return res


@lru_cache(maxsize=1)
def by_gitmoji() -> dict[str, CatGitmoji]:
    return by_code() | by_entity() | by_emoji()


@lru_cache(maxsize=1)
def any_to_catmoji(to_find: str) -> CatGitmoji:
    for gitmoji in by_gitmoji():
        if to_find == gitmoji:
            return by_gitmoji()[gitmoji]

    raise NoSuchGitmojiSupportedError
