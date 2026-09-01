"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Package, CheckCircle, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { Dependency } from "@/types";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function DependenciesPage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { t } = useLanguage();

  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterEco, setFilterEco] = useState<string>("ALL");

  useEffect(() => {
    api.getDependencies(analysisId)
      .then(setDependencies)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [analysisId]);

  const ecosystems = Array.from(new Set(dependencies.map((d) => d.ecosystem)));
  const filtered = filterEco === "ALL" ? dependencies : dependencies.filter((d) => d.ecosystem === filterEco);
  const totalVulns = dependencies.reduce((acc, d) => acc + d.vulnerabilities_count, 0);

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-surface border border-border">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">{t.dependencies.badge}</span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            <Package className="h-5 w-5 text-blue-400" />
            {t.dependencies.title}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            {t.dependencies.desc}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-lg bg-surface-raised border border-border text-center">
            <span className="text-[10px] text-zinc-500 uppercase font-mono font-medium">{t.dependencies.totalPackages}</span>
            <p className="text-base font-mono font-bold text-white mt-0.5">{dependencies.length}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-surface-raised border border-border text-center">
            <span className="text-[10px] text-zinc-500 uppercase font-mono font-medium">{t.dependencies.vulnerabilities}</span>
            <p className={`text-base font-mono font-bold mt-0.5 ${totalVulns > 0 ? "text-red-400" : "text-emerald-400"}`}>{totalVulns}</p>
          </div>
        </div>
      </div>

      {/* Ecosystem Filters */}
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => setFilterEco("ALL")}
          className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium transition-colors border ${
            filterEco === "ALL"
              ? "bg-zinc-800 text-white border-zinc-700 shadow-sm"
              : "bg-surface text-zinc-400 hover:text-white border-border hover:bg-surface-raised"
          }`}
        >
          {t.dependencies.all} ({dependencies.length})
        </button>
        {ecosystems.map((eco) => (
          <button
            key={eco}
            onClick={() => setFilterEco(eco)}
            className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium uppercase transition-colors border ${
              filterEco === eco
                ? "bg-zinc-800 text-white border-zinc-700 shadow-sm"
                : "bg-surface text-zinc-400 hover:text-white border-border hover:bg-surface-raised"
            }`}
          >
            {eco} ({dependencies.filter((d) => d.ecosystem === eco).length})
          </button>
        ))}
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-10 text-center rounded-xl bg-surface border border-border">
          <Package className="h-6 w-6 text-zinc-500 mx-auto mb-2" />
          <h3 className="text-xs font-semibold text-white">{t.dependencies.noDepsTitle}</h3>
          <p className="text-xs text-zinc-400 mt-1 font-mono">{t.dependencies.noDepsDesc}</p>
        </div>
      ) : (
        <div className="rounded-xl bg-surface border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-raised text-zinc-400 border-b border-border font-mono text-[10px] uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-4">{t.dependencies.tablePackage}</th>
                  <th className="py-2.5 px-4">{t.dependencies.tableVersion}</th>
                  <th className="py-2.5 px-4">{t.dependencies.tableEcosystem}</th>
                  <th className="py-2.5 px-4">{t.dependencies.tableSource}</th>
                  <th className="py-2.5 px-4">{t.dependencies.tableStatus}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filtered.map((dep) => (
                  <tr key={dep.id} className="hover:bg-surface-raised/40 transition-colors">
                    <td className="py-2.5 px-4 font-mono font-semibold text-white flex items-center gap-2">
                      <Package className="h-3 w-3 text-zinc-500" />
                      {dep.name}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-zinc-300">{dep.version}</td>
                    <td className="py-2.5 px-4">
                      <span className="px-1.5 py-0.2 rounded bg-surface-raised text-zinc-300 font-mono text-[10px] border border-border">
                        {dep.ecosystem}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 font-mono text-zinc-400 text-[11px]">{dep.manifest_file}</td>
                    <td className="py-2.5 px-4">
                      {dep.vulnerabilities_count > 0 ? (
                        <div className="space-y-1">
                          {dep.vulnerabilities.map((v, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] font-mono font-bold mr-1"
                            >
                              <AlertTriangle className="h-3 w-3" />
                              {v.cve} ({v.severity})
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-mono text-[11px]">
                          <CheckCircle className="h-3 w-3" />
                          {t.dependencies.secure}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
