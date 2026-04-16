import json
from toon_format import encode_json, loads, encode

def test_loads_null_to_none():
    json_str = '{"abc": null, "xyz": 123}'
    data = loads(json_str)
    assert data["abc"] is None
    assert data["xyz"] == 123
    print("test_loads_null_to_none passed")

def test_encode_json_integration():
    json_str = '{"abc": null, "xyz": null}'
    # This should automatically handle null -> None -> TOON null
    toon_output = encode_json(json_str)
    expected = "abc: null\nxyz: null"
    assert toon_output.strip() == expected
    print("test_encode_json_integration passed")

def test_complex_json_integration():
    json_str = '''
    {
        "status": "success",
        "data": {
            "user": null,
            "items": [1, null, 3]
        }
    }
    '''
    toon_output = encode_json(json_str)
    assert "user: null" in toon_output
    # Check for null in items array (can be inline "1,null,3" or list "- null")
    assert "null" in toon_output
    print("test_complex_json_integration passed")

if __name__ == "__main__":
    test_loads_null_to_none()
    test_encode_json_integration()
    test_complex_json_integration()
    print("All JSON integration tests passed!")
