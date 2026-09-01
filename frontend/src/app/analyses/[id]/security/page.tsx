"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ShieldAlert, Search, ArrowUpRight } from "lucide-react";
import { api } from "@/lib/api";
import { Issue } from "@/types";
import { IssueDetailModal } from "@/components/IssueDetailModal";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function SecurityPage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { t, language } = useLanguage();

  const [issues, setIssues] = useState<Issue[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadIssues() {
      try {
        const data = await api.listIssues(analysisId, {
          category: "SECURITY",
          severity: severityFilter === "ALL" ? undefined : severityFilter,
          search: searchQuery || undefined,
          lang: language,
        });
        setIssues(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadIssues();
  }, [analysisId, severityFilter, searchQuery, language]);

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-surface border border-border">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-red-400">{t.security.badge}</span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-400" />
            {t.security.title}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            {t.security.desc}
          </p>
        </div>

        <div className="flex items-center gap-1.5">
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium transition-colors border ${
                severityFilter === sev
                  ? "bg-zinc-800 text-white border-zinc-700 shadow-sm"
                  : "bg-surface text-zinc-400 hover:text-white border-border hover:bg-surface-raised"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Search Bar */}
      <div className="p-2.5 rounded-xl bg-surface border border-border flex items-center gap-2 focus-within:border-zinc-500">
        <Search className="h-4 w-4 text-zinc-500 shrink-0" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t.security.searchPlaceholder}
          className="w-full bg-transparent text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
        />
      </div>

      {/* Issues Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
        </div>
      ) : issues.length === 0 ? (
        <div className="p-10 text-center rounded-xl bg-surface border border-border">
          <ShieldAlert className="h-6 w-6 text-emerald-400 mx-auto mb-2 opacity-80" />
          <h3 className="text-xs font-semibold text-white">{t.security.noIssuesTitle}</h3>
          <p className="text-xs text-zinc-400 mt-1 font-mono">{t.security.noIssuesDesc}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {issues.map((issue) => (
            <button
              key={issue.id}
              onClick={() => setSelectedIssue(issue)}
              className="w-full p-3.5 rounded-xl bg-surface hover:bg-surface-raised border border-border text-left transition-colors flex items-start justify-between gap-4 group"
            >
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold border ${
                      issue.severity === "CRITICAL"
                        ? "bg-red-500/10 text-red-400 border-red-500/20"
                        : issue.severity === "HIGH"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                    }`}
                  >
                    {issue.severity}
                  </span>
                  <span className="text-xs font-semibold text-white group-hover:text-blue-400 transition-colors">
                    {issue.title}
                  </span>
                  <span className="text-[10px] text-zinc-500 font-mono">tool: {issue.tool}</span>
                </div>
                <p className="text-xs text-zinc-300 line-clamp-2 font-sans">{issue.description}</p>
                {issue.code_snippet && (
                  <pre className="p-2 rounded-md bg-[#09090b] border border-border text-[11px] text-red-300 font-mono overflow-x-auto max-w-2xl">
                    <code>{issue.code_snippet}</code>
                  </pre>
                )}
              </div>

              <div className="text-right shrink-0">
                <span className="text-xs text-zinc-400 font-mono block">{issue.file_path}:{issue.line_number}</span>
                <span className="text-[11px] text-blue-400 font-medium flex items-center justify-end gap-1 mt-2 group-hover:underline">
                  {t.security.inspectFix} <ArrowUpRight className="h-3 w-3" />
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      <IssueDetailModal issue={selectedIssue} onClose={() => setSelectedIssue(null)} />
    </div>
  );
}
