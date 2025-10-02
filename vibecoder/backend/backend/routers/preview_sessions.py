from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db import get_session
from ..models import Build, PreviewSession, Revision
from ..preview import PreviewLaunchError, get_preview_runtime
from ..schemas import PreviewSessionCreate, PreviewSessionRead


router = APIRouter(prefix="/preview-sessions", tags=["preview-sessions"])


@router.post("/", response_model=PreviewSessionRead)
def create_preview_session(payload: PreviewSessionCreate) -> PreviewSessionRead:
    runtime = get_preview_runtime()

    with get_session() as session:
        revision = session.get(Revision, payload.revision_id)
        if not revision:
            raise HTTPException(status_code=404, detail="Revision not found")
        if not revision.artifact_path:
            raise HTTPException(status_code=400, detail="Revision does not have an artifact")
        artifact_path = revision.artifact_path

    try:
        launch_result = runtime.launch(
            payload.revision_id,
            artifact_path,
            force_rebuild=payload.force_rebuild,
        )
    except PreviewLaunchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    with get_session() as session:
        preview_session = session.exec(
            select(PreviewSession).where(PreviewSession.revision_id == payload.revision_id)
        ).first()
        if preview_session is None:
            preview_session = PreviewSession(revision_id=payload.revision_id)
        preview_session.status = "running"
        preview_session.port = launch_result.port
        preview_session.url = launch_result.url
        preview_session.process_id = launch_result.pid
        preview_session.log_path = str(launch_result.log_path)

        build = session.exec(select(Build).where(Build.revision_id == payload.revision_id)).first()
        if build:
            build.preview_url = launch_result.url
            session.add(build)

        preview_session.updated_at = datetime.utcnow()
        session.add(preview_session)
        session.commit()

        return PreviewSessionRead(
            revision_id=preview_session.revision_id,
            status=preview_session.status,
            url=preview_session.url,
            port=preview_session.port,
            log_path=preview_session.log_path,
        )


@router.delete("/{revision_id}", response_model=PreviewSessionRead)
def delete_preview_session(revision_id: str) -> PreviewSessionRead:
    runtime = get_preview_runtime()
    runtime.stop(revision_id)

    with get_session() as session:
        preview_session = session.exec(
            select(PreviewSession).where(PreviewSession.revision_id == revision_id)
        ).first()
        if preview_session is None:
            raise HTTPException(status_code=404, detail="Preview session not found")

        preview_session.status = "stopped"
        preview_session.process_id = None
        preview_session.port = None
        preview_session.updated_at = datetime.utcnow()
        session.add(preview_session)
        session.commit()

        return PreviewSessionRead(
            revision_id=preview_session.revision_id,
            status=preview_session.status,
            url=preview_session.url,
            port=preview_session.port,
            log_path=preview_session.log_path,
        )
