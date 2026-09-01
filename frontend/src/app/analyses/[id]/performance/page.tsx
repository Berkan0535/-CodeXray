"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Zap, ArrowUpRight } from "lucide-react";
import { api } from "@/lib/api";
import { Issue } from "@/types";
import { IssueDetailModal } from "@/components/IssueDetailModal";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function PerformancePage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { t, language } = useLanguage();

  const [issues, setIssues] = useState<Issue[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.listIssues(analysisId, { category: "PERFORMANCE", lang: language })
      .then(setIssues)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [analysisId, language]);

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-surface border border-border">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400">{t.performance.badge}</span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <Zap className="h-5 w-5 text-amber-400" />
            {t.performance.title}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            {t.performance.desc}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-surface-raised border border-border text-center">
          <span className="text-[10px] text-zinc-400 uppercase font-mono font-medium">{t.performance.bottlenecksFound}</span>
          <p className="text-xl font-mono font-bold text-amber-400 mt-0.5">{issues.length}</p>
        </div>
      </div>

      {/* Issues list */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 rounded-full border-2 border-amber-500 border-t-transparent animate-spin" />
        </div>
      ) : issues.length === 0 ? (
        <div className="p-10 text-center rounded-xl bg-surface border border-border">
          <Zap className="h-6 w-6 text-emerald-400 mx-auto mb-2 opacity-80" />
          <h3 className="text-xs font-semibold text-white">{t.performance.noIssuesTitle}</h3>
          <p className="text-xs text-zinc-400 mt-1 font-mono">{t.performance.noIssuesDesc}</p>
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
                  <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    {issue.severity}
                  </span>
                  <span className="text-xs font-semibold text-white group-hover:text-amber-400 transition-colors">
                    {issue.title}
                  </span>
                </div>
                <p className="text-xs text-zinc-300 line-clamp-2 font-sans">{issue.description}</p>
                {issue.code_snippet && (
                  <pre className="p-2 rounded-md bg-[#09090b] border border-border text-[11px] text-amber-300 font-mono overflow-x-auto max-w-2xl">
                    <code>{issue.code_snippet}</code>
                  </pre>
                )}
              </div>

              <div className="text-right shrink-0">
                <span className="text-xs text-zinc-400 font-mono block">{issue.file_path}:{issue.line_number}</span>
                <span className="text-[11px] text-blue-400 font-medium flex items-center justify-end gap-1 mt-2 group-hover:underline">
                  {t.performance.inspectSolution} <ArrowUpRight className="h-3 w-3" />
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Modal */}
      <IssueDetailModal issue={selectedIssue} onClose={() => setSelectedIssue(null)} />
    </div>
  );
}
