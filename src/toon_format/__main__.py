# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""CLI entry point for TOON format.

Allows running the package as a module: python -m toon_format
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
