import "../styles/globals.css";
import { ReactNode } from "react";
import { Header } from "@/components/Header";

export const metadata = {
  title: "Vibecoder",
  description: "Generate vibes for your Next.js apps",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full bg-slate-950 text-slate-100">
      <body className="min-h-screen bg-slate-950">
        <div className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-8">
          <Header />
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
