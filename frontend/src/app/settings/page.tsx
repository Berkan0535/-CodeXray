"use client";

import { useState } from "react";
import { Settings, Cpu, Shield, Key, Save, Check } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function SettingsPage() {
  const { t } = useLanguage();
  const [provider, setProvider] = useState("mock");
  const [openaiKey, setOpenaiKey] = useState("");
  const [geminiKey, setGeminiKey] = useState("");
  const [maxFiles, setMaxFiles] = useState(3000);
  const [maxSizeMb, setMaxSizeMb] = useState(150);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-5 animate-fadeIn">
      {/* Header */}
      <div className="p-5 rounded-xl bg-surface border border-border flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">{t.settings.badge}</span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <Settings className="h-5 w-5 text-blue-400" />
            {t.settings.title}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            {t.settings.desc}
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-4">
        {/* AI Provider Section */}
        <div className="p-5 rounded-xl bg-surface border border-border space-y-3">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-blue-400" />
            <h3 className="text-xs font-semibold text-white">{t.settings.providerSelection}</h3>
          </div>
          <p className="text-xs text-zinc-400">
            {t.settings.providerDesc}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
            {[
              { id: "mock", name: t.settings.mockTitle, desc: t.settings.mockDesc },
              { id: "openai", name: t.settings.openaiTitle, desc: t.settings.openaiDesc },
              { id: "gemini", name: t.settings.geminiTitle, desc: t.settings.geminiDesc },
            ].map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setProvider(opt.id)}
                className={`p-3 rounded-lg border text-left transition-colors ${
                  provider === opt.id
                    ? "bg-zinc-800 border-zinc-600 text-white"
                    : "bg-surface-raised border-border text-zinc-400 hover:text-white"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-white">{opt.name}</span>
                  {provider === opt.id && <Check className="h-3.5 w-3.5 text-blue-400" />}
                </div>
                <p className="text-[11px] text-zinc-400 leading-tight">{opt.desc}</p>
              </button>
            ))}
          </div>

          {/* API Keys */}
          {provider === "openai" && (
            <div className="pt-2 space-y-1.5">
              <label className="text-xs font-mono font-medium text-zinc-300 flex items-center gap-1.5">
                <Key className="h-3 w-3 text-zinc-400" />
                OpenAI API Key
              </label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full p-2.5 rounded-lg bg-[#09090b] border border-border text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-mono"
              />
            </div>
          )}

          {provider === "gemini" && (
            <div className="pt-2 space-y-1.5">
              <label className="text-xs font-mono font-medium text-zinc-300 flex items-center gap-1.5">
                <Key className="h-3 w-3 text-zinc-400" />
                Google Gemini API Key
              </label>
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="AIza..."
                className="w-full p-2.5 rounded-lg bg-[#09090b] border border-border text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-mono"
              />
            </div>
          )}
        </div>

        {/* Resource Limits Section */}
        <div className="p-5 rounded-xl bg-surface border border-border space-y-3">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-emerald-400" />
            <h3 className="text-xs font-semibold text-white">{t.settings.resourceLimits}</h3>
          </div>
          <p className="text-xs text-zinc-400">
            {t.settings.resourceDesc}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div className="space-y-1">
              <label className="text-xs font-medium text-zinc-300">{t.settings.maxRepoSize}</label>
              <input
                type="number"
                value={maxSizeMb}
                onChange={(e) => setMaxSizeMb(Number(e.target.value))}
                className="w-full p-2 rounded-lg bg-[#09090b] border border-border text-xs text-white focus:outline-none focus:border-zinc-500 font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-zinc-300">{t.settings.maxFilesScanned}</label>
              <input
                type="number"
                value={maxFiles}
                onChange={(e) => setMaxFiles(Number(e.target.value))}
                className="w-full p-2 rounded-lg bg-[#09090b] border border-border text-xs text-white focus:outline-none focus:border-zinc-500 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-colors"
          >
            {saved ? <Check className="h-3.5 w-3.5 text-white" /> : <Save className="h-3.5 w-3.5" />}
            <span>{saved ? t.settings.savedBtn : t.settings.saveBtn}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
