from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    title: str


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime


class RevisionCreate(BaseModel):
    prompt: str
    mode: str
    base_revision: Optional[str] = None
    vibe: Optional[str] = None


class RevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    message: str
    status: str
    created_at: datetime
    preview_url: Optional[str] = None


class RevisionDetail(RevisionRead):
    artifact_path: Optional[str] = None
    logs_path: Optional[str] = None
    diff: Optional[str] = None


class BuildStatus(BaseModel):
    status: str
    logs_url: Optional[str] = None
    preview_url: Optional[str] = None


class ExportGithub(BaseModel):
    repo: str
    visibility: str


class ExportGithubResponse(BaseModel):
    pr_url: str


class PreviewSessionCreate(BaseModel):
    revision_id: str
    force_rebuild: bool = False


class PreviewSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revision_id: str
    status: str
    url: Optional[str] = None
    port: Optional[int] = None
    log_path: Optional[str] = None
