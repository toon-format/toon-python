# Migrating from `toon_format` 0.9

Version 1.0 is a rewrite that implements TOON specification 4.1. The
distribution is still `toon-format` and the module still `toon_format`, so
`encode(value)` and `decode(text)` keep working. The module now follows the
interface of the standard `json` module: `dumps`, `dump`, `loads`, and `load`
are the primary names, and `encode` and `decode` are their aliases.

## Options are keyword arguments

The options dictionary of 0.9 and its types (`EncodeOptions`, `DecodeOptions`,
`DelimiterKey`) are gone. Pass options as keyword arguments; a positional
options argument raises `TypeError`.

| 0.9 | 1.0 |
| --- | --- |
| `encode(value)` | `dumps(value)` or `encode(value)` |
| `encode(value, {"indent": 4, "delimiter": "\t"})` | `dumps(value, indent_size=4, delimiter="\t")` |
| `encode(value, {"delimiter": "pipe"})` | `dumps(value, delimiter="\|")` |
| `decode(text)` | `loads(text)` or `decode(text)` |
| `decode(text, DecodeOptions(indent=4, strict=False))` | `loads(text, indent_size=4, strict=False)` |

## Removed

- **Token helpers.** `count_tokens`, `estimate_savings`, and
  `compare_formats` are gone. Count tokens with your model provider's
  tokenizer, for example `tiktoken` for OpenAI models.
- **The `toon` command** and `python -m toon_format`. The official command line
  is [`@toon-format/cli`](https://www.npmjs.com/package/@toon-format/cli):
  `npx @toon-format/cli data.json`.
- **Length markers** (`[#3]`), removed from the specification, and the
  `lengthMarker` option.

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
- **Unsupported values** raise `TypeError`, like `json.dumps`, instead of
  silently becoming `null`. Pass `default=` to convert them.
- **Non-string keys** are converted like `json.dumps` does (`1` becomes `"1"`,
  `True` becomes `"true"`); other key types raise `TypeError`.
- **`Decimal`** values keep every digit instead of going through `float`.
- **`ToonDecodeError`** now subclasses `ValueError` and has `line`, `source`,
  and `msg` attributes.
- **Python 3.8 and 3.9** are no longer supported.
