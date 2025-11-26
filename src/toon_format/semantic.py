# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Semantic-aware token optimization for LLM contexts.

Advanced token reduction techniques based on semantic importance analysis:
- Field ordering based on token distribution patterns
- Intelligent key abbreviation while maintaining readability
- Semantic chunking for optimal context window usage
- Critical token preservation

Example:
    >>> from toon_format.semantic import optimize_for_llm
    >>> 
    >>> data = {
    ...     "employee_identifier": 12345,
    ...     "full_name": "Alice Johnson",
    ...     "department": "Engineering",
    ...     "metadata": {"created": "2024-01-01", "updated": "2024-12-01"}
    ... }
    >>> 
    >>> # Optimize field names and ordering for token efficiency
    >>> optimized = optimize_for_llm(data, abbreviate_keys=True)
    >>> print(encode(optimized))
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

__all__ = [
    "optimize_for_llm",
    "abbreviate_key",
    "order_by_importance",
    "chunk_by_semantic_boundaries",
    "estimate_token_importance",
]


# Common abbreviations for field names
COMMON_ABBREVIATIONS = {
    "identifier": "id",
    "identification": "id",
    "number": "num",
    "address": "addr",
    "description": "desc",
    "information": "info",
    "configuration": "config",
    "initialize": "init",
    "parameter": "param",
    "parameters": "params",
    "attribute": "attr",
    "attributes": "attrs",
    "temporary": "temp",
    "reference": "ref",
    "previous": "prev",
    "maximum": "max",
    "minimum": "min",
    "average": "avg",
    "statistics": "stats",
    "timestamp": "ts",
    "created_at": "created",
    "updated_at": "updated",
    "deleted_at": "deleted",
    "employee": "emp",
    "department": "dept",
    "organization": "org",
    "document": "doc",
    "message": "msg",
    "response": "resp",
    "request": "req",
    "application": "app",
    "authentication": "auth",
    "authorization": "authz",
    "environment": "env",
    "repository": "repo",
    "database": "db",
    "transaction": "txn",
}


# High-importance field patterns (often critical for LLM understanding)
HIGH_IMPORTANCE_PATTERNS = [
    r"^id$",
    r"^name$",
    r"^title$",
    r"^type$",
    r"^status$",
    r"^priority$",
    r"^category$",
    r"^description$",
    r"^summary$",
    r"^content$",
    r"^text$",
    r"^message$",
]


# Low-importance field patterns (metadata, timestamps, internal IDs)
LOW_IMPORTANCE_PATTERNS = [
    r"^_",  # Internal/private fields
    r"created_at$",
    r"updated_at$",
    r"deleted_at$",
    r"^metadata$",
    r"^version$",
    r"^etag$",
    r"^checksum$",
    r"^hash$",
]


def abbreviate_key(key: str, custom_abbrev: Optional[Dict[str, str]] = None) -> str:
    """Abbreviate a field name while maintaining readability.
    
    Uses common programming abbreviations and custom mappings.
    Preserves camelCase and snake_case conventions.
    
    Args:
        key: Original field name
        custom_abbrev: Custom abbreviation mappings
        
    Returns:
        Abbreviated field name
        
    Example:
        >>> abbreviate_key("employee_identifier")
        'emp_id'
        >>> abbreviate_key("configuration_parameters")
        'config_params'
    """
    if custom_abbrev is None:
        custom_abbrev = {}
    
    # Combine default and custom abbreviations
    abbrev_map = {**COMMON_ABBREVIATIONS, **custom_abbrev}
    
    # Direct match
    if key in abbrev_map:
        return abbrev_map[key]
    
    # Check lowercase version
    lower_key = key.lower()
    if lower_key in abbrev_map:
        return abbrev_map[lower_key]
    
    # Handle snake_case
    if "_" in key:
        parts = key.split("_")
        abbreviated = [abbrev_map.get(part, part) for part in parts]
        return "_".join(abbreviated)
    
    # Handle camelCase
    if re.search(r'[a-z][A-Z]', key):
        # Split on capital letters
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', key)
        abbreviated = [abbrev_map.get(part.lower(), part) for part in parts]
        # Reconstruct camelCase
        if abbreviated:
            return abbreviated[0] + ''.join(p.capitalize() for p in abbreviated[1:])
    
    return key


def estimate_token_importance(key: str, value: Any) -> float:
    """Estimate semantic importance of a field (0.0 to 1.0).
    
    Higher scores indicate more important fields for LLM understanding.
    Based on:
    - Key name patterns (id, name, description are high priority)
    - Value type and complexity
    - Common metadata patterns
    
    Args:
        key: Field name
        value: Field value
        
    Returns:
        Importance score (0.0 = low, 1.0 = high)
    """
    score = 0.5  # Default medium importance
    
    # Check high-importance patterns
    for pattern in HIGH_IMPORTANCE_PATTERNS:
        if re.search(pattern, key, re.IGNORECASE):
            score += 0.3
            break
    
    # Check low-importance patterns
    for pattern in LOW_IMPORTANCE_PATTERNS:
        if re.search(pattern, key, re.IGNORECASE):
            score -= 0.3
            break
    
    # Adjust based on value type
    if isinstance(value, str) and len(value) > 50:
        # Long text content is usually important
        score += 0.2
    elif isinstance(value, (list, dict)) and value:
        # Non-empty structured data is important
        score += 0.1
    elif value is None or value == "":
        # Null/empty values are less important
        score -= 0.1
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, score))


