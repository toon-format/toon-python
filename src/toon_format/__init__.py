"""
pytoon - Token-Oriented Object Notation for Python

A compact data format optimized for transmitting structured information to LLMs
with 30-60% fewer tokens than JSON.
"""

from .decoder import ToonDecodeError, decode
from .encoder import encode
from .types import DecodeOptions, Delimiter, DelimiterKey, EncodeOptions
from .utils import compare_formats, count_tokens, estimate_savings

__version__ = "0.1.1"
__all__ = [
    "encode",
    "decode",
    "ToonDecodeError",
    "Delimiter",
    "DelimiterKey",
    "EncodeOptions",
    "DecodeOptions",
    "count_tokens",
    "estimate_savings",
    "compare_formats",
]
