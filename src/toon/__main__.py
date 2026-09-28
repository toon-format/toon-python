"""Allow ``python -m toon``."""

import sys

from .cli import main

sys.exit(main())
