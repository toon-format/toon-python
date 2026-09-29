# TOON for Python

[![CI](https://github.com/toon-format/toon-python/actions/workflows/ci.yml/badge.svg)](https://github.com/toon-format/toon-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/toon-python.svg)](https://pypi.org/project/toon-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/toon-python.svg)](https://pypi.org/project/toon-python/)
[![Docs](https://readthedocs.org/projects/toon-python/badge/?version=latest)](https://toon-python.readthedocs.io)
[![TOON spec](https://img.shields.io/badge/TOON%20spec-4.1-blue)](https://github.com/toon-format/spec/blob/main/SPEC.md)

The official Python implementation of **TOON** (Token-Oriented Object Notation):
a compact, human-readable encoding of the JSON data model, designed to save
tokens in LLM prompts.

- **Complete**: implements [TOON specification 4.1](https://github.com/toon-format/spec/blob/main/SPEC.md)
  and passes every official conformance fixture.
- **Familiar**: `dumps`, `dump`, `loads`, and `load`, like the `json` module.
- **Lossless**: `loads(dumps(data)) == data` for every JSON-compatible value.
- **Pure Python**, no dependencies, fully typed, Python 3.10+.

## Example

```python
import toon

data = {
    "context": {"task": "Our favorite hikes together", "location": "Boulder"},
    "friends": ["ana", "luis", "sam"],
    "hikes": [
        {"id": 1, "name": "Blue Lake Trail", "distanceKm": 7.5, "wasSunny": True},
        {"id": 2, "name": "Ridge Overlook", "distanceKm": 9.2, "wasSunny": False},
    ],
}

text = toon.dumps(data)
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
assert toon.loads(text) == data
```

Keys of uniform arrays are written once, as a header, and each object becomes
a row. With OpenAI's `o200k_base` tokenizer, this document takes 65 tokens,
against 76 for compact JSON and 130 for indented JSON. The saving grows with
the number of rows: 100 uniform records take 38% fewer tokens than compact
JSON. Deeply nested or irregular data gains less.

## Installation

```bash
pip install toon-python
# or
uv add toon-python
```

The distribution is named `toon-python`; the module is `toon`. Optional extras:

- `toon-python[pydantic]`: the Pydantic integration.
- `toon-python[tokens]`: token counts with `toon stats`.

## Usage

Encoding and decoding follow the `json` module:

```python
toon.dumps(data, delimiter="\t")  # tabs often tokenize better than commas
toon.dumps(data, default=str)  # fallback for unsupported types
toon.loads(text, parse_float=Decimal)  # same hooks as json.loads
toon.loads(llm_output, strict=False)  # tolerate wrong counts and indentation
```

Invalid documents raise `toon.ToonDecodeError`, a `ValueError` that carries the
1-based `line` and the `source` line of the error.

To find out whether TOON pays off on your own data, compare token counts with
the `toon` command:

```bash
pip install "toon-python[tokens]"
toon stats data.json
```

With Pydantic, `toon.dumps` accepts any model, and `ToonPydanticModel` adds
TOON counterparts of the JSON helpers:

```python
from toon.pydantic import ToonPydanticModel


class User(ToonPydanticModel):
    name: str
    age: int


user = User.model_validate_toon("name: Ada\nage: 36")
```

## Documentation

The full documentation is at
**[toon-python.readthedocs.io](https://toon-python.readthedocs.io)**: usage,
the Python type mapping, the choices the specification leaves to
implementations, the command line, Pydantic, and the API reference.

The documentation site is not published yet. Until it is, read the pages in
[`docs/`](https://github.com/toon-format/toon-python/tree/main/docs) on GitHub.

## Migrating from `toon_format` 0.9

Up to 0.9 the distribution was `toon-format`. `pip install toon-format` and
`import toon_format` still work: the `toon-format` distribution now installs
`toon-python`, and `toon_format` delegates to the new API with a
`DeprecationWarning`. See the
[migration guide](https://github.com/toon-format/toon-python/blob/main/docs/migration.md).

## Contributing

See [CONTRIBUTING.md](https://github.com/toon-format/toon-python/blob/main/CONTRIBUTING.md).
Project conventions for humans and coding agents are in
[AGENTS.md](https://github.com/toon-format/toon-python/blob/main/AGENTS.md).

## Authors

The people who wrote this package are listed in
[AUTHORS](https://github.com/toon-format/toon-python/blob/main/AUTHORS); every
contributor is on the
[contributors page](https://github.com/toon-format/toon-python/graphs/contributors).

## License

[MIT](https://github.com/toon-format/toon-python/blob/main/LICENSE)
