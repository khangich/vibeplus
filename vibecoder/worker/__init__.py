from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

__all__ = ["jobs"]

if TYPE_CHECKING:
    from . import jobs as jobs_module


# Ensure the nested "worker" package directory is treated as part of this
# package so imports like ``worker.pipeline`` resolve correctly when the
# project is used without installation.
_nested_package = Path(__file__).with_name("worker")
if _nested_package.is_dir():
    __path__.append(str(_nested_package))


def __getattr__(name: str) -> ModuleType:
    if name == "jobs":
        module = import_module(".jobs", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
