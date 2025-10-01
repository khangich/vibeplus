"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { postJSON } from "@/lib/api";

const VIBES = [
  { id: "minimal", label: "Minimal" },
  { id: "cozy", label: "Cozy" },
  { id: "retro", label: "Retro" },
];

export function PromptForm() {
  const [prompt, setPrompt] = useState("");
  const [vibe, setVibe] = useState("minimal");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    try {
      const title = prompt.split(" ").slice(0, 5).join(" ") || "Untitled Project";
      const project = await postJSON<{ project_id: string }>("/projects", {
        title,
      });
      const revision = await postJSON<{ revision_id: string }>(
        `/projects/${project.project_id}/generate`,
        {
          prompt,
          mode: "new",
          vibe,
        },
      );
      router.push(`/projects/${project.project_id}/rev/${revision.revision_id}`);
    } catch (error) {
      console.error("Generation failed", error);
      alert("Failed to generate project. Check backend logs.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <textarea
        className="w-full rounded-lg border border-slate-800 bg-slate-950/80 p-4 text-sm text-slate-100 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
        rows={4}
        placeholder="Build a landing page for..."
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
      />
      <div className="flex flex-wrap items-center gap-3 text-sm text-slate-200">
        {VIBES.map((option) => (
          <label
            key={option.id}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 transition ${
              vibe === option.id
                ? "border-sky-400 bg-sky-500/20 text-sky-200"
                : "border-slate-700 bg-slate-900/80"
            }`}
          >
            <input
              type="radio"
              name="vibe"
              value={option.id}
              checked={vibe === option.id}
              onChange={() => setVibe(option.id)}
              className="accent-sky-500"
            />
            {option.label}
          </label>
        ))}
      </div>
      <button
        type="submit"
        disabled={loading}
        className="rounded-md bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {loading ? "Generating..." : "Generate"}
      </button>
    </form>
  );
}
