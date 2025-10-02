import importlib
import sys
import types

import pytest


MODULE_PATH = "worker.__main__"


@pytest.fixture(autouse=True)
def stub_rq(monkeypatch):
    dummy_rq = types.ModuleType("rq")
    dummy_rq.Connection = object
    dummy_rq.Queue = object
    dummy_rq.Worker = object
    monkeypatch.setitem(sys.modules, "rq", dummy_rq)

    backend_pkg = types.ModuleType("backend")
    backend_pkg.__path__ = []
    backend_backend_pkg = types.ModuleType("backend.backend")
    backend_backend_pkg.__path__ = []
    backend_db_module = types.ModuleType("backend.backend.db")
    backend_db_module.get_redis = lambda: None

    monkeypatch.setitem(sys.modules, "backend", backend_pkg)
    monkeypatch.setitem(sys.modules, "backend.backend", backend_backend_pkg)
    monkeypatch.setitem(sys.modules, "backend.backend.db", backend_db_module)

    worker_redis_module = types.ModuleType("worker.redis_client")
    worker_redis_module.get_redis = lambda: None
    monkeypatch.setitem(sys.modules, "worker.redis_client", worker_redis_module)

    structlog_module = types.ModuleType("structlog")

    class _DummyLogger:
        def bind(self, **kwargs):
            return self

        def debug(self, *args, **kwargs):
            return None

        def info(self, *args, **kwargs):
            return None

        def error(self, *args, **kwargs):
            return None

    def get_logger():
        return _DummyLogger()

    structlog_module.get_logger = get_logger
    structlog_module.processors = types.SimpleNamespace(TimeStamper=lambda fmt: None, JSONRenderer=lambda: None)

    def configure(processors):  # pragma: no cover - configuration no-op for tests
        return processors

    structlog_module.configure = configure
    monkeypatch.setitem(sys.modules, "structlog", structlog_module)
    yield
    for name in (
        "rq",
        "rq.signals",
        "rq.worker",
        "backend",
        "backend.backend",
        "backend.backend.db",
        "worker.redis_client",
        "structlog",
    ):
        sys.modules.pop(name, None)


def _reload_module():
    module = importlib.import_module("worker.__main__")
    if not hasattr(module, "_resolve_signal"):
        module = importlib.import_module("worker.worker.__main__")
    return importlib.reload(module)


def test_register_signal_handlers_connects_handlers(monkeypatch):
    module = _reload_module()

    class DummySignal:
        def __init__(self):
            self.handlers = []

        def connect(self, handler):
            self.handlers.append(handler)

    signals = {
        "job_started": DummySignal(),
        "job_finished": DummySignal(),
        "job_failed": DummySignal(),
    }

    monkeypatch.setattr(module, "_resolve_signal", lambda name: signals.get(name))

    module.register_signal_handlers()

    assert signals["job_started"].handlers == [module._log_job_started]
    assert signals["job_finished"].handlers == [module._log_job_finished]
    assert signals["job_failed"].handlers == [module._log_job_failed]


def test_register_signal_handlers_handles_missing_signals(monkeypatch):
    module = _reload_module()

    monkeypatch.setattr(module, "_resolve_signal", lambda name: None)

    module.register_signal_handlers()
