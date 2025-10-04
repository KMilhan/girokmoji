class NoGitmojiInMessageError(ValueError):
    """No gitmoji in the message."""


class MessageDoesNotStartWithGitmojiError(NoGitmojiInMessageError):
    """Message does not start with gitmoji."""


class NoSuchGitmojiSupportedError(ValueError):
    """Unexpected gitmoji by girokmoji."""


class NoSuchTagFoundError(IndexError):
    """Unexpected tag name."""


class NotAncestorError(ValueError):
    """Tail is not an ancestor of head while strict-ancestor is set."""
