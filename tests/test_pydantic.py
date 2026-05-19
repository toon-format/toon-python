import pytest
from pydantic import BaseModel, ValidationError

from toon_format.pydantic import ToonPydanticModel


class User(ToonPydanticModel):
    name: str
    age: int
    email: str | None = None


def test_schema_to_toon():
    schema = User.schema_to_toon()
    assert "name:" in schema
    assert "age:" in schema
    assert "email:" in schema  # optional field
    assert "type: object" in schema


def test_model_validate_toon_success():
    toon = "name:Ansar\nage:25\nemail:null"
    user = User.model_validate_toon(toon)
    assert user.name == "Ansar"
    assert user.age == 25
    assert user.email is None


def test_model_validate_toon_validation_error():
    toon = "name:Ansar\nage:twenty-five"  # wrong type
    with pytest.raises(ValidationError):
        User.model_validate_toon(toon)


def test_model_validate_toon_empty_string():
    with pytest.raises(ValueError, match="Empty string"):
        User.model_validate_toon("")


def test_model_dump_toon():
    user = User(name="Ansar", age=25)
    toon = user.model_dump_toon()
    assert "name: Ansar" in toon
    assert "age: 25" in toon


def test_model_dump_toon_roundtrip():
    user = User(name="Ansar", age=25, email="a@b.com")
    restored = User.model_validate_toon(user.model_dump_toon())
    assert restored == user
