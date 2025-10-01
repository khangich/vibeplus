from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from ..db import get_session
from ..models import Revision
from ..schemas import ExportGithub, ExportGithubResponse
from ..storage import get_signed_url
from ..vcs import export_revision_to_github

router = APIRouter(prefix="/revisions", tags=["export"])


@router.post("/{revision_id}/export/github", response_model=ExportGithubResponse)
def export_github(revision_id: str, payload: ExportGithub) -> ExportGithubResponse:
    with get_session() as session:
        revision = session.get(Revision, revision_id)
        if not revision:
            raise HTTPException(status_code=404, detail="Revision not found")
    pr_url = export_revision_to_github(revision_id, payload.repo, payload.visibility)
    return ExportGithubResponse(pr_url=pr_url)


@router.get("/{revision_id}/export/zip")
def export_zip(revision_id: str):
    with get_session() as session:
        revision = session.get(Revision, revision_id)
        if not revision or not revision.artifact_path:
            raise HTTPException(status_code=404, detail="Artifact not found")
        try:
            url = get_signed_url(revision.artifact_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Artifact missing") from None
    return RedirectResponse(url)
