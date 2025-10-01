from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .routers import auth, builds, export, generate, health, previews, projects, revisions
import os

settings = get_settings()

app = FastAPI(title="Vibecoder API", version="0.1.0")

# Read allowed origins from environment
cors_origins = os.getenv("CORS_ORIGINS", "")
if cors_origins:
    origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
else:
    # Fallback: allow localhost for dev
    origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(generate.router)
app.include_router(revisions.router)
app.include_router(builds.router)
app.include_router(export.router)
app.include_router(previews.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {"message": "Vibecoder API"}
