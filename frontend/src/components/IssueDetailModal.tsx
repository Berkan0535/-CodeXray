"use client";

import { useState } from "react";
import { X, Sparkles, AlertTriangle, CheckCircle, Copy, Check, Wrench, FileCode } from "lucide-react";
import { Issue, IssueExplainResult } from "@/types";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface IssueDetailModalProps {
  issue: Issue | null;
  onClose: () => void;
}

export function IssueDetailModal({ issue, onClose }: IssueDetailModalProps) {
  const { t, language } = useLanguage();
  const [explaining, setExplaining] = useState(false);
  const [aiExplanation, setAiExplanation] = useState<IssueExplainResult | null>(null);
  const [copied, setCopied] = useState(false);

  if (!issue) return null;

  const handleExplainWithAI = async () => {
    setExplaining(true);
    try {
      const res = await api.explainIssue(issue.analysis_id, issue.id, undefined, language);
      setAiExplanation(res);
    } catch (e) {
      console.error(e);
    } finally {
      setExplaining(false);
    }
  };

  const copyCode = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const severityBadges: Record<string, string> = {
    CRITICAL: "bg-red-500/10 text-red-400 border-red-500/20",
    HIGH: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    MEDIUM: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    LOW: "bg-zinc-800 text-zinc-400 border-zinc-700",
    INFO: "bg-zinc-800 text-zinc-400 border-zinc-700",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-3xl rounded-xl bg-surface border border-border shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border bg-surface-raised">
          <div className="flex items-center gap-2.5">
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${severityBadges[issue.severity] || severityBadges.MEDIUM}`}>
              {issue.severity}
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface border border-border text-zinc-300">
              {issue.category}
            </span>
            <span className="text-xs text-zinc-400 font-mono">
              {issue.file_path}:{issue.line_number}
            </span>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-5 overflow-y-auto">
          {/* Title & Description */}
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">{issue.title}</h3>
            <p className="mt-1 text-xs text-zinc-300 leading-relaxed">{issue.description}</p>
          </div>

          {/* Code Snippet */}
          {issue.code_snippet && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-mono font-medium text-zinc-400 flex items-center gap-1.5">
                  <FileCode className="h-3.5 w-3.5 text-zinc-400" />
                  {t.modal.codeContext} ({issue.file_path}:{issue.line_number})
                </span>
                <button
                  onClick={() => copyCode(issue.code_snippet!)}
                  className="text-xs text-zinc-400 hover:text-white flex items-center gap-1 font-mono"
                >
                  {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                  {copied ? t.modal.copied : t.modal.copy}
                </button>
              </div>
              <pre className="p-3 rounded-lg bg-[#09090b] border border-border text-xs text-red-300 font-mono overflow-x-auto">
                <code>{issue.code_snippet}</code>
              </pre>
            </div>
          )}

          {/* Impact & Recommendation */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {issue.impact && (
              <div className="p-3.5 rounded-lg bg-surface-raised border border-border">
                <h4 className="text-xs font-semibold text-amber-400 flex items-center gap-1.5 mb-1">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  {t.modal.impact}
                </h4>
                <p className="text-xs text-zinc-300 leading-relaxed">{issue.impact}</p>
              </div>
            )}

            {issue.recommendation && (
              <div className="p-3.5 rounded-lg bg-surface-raised border border-border">
                <h4 className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 mb-1">
                  <CheckCircle className="h-3.5 w-3.5" />
                  {t.modal.recommendation}
                </h4>
                <p className="text-xs text-zinc-300 leading-relaxed">{issue.recommendation}</p>
              </div>
            )}
          </div>

          {/* Suggested Fix (Static or AI) */}
          {issue.suggested_fix && (
            <div>
              <h4 className="text-xs font-semibold text-blue-400 flex items-center gap-1.5 mb-1.5">
                <Wrench className="h-3.5 w-3.5" />
                {t.modal.suggestedRefactoring}
              </h4>
              <pre className="p-3 rounded-lg bg-[#09090b] border border-border text-xs text-emerald-300 font-mono overflow-x-auto">
                <code>{issue.suggested_fix}</code>
              </pre>
            </div>
          )}

          {/* AI Explanation Area */}
          {aiExplanation ? (
            <div className="p-4 rounded-lg bg-surface-raised border border-zinc-700 space-y-3">
              <div className="flex items-center gap-2 text-xs font-mono font-semibold text-zinc-200">
                <Sparkles className="h-4 w-4 text-blue-400" />
                {t.modal.aiRootCause}
              </div>
              <div className="text-xs text-zinc-200 leading-relaxed whitespace-pre-wrap font-sans">
                {aiExplanation.explanation}
              </div>
              {aiExplanation.suggested_code && (
                <div>
                  <span className="text-[11px] font-mono text-zinc-400">{t.modal.refactoredCode}</span>
                  <pre className="mt-1 p-3 rounded-lg bg-[#09090b] border border-border text-xs text-emerald-300 font-mono overflow-x-auto">
                    <code>{aiExplanation.suggested_code}</code>
                  </pre>
                </div>
              )}
              <p className="text-[10px] text-zinc-500 font-mono italic">{aiExplanation.confidence_note}</p>
            </div>
          ) : (
            <div className="pt-2">
              <button
                onClick={handleExplainWithAI}
                disabled={explaining}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
              >
                <Sparkles className={`h-3.5 w-3.5 ${explaining ? "animate-spin" : ""}`} />
                <span>{explaining ? t.modal.analyzingAi : t.modal.explainWithAi}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
