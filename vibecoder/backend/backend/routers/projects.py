from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db import get_session
from ..models import Project, User
from ..schemas import ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["projects"])


def _ensure_default_user():
    with get_session() as session:
        result = session.exec(select(User).where(User.email == "demo@example.com")).first()
        if result:
            return result
        user = User(email="demo@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@router.post("", response_model=dict)
def create_project(payload: ProjectCreate) -> dict[str, str]:
    user = _ensure_default_user()
    with get_session() as session:
        project = Project(owner_id=user.id, title=payload.title)
        session.add(project)
        session.commit()
        session.refresh(project)
        return {"project_id": project.id}


@router.get("", response_model=list[ProjectRead])
def list_projects() -> list[ProjectRead]:
    with get_session() as session:
        projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
        return [ProjectRead.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str) -> ProjectRead:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectRead.model_validate(project)
