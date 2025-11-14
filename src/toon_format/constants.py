# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Constants for TOON format encoding and decoding.

Defines all string literals, characters, and configuration values used throughout
the TOON implementation. Centralizes magic values for maintainability.
"""

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .types import Delimiter

# region List markers
LIST_ITEM_MARKER = "-"
LIST_ITEM_PREFIX = "- "
# endregion

# region Structural characters
COMMA: "Delimiter" = ","
COLON = ":"
SPACE = " "
PIPE: "Delimiter" = "|"
# endregion

# region Brackets and braces
OPEN_BRACKET = "["
CLOSE_BRACKET = "]"
OPEN_BRACE = "{"
CLOSE_BRACE = "}"
# endregion

# region Literals
NULL_LITERAL = "null"
TRUE_LITERAL = "true"
FALSE_LITERAL = "false"
# endregion

# region Escape characters
BACKSLASH = "\\"
DOUBLE_QUOTE = '"'
NEWLINE = "\n"
CARRIAGE_RETURN = "\r"
TAB: "Delimiter" = "\t"
# endregion

# region Delimiters
DELIMITERS: Dict[str, "Delimiter"] = {
    "comma": COMMA,
    "tab": TAB,
    "pipe": PIPE,
}

DEFAULT_DELIMITER: "Delimiter" = DELIMITERS["comma"]
# endregion

# region Regex patterns
# Pattern strings are compiled in modules that use them
STRUCTURAL_CHARS_REGEX = r"[\[\]{}]"
CONTROL_CHARS_REGEX = r"[\n\r\t]"
NUMERIC_REGEX = r"^-?\d+(?:\.\d+)?(?:e[+-]?\d+)?$"
OCTAL_REGEX = r"^0\d+$"
VALID_KEY_REGEX = r"^[A-Z_][\w.]*$"
HEADER_LENGTH_REGEX = r"^#?(\d+)([\|\t])?$"
INTEGER_REGEX = r"^-?\d+$"
# endregion

# region Escape sequence maps
ESCAPE_SEQUENCES = {
    BACKSLASH: "\\\\",
    DOUBLE_QUOTE: '\\"',
    NEWLINE: "\\n",
    CARRIAGE_RETURN: "\\r",
    TAB: "\\t",
}

UNESCAPE_SEQUENCES = {
    "n": NEWLINE,
    "r": CARRIAGE_RETURN,
    "t": TAB,
    "\\": BACKSLASH,
    '"': DOUBLE_QUOTE,
}
# endregion
