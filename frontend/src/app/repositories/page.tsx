"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Layers,
  GitBranch,
  ExternalLink,
  Calendar,
  Search,
  Plus,
  ArrowRight,
  Network,
  ShieldAlert,
  Zap,
  CheckCircle2,
  MessageSquareCode,
  FileText,
  Package,
  Sparkles,
  RefreshCw,
  History,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Repository, Analysis } from "@/types";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function RepositoriesListPage() {
  const router = useRouter();
  const { t, language } = useLanguage();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [reanalyzingRepoId, setReanalyzingRepoId] = useState<string | null>(null);

  // History modal state
  const [historyModalRepo, setHistoryModalRepo] = useState<Repository | null>(null);
  const [historyAnalyses, setHistoryAnalyses] = useState<Analysis[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    try {
      setLoading(true);
      const data = await api.listRepositories();
      setRepositories(data);
    } catch (err) {
      console.error("Failed to load repositories:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReanalyze = async (e: React.MouseEvent, repo: Repository) => {
    e.stopPropagation();
    e.preventDefault();
    try {
      setReanalyzingRepoId(repo.id);
      const analysis = await api.analyzeRepository(repo.url, repo.default_branch);
      router.push(`/analyses/${analysis.id}`);
    } catch (err) {
      console.error("Failed to reanalyze:", err);
      setReanalyzingRepoId(null);
    }
  };

  const handleOpenHistory = async (e: React.MouseEvent, repo: Repository) => {
    e.stopPropagation();
    e.preventDefault();
    setHistoryModalRepo(repo);
    setHistoryLoading(true);
    try {
      const data = await api.listRepositoryAnalyses(repo.id);
      setHistoryAnalyses(data);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const filtered = repositories.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.owner.toLowerCase().includes(search.toLowerCase()) ||
      r.url.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-surface border border-border shadow-sm">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-blue-400 font-semibold">
            {t.repositories.badge}
          </span>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1 flex items-center gap-2.5">
            <Layers className="h-6 w-6 text-blue-400" />
            {t.repositories.title}
          </h1>
          <p className="text-xs text-zinc-400 mt-1 max-w-xl">
            {t.repositories.desc}
          </p>
        </div>

        <Link
          href="/"
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition-all self-start sm:self-auto hover:shadow-blue-500/20"
        >
          <Plus className="h-4 w-4" />
          <span>{t.repositories.analyzeNew}</span>
        </Link>
      </div>

      {/* Search Bar */}
      <div className="p-3 rounded-xl bg-surface border border-border flex items-center gap-2.5 focus-within:border-zinc-500 shadow-sm transition-colors">
        <Search className="h-4 w-4 text-zinc-500 shrink-0 ml-1" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t.repositories.searchPlaceholder}
          className="w-full bg-transparent text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
        />
        {search && (
          <button
            onClick={() => setSearch("")}
            className="text-[11px] text-zinc-500 hover:text-zinc-300 font-mono px-2"
          >
            {language === "tr" ? "Temizle" : "Clear"}
          </button>
        )}
      </div>

      {/* Repositories Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-3">
          <div className="h-8 w-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
          <span className="text-xs text-zinc-400 font-mono">
            {language === "tr" ? "Depolar yükleniyor..." : "Loading repositories..."}
          </span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-surface border border-border space-y-3">
          <Layers className="h-8 w-8 text-zinc-600 mx-auto" />
          <h3 className="text-sm font-semibold text-white">{t.repositories.emptyTitle}</h3>
          <p className="text-xs text-zinc-400 font-mono max-w-sm mx-auto">{t.repositories.emptyDesc}</p>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors mt-2"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>{t.repositories.analyzeNew}</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((repo) => {
            const targetAnalysisId = repo.latest_analysis_id || repo.id;
            const isCompleted = repo.latest_status === "completed" || ((repo.overall_score || 0) > 0);
            const isFailed = repo.latest_status === "failed";
            const isRunning = repo.latest_status === "running" || repo.latest_status === "queued";

            return (
              <div
                key={repo.id}
                className="p-5 rounded-2xl bg-surface hover:bg-surface-raised border border-border hover:border-zinc-700 transition-all flex flex-col justify-between space-y-4 group shadow-sm hover:shadow-md"
              >
                {/* Card Header */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400 bg-surface-raised px-2 py-0.5 rounded border border-border/60">
                      {repo.owner}
                    </span>

                    <div className="flex items-center gap-2">
                      {/* Status Badge */}
                      {isCompleted ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          {t.repositories.statusCompleted}
                        </span>
                      ) : isFailed ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-red-500/10 text-red-400 border border-red-500/20 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {t.repositories.statusFailed}
                        </span>
                      ) : isRunning ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1">
                          <div className="h-2 w-2 rounded-full border border-blue-400 border-t-transparent animate-spin" />
                          {t.repositories.statusRunning}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-zinc-800 text-zinc-400 border border-zinc-700">
                          {repo.default_branch}
                        </span>
                      )}

                      <a
                        href={repo.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-zinc-500 hover:text-zinc-300 transition-colors p-1"
                        title="GitHub"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  </div>

                  <div>
                    <Link
                      href={`/analyses/${targetAnalysisId}`}
                      className="text-base font-bold text-white group-hover:text-blue-400 transition-colors font-mono line-clamp-1 hover:underline"
                    >
                      {repo.name}
                    </Link>
                    <p className="text-[11px] font-mono text-zinc-500 truncate mt-0.5">{repo.url}</p>
                  </div>

                  {/* Score & Key Metrics Banner */}
                  {isCompleted && (
                    <div className="grid grid-cols-3 gap-2 p-2.5 rounded-xl bg-surface-raised border border-border/70 text-center">
                      <div>
                        <span className="text-[9px] text-zinc-500 uppercase font-mono block">
                          {t.repositories.overallScore}
                        </span>
                        <span
                          className={`text-sm font-bold font-mono ${
                            (repo.overall_score || 0) >= 80
                              ? "text-emerald-400"
                              : (repo.overall_score || 0) >= 60
                              ? "text-amber-400"
                              : "text-red-400"
                          }`}
                        >
                          {repo.overall_score ? Math.round(repo.overall_score) : 0}/100
                        </span>
                      </div>

                      <div className="border-x border-border/60">
                        <span className="text-[9px] text-zinc-500 uppercase font-mono block">
                          {t.repositories.criticalIssues}
                        </span>
                        <span
                          className={`text-sm font-bold font-mono ${
                            (repo.critical_issues_count || 0) > 0 ? "text-red-400" : "text-zinc-300"
                          }`}
                        >
                          {repo.critical_issues_count || 0}
                        </span>
                      </div>

                      <div>
                        <span className="text-[9px] text-zinc-500 uppercase font-mono block">
                          {repo.primary_language || t.repositories.filesCount}
                        </span>
                        <span className="text-xs font-semibold text-zinc-300 font-mono">
                          {repo.total_files ? `${repo.total_files} f` : "Code"}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Quick Feature Navigation Shortcuts */}
                {isCompleted && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[9px] font-mono uppercase tracking-wider text-zinc-500 block">
                      {language === "tr" ? "Özelliklere Hızlı Erişim:" : "Quick Feature Access:"}
                    </span>
                    <div className="grid grid-cols-4 gap-1.5 text-center">
                      <Link
                        href={`/analyses/${targetAnalysisId}/architecture`}
                        className="p-1.5 rounded-lg bg-surface-raised hover:bg-zinc-800 border border-border hover:border-zinc-600 text-zinc-300 hover:text-white transition-all flex flex-col items-center gap-1 group/btn"
                        title={t.repositories.features.architecture}
                      >
                        <Network className="h-3.5 w-3.5 text-blue-400 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[9px] font-medium leading-none">{t.repositories.features.architecture}</span>
                      </Link>

                      <Link
                        href={`/analyses/${targetAnalysisId}/security`}
                        className="p-1.5 rounded-lg bg-surface-raised hover:bg-zinc-800 border border-border hover:border-zinc-600 text-zinc-300 hover:text-white transition-all flex flex-col items-center gap-1 group/btn"
                        title={t.repositories.features.security}
                      >
                        <ShieldAlert className="h-3.5 w-3.5 text-red-400 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[9px] font-medium leading-none">{t.repositories.features.security}</span>
                      </Link>

                      <Link
                        href={`/analyses/${targetAnalysisId}/performance`}
                        className="p-1.5 rounded-lg bg-surface-raised hover:bg-zinc-800 border border-border hover:border-zinc-600 text-zinc-300 hover:text-white transition-all flex flex-col items-center gap-1 group/btn"
                        title={t.repositories.features.performance}
                      >
                        <Zap className="h-3.5 w-3.5 text-amber-400 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[9px] font-medium leading-none">{t.repositories.features.performance}</span>
                      </Link>

                      <Link
                        href={`/analyses/${targetAnalysisId}/chat`}
                        className="p-1.5 rounded-lg bg-surface-raised hover:bg-zinc-800 border border-border hover:border-zinc-600 text-zinc-300 hover:text-white transition-all flex flex-col items-center gap-1 group/btn"
                        title={t.repositories.features.chat}
                      >
                        <MessageSquareCode className="h-3.5 w-3.5 text-indigo-400 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[9px] font-medium leading-none">{t.repositories.features.chat}</span>
                      </Link>
                    </div>

                    <div className="grid grid-cols-4 gap-1.5 text-center pt-1">
                      <Link
                        href={`/analyses/${targetAnalysisId}/quality`}
                        className="p-1.5 rounded-lg bg-surface-raised hover:bg-zinc-800 border border-border hover:border-zinc-600 text-zinc-300 hover:text-white transition-all flex flex-col items-center gap-1 group/btn"
                        title={t.repositories.features.quality}
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[9px] font-medium leading-none">{t.repositories.features.quality}</span>
                      </Link>

                      <Link
                        href={`/analyses/${targetAnalysisId}/dependencies`}
                        className="p-1.5 rounded-lg bg-surface-raised hover:bg-zinc-800 border border-border hover:border-zinc-600 text-zinc-300 hover:text-white transition-all flex flex-col items-center gap-1 group/btn"
                        title={t.repositories.features.dependencies}
                      >
                        <Package className="h-3.5 w-3.5 text-cyan-400 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[9px] font-medium leading-none">{t.repositories.features.dependencies}</span>
                      </Link>

                      <Link
                        href={`/analyses/${targetAnalysisId}/ai-review`}
                        className="p-1.5 rounded-lg bg-surface-raised hover:bg-zinc-800 border border-border hover:border-zinc-600 text-zinc-300 hover:text-white transition-all flex flex-col items-center gap-1 group/btn"
                        title={t.repositories.features.aiReview}
                      >
                        <Sparkles className="h-3.5 w-3.5 text-purple-400 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[9px] font-medium leading-none">{t.repositories.features.aiReview}</span>
                      </Link>

                      <Link
                        href={`/analyses/${targetAnalysisId}/report`}
                        className="p-1.5 rounded-lg bg-surface-raised hover:bg-zinc-800 border border-border hover:border-zinc-600 text-zinc-300 hover:text-white transition-all flex flex-col items-center gap-1 group/btn"
                        title={t.repositories.features.report}
                      >
                        <FileText className="h-3.5 w-3.5 text-zinc-300 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[9px] font-medium leading-none">{t.repositories.features.report}</span>
                      </Link>
                    </div>
                  </div>
                )}

                {/* Card Actions & Footer */}
                <div className="pt-3 border-t border-border/60 space-y-2.5">
                  <div className="flex items-center justify-between text-[11px] text-zinc-500 font-mono">
                    <div className="flex items-center gap-1">
                      <GitBranch className="h-3 w-3 text-zinc-400" />
                      <span>{repo.default_branch}</span>
                    </div>

                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3 text-zinc-400" />
                      <span>{new Date(repo.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Primary Button */}
                    {isCompleted ? (
                      <Link
                        href={`/analyses/${targetAnalysisId}`}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-all hover:shadow-blue-500/20"
                      >
                        <span>{t.repositories.openAnalysis}</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    ) : (
                      <button
                        onClick={(e) => handleReanalyze(e, repo)}
                        disabled={reanalyzingRepoId === repo.id}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${reanalyzingRepoId === repo.id ? "animate-spin" : ""}`} />
                        <span>{reanalyzingRepoId === repo.id ? t.landing.startingBtn : t.repositories.reanalyze}</span>
                      </button>
                    )}

                    {/* Analysis History Button */}
                    {(repo.analyses_count || 0) > 1 && (
                      <button
                        onClick={(e) => handleOpenHistory(e, repo)}
                        className="p-2 rounded-xl bg-surface-raised hover:bg-zinc-800 border border-border text-zinc-400 hover:text-white transition-colors"
                        title={`${repo.analyses_count} ${t.repositories.history}`}
                      >
                        <History className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* History Modal */}
      {historyModalRepo && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-surface border border-border rounded-2xl max-w-xl w-full p-6 space-y-4 shadow-2xl animate-scaleUp">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <History className="h-5 w-5 text-blue-400" />
                <h3 className="text-base font-bold text-white font-mono">
                  {historyModalRepo.name} — {t.repositories.history}
                </h3>
              </div>
              <button
                onClick={() => setHistoryModalRepo(null)}
                className="text-zinc-500 hover:text-white text-xs font-mono px-2 py-1 rounded-md bg-surface-raised border border-border"
              >
                ✕
              </button>
            </div>

            {historyLoading ? (
              <div className="flex justify-center py-8">
                <div className="h-6 w-6 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
              </div>
            ) : historyAnalyses.length === 0 ? (
              <p className="text-xs text-zinc-400 py-6 text-center font-mono">
                {language === "tr" ? "Geçmiş analiz kaydı bulunamadı." : "No previous analyses found."}
              </p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {historyAnalyses.map((item, idx) => (
                  <Link
                    key={item.id}
                    href={`/analyses/${item.id}`}
                    onClick={() => setHistoryModalRepo(null)}
                    className="p-3 rounded-xl bg-surface-raised hover:bg-zinc-800 border border-border flex items-center justify-between transition-all group"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-white group-hover:text-blue-400 transition-colors">
                          #{historyAnalyses.length - idx}
                        </span>
                        <span
                          className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold ${
                            item.status === "completed"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : item.status === "failed"
                              ? "bg-red-500/10 text-red-400 border border-red-500/20"
                              : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                          }`}
                        >
                          {item.status}
                        </span>
                        <span className="text-[11px] text-zinc-400 font-mono">
                          {item.branch || "main"}
                        </span>
                      </div>
                      <p className="text-[10px] text-zinc-500 font-mono">
                        {new Date(item.created_at).toLocaleString()} • {item.duration_seconds.toFixed(1)}s
                      </p>
                    </div>

                    <div className="text-right flex items-center gap-3">
                      {item.status === "completed" && (
                        <div>
                          <span className="text-[9px] text-zinc-500 uppercase font-mono block">Skor</span>
                          <span className="text-xs font-bold font-mono text-emerald-400">
                            {Math.round(item.overall_score)}/100
                          </span>
                        </div>
                      )}
                      <ArrowRight className="h-4 w-4 text-zinc-500 group-hover:text-white group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
