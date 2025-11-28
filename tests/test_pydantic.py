import pytest
from pydantic import BaseModel, ValidationError

from toon_format.pydantic import ToonPydanticModel


class User(ToonPydanticModel):
    name: str
    age: int
    email: str | None = None


def test_schema_to_toon():
    schema = User.schema_to_toon()
    assert "name:str" in schema
    assert "age:int" in schema
    assert "email:" in schema  # optional field


def test_from_toon_success():
    toon = "name:Ansar\nage:25\nemail:null"
    user = User.from_toon(toon)
    assert user.name == "Ansar"
    assert user.age == 25
    assert user.email is None


def test_from_toon_validation_error():
    toon = "name:Ansar\nage:twenty-five"  # wrong type
    with pytest.raises(ValidationError):
        User.from_toon(toon)


def test_from_toon_empty_string():
    with pytest.raises(ValueError, match="Empty string"):
        User.from_toon("")