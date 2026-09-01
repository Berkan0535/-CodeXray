"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  ShieldAlert,
  Zap,
  Network,
  CheckCircle2,
  AlertTriangle,
  Code,
  FileText,
  Terminal,
  ArrowUpRight,
} from "lucide-react";
import { api } from "@/lib/api";
import { Analysis, Issue } from "@/types";
import { ScoreGauge } from "@/components/ScoreGauge";
import { IssueDetailModal } from "@/components/IssueDetailModal";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import Link from "next/link";

export default function AnalysisOverviewPage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { t, language } = useLanguage();

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [topIssues, setTopIssues] = useState<Issue[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [aData, iData] = await Promise.all([
          api.getAnalysis(analysisId),
          api.listIssues(analysisId, { lang: language }),
        ]);
        setAnalysis(aData);
        setTopIssues(iData.slice(0, 5));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [analysisId, language]);

  if (loading || !analysis) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="h-6 w-6 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  const langList = Object.entries(analysis.languages_breakdown || {}).sort(
    (a, b) => b[1].code_lines - a[1].code_lines
  );

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner: Repo Title & Summary Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-xl bg-surface border border-border">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">{t.overview.badge}</span>
            <span className="text-zinc-600">•</span>
            <span className="text-[11px] font-mono text-zinc-500">commit: {analysis.commit_hash?.slice(0, 7) || "HEAD"}</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1">
            {analysis.repository?.name || "Repository Overview"}
          </h1>
          <p className="text-xs text-zinc-400 mt-1 font-mono">
            {t.overview.scannedSummary
              .replace("{{files}}", String(analysis.total_files))
              .replace("{{loc}}", String(analysis.total_code_lines))
              .replace("{{seconds}}", String(analysis.duration_seconds))}
          </p>
        </div>

        {/* Framework badges */}
        <div className="flex flex-wrap items-center gap-1.5">
          {analysis.project_frameworks?.map((fw) => (
            <span key={fw} className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
              {fw}
            </span>
          ))}
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-zinc-800 text-blue-400 border border-zinc-700">
            {analysis.primary_language}
          </span>
        </div>
      </div>

      {/* Scorecards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <ScoreGauge score={analysis.overall_score} label={t.overview.overallScore} size="lg" subtitle={t.overview.overallSubtitle} />
        <ScoreGauge score={analysis.architecture_score} label={t.overview.architecture} size="md" />
        <ScoreGauge score={analysis.security_score} label={t.overview.security} size="md" />
        <ScoreGauge score={analysis.performance_score} label={t.overview.performance} size="md" />
        <ScoreGauge score={analysis.quality_score} label={t.overview.quality} size="md" />
        <ScoreGauge score={analysis.maintainability_score} label={t.overview.maintainability} size="md" />
      </div>

      {/* Severity Alert Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-surface border border-border flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono font-medium text-red-400 uppercase tracking-wider">{t.overview.criticalIssues}</span>
            <p className="text-xl font-mono font-bold text-white mt-0.5">{analysis.critical_issues_count}</p>
          </div>
          <AlertTriangle className="h-5 w-5 text-red-400 opacity-80" />
        </div>

        <div className="p-3.5 rounded-xl bg-surface border border-border flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono font-medium text-amber-400 uppercase tracking-wider">{t.overview.highPriority}</span>
            <p className="text-xl font-mono font-bold text-white mt-0.5">{analysis.high_issues_count}</p>
          </div>
          <ShieldAlert className="h-5 w-5 text-amber-400 opacity-80" />
        </div>

        <div className="p-3.5 rounded-xl bg-surface border border-border flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono font-medium text-zinc-300 uppercase tracking-wider">{t.overview.mediumIssues}</span>
            <p className="text-xl font-mono font-bold text-white mt-0.5">{analysis.medium_issues_count}</p>
          </div>
          <Zap className="h-5 w-5 text-zinc-400 opacity-80" />
        </div>

        <div className="p-3.5 rounded-xl bg-surface border border-border flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono font-medium text-zinc-400 uppercase tracking-wider">{t.overview.lowInfo}</span>
            <p className="text-xl font-mono font-bold text-white mt-0.5">{analysis.low_issues_count + analysis.info_issues_count}</p>
          </div>
          <CheckCircle2 className="h-5 w-5 text-zinc-500 opacity-80" />
        </div>
      </div>

      {/* AI Summary Box */}
      {analysis.ai_summary && (
        <div className="p-5 rounded-xl bg-surface border border-border space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold text-zinc-300">
            <Terminal className="h-4 w-4 text-blue-400" />
            {t.overview.aiBriefing}
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed font-sans">{analysis.ai_summary}</p>
        </div>
      )}

      {/* Languages & Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Language Breakdown */}
        <div className="p-5 rounded-xl bg-surface border border-border space-y-4">
          <h3 className="text-xs font-semibold text-white flex items-center gap-2">
            <Code className="h-4 w-4 text-zinc-400" />
            {t.overview.languageDistribution}
          </h3>

          {/* Minimalist stacked progress bar */}
          <div className="h-1.5 w-full rounded-full bg-zinc-800 flex overflow-hidden">
            {langList.slice(0, 5).map(([lang, stats], idx) => {
              const colors = ["bg-blue-500", "bg-emerald-500", "bg-amber-500", "bg-cyan-500", "bg-zinc-400"];
              return (
                <div
                  key={lang}
                  className={colors[idx % colors.length]}
                  style={{ width: `${stats.percentage}%` }}
                  title={`${lang}: ${stats.percentage}%`}
                />
              );
            })}
          </div>

          <div className="space-y-1.5 pt-1">
            {langList.slice(0, 6).map(([lang, stats]) => (
              <div key={lang} className="flex items-center justify-between text-xs">
                <span className="text-zinc-300 font-medium">{lang}</span>
                <span className="text-zinc-400 font-mono text-[11px]">
                  {stats.percentage}% ({stats.code_lines} LOC)
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Discovered Issues */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-surface border border-border space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-white flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-red-400" />
              {t.overview.highPriorityActions}
            </h3>
            <Link
              href={`/analyses/${analysisId}/security`}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
            >
              {t.overview.viewAll} ({topIssues.length})
              <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="space-y-2">
            {topIssues.map((issue) => (
              <button
                key={issue.id}
                onClick={() => setSelectedIssue(issue)}
                className="w-full p-3 rounded-lg bg-surface-raised hover:bg-[#202024] border border-border text-left transition-colors flex items-start justify-between gap-3 group"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold border ${
                        issue.severity === "CRITICAL"
                          ? "bg-red-500/10 text-red-400 border-red-500/20"
                          : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      }`}
                    >
                      {issue.severity}
                    </span>
                    <span className="text-xs font-medium text-white group-hover:text-blue-400 transition-colors">
                      {issue.title}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 line-clamp-1">{issue.description}</p>
                </div>
                <span className="text-[11px] text-zinc-500 font-mono shrink-0">{issue.file_path}:{issue.line_number}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Issue Detail Modal */}
      <IssueDetailModal issue={selectedIssue} onClose={() => setSelectedIssue(null)} />
    </div>
  );
}
