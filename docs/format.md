# TOON Format Specification

Detailed format rules, syntax, and examples for TOON (Token-Oriented Object Notation).

## Overview

TOON uses indentation-based structure like YAML for nested objects and tabular format like CSV for uniform arrays. This document explains the complete syntax and formatting rules.

---

## Objects

Objects use `key: value` pairs with indentation for nesting.

### Simple Objects

```python
{"name": "Alice", "age": 30, "active": True}
```

```toon
name: Alice
age: 30
active: true
```

### Nested Objects

```python
{
    "user": {
        "name": "Alice",
        "settings": {
            "theme": "dark"
        }
    }
}
```

```toon
user:
  name: Alice
  settings:
    theme: dark
```

### Object Keys

Keys follow identifier rules or must be quoted:

```python
{
    "simple_key": 1,
    "with-dash": 2,
    "123": 3,           # Numeric key
    "with space": 4,    # Spaces require quotes
    "": 5               # Empty key requires quotes
}
```

```toon
simple_key: 1
with-dash: 2
"123": 3
"with space": 4
"": 5
```

---

## Arrays

All arrays include length indicator `[N]` for validation.

### Primitive Arrays

Arrays of primitives use inline format with comma separation:

```python
[1, 2, 3, 4, 5]
```

```toon
[5]: 1,2,3,4,5
```

```python
["alpha", "beta", "gamma"]
```

```toon
[3]: alpha,beta,gamma
```

**Note:** Comma delimiter is hidden in primitive arrays: `[5]:` not `[5,]:`

### Tabular Arrays

Uniform objects with primitive-only fields use CSV-like format:

```python
[
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 25},
    {"id": 3, "name": "Charlie", "age": 35}
]
```

```toon
[3,]{id,name,age}:
  1,Alice,30
  2,Bob,25
  3,Charlie,35
```

**Tabular Format Rules:**
- All objects must have identical keys
- All values must be primitives (no nested objects/arrays)
- Field order in header determines column order
- Delimiter appears in header: `[N,]` or `[N|]` or `[N\t]`

### List Arrays

Non-uniform or nested arrays use list format with `-` markers:

```python
[
    {"name": "Alice"},
    42,
    "hello"
]
```

```toon
[3]:
  - name: Alice
  - 42
  - hello
```

### Nested Arrays

```python
{
    "matrix": [
        [1, 2, 3],
        [4, 5, 6]
    ]
}
```

```toon
matrix[2]:
  - [3]: 1,2,3
  - [3]: 4,5,6
```

### Empty Arrays

```python
{"items": []}
```

```toon
items[0]:
```

---

## Delimiters

Three delimiter options for array values:

### Comma (Default)

```python
encode([1, 2, 3])  # Default delimiter
```

```toon
[3]: 1,2,3
```

For tabular arrays, delimiter shown in header:
```toon
users[2,]{id,name}:
  1,Alice
  2,Bob
```

### Tab

```python
encode([1, 2, 3], {"delimiter": "\t"})
```

```toon
[3	]: 1	2	3
```

Tabular with tab:
```toon
users[2	]{id,name}:
  1	Alice
  2	Bob
```

### Pipe

```python
encode([1, 2, 3], {"delimiter": "|"})
```

```toon
[3|]: 1|2|3
```

Tabular with pipe:
```toon
users[2|]{id,name}:
  1|Alice
  2|Bob
```

---

## String Quoting Rules

Strings are quoted **only when necessary** to avoid ambiguity.

### Unquoted Strings (Safe)

```python
"hello"          # Simple identifier
"hello world"    # Internal spaces OK
"user_name"      # Underscores OK
"hello-world"    # Hyphens OK
```

```toon
hello
hello world
user_name
hello-world
```

### Quoted Strings (Required)

**Empty strings:**
```python
""
```
```toon
""
```

**Reserved keywords:**
```python
"null"
"true"
"false"
```
```toon
"null"
"true"
"false"
```

**Numeric-looking strings:**
```python
"42"
"-3.14"
"1e5"
"0123"  # Leading zero
```
```toon
"42"
"-3.14"
"1e5"
"0123"
```

**Leading/trailing whitespace:**
```python
" hello"
"hello "
" hello "
```
```toon
" hello"
"hello "
" hello "
```

**Structural characters:**
```python
"key: value"     # Colon
"[array]"        # Brackets
"{object}"       # Braces
"- item"         # Leading hyphen
```
```toon
"key: value"
"[array]"
"{object}"
"- item"
```

**Delimiter characters:**
```python
# When using comma delimiter
"a,b"
```
```toon
"a,b"
```

**Control characters:**
```python
"line1\nline2"
"tab\there"
```
```toon
"line1\nline2"
"tab\there"
```

### Escape Sequences

Inside quoted strings:

| Sequence | Meaning |
|----------|---------|
| `\"` | Double quote |
| `\\` | Backslash |
| `\n` | Newline |
| `\r` | Carriage return |
| `\t` | Tab |
| `\uXXXX` | Unicode character (4 hex digits) |

**Example:**

```python
{
    "text": "Hello \"world\"\nNew line",
    "path": "C:\\Users\\Alice"
}
```

