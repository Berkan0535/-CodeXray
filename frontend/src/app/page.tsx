"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Shield,
  Zap,
  Network,
  CheckCircle2,
  GitBranch,
  Terminal,
  AlertCircle,
  Key,
  ChevronDown,
  ChevronUp,
  MessageSquareCode,
  Layers,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import { AnalysisStatus, Repository } from "@/types";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const STAGE_KEYS = [
  "CLONING",
  "FILE_SCANNING",
  "LANGUAGE_DETECTION",
  "PROJECT_DETECTION",
  "CODE_PARSING",
  "DEPENDENCY_ANALYSIS",
  "SECURITY_SCAN",
  "PERFORMANCE_ANALYSIS",
  "QUALITY_ANALYSIS",
  "ARCHITECTURE_ANALYSIS",
  "SCORING",
  "AI_REVIEW",
  "RAG_INDEXING",
];

export default function LandingPage() {
  const router = useRouter();
  const { language, t } = useLanguage();
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [authToken, setAuthToken] = useState("");
  const [showTokenInput, setShowTokenInput] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentRepos, setRecentRepos] = useState<Repository[]>([]);

  const [activeAnalysisId, setActiveAnalysisId] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);

  useEffect(() => {
    api.listRepositories()
      .then((repos) => setRecentRepos(repos.slice(0, 6)))
      .catch(console.error);
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!repoUrl.trim()) {
      setError(language === "tr" ? "Lütfen geçerli bir GitHub depo URL'si girin." : "Please enter a valid GitHub repository URL.");
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const analysis = await api.analyzeRepository(
        repoUrl.trim(),
        branch.trim() || undefined,
        authToken.trim() || undefined
      );
      setActiveAnalysisId(analysis.id);
      setAnalysisStatus({
        id: analysis.id,
        repository_id: analysis.repository_id,
        status: analysis.status,
        stage: analysis.stage,
        progress_percent: analysis.progress_percent,
        created_at: analysis.created_at,
        duration_seconds: 0,
      });
    } catch (err: any) {
      setError(err.message || (language === "tr" ? "Analiz başlatılamadı." : "Failed to initiate repository analysis."));
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!activeAnalysisId) return;

    const interval = setInterval(async () => {
      try {
        const status = await api.getAnalysisStatus(activeAnalysisId);
        setAnalysisStatus(status);

        if (status.status === "completed") {
          clearInterval(interval);
          setTimeout(() => {
            router.push(`/analyses/${activeAnalysisId}`);
          }, 600);
        } else if (status.status === "failed") {
          clearInterval(interval);
          setError(status.error_message || (language === "tr" ? "Analiz başarısız oldu." : "Analysis failed."));
          setIsLoading(false);
        }
      } catch (err) {
        console.error("Poll error:", err);
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [activeAnalysisId, router, language]);

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] flex flex-col justify-center px-4 py-16 sm:px-6 lg:px-8 max-w-5xl mx-auto">
      <div className="text-center space-y-4">
        {/* Clean, high-contrast headline */}
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white max-w-3xl mx-auto leading-tight">
          {t.landing.heroTitlePrefix}{" "}
          <span className="text-zinc-100">{t.landing.heroTitleHighlight}</span>{" "}
          {t.landing.heroTitleSuffix}
        </h1>

        <p className="text-sm sm:text-base text-zinc-400 max-w-2xl mx-auto leading-relaxed">
          {t.landing.heroDesc}
        </p>

        {/* Command Bar Form */}
        <div className="mt-8 max-w-2xl mx-auto w-full pt-2">
          {!activeAnalysisId ? (
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="flex flex-col sm:flex-row items-center gap-2 p-1.5 rounded-xl bg-surface border border-border shadow-lg focus-within:border-zinc-500 transition-colors">
                <div className="flex-1 flex items-center gap-2 px-3 w-full">
                  <Terminal className="h-4 w-4 text-zinc-500 shrink-0" />
                  <input
                    type="text"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder={t.landing.inputPlaceholder}
                    disabled={isLoading}
                    className="w-full bg-transparent border-0 text-xs sm:text-sm text-white placeholder-zinc-500 focus:outline-none font-mono"
                  />
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-raised border border-border text-xs text-zinc-400">
                    <GitBranch className="h-3 w-3 text-zinc-400" />
                    <input
                      type="text"
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      placeholder={t.landing.branchPlaceholder}
                      className="w-14 bg-transparent text-xs text-white focus:outline-none font-mono"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
                  >
                    <span>{isLoading ? t.landing.startingBtn : t.landing.analyzeBtn}</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {/* Private Repo Auth Toggle */}
              <div className="text-left">
                <button
                  type="button"
                  onClick={() => setShowTokenInput(!showTokenInput)}
                  className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors inline-flex items-center gap-1.5 px-1 py-0.5"
                >
                  <Key className="h-3 w-3" />
                  <span>{t.landing.tokenToggle}</span>
                  {showTokenInput ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>

                {showTokenInput && (
                  <div className="mt-2 p-2 rounded-lg bg-surface border border-border flex items-center gap-2 animate-fadeIn">
                    <Key className="h-3.5 w-3.5 text-zinc-400 shrink-0 ml-1" />
                    <input
                      type="password"
                      value={authToken}
                      onChange={(e) => setAuthToken(e.target.value)}
                      placeholder={t.landing.tokenPlaceholder}
                      className="w-full bg-transparent text-xs text-white placeholder-zinc-600 focus:outline-none font-mono"
                    />
                  </div>
                )}
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-950/30 border border-red-500/30 text-xs text-red-300 flex items-center gap-2.5 text-left animate-fadeIn">
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
                  <span>{error}</span>
                </div>
              )}
            </form>
          ) : (
            /* Live Analysis Progress View */
            <div className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-5 text-left animate-fadeIn">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-wider text-blue-400">{t.landing.inProgressBadge}</span>
                  <h3 className="text-sm font-semibold text-white mt-0.5 truncate max-w-sm font-mono">{repoUrl}</h3>
                </div>
                <div className="text-right">
                  <span className="text-xl font-mono font-bold text-white">{analysisStatus?.progress_percent || 0}%</span>
                  <p className="text-[10px] text-zinc-500 font-mono">{t.landing.elapsed} {analysisStatus?.duration_seconds || 0}s</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${analysisStatus?.progress_percent || 5}%` }}
                />
              </div>

              {/* Live Stages Checklist */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-border">
                {STAGE_KEYS.map((stageKey, idx) => {
                  const currentIdx = STAGE_KEYS.findIndex((s) => s === analysisStatus?.stage);
                  const isDone = currentIdx > idx || analysisStatus?.status === "completed";
                  const isCurrent = analysisStatus?.stage === stageKey;
                  const label = (t.landing.stages as any)[stageKey] || stageKey;

                  return (
                    <div
                      key={stageKey}
                      className={`flex items-center gap-2 p-2 rounded-md text-xs transition-colors ${
                        isCurrent
                          ? "bg-zinc-800 text-white font-medium border border-zinc-700"
                          : isDone
                          ? "text-zinc-300"
                          : "text-zinc-600"
                      }`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                      ) : isCurrent ? (
                        <div className="h-3.5 w-3.5 rounded-full border-2 border-blue-400 border-t-transparent animate-spin shrink-0" />
                      ) : (
                        <div className="h-3.5 w-3.5 rounded-full border border-zinc-700 shrink-0" />
                      )}
                      <span className="truncate">{label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Recently Analyzed Repositories Showcase */}
        {recentRepos.length > 0 && !activeAnalysisId && (
          <div className="mt-8 max-w-3xl mx-auto w-full text-left space-y-3 animate-fadeIn">
            <div className="flex items-center justify-between px-1">
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-blue-400" />
                {language === "tr" ? "Son Analiz Edilen Projeler" : "Recently Analyzed Repositories"}
              </span>
              <Link
                href="/repositories"
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors font-mono flex items-center gap-1 hover:underline"
              >
                <span>{language === "tr" ? "Tümünü Gör" : "View All"}</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {recentRepos.map((repo) => {
                const targetId = repo.latest_analysis_id || repo.id;
                const isCompleted = repo.latest_status === "completed" || ((repo.overall_score || 0) > 0);

                return (
                  <Link
                    key={repo.id}
                    href={`/analyses/${targetId}`}
                    className="p-3 rounded-xl bg-surface hover:bg-surface-raised border border-border hover:border-zinc-700 transition-all flex flex-col justify-between space-y-2 group shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <span className="text-[9px] font-mono text-zinc-500 uppercase block truncate">
                          {repo.owner}
                        </span>
                        <h4 className="text-xs font-bold text-white font-mono truncate group-hover:text-blue-400 transition-colors">
                          {repo.name}
                        </h4>
                      </div>

                      {isCompleted && (repo.overall_score || 0) > 0 ? (
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold shrink-0 ${
                            (repo.overall_score || 0) >= 80
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : (repo.overall_score || 0) >= 60
                              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                              : "bg-red-500/10 text-red-400 border border-red-500/20"
                          }`}
                        >
                          {Math.round(repo.overall_score || 0)}/100
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-zinc-800 text-zinc-400 border border-zinc-700 shrink-0">
                          {repo.latest_status || repo.default_branch}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-zinc-500 font-mono pt-1 border-t border-border/50">
                      <span className="truncate">{repo.primary_language || repo.default_branch}</span>
                      <span className="text-blue-400 group-hover:underline flex items-center gap-0.5">
                        {language === "tr" ? "İncele" : "Open"} →
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {/* Feature Grid */}
        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-left">
          <div className="p-4 rounded-xl bg-surface border border-border hover:border-zinc-700 transition-colors">
            <Network className="h-5 w-5 text-blue-400 mb-2.5" />
            <h3 className="text-xs font-semibold text-white">{t.landing.features.architecture.title}</h3>
            <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
              {t.landing.features.architecture.desc}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-surface border border-border hover:border-zinc-700 transition-colors">
            <Shield className="h-5 w-5 text-emerald-400 mb-2.5" />
            <h3 className="text-xs font-semibold text-white">{t.landing.features.security.title}</h3>
            <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
              {t.landing.features.security.desc}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-surface border border-border hover:border-zinc-700 transition-colors">
            <Zap className="h-5 w-5 text-amber-400 mb-2.5" />
            <h3 className="text-xs font-semibold text-white">{t.landing.features.performance.title}</h3>
            <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
              {t.landing.features.performance.desc}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-surface border border-border hover:border-zinc-700 transition-colors">
            <MessageSquareCode className="h-5 w-5 text-zinc-300 mb-2.5" />
            <h3 className="text-xs font-semibold text-white">{t.landing.features.rag.title}</h3>
            <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
              {t.landing.features.rag.desc}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
