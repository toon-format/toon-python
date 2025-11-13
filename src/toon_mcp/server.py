"""TOON MCP Server - FastMCP server for TOON format encoding and decoding."""

from typing import Any

from fastmcp import FastMCP

# Import from the local toon_format package
from toon_format import decode, encode
from toon_format.types import DecodeOptions, EncodeOptions

# Create FastMCP server instance
mcp = FastMCP(
    name="toon-mcp-server",
    version="1.0.0",
)


@mcp.tool()
def toon_encode(
    data: Any,
    indent: int = 2,
    delimiter: str = ",",
) -> str:
    """
    Encode JSON data into TOON format.

    TOON (Token-Oriented Object Notation) is a compact format designed for LLM
    prompts with reduced token usage (typically 30-60% fewer tokens than JSON
    on large uniform arrays).

    Args:
        data: The JSON data to encode into TOON format (objects, arrays, primitives)
        indent: Number of spaces per indentation level (default: 2)
        delimiter: Delimiter for array values - comma (','), tab ('\\t'), or pipe ('|')

    Returns:
        TOON formatted string

    Examples:
        >>> toon_encode({"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]})
        'users[2]{id,name}:\\n  1,Alice\\n  2,Bob'

        >>> toon_encode({"items": ["a", "b", "c"]})
        'items[3]: a,b,c'

        >>> toon_encode({"id": 123, "name": "Ada", "active": True})
        'id: 123\\nname: Ada\\nactive: true'
    """
    options: EncodeOptions = {
        "indent": indent,
        "delimiter": delimiter,
    }

    return encode(data, options)


@mcp.tool()
def toon_decode(
    toon_string: str,
    indent: int = 2,
    strict: bool = True,
) -> dict[str, Any] | list[Any] | str | int | float | bool | None:
    """
    Decode TOON format string back into JSON data.

    Args:
        toon_string: The TOON formatted string to decode
        indent: Expected number of spaces per indentation level (default: 2)
        strict: Enable strict validation during decoding (default: True)

    Returns:
        Decoded data as Python objects (dict, list, str, int, float, bool, or None)

    Examples:
        >>> toon_decode('users[2]{id,name}:\\n  1,Alice\\n  2,Bob')
        {'users': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]}

        >>> toon_decode('items[3]: a,b,c')
        {'items': ['a', 'b', 'c']}

        >>> toon_decode('id: 123\\nname: Ada\\nactive: true')
        {'id': 123, 'name': 'Ada', 'active': True}
    """
    options = DecodeOptions(indent=indent, strict=strict)
    return decode(toon_string, options)


def main():
    """Run the TOON MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
