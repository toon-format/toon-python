# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Streaming encoder/decoder for processing large datasets.

Provides memory-efficient processing of large TOON files using iterators
and generators. Particularly useful for:
- Large JSON/TOON files that don't fit in memory
- Real-time data processing
- Batch processing of multiple documents
- Server-side streaming APIs

Example:
    >>> from toon_format.streaming import stream_encode_array, stream_decode_array
    >>> 
    >>> # Stream encode large dataset
    >>> def data_generator():
    ...     for i in range(1000000):
    ...         yield {"id": i, "value": f"item_{i}"}
    >>> 
    >>> with open("output.toon", "w") as f:
    ...     for chunk in stream_encode_array(data_generator()):
    ...         f.write(chunk)
    >>> 
    >>> # Stream decode
    >>> for item in stream_decode_array("output.toon"):
    ...     process(item)  # Process one item at a time
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, TextIO, Union

from .constants import COLON, COMMA, LIST_ITEM_MARKER, OPEN_BRACKET, CLOSE_BRACKET
from .decoder import decode, parse_primitive
from .encoder import encode
from .types import EncodeOptions, DecodeOptions, JsonValue
from .writer import LineWriter

__all__ = [
    "stream_encode_array",
    "stream_encode_objects",
    "stream_decode_array",
    "stream_decode_objects",
    "StreamEncoder",
    "StreamDecoder",
]


