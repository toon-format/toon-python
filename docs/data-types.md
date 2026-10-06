# Data types

## Encoding

| Python | TOON |
| --- | --- |
| `dict` and other mappings | object; keys may be `str`, `int`, `float`, `bool`, or `None`, converted like `json.dumps` does |
| `list`, `tuple` | array |
| `set`, `frozenset` | array, sorted |
| `str` | string, quoted only when needed |
| `int` | number, exact at any size |
| `float` | number; `nan` and infinities become `null` |
| `decimal.Decimal` | number, with every digit preserved (see [Numbers](#specification-choices)) |
| `bool`, `None` | `true`, `false`, `null` |
| `datetime`, `date`, `time` | ISO 8601 string |
| `uuid.UUID`, `pathlib.PurePath` | string |
| `enum.Enum` | its value |
| dataclass instance | object of its fields |
| `attrs` class instance | object of its fields (attrs is not imported) |
| `pydantic.BaseModel` | `model_dump(mode="json")` |

Anything else goes to `default`, or raises `TypeError`.

## Decoding

Decoding produces `dict`, `list`, `str`, `int`, `float`, `bool`, and `None`.
A number without a fraction or exponent is an `int`; any other number is a
`float`, unless `parse_float` or `parse_int` says otherwise. Strings are never
converted back to dates or other types.

## Specification choices

This package targets **TOON 4.3** (`toon_format.__toon_spec__`). The specification
asks implementations to document the following choices.

**Numbers.** Integers encode and decode exactly at any size. Floats use the
shortest representation that round-trips, in plain decimal between 1e-6 and
1e21 and in exponent form (`1e+21`, `1e-7`) outside it. Integral floats from
2⁵³ up are written with their exact digits, so that they decode to an equal
`int`. A decoded number beyond the double range is an error in strict mode and
`±inf` otherwise. `Decimal` input keeps every digit, and `parse_float=Decimal`
keeps them when decoding. A `Decimal` beyond the double range, such as
`Decimal("1e400")`, therefore encodes but does not decode back with the
default strict decoder: pass `parse_float=Decimal` to read it.

**Strings.** A string holding an unpaired surrogate cannot be encoded and
raises `ValueError`. A root string starting with U+FEFF is quoted, because a
leading U+FEFF in a document is read as a byte-order mark.

**Key order** is preserved, except that tabular rows follow the header's field
order. With `strict=False`, a duplicate key keeps its first position and its
last value, as in `json.loads`. When encoding, keys that become equal once
converted to strings (`1` and `"1"`, `True` and `"true"`) raise `ValueError`
instead of dropping a value. No key is special: `__proto__` is an ordinary key.

**Tabs in indentation** are an error in strict mode; otherwise each leading tab
counts as one level.

**Nesting** deeper than the interpreter's recursion limit raises `ValueError`
when encoding and `ToonDecodeError` when decoding.
