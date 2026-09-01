"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Network } from "lucide-react";
import { api } from "@/lib/api";
import { ArchitectureGraph } from "@/types";
import { ArchitectureGraphView } from "@/components/ArchitectureGraphView";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function ArchitecturePage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { t } = useLanguage();

  const [graph, setGraph] = useState<ArchitectureGraph | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getArchitecture(analysisId)
      .then(setGraph)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [analysisId]);

  if (loading || !graph) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="h-8 w-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-surface border border-border">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">{t.architecture.badge}</span>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1 flex items-center gap-2.5">
            <Network className="h-6 w-6 text-indigo-400" />
            {t.architecture.title}
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            {t.architecture.desc}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-surface-raised border border-border text-center">
            <span className="text-[10px] text-gray-400 uppercase font-bold">{t.architecture.totalModules}</span>
            <p className="text-lg font-black text-white">{graph.nodes.length}</p>
          </div>
          <div className="p-3 rounded-xl bg-surface-raised border border-border text-center">
            <span className="text-[10px] text-gray-400 uppercase font-bold">{t.architecture.importEdges}</span>
            <p className="text-lg font-black text-white">{graph.edges.length}</p>
          </div>
        </div>
      </div>

      {/* Interactive Layer Visualizer */}
      <ArchitectureGraphView graph={graph} />
    </div>
  );
}
