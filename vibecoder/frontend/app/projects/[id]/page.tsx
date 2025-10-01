import Link from "next/link";
import { notFound } from "next/navigation";
import { RevisionList } from "@/components/RevisionList";
import { fetchJSON } from "@/lib/api";

interface ProjectDetail {
  id: string;
  title: string;
  created_at: string;
}

const PUBLIC_API_BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";


async function getProject(projectId: string): Promise<ProjectDetail | null> {
  try {
    return await fetchJSON<ProjectDetail>(`/projects/${projectId}`);
  } catch (error) {
    console.error("Failed to load project", error);
    return null;
  }
}

export default async function ProjectPage({ params }: { params: { id: string } }) {
  const project = await getProject(params.id);

  if (!project) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{project.title}</h1>
          <p className="text-xs text-slate-400">
            Created {new Date(project.created_at).toLocaleString()}
          </p>
        </div>
        <Link
          href="/"
          className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
        >
          Back
        </Link>
      </div>
      <RevisionList projectId={project.id} />
    </div>
  );
}
