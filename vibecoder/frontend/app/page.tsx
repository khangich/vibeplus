import Link from "next/link";
import { PromptForm } from "@/components/PromptForm";
import { RevisionList } from "@/components/RevisionList";
import { fetchJSON } from "@/lib/api";

type Project = {
  id: string;
  title: string;
  created_at: string;
};

const PUBLIC_API_BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";


async function getProjects(): Promise<Project[]> {
  try {
    const data = await fetchJSON<Project[]>(`/projects`);
    return data;
  } catch (err) {
    console.error("Failed to load projects", err);
    return [];
  }
}

export default async function HomePage() {
  const projects = await getProjects();

  return (
    <div className="space-y-12">
      <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl">
        <h2 className="text-2xl font-semibold">Start a new vibe</h2>
        <p className="mt-2 text-sm text-slate-300">
          Describe your idea and pick a style. Vibecoder will plan, scaffold, build,
          and host a live preview for you.
        </p>
        <div className="mt-6">
          <PromptForm />
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Recent projects</h2>
          <Link href="/" className="text-sm text-slate-300 hover:text-slate-100">
            Refresh
          </Link>
        </div>
        {projects.length === 0 ? (
          <p className="text-sm text-slate-400">No projects yet. Generate your first vibe!</p>
        ) : (
          <div className="space-y-4">
            {projects.map((project) => (
              <div
                key={project.id}
                className="rounded-lg border border-slate-800 bg-slate-900/40 p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-100">{project.title}</h3>
                    <p className="text-xs text-slate-400">
                      Created {new Date(project.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Link
                    href={`/projects/${project.id}`}
                    className="rounded-md bg-sky-500 px-3 py-2 text-sm font-medium text-white shadow hover:bg-sky-400"
                  >
                    View
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <RevisionList compact />
      </section>
    </div>
  );
}
