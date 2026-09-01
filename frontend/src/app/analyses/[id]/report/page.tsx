"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { FileText, Download, Copy, Check } from "lucide-react";
import { api } from "@/lib/api";
import { ReportData } from "@/types";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function ReportPage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { t, language } = useLanguage();

  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getReport(analysisId, "json", language)
      .then((data) => setReport(data as ReportData))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [analysisId, language]);

  const handleDownloadMarkdown = () => {
    if (!report?.markdown_report) return;
    const blob = new Blob([report.markdown_report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `codebase-analysis-${report.analysis.repository?.name || "report"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyMarkdown = () => {
    if (!report?.markdown_report) return;
    navigator.clipboard.writeText(report.markdown_report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading || !report) {
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
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">{t.report.badge}</span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-400" />
            {t.report.title}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            {t.report.desc}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyMarkdown}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-[#202024] border border-border text-xs font-mono font-medium text-zinc-300 hover:text-white transition-colors"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? t.report.copied : t.report.copyMarkdown}
          </button>

          <button
            onClick={handleDownloadMarkdown}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            {t.report.downloadMarkdown}
          </button>
        </div>
      </div>

      {/* Report Document Box */}
      <div className="p-6 rounded-xl bg-surface border border-border">
        <pre className="text-xs text-zinc-300 whitespace-pre-wrap font-mono leading-relaxed overflow-x-auto">
          <code>{report.markdown_report}</code>
        </pre>
      </div>
    </div>
  );
}
