# Advanced Features Guide

## Overview

TOON Format v0.9+ includes cutting-edge features that make it the most advanced serialization library for LLM applications:

1. **Type-Safe Model Integration** - Pydantic, dataclasses, attrs support
2. **Streaming Processing** - Handle datasets larger than memory
3. **Plugin System** - Custom type handlers for any data type
4. **Semantic Optimization** - AI-aware token reduction
5. **Batch Processing** - Multi-format conversion with auto-detection

---

## 1. Type-Safe Model Integration

### Pydantic Models

Seamless integration with Pydantic v1 and v2:

```python
from pydantic import BaseModel
from toon_format import encode_model, decode_model

class User(BaseModel):
    name: str
    age: int
    email: str

# Encode with validation
user = User(name="Alice", age=30, email="alice@example.com")
toon_str = encode_model(user)
print(toon_str)
# name: Alice
# age: 30
# email: alice@example.com

# Decode with validation
decoded = decode_model(toon_str, User)
assert isinstance(decoded, User)
```

### Python Dataclasses

Native support for Python's built-in dataclasses:

```python
from dataclasses import dataclass
from toon_format import encode_model, decode_model

@dataclass
class Point:
    x: float
    y: float
    label: str = "origin"

point = Point(x=10.5, y=20.3, label="A")
toon_str = encode_model(point)
decoded = decode_model(toon_str, Point)
```

### attrs Classes

Support for attrs library:

```python
import attrs
from toon_format import encode_model

@attrs.define
class Product:
    name: str
    price: float
    stock: int

product = Product(name="Widget", price=9.99, stock=100)
toon_str = encode_model(product)
```

---

## 2. Streaming Processing

Process large datasets without loading everything into memory.

### Streaming Encoder

```python
from toon_format.streaming import StreamEncoder

# Stream large dataset to file
with StreamEncoder(output_file="large_data.toon") as encoder:
    encoder.start_array(fields=["id", "name", "value"])
    
    for i in range(1_000_000):
        encoder.encode_item({
            "id": i,
            "name": f"item_{i}",
            "value": i * 1.5
        })
    
    encoder.end_array()
```

### Streaming Decoder

```python
from toon_format.streaming import stream_decode_array

# Process one item at a time
for item in stream_decode_array("large_data.toon"):
    process(item)  # Memory-efficient processing
```

### Stream Encode Generators

```python
from toon_format.streaming import stream_encode_array

def data_generator():
    """Generate data on-the-fly"""
    for i in range(10000):
        yield {"id": i, "data": f"record_{i}"}

# Stream chunks to output
with open("output.toon", "w") as f:
    for chunk in stream_encode_array(data_generator(), fields=["id", "data"]):
        f.write(chunk)
```

---

## 3. Plugin System

Register custom encoders/decoders for any type.

### Built-in Support

The following types are automatically supported:
- `uuid.UUID`
- `decimal.Decimal`
- `datetime`, `date`, `time`
- `numpy.ndarray`
- `pandas.DataFrame`, `pandas.Series`

### Custom Type Registration

```python
from toon_format.plugins import register_encoder, register_decoder
import uuid

# Register UUID handler
register_encoder(
    uuid.UUID,
    lambda u: {"__type__": "UUID", "value": str(u)}
)

register_decoder(
    "UUID",
    lambda data: uuid.UUID(data["value"]) if isinstance(data, dict) else data
)

# Now UUIDs work seamlessly
from toon_format import encode, decode

data = {"id": uuid.uuid4(), "name": "Alice"}
toon_str = encode(data)
decoded = decode(toon_str)
assert isinstance(decoded["id"], uuid.UUID)
```

### NumPy Arrays

```python
import numpy as np
from toon_format import encode, decode

# NumPy arrays are automatically handled
data = {
    "matrix": np.array([[1, 2], [3, 4]]),
    "vector": np.array([1.5, 2.5, 3.5])
}

toon_str = encode(data)
decoded = decode(toon_str)
assert isinstance(decoded["matrix"], np.ndarray)
```

### Pandas DataFrames

```python
import pandas as pd
from toon_format import encode, decode

df = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "score": [95.5, 87.3, 92.1]
})

data = {"results": df}
toon_str = encode(data)
decoded = decode(toon_str)
assert isinstance(decoded["results"], pd.DataFrame)
```

---

## 4. Semantic Token Optimization

AI-aware optimization for maximum token efficiency.

### Field Name Abbreviation

```python
from toon_format.semantic import optimize_for_llm
from toon_format import encode

data = {
    "employee_identifier": 12345,
    "full_name": "Alice Johnson",
    "department": "Engineering",
    "description": "Senior Software Engineer",
    "created_at": "2024-01-01",
    "metadata": {"version": 1}
}

# Optimize field names
optimized = optimize_for_llm(data, abbreviate_keys=True)
print(encode(optimized))
# id: 12345
# name: Alice Johnson
# dept: Engineering
# desc: Senior Software Engineer
# created: 2024-01-01
```

### Importance-Based Field Ordering

```python
from toon_format.semantic import order_by_importance

data = {
    "metadata": {"version": 1},
    "created_at": "2024-01-01",
    "description": "Important user data",
    "name": "Alice",
    "id": 123
}

# Reorder by importance (id, name, description come first)
ordered = order_by_importance(data)
# Order: id, name, description, created_at, metadata
```

### Custom Abbreviations

```python
from toon_format.semantic import optimize_for_llm

custom_abbrev = {
    "customer_identifier": "cust_id",
    "transaction_timestamp": "tx_ts",
    "product_catalog": "catalog"
}

optimized = optimize_for_llm(
    data,
    abbreviate_keys=True,
    custom_abbreviations=custom_abbrev
)
```

