from __future__ import annotations

import json
import logging
import os
import textwrap
from pathlib import Path
from typing import Any

try:  # pragma: no cover - import guarded for optional dependency
    from openai import OpenAI
except Exception:  # pragma: no cover - library may be absent during tests
    OpenAI = None  # type: ignore

from .interface import CodeLLM, GeneratedTree, PatchSet, Plan


logger = logging.getLogger(__name__)


STYLE_CLASSES = {
    "minimal": "bg-slate-900 text-slate-100",
    "cozy": "bg-amber-50 text-amber-950",
    "retro": "bg-emerald-950 text-emerald-100",
}


PLAN_SCHEMA: dict[str, Any] = {
    "name": "site_plan",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "style": {"type": "string"},
            "pages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "route": {"type": "string", "pattern": r"^/"},
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                    },
                    "required": ["route", "title", "summary"],
                    "additionalProperties": False,
                },
                "minItems": 1,
            },
        },
        "required": ["style", "pages"],
        "additionalProperties": False,
    },
}


SCAFFOLD_SCHEMA: dict[str, Any] = {
    "name": "file_tree",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "contents": {"type": "string"},
                    },
                    "required": ["path", "contents"],
                    "additionalProperties": False,
                },
                "minItems": 1,
            }
        },
        "required": ["files"],
        "additionalProperties": False,
    },
}


