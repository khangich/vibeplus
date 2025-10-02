from __future__ import annotations

import importlib
import io
import json
import os
import sys
import tarfile
from pathlib import Path
from types import MethodType, ModuleType, SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.backend.llm.mock import MockCodeLLM  # noqa: E402
from backend.backend.models import Build, Revision  # noqa: E402


def test_mock_code_llm_prefers_responses_api_for_plan(monkeypatch):
    captured_input: dict[str, object] = {}

    class DummyResponses:
        def create(self, *, model, input, response_format):
            captured_input["model"] = model
            captured_input["input"] = input
            captured_input["response_format"] = response_format
            payload = {
                "style": "cozy",
                "pages": [
                    {"route": "/", "title": "Home", "summary": "Welcome"},
                    {"route": "/about", "title": "About", "summary": "About us"},
                ],
            }
            return SimpleNamespace(output_text=json.dumps(payload))

    llm = MockCodeLLM(client=SimpleNamespace(responses=DummyResponses()))

    def _fail_plan(*_args, **_kwargs):
        raise AssertionError("fallback plan should not run when responses API succeeds")

    monkeypatch.setattr(llm._fallback, "plan", MethodType(_fail_plan, llm._fallback))

    plan = llm.plan("Build a cozy cafe site", "cozy")

    assert plan.pages == ["/", "/about"]
    assert plan.style == "cozy"
    assert captured_input["model"] == llm.plan_model
    formatted_messages = captured_input["input"]
    assert isinstance(formatted_messages, list)
    assert formatted_messages[0]["content"][0]["type"] == "text"


def test_mock_code_llm_chat_completions_fallback(monkeypatch):
    class DummyCompletions:
        def __init__(self):
            self.calls: int = 0

        def create(self, *, model, messages, response_format=None):
            self.calls += 1
            if response_format is not None:
                raise TypeError("response_format not supported")
            payload = {
                "style": "minimal",
                "pages": [
                    {"route": "/", "title": "Home", "summary": "Welcome"},
                ],
            }
            return SimpleNamespace(output_text=json.dumps(payload))

    completions = DummyCompletions()
    llm = MockCodeLLM(client=SimpleNamespace(chat=SimpleNamespace(completions=completions)))

    def _fail_plan(*_args, **_kwargs):
        raise AssertionError("fallback plan should not run when chat completions succeeds")

    monkeypatch.setattr(llm._fallback, "plan", MethodType(_fail_plan, llm._fallback))

    plan = llm.plan("Build a landing page", "minimal")

    assert plan.pages == ["/"]
    assert plan.style == "minimal"
    assert completions.calls == 2

