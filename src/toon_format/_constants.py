"""Constants for TOON format parsing and encoding."""

# Delimiters
COMMA = ","
TAB = "\t"
PIPE = "|"
DEFAULT_DELIMITER = COMMA
DELIMITERS = {"comma": COMMA, "tab": TAB, "pipe": PIPE}

# Structural characters
COLON = ":"
SPACE = " "
OPEN_BRACKET = "["
CLOSE_BRACKET = "]"
OPEN_BRACE = "{"
CLOSE_BRACE = "}"

# List markers
LIST_ITEM_PREFIX = "- "
LIST_ITEM_MARKER = "-"

# Literal values
NULL_LITERAL = "null"
TRUE_LITERAL = "true"
FALSE_LITERAL = "false"

# Escape characters
BACKSLASH = "\\"
DOUBLE_QUOTE = '"'
NEWLINE = "\n"
CARRIAGE_RETURN = "\r"
HASH = "#"
