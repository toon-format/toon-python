# Migrating from `toon_format` 0.9

Version 1.0 is a rewrite that implements TOON specification 4.1 and moves the
package to the `toon` module with a `json`-style interface. The old
`toon_format` module still works: it delegates to the new implementation and
emits a `DeprecationWarning` when imported.

The distribution is now `toon-python`. Replace `toon-format` with
`toon-python` in your dependencies; until then, `toon-format` 1.0 installs
`toon-python` and keeps the `toon_format` module and the `toon` command, so
upgrading needs no other change.

## Renamed functions

| 0.9 | 1.0 |
| --- | --- |
| `from toon_format import encode, decode` | `import toon` |
| `encode(value)` | `toon.dumps(value)` |
| `encode(value, {"indent": 4, "delimiter": "\t"})` | `toon.dumps(value, indent_size=4, delimiter="\t")` |
| `decode(text)` | `toon.loads(text)` |
| `decode(text, DecodeOptions(indent=4, strict=False))` | `toon.loads(text, indent_size=4, strict=False)` |
| `toon_format.ToonDecodeError` | `toon.ToonDecodeError` |
| `toon_format.pydantic.ToonPydanticModel` | `toon.pydantic.ToonPydanticModel` |
| `python -m toon_format` | `python -m toon` (or the `toon` command) |

`count_tokens`, `estimate_savings`, and `compare_formats` remain available from
`toon_format` only; install `toon-format[tokens]` for them. On the command
line, `toon --stats` replaces them. Both count with OpenAI's tokenizers, so the
counts are exact for OpenAI models only.

## Behavior changes

The 0.9 encoder and decoder implemented specification 1.3. Moving to 4.1
changes some output and fixes many bugs, among them
[#33](https://github.com/toon-format/toon-python/issues/33),
[#47](https://github.com/toon-format/toon-python/issues/47),
[#61](https://github.com/toon-format/toon-python/issues/61),
[#62](https://github.com/toon-format/toon-python/issues/62),
[#63](https://github.com/toon-format/toon-python/issues/63),
[#64](https://github.com/toon-format/toon-python/issues/64), and
[#65](https://github.com/toon-format/toon-python/issues/65).

- **Empty arrays** encode as `key: []` and `[]` instead of `key[0]:`. Both forms decode.
- **Objects of uniform objects** use the keyed tabular form `key[N:]{fields}:`.
- **Uniform nested objects** in tabular arrays become nested field groups:
  `orders[2]{id,customer{name,country}}:`.
- **Comment lines** starting with `#` are ignored by the decoder.
- **Length markers** (`[#3]`) are gone from the specification. The
  `lengthMarker` option and the `--length-marker` flag are accepted and ignored.
- **Unsupported values** raise `TypeError` in `toon.dumps`, like `json.dumps`,
  instead of silently becoming `null`. Pass `default=` to convert them.
  `toon_format.encode` keeps the old behavior.
- **Non-string keys** are converted like `json.dumps` does (`1` becomes `"1"`,
  `True` becomes `"true"`); other key types raise `TypeError`.
- **`Decimal`** values keep every digit instead of going through `float`.
- **`ToonDecodeError`** now subclasses `ValueError` and has `line`, `source`,
  and `msg` attributes.
- **Python 3.8 and 3.9** are no longer supported.
