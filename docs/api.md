# API Reference

Complete API documentation for toon_format Python package.

## Core Functions

### `encode(value, options=None)`

Converts a Python value to TOON format string.

**Parameters:**
- `value` (Any): JSON-serializable Python value (dict, list, primitives, or nested structures)
- `options` (dict | EncodeOptions, optional): Encoding configuration

**Returns:** `str` - TOON-formatted string

**Raises:**
- `ValueError`: If value contains non-normalizable types

**Examples:**

```python
from toon_format import encode

# Simple encoding
encode({"name": "Alice", "age": 30})
# name: Alice
# age: 30

# With options (dict)
encode([1, 2, 3], {"delimiter": "\t"})
# [3	]: 1	2	3

# With typed options
from toon_format.types import EncodeOptions
options = EncodeOptions(delimiter="|", indent=4, lengthMarker="#")
encode([1, 2, 3], options)
# [#3|]: 1|2|3
```

---

### `decode(input_str, options=None)`

Converts a TOON-formatted string back to Python values.

**Parameters:**
- `input_str` (str): TOON-formatted string
- `options` (dict | DecodeOptions, optional): Decoding configuration

**Returns:** `Any` - Python value (dict, list, or primitive)

**Raises:**
- `ToonDecodeError`: On syntax errors, validation failures, or malformed input

**Examples:**

```python
from toon_format import decode

# Simple decoding
decode("name: Alice\nage: 30")
# {'name': 'Alice', 'age': 30}

# Tabular arrays
decode("users[2,]{id,name}:\n  1,Alice\n  2,Bob")
# {'users': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]}

# With options
from toon_format.types import DecodeOptions
decode("  item: value", DecodeOptions(indent=4, strict=False))
```

---

## Options Classes

### `EncodeOptions`

Configuration for encoding behavior.

**Fields:**
- `delimiter` (str): Array value separator
  - `","` - Comma (default)
  - `"\t"` - Tab
  - `"|"` - Pipe
- `indent` (int): Spaces per indentation level (default: `2`)
- `lengthMarker` (str): Prefix for array lengths
  - `""` - No marker (default)
  - `"#"` - Add `#` prefix (e.g., `[#5]`)

**Example:**

```python
from toon_format import encode
from toon_format.types import EncodeOptions

options = EncodeOptions(
    delimiter="\t",
    indent=4,
    lengthMarker="#"
)

data = [{"id": 1}, {"id": 2}]
print(encode(data, options))
# [#2	]{id}:
#     1
#     2
```

---

### `DecodeOptions`

Configuration for decoding behavior.

**Fields:**
- `indent` (int): Expected spaces per indentation level (default: `2`)
- `strict` (bool): Enable strict validation (default: `True`)

**Strict Mode Validation:**

When `strict=True`, the decoder enforces:
- **Indentation**: Must be consistent multiples of `indent` value
- **No tabs**: Tabs in indentation cause errors
- **Array lengths**: Declared length must match actual element count
- **Delimiter consistency**: All rows must use same delimiter as header
- **No blank lines**: Blank lines within arrays are rejected
- **Valid syntax**: Missing colons, unterminated strings, invalid escapes fail

When `strict=False`:
- Lenient indentation (accepts tabs, inconsistent spacing)
- Array length mismatches allowed
- Blank lines tolerated

**Example:**

```python
from toon_format import decode
from toon_format.types import DecodeOptions

# Strict validation (default)
try:
    decode("items[5]: a,b,c", DecodeOptions(strict=True))
except ToonDecodeError as e:
    print(f"Error: {e}")  # Length mismatch: expected 5, got 3

# Lenient parsing
result = decode("items[5]: a,b,c", DecodeOptions(strict=False))
# {'items': ['a', 'b', 'c']}  # Accepts mismatch
```

---

## Error Handling

### `ToonDecodeError`

Exception raised when decoding fails.

**Attributes:**
- `message` (str): Human-readable error description
- `line` (int | None): Line number where error occurred (if applicable)

**Common Error Scenarios:**

