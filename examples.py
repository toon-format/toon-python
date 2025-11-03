"""Examples demonstrating toon_format usage."""

from toon_format import encode

# Example 1: Simple object
print("=" * 60)
print("Example 1: Simple Object")
print("=" * 60)
data = {"name": "Alice", "age": 30, "city": "New York"}
print("Input:", data)
print("\nTOON Output:")
print(encode(data))

# Example 2: Tabular array
print("\n" + "=" * 60)
print("Example 2: Tabular Array (Uniform Objects)")
print("=" * 60)
users = [
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 25},
    {"id": 3, "name": "Charlie", "age": 35},
]
print("Input:", users)
print("\nTOON Output:")
print(encode(users))

# Example 3: Complex nested structure
print("\n" + "=" * 60)
print("Example 3: Complex Nested Structure")
print("=" * 60)
data = {
    "metadata": {"version": 1, "author": "test"},
    "items": [
        {"id": 1, "name": "Item1", "price": 9.99},
        {"id": 2, "name": "Item2", "price": 19.99},
    ],
    "tags": ["alpha", "beta", "gamma"],
}
print("Input:", data)
print("\nTOON Output:")
print(encode(data))

# Example 4: Different delimiters
print("\n" + "=" * 60)
print("Example 4: Different Delimiters")
print("=" * 60)
arr = [1, 2, 3, 4, 5]
print("Input:", arr)
print("\nComma (default):")
print(encode(arr))
print("\nTab delimiter:")
print(encode(arr, {"delimiter": "\t"}))
print("\nPipe delimiter:")
print(encode(arr, {"delimiter": "|"}))

# Example 5: Length markers
print("\n" + "=" * 60)
print("Example 5: Length Markers")
print("=" * 60)
users = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
]
print("Input:", users)
print("\nWith length marker:")
print(encode(users, {"length_marker": True}))

# Example 6: Primitive arrays
print("\n" + "=" * 60)
print("Example 6: Primitive Arrays")
print("=" * 60)
print("Numbers:", encode([1, 2, 3, 4, 5]))
print("Strings:", encode(["apple", "banana", "cherry"]))
print("Mixed:", encode([1, "two", True, None]))

# Example 7: Token comparison
print("\n" + "=" * 60)
print("Example 7: Token Efficiency Demo")
print("=" * 60)
import json

data = {
    "users": [
        {"id": 1, "name": "Alice", "age": 30, "active": True},
        {"id": 2, "name": "Bob", "age": 25, "active": True},
        {"id": 3, "name": "Charlie", "age": 35, "active": False},
    ]
}

json_str = json.dumps(data)
toon_str = encode(data)

print(f"JSON length: {len(json_str)} characters")
print(f"TOON length: {len(toon_str)} characters")
print(f"Reduction: {100 * (1 - len(toon_str) / len(json_str)):.1f}%")
print("\nJSON:")
print(json_str)
print("\nTOON:")
print(toon_str)
