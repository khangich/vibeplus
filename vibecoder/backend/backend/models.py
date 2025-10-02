from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("usr%Y%m%d%H%M%S%f"), primary_key=True)
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("prj%Y%m%d%H%M%S%f"), primary_key=True)
    owner_id: str
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Revision(SQLModel, table=True):
    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("rev%Y%m%d%H%M%S%f"), primary_key=True)
    project_id: str = Field(index=True)
    parent_id: Optional[str] = Field(default=None, foreign_key="revision.id")
    message: str
    status: str = Field(default="queued")
    artifact_path: Optional[str] = None
    logs_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Build(SQLModel, table=True):
    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("bld%Y%m%d%H%M%S%f"), primary_key=True)
    revision_id: str = Field(index=True)
    status: str = Field(default="pending")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    preview_url: Optional[str] = None


class Event(SQLModel, table=True):
    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("evt%Y%m%d%H%M%S%f"), primary_key=True)
    project_id: str = Field(index=True)
    revision_id: Optional[str] = Field(default=None, index=True)
    kind: str
    payload_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PreviewSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("prv%Y%m%d%H%M%S%f"), primary_key=True)
    revision_id: str = Field(index=True, unique=True)
    status: str = Field(default="pending")
    port: Optional[int] = None
    url: Optional[str] = None
    process_id: Optional[int] = None
    log_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
