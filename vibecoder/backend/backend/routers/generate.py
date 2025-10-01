from __future__ import annotations

from fastapi import APIRouter, HTTPException
from redis.exceptions import RedisError
from sqlmodel import select

from ..db import get_queue, get_redis, get_session
from ..models import Build, Event, Project, Revision
from ..rate_limit import is_rate_limited
from ..schemas import RevisionCreate

router = APIRouter(prefix="/projects", tags=["generate"])


@router.post("/{project_id}/generate")
def trigger_generation(project_id: str, payload: RevisionCreate) -> dict[str, str]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        redis = get_redis()
        try:
            limited = is_rate_limited(redis, project.owner_id)
        except RedisError:
            limited = False
        if limited:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        base_revision = None
        if payload.base_revision:
            base_revision = session.exec(
                select(Revision).where(Revision.id == payload.base_revision, Revision.project_id == project_id)
            ).first()
            if not base_revision:
                raise HTTPException(status_code=400, detail="Base revision not found")

        revision = Revision(
            project_id=project_id,
            parent_id=base_revision.id if base_revision else None,
            message=payload.prompt,
            status="queued",
        )
        session.add(revision)
        build = Build(revision_id=revision.id, status="pending")
        session.add(build)
        event = Event(project_id=project_id, revision_id=revision.id, kind="generate", payload_json=payload.model_dump_json())
        session.add(event)
        session.commit()
        session.refresh(revision)

    job_payload = {
        "revision_id": revision.id,
        "prompt": payload.prompt,
        "mode": payload.mode,
        "vibe": payload.vibe,
    }

    queue = get_queue()
    try:
        queue.enqueue("worker.jobs.run_revision_pipeline", job_payload)
    except Exception:
        from worker.jobs import run_revision_pipeline

        run_revision_pipeline(job_payload)

    return {"revision_id": revision.id}
