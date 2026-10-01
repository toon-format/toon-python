# Conversion to Other Formats

This package converts between Python values and TOON, and nothing else. It does not parse or write CSV, YAML, or XML, does not auto-detect input formats, and does not batch-convert files or bundle them into archives.

## Why this is out of scope

The spec scopes TOON as a translation layer for the JSON data model: "produce data as JSON in code, encode to TOON for downstream consumption, and decode back to JSON if needed" (Introduction, Purpose and Scope). Python values are the hub. Any other format reaches TOON through a parser that already turns it into dicts and lists:

```python
import csv
import json

encode(json.load(f))
encode({"rows": list(csv.DictReader(f))})

rows = decode(text)["rows"]
writer = csv.DictWriter(out, fieldnames=rows[0].keys())
writer.writeheader()
writer.writerows(rows)
```

Shipping our own CSV or YAML reader would duplicate the standard library and mature third-party parsers, and every edge case of those formats would turn into a bug report here. As Johann put it on the CSV pull request: "this is completely out of scope for the TOON Python package. There are numerous battle-tested CSV parsers available" ([#39](https://github.com/toon-format/toon-python/pull/39#issuecomment-3539108955)).

The `toon` command follows the same line: it converts between JSON and TOON, because JSON is the data model TOON carries (§2).

## Prior requests

- [#25](https://github.com/toon-format/toon-python/issues/25) / [#35](https://github.com/toon-format/toon-python/pull/35): "batch processing" – multi-format conversion between JSON, YAML, XML, CSV, and TOON with auto-detection
- [#38](https://github.com/toon-format/toon-python/discussions/38): "TOON to CSV python lib" – merging `tooncsv` into this package
- [#39](https://github.com/toon-format/toon-python/pull/39): "Add CSV Parsing & Writing Support to toon_format"
