# TOON for Python

The official Python implementation of **TOON** (Token-Oriented Object Notation):
a compact, human-readable encoding of the JSON data model, designed to save
tokens in LLM prompts.

- **Complete**: implements [TOON specification 4.1](https://github.com/toon-format/spec/blob/main/SPEC.md)
  and passes every official conformance fixture.
- **Familiar**: `dumps`, `dump`, `loads`, and `load`, like the `json` module,
  with `encode` and `decode` as aliases.
- **Pure Python**, no dependencies, fully typed, Python 3.10+.

## Installation

```bash
pip install toon-format
# or
uv add toon-format
```

The module is `toon_format`. Install `toon-format[pydantic]` for the
[Pydantic integration](usage.md#pydantic).

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

## Next steps

- [Usage](usage.md): encoding, decoding, errors, and Pydantic.
- [Data types](data-types.md): how Python values map to TOON.
- [Migrating from 0.9](migration.md): what changed since `toon-format` 0.9.
