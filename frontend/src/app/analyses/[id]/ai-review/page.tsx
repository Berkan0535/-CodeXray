"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Network, ShieldAlert, Zap, CheckCircle2, Copy, Check, Terminal } from "lucide-react";
import { api } from "@/lib/api";
import { Analysis } from "@/types";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function AIReviewPage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { t } = useLanguage();

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [activeTab, setActiveTab] = useState<"architecture" | "security" | "performance" | "quality">("architecture");
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.getAnalysis(analysisId)
      .then(setAnalysis)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [analysisId]);

  if (loading || !analysis) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="h-6 w-6 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  const sections = analysis.ai_review_sections || {};
  const currentContent = sections[activeTab] || "AI analysis section generated during scan.";

  const tabs = [
    { key: "architecture", label: t.aiReview.tabs.architecture, icon: Network, color: "text-blue-400" },
    { key: "security", label: t.aiReview.tabs.security, icon: ShieldAlert, color: "text-red-400" },
    { key: "performance", label: t.aiReview.tabs.performance, icon: Zap, color: "text-amber-400" },
    { key: "quality", label: t.aiReview.tabs.quality, icon: CheckCircle2, color: "text-emerald-400" },
  ];

  const handleCopy = () => {
    navigator.clipboard.writeText(currentContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Header */}
      <div className="p-5 rounded-xl bg-surface border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
            <Terminal className="h-3 w-3 text-blue-400" />
            {t.aiReview.badge}
          </span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1">
            {t.aiReview.title}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            {t.aiReview.desc}
          </p>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-[#202024] border border-border text-xs font-mono font-medium text-zinc-300 hover:text-white transition-colors self-start sm:self-auto"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? t.aiReview.copied : t.aiReview.copySection}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 border-b border-border pb-2.5">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;

          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors border ${
                isActive
                  ? "bg-zinc-800 text-white border-zinc-700 shadow-sm"
                  : "bg-surface text-zinc-400 hover:text-white border-border hover:bg-surface-raised"
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${tab.color}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="p-6 rounded-xl bg-surface border border-border">
        <div className="text-xs text-zinc-200 leading-relaxed whitespace-pre-wrap font-sans">
          {currentContent}
        </div>
      </div>
    </div>
  );
}
