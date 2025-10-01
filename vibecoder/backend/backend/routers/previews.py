from __future__ import annotations

import mimetypes
from pathlib import PurePosixPath

from fastapi import APIRouter, HTTPException, Response

from ..storage import get_bytes

router = APIRouter(prefix="/previews", tags=["previews"])


def _candidate_rel_paths(path: str) -> list[str]:
    clean = path.strip()
    if clean == "":
        return ["index.html"]

    pure = PurePosixPath(clean)
    if any(part == ".." for part in pure.parts):
        raise HTTPException(status_code=400, detail="Invalid preview path")

    normalized = str(pure).strip("/")
    # Handle root-style and directory-style requests gracefully.
    candidates = [normalized]
    last_part = pure.name
    if last_part and "." not in last_part:
        candidates.append(f"{normalized}.html")
        candidates.append(f"{normalized}/index.html")
    return list(dict.fromkeys(filter(None, candidates)))


@router.get("/{revision_id}/{path:path}")
def serve_preview_asset(revision_id: str, path: str = "") -> Response:
    # The empty string represents the root request.
    attempted_paths = _candidate_rel_paths(path)
    base = f"previews/{revision_id}/"

    for candidate in attempted_paths:
        storage_path = base + candidate
        try:
            payload = get_bytes(storage_path)
        except FileNotFoundError:
            continue

        media_type = mimetypes.guess_type(candidate)[0] or "text/html"
        if media_type.startswith("text/") and "charset" not in media_type:
            media_type = f"{media_type}; charset=utf-8"
        return Response(content=payload, media_type=media_type)

    if path:
        fallback_path = base + "index.html"
        try:
            payload = get_bytes(fallback_path)
        except FileNotFoundError:
            pass
        else:
            return Response(content=payload, media_type="text/html; charset=utf-8")

    raise HTTPException(status_code=404, detail="Preview asset not found")
