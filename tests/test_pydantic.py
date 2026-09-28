"""The pydantic integration."""

from __future__ import annotations

import pytest

pydantic = pytest.importorskip("pydantic")

import toon  # noqa: E402
from toon.pydantic import ToonPydanticModel  # noqa: E402


class Address(pydantic.BaseModel):
    city: str
    zip: str


class User(ToonPydanticModel):
    name: str
    age: int
    tags: list[str] = pydantic.Field(default_factory=list)
    address: Address | None = None


def test_dumps_accepts_any_base_model() -> None:
    assert (
        toon.dumps({"home": Address(city="Oslo", zip="0150")})
        == 'home:\n  city: Oslo\n  zip: "0150"'
    )


def test_model_dump_toon() -> None:
    user = User(name="Ada", age=36, tags=["math", "code"])
    assert (
        user.model_dump_toon()
        == "name: Ada\nage: 36\ntags[2]: math,code\naddress: null"
    )
    assert (
        user.model_dump_toon(exclude_none=True, delimiter="|")
        == "name: Ada\nage: 36\ntags[2|]: math|code"
    )


def test_model_validate_toon() -> None:
    text = 'name: Ada\nage: 36\naddress:\n  city: Oslo\n  zip: "0150"'
    user = User.model_validate_toon(text)
    assert user == User(name="Ada", age=36, address=Address(city="Oslo", zip="0150"))
    assert User.model_validate_toon(text.encode()) == user


def test_model_validate_toon_errors() -> None:
    with pytest.raises(toon.ToonDecodeError):
        User.model_validate_toon("name: Ada\nage: 36\ntags[3]: a")
    with pytest.raises(pydantic.ValidationError):
        User.model_validate_toon("name: Ada\nage: old")


def test_schema_to_toon() -> None:
    schema = User.schema_to_toon()
    assert toon.loads(schema) == User.model_json_schema()
    assert "properties:" in schema
