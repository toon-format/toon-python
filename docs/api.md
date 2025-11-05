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

# With typed options (TypedDict)
from toon_format.types import EncodeOptions
options: EncodeOptions = {"delimiter": "|", "indent": 4, "lengthMarker": "#"}
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

# With options (class)
from toon_format.types import DecodeOptions
decode("  item: value", DecodeOptions(indent=4, strict=False))

# Or use dict
decode("  item: value", {"indent": 4, "strict": False})
```

---

## Options Classes

### `EncodeOptions`

TypedDict for encoding configuration. Use dict syntax to create options.

**Fields:**
- `delimiter` (str, optional): Array value separator
  - `","` - Comma (default)
  - `"\t"` - Tab
  - `"|"` - Pipe
- `indent` (int, optional): Spaces per indentation level (default: `2`)
- `lengthMarker` (Literal["#"] | Literal[False], optional): Prefix for array lengths
  - `False` - No marker (default)
  - `"#"` - Add `#` prefix (e.g., `[#5]`)

**Example:**

```python
from toon_format import encode
from toon_format.types import EncodeOptions

# EncodeOptions is a TypedDict, use dict syntax
options: EncodeOptions = {
    "delimiter": "\t",
    "indent": 4,
    "lengthMarker": "#"
}

data = [{"id": 1}, {"id": 2}]
print(encode(data, options))
# [#2	]{id}:
#     1
#     2
```

---

### `DecodeOptions`

Configuration class for decoding behavior.

**Constructor:**
```python
DecodeOptions(indent=2, strict=True)
```

**Parameters:**
- `indent` (int): Expected spaces per indentation level (default: `2`)
- `strict` (bool): Enable strict validation (default: `True`)

**Note:** Unlike `EncodeOptions` (which is a TypedDict), `DecodeOptions` is a class. You can also pass a plain dict with the same keys to `decode()`.

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

## Utility Functions

### `count_tokens(text, encoding="o200k_base")`

Count tokens in a text string using tiktoken.

**Parameters:**
- `text` (str): The string to tokenize
- `encoding` (str, optional): Tokenizer encoding name (default: `"o200k_base"` for gpt5/gpt5-mini)
  - Other options: `"cl100k_base"` (GPT-3.5), `"p50k_base"` (older models)

**Returns:** `int` - The number of tokens in the text

**Raises:**
- `RuntimeError`: If tiktoken is not installed

**Requirements:**
- Install tiktoken: `uv add tiktoken` or `uv add toon_format[benchmark]`

**Example:**

```python
from toon_format import count_tokens

text = "Hello, world!"
tokens = count_tokens(text)
print(f"Token count: {tokens}")
# Token count: 4
```

---

### `estimate_savings(data, encoding="o200k_base")`

Compare token counts between JSON and TOON formats.

**Parameters:**
- `data` (Any): Python dict or list to compare
- `encoding` (str, optional): Tokenizer encoding name (default: `"o200k_base"`)

**Returns:** `dict` containing:
- `json_tokens` (int): Token count for JSON format
- `toon_tokens` (int): Token count for TOON format
- `savings` (int): Absolute token savings (json_tokens - toon_tokens)
- `savings_percent` (float): Percentage savings

**Example:**

```python
from toon_format import estimate_savings

data = {
    "employees": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
}

result = estimate_savings(data)
print(f"JSON tokens: {result['json_tokens']}")
print(f"TOON tokens: {result['toon_tokens']}")
print(f"Savings: {result['savings_percent']:.1f}%")
# JSON tokens: 45
# TOON tokens: 28
# Savings: 37.8%
```

**Note:** Significant savings are typically achieved with structured data, especially arrays of uniform objects (tabular data).

---

### `compare_formats(data, encoding="o200k_base")`

Generate a formatted comparison table showing JSON vs TOON metrics.

**Parameters:**
- `data` (Any): Python dict or list to compare
- `encoding` (str, optional): Tokenizer encoding name (default: `"o200k_base"`)

**Returns:** `str` - Formatted table as multi-line string showing token counts, character sizes, and savings percentage

**Example:**

```python
from toon_format import compare_formats

data = {
    "users": [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25}
    ]
}

print(compare_formats(data))
# Format Comparison
# ────────────────────────────────────────────────
# Format      Tokens    Size (chars)
# JSON            45           123
# TOON            28            85
# ────────────────────────────────────────────────
# Savings: 17 tokens (37.8%)
```

**Note:** Useful for quick visual comparison during development and optimization.

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
