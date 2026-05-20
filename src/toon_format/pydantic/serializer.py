from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from toon_format import decode, encode

T = TypeVar("T", bound="ToonPydanticModel")


class ToonPydanticModel(BaseModel):
    """
    Pydantic mixin that adds TOON superpowers.

    • schema_to_toon()        → TOON schema string (for LLM few-shot / system prompts)
    • model_dump_toon()       → Serialize this model instance to a TOON string
    • model_validate_toon()   → Parse TOON output directly into a validated model
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

    def model_dump_toon(self, **kwargs) -> str:
        """
        Serialize this model instance into a compact TOON string.

        Mirrors pydantic's ``model_dump_json()``. Extra keyword arguments are
        forwarded to ``model_dump()`` (e.g. ``exclude_none=True``).
        """
        data = self.model_dump(mode="json", **kwargs)
        return encode(data)

    @classmethod
    def model_validate_toon(cls: type[T], text: str) -> T:
        """
        Parse a raw TOON string (from an LLM) into a fully validated model.

        Mirrors pydantic's ``model_validate_json()``.

        Raises:
            ValueError – If TOON parsing fails or the input is empty
            ValidationError – If data doesn't match the model
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
