from __future__ import annotations

import difflib
from pathlib import Path


def unified_diff(old_dir: Path, new_dir: Path) -> str:
    diff_lines: list[str] = []
    for new_path in sorted(new_dir.rglob("*")):
        if new_path.is_dir():
            continue
        rel_path = new_path.relative_to(new_dir)
        old_path = old_dir / rel_path
        old_text = old_path.read_text(encoding="utf-8") if old_path.exists() else ""
        new_text = new_path.read_text(encoding="utf-8")
        diff = difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile=str(rel_path),
            tofile=str(rel_path),
            lineterm="",
        )
        diff_lines.extend(diff)
    return "\n".join(diff_lines)
