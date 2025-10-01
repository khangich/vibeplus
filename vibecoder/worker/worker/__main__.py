from __future__ import annotations

from importlib import import_module
from typing import Any, Optional

from rq import Connection, Queue, Worker

from worker.redis_client import get_redis
from .logger import get_logger

listen_queues = ["default"]
logger = get_logger("worker")


def _resolve_signal(name: str) -> Optional[Any]:
    """Attempt to load an RQ signal by name, handling version differences."""
    for module_name in ("rq.signals", "rq.worker"):
        try:
            module = import_module(module_name)
        except ImportError:  # pragma: no cover - absence is expected in some versions
            continue
        signal = getattr(module, name, None)
        if signal is not None:
            return signal
    return None


def _safe_repr(value: object, max_length: int = 200) -> str:
    """Generate a safe, bounded string representation for logging."""
    try:
        text = repr(value)
    except Exception:  # pragma: no cover - defensive safeguard
        text = f"<{type(value).__name__}>"
    if len(text) > max_length:
        text = text[: max_length - 3] + "..."
    return text


def _log_job_started(job, **kwargs):
    logger.info(
        "job_started",
        job_id=job.id,
        queue=job.origin,
        func=job.func_name,
        args_count=len(job.args or ()),
        kwargs_keys=sorted(job.kwargs.keys()) if job.kwargs else [],
    )


def _log_job_finished(job, connection=None, result=None, **kwargs):
    logger.info(
        "job_finished",
        job_id=job.id,
        queue=job.origin,
        status=job.get_status(refresh=False),
        result_summary=_safe_repr(result) if result is not None else None,
    )


def _log_job_failed(job, connection=None, type_=None, value=None, traceback=None, **kwargs):
    logger.error(
        "job_failed",
        job_id=job.id,
        queue=job.origin,
        exc_type=_safe_repr(type_),
        exc_value=_safe_repr(value),
    )


def register_signal_handlers() -> None:
    signals = {
        "job_started": _resolve_signal("job_started"),
        "job_finished": _resolve_signal("job_finished"),
        "job_failed": _resolve_signal("job_failed"),
    }

    if signals["job_started"] is not None:
        signals["job_started"].connect(_log_job_started)
    else:
        logger.debug("rq job_started signal unavailable; start events will not be logged")

    if signals["job_finished"] is not None:
        signals["job_finished"].connect(_log_job_finished)
    else:
        logger.debug("rq job_finished signal unavailable; finish events will not be logged")

    if signals["job_failed"] is not None:
        signals["job_failed"].connect(_log_job_failed)
    else:
        logger.debug("rq job_failed signal unavailable; failure events will not be logged")


def main() -> None:
    redis = get_redis()
    with Connection(redis):
        register_signal_handlers()
        worker = Worker(list(map(Queue, listen_queues)))
        worker.work(logging_level="DEBUG")


if __name__ == "__main__":
    main()
