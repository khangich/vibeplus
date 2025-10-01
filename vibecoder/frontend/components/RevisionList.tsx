"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchJSON, postJSON } from "@/lib/api";

type Revision = {
  id: string;
  project_id: string;
  message: string;
  status: string;
  created_at: string;
  preview_url?: string | null;
};

interface Props {
  projectId?: string;
  compact?: boolean;
}

export function RevisionList({ projectId, compact }: Props) {
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const path = projectId ? `/projects/${projectId}/revisions` : "/revisions";
        const data = await fetchJSON<Revision[]>(path);
        if (active) {
          setRevisions(data);
        }
      } catch (error) {
        console.error("Failed to load revisions", error);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 4000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [projectId]);

  async function regenerate(project: Revision) {
    try {
      const { revision_id } = await postJSON<{ revision_id: string }>(
        `/projects/${project.project_id}/generate`,
        {
          prompt: project.message,
          mode: "edit",
          base_revision: project.id,
        },
      );
      window.location.href = `/projects/${project.project_id}/rev/${revision_id}`;
    } catch (error) {
      console.error("Failed to regenerate", error);
      alert("Unable to start regeneration");
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-400">Loading revisions...</p>;
  }

  if (revisions.length === 0) {
    return <p className="text-sm text-slate-400">No revisions yet.</p>;
  }

  return (
    <div className="space-y-3">
      {revisions.map((revision) => (
        <div
          key={revision.id}
          className={`flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/50 p-4 ${
            compact ? "text-xs" : "text-sm"
          }`}
        >
          <div>
            <p className="font-medium text-slate-100">
              Revision {revision.id.slice(0, 8)}
            </p>
            <p className="text-slate-400">
              {revision.status} • {new Date(revision.created_at).toLocaleString()}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {revision.preview_url && (
              <a
                href={revision.preview_url}
                className="rounded-md border border-emerald-500/70 px-3 py-1 text-emerald-200 hover:bg-emerald-500/10"
              >
                Preview
              </a>
            )}
            <Link
              href={`/projects/${revision.project_id}/rev/${revision.id}`}
              className="rounded-md border border-slate-700 px-3 py-1 text-slate-200 hover:bg-slate-800"
            >
              Details
            </Link>
            <button
              onClick={() => regenerate(revision)}
              className="rounded-md border border-sky-500/70 px-3 py-1 text-sky-200 hover:bg-sky-500/10"
            >
              Regenerate
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