class StreamEncoder:
    """Streaming TOON encoder for large datasets.
    
    Encodes data incrementally without loading entire dataset into memory.
    Useful for processing large files or real-time data streams.
    
    Example:
        >>> encoder = StreamEncoder(output_file="data.toon")
        >>> encoder.start_array(fields=["id", "name"])
        >>> for item in large_dataset:
        ...     encoder.encode_item(item)
        >>> encoder.end_array()
    """
    
    def __init__(
        self,
        output_file: Optional[Union[str, Path, TextIO]] = None,
        options: Optional[EncodeOptions] = None,
        buffer_size: int = 8192
    ):
        """Initialize stream encoder.
        
        Args:
            output_file: Output file path or file object (None for in-memory)
            options: Encoding options
            buffer_size: Write buffer size in bytes
        """
        self.options = options or {}
        self.buffer_size = buffer_size
        self.buffer: List[str] = []
        self.buffer_length = 0
        self.item_count = 0
        self.in_array = False
        self.array_fields: Optional[List[str]] = None
        
        if isinstance(output_file, (str, Path)):
            self.file = open(output_file, 'w', encoding='utf-8')
            self.owns_file = True
        elif output_file is not None:
            self.file = output_file
            self.owns_file = False
        else:
            self.file = None
            self.owns_file = False
    
    def _write(self, text: str) -> None:
        """Write text to buffer or file."""
        if self.file is not None:
            self.buffer.append(text)
            self.buffer_length += len(text)
            
            if self.buffer_length >= self.buffer_size:
                self.flush()
        else:
            self.buffer.append(text)
    
    def flush(self) -> None:
        """Flush buffer to file."""
        if self.file and self.buffer:
            self.file.write(''.join(self.buffer))
            self.buffer.clear()
            self.buffer_length = 0
    
    def start_array(
        self,
        fields: Optional[List[str]] = None,
        delimiter: str = COMMA,
        estimated_length: Optional[int] = None
    ) -> None:
        """Start streaming an array.
        
        Args:
            fields: Field names for tabular arrays (uniform objects)
            delimiter: Delimiter for tabular arrays
            estimated_length: Estimated array length (optional)
        """
        self.in_array = True
        self.array_fields = fields
        self.item_count = 0
        
        # Write array header (we'll update length later)
        if fields:
            # Tabular array header
            length_marker = estimated_length if estimated_length else "N"
            fields_str = delimiter.join(fields)
            header = f"[{length_marker}{delimiter}]{{{fields_str}}}:\n"
        else:
            # List format header
            length_marker = estimated_length if estimated_length else "N"
            header = f"[{length_marker}]:\n"
        
        self._write(header)
    
    def encode_item(self, item: Any) -> None:
        """Encode a single array item.
        
        Args:
            item: Item to encode
        """
        if not self.in_array:
            raise RuntimeError("Must call start_array() before encode_item()")
        
        indent = self.options.get("indent", 2)
        
        if self.array_fields and isinstance(item, dict):
            # Tabular row
            delimiter = self.options.get("delimiter", COMMA)
            values = [str(item.get(field, "")) for field in self.array_fields]
            row = delimiter.join(values)
            self._write(f"{' ' * indent}{row}\n")
        else:
            # List item
            # Encode item on single line if primitive, or multi-line if complex
            if isinstance(item, (str, int, float, bool, type(None))):
                item_str = encode(item, self.options).strip()
                self._write(f"{' ' * indent}{LIST_ITEM_MARKER}{item_str}\n")
            else:
                # Complex item - encode normally then indent
                item_str = encode(item, self.options)
                lines = item_str.split('\n')
                self._write(f"{' ' * indent}{LIST_ITEM_MARKER}{lines[0]}\n")
                for line in lines[1:]:
                    self._write(f"{' ' * (indent * 2)}{line}\n")
        
        self.item_count += 1
    
    def end_array(self) -> None:
        """End the array and finalize output."""
        if not self.in_array:
            raise RuntimeError("No array in progress")
        
        self.in_array = False
        self.flush()
    
    def get_result(self) -> str:
        """Get encoded result (for in-memory encoding)."""
        if self.file is not None:
            raise RuntimeError("Cannot get_result() when writing to file")
        return ''.join(self.buffer)
    
    def close(self) -> None:
        """Close the encoder and file if owned."""
        self.flush()
        if self.owns_file and self.file:
            self.file.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class StreamDecoder:
    """Streaming TOON decoder for large datasets.
    
    Decodes TOON data incrementally without loading entire file into memory.
    
    Example:
        >>> decoder = StreamDecoder("large_file.toon")
        >>> for item in decoder.iter_array():
        ...     process(item)
    """
    
    def __init__(
        self,
        input_file: Union[str, Path, TextIO],
        options: Optional[DecodeOptions] = None,
        chunk_size: int = 8192
    ):
        """Initialize stream decoder.
        
        Args:
            input_file: Input file path or file object
            options: Decoding options
            chunk_size: Read chunk size in bytes
        """
        if isinstance(input_file, (str, Path)):
            self.file = open(input_file, 'r', encoding='utf-8')
            self.owns_file = True
        else:
            self.file = input_file
            self.owns_file = False
        
        self.options = options or DecodeOptions()
        self.chunk_size = chunk_size
    
    def iter_array(self) -> Iterator[JsonValue]:
        """Iterate over array items.
        
        Yields:
            Decoded array items one at a time
        """
        # Read header
        header = self.file.readline().strip()
        
        # Parse header to determine array format
        # Simple implementation - assumes tabular or list format
        if "{" in header:
            # Tabular format
            yield from self._iter_tabular_array(header)
        else:
            # List format
            yield from self._iter_list_array()
    
    def _iter_tabular_array(self, header: str) -> Iterator[Dict[str, Any]]:
        """Iterate over tabular array items."""
        # Parse fields from header
        fields_start = header.index("{") + 1
        fields_end = header.index("}")
        fields_str = header[fields_start:fields_end]
        
        # Determine delimiter
        delimiter = COMMA
        if "\t" in fields_str:
            delimiter = "\t"
        elif "|" in fields_str:
            delimiter = "|"
        
        fields = [f.strip() for f in fields_str.split(delimiter)]
        
        # Read rows
        for line in self.file:
            line = line.strip()
            if not line:
                continue
            
            values = [v.strip() for v in line.split(delimiter)]
            item = {fields[i]: parse_primitive(values[i]) for i in range(min(len(fields), len(values)))}
            yield item
    
    def _iter_list_array(self) -> Iterator[JsonValue]:
        """Iterate over list format array items."""
        current_item_lines: List[str] = []
        base_indent = None
        
        for line in self.file:
            stripped = line.lstrip()
            indent_count = len(line) - len(stripped)
            
            if stripped.startswith(LIST_ITEM_MARKER):
                # New item
                if current_item_lines:
                    # Decode previous item
                    item_text = '\n'.join(current_item_lines)
                    yield decode(item_text, self.options)
                    current_item_lines.clear()
                
                # Start new item
                if base_indent is None:
                    base_indent = indent_count
                
                # Remove "- " prefix
                item_line = stripped[len(LIST_ITEM_MARKER):]
                current_item_lines.append(item_line)
            elif current_item_lines:
                # Continuation of current item
                current_item_lines.append(stripped)
        
        # Decode last item
        if current_item_lines:
            item_text = '\n'.join(current_item_lines)
            yield decode(item_text, self.options)
    
    def close(self) -> None:
        """Close the decoder and file if owned."""
        if self.owns_file and self.file:
            self.file.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def stream_encode_array(
    items: Iterator[Any],
    fields: Optional[List[str]] = None,
    options: Optional[EncodeOptions] = None
) -> Iterator[str]:
    """Stream encode an array of items.
    
    Args:
        items: Iterator of items to encode
        fields: Field names for tabular arrays
        options: Encoding options
        
    Yields:
        TOON string chunks
        
    Example:
        >>> def data_gen():
        ...     for i in range(1000):
        ...         yield {"id": i, "name": f"user_{i}"}
        >>> 
        >>> for chunk in stream_encode_array(data_gen(), fields=["id", "name"]):
        ...     print(chunk, end='')
    """
    encoder = StreamEncoder(options=options)
    encoder.start_array(fields=fields)
    
    # Yield header
    yield encoder.get_result()
    encoder.buffer.clear()
    
    # Yield items
    for item in items:
        encoder.encode_item(item)
        if encoder.buffer_length >= encoder.buffer_size:
            yield encoder.get_result()
            encoder.buffer.clear()
            encoder.buffer_length = 0
    
    # Yield remaining
    encoder.end_array()
    result = encoder.get_result()
    if result:
        yield result


