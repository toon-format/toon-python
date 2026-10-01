# JSON Text Helpers

The encoder takes Python values and the decoder returns them, as the `json` module does. There are no variants that read or write JSON text – no JSON indentation option on decode, no `encode_json(text)`, no wrapper around `json.loads`.

## Why this is out of scope

Each helper would wrap a single call to the `json` module, and a JSON indentation option would also make decode return a string instead of the decoded value. JSON text belongs to the `toon` command, which reads JSON and writes indented JSON.

JSON `null` needs no helper either: `json.loads` returns `None`, which encodes as `null`.

## Prior requests

- [#10](https://github.com/toon-format/toon-python/issues/10) – "JSON indentation option in decode method"
- [#37](https://github.com/toon-format/toon-python/pull/37) – "feat: Add JSON indentation option to decode() method"
- [#49](https://github.com/toon-format/toon-python/issues/49) – "Support JSON null values (auto-convert to Python None) in toon-python encoding flow"
- [#57](https://github.com/toon-format/toon-python/pull/57) – "feat: add encode_json and loads helpers for better JSON null support"