```python
from toon_format import decode, ToonDecodeError

# Unterminated string
try:
    decode('text: "unterminated')
except ToonDecodeError as e:
    print(e)  # Unterminated quoted string

# Array length mismatch
try:
    decode("items[3]: a,b")  # Declared 3, provided 2
except ToonDecodeError as e:
    print(e)  # Expected 3 items, but got 2

# Invalid indentation
try:
    decode("outer:\n   inner: value")  # 3 spaces, not multiple of 2
except ToonDecodeError as e:
    print(e)  # Invalid indentation: expected multiple of 2
```

---

## Type Normalization

Non-JSON types are automatically normalized during encoding:

| Python Type | Normalized To | Example |
|-------------|---------------|---------|
| `datetime.datetime` | ISO 8601 string | `"2024-01-15T10:30:00"` |
| `datetime.date` | ISO 8601 date | `"2024-01-15"` |
| `decimal.Decimal` | `float` | `3.14` |
| `tuple` | `list` | `[1, 2, 3]` |
| `set` / `frozenset` | Sorted `list` | `[1, 2, 3]` |
| `float('inf')` | `null` | `null` |
| `float('-inf')` | `null` | `null` |
| `float('nan')` | `null` | `null` |
| Functions / Callables | `null` | `null` |
| `-0.0` | `0` | `0` |

**Example:**

```python
from datetime import datetime, date
from decimal import Decimal

data = {
    "timestamp": datetime(2024, 1, 15, 10, 30),
    "date": date(2024, 1, 15),
    "price": Decimal("19.99"),
    "tags": {"alpha", "beta"},  # set
    "coords": (10, 20),         # tuple
    "infinity": float("inf"),
    "func": lambda x: x
}

toon = encode(data)
# timestamp: "2024-01-15T10:30:00"
# date: "2024-01-15"
# price: 19.99
# tags[2]: alpha,beta
# coords[2]: 10,20
# infinity: null
# func: null
```

---

## Advanced Usage

### Working with Large Integers

Integers larger than 2^53-1 are converted to strings for JavaScript compatibility:

```python
encode({"bigInt": 9007199254740992})
# bigInt: "9007199254740992"
```

### Custom Delimiters

Use different delimiters based on your data:

```python
# Comma (best for general use)
encode([1, 2, 3])
# [3]: 1,2,3

# Tab (for data with commas)
encode(["a,b", "c,d"], {"delimiter": "\t"})
# [2	]: a,b	c,d

# Pipe (alternative)
encode([1, 2, 3], {"delimiter": "|"})
# [3|]: 1|2|3
```

### Length Markers

Add `#` prefix for explicit length indication:

```python
users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

# Without marker
encode(users)
# [2,]{id,name}:
#   1,Alice
#   2,Bob

# With marker
encode(users, {"lengthMarker": "#"})
# [#2,]{id,name}:
#   1,Alice
#   2,Bob
```

### Zero Indentation

Use `indent=0` for minimal whitespace (not recommended for readability):

```python
encode({"outer": {"inner": 1}}, {"indent": 0})
# outer:
#  inner: 1
```

---

## Type Hints

The package includes comprehensive type hints for static analysis:

```python
from typing import Any, Dict, List, Union
from toon_format import encode, decode
from toon_format.types import EncodeOptions, DecodeOptions, JsonValue

# Type-safe usage
data: Dict[str, Any] = {"key": "value"}
options: EncodeOptions = EncodeOptions(delimiter=",")
result: str = encode(data, options)

decoded: JsonValue = decode(result)
```

---

## Performance Considerations

- **Caching**: The encoder caches indent strings for performance
- **Large arrays**: Tabular format is most efficient for uniform object arrays
- **Validation**: Disable strict mode (`strict=False`) for lenient parsing of untrusted input
- **Memory**: Decode operations are memory-efficient, processing line-by-line

---

## See Also

- [Format Specification](format.md) - Detailed format rules and examples
- [LLM Integration](llm-integration.md) - Best practices for using TOON with LLMs
- [TOON Specification](https://github.com/toon-format/spec) - Official specification
