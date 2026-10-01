# JSON Text Helpers

`encode()` takes Python values and `decode()` returns Python values, the same way `json.dumps` and `json.loads` work. The package does not add variants that read or write JSON text: no `json_indent` option on `decode()`, no `encode_json(text)`, no `loads` alias for `json.loads`.

## Why this is out of scope

The `json` module already does the JSON half, and each helper would only wrap one call to it:

```python
import json

encode(json.loads(text))                  # JSON text → TOON
json.dumps(decode(toon_text), indent=2)   # TOON → pretty-printed JSON
```

A `json_indent` option on `decode()` also breaks the return type: with it set, `decode()` returns a `str` instead of the decoded value, so every typed caller has to narrow a `JsonValue | str` union – for output that `json.dumps` produces without it.

The public API also stays close to the reference implementation, where `encode()` and `decode()` work on in-memory values only. @smortezah raised this on the `encode_json` pull request: "To maintain alignment with the original TypeScript implementation of toon-format, I suggest we avoid adding excessive functions" ([#57](https://github.com/toon-format/toon-python/pull/57)).

The `toon` command is where JSON text belongs: it reads and writes JSON files and indents its JSON output on decode.

JSON `null` needs no helper either: `json.loads` returns `None`, which `encode()` emits as `null` (§2).

## Prior requests

- [#10](https://github.com/toon-format/toon-python/issues/10): "JSON indentation option in decode method"
- [#37](https://github.com/toon-format/toon-python/pull/37): "feat: Add JSON indentation option to decode() method"
- [#57](https://github.com/toon-format/toon-python/pull/57): "feat: add encode_json and loads helpers for better JSON null support"
