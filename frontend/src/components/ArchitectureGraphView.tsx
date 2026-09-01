"use client";

import { useState } from "react";
import { ArchitectureGraph, ArchitectureNode } from "@/types";
import { Layers, Box, ArrowRight, AlertCircle } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface ArchitectureGraphViewProps {
  graph: ArchitectureGraph;
}

export function ArchitectureGraphView({ graph }: ArchitectureGraphViewProps) {
  const { t } = useLanguage();
  const [selectedLayer, setSelectedLayer] = useState<string>("all");
  const [selectedNode, setSelectedNode] = useState<ArchitectureNode | null>(null);

  // Professional functional palette (understated, no neon/pink/magenta)
  const layerColors: Record<string, { bg: string; border: string; text: string; badge: string }> = {
    frontend: { bg: "bg-surface", border: "border-blue-500/30", text: "text-blue-400", badge: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
    api: { bg: "bg-surface", border: "border-indigo-500/30", text: "text-indigo-400", badge: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20" },
    service: { bg: "bg-surface", border: "border-purple-500/30", text: "text-purple-400", badge: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
    repository: { bg: "bg-surface", border: "border-amber-500/30", text: "text-amber-400", badge: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    database: { bg: "bg-surface", border: "border-emerald-500/30", text: "text-emerald-400", badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    infra: { bg: "bg-surface", border: "border-zinc-500/30", text: "text-zinc-300", badge: "bg-zinc-500/10 text-zinc-300 border-zinc-500/20" },
    core: { bg: "bg-surface", border: "border-zinc-700", text: "text-zinc-400", badge: "bg-zinc-800 text-zinc-400 border-zinc-700" },
  };

  const layersList = ["frontend", "api", "service", "repository", "database", "infra", "core"];

  // Group nodes by layer
  const nodesByLayer: Record<string, ArchitectureNode[]> = {};
  layersList.forEach((l) => (nodesByLayer[l] = []));
  
  graph.nodes.forEach((n) => {
    const layer = (n.layer || "core").toLowerCase();
    if (nodesByLayer[layer]) {
      nodesByLayer[layer].push(n);
    } else {
      nodesByLayer["core"].push(n);
    }
  });

  return (
    <div className="space-y-5">
      {/* Circular Dependencies Alert if any */}
      {graph.circular_dependencies && graph.circular_dependencies.length > 0 && (
        <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-red-400 font-mono">
              {graph.circular_dependencies.length} {t.architecture.circularAlert}
            </h4>
            <p className="text-xs text-zinc-300 mt-1">
              {t.architecture.circularDesc}
            </p>
            <ul className="mt-2 space-y-1">
              {graph.circular_dependencies.map((cycle, idx) => (
                <li key={idx} className="text-xs font-mono text-red-300">
                  {cycle.join(" ➔ ")}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Layer Filter Buttons */}
      <div className="flex flex-wrap items-center gap-1.5">
        <button
          onClick={() => setSelectedLayer("all")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-colors border ${
            selectedLayer === "all"
              ? "bg-zinc-800 text-white border-zinc-700 shadow-sm"
              : "bg-surface text-zinc-400 hover:text-white border-border hover:bg-surface-raised"
          }`}
        >
          {t.architecture.allLayers} ({graph.nodes.length})
        </button>

        {layersList.map((layer) => {
          const count = nodesByLayer[layer]?.length || 0;
          if (count === 0) return null;
          const style = layerColors[layer] || layerColors.core;

          return (
            <button
              key={layer}
              onClick={() => setSelectedLayer(layer)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono uppercase tracking-wider transition-colors border ${
                selectedLayer === layer
                  ? "bg-zinc-800 text-white border-zinc-700 shadow-sm"
                  : "bg-surface text-zinc-400 hover:text-white border-border hover:bg-surface-raised"
              }`}
            >
              {layer} ({count})
            </button>
          );
        })}
      </div>

      {/* Interactive Layer Pipeline Stack */}
      <div className="space-y-3">
        {layersList.map((layer, idx) => {
          const nodes = nodesByLayer[layer] || [];
          if (nodes.length === 0) return null;
          if (selectedLayer !== "all" && selectedLayer !== layer) return null;

          const style = layerColors[layer] || layerColors.core;

          return (
            <div key={layer} className="relative">
              <div className={`p-4 rounded-xl bg-surface border ${style.border} space-y-3`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Layers className={`h-4 w-4 ${style.text}`} />
                    <span className={`text-xs font-mono font-semibold uppercase tracking-wider ${style.text}`}>
                      {layer} Layer
                    </span>
                  </div>
                  <span className="text-[11px] text-zinc-500 font-mono">{nodes.length} module{nodes.length > 1 ? "s" : ""}</span>
                </div>

                {/* Nodes Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
                  {nodes.map((node) => (
                    <button
                      key={node.node_id}
                      onClick={() => setSelectedNode(node)}
                      className={`p-2.5 rounded-lg bg-surface-raised hover:bg-[#202024] border border-border text-left transition-colors ${
                        selectedNode?.node_id === node.node_id ? "ring-1 ring-blue-500 border-blue-500" : ""
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-1">
                        <Box className="h-3 w-3 text-zinc-400 shrink-0" />
                        <span className="text-xs font-semibold text-white truncate">{node.name}</span>
                      </div>
                      <p className="text-[10px] text-zinc-500 font-mono truncate">{node.file_path || node.node_id}</p>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/60 text-[10px] text-zinc-400 font-mono">
                        <span>{node.lines_of_code} LOC</span>
                        <span>{node.dependencies_count} deps</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Connecting Flow Arrow */}
              {idx < layersList.length - 1 && selectedLayer === "all" && (
                <div className="flex justify-center my-1 text-zinc-600">
                  <ArrowRight className="h-3.5 w-3.5 rotate-90" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="p-4 rounded-xl bg-surface-raised border border-border flex items-start justify-between animate-fadeIn">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                {selectedNode.layer}
              </span>
              <h4 className="text-sm font-bold text-white font-mono">{selectedNode.name}</h4>
            </div>
            <p className="text-xs text-zinc-400 font-mono mt-1">path: {selectedNode.file_path || selectedNode.node_id}</p>
            <div className="flex items-center gap-4 mt-2 text-xs text-zinc-300 font-mono">
              <span>{t.architecture.linesOfCode} <strong>{selectedNode.lines_of_code}</strong></span>
              <span>{t.architecture.dependencies} <strong>{selectedNode.dependencies_count}</strong></span>
            </div>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="text-xs text-zinc-400 hover:text-white px-2.5 py-1 rounded bg-surface border border-border"
          >
            {t.architecture.close}
          </button>
        </div>
      )}
    </div>
  );
}
