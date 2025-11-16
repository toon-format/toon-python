import pytest
from toon_format.csv import parser, writer


def test_parse_to_csv_simple_key_value():
    data = "name: John"
    result = parser.parse_to_csv(data)
    assert "name" in result
    assert result["name"].strip() == "name\nJohn"


def test_parse_to_csv_object():
    data = """
user:
  name: Alice
  age: 25
"""
    result = parser.parse_to_csv(data)
    assert "user" in result
    assert "name,age" in result["user"]
    assert "Alice,25" in result["user"]


def test_parse_to_csv_array():
    data = """
items [2] {id, value}:
  1,foo
  2,bar
"""
    result = parser.parse_to_csv(data)
    assert "items" in result
    assert "id,value" in result["items"]
    assert "1,foo" in result["items"]
    assert "2,bar" in result["items"]


def test_write_csvs(tmp_path):
    csvs = {"test": "col1,col2\n1,2\n3,4\n"}
    out_dir = tmp_path / "csvs"
    zip_name = tmp_path / "csvs.zip"
    out, zip_path = writer.write_csvs(csvs, out_dir=str(out_dir), zip_name=str(zip_name), bom=False, flat=True)
    assert out.exists()
    assert zip_path.exists()
    csv_file = out / "test.csv"
    assert csv_file.exists()
    with open(csv_file, encoding="utf-8") as f:
        content = f.read()
    assert "col1,col2" in content
    assert "1,2" in content
    assert "3,4" in content