```toon
text: "Hello \"world\"\nNew line"
path: "C:\\Users\\Alice"
```

---

## Primitives

### Numbers

**Integers:**
```python
42
-17
0
```

```toon
42
-17
0
```

**Floats:**
```python
3.14
-0.5
0.0
```

```toon
3.14
-0.5
0
```

**Special Numbers:**
- **Scientific notation accepted in decoding:** `1e5`, `-3.14E-2`
- **Encoders must NOT use scientific notation** - always decimal form
- **Negative zero normalized:** `-0.0` → `0`
- **Non-finite values → null:** `Infinity`, `-Infinity`, `NaN` → `null`

**Large integers (>2^53-1):**
```python
9007199254740993  # Exceeds JS safe integer
```

```toon
"9007199254740993"  # Quoted for JS compatibility
```

### Booleans

```python
True   # true in TOON (lowercase)
False  # false in TOON (lowercase)
```

```toon
true
false
```

### Null

```python
None  # null in TOON (lowercase)
```

```toon
null
```

---

## Indentation

Default: 2 spaces per level (configurable)

```python
{
    "level1": {
        "level2": {
            "level3": "value"
        }
    }
}
```

```toon
level1:
  level2:
    level3: value
```

**With 4-space indent:**
```python
encode(data, {"indent": 4})
```

```toon
level1:
    level2:
        level3: value
```

**Strict mode rules:**
- Indentation must be consistent multiples of `indent` value
- Tabs not allowed in indentation
- Mixing spaces and tabs causes errors

---

## Array Length Indicators

All arrays include `[N]` to indicate element count for validation.

### Without Length Marker (Default)

```toon
items[3]: a,b,c
users[2,]{id,name}:
  1,Alice
  2,Bob
```

### With Length Marker (`#`)

```python
encode(data, {"lengthMarker": "#"})
```

```toon
items[#3]: a,b,c
users[#2,]{id,name}:
  1,Alice
  2,Bob
```

The `#` prefix makes length indicators more explicit for validation-focused use cases.

---

## Blank Lines

**Within arrays:** Blank lines are **not allowed** in strict mode

```toon
# ❌ Invalid (blank line in array)
items[3]:
  - a

  - b
  - c
```

```toon
# ✅ Valid (no blank lines)
items[3]:
  - a
  - b
  - c
```

**Between top-level keys:** Blank lines are allowed and ignored

```toon
# ✅ Valid (blank lines between objects)
name: Alice

age: 30
```

---

## Comments

**TOON does not support comments.** The format prioritizes minimal syntax for token efficiency.

If you need to document TOON data, use surrounding markdown or separate documentation files.

---

## Whitespace

### Trailing Whitespace

Trailing whitespace on lines is **allowed** and **ignored**.

### Leading Whitespace in Values

Leading/trailing whitespace in string values requires quoting:

```python
{"text": " value "}
```

```toon
text: " value "
```

---

## Order Preservation

**Object key order** and **array element order** are **always preserved** during encoding and decoding.

```python
from collections import OrderedDict

data = OrderedDict([("z", 1), ("a", 2), ("m", 3)])
toon = encode(data)
```

```toon
z: 1
a: 2
m: 3
```

Decoding preserves order:
```python
decoded = decode(toon)
list(decoded.keys())  # ['z', 'a', 'm']
```

---

## Complete Examples

### Simple Configuration

```python
{
    "app": "myapp",
    "version": "1.0.0",
    "debug": False,
    "port": 8080
}
```

```toon
app: myapp
version: "1.0.0"
debug: false
port: 8080
```

### Nested Structure with Arrays

```python
{
    "metadata": {
        "version": 2,
        "author": "Alice"
    },
    "items": [
        {"id": 1, "name": "Item1", "qty": 10},
        {"id": 2, "name": "Item2", "qty": 5}
    ],
    "tags": ["alpha", "beta", "gamma"]
}
```

```toon
metadata:
  version: 2
  author: Alice
items[2,]{id,name,qty}:
  1,Item1,10
  2,Item2,5
tags[3]: alpha,beta,gamma
```

### Mixed Array Types

```python
{
    "data": [
        {"type": "user", "id": 1},
        {"type": "user", "id": 2, "extra": "field"},  # Non-uniform
        42,
        "hello"
    ]
}
```

```toon
data[4]:
  - type: user
    id: 1
  - type: user
    id: 2
    extra: field
  - 42
  - hello
```

---

## Token Efficiency Comparison

**JSON (177 chars):**
```json
{"users":[{"id":1,"name":"Alice","age":30,"active":true},{"id":2,"name":"Bob","age":25,"active":true},{"id":3,"name":"Charlie","age":35,"active":false}]}
```

**TOON (85 chars, 52% reduction):**
```toon
users[3,]{id,name,age,active}:
  1,Alice,30,true
  2,Bob,25,true
  3,Charlie,35,false
```

---

## See Also

- [API Reference](api.md) - Complete function documentation
- [LLM Integration](llm-integration.md) - Best practices for LLM usage
- [Official Specification](https://github.com/toon-format/spec/blob/main/SPEC.md) - Normative spec
