from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from backend.backend.sandbox.allowlist import is_allowed


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def apply_patch(path: Path, patch: str) -> None:
    # Simplified patch application: overwrite file for MVP.
    write_file(path, patch)


def safe_exec(cmd: list[str], cwd: Path, timeout: int = 300) -> str:
    if not is_allowed(cmd):
        raise RuntimeError(f"Command not allowed: {cmd}")
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, check=False)
    output = proc.stdout + "\n" + proc.stderr
    if proc.returncode != 0:
        raise RuntimeError(output)
    return output


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
