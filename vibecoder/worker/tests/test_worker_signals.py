import importlib
import sys
import types

import pytest


MODULE_PATH = "worker.worker.__main__"


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
        "structlog",
    ):
        sys.modules.pop(name, None)


def _reload_module():
    module = importlib.import_module(MODULE_PATH)
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
