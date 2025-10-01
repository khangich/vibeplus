import Link from "next/link";
import { notFound } from "next/navigation";
import { DiffViewer } from "@/components/DiffViewer";
import { fetchJSON } from "@/lib/api";

type RevisionDetail = {
  id: string;
  project_id: string;
  message: string;
  status: string;
  preview_url?: string | null;
  logs_url?: string | null;
  created_at: string;
  diff?: string;
};

async function getRevision(id: string): Promise<RevisionDetail | null> {
  try {
    return await fetchJSON<RevisionDetail>(`/revisions/${id}`);
  } catch (error) {
    console.error("Failed to fetch revision", error);
    return null;
  }
}

export default async function RevisionPage({
  params,
}: {
  params: { id: string; revId: string };
}) {
  const revision = await getRevision(params.revId);

  if (!revision) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Revision {revision.id}</h1>
          <p className="text-xs text-slate-400">Status: {revision.status}</p>
        </div>
        <Link
          href={`/projects/${params.id}`}
          className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
        >
          Back to project
        </Link>
      </div>

      {revision.preview_url && (
        <a
          href={revision.preview_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-md bg-emerald-500 px-3 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-400"
        >
          Open Preview
        </a>
      )}

      {revision.logs_url && (
        <a
          href={revision.logs_url}
          className="block text-sm text-slate-300 hover:text-slate-100"
        >
          Download build logs
        </a>
      )}

      <DiffViewer diff={revision.diff ?? "No diff available."} />

      <div className="flex gap-4">
        <Link
          href={`/revisions/${revision.id}/export/zip`}
          className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
        >
          Download Zip
        </Link>
        <Link
          href={`/revisions/${revision.id}/export/github`}
          className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
        >
          View GitHub Export
        </Link>
      </div>
    </div>
  );
}