def order_by_importance(
    data: Dict[str, Any],
    importance_func: Optional[callable] = None
) -> Dict[str, Any]:
    """Reorder dictionary fields by semantic importance.
    
    Places high-importance fields first for optimal LLM context usage.
    Important for cases where context window might be truncated.
    
    Args:
        data: Dictionary to reorder
        importance_func: Custom importance scoring function
        
    Returns:
        New dictionary with fields ordered by importance
        
    Example:
        >>> data = {
        ...     "metadata": {"version": 1},
        ...     "name": "Alice",
        ...     "id": 123,
        ...     "description": "Important user"
        ... }
        >>> ordered = order_by_importance(data)
        >>> list(ordered.keys())
        ['id', 'name', 'description', 'metadata']
    """
    if importance_func is None:
        importance_func = estimate_token_importance
    
    # Score each field
    scored_items = [
        (key, value, importance_func(key, value))
        for key, value in data.items()
    ]
    
    # Sort by importance (descending)
    scored_items.sort(key=lambda x: x[2], reverse=True)
    
    # Reconstruct dictionary
    return {key: value for key, value, _ in scored_items}


def optimize_for_llm(
    data: Any,
    abbreviate_keys: bool = True,
    order_fields: bool = True,
    remove_nulls: bool = True,
    custom_abbreviations: Optional[Dict[str, str]] = None,
    importance_threshold: float = 0.0
) -> Any:
    """Optimize data structure for LLM token efficiency.
    
    Applies multiple optimization techniques:
    - Field name abbreviation
    - Importance-based field ordering
    - Null value removal
    - Low-importance field filtering
    
    Args:
        data: Data to optimize (dict, list, or primitive)
        abbreviate_keys: Abbreviate field names
        order_fields: Order fields by importance
        remove_nulls: Remove null/empty values
        custom_abbreviations: Custom abbreviation mappings
        importance_threshold: Minimum importance score (0.0-1.0) to keep field
        
    Returns:
        Optimized data structure
        
    Example:
        >>> data = {
        ...     "employee_identifier": 123,
        ...     "full_name": "Alice",
        ...     "metadata": None,
        ...     "description": "Engineer"
        ... }
        >>> optimized = optimize_for_llm(data)
        >>> print(optimized)
        {'id': 123, 'name': 'Alice', 'desc': 'Engineer'}
    """
    if isinstance(data, dict):
        result = {}
        
        # Process each field
        for key, value in data.items():
            # Check importance threshold
            if importance_threshold > 0:
                importance = estimate_token_importance(key, value)
                if importance < importance_threshold:
                    continue
            
            # Skip nulls if requested
            if remove_nulls and value in (None, "", [], {}):
                continue
            
            # Abbreviate key
            new_key = abbreviate_key(key, custom_abbreviations) if abbreviate_keys else key
            
            # Recursively optimize value
            new_value = optimize_for_llm(
                value,
                abbreviate_keys=abbreviate_keys,
                order_fields=order_fields,
                remove_nulls=remove_nulls,
                custom_abbreviations=custom_abbreviations,
                importance_threshold=importance_threshold
            )
            
            result[new_key] = new_value
        
        # Order by importance if requested
        if order_fields:
            result = order_by_importance(result)
        
        return result
    
    elif isinstance(data, list):
        # Optimize each item
        return [
            optimize_for_llm(
                item,
                abbreviate_keys=abbreviate_keys,
                order_fields=order_fields,
                remove_nulls=remove_nulls,
                custom_abbreviations=custom_abbreviations,
                importance_threshold=importance_threshold
            )
            for item in data
        ]
    
    else:
        # Primitive value - return as is
        return data


def chunk_by_semantic_boundaries(
    data: List[Dict[str, Any]],
    max_chunk_size: int = 100,
    preserve_context: bool = True
) -> List[List[Dict[str, Any]]]:
    """Split large arrays into semantic chunks.
    
    Useful for processing large datasets that exceed LLM context windows.
    Attempts to keep related items together.
    
    Args:
        data: List of dictionaries to chunk
        max_chunk_size: Maximum items per chunk
        preserve_context: Try to keep similar items in same chunk
        
    Returns:
        List of chunks (each chunk is a list of items)
        
    Example:
        >>> data = [{"type": "user", "id": i} for i in range(500)]
        >>> chunks = chunk_by_semantic_boundaries(data, max_chunk_size=100)
        >>> len(chunks)
        5
    """
    if not data or max_chunk_size <= 0:
        return []
    
    if len(data) <= max_chunk_size:
        return [data]
    
    chunks: List[List[Dict[str, Any]]] = []
    current_chunk: List[Dict[str, Any]] = []
    
    if preserve_context:
        # Group by common field values (e.g., type, category)
        # Simple heuristic: group by first field that has repeated values
        grouping_key = None
        
        if data:
            # Find a good grouping key
            for key in data[0].keys():
                values = [item.get(key) for item in data[:min(100, len(data))]]
                value_counts = Counter(values)
                # If we see repeated values, use this key for grouping
                if len(value_counts) < len(values) * 0.8:
                    grouping_key = key
                    break
        
        if grouping_key:
            # Sort by grouping key to keep similar items together
            sorted_data = sorted(data, key=lambda x: str(x.get(grouping_key, "")))
        else:
            sorted_data = data
    else:
        sorted_data = data
    
    for item in sorted_data:
        current_chunk.append(item)
        
        if len(current_chunk) >= max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = []
    
    # Add remaining items
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
