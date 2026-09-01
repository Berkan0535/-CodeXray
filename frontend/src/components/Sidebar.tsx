"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Network,
  ShieldAlert,
  Zap,
  CheckCircle2,
  Package,
  Sparkles,
  MessageSquareCode,
  FileText,
  RefreshCw,
  ExternalLink,
  GitBranch,
} from "lucide-react";
import { Analysis } from "@/types";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface SidebarProps {
  analysisId: string;
  analysis?: Analysis;
  onReanalyze?: () => void;
  isReanalyzing?: boolean;
}

export function Sidebar({ analysisId, analysis, onReanalyze, isReanalyzing }: SidebarProps) {
  const pathname = usePathname();
  const { t } = useLanguage();

  const links = [
    { href: `/analyses/${analysisId}`, label: t.sidebar.overview, icon: LayoutDashboard },
    { href: `/analyses/${analysisId}/architecture`, label: t.sidebar.architecture, icon: Network },
    {
      href: `/analyses/${analysisId}/security`,
      label: t.sidebar.security,
      icon: ShieldAlert,
      badge: analysis?.critical_issues_count ? `${analysis.critical_issues_count}` : undefined,
      badgeColor: "bg-red-500/10 text-red-400 border-red-500/20",
    },
    { href: `/analyses/${analysisId}/performance`, label: t.sidebar.performance, icon: Zap },
    { href: `/analyses/${analysisId}/quality`, label: t.sidebar.quality, icon: CheckCircle2 },
    { href: `/analyses/${analysisId}/dependencies`, label: t.sidebar.dependencies, icon: Package },
    { href: `/analyses/${analysisId}/ai-review`, label: t.sidebar.aiReview, icon: Sparkles },
    { href: `/analyses/${analysisId}/chat`, label: t.sidebar.chat, icon: MessageSquareCode, isNew: true },
    { href: `/analyses/${analysisId}/report`, label: t.sidebar.report, icon: FileText },
  ];

  return (
    <aside className="w-60 shrink-0 border-r border-border bg-background min-h-[calc(100vh-3.5rem)] p-3 flex flex-col justify-between">
      <div>
        {/* Repo Header */}
        <div className="mb-4 p-3 rounded-lg bg-surface border border-border">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              {t.sidebar.targetProject}
            </span>
            {analysis?.repository?.url && (
              <a
                href={analysis.repository.url}
                target="_blank"
                rel="noreferrer"
                className="text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
          <p className="text-xs font-semibold text-white truncate">{analysis?.repository?.name || "Codebase"}</p>
          <div className="flex items-center gap-1 mt-1 text-[11px] text-zinc-500 font-mono">
            <GitBranch className="h-3 w-3" />
            <span className="truncate">{analysis?.branch || "main"}</span>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="space-y-0.5">
          {links.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? "bg-zinc-800 text-white font-semibold border border-zinc-700 shadow-sm"
                    : "text-zinc-400 hover:text-white hover:bg-surface border border-transparent"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${isActive ? "text-blue-400" : "text-zinc-400"}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold border ${item.badgeColor}`}>
                    {item.badge}
                  </span>
                )}
                {item.isNew && (
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-zinc-800 text-blue-400 border border-zinc-700">
                    RAG
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Re-run button */}
      {onReanalyze && (
        <div className="pt-3 border-t border-border mt-3">
          <button
            onClick={onReanalyze}
            disabled={isReanalyzing}
            className="w-full flex items-center justify-center gap-2 py-1.5 px-3 rounded-md bg-surface hover:bg-surface-raised border border-border text-xs font-medium text-zinc-300 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3 w-3 ${isReanalyzing ? "animate-spin text-blue-400" : "text-zinc-400"}`} />
            <span>{isReanalyzing ? t.sidebar.analyzing : t.sidebar.reanalyze}</span>
          </button>
        </div>
      )}
    </aside>
  );
}
