# TOON Format for Python

[![Tests](https://github.com/toon-format/toon-python/actions/workflows/test.yml/badge.svg)](https://github.com/toon-format/toon-python/actions)
[![Python Versions](https://img.shields.io/pypi/pyversions/toon_format.svg)](https://pypi.org/project/toon_format/)

> **⚠️ Beta Status (v0.9.x):** This library is in active development and working towards spec compliance. Beta published to PyPI. API may change before 1.0.0 release.

Compact, human-readable serialization format for LLM contexts with **30-60% token reduction** vs JSON. Combines YAML-like indentation with CSV-like tabular arrays. Working towards full compatibility with the [official TOON specification](https://github.com/toon-format/spec).

**Key Features:** Minimal syntax • Tabular arrays for uniform data • Array length validation • Python 3.8+ • Comprehensive test coverage.

```bash
# Beta published to PyPI - install from source:
git clone https://github.com/toon-format/toon-python.git
cd toon-python
uv sync

# Or install directly from GitHub:
pip install git+https://github.com/toon-format/toon-python.git
```

## Quick Start

```python
from toon_format import encode, decode

# Simple object
encode({"name": "Alice", "age": 30})
# name: Alice
# age: 30

# Tabular array (uniform objects)
encode([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
# [2,]{id,name}:
#   1,Alice
#   2,Bob

# Decode back to Python
decode("items[2]: apple,banana")
# {'items': ['apple', 'banana']}
```

## CLI Usage

```bash
# Auto-detect format by extension
toon input.json -o output.toon      # Encode
toon data.toon -o output.json       # Decode
echo '{"x": 1}' | toon -            # Stdin/stdout

# Options
toon data.json --encode --delimiter "\t" --length-marker
toon data.toon --decode --no-strict --indent 4
```

**Options:** `-e/--encode` `-d/--decode` `-o/--output` `--delimiter` `--indent` `--length-marker` `--no-strict`

## API Reference

### `encode(value, options=None)` → `str`

```python
encode({"id": 123}, {"delimiter": "\t", "indent": 4, "lengthMarker": "#"})
```

**Options:**
- `delimiter`: `","` (default), `"\t"`, `"|"`
- `indent`: Spaces per level (default: `2`)
- `lengthMarker`: `""` (default) or `"#"` to prefix array lengths

### `decode(input_str, options=None)` → `Any`

```python
decode("id: 123", {"indent": 2, "strict": True})
```

**Options:**
- `indent`: Expected indent size (default: `2`)
- `strict`: Validate syntax, lengths, delimiters (default: `True`)

### Token Counting & Comparison

Measure token efficiency and compare formats:

```python
from toon_format import estimate_savings, compare_formats, count_tokens

# Measure savings
data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
result = estimate_savings(data)
print(f"Saves {result['savings_percent']:.1f}% tokens")  # Saves 42.3% tokens

# Visual comparison
print(compare_formats(data))
# Format Comparison
# ────────────────────────────────────────────────
# Format      Tokens    Size (chars)
# JSON            45             123
# TOON            28              85
# ────────────────────────────────────────────────
# Savings: 17 tokens (37.8%)

# Count tokens directly
toon_str = encode(data)
tokens = count_tokens(toon_str)  # Uses tiktoken (gpt5/gpt5-mini)
```

**Requires tiktoken:** `uv add tiktoken` (benchmark features are optional)

## Format Specification

| Type | Example Input | TOON Output |
|------|---------------|-------------|
| **Object** | `{"name": "Alice", "age": 30}` | `name: Alice`<br>`age: 30` |
| **Primitive Array** | `[1, 2, 3]` | `[3]: 1,2,3` |
| **Tabular Array** | `[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]` | `[2,]{id,name}:`<br>&nbsp;&nbsp;`1,A`<br>&nbsp;&nbsp;`2,B` |
| **Mixed Array** | `[{"x": 1}, 42, "hi"]` | `[3]:`<br>&nbsp;&nbsp;`- x: 1`<br>&nbsp;&nbsp;`- 42`<br>&nbsp;&nbsp;`- hi` |

**Quoting:** Only when necessary (empty, keywords, numeric strings, whitespace, structural chars, delimiters)

**Type Normalization:** `Infinity/NaN/Functions` → `null` • `Decimal` → `float` • `datetime` → ISO 8601 • `-0` → `0`

## LangChain Integration

Install with:
```bash
pip install "toon-python[langchain]"
```
Adds a **completely optional** LangChain integration via the `[langchain]` extra.

### Features
- `ToonSerializer`: `Document` → TOON (30-60 % token reduction)
- `ToonOutputParser`: TOON response → Python object
- Sync + async support
- 2 unit tests (100 % coverage for new code)
- README example + optional doc page

## Usage After Release
```bash
pip install "toon-python[langchain]"
from toon_format.langchain import ToonSerializer
```
## Development

```bash
# Setup (requires uv: https://docs.astral.sh/uv/)
git clone https://github.com/toon-format/toon-python.git
cd toon-python
uv sync

# Run tests (792 tests, 91% coverage, 85% enforced)
uv run pytest --cov=toon_format --cov-report=term

# Code quality
uv run ruff check src/ tests/        # Lint
uv run ruff format src/ tests/       # Format
uv run mypy src/                     # Type check
```

**CI/CD:** GitHub Actions • Python 3.8-3.14 • Coverage enforcement • PR coverage comments

## Project Status & Roadmap

Following semantic versioning towards 1.0.0:

- **v0.8.x** - Initial code set, tests, documentation ✅
- **v0.9.x** - Serializer improvements, spec compliance testing, publishing setup (current)
- **v1.0.0-rc.x** - Release candidates for production readiness
- **v1.0.0** - First stable release with full spec compliance

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Documentation

- [📘 Full Documentation](docs/) - Complete guides and references
- [🔧 API Reference](docs/api.md) - Detailed function documentation
- [📋 Format Specification](docs/format.md) - TOON syntax and rules
- [🤖 LLM Integration](docs/llm-integration.md) - Best practices for LLM usage
- [📜 TOON Spec](https://github.com/toon-format/spec) - Official specification
- [🐛 Issues](https://github.com/toon-format/toon-python/issues) - Bug reports and features
- [🤝 Contributing](CONTRIBUTING.md) - Contribution guidelines

## Contributors

- [Xavi Vinaixa](https://github.com/xaviviro)
- [David Pirogov](https://github.com/davidpirogov)
- [Justar](https://github.com/Justar96)
- [Johann Schopplich](https://github.com/johannschopplich)

## License

MIT License – see [LICENSE](LICENSE) for details
