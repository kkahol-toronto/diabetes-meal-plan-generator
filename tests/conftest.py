"""Project-wide pytest configuration.

We add the repository root (two levels up from this file) to ``sys.path`` so
imports such as ``import backend...`` work regardless of the working
 directory from which tests are invoked.
"""

import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR)) 