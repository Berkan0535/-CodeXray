"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import {
  MessageSquareCode,
  Send,
  Terminal,
  Bot,
  User,
  FileCode,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from "lucide-react";
import { api } from "@/lib/api";
import { ChatMessage } from "@/types";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const SUGGESTIONS_TR = [
  "Kimlik doğrulama (auth) nasıl çalışıyor?",
  "Veritabanı modelleri ve ilişkileri nerede tanımlı?",
  "Bu projedeki en büyük güvenlik ve performans riskleri neler?",
  "Hata yakalama (error handling) mekanizması nasıl tasarlanmış?",
];

const SUGGESTIONS_EN = [
  "How does authentication and authorization work?",
  "Where are the database models and migrations defined?",
  "What are the top security risks in this codebase?",
  "How is error handling and validation implemented?",
];

export default function AskCodebaseChatPage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { language, t } = useLanguage();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedCitation, setExpandedCitation] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getChatHistory(analysisId).then(setMessages).catch(console.error);
  }, [analysisId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    setInput("");
    const userMsg: ChatMessage = {
      id: "temp-" + Date.now(),
      role: "user",
      content: text,
      citations: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const resp = await api.sendChatMessage(analysisId, text);
      setMessages((prev) => [...prev, resp]);
    } catch (e: any) {
      console.error(e);
      const errMsg: ChatMessage = {
        id: "err-" + Date.now(),
        role: "assistant",
        content: `Error: ${e.message || "Failed to process question with RAG."}`,
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const copyAnswer = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const suggestions = language === "tr" ? SUGGESTIONS_TR : SUGGESTIONS_EN;

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] space-y-3 animate-fadeIn">
      {/* Header */}
      <div className="p-3.5 rounded-xl bg-surface border border-border flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-300">
            <MessageSquareCode className="h-4 w-4 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xs font-bold text-white flex items-center gap-1.5">
              <span>{t.chat.title}</span>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
                {t.chat.ragBadge}
              </span>
            </h1>
            <p className="text-[11px] text-zinc-500 font-mono">{t.chat.subtitle}</p>
          </div>
        </div>
      </div>

      {/* Chat Messages Log */}
      <div className="flex-1 p-4 rounded-xl bg-surface border border-border overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-4">
            <div className="h-10 w-10 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300">
              <Terminal className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">{t.chat.emptyTitle}</h3>
              <p className="text-xs text-zinc-400 max-w-md mt-1">
                {t.chat.emptyDesc}
              </p>
            </div>

            {/* Suggestions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full pt-1">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="p-2.5 rounded-lg bg-surface-raised hover:bg-[#202024] border border-border text-left text-xs text-zinc-300 hover:text-white transition-colors"
                >
                  "{s}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={`flex items-start gap-2.5 ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div
                className={`h-7 w-7 rounded-md flex items-center justify-center shrink-0 text-xs ${
                  m.role === "user"
                    ? "bg-blue-600 text-white font-mono"
                    : "bg-zinc-800 border border-zinc-700 text-zinc-300"
                }`}
              >
                {m.role === "user" ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
              </div>

              <div
                className={`max-w-2xl rounded-xl p-3.5 text-xs leading-relaxed space-y-2.5 ${
                  m.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-none"
                    : "bg-surface-raised border border-border text-zinc-200 rounded-tl-none"
                }`}
              >
                <div className="whitespace-pre-wrap">{m.content}</div>

                {/* Citations from Codebase */}
                {m.citations && m.citations.length > 0 && (
                  <div className="pt-2 border-t border-zinc-700/60 space-y-1.5">
                    <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400 block">
                      {t.chat.contextTitle} ({m.citations.length})
                    </span>
                    <div className="space-y-1">
                      {m.citations.map((cit, idx) => {
                        const citKey = `${m.id}-cit-${idx}`;
                        const isExp = expandedCitation === citKey;

                        return (
                          <div key={citKey} className="rounded-md bg-[#09090b] border border-border p-2 text-[11px]">
                            <div
                              onClick={() => setExpandedCitation(isExp ? null : citKey)}
                              className="flex items-center justify-between cursor-pointer text-zinc-300 hover:text-white"
                            >
                              <div className="flex items-center gap-1.5 font-mono">
                                <FileCode className="h-3 w-3 text-zinc-400 shrink-0" />
                                <span>{cit.file_path}:{cit.line_number || 1}</span>
                                {cit.symbol_name && (
                                  <span className="text-zinc-500">({cit.symbol_name})</span>
                                )}
                              </div>
                              {isExp ? <ChevronUp className="h-3 w-3 text-zinc-500" /> : <ChevronDown className="h-3 w-3 text-zinc-500" />}
                            </div>

                            {isExp && cit.snippet && (
                              <pre className="mt-2 p-2 rounded bg-black/50 border border-zinc-800 font-mono text-[10px] text-zinc-300 overflow-x-auto">
                                <code>{cit.snippet}</code>
                              </pre>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Copy button for Assistant messages */}
                {m.role === "assistant" && (
                  <div className="flex justify-end pt-1">
                    <button
                      onClick={() => copyAnswer(m.id, m.content)}
                      className="text-[10px] text-zinc-400 hover:text-white flex items-center gap-1 font-mono"
                    >
                      {copiedId === m.id ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      {copiedId === m.id ? t.chat.copied : t.chat.copyResponse}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="flex items-start gap-2.5">
            <div className="h-7 w-7 rounded-md bg-zinc-800 border border-zinc-700 text-zinc-300 flex items-center justify-center">
              <Bot className="h-3.5 w-3.5" />
            </div>
            <div className="p-3 rounded-xl rounded-tl-none bg-surface-raised border border-border flex items-center gap-2 text-xs text-zinc-400 font-mono">
              <div className="h-3 w-3 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
              {t.chat.thinking}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-1.5 rounded-xl bg-surface border border-border flex items-center gap-2 focus-within:border-zinc-500"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t.chat.inputPlaceholder}
          disabled={loading}
          className="flex-1 bg-transparent px-3 text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="flex items-center justify-center p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-40"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </form>
    </div>
  );
}
