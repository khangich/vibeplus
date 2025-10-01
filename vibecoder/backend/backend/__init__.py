from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root is on sys.path so sibling packages (e.g. worker) are importable.
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.append(str(_repo_root))

__all__ = []
