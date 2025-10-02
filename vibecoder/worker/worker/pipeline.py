from __future__ import annotations

import io
import json
import tarfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from sqlmodel import select

from backend.backend.config import get_settings
from backend.backend.db import get_session
from backend.backend.llm.mock import MockCodeLLM
from backend.backend.models import Build, Event, Revision
from backend.backend.storage import put_bytes
from .logger import get_logger

logger = get_logger("worker")

PREVIEW_REQUEST_TIMEOUT_SECONDS = 600


def _write_tree(base: Path, files: dict[str, str]) -> None:
    for rel_path, content in files.items():
        target = base / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _tar_directory(path: Path) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(mode="w:gz", fileobj=buffer) as tar:
        tar.add(path, arcname=".")
    buffer.seek(0)
    return buffer.read()


def _write_preview_manifest(revision_id: str) -> str:
    manifest = {
        "packageManager": "npm",
        "commands": {
            "install": "npm install",
            "build": "npm run build",
            "start": "npm run start -- --hostname 0.0.0.0 --port ${PORT}",
        },
    }
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
    manifest_path = f"manifests/{revision_id}.json"
    put_bytes(manifest_path, manifest_bytes, content_type="application/json")
    return manifest_path


def _trigger_preview_session(revision_id: str, settings) -> str:
    base_url = getattr(settings, "backend_internal_url", "").strip()
    if not base_url:
        logger.warning("preview.launch_skipped", revision_id=revision_id, reason="missing backend_internal_url")
        return ""

    request_url = base_url.rstrip("/") + "/preview-sessions/"
    payload = {"revision_id": revision_id, "force_rebuild": True}
    logger.info("preview.launch_request", revision_id=revision_id, url=request_url)
    try:
        response = httpx.post(request_url, json=payload, timeout=PREVIEW_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network/runtime failures
        logger.error("preview.launch_failed", revision_id=revision_id, error=str(exc))
        return ""

    try:
        data = response.json()
    except ValueError as exc:  # pragma: no cover
        logger.error("preview.launch_invalid_response", revision_id=revision_id, error=str(exc))
        return ""

    preview_url = data.get("url") or ""
    logger.info(
        "preview.launch_success",
        revision_id=revision_id,
        preview_url=preview_url,
        port=data.get("port"),
    )
    return preview_url


def run_pipeline(payload: dict[str, str]) -> None:
    revision_id = payload["revision_id"]
    prompt = payload.get("prompt", "")
    vibe = payload.get("vibe")

    settings = get_settings()
    llm = MockCodeLLM()
    logger.info("pipeline.start", revision_id=revision_id, step="plan")
    plan = llm.plan(prompt, vibe)
    tree = llm.scaffold(plan)

    manifest_path = _write_preview_manifest(revision_id)

    with TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        _write_tree(workdir, tree.files)

        artifact_bytes = _tar_directory(workdir)
        artifact_path = f"artifacts/{revision_id}.tar.gz"
        put_bytes(artifact_path, artifact_bytes, content_type="application/gzip")

        diff_text = "Generated files:\n" + "\n".join(sorted(tree.files.keys()))
        log_lines = [
            "Plan successful",
            "Scaffolded files",
            f"Preview manifest stored at {manifest_path}",
            "Build and runtime will be handled by the preview service",
        ]
        log_text = "\n".join(log_lines)
        logs_path = f"logs/{revision_id}.log"
        put_bytes(logs_path, log_text.encode(), content_type="text/plain")

    with get_session() as session:
        revision = session.get(Revision, revision_id)
        if not revision:
            logger.error("revision missing", revision_id=revision_id)
            return
        revision.artifact_path = artifact_path
        revision.logs_path = logs_path
        session.add(revision)
        session.commit()

    preview_url = ""
    if settings.preview_runtime_mode != "off":
        preview_url = _trigger_preview_session(revision_id, settings)
    else:
        logger.info("preview.runtime_disabled", revision_id=revision_id)

    with get_session() as session:
        revision = session.get(Revision, revision_id)
        if not revision:
            logger.error("revision missing", revision_id=revision_id)
            return
        revision.status = "succeeded"
        session.add(revision)

        build = session.exec(select(Build).where(Build.revision_id == revision_id)).first()
        finished_at = datetime.utcnow()
        if build is None:
            build = Build(revision_id=revision_id, status="succeeded", preview_url=preview_url, finished_at=finished_at)
        else:
            build.status = "succeeded"
            build.finished_at = finished_at
            build.preview_url = preview_url
        session.add(build)

        event = Event(project_id=revision.project_id, revision_id=revision.id, kind="diff", payload_json=diff_text)
        session.add(event)
        session.commit()

    logger.info("pipeline.complete", revision_id=revision_id, step="done", preview_url=preview_url)
