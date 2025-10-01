import Link from "next/link";

export function Header() {
  return (
    <header className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 px-6 py-4 shadow-lg">
      <Link href="/" className="text-xl font-semibold text-slate-100">
        Vibecoder
      </Link>
      <nav className="flex items-center gap-4 text-sm text-slate-300">
        <Link href="/" className="hover:text-slate-100">
          Home
        </Link>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-slate-100"
        >
          GitHub
        </a>
      </nav>
    </header>
  );
}
