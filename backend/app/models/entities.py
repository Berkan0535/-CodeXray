import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    url = Column(String(512), nullable=False, unique=True, index=True)
    name = Column(String(256), nullable=False)
    owner = Column(String(256), nullable=False)
    default_branch = Column(String(128), default="main")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_analyzed_at = Column(DateTime, nullable=True)

    analyses = relationship("Analysis", back_populates="repository", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String(32), default="queued", index=True)  # queued, running, completed, failed
    stage = Column(String(64), default="QUEUED")
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    commit_hash = Column(String(64), nullable=True)
    branch = Column(String(128), default="main")
    
    # Overview metrics
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    total_code_lines = Column(Integer, default=0)
    primary_language = Column(String(64), nullable=True)
    languages_breakdown = Column(JSON, default=dict)
    project_frameworks = Column(JSON, default=list)
    
    # Calculated Scores (0-100)
    overall_score = Column(Float, default=0.0)
    architecture_score = Column(Float, default=0.0)
    security_score = Column(Float, default=0.0)
    performance_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    maintainability_score = Column(Float, default=0.0)
    
    # Issue Counts
    critical_issues_count = Column(Integer, default=0)
    high_issues_count = Column(Integer, default=0)
    medium_issues_count = Column(Integer, default=0)
    low_issues_count = Column(Integer, default=0)
    info_issues_count = Column(Integer, default=0)
    
    # AI Review & Executive Summary
    ai_summary = Column(Text, nullable=True)
    ai_review_sections = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)

    # Relationships
    repository = relationship("Repository", back_populates="analyses")
    issues = relationship("AnalysisIssue", back_populates="analysis", cascade="all, delete-orphan")
    metrics = relationship("AnalysisMetric", back_populates="analysis", cascade="all, delete-orphan")
    dependencies = relationship("Dependency", back_populates="analysis", cascade="all, delete-orphan")
    architecture_nodes = relationship("ArchitectureNode", back_populates="analysis", cascade="all, delete-orphan")
    architecture_edges = relationship("ArchitectureEdge", back_populates="analysis", cascade="all, delete-orphan")
    code_chunks = relationship("CodeChunk", back_populates="analysis", cascade="all, delete-orphan")
    chat_messages = relationship("AIMessage", back_populates="analysis", cascade="all, delete-orphan")


class AnalysisIssue(Base):
    __tablename__ = "analysis_issues"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    severity = Column(String(16), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category = Column(String(32), nullable=False, index=True)  # SECURITY, PERFORMANCE, QUALITY, ARCHITECTURE, DEPENDENCY, MAINTAINABILITY
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String(512), nullable=False, index=True)
    line_number = Column(Integer, default=1)
    end_line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    tool = Column(String(64), default="analyzer")
    confidence = Column(String(16), default="HIGH")  # HIGH, MEDIUM, LOW

    analysis = relationship("Analysis", back_populates="issues")


class AnalysisMetric(Base):
    __tablename__ = "analysis_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(128), nullable=False, index=True)
    category = Column(String(64), nullable=False)
    value = Column(Float, nullable=False)
    details = Column(JSON, default=dict)

    analysis = relationship("Analysis", back_populates="metrics")


class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(256), nullable=False, index=True)
    version = Column(String(64), nullable=False)
    ecosystem = Column(String(64), nullable=False)  # npm, pypi, golang, maven, cargo
    manifest_file = Column(String(256), nullable=False)
    is_outdated = Column(Boolean, default=False)
    latest_version = Column(String(64), nullable=True)
    vulnerabilities_count = Column(Integer, default=0)
    vulnerabilities = Column(JSON, default=list)

    analysis = relationship("Analysis", back_populates="dependencies")


class ArchitectureNode(Base):
    __tablename__ = "architecture_nodes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    node_id = Column(String(256), nullable=False)
    name = Column(String(256), nullable=False)
    layer = Column(String(64), nullable=False)  # frontend, api, service, repository, database, infra, core, util
    node_type = Column(String(64), default="module")
    file_path = Column(String(512), nullable=True)
    lines_of_code = Column(Integer, default=0)
    dependencies_count = Column(Integer, default=0)

    analysis = relationship("Analysis", back_populates="architecture_nodes")


class ArchitectureEdge(Base):
    __tablename__ = "architecture_edges"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source_node_id = Column(String(256), nullable=False)
    target_node_id = Column(String(256), nullable=False)
    edge_type = Column(String(64), default="imports")
    weight = Column(Integer, default=1)

    analysis = relationship("Analysis", back_populates="architecture_edges")


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_path = Column(String(512), nullable=False, index=True)
    symbol_name = Column(String(256), nullable=True)
    chunk_type = Column(String(64), default="block")  # function, class, module, block
    start_line = Column(Integer, default=1)
    end_line = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    embedding_json = Column(JSON, nullable=True)

    analysis = relationship("Analysis", back_populates="code_chunks")


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(String(16), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations = Column(JSON, default=list)  # list of {file_path, line_number, symbol_name}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("Analysis", back_populates="chat_messages")
