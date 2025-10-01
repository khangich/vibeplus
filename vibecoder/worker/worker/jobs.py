from __future__ import annotations

from worker.worker.pipeline import run_pipeline


def run_revision_pipeline(job_payload: dict[str, str]) -> None:
    run_pipeline(job_payload)
