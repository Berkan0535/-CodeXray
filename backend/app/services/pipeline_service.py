import asyncio
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.models.entities import (
    Repository,
    Analysis,
    AnalysisIssue,
    AnalysisMetric,
    Dependency,
    ArchitectureNode,
    ArchitectureEdge,
    CodeChunk,
)
from app.services.repo_manager import RepoManager
from app.analyzers.file_scanner import FileScanner
from app.analyzers.language_detector import LanguageDetector
from app.analyzers.project_detector import ProjectDetector
from app.analyzers.parser.ast_extractor import TreeSitterParserEngine
from app.analyzers.security.security_scanner import SecurityScanner
from app.analyzers.performance.performance_analyzer import PerformanceAnalyzer
from app.analyzers.quality.quality_analyzer import QualityAnalyzer
from app.analyzers.dependencies.dependency_analyzer import DependencyAnalyzer
from app.analyzers.architecture.architecture_analyzer import ArchitectureAnalyzer
from app.services.scoring_service import ScoringService
from app.ai.reviewer import AIReviewer
from app.ai.factory import AIProviderFactory
from app.rag.chunker import CodeChunker
from app.rag.vector_store import vector_store


class PipelineService:
    """
    Main orchestration engine executing the 14-stage automated analysis pipeline.
    """

    @classmethod
    async def run_pipeline(cls, analysis_id: str, provider_type: Optional[str] = None) -> None:
        start_time = time.time()
        logger.info(f"Starting analysis pipeline for analysis_id: {analysis_id}")

        async with AsyncSessionLocal() as session:
            # 1. Fetch Analysis and Repo
            stmt = select(Analysis).where(Analysis.id == analysis_id)
            res = await session.execute(stmt)
            analysis = res.scalar_one_or_none()
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found.")
                return

            repo_stmt = select(Repository).where(Repository.id == analysis.repository_id)
            repo_res = await session.execute(repo_stmt)
            repo = repo_res.scalar_one_or_none()
            if not repo:
                logger.error(f"Repository {analysis.repository_id} not found.")
                return

            try:
                # Stage 1: CLONING (10%)
                await cls._update_stage(session, analysis, "CLONING", 10, "running")
                clone_res = RepoManager.clone_or_fetch(
                    url=repo.url,
                    repository_id=repo.id,
                    branch=analysis.branch
                )
                target_dir = clone_res["target_dir"]
                analysis.commit_hash = clone_res["commit_hash"]
                analysis.branch = clone_res["branch"]
                await session.commit()

                # Stage 2: FILE_SCANNING (25%)
                await cls._update_stage(session, analysis, "FILE_SCANNING", 25)
                scanned_files = FileScanner.scan_directory(target_dir)
                analysis.total_files = len(scanned_files)
                total_loc = sum(f.total_lines for f in scanned_files if not f.is_binary)
                total_code = sum(f.code_lines for f in scanned_files if not f.is_binary)
                analysis.total_lines = total_loc
                analysis.total_code_lines = total_code

                # Stage 3: LANGUAGE_DETECTION (35%)
                await cls._update_stage(session, analysis, "LANGUAGE_DETECTION", 35)
                lang_res = LanguageDetector.detect_languages(scanned_files)
                analysis.primary_language = lang_res["primary_language"]
                analysis.languages_breakdown = lang_res["languages"]

                # Stage 4: PROJECT_DETECTION (45%)
                await cls._update_stage(session, analysis, "PROJECT_DETECTION", 45)
                proj_res = ProjectDetector.detect(target_dir, scanned_files)
                analysis.project_frameworks = proj_res["frameworks"]

                # Stage 5: CODE_PARSING (55%)
                await cls._update_stage(session, analysis, "CODE_PARSING", 55)
                parser_engine = TreeSitterParserEngine()
                parsed_asts = []
                for sf in scanned_files:
                    if sf.is_binary or sf.code_lines == 0:
                        continue
                    try:
                        with open(sf.absolute_path, "r", encoding="utf-8", errors="ignore") as f:
                            code_str = f.read()
                        ast_res = parser_engine.parse_file(sf.relative_path, code_str, sf.extension.lstrip("."))
                        parsed_asts.append(ast_res)
                    except Exception:
                        pass

                # Stage 6: DEPENDENCY_ANALYSIS (65%)
                await cls._update_stage(session, analysis, "DEPENDENCY_ANALYSIS", 65)
                deps_list, dep_issues = DependencyAnalyzer.analyze(target_dir, scanned_files)
                for dep in deps_list:
                    session.add(
                        Dependency(
                            analysis_id=analysis.id,
                            name=dep["name"],
                            version=dep["version"],
                            ecosystem=dep["ecosystem"],
                            manifest_file=dep["manifest_file"],
                            is_outdated=dep["is_outdated"],
                            latest_version=dep["latest_version"],
                            vulnerabilities_count=dep["vulnerabilities_count"],
                            vulnerabilities=dep["vulnerabilities"],
                        )
                    )

                # Stage 7: SECURITY_SCAN (75%)
                await cls._update_stage(session, analysis, "SECURITY_SCAN", 75)
                sec_issues = SecurityScanner.scan_codebase(target_dir, scanned_files)
                # Combine security and dependency security issues
                all_sec_issues = sec_issues + dep_issues

                # Stage 8: PERFORMANCE_ANALYSIS (82%)
                await cls._update_stage(session, analysis, "PERFORMANCE_ANALYSIS", 82)
                perf_issues = PerformanceAnalyzer.analyze_codebase(target_dir, scanned_files)

                # Stage 9: QUALITY_ANALYSIS (88%)
                await cls._update_stage(session, analysis, "QUALITY_ANALYSIS", 88)
                qual_res = QualityAnalyzer.analyze(scanned_files, parsed_asts)
                qual_issues = qual_res.get("quality_issues", [])

                # Stage 10: ARCHITECTURE_ANALYSIS (92%)
                await cls._update_stage(session, analysis, "ARCHITECTURE_ANALYSIS", 92)
                arch_res = ArchitectureAnalyzer.analyze(scanned_files, parsed_asts)
                arch_issues = arch_res.get("architecture_issues", [])

                # Save architecture nodes and edges
                for n in arch_res.get("nodes", []):
                    session.add(
                        ArchitectureNode(
                            analysis_id=analysis.id,
                            node_id=n["node_id"],
                            name=n["name"],
                            layer=n["layer"],
                            node_type=n.get("node_type", "module"),
                            file_path=n.get("file_path"),
                            lines_of_code=n.get("lines_of_code", 0),
                            dependencies_count=n.get("dependencies_count", 0),
                        )
                    )
                for e in arch_res.get("edges", []):
                    session.add(
                        ArchitectureEdge(
                            analysis_id=analysis.id,
                            source_node_id=e["source_node_id"],
                            target_node_id=e["target_node_id"],
                            edge_type=e.get("edge_type", "imports"),
                            weight=e.get("weight", 1),
                        )
                    )

                # Save all collected issues
                all_issues = all_sec_issues + perf_issues + qual_issues + arch_issues
                for iss in all_issues:
                    session.add(
                        AnalysisIssue(
                            analysis_id=analysis.id,
                            severity=iss.get("severity", "MEDIUM"),
                            category=iss.get("category", "QUALITY"),
                            title=iss.get("title", "Issue"),
                            description=iss.get("description", ""),
                            file_path=iss.get("file_path", "unknown"),
                            line_number=iss.get("line_number", 1),
                            end_line_number=iss.get("end_line_number"),
                            code_snippet=iss.get("code_snippet"),
                            impact=iss.get("impact"),
                            recommendation=iss.get("recommendation"),
                            suggested_fix=iss.get("suggested_fix"),
                            tool=iss.get("tool", "analyzer"),
                            confidence=iss.get("confidence", "HIGH"),
                        )
                    )

                # Count issues by severity
                analysis.critical_issues_count = sum(1 for i in all_issues if i.get("severity") == "CRITICAL")
                analysis.high_issues_count = sum(1 for i in all_issues if i.get("severity") == "HIGH")
                analysis.medium_issues_count = sum(1 for i in all_issues if i.get("severity") == "MEDIUM")
                analysis.low_issues_count = sum(1 for i in all_issues if i.get("severity") == "LOW")
                analysis.info_issues_count = sum(1 for i in all_issues if i.get("severity") == "INFO")

                # Stage 11: SCORING (95%)
                await cls._update_stage(session, analysis, "SCORING", 95)
                scores = ScoringService.calculate_scores(
                    issues=all_issues,
                    arch_result=arch_res,
                    quality_result=qual_res,
                    perf_issues=perf_issues,
                    sec_issues=all_sec_issues,
                )
                analysis.overall_score = scores["overall_score"]
                analysis.architecture_score = scores["architecture_score"]
                analysis.security_score = scores["security_score"]
                analysis.performance_score = scores["performance_score"]
                analysis.quality_score = scores["quality_score"]
                analysis.maintainability_score = scores["maintainability_score"]

                # Stage 12: AI_REVIEW (97%)
                await cls._update_stage(session, analysis, "AI_REVIEW", 97)
                ai_ctx = {
                    "repo_name": repo.name,
                    "primary_language": analysis.primary_language,
                    "frameworks": analysis.project_frameworks,
                    "databases": proj_res.get("databases", []),
                    "total_files": analysis.total_files,
                    "total_code_lines": analysis.total_code_lines,
                    "layers": arch_res.get("layers", []),
                    "circular_dependencies": arch_res.get("circular_dependencies", []),
                    "security_issues": all_sec_issues,
                    "performance_issues": perf_issues,
                    "quality_metrics": qual_res,
                }
                ai_review = await AIReviewer.generate_codebase_review(ai_ctx, provider_type, language="tr")
                analysis.ai_summary = ai_review.get("ai_summary")
                analysis.ai_review_sections = ai_review.get("sections", {})

                # Stage 13: RAG_INDEXING (99%)
                await cls._update_stage(session, analysis, "RAG_INDEXING", 99)
                raw_chunks = CodeChunker.chunk_repository(target_dir, scanned_files, parsed_asts)
                ai_provider = AIProviderFactory.get_provider(provider_type)
                
                # Batch generate embeddings for sample chunks
                sample_chunks = raw_chunks[:150]
                texts_to_embed = [c.content for c in sample_chunks]
                embeddings = await ai_provider.generate_embeddings(texts_to_embed)

                indexed_chunk_dicts = []
                for chunk_item, emb in zip(sample_chunks, embeddings):
                    chunk_dict = chunk_item.to_dict()
                    chunk_dict["embedding"] = emb
                    indexed_chunk_dicts.append(chunk_dict)

                    session.add(
                        CodeChunk(
                            analysis_id=analysis.id,
                            file_path=chunk_item.file_path,
                            symbol_name=chunk_item.symbol_name,
                            chunk_type=chunk_item.chunk_type,
                            start_line=chunk_item.start_line,
                            end_line=chunk_item.end_line,
                            content=chunk_item.content,
                            embedding_json=emb,
                        )
                    )

                vector_store.index_chunks(analysis.id, indexed_chunk_dicts)

                # Stage 14: DONE (100%)
                analysis.status = "completed"
                analysis.stage = "DONE"
                analysis.progress_percent = 100
                analysis.completed_at = datetime.now(timezone.utc)
                analysis.duration_seconds = round(time.time() - start_time, 2)
                
                repo.last_analyzed_at = datetime.now(timezone.utc)

                await session.commit()
                logger.info(f"Analysis {analysis_id} completed successfully in {analysis.duration_seconds}s!")

            except Exception as e:
                logger.exception(f"Pipeline error in analysis {analysis_id}: {e}")
                analysis.status = "failed"
                analysis.stage = "ERROR"
                analysis.error_message = str(e)
                analysis.completed_at = datetime.now(timezone.utc)
                analysis.duration_seconds = round(time.time() - start_time, 2)
                await session.commit()

    @classmethod
    async def _update_stage(
        cls,
        session: AsyncSession,
        analysis: Analysis,
        stage: str,
        progress: int,
        status: Optional[str] = None
    ) -> None:
        analysis.stage = stage
        analysis.progress_percent = progress
        if status:
            analysis.status = status
        await session.commit()
        logger.info(f"Analysis [{analysis.id}] Stage: {stage} ({progress}%)")
