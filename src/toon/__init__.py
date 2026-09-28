"""TOON (Token-Oriented Object Notation) for Python.

TOON encodes the JSON data model in a compact, line-oriented form that saves
tokens in LLM prompts. This package follows the interface of the standard
:mod:`json` module::

    >>> import toon
    >>> users = [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]
    >>> print(toon.dumps({"users": users}))
    users[2]{id,name}:
      1,Ada
      2,Bob
    >>> toon.loads("tags[2]: a,b")
    {'tags': ['a', 'b']}
"""

from importlib.metadata import PackageNotFoundError, version

from ._api import Delimiter, dump, dumps, load, loads
from ._errors import ToonDecodeError

__all__ = [
    "Delimiter",
    "ToonDecodeError",
    "__toon_spec__",
    "__version__",
    "dump",
    "dumps",
    "load",
    "loads",
]

ToonDecodeError.__module__ = __name__  # shown as toon.ToonDecodeError in tracebacks

__toon_spec__ = "4.1"
"""Version of the TOON specification this package implements."""

try:
    __version__ = version("toon-format")
except PackageNotFoundError:  # pragma: no cover - running from a source tree
    __version__ = "0.0.0"
