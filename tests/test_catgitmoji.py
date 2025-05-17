import pytest

from girokmoji import catgitmoji


def test_lookup_functions():
    first = catgitmoji.RAW[0]
    assert catgitmoji.by_code()[first.code] is first
    assert catgitmoji.by_entity()[first.entity] is first
    assert catgitmoji.by_emoji()[first.emoji] is first
    assert catgitmoji.by_gitmoji()[first.code] is first
    assert catgitmoji.any_to_catmoji(first.code) is first
    with pytest.raises(catgitmoji.NoSuchGitmojiSupportedError):
        catgitmoji.any_to_catmoji(":unknown:")