def test_mock_code_llm_scaffold_generates_app(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    llm = MockCodeLLM()
    prompt = "Launch a marketing site for a boutique coffee roaster."

    plan = llm.plan(prompt, vibe="cozy")
    tree = llm.scaffold(plan)
    files = tree.files

    expected_paths = {
        "package.json",
        "pages/index.tsx",
        "pages/about.tsx",
        "pages/contact.tsx",
        "pages/api/health.ts",
    }

    assert expected_paths.issubset(files)
    assert prompt in files["pages/index.tsx"]
    assert '"next": "14.2.3"' in files["package.json"]

    materialized_root = tmp_path / "generated_app"
    for relative_path, contents in files.items():
        target = materialized_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")

    for relative_path in expected_paths:
        assert (materialized_root / relative_path).is_file()


@pytest.mark.integration
def test_worker_pipeline_generates_artifacts_with_real_openai(monkeypatch):
    pytest.importorskip("openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY must be set to exercise the real OpenAI client")

    dummy_rq = ModuleType("rq")
    dummy_rq.Queue = object
    monkeypatch.setitem(sys.modules, "rq", dummy_rq)

    class _StubRedis:
        @staticmethod
        def from_url(*_args, **_kwargs):
            return object()

    dummy_redis = ModuleType("redis")
    dummy_redis.Redis = _StubRedis
    monkeypatch.setitem(sys.modules, "redis", dummy_redis)

    pipeline_module = importlib.import_module("worker.pipeline")
    pipeline_module = importlib.reload(pipeline_module)

    llm = MockCodeLLM()
    if llm._client is None:
        pytest.skip("MockCodeLLM could not initialize an OpenAI client with the provided credentials")

    def _fail_plan(self, *_args, **_kwargs):
        raise AssertionError("MockCodeLLM fallback plan should not run during OpenAI integration test")

    def _fail_scaffold(self, *_args, **_kwargs):
        raise AssertionError("MockCodeLLM fallback scaffold should not run during OpenAI integration test")

    print(">>> OPENAI_API_KEY  ==== ", os.getenv("OPENAI_API_KEY"))
    monkeypatch.setattr(llm._fallback, "plan", MethodType(_fail_plan, llm._fallback), raising=False)
    monkeypatch.setattr(llm._fallback, "scaffold", MethodType(_fail_scaffold, llm._fallback), raising=False)
    monkeypatch.setattr(pipeline_module, "MockCodeLLM", lambda: llm)

    captured_puts: dict[str, dict[str, object]] = {}

    def _capture_put_bytes(path: str, data: bytes, *, content_type: str) -> None:
        captured_puts[path] = {"data": data, "content_type": content_type}

    monkeypatch.setattr(pipeline_module, "put_bytes", _capture_put_bytes)

    settings = SimpleNamespace(preview_base_host="preview.test")
    monkeypatch.setattr(pipeline_module, "get_settings", lambda: settings)

    prompt = "Launch a marketing site for a custom pottery studio."
    revision_id = "rev-openai-integration"
    revision = Revision(id=revision_id, project_id="proj-openai", message=prompt)

    class DummySession:
        def __init__(self, revision_obj: Revision):
            self._revision = revision_obj
            self.build: Build | None = None
            self.added: list[object] = []
            self.committed = False

        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb):
            return False

        def get(self, model, ident):
            if model is Revision and ident == self._revision.id:
                return self._revision
            return None

        def exec(self, _query):
            build = self.build

            class _Result:
                def __init__(self, value):
                    self._value = value

                def first(self):
                    return self._value

            return _Result(build)

        def add(self, instance):
            if isinstance(instance, Build):
                self.build = instance
            self.added.append(instance)

        def commit(self):
            self.committed = True

    session = DummySession(revision)
    monkeypatch.setattr(pipeline_module, "get_session", lambda: session)

    pipeline_module.run_pipeline({"revision_id": revision_id, "prompt": prompt, "vibe": "cozy"})

    artifact_key = f"artifacts/{revision_id}.tar.gz"
    assert artifact_key in captured_puts
    artifact_payload = captured_puts[artifact_key]
    assert artifact_payload["content_type"] == "application/gzip"

    with tarfile.open(fileobj=io.BytesIO(artifact_payload["data"]), mode="r:gz") as archive:
        member_names = {name.lstrip("./") for name in archive.getnames()}
        expected_members = {"package.json", "pages/index.tsx", "pages/api/health.ts"}
        assert expected_members.issubset(member_names)

        index_contents = None
        for candidate in ("pages/index.tsx", "./pages/index.tsx"):
            try:
                handle = archive.extractfile(candidate)
            except KeyError:
                continue
            if handle is not None:
                index_contents = handle.read().decode("utf-8")
                break
        assert index_contents is not None and index_contents.strip()

    preview_prefix = f"previews/{revision_id}/"
    preview_keys = [path for path in captured_puts if path.startswith(preview_prefix)]
    assert preview_keys

    logs_key = f"logs/{revision_id}.log"
    assert logs_key in captured_puts
    assert captured_puts[logs_key]["content_type"] == "text/plain"

    assert session.committed
    assert revision.status == "succeeded"
    assert revision.artifact_path == artifact_key
    assert revision.logs_path == logs_key
    assert session.build is not None
    assert session.build.status == "succeeded"
    expected_preview_url = f"http://{revision_id}.{settings.preview_base_host}:8080/"
    assert session.build.preview_url == expected_preview_url
