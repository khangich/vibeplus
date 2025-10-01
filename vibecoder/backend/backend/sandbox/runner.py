from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from .allowlist import is_allowed


class SandboxError(RuntimeError):
    pass


def run_command(command: list[str], cwd: Path, timeout: int = 600) -> str:
    if not is_allowed(command):
        raise SandboxError(f"Command not allowed: {command}")
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    output = proc.stdout + "\n" + proc.stderr
    if proc.returncode != 0:
        raise SandboxError(output)
    return output


def run_build(workdir: Path) -> list[str]:
    logs: list[str] = []
    for cmd in (["npm", "ci"], ["npm", "run", "build"], ["npm", "run", "start", "--", "-p", "8080"]):
        logs.append(run_command(cmd, workdir))
    return logs


def stop_processes(processes: Iterable[subprocess.Popen]) -> None:
    for process in processes:
        try:
            process.terminate()
        except Exception:
            pass
