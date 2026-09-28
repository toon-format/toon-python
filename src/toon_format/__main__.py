"""Allow ``python -m toon_format`` (deprecated; use ``python -m toon``)."""

import sys

from toon.cli import main

sys.exit(main())
