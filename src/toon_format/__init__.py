# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""TOON Format for Python.

Token-Oriented Object Notation (TOON) is a compact, human-readable serialization
format optimized for LLM contexts. Achieves 30-60% token reduction vs JSON while
maintaining readability and structure.

This package provides encoding and decoding functionality with 100% compatibility
with the official TOON specification (v1.3).

Advanced Features (v0.9+):
- Pydantic/dataclass/attrs integration for type-safe serialization
- Streaming encoder/decoder for large datasets
- Plugin system for custom types (NumPy, Pandas, etc.)
- Semantic-aware token optimization
- Batch processing with format auto-detection (JSON, YAML, XML, CSV)

Example:
    >>> from toon_format import encode, decode
    >>> data = {"name": "Alice", "age": 30}
    >>> toon = encode(data)
    >>> print(toon)
    name: Alice
    age: 30
    >>> decode(toon)
    {'name': 'Alice', 'age': 30}
    
    # Advanced: Pydantic integration
    >>> from pydantic import BaseModel
    >>> from toon_format import encode_model, decode_model
    >>> 
    >>> class User(BaseModel):
    ...     name: str
    ...     age: int
    >>> 
    >>> user = User(name="Alice", age=30)
    >>> toon_str = encode_model(user)
    >>> decoded = decode_model(toon_str, User)
"""

from .decoder import ToonDecodeError, decode
from .encoder import encode
from .types import DecodeOptions, Delimiter, DelimiterKey, EncodeOptions
from .utils import compare_formats, count_tokens, estimate_savings

# Advanced features
from .integrations import encode_model, decode_model, is_supported_model, model_to_dict
from .streaming import (
    stream_encode_array,
    stream_encode_objects,
    stream_decode_array,
    stream_decode_objects,
    StreamEncoder,
    StreamDecoder,
)
from .plugins import register_encoder, register_decoder, clear_custom_handlers
from .semantic import optimize_for_llm, abbreviate_key, order_by_importance
from .batch import detect_format, convert_file, batch_convert, convert_data

__version__ = "0.9.0-beta.2"
__all__ = [
    # Core functionality
    "encode",
    "decode",
    "ToonDecodeError",
    "Delimiter",
    "DelimiterKey",
    "EncodeOptions",
    "DecodeOptions",
    
    # Token analysis
    "count_tokens",
    "estimate_savings",
    "compare_formats",
    
    # Model integration
    "encode_model",
    "decode_model",
    "is_supported_model",
    "model_to_dict",
    
    # Streaming
    "stream_encode_array",
    "stream_encode_objects",
    "stream_decode_array",
    "stream_decode_objects",
    "StreamEncoder",
    "StreamDecoder",
    
    # Plugins
    "register_encoder",
    "register_decoder",
    "clear_custom_handlers",
    
    # Semantic optimization
    "optimize_for_llm",
    "abbreviate_key",
    "order_by_importance",
    
    # Batch processing
    "detect_format",
    "convert_file",
    "batch_convert",
    "convert_data",
]
