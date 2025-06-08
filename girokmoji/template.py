from dataclasses import dataclass
from string import Template
from typing import ClassVar

from girokmoji.const import CATEGORY


class SupportTemplate:
    markdown_template: ClassVar[str]

    @property
    def markdown(self):
        raise NotImplementedError


@dataclass
class Head(SupportTemplate):
    project_name: str
    version: str
    subtext: str
    release_date: str


@dataclass
class CategorySection(SupportTemplate):
    category: CATEGORY
    subtext: str


@dataclass
class Entry(SupportTemplate):
    emoji: str
    gitmoji_description: str
    commit_description: str
    commit_hash: str


@dataclass
class Separator(SupportTemplate):
    pass


class DefaultHead(Head):
    markdown_template = """
# 🚀 **$project_name** Release Changelog $version

$subtext

**Release Date:** $release_date

"""

    @property
    def markdown(self):
        return Template(self.markdown_template).substitute(
            project_name=self.project_name,
            version=self.version,
            subtext=self.subtext,
            release_date=self.release_date,
        )


class DefaultCategorySection(CategorySection):
    markdown_template: ClassVar[str] = """
## $category

*$subtext*

"""

    @property
    def markdown(self):
        return Template(self.markdown_template).substitute(
            category=self.category,
            subtext=self.subtext,
        )


class DefaultEntry(Entry):
    markdown_template: ClassVar[str] = (
        "- **$emoji $gitmoji_description**: [*$commit_description*](../../commit/$commit_hash)\n"
    )

    @property
    def markdown(self):
        return Template(self.markdown_template).substitute(
            emoji=self.emoji,
            gitmoji_description=self.gitmoji_description,
            commit_description=self.commit_description,
            commit_hash=self.commit_hash,
        )


@dataclass
class EntryGroupHeader(SupportTemplate):
    emoji: str
    gitmoji_description: str


class DefaultEntryGroupHeader(EntryGroupHeader):
    markdown_template: ClassVar[str] = "- **$emoji $gitmoji_description**\n"

    @property
    def markdown(self):
        return Template(self.markdown_template).substitute(
            emoji=self.emoji,
            gitmoji_description=self.gitmoji_description,
        )


@dataclass
class EntrySubItem(SupportTemplate):
    commit_description: str
    commit_hash: str


class DefaultEntrySubItem(EntrySubItem):
    markdown_template: ClassVar[str] = (
        "  - [*$commit_description*](../../commit/$commit_hash)\n"
    )

    @property
    def markdown(self):
        return Template(self.markdown_template).substitute(
            commit_description=self.commit_description,
            commit_hash=self.commit_hash,
        )


class DefaultSeparator(Separator):
    markdown_template: ClassVar[str] = """
---

"""

    @property
    def markdown(self):
        return Template(self.markdown_template).substitute()


HEAD = DefaultHead
CATEGORY_SECTION = DefaultCategorySection
ENTRY = DefaultEntry
ENTRY_GROUP_HEADER = DefaultEntryGroupHeader
ENTRY_SUBITEM = DefaultEntrySubItem
SEPARATOR = DefaultSeparator
