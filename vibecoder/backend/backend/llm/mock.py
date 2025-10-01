from __future__ import annotations

from pathlib import Path

from .interface import CodeLLM, GeneratedTree, PatchSet, Plan


STYLE_CLASSES = {
    "minimal": "bg-slate-900 text-slate-100",
    "cozy": "bg-amber-50 text-amber-950",
    "retro": "bg-emerald-950 text-emerald-100",
}


class MockCodeLLM(CodeLLM):
    def plan(self, prompt: str, vibe: str | None = None) -> Plan:
        pages = ["/", "/about", "/contact"]
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
