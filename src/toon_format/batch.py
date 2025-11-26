# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Batch processing with automatic format detection.

Supports converting between multiple formats:
- JSON → TOON
- YAML → TOON
- XML → TOON
- CSV → TOON
- TOON → JSON/YAML/XML/CSV

Includes parallel processing for large batches.

Example:
    >>> from toon_format.batch import convert_file, batch_convert
    >>> 
    >>> # Auto-detect and convert single file
    >>> convert_file("data.json", "data.toon")
    >>> 
    >>> # Batch convert directory
    >>> batch_convert("input/", "output/", from_format="json", to_format="toon")
"""

import concurrent.futures
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from .decoder import decode
from .encoder import encode
from .types import DecodeOptions, EncodeOptions

__all__ = [
    "detect_format",
    "convert_file",
    "batch_convert",
    "convert_data",
    "FormatType",
]

FormatType = Literal["json", "yaml", "xml", "csv", "toon", "auto"]


def detect_format(
    content: str,
    filename: Optional[str] = None
) -> FormatType:
    """Automatically detect data format from content or filename.
    
    Uses multiple heuristics:
    1. File extension
    2. Content analysis
    3. Structure patterns
    
    Args:
        content: File content
        filename: Optional filename for extension-based detection
        
    Returns:
        Detected format type
        
    Example:
        >>> content = '{"name": "Alice", "age": 30}'
        >>> detect_format(content)
        'json'
    """
    # Try extension first
    if filename:
        ext = Path(filename).suffix.lower()
        if ext == ".json":
            return "json"
        elif ext in (".yaml", ".yml"):
            return "yaml"
        elif ext == ".xml":
            return "xml"
        elif ext == ".csv":
            return "csv"
        elif ext == ".toon":
            return "toon"
    
    # Content-based detection
    content = content.strip()
    
    if not content:
        return "json"  # Default
    
    # JSON detection
    if (content.startswith("{") and content.endswith("}")) or \
       (content.startswith("[") and content.endswith("]")):
        try:
            json.loads(content)
            return "json"
        except (json.JSONDecodeError, ValueError):
            pass
    
    # XML detection
    if content.startswith("<") and content.endswith(">"):
        if re.match(r'<\?xml', content, re.IGNORECASE) or \
           re.match(r'<[a-zA-Z]', content):
            return "xml"
    
    # YAML detection (simple heuristics)
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*:\s', content, re.MULTILINE):
        # Check for YAML-specific syntax
        if "---" in content or re.search(r'^\s+-\s', content, re.MULTILINE):
            return "yaml"
    
    # CSV detection
    if "," in content and "\n" in content:
        lines = content.split("\n")
        if len(lines) >= 2:
            # Check if first two lines have same number of commas
            comma_counts = [line.count(",") for line in lines[:2]]
            if comma_counts[0] == comma_counts[1] and comma_counts[0] > 0:
                return "csv"
    
    # TOON detection - look for TOON-specific patterns
    # Array headers: [N]:
    if re.search(r'\[\d+[,|\t]?\]:', content):
        return "toon"
    
    # Key-value pairs with colons (but not JSON-like)
    if re.search(r'^[a-zA-Z_][a-zA-Z0-9_]*:\s+[^{[]', content, re.MULTILINE):
        return "toon"
    
    # Default to JSON
    return "json"


def parse_json(content: str) -> Any:
    """Parse JSON content."""
    return json.loads(content)


def parse_yaml(content: str) -> Any:
    """Parse YAML content."""
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError as e:
        raise RuntimeError(
            "PyYAML is required for YAML parsing. Install with: pip install pyyaml"
        ) from e


def parse_xml(content: str) -> Any:
    """Parse XML content to dictionary."""
    try:
        import xml.etree.ElementTree as ET
    except ImportError as e:
        raise RuntimeError("xml.etree.ElementTree is required for XML parsing") from e
    
    def element_to_dict(element: ET.Element) -> Any:
        """Convert XML element to dictionary."""
        result: Dict[str, Any] = {}
        
        # Add attributes
        if element.attrib:
            result["@attributes"] = dict(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:  # No children
                return element.text.strip()
            result["@text"] = element.text.strip()
        
        # Add children
        for child in element:
            child_data = element_to_dict(child)
            if child.tag in result:
                # Multiple children with same tag -> list
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result if result else (element.text or "")
    
    root = ET.fromstring(content)
    return {root.tag: element_to_dict(root)}


def parse_csv(content: str) -> List[Dict[str, Any]]:
    """Parse CSV content to list of dictionaries."""
    import csv
    from io import StringIO
    
    reader = csv.DictReader(StringIO(content))
    return list(reader)


def to_json(data: Any, indent: int = 2) -> str:
    """Convert data to JSON."""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def to_yaml(data: Any) -> str:
    """Convert data to YAML."""
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    except ImportError as e:
        raise RuntimeError(
            "PyYAML is required for YAML output. Install with: pip install pyyaml"
        ) from e


def to_xml(data: Any, root_name: str = "root") -> str:
    """Convert data to XML."""
    try:
        import xml.etree.ElementTree as ET
    except ImportError as e:
        raise RuntimeError("xml.etree.ElementTree is required for XML output") from e
    
    def dict_to_element(parent: ET.Element, data: Any) -> None:
        """Convert dictionary to XML elements."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "@attributes":
                    parent.attrib.update(value)
                elif key == "@text":
                    parent.text = str(value)
                else:
                    if isinstance(value, list):
                        for item in value:
                            child = ET.SubElement(parent, key)
                            dict_to_element(child, item)
                    else:
                        child = ET.SubElement(parent, key)
                        dict_to_element(child, value)
        else:
            parent.text = str(data)
    
    # Handle root
    if isinstance(data, dict) and len(data) == 1:
        root_name = list(data.keys())[0]
        root_data = data[root_name]
    else:
        root_data = data
    
    root = ET.Element(root_name)
    dict_to_element(root, root_data)
    
    return ET.tostring(root, encoding='unicode', method='xml')


