from __future__ import annotations

from typing import TypeVar, Type

from pydantic import BaseModel, ValidationError
from toon_format import encode, decode

T = TypeVar("T", bound="ToonPydanticModel")


class ToonPydanticModel(BaseModel):
    """
    Pydantic mixin that adds TOON superpowers.

    • schema_to_toon() → TOON schema string (for LLM few-shot / system prompts)
    • from_toon()       → Parse TOON output directly into validated model
    """

    @classmethod
    def schema_to_toon(cls) -> str:
        """
        Convert the model's JSON schema into compact TOON format.
        Use this in your LLM prompt to save 40–60% tokens vs JSON schema.
        """
        schema = cls.model_json_schema()
        # Pydantic gives us full JSON schema
        return encode(schema)

    @classmethod
    def from_toon(cls: Type[T], text: str) -> T:
        """
        Parse raw TOON string (from LLM) into a fully validated Pydantic model.

        Raises:
            ValueError – If TOON parsing fails
            ValidationError – If data doesn't match model
            ValueError – Friendly wrapper for both
        """
        if not text.strip():
            raise ValueError("Empty string cannot be parsed as TOON")

        try:
            data = decode(text.strip())
            return cls.model_validate(data)
        except ValidationError as e:
            raise e  # Let Pydantic's rich error surface (best UX)
        except Exception as e:
            raise ValueError(f"Failed to parse TOON into {cls.__name__}: {e}") from e