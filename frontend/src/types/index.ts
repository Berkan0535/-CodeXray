export interface Repository {
  id: string;
  url: string;
  name: string;
  owner: string;
  default_branch: string;
  created_at: string;
  updated_at: string;
  last_analyzed_at?: string;
  latest_analysis_id?: string;
  latest_status?: "queued" | "running" | "completed" | "failed" | string;
  overall_score?: number;
  critical_issues_count?: number;
  high_issues_count?: number;
  primary_language?: string;
  total_files?: number;
  total_lines?: number;
  total_code_lines?: number;
  analyses_count?: number;
}

export interface Analysis {
  id: string;
  repository_id: string;
  status: "queued" | "running" | "completed" | "failed";
  stage: string;
  progress_percent: number;
  error_message?: string;
  commit_hash?: string;
  branch: string;
  total_files: number;
  total_lines: number;
  total_code_lines: number;
  primary_language?: string;
  languages_breakdown: Record<string, { files: number; lines: number; code_lines: number; percentage: number }>;
  project_frameworks: string[];
  
  // Scores (0 - 100)
  overall_score: number;
  architecture_score: number;
  security_score: number;
  performance_score: number;
  quality_score: number;
  maintainability_score: number;
  
  // Issue Counts
  critical_issues_count: number;
  high_issues_count: number;
  medium_issues_count: number;
  low_issues_count: number;
  info_issues_count: number;
  
  ai_summary?: string;
  ai_review_sections?: {
    architecture?: string;
    security?: string;
    performance?: string;
    quality?: string;
  };
  
  created_at: string;
  completed_at?: string;
  duration_seconds: number;
  repository?: Repository;
}

export interface AnalysisStatus {
  id: string;
  repository_id: string;
  status: "queued" | "running" | "completed" | "failed";
  stage: string;
  progress_percent: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  duration_seconds: number;
}

export interface Issue {
  id: string;
  analysis_id: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  category: "SECURITY" | "PERFORMANCE" | "QUALITY" | "ARCHITECTURE" | "DEPENDENCY" | "MAINTAINABILITY";
  title: string;
  description: string;
  file_path: string;
  line_number: number;
  end_line_number?: number;
  code_snippet?: string;
  impact?: string;
  recommendation?: string;
  suggested_fix?: string;
  tool: string;
  confidence: string;
}

export interface IssueExplainResult {
  issue_id: string;
  explanation: string;
  detailed_impact: string;
  suggested_code?: string;
  confidence_note: string;
}

export interface Dependency {
  id: string;
  name: string;
  version: string;
  ecosystem: string;
  manifest_file: string;
  is_outdated: boolean;
  latest_version?: string;
  vulnerabilities_count: number;
  vulnerabilities: Array<{
    vulnerable_below: string;
    cve: string;
    severity: string;
    desc: string;
  }>;
}

export interface ArchitectureNode {
  id: string;
  node_id: string;
  name: string;
  layer: "frontend" | "api" | "service" | "repository" | "database" | "infra" | "core" | string;
  node_type: string;
  file_path?: string;
  lines_of_code: number;
  dependencies_count: number;
}

export interface ArchitectureEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  edge_type: string;
  weight: number;
}

export interface ArchitectureGraph {
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
  layers: string[];
  circular_dependencies: string[][];
  coupling_metrics: Record<string, { ca_afferent: number; ce_efferent: number; instability: number }>;
}

export interface Citation {
  file_path: string;
  line_number?: number;
  symbol_name?: string;
  snippet?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ReportData {
  analysis: Analysis;
  issues_summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  top_issues: Issue[];
  dependencies: Dependency[];
  markdown_report: string;
}
