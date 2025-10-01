interface DiffViewerProps {
  diff: string;
}

export function DiffViewer({ diff }: DiffViewerProps) {
  return (
    <pre className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/80 p-4 text-xs text-slate-200">
      {diff || "No diff available."}
    </pre>
  );
}
