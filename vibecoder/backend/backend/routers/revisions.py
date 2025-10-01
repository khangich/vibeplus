from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db import get_session
from ..models import Build, Event, Project, Revision
from ..schemas import RevisionDetail, RevisionRead

router = APIRouter(tags=["revisions"])


@router.get("/revisions", response_model=list[RevisionRead])
def list_recent_revisions() -> list[RevisionRead]:
    with get_session() as session:
        revisions = session.exec(select(Revision).order_by(Revision.created_at.desc()).limit(20)).all()
        return [_to_read(session, revision) for revision in revisions]


@router.get("/revisions/{revision_id}", response_model=RevisionDetail)
def get_revision(revision_id: str) -> RevisionDetail:
    with get_session() as session:
        revision = session.get(Revision, revision_id)
        if not revision:
            raise HTTPException(status_code=404, detail="Revision not found")
        build = session.exec(select(Build).where(Build.revision_id == revision.id)).first()
        diff_event = session.exec(
            select(Event).where(Event.revision_id == revision.id, Event.kind == "diff").order_by(Event.created_at.desc())
        ).first()
        return RevisionDetail(
            id=revision.id,
            project_id=revision.project_id,
            message=revision.message,
            status=revision.status,
            created_at=revision.created_at,
            artifact_path=revision.artifact_path,
            logs_path=revision.logs_path,
            preview_url=build.preview_url if build else None,
            diff=diff_event.payload_json if diff_event else None,
        )


@router.get("/revisions/{revision_id}/diff/{previous_id}")
def get_diff(revision_id: str, previous_id: str) -> dict[str, str]:
    with get_session() as session:
        diff_event = session.exec(
            select(Event).where(Event.revision_id == revision_id, Event.kind == "diff")
        ).first()
        if not diff_event:
            raise HTTPException(status_code=404, detail="Diff not available")
        return {"diff": diff_event.payload_json}


@router.get("/projects/{project_id}/revisions", response_model=list[RevisionRead])
def list_project_revisions(project_id: str) -> list[RevisionRead]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        revisions = session.exec(
            select(Revision).where(Revision.project_id == project_id).order_by(Revision.created_at.desc())
        ).all()
        return [_to_read(session, revision) for revision in revisions]


def _to_read(session, revision: Revision) -> RevisionRead:
    build = session.exec(select(Build).where(Build.revision_id == revision.id)).first()
    return RevisionRead(
        id=revision.id,
        project_id=revision.project_id,
        message=revision.message,
        status=revision.status,
        created_at=revision.created_at,
        preview_url=build.preview_url if build else None,
    )
