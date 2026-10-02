"""Exceptions raised by the decoder."""

from __future__ import annotations

__all__ = ["ToonDecodeError"]


class ToonDecodeError(ValueError):
    """Raised when a TOON document cannot be decoded.

    Subclasses :class:`ValueError`, like :class:`json.JSONDecodeError`, so
    existing ``except ValueError`` handlers keep working.

    Attributes:
        msg: The unformatted error message.
        line: 1-based line number of the offending line, or ``None`` when the
            error is not tied to a line (for example, invalid UTF-8 input).
        source: The offending line as it appears in the document, or ``None``.
    """

    msg: str
    line: int | None
    source: str | None

    def __init__(
        self, msg: str, line: int | None = None, source: str | None = None
    ) -> None:
        self.msg = msg
        self.line = line
        self.source = source
        super().__init__(f"line {line}: {msg}" if line is not None else msg)

    def __reduce__(
        self,
    ) -> tuple[type[ToonDecodeError], tuple[str, int | None, str | None]]:
        return type(self), (self.msg, self.line, self.source)