### Remove Low-Importance Fields

```python
optimized = optimize_for_llm(
    data,
    importance_threshold=0.5,  # Remove fields with <50% importance
    remove_nulls=True          # Remove null values
)
```

### Semantic Chunking

```python
from toon_format.semantic import chunk_by_semantic_boundaries

# Split large dataset into chunks
large_dataset = [{"type": "user", "id": i} for i in range(10000)]

chunks = chunk_by_semantic_boundaries(
    large_dataset,
    max_chunk_size=1000,
    preserve_context=True  # Keep similar items together
)

print(f"Split into {len(chunks)} chunks")
```

---

## 5. Batch Processing

Convert between multiple formats with automatic detection.

### Supported Formats

- JSON
- YAML (requires `pyyaml`)
- XML
- CSV
- TOON

### Auto-Detection

```python
from toon_format.batch import detect_format

# Detect from content
json_content = '{"name": "Alice"}'
format_type = detect_format(json_content)  # "json"

# Detect from filename
format_type = detect_format("", filename="data.yaml")  # "yaml"
```

### Single File Conversion

```python
from toon_format.batch import convert_file

# Auto-detect input format
convert_file("data.json", "data.toon")

# Specify formats
convert_file("input.yaml", "output.toon", from_format="yaml")

# JSON to TOON
convert_file("config.json", "config.toon", to_format="toon")

# TOON to JSON
convert_file("data.toon", "data.json", to_format="json")
```

### Batch Directory Conversion

```python
from toon_format.batch import batch_convert

# Convert all JSON files to TOON
batch_convert(
    "input_json/",
    "output_toon/",
    from_format="json",
    to_format="toon",
    pattern="*.json"
)

# Parallel processing (default)
output_files = batch_convert(
    "data/",
    "converted/",
    parallel=True,
    max_workers=8
)

print(f"Converted {len(output_files)} files")
```

### Format Conversion Examples

```python
from toon_format.batch import convert_data

# JSON → TOON
json_str = '{"name": "Alice", "age": 30}'
toon_str = convert_data(json_str, from_format="json", to_format="toon")

# YAML → TOON
yaml_str = "name: Alice\nage: 30"
toon_str = convert_data(yaml_str, from_format="yaml", to_format="toon")

# CSV → TOON
csv_str = "id,name\n1,Alice\n2,Bob"
toon_str = convert_data(csv_str, from_format="csv", to_format="toon")

# TOON → JSON
toon_str = "name: Alice\nage: 30"
json_str = convert_data(toon_str, from_format="toon", to_format="json")
```

---

## Performance Tips

### Token Efficiency

```python
from toon_format import estimate_savings

data = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ]
}

result = estimate_savings(data)
print(f"Token savings: {result['savings_percent']:.1f}%")
print(f"JSON: {result['json_tokens']} tokens")
print(f"TOON: {result['toon_tokens']} tokens")
```

### Combined Optimizations

```python
from toon_format import encode, estimate_savings
from toon_format.semantic import optimize_for_llm

# Original data
data = {
    "employee_records": [
        {
            "employee_identifier": 1,
            "full_name": "Alice Johnson",
            "department_name": "Engineering",
            "email_address": "alice@company.com",
            "metadata": {"created_at": "2024-01-01"}
        }
        # ... many more records
    ]
}

# Optimize
optimized = optimize_for_llm(
    data,
    abbreviate_keys=True,
    order_fields=True,
    remove_nulls=True
)

# Encode
toon_str = encode(optimized)

# Measure savings
savings = estimate_savings(optimized)
print(f"Total savings: {savings['savings_percent']:.1f}%")
```

---

## Best Practices

### 1. Choose the Right Tool

- **Small data** (<1MB): Use standard `encode()`/`decode()`
- **Large data** (>1MB): Use streaming encoder/decoder
- **Batch conversion**: Use `batch_convert()` with parallel processing
- **Type safety**: Use `encode_model()`/`decode_model()` with Pydantic

### 2. Optimize for Your Use Case

- **LLM contexts**: Use `optimize_for_llm()` before encoding
- **API responses**: Use field abbreviation to reduce bandwidth
- **Data analytics**: Use Pandas integration for DataFrames
- **Scientific computing**: Use NumPy integration for arrays

### 3. Error Handling

```python
from toon_format import decode, ToonDecodeError

try:
    data = decode(toon_str, options={"strict": True})
except ToonDecodeError as e:
    print(f"Parsing error: {e}")
```

### 4. Performance Monitoring

```python
import time
from toon_format import encode, count_tokens

start = time.time()
toon_str = encode(large_data)
encode_time = time.time() - start

token_count = count_tokens(toon_str)

print(f"Encoded in {encode_time:.2f}s")
print(f"Token count: {token_count:,}")
```

---

## Migration Guide

### From v0.8 to v0.9

All existing code continues to work. New features are additive:

```python
# v0.8 - still works
from toon_format import encode, decode

# v0.9 - new features available
from toon_format import (
    encode_model,          # New: Pydantic/dataclass support
    stream_encode_array,   # New: Streaming
    optimize_for_llm,      # New: Semantic optimization
    batch_convert,         # New: Batch processing
)
```

---

## Next Steps

- Read the [API Reference](api.md) for detailed function documentation
- Check [Format Specification](format.md) for TOON syntax details
- See [LLM Integration](llm-integration.md) for best practices with LLMs
- Explore the [tests/](../tests/) directory for more examples
