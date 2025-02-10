class NoGitmojiInMessageError(ValueError):
    """No gitmoji in the message."""


class MessageDoesNotStartWithGitmojiError(NoGitmojiInMessageError):
    """Message does not start with gitmoji."""


class NoSuchGitmojiSupportedError(ValueError):
    """Unexpected gitmoji by girokmoji."""


class NoSuchTagFoundError(IndexError):
    """Unexpected tag name."""
