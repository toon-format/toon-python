# Documentation

Comprehensive documentation for toon_format Python package.

## Quick Links

- [API Reference](api.md) - Complete function and class documentation
- [Format Specification](format.md) - Detailed TOON syntax and rules
- [LLM Integration](llm-integration.md) - Best practices for using TOON with LLMs

## Getting Started

New to TOON? Start here:

1. Read the [main README](../README.md) for quick start examples
2. Review the [Format Specification](format.md) to understand TOON syntax
3. Check the [API Reference](api.md) for detailed function usage
4. See [LLM Integration](llm-integration.md) for advanced use cases

## Documentation Structure

### [API Reference](api.md)

Complete reference for all public functions and classes:
- `encode()` - Convert Python to TOON
- `decode()` - Convert TOON to Python
- `EncodeOptions` - Encoding configuration
- `DecodeOptions` - Decoding configuration
- `ToonDecodeError` - Error handling
- Type normalization rules
- Advanced usage patterns

### [Format Specification](format.md)

Detailed explanation of TOON format rules:
- Objects (key-value pairs, nesting)
- Arrays (primitive, tabular, list, nested)
- Delimiters (comma, tab, pipe)
- String quoting rules
- Primitives (numbers, booleans, null)
- Indentation rules
- Complete format examples

### [LLM Integration](llm-integration.md)

Best practices for LLM usage:
- Why TOON for LLMs
- Prompting strategies
- Token efficiency techniques
- Real-world use cases
- Error handling
- Integration examples (OpenAI, Anthropic)
- Performance metrics
- Debugging tips

## External Resources

- [Official TOON Specification](https://github.com/toon-format/spec) - Normative spec
- [TypeScript Reference](https://github.com/toon-format/toon) - Original implementation
- [Test Fixtures](../tests/README.md) - Spec compliance test suite
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute

## Examples

### Basic Encoding

```python
from toon_format import encode

data = {"name": "Alice", "age": 30}
print(encode(data))
# name: Alice
# age: 30
```

### Basic Decoding

```python
from toon_format import decode

toon = "items[2]: apple,banana"
data = decode(toon)
# {'items': ['apple', 'banana']}
```

### With Options

```python
# Custom delimiter
encode([1, 2, 3], {"delimiter": "\t"})
# [3	]: 1	2	3

# Lenient decoding
decode("items[5]: a,b,c", {"strict": False})
# {'items': ['a', 'b', 'c']}  # Accepts length mismatch
```

## Support

- **Bug Reports:** [GitHub Issues](https://github.com/toon-format/toon-python/issues)
- **Questions:** [GitHub Discussions](https://github.com/toon-format/toon-python/discussions)
- **Contributing:** See [CONTRIBUTING.md](../CONTRIBUTING.md)

## License

MIT License - see [LICENSE](../LICENSE)
