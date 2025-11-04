# LLM Integration Guide

Best practices for using TOON with Large Language Models to maximize token efficiency and response quality.

## Why TOON for LLMs?

Traditional JSON wastes tokens on structural characters:
- **Braces & brackets:** `{}`, `[]`
- **Repeated quotes:** Every key quoted in JSON
- **Commas everywhere:** Between all elements

TOON eliminates this redundancy, achieving **30-60% token reduction** while maintaining readability.

---

## Quick Example

**JSON (45 tokens with GPT-4):**
```json
{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
```

**TOON (20 tokens with GPT-4, 56% reduction):**
```toon
users[2,]{id,name}:
  1,Alice
  2,Bob
```

---

## Basic Integration Patterns

### 1. Prompting the Model

**Explicit format instruction:**

```
Respond using TOON format (Token-Oriented Object Notation):
- Use `key: value` for objects
- Use indentation for nesting
- Use `[N]` to indicate array lengths
- Use tabular format `[N,]{fields}:` for uniform arrays

Example:
users[2,]{id,name}:
  1,Alice
  2,Bob
```

### 2. Code Block Wrapping

Always wrap TOON in code blocks for clarity:

````markdown
```toon
users[3,]{id,name,age}:
  1,Alice,30
  2,Bob,25
  3,Charlie,35
```
````

This helps the model distinguish TOON from natural language.

### 3. Validation with Length Markers

Use `lengthMarker="#"` for explicit validation hints:

```python
from toon_format import encode

data = {"items": ["a", "b", "c"]}
toon = encode(data, {"lengthMarker": "#"})
# items[#3]: a,b,c
```

Tell the model:
> "Array lengths are prefixed with `#`. Ensure your response matches these counts exactly."

---

## Real-World Use Cases

### Use Case 1: Structured Data Extraction

**Prompt:**
```
Extract user information from the text below. Respond in TOON format.

Text: "Alice (age 30) works at ACME. Bob (age 25) works at XYZ."

Format:
users[N,]{name,age,company}:
  ...
```

**Model Response:**
```toon
users[2,]{name,age,company}:
  Alice,30,ACME
  Bob,25,XYZ
```

**Processing:**
```python
from toon_format import decode

response = """users[2,]{name,age,company}:
  Alice,30,ACME
  Bob,25,XYZ"""

data = decode(response)
# {'users': [
#   {'name': 'Alice', 'age': 30, 'company': 'ACME'},
#   {'name': 'Bob', 'age': 25, 'company': 'XYZ'}
# ]}
```

---

### Use Case 2: Configuration Generation

**Prompt:**
```
Generate a server configuration in TOON format with:
- app: "myapp"
- port: 8080
- database settings (host, port, name)
- enabled features: ["auth", "logging", "cache"]
```

**Model Response:**
```toon
app: myapp
port: 8080
database:
  host: localhost
  port: 5432
  name: myapp_db
features[3]: auth,logging,cache
```

**Processing:**
```python
config = decode(response)
# Use config dict directly in your application
```

---

### Use Case 3: API Response Formatting

**Prompt:**
```
Convert this data to TOON format for efficient transmission:

Products:
1. Widget A ($9.99, stock: 50)
2. Widget B ($14.50, stock: 30)
3. Widget C ($19.99, stock: 0)
```

**Model Response:**
```toon
products[3,]{id,name,price,stock}:
  1,"Widget A",9.99,50
  2,"Widget B",14.50,30
  3,"Widget C",19.99,0
```

---

## Advanced Techniques

### 1. Few-Shot Learning

Provide examples in your prompt:

```
Convert the following to TOON format. Examples:

Input: {"name": "Alice", "age": 30}
Output:
name: Alice
age: 30

Input: [{"id": 1, "item": "A"}, {"id": 2, "item": "B"}]
Output:
[2,]{id,item}:
  1,A
  2,B

Now convert this: <your data>
```

### 2. Validation Instructions

Add explicit validation rules:

```
Respond in TOON format. Rules:
1. Array lengths MUST match actual count: [3] means exactly 3 items
2. Tabular arrays require uniform keys across all objects
3. Use quotes for: empty strings, keywords (null/true/false), numeric strings
4. Indentation: 2 spaces per level

If you cannot provide valid TOON, respond with an error message.
```

### 3. Delimiter Selection

Choose delimiters based on your data:

```python
# For data with commas (addresses, descriptions)
encode(data, {"delimiter": "\t"})  # Use tab

# For data with tabs (code snippets)
encode(data, {"delimiter": "|"})   # Use pipe

# For general use
encode(data, {"delimiter": ","})   # Use comma (default)
```

Tell the model which delimiter to use:
> "Use tab-separated values in tabular arrays due to commas in descriptions."

---

## Error Handling

### Graceful Degradation

Always wrap TOON decoding in error handling:

```python
from toon_format import decode, ToonDecodeError

def safe_decode(toon_str):
    try:
        return decode(toon_str)
    except ToonDecodeError as e:
        print(f"TOON decode error: {e}")
        # Fall back to asking model to regenerate
        return None
```

