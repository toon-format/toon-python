# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Plugin system for custom type handlers.

Allows registering custom encoders/decoders for domain-specific types
that aren't natively supported by TOON. Examples:
- NumPy arrays
- Pandas DataFrames
- UUID objects
- Custom datetime formats
- Complex numbers
- Decimal numbers with specific precision

Example:
    >>> from toon_format.plugins import register_encoder, register_decoder
    >>> import uuid
    >>> 
    >>> # Register UUID handler
    >>> register_encoder(uuid.UUID, lambda u: str(u))
    >>> register_decoder("UUID", lambda s: uuid.UUID(s))
    >>> 
    >>> # Now UUIDs work seamlessly
    >>> data = {"id": uuid.uuid4(), "name": "Alice"}
    >>> toon_str = encode(data)
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar

__all__ = [
    "register_encoder",
    "register_decoder",
    "unregister_encoder",
    "unregister_decoder",
    "clear_custom_handlers",
    "TypeEncoder",
    "TypeDecoder",
]

T = TypeVar("T")

# Type aliases for encoder/decoder functions
TypeEncoder = Callable[[Any], Any]
TypeDecoder = Callable[[Any], Any]

# Global registries
_CUSTOM_ENCODERS: Dict[Type, TypeEncoder] = {}
_CUSTOM_DECODERS: Dict[str, TypeDecoder] = {}


def register_encoder(type_class: Type[T], encoder: TypeEncoder) -> None:
    """Register a custom encoder for a specific type.
    
    The encoder function should convert instances of `type_class` into
    JSON-serializable Python values (dict, list, str, int, float, bool, None).
    
    Args:
        type_class: The type to register an encoder for
        encoder: Function that converts instances to JSON-serializable values
        
    Example:
        >>> import uuid
        >>> from toon_format.plugins import register_encoder
        >>> 
        >>> def encode_uuid(u):
        ...     return {"__type__": "UUID", "value": str(u)}
        >>> 
        >>> register_encoder(uuid.UUID, encode_uuid)
    """
    _CUSTOM_ENCODERS[type_class] = encoder


def register_decoder(type_name: str, decoder: TypeDecoder) -> None:
    """Register a custom decoder for a specific type identifier.
    
    The decoder function should convert a JSON-serializable value back
    to the original type.
    
    Args:
        type_name: Unique identifier for this type (e.g., "UUID", "DataFrame")
        decoder: Function that converts JSON values back to the original type
        
    Example:
        >>> import uuid
        >>> from toon_format.plugins import register_decoder
        >>> 
        >>> def decode_uuid(data):
        ...     if isinstance(data, dict) and data.get("__type__") == "UUID":
        ...         return uuid.UUID(data["value"])
        ...     return data
        >>> 
        >>> register_decoder("UUID", decode_uuid)
    """
    _CUSTOM_DECODERS[type_name] = decoder


def unregister_encoder(type_class: Type) -> None:
    """Unregister a custom encoder.
    
    Args:
        type_class: The type to unregister
    """
    _CUSTOM_ENCODERS.pop(type_class, None)


def unregister_decoder(type_name: str) -> None:
    """Unregister a custom decoder.
    
    Args:
        type_name: The type identifier to unregister
    """
    _CUSTOM_DECODERS.pop(type_name, None)


def clear_custom_handlers() -> None:
    """Clear all custom encoders and decoders."""
    _CUSTOM_ENCODERS.clear()
    _CUSTOM_DECODERS.clear()


def get_custom_encoder(obj: Any) -> Optional[TypeEncoder]:
    """Get custom encoder for an object's type.
    
    Args:
        obj: Object to find encoder for
        
    Returns:
        Encoder function if registered, None otherwise
    """
    obj_type = type(obj)
    
    # Direct type match
    if obj_type in _CUSTOM_ENCODERS:
        return _CUSTOM_ENCODERS[obj_type]
    
    # Check parent classes (MRO)
    for base_class in obj_type.__mro__[1:]:
        if base_class in _CUSTOM_ENCODERS:
            return _CUSTOM_ENCODERS[base_class]
    
    return None


