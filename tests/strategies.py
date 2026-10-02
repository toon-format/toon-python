"""Hypothesis strategies for values in the JSON data model."""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st

# Characters that exercise quoting, escaping, and delimiter handling.
_TRICKY = st.sampled_from(
    [
        ":",
        ",",
        "|",
        "\t",
        "\n",
        "\r",
        "-",
        "#",
        " ",
        '"',
        "\\",
        "[",
        "]",
        "{",
        "}",
        "\x00",
        "\x1f",
        "é",
        "🚀",
    ]
)
_WORDS = st.sampled_from(
    [
        "",
        "a",
        "id",
        "name",
        "true",
        "false",
        "null",
        "42",
        "-1",
        "05",
        "1e6",
        "[]",
        "- x",
        "a.b",
        "x y",
    ]
)

strings = st.one_of(
    _WORDS,
    st.text(st.one_of(_TRICKY, st.characters(codec="utf-8")), max_size=8),
)
keys = st.one_of(st.sampled_from(["a", "b", "c", "id", "x.y", "_k"]), strings)
numbers = st.one_of(
    st.integers(),
    st.integers(min_value=-(10**30), max_value=10**30),
    st.floats(allow_nan=False, allow_infinity=False),
)
primitives = st.one_of(st.none(), st.booleans(), numbers, strings)


def _uniform_objects(
    children: st.SearchStrategy[Any],
) -> st.SearchStrategy[list[dict[str, Any]]]:
    """Lists of objects sharing one key set, to reach the tabular forms."""
    return st.lists(keys, min_size=1, max_size=3, unique=True).flatmap(
        lambda names: st.lists(
            st.fixed_dictionaries(dict.fromkeys(names, children)),
            min_size=1,
            max_size=4,
        )
    )


def _extend(children: st.SearchStrategy[Any]) -> st.SearchStrategy[Any]:
    return st.one_of(
        st.lists(children, max_size=4),
        st.dictionaries(keys, children, max_size=4),
        _uniform_objects(primitives),
        _uniform_objects(st.fixed_dictionaries({"p": primitives, "q": primitives})),
        _uniform_objects(primitives).map(
            lambda rows: {f"k{i}": row for i, row in enumerate(rows)}
        ),
    )


json_values = st.recursive(primitives, _extend, max_leaves=24)
documents = st.one_of(json_values, st.dictionaries(keys, json_values, max_size=5))
