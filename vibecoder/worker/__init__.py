from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING

__all__ = ["jobs"]

if TYPE_CHECKING:
    from . import jobs as jobs_module


def __getattr__(name: str) -> ModuleType:
    if name == "jobs":
        module = import_module(".jobs", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