def get_custom_decoder(type_name: str) -> Optional[TypeDecoder]:
    """Get custom decoder for a type name.
    
    Args:
        type_name: Type identifier
        
    Returns:
        Decoder function if registered, None otherwise
    """
    return _CUSTOM_DECODERS.get(type_name)


def encode_with_custom_handlers(obj: Any) -> Any:
    """Encode object using custom handlers if available.
    
    Args:
        obj: Object to encode
        
    Returns:
        Encoded value (may be the original if no handler found)
    """
    encoder = get_custom_encoder(obj)
    if encoder:
        return encoder(obj)
    return obj


def decode_with_custom_handlers(value: Any) -> Any:
    """Decode value using custom handlers if applicable.
    
    Looks for special "__type__" field in dictionaries to identify
    custom types that need decoding.
    
    Args:
        value: Value to decode
        
    Returns:
        Decoded value (may be the original if no handler found)
    """
    if isinstance(value, dict) and "__type__" in value:
        type_name = value["__type__"]
        decoder = get_custom_decoder(type_name)
        if decoder:
            return decoder(value)
    
    return value


# Built-in handlers for common types

def _register_builtin_handlers() -> None:
    """Register built-in handlers for common types."""
    try:
        import uuid
        
        register_encoder(
            uuid.UUID,
            lambda u: {"__type__": "UUID", "value": str(u)}
        )
        
        register_decoder(
            "UUID",
            lambda data: uuid.UUID(data["value"]) if isinstance(data, dict) else data
        )
    except ImportError:
        pass
    
    try:
        from decimal import Decimal
        
        register_encoder(
            Decimal,
            lambda d: {"__type__": "Decimal", "value": str(d)}
        )
        
        register_decoder(
            "Decimal",
            lambda data: Decimal(data["value"]) if isinstance(data, dict) else data
        )
    except ImportError:
        pass
    
    try:
        from datetime import datetime, date, time
        
        register_encoder(
            datetime,
            lambda dt: {"__type__": "datetime", "value": dt.isoformat()}
        )
        
        register_encoder(
            date,
            lambda d: {"__type__": "date", "value": d.isoformat()}
        )
        
        register_encoder(
            time,
            lambda t: {"__type__": "time", "value": t.isoformat()}
        )
        
        register_decoder(
            "datetime",
            lambda data: datetime.fromisoformat(data["value"]) if isinstance(data, dict) else data
        )
        
        register_decoder(
            "date",
            lambda data: date.fromisoformat(data["value"]) if isinstance(data, dict) else data
        )
        
        register_decoder(
            "time",
            lambda data: time.fromisoformat(data["value"]) if isinstance(data, dict) else data
        )
    except ImportError:
        pass
    
    try:
        import numpy as np
        
        def encode_ndarray(arr):
            return {
                "__type__": "ndarray",
                "dtype": str(arr.dtype),
                "shape": list(arr.shape),
                "data": arr.tolist()
            }
        
        def decode_ndarray(data):
            if isinstance(data, dict) and data.get("__type__") == "ndarray":
                return np.array(data["data"], dtype=data["dtype"]).reshape(data["shape"])
            return data
        
        register_encoder(np.ndarray, encode_ndarray)
        register_decoder("ndarray", decode_ndarray)
    except ImportError:
        pass
    
    try:
        import pandas as pd
        
        def encode_dataframe(df):
            return {
                "__type__": "DataFrame",
                "columns": list(df.columns),
                "data": df.to_dict(orient='records')
            }
        
        def decode_dataframe(data):
            if isinstance(data, dict) and data.get("__type__") == "DataFrame":
                return pd.DataFrame(data["data"], columns=data["columns"])
            return data
        
        register_encoder(pd.DataFrame, encode_dataframe)
        register_decoder("DataFrame", decode_dataframe)
        
        def encode_series(s):
            return {
                "__type__": "Series",
                "name": s.name,
                "data": s.to_list()
            }
        
        def decode_series(data):
            if isinstance(data, dict) and data.get("__type__") == "Series":
                return pd.Series(data["data"], name=data["name"])
            return data
        
        register_encoder(pd.Series, encode_series)
        register_decoder("Series", decode_series)
    except ImportError:
        pass


# Auto-register built-in handlers on import
_register_builtin_handlers()
