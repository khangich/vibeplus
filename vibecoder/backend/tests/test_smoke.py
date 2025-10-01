import asyncio
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.backend.db import init_db
from backend.backend.main import app


@pytest.mark.asyncio
async def test_generate_flow(tmp_path, monkeypatch):
    init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        project_resp = await client.post("/projects", json={"title": "Smoke"})
        project_resp.raise_for_status()
        project_id = project_resp.json()["project_id"]

        generate_resp = await client.post(
            f"/projects/{project_id}/generate",
            json={"prompt": "Create a homepage", "mode": "new", "vibe": "minimal"},
        )
        generate_resp.raise_for_status()
        revision_id = generate_resp.json()["revision_id"]

        status = None
        for _ in range(5):
            build_resp = await client.get(f"/builds/{revision_id}")
            if build_resp.status_code == 200:
                body = build_resp.json()
                status = body["status"]
                if status == "succeeded" and body.get("preview_url"):
                    break
            await asyncio.sleep(0.1)

        assert status == "succeeded"

        revision_resp = await client.get(f"/revisions/{revision_id}")
        revision_resp.raise_for_status()
        revision = revision_resp.json()
        assert revision["preview_url"]
        diff_resp = await client.get(f"/revisions/{revision_id}/diff/{revision_id}")
        assert diff_resp.status_code == 200
