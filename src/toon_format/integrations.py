# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Integration with popular Python data modeling libraries.

Provides seamless encoding/decoding support for:
- Pydantic models (v1 and v2)
- Python dataclasses
- attrs classes

This enables type-safe serialization with runtime validation and
modern Python type hint integration.

Example:
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

import dataclasses
import inspect
from typing import Any, Dict, Optional, Type, TypeVar, get_type_hints

from .decoder import decode
from .encoder import encode
from .types import DecodeOptions, EncodeOptions

__all__ = ["encode_model", "decode_model", "is_supported_model", "model_to_dict"]

T = TypeVar("T")


def is_pydantic_model(obj: Any) -> bool:
    """Check if object is a Pydantic model instance or class.
    
    Args:
        obj: Object to check
        
    Returns:
        True if obj is a Pydantic model
    """
    try:
        # Try Pydantic v2
        from pydantic import BaseModel
        
        if isinstance(obj, type):
            return issubclass(obj, BaseModel)
        return isinstance(obj, BaseModel)
    except ImportError:
        pass
    
    try:
        # Try Pydantic v1
        from pydantic import BaseModel as BaseModelV1
        
        if isinstance(obj, type):
            return issubclass(obj, BaseModelV1)
        return isinstance(obj, BaseModelV1)
    except ImportError:
        pass
    
    return False


def is_attrs_class(obj: Any) -> bool:
    """Check if object is an attrs class instance or class.
    
    Args:
        obj: Object to check
        
    Returns:
        True if obj is an attrs class
    """
    try:
        import attrs
        
        if isinstance(obj, type):
            return attrs.has(obj)
        return attrs.has(type(obj))
    except ImportError:
        return False


def is_supported_model(obj: Any) -> bool:
    """Check if object is a supported model type.
    
    Supports:
    - Pydantic models (v1 and v2)
    - Python dataclasses
    - attrs classes
    
    Args:
        obj: Object to check
        
    Returns:
        True if obj is a supported model type
    """
    if dataclasses.is_dataclass(obj):
        return True
    if is_pydantic_model(obj):
        return True
    if is_attrs_class(obj):
        return True
    return False


def model_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert a model instance to a dictionary.
    
    Args:
        obj: Model instance (Pydantic, dataclass, or attrs)
        
    Returns:
        Dictionary representation of the model
        
    Raises:
        TypeError: If obj is not a supported model type
    """
    # Try Pydantic first (has built-in dict method)
    if is_pydantic_model(obj):
        try:
            # Pydantic v2
            return obj.model_dump()
        except AttributeError:
            # Pydantic v1
            return obj.dict()
    
    # Try dataclass
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    
    # Try attrs
    if is_attrs_class(obj):
        import attrs
        return attrs.asdict(obj)
    
    raise TypeError(
        f"Unsupported model type: {type(obj).__name__}. "
        "Supported types: Pydantic models, dataclasses, attrs classes"
    )


def dict_to_model(data: Dict[str, Any], model_class: Type[T]) -> T:
    """Convert a dictionary to a model instance.
    
    Args:
        data: Dictionary to convert
        model_class: Target model class
        
    Returns:
        Instance of model_class
        
    Raises:
        TypeError: If model_class is not a supported model type
    """
    # Try Pydantic
    if is_pydantic_model(model_class):
        try:
            # Pydantic v2
            return model_class.model_validate(data)
        except AttributeError:
            # Pydantic v1
            return model_class.parse_obj(data)
    
    # Try dataclass
    if dataclasses.is_dataclass(model_class):
        return model_class(**data)
    
    # Try attrs
    if is_attrs_class(model_class):
        return model_class(**data)
    
    raise TypeError(
        f"Unsupported model type: {model_class.__name__}. "
        "Supported types: Pydantic models, dataclasses, attrs classes"
    )


def encode_model(
    model: Any,
    options: Optional[EncodeOptions] = None,
    validate: bool = True
) -> str:
    """Encode a Pydantic model, dataclass, or attrs instance to TOON format.
    
    Args:
        model: Model instance to encode
        options: Optional encoding options
        validate: Whether to validate before encoding (default: True)
        
    Returns:
        TOON-formatted string
        
    Raises:
        TypeError: If model is not a supported type
        ValidationError: If validation fails (Pydantic only)
        
    Example:
        >>> from dataclasses import dataclass
        >>> from toon_format import encode_model
        >>> 
        >>> @dataclass
        ... class Point:
        ...     x: int
        ...     y: int
        >>> 
        >>> point = Point(x=10, y=20)
        >>> print(encode_model(point))
        x: 10
        y: 20
    """
    if not is_supported_model(model):
        raise TypeError(
            f"Unsupported model type: {type(model).__name__}. "
            "Use regular encode() for plain dicts/lists, or use a supported model type."
        )
    
    # Validate if requested (Pydantic only)
    if validate and is_pydantic_model(model):
        try:
            # Pydantic v2
            model.model_validate(model)
        except AttributeError:
            # Pydantic v1 - validation happens automatically on construction
            pass
    
    # Convert to dict and encode
    data = model_to_dict(model)
    return encode(data, options)


def decode_model(
    input_str: str,
    model_class: Type[T],
    decode_options: Optional[DecodeOptions] = None,
    validate: bool = True
) -> T:
    """Decode a TOON string to a Pydantic model, dataclass, or attrs instance.
    
    Args:
        input_str: TOON-formatted string
        model_class: Target model class
        decode_options: Optional decoding options
        validate: Whether to validate after decoding (default: True)
        
    Returns:
        Instance of model_class
        
    Raises:
        TypeError: If model_class is not a supported type
        ToonDecodeError: If TOON parsing fails
        ValidationError: If validation fails (Pydantic only)
        
    Example:
        >>> from pydantic import BaseModel
        >>> from toon_format import decode_model
        >>> 
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> 
        >>> toon_str = "name: Alice\\nage: 30"
        >>> user = decode_model(toon_str, User)
        >>> print(user.name, user.age)
        Alice 30
    """
    if not is_supported_model(model_class):
        raise TypeError(
            f"Unsupported model type: {model_class.__name__}. "
            "Supported types: Pydantic models, dataclasses, attrs classes"
        )
    
    # Decode to dict
    data = decode(input_str, decode_options)
    
    if not isinstance(data, dict):
        raise ValueError(
            f"Expected root object for model decoding, got {type(data).__name__}"
        )
    
    # Convert to model (validation happens automatically for Pydantic)
    return dict_to_model(data, model_class)
