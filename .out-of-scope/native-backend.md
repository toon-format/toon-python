# Native Backend

This package is pure Python. It does not bind the Rust implementation through PyO3 or ship any other compiled backend, optional or not.

## Why this is out of scope

A pure Python package installs from a single wheel on every interpreter and platform – CPython, PyPy, GraalPy, free-threaded builds – without a compiler toolchain. A native backend trades that for a wheel matrix per Python version, OS, and architecture, plus a fallback path for everything the matrix misses. @Justar96 laid out the same reasoning when the question first came up: "We're prioritizing pure python for maximal portability (no wheels/toolchains) interpreter coverage PyPy/GraalPy" ([#9](https://github.com/toon-format/toon-python/discussions/9#discussioncomment-14871615)).

Sharing one implementation across languages doesn't buy correctness either. The ports validate against the same language-agnostic test suite (Appendix C), so the Python and Rust decoders agree because both pass it, not because they share code. A binding would also tie Python releases to the Rust crate's API and release schedule.

Anyone who needs a Rust-backed binding can publish it as a separate package.

## Prior requests

- [#9](https://github.com/toon-format/toon-python/discussions/9): "Using the rust library instead of a pure python implementation"
