# TOON for Python

[![CI](https://github.com/toon-format/toon-python/actions/workflows/ci.yml/badge.svg)](https://github.com/toon-format/toon-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/toon-format.svg)](https://pypi.org/project/toon-format/)
[![Python versions](https://img.shields.io/pypi/pyversions/toon-format.svg)](https://pypi.org/project/toon-format/)
[![TOON spec](https://img.shields.io/badge/TOON%20spec-4.1-blue)](https://github.com/toon-format/spec/blob/main/SPEC.md)
[![Documentation](https://readthedocs.org/projects/toon-format/badge/?version=stable)](https://toon-format.readthedocs.io/en/stable/)

The official Python implementation of **TOON** (Token-Oriented Object Notation):
a compact, human-readable encoding of the JSON data model, designed to save
tokens in LLM prompts. Keep working with dictionaries and lists in your code,
and encode them as TOON only where a model reads them.

- **Complete**: implements [TOON specification 4.1](https://github.com/toon-format/spec/blob/main/SPEC.md)
  and passes every official conformance fixture.
- **Familiar**: `dumps`, `dump`, `loads`, and `load`, like the `json` module,
  plus [`encode` and `decode`](#encode-and-decode), the names of the
  TypeScript reference implementation.
- **Lossless**: `loads(dumps(data)) == data` for every JSON-compatible value.
- **Pure Python**, no dependencies, fully typed, Python 3.10+.

## Installation

```bash
pip install toon-format
# or
uv add toon-format
```

The module is `toon_format`. Install `toon-format[pydantic]` for the Pydantic
integration.

## Quick start

```python
import toon_format

data = {
    "context": {"task": "Our favorite hikes together", "location": "Boulder"},
    "friends": ["ana", "luis", "sam"],
    "hikes": [
        {"id": 1, "name": "Blue Lake Trail", "distanceKm": 7.5, "wasSunny": True},
        {"id": 2, "name": "Ridge Overlook", "distanceKm": 9.2, "wasSunny": False},
    ],
}

text = toon_format.dumps(data)
print(text)
```

```
context:
  task: Our favorite hikes together
  location: Boulder
friends[3]: ana,luis,sam
hikes[2]{id,name,distanceKm,wasSunny}:
  1,Blue Lake Trail,7.5,true
  2,Ridge Overlook,9.2,false
```

```python
assert toon_format.loads(text) == data
```

Keys of uniform arrays are written once, as a header, and each object becomes
a row. With OpenAI's `o200k_base` tokenizer, this document takes 65 tokens,
against 76 for compact JSON and 130 for indented JSON. The saving grows with
the number of rows: 100 uniform records take 38% fewer tokens than compact
JSON. Deeply nested or irregular data gains less.

## Usage

### Options

Encoding and decoding follow the `json` module, with the same keyword
arguments where they apply:

```python
toon_format.dumps(data, delimiter="\t")  # tabs often tokenize better than commas
toon_format.dumps(data, default=str)  # fallback for unsupported types
toon_format.loads(text, parse_float=Decimal)  # same hooks as json.loads
toon_format.loads(llm_output, strict=False)  # tolerate wrong counts and indentation
```

### Errors

Invalid documents raise `toon_format.ToonDecodeError`, a `ValueError` that
carries the 1-based `line` and the `source` line of the error:

```python
try:
    toon_format.loads("a: 1\ntags[3]: a,b")
except toon_format.ToonDecodeError as exc:
    print(exc.line, exc.source)  # 2 tags[3]: a,b
    print(exc)  # line 2: Declared length 3 but found 2
```

### `encode` and `decode`

`encode` and `decode` are the names used by the TypeScript reference
implementation, [`@toon-format/toon`](https://www.npmjs.com/package/@toon-format/toon),
and by the other TOON implementations. Here they are aliases of `dumps` and
`loads`, so code and examples carry over from one language to the other:

```python
from toon_format import decode, encode

data = {
    "users": [
        {"id": 1, "name": "Ada", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"},
    ]
}

print(encode(data))
# users[2]{id,name,role}:
#   1,Ada,admin
#   2,Bob,user

assert decode(encode(data)) == data
```

Options are keyword arguments in snake case, a spelling the specification
allows (§13):

| TypeScript                                         | Python                                        |
| -------------------------------------------------- | --------------------------------------------- |
| `encode(data)`                                     | `encode(data)`                                |
| `encode(data, { indentSize: 4, delimiter: '\t' })` | `encode(data, indent_size=4, delimiter="\t")` |
| `decode(text)`                                     | `decode(text)`                                |
| `decode(text, { strict: false })`                  | `decode(text, strict=False)`                  |

The streaming functions (`encodeLines`, `decodeStream`) and the `replacer`
option have no Python counterpart.

### Pydantic

With Pydantic, `toon_format.dumps` accepts any model, and `ToonPydanticModel`
adds TOON counterparts of the JSON helpers:

```python
from toon_format.pydantic import ToonPydanticModel


class User(ToonPydanticModel):
    name: str
    age: int


user = User.model_validate_toon("name: Ada\nage: 36")
```

## Command line

This package has no command; use the official
[`@toon-format/cli`](https://www.npmjs.com/package/@toon-format/cli), which
runs with Node.js and needs no installation:

```bash
npx @toon-format/cli data.json -o data.toon   # JSON to TOON
npx @toon-format/cli data.toon -o data.json   # TOON to JSON
npx @toon-format/cli data.json --stats        # token savings against JSON
```

## Documentation

The full documentation is on
**[Read the Docs](https://toon-format.readthedocs.io/en/stable/)**:
usage, the Python type mapping, the choices the specification leaves to
implementations, and Pydantic.

## Migrating from `toon_format` 0.9

The distribution and the module keep their names, and `encode(value)` and
`decode(text)` keep working. Options are now keyword arguments instead of a
dictionary, the token helpers and the `toon` command are gone, and the output
follows specification 4.1. See the
[migration guide](https://toon-format.readthedocs.io/en/stable/migration/).

## Contributing

See [CONTRIBUTING.md](https://github.com/toon-format/toon-python/blob/main/CONTRIBUTING.md).
Project conventions for humans and coding agents are in
[AGENTS.md](https://github.com/toon-format/toon-python/blob/main/AGENTS.md).

## License

[MIT](https://github.com/toon-format/toon-python/blob/main/LICENSE)
