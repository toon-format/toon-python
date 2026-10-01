# Usage

`toon_format` follows the interface of the standard `json` module. Every
option is described in the [API reference](api-reference.md). `encode` and
`decode`, the names used by the other TOON implementations, are aliases of
`dumps` and `loads` and take the same options.

## Encoding

```python
toon_format.dumps(obj, *, indent_size=2, delimiter=",", default=None, sort_keys=False) -> str
toon_format.dump(obj, fp, **options) -> None
```

The encoder picks the most compact form the specification allows for each
value; the choice follows from the value's shape. Arrays of primitives stay on
one line and arrays of uniform objects become tables:

```python
>>> print(toon_format.dumps({"tags": ["a", "b"], "users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]}))
tags[2]: a,b
users[2]{id,name}:
  1,Ada
  2,Bob
```

Objects whose values share one shape use the keyed tabular form, and uniform
nested objects collapse into nested field groups:

```python
>>> print(toon_format.dumps({"servers": {"alpha": {"host": "a.example.com", "port": 8080},
...                                      "beta": {"host": "b.example.com", "port": 9090}}}))
servers[2:]{host,port}:
  alpha: a.example.com,8080
  beta: b.example.com,9090

>>> print(toon_format.dumps({"orders": [{"id": 1, "customer": {"name": "Ada", "country": "DK"}},
...                                     {"id": 2, "customer": {"name": "Bob", "country": "UK"}}]}))
orders[2]{id,customer{name,country}}:
  1,Ada,DK
  2,Bob,UK
```

Everything else uses the list form:

```python
>>> print(toon_format.dumps({"items": [1, {"a": 1}, [2, 3]]}))
items[3]:
  - 1
  - a: 1
  - [2]: 2,3
```

`delimiter="\t"` or `"|"` often tokenizes better than commas. Types without a
TOON representation go to `default`, as with `json.dumps`:

```python
>>> toon_format.dumps({"z": 1 + 2j}, default=lambda value: [value.real, value.imag])
'z[2]: 1,2'
```

### NumPy and pandas

`toon_format` does not depend on either library. A pandas `DataFrame` becomes a table
through its records; missing values (`NaN`) become `null` and timestamps ISO
8601 strings:

```python
>>> df = pd.DataFrame({"id": [1, 2], "name": ["Ada", "Bob"], "score": [9.5, None]})
>>> print(toon_format.dumps({"users": df.to_dict("records")}))
users[2]{id,name,score}:
  1,Ada,9.5
  2,Bob,null
```

NumPy arrays and scalars such as `np.int64` convert with `tolist()`:

```python
>>> toon_format.dumps({"matrix": np.arange(6).reshape(2, 3), "n": np.int64(6)},
...                   default=lambda value: value.tolist())
'matrix[2]:\n  - [3]: 0,1,2\n  - [3]: 3,4,5\nn: 6'
```

## Decoding

```python
toon_format.loads(s, *, strict=True, indent_size=2, parse_float=None, parse_int=None,
           object_hook=None, object_pairs_hook=None) -> Any
toon_format.load(fp, **options) -> Any
```

`s` may also be `bytes`, and `fp` a binary file. By default the decoder
enforces every check of the specification: declared lengths, row widths,
indentation, blank lines inside arrays, and duplicate keys. `strict=False`
tolerates them, which helps with hand-written or LLM-generated documents.
The hooks work as in `json.loads`:

```python
>>> from decimal import Decimal
>>> toon_format.loads("price: 0.1", parse_float=Decimal)
{'price': Decimal('0.1')}
```

Invalid documents raise `toon_format.ToonDecodeError`, a `ValueError` that carries the
1-based `line`, the offending `source` line, and the bare `msg`:

```python
>>> try:
...     toon_format.loads("a: 1\ntags[3]: a,b")
... except toon_format.ToonDecodeError as exc:
...     print(exc.line, repr(exc.source), exc.msg)
2 'tags[3]: a,b' Declared length 3 but found 2
```

## Pydantic

With the `toon-format[pydantic]` extra, `toon_format.dumps` accepts any
`pydantic.BaseModel`, and `ToonPydanticModel` adds TOON counterparts of
pydantic's JSON helpers:

```python
from toon_format.pydantic import ToonPydanticModel


class User(ToonPydanticModel):
    name: str
    age: int


prompt = User.schema_to_toon()  # the JSON schema, as TOON
user = User.model_validate_toon("name: Ada\nage: 36")  # parse an LLM answer
text = user.model_dump_toon()
```

`model_validate_toon(text, strict=...)` passes `strict` to both the TOON
decoder and pydantic. The default, `None`, decodes in strict mode and follows
the model's own configuration for validation.
