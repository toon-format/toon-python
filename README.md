# TOON for Python

[![CI](https://github.com/toon-format/toon-python/actions/workflows/ci.yml/badge.svg)](https://github.com/toon-format/toon-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/toon-format.svg)](https://pypi.org/project/toon-format/)
[![Python versions](https://img.shields.io/pypi/pyversions/toon-format.svg)](https://pypi.org/project/toon-format/)
[![Docs](https://readthedocs.org/projects/toon-python/badge/?version=latest)](https://toon-python.readthedocs.io)
[![TOON spec](https://img.shields.io/badge/TOON%20spec-4.1-blue)](https://github.com/toon-format/spec/blob/main/SPEC.md)

The official Python implementation of **TOON** (Token-Oriented Object Notation):
a compact, human-readable encoding of the JSON data model, designed to save
tokens in LLM prompts.

- **Complete**: implements [TOON specification 4.1](https://github.com/toon-format/spec/blob/main/SPEC.md)
  and passes every official conformance fixture.
- **Familiar**: `dumps`, `dump`, `loads`, and `load`, like the `json` module.
- **Pure Python**, no dependencies, fully typed, Python 3.10+.

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

print(toon.dumps(data))
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
assert toon.loads(toon.dumps(data)) == data
```

## Installation

```bash
pip install toon-format
# or
uv add toon-format
```

The distribution is named `toon-format`; the module is `toon`. Optional extras:
`toon-format[pydantic]` for the Pydantic integration.

## Usage

```python
toon.dumps(obj, *, indent_size=2, delimiter=",", default=None, sort_keys=False)
toon.loads(s, *, strict=True, indent_size=2, parse_float=None, parse_int=None,
           object_hook=None, object_pairs_hook=None)
```

`dump` and `load` do the same with files. Invalid documents raise
`toon.ToonDecodeError`, a `ValueError` that carries the `line` and `source` of
the error. The package also provides a `toon` command and a Pydantic integration:

```bash
toon data.json -o data.toon   # JSON to TOON
toon --check response.toon    # validate only
```

## Documentation

The full documentation is at
**[toon-python.readthedocs.io](https://toon-python.readthedocs.io)**: usage,
the Python type mapping, the choices the specification leaves to
implementations, the command line, Pydantic, and the API reference.

> [!NOTE]
> The documentation site is not published yet. Until it is, read the pages in
> [`docs/`](docs/) on GitHub.

## Migrating from `toon_format` 0.9

`import toon_format` still works and delegates to the new API, with a
`DeprecationWarning`. See the [migration guide](https://toon-python.readthedocs.io/en/latest/migration/).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Project conventions for humans and coding
agents are in [AGENTS.md](AGENTS.md).

## Authors

The people who wrote this package are listed in [AUTHORS](AUTHORS); every
contributor is on the [contributors page](https://github.com/toon-format/toon-python/graphs/contributors).

## License

[MIT](LICENSE)
