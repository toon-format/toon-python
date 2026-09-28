"""Pydantic integration.

Requires the ``pydantic`` extra: ``pip install "toon-format[pydantic]"``.

Plain :class:`pydantic.BaseModel` instances can be passed to
:func:`toon.dumps` directly. :class:`ToonPydanticModel` adds TOON
counterparts of pydantic's JSON helpers::

    class User(ToonPydanticModel):
        name: str
        age: int

    text = User(name="Ada", age=36).model_dump_toon()
    user = User.model_validate_toon(text)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from typing_extensions import Self

from ._api import dumps, loads

__all__ = ["ToonPydanticModel"]


class ToonPydanticModel(BaseModel):
    """A :class:`pydantic.BaseModel` that reads and writes TOON."""

    @classmethod
    def schema_to_toon(cls, *, indent_size: int = 2, delimiter: str = ",") -> str:
        """Return the model's JSON schema encoded as TOON, for use in prompts."""
        return dumps(
            cls.model_json_schema(), indent_size=indent_size, delimiter=delimiter
        )

    def model_dump_toon(
        self, *, indent_size: int = 2, delimiter: str = ",", **kwargs: Any
    ) -> str:
        """Serialize the model to TOON, like ``BaseModel.model_dump_json``.

        Extra keyword arguments go to :meth:`pydantic.BaseModel.model_dump`
        (for example ``exclude_none=True``).
        """
        data = self.model_dump(mode="json", **kwargs)
        return dumps(data, indent_size=indent_size, delimiter=delimiter)

    @classmethod
    def model_validate_toon(
        cls, text: str | bytes, *, strict: bool = True, **kwargs: Any
    ) -> Self:
        """Decode and validate TOON, like ``BaseModel.model_validate_json``.

        Extra keyword arguments go to :meth:`pydantic.BaseModel.model_validate`.

        Raises:
            toon.ToonDecodeError: The text is not valid TOON.
            pydantic.ValidationError: The data does not match the model.
        """
        return cls.model_validate(loads(text, strict=strict), **kwargs)
