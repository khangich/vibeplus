from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class Plan:
    prompt: str
    pages: list[str]
    style: str


@dataclass
class GeneratedTree:
    files: dict[str, str]


@dataclass
class PatchSet:
    patches: dict[str, str]


class CodeLLM(Protocol):
    def plan(self, prompt: str, vibe: str | None = None) -> Plan:
        ...

    def scaffold(self, plan: Plan) -> GeneratedTree:
        ...

    def edit(self, repo_path: Path, instructions: str) -> PatchSet:
        ...
