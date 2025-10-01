from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db import get_session
from ..models import Build, Revision
from ..schemas import BuildStatus
from ..storage import get_signed_url

router = APIRouter(prefix="/builds", tags=["builds"])


@router.get("/{revision_id}", response_model=BuildStatus)
def get_build(revision_id: str) -> BuildStatus:
    with get_session() as session:
        revision = session.get(Revision, revision_id)
        if not revision:
            raise HTTPException(status_code=404, detail="Revision not found")
        build = session.exec(select(Build).where(Build.revision_id == revision_id)).first()
        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        logs_url = None
        if revision.logs_path:
            try:
                logs_url = get_signed_url(revision.logs_path)
            except Exception:
                logs_url = None
        preview_url = build.preview_url
        return BuildStatus(status=build.status, logs_url=logs_url, preview_url=preview_url)