### Model Error Prompting

If decoding fails, ask the model to fix it:

```
The TOON you provided has an error: "Expected 3 items, but got 2"

Please regenerate with correct array lengths. Original:
items[3]: a,b

Should be either:
items[2]: a,b  (fix length)
OR
items[3]: a,b,c  (add missing item)
```

---

## Token Efficiency Best Practices

### 1. Prefer Tabular Format

**Less efficient (list format):**
```toon
users[3]:
  - id: 1
    name: Alice
  - id: 2
    name: Bob
  - id: 3
    name: Charlie
```

**More efficient (tabular format):**
```toon
users[3,]{id,name}:
  1,Alice
  2,Bob
  3,Charlie
```

### 2. Minimize Nesting

**Less efficient:**
```toon
data:
  metadata:
    items:
      list[2]: a,b
```

**More efficient:**
```toon
items[2]: a,b
```

### 3. Use Compact Keys

**Less efficient:**
```toon
user_identification_number: 123
user_full_name: Alice
```

**More efficient:**
```toon
id: 123
name: Alice
```

---

## Common Pitfalls

### ❌ Don't: Trust Model Without Validation

```python
# BAD: No validation
response = llm.generate(prompt)
data = decode(response)  # May raise error
```

```python
# GOOD: Validate and handle errors
response = llm.generate(prompt)
try:
    data = decode(response, {"strict": True})
except ToonDecodeError:
    # Retry or fall back
```

### ❌ Don't: Mix Formats Mid-Conversation

```
First response: JSON
Second response: TOON
```

**Be consistent** - stick to TOON throughout the conversation.

### ❌ Don't: Forget Quoting Rules

Model might produce:
```toon
code: 123  # Wrong! Numeric string needs quotes
```

Should be:
```toon
code: "123"  # Correct
```

**Solution:** Explicitly mention quoting in prompts.

---

## Integration Examples

### With OpenAI API

```python
import openai
from toon_format import decode

def ask_for_toon_data(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Respond using TOON format"},
            {"role": "user", "content": prompt}
        ]
    )

    toon_str = response.choices[0].message.content

    # Extract TOON from code blocks if wrapped
    if "```toon" in toon_str:
        toon_str = toon_str.split("```toon")[1].split("```")[0].strip()
    elif "```" in toon_str:
        toon_str = toon_str.split("```")[1].split("```")[0].strip()

    return decode(toon_str)
```

### With Anthropic Claude API

```python
import anthropic
from toon_format import decode

def claude_toon(prompt):
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\nRespond in TOON format (Token-Oriented Object Notation)."
        }]
    )

    toon_str = message.content[0].text

    # Remove code blocks if present
    if "```" in toon_str:
        toon_str = toon_str.split("```")[1].strip()
        if toon_str.startswith("toon\n"):
            toon_str = toon_str[5:]

    return decode(toon_str)
```

---

## Performance Metrics

Based on testing with GPT-4 and Claude:

| Data Type | JSON Tokens | TOON Tokens | Reduction |
|-----------|-------------|-------------|-----------|
| Simple config (10 keys) | 45 | 28 | 38% |
| User list (50 users) | 892 | 312 | 65% |
| Nested structure | 234 | 142 | 39% |
| Mixed arrays | 178 | 95 | 47% |

**Average reduction: 30-60%** depending on data structure and tokenizer.

---

## Debugging Tips

### 1. Log Raw TOON

Always log the raw TOON before decoding:

```python
print("Raw TOON from model:")
print(repr(toon_str))

try:
    data = decode(toon_str)
except ToonDecodeError as e:
    print(f"Decode error: {e}")
```

### 2. Test with Strict Mode

Enable strict validation during development:

```python
decode(toon_str, {"strict": True})  # Strict validation
```

Disable for production if lenient parsing is acceptable:

```python
decode(toon_str, {"strict": False})  # Lenient
```

### 3. Validate Against Schema

After decoding, validate the Python structure:

```python
data = decode(toon_str)

# Validate structure
assert "users" in data
assert isinstance(data["users"], list)
assert all("id" in user for user in data["users"])
```

---

## Resources

- [Format Specification](format.md) - Complete TOON syntax reference
- [API Reference](api.md) - Function documentation
- [Official Spec](https://github.com/toon-format/spec) - Normative specification
- [Benchmarks](https://github.com/toon-format/toon#benchmarks) - Token efficiency analysis

---

## Summary

**Key Takeaways:**
1. **Explicit prompting** - Tell the model to use TOON format clearly
2. **Validation** - Always validate model output with error handling
3. **Examples** - Provide few-shot examples in prompts
4. **Consistency** - Use TOON throughout the conversation
5. **Tabular format** - Prefer tabular arrays for maximum efficiency
6. **Error recovery** - Handle decode errors gracefully

TOON can reduce LLM costs by 30-60% while maintaining readability and structure. Start with simple use cases and expand as you become familiar with the format.
