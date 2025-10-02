from __future__ import annotations

import atexit
import io
import os
import shutil
import socket
import subprocess
import tarfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from ..config import get_settings
from ..storage import get_bytes


class PreviewLaunchError(RuntimeError):
    pass


@dataclass
class PreviewLaunchResult:
    revision_id: str
    port: int
    url: str
    workdir: Path
    log_path: Path
    pid: int


@dataclass
class _PreviewProcess:
    process: subprocess.Popen[bytes]
    port: int
    workdir: Path
    log_path: Path
    log_handle: io.TextIOWrapper


_lock = threading.Lock()
_processes: Dict[str, _PreviewProcess] = {}


def get_preview_runtime() -> "LocalPreviewRuntime":
    settings = get_settings()
    if settings.preview_runtime_mode != "local":  # pragma: no cover - future extension
        raise PreviewLaunchError(f"Unsupported preview runtime mode: {settings.preview_runtime_mode}")
    return LocalPreviewRuntime(
        root=Path(settings.preview_runtime_root).resolve(),
        public_url_template=settings.preview_public_url_template,
    )


class LocalPreviewRuntime:
    def __init__(self, *, root: Path, public_url_template: str) -> None:
        self.root = root
        self.public_url_template = public_url_template or "http://localhost:{port}/"
        self.root.mkdir(parents=True, exist_ok=True)

    def launch(self, revision_id: str, artifact_path: str, *, force_rebuild: bool = False) -> PreviewLaunchResult:
        with _lock:
            existing = _processes.get(revision_id)
        if existing is not None:
            if force_rebuild:
                self.stop(revision_id)
            else:
                if existing.process.poll() is None:
                    return PreviewLaunchResult(
                        revision_id=revision_id,
                        port=existing.port,
                        url=self._format_public_url(revision_id, existing.port),
                        workdir=existing.workdir,
                        log_path=existing.log_path,
                        pid=existing.process.pid,
                    )
                self.stop(revision_id)

        workdir = self.root / revision_id
        if force_rebuild and workdir.exists():
            shutil.rmtree(workdir)
        workdir.mkdir(parents=True, exist_ok=True)

        self._extract_artifact(artifact_path, workdir)

        port = self._allocate_port()
        log_path = workdir / "preview.log"
        log_handle = open(log_path, "w", encoding="utf-8")
        try:
            env = os.environ.copy()
            env.setdefault("NODE_ENV", "production")
            env["PORT"] = str(port)

            self._run_blocking(["npm", "install"], workdir, env, log_handle)
            self._run_blocking(["npm", "run", "build"], workdir, env, log_handle)

            start_command = [
                "npm",
                "run",
                "start",
                "--",
                "--hostname",
                "0.0.0.0",
                "--port",
                str(port),
            ]
            process = subprocess.Popen(
                start_command,
                cwd=workdir,
                env=env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
        except Exception:
            log_handle.close()
            raise

        preview_process = _PreviewProcess(
            process=process,
            port=port,
            workdir=workdir,
            log_path=log_path,
            log_handle=log_handle,
        )
        with _lock:
            _processes[revision_id] = preview_process

        return PreviewLaunchResult(
            revision_id=revision_id,
            port=port,
            url=self._format_public_url(revision_id, port),
            workdir=workdir,
            log_path=log_path,
            pid=process.pid,
        )

    def stop(self, revision_id: str) -> None:
        with _lock:
            proc = _processes.pop(revision_id, None)
        if not proc:
            return
        try:
            if proc.process.poll() is None:
                proc.process.terminate()
                try:
                    proc.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.process.kill()
        finally:
            proc.log_handle.close()

    def stop_all(self) -> None:
        with _lock:
            revisions = list(_processes.keys())
        for revision_id in revisions:
            self.stop(revision_id)

    def _extract_artifact(self, artifact_path: str, target: Path) -> None:
        data = get_bytes(artifact_path)
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            archive.extractall(target)

    def _run_blocking(
        self,
        command: list[str],
        cwd: Path,
        env: dict[str, str],
        log_handle: io.TextIOWrapper,
    ) -> None:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
        log_handle.flush()
        if completed.returncode != 0:
            raise PreviewLaunchError(f"Command '{' '.join(command)}' failed with exit code {completed.returncode}")

    def _allocate_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    def _format_public_url(self, revision_id: str, port: int) -> str:
        template = self.public_url_template
        try:
            return template.format(revision=revision_id, port=port)
        except KeyError as exc:  # pragma: no cover - misconfigured template
            raise PreviewLaunchError(f"Invalid preview_public_url_template: missing {exc.args[0]}") from exc


def _shutdown_all() -> None:
    try:
        runtime = get_preview_runtime()
    except Exception:
        return
    runtime.stop_all()


atexit.register(_shutdown_all)
