# TOON Format for Python

[![PyPI version](https://img.shields.io/pypi/v/toon-format.svg)](https://pypi.org/project/toon-format/)
[![Python versions](https://img.shields.io/pypi/pyversions/toon-format.svg)](https://pypi.org/project/toon-format/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

**Token-Oriented Object Notation** is a compact, human-readable format designed for passing structured data to Large Language Models with significantly reduced token usage.

## Installation

```bash
pip install toon-format
```

Or using `uv`:

```bash
uv add toon-format
```

## Quick Start

```python
from toon_format import encode, decode

# Encode Python data to TOON format
data = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"}
    ]
}

toon_string = encode(data)
print(toon_string)
# users[2]{id,name,role}:
#   1,Alice,admin
#   2,Bob,user

# Decode TOON format back to Python
decoded = decode(toon_string)
assert decoded == data
```

## Features

- ✅ **Full TOON 1.3 specification support**
- ✅ **Encoder**: Convert Python objects/arrays to TOON format
- ✅ **Decoder**: Parse TOON format back to Python data structures
- ✅ **Strict mode validation**: Enforce array length and structure constraints
- ✅ **Flexible encoding options**: Custom indentation, delimiters, and length markers
- ✅ **Type-safe**: Full type hints and mypy support

## Examples

### Encoding Objects

```python
from toon_format import encode

# Simple object
encode({"id": 123, "name": "Alice", "active": True})
# 'id: 123\nname: Alice\nactive: true'

# Nested objects
encode({
    "user": {
        "id": 123,
        "address": {"city": "NYC", "zip": 10001}
    }
})
# 'user:\n  id: 123\n  address:\n    city: NYC\n    zip: 10001'
```

### Encoding Arrays

```python
# Primitive arrays (inline)
encode({"tags": ["foo", "bar", "baz"]})
# 'tags[3]: foo,bar,baz'

# Tabular arrays (uniform objects)
encode({
    "items": [
        {"sku": "A1", "qty": 2, "price": 9.99},
        {"sku": "B2", "qty": 1, "price": 14.5}
    ]
})
# 'items[2]{sku,qty,price}:\n  A1,2,9.99\n  B2,1,14.5'

# Root-level arrays
encode([1, 2, 3])
# '[3]: 1,2,3'
```

### Decoding

```python
from toon_format import decode

# Decode tabular array
decode("items[2]{sku,qty}:\n  A1,2\n  B2,1")
# {'items': [{'sku': 'A1', 'qty': 2}, {'sku': 'B2', 'qty': 1}]}

# Decode primitive array
decode("tags[3]: foo,bar,baz")
# {'tags': ['foo', 'bar', 'baz']}

# Decode root array
decode("[3]: 1,2,3")
# [1, 2, 3]
```

### Encoding Options

```python
# Custom delimiter (tab)
encode({"tags": ["foo", "bar"]}, {"delimiter": "\t"})
# 'tags[3\t]: foo\tbar'

# Length marker
encode({"tags": ["foo", "bar"]}, {"length_marker": "#"})
# 'tags[#2]: foo,bar'

# Custom indentation
encode({"a": {"b": 1}}, {"indent": 4})
# 'a:\n    b: 1'
```

### Decoding Options

```python
# Strict mode (default: True)
# Validates array lengths and structure
decode("items[2]:\n  - 1\n  - 2", {"strict": True})

# Non-strict mode (allows extra items)
decode("items[2]:\n  - 1\n  - 2\n  - 3", {"strict": False})
# {'items': [1, 2]}

# Custom indent size
decode("key:\n    nested: value", {"indent": 4})
```

## API Reference

### `encode(value, options=None)`

Convert a Python value to TOON format.

**Parameters:**
- `value`: Any JSON-serializable value (object, array, primitive, or nested)
- `options`: Optional `EncodeOptions` dict:
  - `indent`: Number of spaces per indentation level (default: 2)
  - `delimiter`: Delimiter for arrays (`","`, `"\t"`, or `"|"`, default: `","`)
  - `length_marker`: Optional marker to prefix array lengths (`"#"` or `False`, default: `False`)

**Returns:** `str` - TOON-formatted string

**Raises:**
- `TypeError`: If value cannot be normalized

### `decode(input_str, options=None)`

Convert a TOON-formatted string to a Python value.

**Parameters:**
- `input_str`: A TOON-formatted string to parse
- `options`: Optional `DecodeOptions` dict:
  - `indent`: Expected number of spaces per indentation level (default: 2)
  - `strict`: Enable strict validation (default: `True`)

**Returns:** `dict | list | str | int | float | bool | None` - Parsed Python value

**Raises:**
- `SyntaxError`: If input has syntax errors (invalid escapes, missing colons, etc.)
- `ValueError`: If input is malformed (when `strict=True`, e.g., count mismatches)
- `TypeError`: If input is empty

## Type Definitions

The package exports `EncodeOptions` and `DecodeOptions` TypedDicts for type hints:

```python
from toon_format import EncodeOptions, DecodeOptions

def process_data(data: dict, encode_opts: EncodeOptions | None = None):
    return encode(data, encode_opts)
```

## Resources

- [TOON Specification](https://github.com/toon-format/spec/blob/main/SPEC.md)
- [Main Repository](https://github.com/toon-format/toon)
- [Benchmarks & Performance](https://github.com/toon-format/toon#benchmarks)
- [Other Language Implementations](https://github.com/toon-format/toon#other-implementations)

## Contributing

Contributions are welcome! This implementation follows the [TOON specification v1.3](https://github.com/toon-format/spec/blob/main/SPEC.md).

### Development Setup

```bash
# Clone the repository
git clone https://github.com/toon-format/toon-python.git
cd toon-python

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run type checking
uv run mypy src/

# Run linting
uv run ruff check src/ tests/
```

## License

MIT License © 2025-PRESENT [Johann Schopplich](https://github.com/johannschopplich)
