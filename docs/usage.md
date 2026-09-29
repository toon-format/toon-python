# Usage

`toon` follows the interface of the standard `json` module. Every option is
described in the [API reference](api-reference.md).

## Encoding

```python
toon.dumps(obj, *, indent_size=2, delimiter=",", default=None, sort_keys=False) -> str
toon.dump(obj, fp, **options) -> None
```

The encoder picks the most compact form the specification allows for each
value; the choice follows from the value's shape. Arrays of primitives stay on
one line and arrays of uniform objects become tables:

```python
>>> print(toon.dumps({"tags": ["a", "b"], "users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]}))
tags[2]: a,b
users[2]{id,name}:
  1,Ada
  2,Bob
```

Objects whose values share one shape use the keyed tabular form, and uniform
nested objects collapse into nested field groups:

```python
>>> print(toon.dumps({"servers": {"alpha": {"host": "a.example.com", "port": 8080},
...                               "beta": {"host": "b.example.com", "port": 9090}}}))
servers[2:]{host,port}:
  alpha: a.example.com,8080
  beta: b.example.com,9090

>>> print(toon.dumps({"orders": [{"id": 1, "customer": {"name": "Ada", "country": "DK"}},
...                              {"id": 2, "customer": {"name": "Bob", "country": "UK"}}]}))
orders[2]{id,customer{name,country}}:
  1,Ada,DK
  2,Bob,UK
```

Everything else uses the list form:

```python
>>> print(toon.dumps({"items": [1, {"a": 1}, [2, 3]]}))
items[3]:
  - 1
  - a: 1
  - [2]: 2,3
```

`delimiter="\t"` or `"|"` often tokenizes better than commas. Types without a
TOON representation go to `default`, as with `json.dumps`:

```python
>>> toon.dumps({"z": 1 + 2j}, default=lambda value: [value.real, value.imag])
'z[2]: 1,2'
```

### NumPy and pandas

`toon` does not depend on either library. A pandas `DataFrame` becomes a table
through its records; missing values (`NaN`) become `null` and timestamps ISO
8601 strings:

```python
>>> df = pd.DataFrame({"id": [1, 2], "name": ["Ada", "Bob"], "score": [9.5, None]})
>>> print(toon.dumps({"users": df.to_dict("records")}))
users[2]{id,name,score}:
  1,Ada,9.5
  2,Bob,null
```

NumPy arrays and scalars such as `np.int64` convert with `tolist()`:

```python
>>> toon.dumps({"matrix": np.arange(6).reshape(2, 3), "n": np.int64(6)},
...            default=lambda value: value.tolist())
'matrix[2]:\n  - [3]: 0,1,2\n  - [3]: 3,4,5\nn: 6'
```

## Decoding

```python
toon.loads(s, *, strict=True, indent_size=2, parse_float=None, parse_int=None,
           object_hook=None, object_pairs_hook=None) -> Any
toon.load(fp, **options) -> Any
```

`s` may also be `bytes`, and `fp` a binary file. By default the decoder
enforces every check of the specification: declared lengths, row widths,
indentation, blank lines inside arrays, and duplicate keys. `strict=False`
tolerates them, which helps with hand-written or LLM-generated documents.
The hooks work as in `json.loads`:

```python
>>> from decimal import Decimal
>>> toon.loads("price: 0.1", parse_float=Decimal)
{'price': Decimal('0.1')}
```

Invalid documents raise `toon.ToonDecodeError`, a `ValueError` that carries the
1-based `line`, the offending `source` line, and the bare `msg`:

```python
>>> try:
...     toon.loads("a: 1\ntags[3]: a,b")
... except toon.ToonDecodeError as exc:
...     print(exc.line, repr(exc.source), exc.msg)
2 'tags[3]: a,b' Declared length 3 but found 2
```

## Command line

The `toon` command (also `python -m toon`) converts in either direction,
choosing it from the file extension or, failing that, from the content:

```bash
toon data.json -o data.toon          # JSON to TOON
toon data.toon                       # TOON to JSON on standard output
cat data.json | toon --delimiter tab # from standard input
toon --check response.toon           # validate only; exit status 1 if invalid
toon data.json --stats               # also print token counts to standard error
```

`--stats` compares the token counts of compact JSON, indented JSON, and TOON.
It needs the `tokens` extra (`pip install "toon-python[tokens]"`) and counts
offline with OpenAI's `o200k_base` tokenizer through `tiktoken`, so the counts
are exact for OpenAI models only. Other models, Claude and Gemini among them,
use different tokenizers: treat the figures as an estimate for them.

Run `toon --help` for the other options.

## Pydantic

With the `toon-python[pydantic]` extra, `toon.dumps` accepts any
`pydantic.BaseModel`, and `ToonPydanticModel` adds TOON counterparts of
pydantic's JSON helpers:

```python
from toon.pydantic import ToonPydanticModel


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
