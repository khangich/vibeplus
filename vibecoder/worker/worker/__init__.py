from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING

__all__ = ["jobs"]

if TYPE_CHECKING:  # pragma: no cover - import for type checkers only
    from . import jobs as jobs_module

    jobs: jobs_module


def __getattr__(name: str) -> ModuleType:
    if name == "jobs":
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
