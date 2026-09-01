"use client";

import React from "react";

interface ScoreGaugeProps {
  score: number;
  label: string;
  size?: "sm" | "md" | "lg";
  subtitle?: string;
}

export function ScoreGauge({ score, label, size = "md", subtitle }: ScoreGaugeProps) {
  const normalized = Math.max(0, Math.min(100, score || 0));

  // Professional functional palette (no neon/glowing pinks)
  const getScoreColor = (val: number) => {
    if (val >= 85) return { stroke: "#10b981", text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" };
    if (val >= 70) return { stroke: "#3b82f6", text: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" };
    if (val >= 50) return { stroke: "#f59e0b", text: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" };
    return { stroke: "#ef4444", text: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" };
  };

  const theme = getScoreColor(normalized);

  const radius = size === "lg" ? 44 : size === "md" ? 34 : 26;
  const strokeWidth = size === "lg" ? 6 : size === "md" ? 5 : 4;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalized / 100) * circumference;
  const svgSize = (radius + strokeWidth) * 2;

  return (
    <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-surface border border-border text-center hover:border-zinc-700 transition-colors">
      <div className="relative flex items-center justify-center">
        <svg width={svgSize} height={svgSize} className="-rotate-90">
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            stroke="#27272a"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            stroke={theme.stroke}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`font-mono font-bold tracking-tight ${size === "lg" ? "text-2xl text-white" : size === "md" ? "text-lg text-white" : "text-sm text-white"}`}>
            {normalized.toFixed(0)}
          </span>
          <span className="text-[9px] font-mono text-zinc-500">/100</span>
        </div>
      </div>

      <div className="mt-2.5">
        <h4 className="text-xs font-semibold text-zinc-200">{label}</h4>
        {subtitle && <p className="text-[10px] text-zinc-500 font-mono mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}
