from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RepositoryBase(BaseModel):
    url: str = Field(..., description="Git repository URL (HTTPS or SSH)")
    default_branch: Optional[str] = Field("main", description="Target branch to analyze")


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    name: str
    owner: str
    default_branch: str
    created_at: datetime
    updated_at: datetime
    last_analyzed_at: Optional[datetime] = None
    latest_analysis_id: Optional[str] = None
    latest_status: Optional[str] = None
    overall_score: Optional[float] = None
    critical_issues_count: Optional[int] = None
    high_issues_count: Optional[int] = None
    primary_language: Optional[str] = None
    total_files: Optional[int] = None
    total_lines: Optional[int] = None
    total_code_lines: Optional[int] = None
    analyses_count: Optional[int] = 0


class AnalysisCreate(BaseModel):
    repository_url: str = Field(..., description="GitHub repository URL")
    branch: Optional[str] = Field(None, description="Branch to analyze (defaults to repo default)")


class AnalysisStatusResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    stage: str
    progress_percent: int
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    analysis_id: str
    severity: str
    category: str
    title: str
    description: str
    file_path: str
    line_number: int
    end_line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    impact: Optional[str] = None
    recommendation: Optional[str] = None
    suggested_fix: Optional[str] = None
    tool: str
    confidence: str


class IssueExplainRequest(BaseModel):
    question: Optional[str] = "Can you explain why this issue is problematic and how to properly refactor it?"


class IssueExplainResponse(BaseModel):
    issue_id: str
    explanation: str
    detailed_impact: str
    suggested_code: Optional[str] = None
    confidence_note: str


class MetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    value: float
    details: Dict[str, Any] = {}


class DependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: str
    ecosystem: str
    manifest_file: str
    is_outdated: bool
    latest_version: Optional[str] = None
    vulnerabilities_count: int
    vulnerabilities: List[Dict[str, Any]] = []


class ArchitectureNodeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    node_id: str
    name: str
    layer: str
    node_type: str
    file_path: Optional[str] = None
    lines_of_code: int = 0
    dependencies_count: int = 0


class ArchitectureEdgeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_node_id: str
    target_node_id: str
    edge_type: str
    weight: int = 1


class ArchitectureGraphResponse(BaseModel):
    nodes: List[ArchitectureNodeSchema]
    edges: List[ArchitectureEdgeSchema]
    layers: List[str]
    circular_dependencies: List[List[str]] = []
    coupling_metrics: Dict[str, Any] = {}


class CitationSchema(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    symbol_name: Optional[str] = None
    snippet: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="Question regarding the analyzed codebase")


class ChatResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: List[CitationSchema] = []
    created_at: datetime


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    status: str
    stage: str
    progress_percent: int
    error_message: Optional[str] = None
    commit_hash: Optional[str] = None
    branch: str
    total_files: int
    total_lines: int
    total_code_lines: int
    primary_language: Optional[str] = None
    languages_breakdown: Dict[str, Any] = {}
    project_frameworks: List[str] = []
    
    # Scores
    overall_score: float
    architecture_score: float
    security_score: float
    performance_score: float
    quality_score: float
    maintainability_score: float
    
    # Issue Counts
    critical_issues_count: int
    high_issues_count: int
    medium_issues_count: int
    low_issues_count: int
    info_issues_count: int
    
    # Summaries
    ai_summary: Optional[str] = None
    ai_review_sections: Dict[str, Any] = {}
    
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float
    
    repository: Optional[RepositoryResponse] = None


class ReportResponse(BaseModel):
    analysis: AnalysisResponse
    issues_summary: Dict[str, int]
    top_issues: List[IssueResponse]
    metrics: List[MetricResponse]
    dependencies: List[DependencyResponse]
    architecture_summary: Dict[str, Any]
    markdown_report: str
