"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CheckCircle2, ArrowUpRight } from "lucide-react";
import { api } from "@/lib/api";
import { Analysis, Issue } from "@/types";
import { ScoreGauge } from "@/components/ScoreGauge";
import { IssueDetailModal } from "@/components/IssueDetailModal";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function QualityPage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { t, language } = useLanguage();

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getAnalysis(analysisId),
      api.listIssues(analysisId, { category: "QUALITY", lang: language }),
    ])
      .then(([aData, iData]) => {
        setAnalysis(aData);
        setIssues(iData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [analysisId, language]);

  if (loading || !analysis) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="h-6 w-6 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-surface border border-border">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400">{t.quality.badge}</span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            {t.quality.title}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            {t.quality.desc}
          </p>
        </div>
      </div>

      {/* Metrics Gauges */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <ScoreGauge score={analysis.quality_score} label={t.quality.codeQuality} size="md" subtitle={t.quality.compositeRating} />
        <ScoreGauge score={analysis.maintainability_score} label={t.quality.maintainabilityIndex} size="md" subtitle="MI Formula" />
        <div className="p-4 rounded-xl bg-surface border border-border flex flex-col justify-center items-center text-center">
          <span className="text-xs font-medium text-zinc-400">{t.quality.totalCodeLines}</span>
          <p className="text-2xl font-mono font-bold text-white mt-1">{analysis.total_code_lines}</p>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5">({analysis.total_files} files)</span>
        </div>
        <div className="p-4 rounded-xl bg-surface border border-border flex flex-col justify-center items-center text-center">
          <span className="text-xs font-medium text-zinc-400">{t.quality.refactoringTargets}</span>
          <p className="text-2xl font-mono font-bold text-blue-400 mt-1">{issues.length}</p>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5">{t.quality.hotspots}</span>
        </div>
      </div>

      {/* Quality Issues List */}
      <div className="space-y-3">
        <h3 className="text-xs font-mono font-semibold text-zinc-300 uppercase tracking-wider">{t.quality.findingsTitle}</h3>
        {issues.length === 0 ? (
          <div className="p-10 text-center rounded-xl bg-surface border border-border">
            <CheckCircle2 className="h-6 w-6 text-emerald-400 mx-auto mb-2 opacity-80" />
            <h3 className="text-xs font-semibold text-white">{t.quality.excellentTitle}</h3>
            <p className="text-xs text-zinc-400 mt-1 font-mono">{t.quality.excellentDesc}</p>
          </div>
        ) : (
          issues.map((issue) => (
            <button
              key={issue.id}
              onClick={() => setSelectedIssue(issue)}
              className="w-full p-3.5 rounded-xl bg-surface hover:bg-surface-raised border border-border text-left transition-colors flex items-start justify-between gap-4 group"
            >
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {issue.severity}
                  </span>
                  <span className="text-xs font-semibold text-white group-hover:text-blue-400 transition-colors">
                    {issue.title}
                  </span>
                </div>
                <p className="text-xs text-zinc-300 font-sans">{issue.description}</p>
              </div>

              <div className="text-right shrink-0">
                <span className="text-xs text-zinc-400 font-mono block">{issue.file_path}:{issue.line_number}</span>
                <span className="text-[11px] text-blue-400 font-medium flex items-center justify-end gap-1 mt-2 group-hover:underline">
                  Inspect <ArrowUpRight className="h-3 w-3" />
                </span>
              </div>
            </button>
          ))
        )}
      </div>

      {/* Modal */}
      <IssueDetailModal issue={selectedIssue} onClose={() => setSelectedIssue(null)} />
    </div>
  );
}