def to_csv(data: Any) -> str:
    """Convert data to CSV."""
    import csv
    from io import StringIO
    
    if not isinstance(data, list):
        raise ValueError("CSV output requires a list of dictionaries")
    
    if not data:
        return ""
    
    output = StringIO()
    
    # Get all field names
    fieldnames: List[str] = []
    for item in data:
        if isinstance(item, dict):
            for key in item.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()


def convert_data(
    data: Any,
    from_format: FormatType,
    to_format: FormatType,
    encode_options: Optional[EncodeOptions] = None,
    decode_options: Optional[DecodeOptions] = None
) -> str:
    """Convert data between formats.
    
    Args:
        data: Data to convert (string or parsed object)
        from_format: Source format
        to_format: Target format
        encode_options: TOON encoding options
        decode_options: TOON decoding options
        
    Returns:
        Converted data as string
    """
    # Parse input
    if isinstance(data, str):
        if from_format == "auto":
            from_format = detect_format(data)
        
        if from_format == "json":
            parsed = parse_json(data)
        elif from_format == "yaml":
            parsed = parse_yaml(data)
        elif from_format == "xml":
            parsed = parse_xml(data)
        elif from_format == "csv":
            parsed = parse_csv(data)
        elif from_format == "toon":
            parsed = decode(data, decode_options)
        else:
            raise ValueError(f"Unknown input format: {from_format}")
    else:
        parsed = data
    
    # Convert to output format
    if to_format == "json":
        return to_json(parsed)
    elif to_format == "yaml":
        return to_yaml(parsed)
    elif to_format == "xml":
        return to_xml(parsed)
    elif to_format == "csv":
        return to_csv(parsed)
    elif to_format == "toon":
        return encode(parsed, encode_options)
    else:
        raise ValueError(f"Unknown output format: {to_format}")


def convert_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    from_format: FormatType = "auto",
    to_format: FormatType = "toon",
    encode_options: Optional[EncodeOptions] = None,
    decode_options: Optional[DecodeOptions] = None
) -> None:
    """Convert a single file between formats.
    
    Args:
        input_path: Input file path
        output_path: Output file path
        from_format: Source format (default: auto-detect)
        to_format: Target format
        encode_options: TOON encoding options
        decode_options: TOON decoding options
        
    Example:
        >>> convert_file("data.json", "data.toon")
        >>> convert_file("input.yaml", "output.toon", from_format="yaml")
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Read input
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Auto-detect format if needed
    if from_format == "auto":
        from_format = detect_format(content, str(input_path))
    
    # Convert
    output = convert_data(content, from_format, to_format, encode_options, decode_options)
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)


def batch_convert(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    from_format: FormatType = "auto",
    to_format: FormatType = "toon",
    pattern: str = "*.*",
    parallel: bool = True,
    max_workers: Optional[int] = None,
    encode_options: Optional[EncodeOptions] = None,
    decode_options: Optional[DecodeOptions] = None
) -> List[Path]:
    """Batch convert files in a directory.
    
    Args:
        input_dir: Input directory
        output_dir: Output directory
        from_format: Source format (default: auto-detect)
        to_format: Target format
        pattern: File pattern to match (default: all files)
        parallel: Use parallel processing
        max_workers: Max worker threads (default: CPU count)
        encode_options: TOON encoding options
        decode_options: TOON decoding options
        
    Returns:
        List of converted output file paths
        
    Example:
        >>> # Convert all JSON files to TOON
        >>> batch_convert("data/json/", "data/toon/", pattern="*.json")
        >>> 
        >>> # Convert with parallel processing
        >>> batch_convert("input/", "output/", parallel=True, max_workers=4)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Find all matching files
    input_files = list(input_dir.glob(pattern))
    
    if not input_files:
        return []
    
    # Determine output extension
    ext_map = {
        "json": ".json",
        "yaml": ".yaml",
        "xml": ".xml",
        "csv": ".csv",
        "toon": ".toon",
    }
    output_ext = ext_map.get(to_format, ".txt")
    
    def convert_one(input_file: Path) -> Path:
        """Convert single file."""
        # Compute output path
        relative = input_file.relative_to(input_dir)
        output_file = output_dir / relative.with_suffix(output_ext)
        
        # Convert
        convert_file(
            input_file,
            output_file,
            from_format=from_format,
            to_format=to_format,
            encode_options=encode_options,
            decode_options=decode_options
        )
        
        return output_file
    
    # Process files
    output_files: List[Path] = []
    
    if parallel and len(input_files) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(convert_one, f) for f in input_files]
            for future in concurrent.futures.as_completed(futures):
                output_files.append(future.result())
    else:
        for input_file in input_files:
            output_files.append(convert_one(input_file))
    
    return output_files
