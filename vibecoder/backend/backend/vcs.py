from __future__ import annotations

from dataclasses import dataclass

from .config import get_settings


@dataclass
class ExportPlan:
    repo: str
    visibility: str
    branch: str
    revision_id: str


def export_revision_to_github(revision_id: str, repo: str, visibility: str) -> str:
    settings = get_settings()
    branch = f"vibe/rev-{revision_id}"
    # TODO: integrate with GitHub API. For now, log the intent and return a fake URL.
    base_url = settings.supabase_url or "https://example.com"
    return f"{base_url}/{repo}/pull/{branch}"
