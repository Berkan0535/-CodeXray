"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { api } from "@/lib/api";
import { Analysis } from "@/types";

export default function AnalysisLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const router = useRouter();
  const analysisId = params.id as string;
  const [analysis, setAnalysis] = useState<Analysis | undefined>(undefined);
  const [isReanalyzing, setIsReanalyzing] = useState(false);

  useEffect(() => {
    if (!analysisId) return;
    api.getAnalysis(analysisId).then(setAnalysis).catch(console.error);
  }, [analysisId]);

  const handleReanalyze = async () => {
    setIsReanalyzing(true);
    try {
      await api.reanalyze(analysisId);
      router.push("/");
    } catch (e) {
      console.error(e);
      setIsReanalyzing(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <Sidebar
        analysisId={analysisId}
        analysis={analysis}
        onReanalyze={handleReanalyze}
        isReanalyzing={isReanalyzing}
      />
      <div className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">{children}</div>
    </div>
  );
}