def stream_encode_objects(
    objects: Iterator[Dict[str, Any]],
    options: Optional[EncodeOptions] = None
) -> Iterator[str]:
    """Stream encode a sequence of objects.
    
    Args:
        objects: Iterator of dictionaries
        options: Encoding options
        
    Yields:
        TOON string chunks for each object
    """
    for obj in objects:
        yield encode(obj, options)
        yield '\n---\n'  # Separator between objects


def stream_decode_array(
    input_file: Union[str, Path, TextIO],
    options: Optional[DecodeOptions] = None
) -> Iterator[JsonValue]:
    """Stream decode array items from a TOON file.
    
    Args:
        input_file: Input file path or file object
        options: Decoding options
        
    Yields:
        Decoded array items
        
    Example:
        >>> for item in stream_decode_array("data.toon"):
        ...     process(item)
    """
    with StreamDecoder(input_file, options) as decoder:
        yield from decoder.iter_array()


def stream_decode_objects(
    input_file: Union[str, Path, TextIO],
    options: Optional[DecodeOptions] = None,
    separator: str = '---'
) -> Iterator[Dict[str, Any]]:
    """Stream decode multiple objects from a TOON file.
    
    Args:
        input_file: Input file path or file object
        options: Decoding options
        separator: Object separator
        
    Yields:
        Decoded objects
    """
    if isinstance(input_file, (str, Path)):
        file = open(input_file, 'r', encoding='utf-8')
        owns_file = True
    else:
        file = input_file
        owns_file = False
    
    try:
        current_lines: List[str] = []
        
        for line in file:
            if line.strip() == separator:
                if current_lines:
                    obj_text = '\n'.join(current_lines)
                    yield decode(obj_text, options)  # type: ignore
                    current_lines.clear()
            else:
                current_lines.append(line.rstrip('\n'))
        
        # Decode last object
        if current_lines:
            obj_text = '\n'.join(current_lines)
            yield decode(obj_text, options)  # type: ignore
    finally:
        if owns_file:
            file.close()
