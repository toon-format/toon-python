#!/usr/bin/env python3
"""
Advanced TOON Format Features Demo

Showcases all the cutting-edge features in v0.9+:
1. Type-safe model integration (Pydantic, dataclasses)
2. Streaming processing for large datasets
3. Plugin system for custom types
4. Semantic optimization
5. Batch processing with format auto-detection

Run this script to see the features in action.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import toon_format
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# Core TOON functionality
from src.toon_format import encode, decode, estimate_savings, compare_formats

print("=" * 70)
print("TOON Format Advanced Features Demo")
print("=" * 70)
print()

# ============================================================================
# 1. TYPE-SAFE MODEL INTEGRATION
# ============================================================================
print("1. TYPE-SAFE MODEL INTEGRATION")
print("-" * 70)

try:
    from dataclasses import dataclass
    from src.toon_format import encode_model, decode_model
    
    @dataclass
    class Employee:
        id: int
        name: str
        department: str
        salary: float
    
    emp = Employee(id=12345, name="Alice Johnson", department="Engineering", salary=125000.50)
    
    print(f"Original dataclass: {emp}")
    toon_str = encode_model(emp)
    print(f"\nTOON encoded:\n{toon_str}")
    
    decoded = decode_model(toon_str, Employee)
    print(f"\nDecoded back: {decoded}")
    print(f"Type preserved: {isinstance(decoded, Employee)}")
    
except ImportError as e:
    print(f"Skipping (missing dependency): {e}")

print("\n")

# ============================================================================
# 2. STREAMING PROCESSING
# ============================================================================
print("2. STREAMING PROCESSING FOR LARGE DATASETS")
print("-" * 70)

from src.toon_format.streaming import StreamEncoder, stream_decode_array
import tempfile

# Create a temporary file
temp_file = Path(tempfile.gettempdir()) / "toon_demo_large_data.toon"

print(f"Creating large dataset with 10,000 records...")
with StreamEncoder(output_file=temp_file) as encoder:
    encoder.start_array(fields=["id", "username", "score"])
    
    for i in range(10000):
        encoder.encode_item({
            "id": i,
            "username": f"user_{i}",
            "score": (i * 13) % 100
        })
    
    encoder.end_array()

print(f"[OK] Written to: {temp_file}")
print(f"File size: {temp_file.stat().st_size / 1024:.1f} KB")

# Stream decode (memory-efficient)
print("\nReading back first 5 items (streaming):")
count = 0
for item in stream_decode_array(temp_file):
    if count < 5:
        print(f"  {item}")
    count += 1

print(f"[OK] Total items: {count}")

# Cleanup
temp_file.unlink()

print("\n")

# ============================================================================
# 3. PLUGIN SYSTEM
# ============================================================================
print("3. PLUGIN SYSTEM FOR CUSTOM TYPES")
print("-" * 70)

try:
    import uuid
    from datetime import datetime
    from src.toon_format import encode, decode
    
    # These types are automatically supported via plugins!
    data = {
        "request_id": uuid.uuid4(),
        "timestamp": datetime.now(),
        "user": "alice",
        "action": "login"
    }
    
    print(f"Data with custom types:")
    print(f"  request_id: {data['request_id']} (UUID)")
    print(f"  timestamp: {data['timestamp']} (datetime)")
    
    toon_str = encode(data)
    print(f"\nTOON encoded:\n{toon_str}")
    
    decoded = decode(toon_str)
    print(f"\nDecoded:")
    print(f"  request_id type: {type(decoded['request_id']).__name__}")
    print(f"  timestamp type: {type(decoded['timestamp']).__name__}")
    
except ImportError as e:
    print(f"Skipping (missing dependency): {e}")

print("\n")

# ============================================================================
# 4. SEMANTIC OPTIMIZATION
# ============================================================================
print("4. SEMANTIC OPTIMIZATION")
print("-" * 70)

from src.toon_format.semantic import optimize_for_llm, abbreviate_key

# Original verbose data
verbose_data = {
    "employee_identifier": 67890,
    "full_name": "Bob Smith",
    "department_name": "Marketing",
    "email_address": "bob.smith@company.com",
    "created_at": "2024-01-15",
    "updated_at": "2024-12-01",
    "metadata": {
        "version": 1,
        "internal_notes": None
    }
}

print("Original data (verbose field names):")
original_toon = encode(verbose_data)
print(original_toon)

# Optimize
optimized = optimize_for_llm(
    verbose_data,
    abbreviate_keys=True,
    order_fields=True,
    remove_nulls=True
)

print("\nOptimized data (abbreviated, ordered, nulls removed):")
optimized_toon = encode(optimized)
print(optimized_toon)

# Token comparison
original_tokens = len(original_toon.split())
optimized_tokens = len(optimized_toon.split())
savings = ((original_tokens - optimized_tokens) / original_tokens * 100)

print(f"\nToken reduction:")
print(f"  Original: ~{original_tokens} words")
print(f"  Optimized: ~{optimized_tokens} words")
print(f"  Savings: ~{savings:.1f}%")

print("\n")

# ============================================================================
# 5. BATCH PROCESSING
# ============================================================================
print("5. BATCH PROCESSING WITH FORMAT AUTO-DETECTION")
print("-" * 70)

from src.toon_format.batch import detect_format, convert_data

# Test various formats
formats_to_test = {
    "JSON": '{"name": "Alice", "age": 30}',
    "CSV": "id,name,score\n1,Alice,95\n2,Bob,87",
    "TOON": "name: Alice\nage: 30"
}

print("Auto-detecting formats:")
for format_name, content in formats_to_test.items():
    detected = detect_format(content)
    print(f"  {format_name:6s} → detected as: {detected}")

# Convert JSON to TOON
json_data = '''
{
  "users": [
    {"id": 1, "name": "Alice", "role": "admin"},
    {"id": 2, "name": "Bob", "role": "user"}
  ]
}
'''

print("\nConverting JSON to TOON:")
print("Input (JSON):")
print(json_data)

toon_output = convert_data(json_data, from_format="json", to_format="toon")
print("\nOutput (TOON):")
print(toon_output)

# Convert back to JSON
json_output = convert_data(toon_output, from_format="toon", to_format="json")
print("\nConvert back to JSON:")
print(json_output)

print("\n")

# ============================================================================
# 6. TOKEN EFFICIENCY COMPARISON
# ============================================================================
print("6. TOKEN EFFICIENCY COMPARISON")
print("-" * 70)

test_data = {
    "employees": [
        {"id": 1, "name": "Alice Johnson", "dept": "Engineering", "salary": 125000},
        {"id": 2, "name": "Bob Smith", "dept": "Marketing", "salary": 95000},
        {"id": 3, "name": "Charlie Davis", "dept": "Sales", "salary": 105000},
        {"id": 4, "name": "Diana Prince", "dept": "HR", "salary": 85000},
    ]
}

print("Comparing TOON vs JSON token efficiency:\n")
print(compare_formats(test_data))

print("\n")

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("SUMMARY - Advanced Features Demonstrated")
print("=" * 70)
print("""
[OK] Type-safe integration with dataclasses/Pydantic
[OK] Streaming encoder/decoder for large datasets
[OK] Plugin system with automatic UUID/datetime support
[OK] Semantic optimization (field abbreviation & ordering)
[OK] Batch processing with format auto-detection
[OK] 30-60% token reduction vs JSON

For more details, see:
  - docs/features.md
  - docs/api.md
  - tests/ directory for comprehensive examples
""")

print("Demo completed successfully!")
