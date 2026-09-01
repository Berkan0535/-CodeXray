"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Code2, Terminal, Layers, BookOpen, Settings, Github } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export function Navbar() {
  const pathname = usePathname();
  const { language, setLanguage, t } = useLanguage();

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/90 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800 border border-zinc-700 text-white group-hover:border-zinc-500 transition-colors">
            <Code2 className="h-4 w-4 text-blue-400" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold tracking-tight text-white">{t.nav.title}</span>
            <span className="rounded px-1.5 py-0.5 text-[10px] font-mono font-medium text-zinc-400 bg-zinc-800/80 border border-zinc-700/60">
              v1.0
            </span>
          </div>
        </Link>

        {/* Center Nav */}
        <nav className="hidden md:flex items-center gap-1 bg-surface p-1 rounded-lg border border-border">
          <Link
            href="/"
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              pathname === "/"
                ? "bg-zinc-800 text-white shadow-sm border border-zinc-700/80"
                : "text-zinc-400 hover:text-white hover:bg-surface-raised"
            }`}
          >
            <Terminal className="h-3.5 w-3.5" />
            {t.nav.analyze}
          </Link>
          <Link
            href="/repositories"
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              pathname.startsWith("/repositories")
                ? "bg-zinc-800 text-white shadow-sm border border-zinc-700/80"
                : "text-zinc-400 hover:text-white hover:bg-surface-raised"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            {t.nav.repositories}
          </Link>
          <Link
            href="/settings"
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              pathname === "/settings"
                ? "bg-zinc-800 text-white shadow-sm border border-zinc-700/80"
                : "text-zinc-400 hover:text-white hover:bg-surface-raised"
            }`}
          >
            <Settings className="h-3.5 w-3.5" />
            {t.nav.settings}
          </Link>
        </nav>

        {/* Right Actions & Language Switcher */}
        <div className="flex items-center gap-2">
          {/* Minimalist Language Switcher */}
          <div className="flex items-center bg-surface p-0.5 rounded-lg border border-border">
            <button
              onClick={() => setLanguage("tr")}
              className={`px-2 py-0.5 rounded text-[11px] font-medium font-mono transition-all ${
                language === "tr"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              TR
            </button>
            <button
              onClick={() => setLanguage("en")}
              className={`px-2 py-0.5 rounded text-[11px] font-medium font-mono transition-all ${
                language === "en"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              EN
            </button>
          </div>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="hidden sm:flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition-colors px-2.5 py-1 rounded-md hover:bg-surface border border-transparent hover:border-border"
          >
            <BookOpen className="h-3.5 w-3.5 text-zinc-400" />
            <span>{t.nav.apiDocs}</span>
          </a>

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-md bg-surface px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white hover:bg-surface-raised border border-border transition-colors"
          >
            <Github className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">GitHub</span>
          </a>
        </div>
      </div>
    </header>
  );
}
