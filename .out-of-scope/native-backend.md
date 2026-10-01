# Native Backend

`toon-format` stays pure Python. A compiled backend – Rust through PyO3 or C++ – belongs in a separate package, not in this one, optional or not.

## Why this is out of scope

A pure Python wheel installs on every interpreter and platform, PyPy and GraalPy included, without a compiler toolchain. A native backend trades that for a wheel matrix per Python version, OS, and architecture. Speed-focused packages already exist on their own: [toons](https://github.com/alesanfra/toons) (Rust) and [ctoon](https://github.com/mohammadraziei/ctoon) (C++) are listed on the [implementations page](https://toonformat.dev/ecosystem/implementations).

## Prior requests

- [#9](https://github.com/toon-format/toon-python/discussions/9) – "Using the rust library instead of a pure python implementation"
