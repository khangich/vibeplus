from __future__ import annotations

import io
import tarfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlmodel import select

from backend.backend.config import get_settings
from backend.backend.db import get_session
from backend.backend.llm.mock import MockCodeLLM
from backend.backend.models import Build, Event, Revision
from backend.backend.storage import put_bytes
from worker.worker.logger import get_logger

logger = get_logger("worker")


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


def run_pipeline(payload: dict[str, str]) -> None:
    revision_id = payload["revision_id"]
    prompt = payload.get("prompt", "")
    vibe = payload.get("vibe")

    settings = get_settings()
    llm = MockCodeLLM()
    logger.info("pipeline.start", revision_id=revision_id, step="plan")
    plan = llm.plan(prompt, vibe)
    tree = llm.scaffold(plan)

    with TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        _write_tree(workdir, tree.files)

        artifact_bytes = _tar_directory(workdir)
        artifact_path = f"artifacts/{revision_id}.tar.gz"
        put_bytes(artifact_path, artifact_bytes, content_type="application/gzip")

        diff_text = "Generated files:\n" + "\n".join(sorted(tree.files.keys()))
        log_text = "Plan successful\nScaffolded files\nBuild skipped (mock)\nVerify passed"
        logs_path = f"logs/{revision_id}.log"
        put_bytes(logs_path, log_text.encode(), content_type="text/plain")

    preview_url = f"http://{revision_id}.{settings.preview_base_host}:8080/"

    with get_session() as session:
        revision = session.get(Revision, revision_id)
        if not revision:
            logger.error("revision missing", revision_id=revision_id)
            return
        revision.status = "succeeded"
        revision.artifact_path = artifact_path
        revision.logs_path = logs_path
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