class MockCodeLLM(CodeLLM):
    def __init__(
        self,
        *,
        client: OpenAI | None = None,
        plan_model: str | None = None,
        scaffold_model: str | None = None,
    ) -> None:
        self._fallback = _DeterministicLLM()
        self._client = client or self._build_client()
        self.plan_model = plan_model or os.getenv("OPENAI_PLAN_MODEL", "gpt-4.1-mini")
        self.scaffold_model = scaffold_model or os.getenv("OPENAI_CODE_MODEL", "o4-mini")
        self._last_plan_details: list[dict[str, str]] | None = None

    def plan(self, prompt: str, vibe: str | None = None) -> Plan:
        if not self._client:
            return self._fallback.plan(prompt, vibe)
        try:
            plan_payload = self._request_plan(prompt, vibe)
            self._last_plan_details = plan_payload.get("pages", [])
            pages = [page.get("route", "/") for page in self._last_plan_details]
            style = plan_payload.get("style") or vibe or "minimal"
            return Plan(prompt=prompt, pages=pages, style=style)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("plan_fallback", exc_info=True)
            return self._fallback.plan(prompt, vibe)

    def scaffold(self, plan: Plan) -> GeneratedTree:
        if not self._client:
            return self._fallback.scaffold(plan)
        try:
            files = self._request_scaffold(plan)
            return GeneratedTree(files=files)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("scaffold_fallback", exc_info=True)
            return self._fallback.scaffold(plan)

    def edit(self, repo_path: Path, instructions: str) -> PatchSet:
        return self._fallback.edit(repo_path, instructions)

    def _build_client(self) -> OpenAI | None:
        if OpenAI is None:
            return None
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.info("openai_missing_api_key, falling back to deterministic LLM")
            return None
        base_url = os.getenv("OPENAI_BASE_URL")
        kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url.rstrip("/")
        return OpenAI(**kwargs)

    def _request_plan(self, prompt: str, vibe: str | None) -> dict[str, Any]:
        assert self._client is not None
        user_prompt = textwrap.dedent(
            f"""
            You design small marketing websites in Next.js. Analyze the user's idea and propose 3-5 pages
            that cover the concept. Use concise titles and summaries. Prefer the requested vibe if provided.
            Respond with JSON.

            User prompt: {prompt.strip() or 'Generate a Next.js starter.'}
            Preferred vibe: {vibe or 'minimal'}
            """
        ).strip()
        response = self._create_llm_response(
            model=self.plan_model,
            messages=[
                {"role": "system", "content": "You are an expert product strategist for web apps."},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_schema", "json_schema": PLAN_SCHEMA},
        )
        text = _extract_output_text(response)
        return json.loads(text)

    def _request_scaffold(self, plan: Plan) -> dict[str, str]:
        assert self._client is not None
        page_specs = self._last_plan_details or [
            {"route": route, "title": _derive_title(route), "summary": plan.prompt}
            for route in plan.pages
        ]
        prompt_payload = textwrap.dedent(
            """
            Build a minimal Next.js (pages router) TypeScript project. Follow these requirements:
            - Provide React components under `pages/` matching each route.
            - Each page must include a <h1> with the title and a descriptive <p> paragraph.
            - Include a simple `pages/api/health.ts` endpoint returning `{ ok: true }`.
            - Include a `package.json` with Next.js 14.2.3 and React 18.
            - Keep styling inline with basic Tailwind-like classes; avoid external dependencies beyond Next/React.
            - Base the tone on the requested vibe.
            Respond with JSON following the supplied schema.
            """
        ).strip()
        plan_json = json.dumps(
            {
                "prompt": plan.prompt,
                "style": plan.style,
                "pages": page_specs,
            },
            indent=2,
        )
        response = self._create_llm_response(
            model=self.scaffold_model,
            messages=[
                {"role": "system", "content": "You are Codex, generating file trees for web apps."},
                {"role": "user", "content": f"{prompt_payload}\n\nPlan details:\n{plan_json}"},
            ],
            response_format={"type": "json_schema", "json_schema": SCAFFOLD_SCHEMA},
        )
        text = _extract_output_text(response)
        data = json.loads(text)
        files = {entry["path"].lstrip("./"): entry["contents"] for entry in data["files"]}
        _ensure_required_files(files, plan)
        return files

    def _create_llm_response(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        response_format: dict[str, Any] | None = None,
    ) -> Any:
        assert self._client is not None
        last_error: Exception | None = None

        responses_api = getattr(self._client, "responses", None)
        if responses_api and hasattr(responses_api, "create"):
            try:
                formatted_input = _format_for_responses_api(messages)
                return responses_api.create(
                    model=model,
                    input=formatted_input,
                    response_format=response_format,
                )
            except Exception as exc:  # pragma: no cover - rely on alternate API paths
                logger.debug("responses_api_failed", exc_info=True)
                last_error = exc

        chat_api = getattr(self._client, "chat", None)
        completions_api = getattr(chat_api, "completions", None) if chat_api else None
        if completions_api and hasattr(completions_api, "create"):
            kwargs: dict[str, Any] = {"model": model, "messages": messages}
            if response_format:
                kwargs["response_format"] = response_format
            try:
                return completions_api.create(**kwargs)
            except TypeError as exc:  # Older SDKs may not support response_format
                logger.debug("chat_completions_retry_without_response_format", exc_info=True)
                last_error = exc
                kwargs.pop("response_format", None)
                return completions_api.create(**kwargs)
            except Exception as exc:  # pragma: no cover - defensive
                last_error = exc
        if last_error:
            raise last_error
        raise AttributeError("OpenAI client does not support responses or chat.completions APIs")


def _format_for_responses_api(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if isinstance(content, list):
            entries: list[dict[str, Any]] = []
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type") or "text"
                    if item_type == "text" and "text" not in item and "value" in item:
                        entries.append({"type": "text", "text": item["value"]})
                    else:
                        entries.append(item)
                elif isinstance(item, str):
                    entries.append({"type": "text", "text": item})
                else:
                    entries.append({"type": "text", "text": str(item)})
        elif isinstance(content, str):
            entries = [{"type": "text", "text": content}]
        else:
            entries = [{"type": "text", "text": str(content)}]
        formatted.append({"role": role, "content": entries})
    return formatted


class _DeterministicLLM(CodeLLM):
    def plan(self, prompt: str, vibe: str | None = None) -> Plan:
        pages = ["/", "/about", "/contact"]
        print(">>>> fallback to deterministic LLM plan", prompt, vibe)
        return Plan(prompt=prompt, pages=pages, style=vibe or "minimal")

    def scaffold(self, plan: Plan) -> GeneratedTree:
        style = STYLE_CLASSES.get(plan.style, STYLE_CLASSES["minimal"])
        files = {
            "package.json": _PACKAGE_JSON,
            "pages/index.tsx": _page("Home", plan.prompt, style),
            "pages/about.tsx": _page("About", "We build with vibes.", style),
            "pages/contact.tsx": _page("Contact", "Reach out to the vibe team.", style),
            "pages/api/health.ts": "export default function handler(req, res) { res.status(200).json({ ok: true }); }",
        }
        return GeneratedTree(files=files)

    def edit(self, repo_path: Path, instructions: str) -> PatchSet:
        return PatchSet(patches={"README.md": f"Applied edit: {instructions}"})


def _ensure_required_files(files: dict[str, str], plan: Plan) -> None:
    if "package.json" not in files:
        files["package.json"] = _PACKAGE_JSON
    required_routes = set(plan.pages) | {"/"}
    for route in required_routes:
        path = _route_to_path(route)
        if path not in files:
            title = _derive_title(route)
            body = plan.prompt or "This page was generated by Vibecoder."
            style = STYLE_CLASSES.get(plan.style, STYLE_CLASSES["minimal"])
            files[path] = _page(title, body, style)
    if "pages/api/health.ts" not in files:
        files["pages/api/health.ts"] = "export default function handler(req, res) { res.status(200).json({ ok: true }); }"


def _route_to_path(route: str) -> str:
    clean = route.strip().lstrip("/")
    if not clean:
        clean = "index"
    return f"pages/{clean}.tsx"


def _derive_title(route: str) -> str:
    if route in {"", "/", "/index"}:
        return "Home"
    parts = [part for part in route.strip("/").split("/") if part]
    return " ".join(word.capitalize() for word in parts) or "Page"


def _extract_output_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text
    choices = getattr(response, "choices", None)
    choice_chunks = _extract_text_from_choices(choices)
    if choice_chunks:
        combined = "".join(choice_chunks)
        if combined.strip():
            return combined
    model_dump = getattr(response, "model_dump", None)
    if callable(model_dump):
        payload = model_dump()
    else:
        payload = getattr(response, "dict", lambda: {})()
    if not payload:
        payload = {}
    choice_chunks = _extract_text_from_choices(payload.get("choices"))
    if choice_chunks:
        combined = "".join(choice_chunks)
        if combined.strip():
            return combined
    output = payload.get("output") or []
    chunks: list[str] = []
    for item in output:
        for content in item.get("content", []):
            text_obj = content.get("text")
            if isinstance(text_obj, dict):
                value = text_obj.get("value")
                if value:
                    chunks.append(value)
            elif isinstance(text_obj, str):
                chunks.append(text_obj)
    combined = "".join(chunks)
    if combined.strip():
        return combined
    raise ValueError("Unable to extract text from OpenAI response")


def _extract_text_from_choices(choices: Any) -> list[str]:
    if not choices:
        return []
    extracted: list[str] = []
    for choice in choices:
        message = None
        if isinstance(choice, dict):
            message = choice.get("message")
        else:
            message = getattr(choice, "message", None)
        if not message:
            continue
        content = None
        if isinstance(message, dict):
            content = message.get("content")
        else:
            content = getattr(message, "content", None)
        if isinstance(content, str):
            extracted.append(content)
            continue
        if isinstance(content, list):
            for entry in content:
                if isinstance(entry, dict):
                    value = entry.get("text") or entry.get("value")
                    if isinstance(value, str):
                        extracted.append(value)
        # Some SDK versions expose assistant message at top level
        elif isinstance(message, str):
            extracted.append(message)
    return extracted


def _page(title: str, body: str, style: str) -> str:
    return f"""
import Head from "next/head";

export default function Page() {{
  return (
    <div className=\"min-h-screen flex flex-col items-center justify-center p-8 {style}\">
      <Head>
        <title>{title}</title>
      </Head>
      <main className=\"max-w-2xl space-y-6 text-center\">
        <h1 className=\"text-4xl font-bold\">{title}</h1>
        <p className=\"text-lg leading-relaxed\">{body}</p>
      </main>
    </div>
  );
}}
"""


_PACKAGE_JSON = """
{
  \"name\": \"vibecoder-generated\",
  \"version\": \"0.1.0\",
  \"private\": true,
  \"scripts\": {
    \"dev\": \"next dev\",
    \"build\": \"next build\",
    \"start\": \"next start\"
  },
  \"dependencies\": {
    \"next\": \"14.2.3\",
    \"react\": \"18.3.1\",
    \"react-dom\": \"18.3.1\"
  }
}
"""
