import os
import re
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Set
from app.analyzers.file_scanner import ScannedFile
from app.analyzers.parser.ast_extractor import ParsedFileAST
from app.core.logging import logger


LAYER_RULES = [
    ("frontend", [r"/components/", r"/pages/", r"/app/", r"/views/", r"/static/", r"/assets/", r"/ui/", r"/templates/"]),
    ("api", [r"/api/", r"/controllers/", r"/routes/", r"/endpoints/", r"/handlers/", r"/graphql/", r"/routers/"]),
    ("service", [r"/services/", r"/usecases/", r"/domain/", r"/logic/", r"/managers/", r"/jobs/", r"/tasks/"]),
    ("repository", [r"/repositories/", r"/dao/", r"/data/", r"/models/", r"/schemas/", r"/entities/", r"/database/"]),
    ("database", [r"/migrations/", r"/alembic/", r"/prisma/", r"/sql/", r"/db/"]),
    ("infra", [r"/k8s/", r"/docker/", r"/terraform/", r"/\.github/", r"/deploy/", r"/infra/"]),
    ("core", [r"/core/", r"/config/", r"/common/", r"/utils/", r"/helpers/", r"/middleware/"]),
]


class ArchitectureAnalyzer:
    """
    Analyzes codebase modularity, classifies architectural layers (Frontend -> API -> Service -> Repository -> Database),
    constructs import dependency graph, detects circular dependencies, and computes coupling metrics.
    """

    @classmethod
    def analyze(
        cls,
        scanned_files: List[ScannedFile],
        parsed_asts: List[ParsedFileAST]
    ) -> Dict[str, Any]:
        nodes_dict: Dict[str, Dict[str, Any]] = {}
        edges_dict: Dict[Tuple[str, str], int] = defaultdict(int)
        file_to_node: Dict[str, str] = {}
        ast_map = {ast_item.file_path: ast_item for ast_item in parsed_asts}

        # 1. Classify layers and create Nodes
        for f in scanned_files:
            if f.is_binary:
                continue

            node_id = cls._get_module_id(f.relative_path)
            layer = cls._classify_layer(f.relative_path)
            file_to_node[f.relative_path] = node_id

            if node_id not in nodes_dict:
                nodes_dict[node_id] = {
                    "node_id": node_id,
                    "name": os.path.basename(node_id) or node_id,
                    "layer": layer,
                    "node_type": "module",
                    "file_path": f.relative_path,
                    "lines_of_code": f.code_lines,
                    "files_count": 1,
                    "dependencies_count": 0,
                }
            else:
                nodes_dict[node_id]["lines_of_code"] += f.code_lines
                nodes_dict[node_id]["files_count"] += 1

        # 2. Build Directed Edges from Imports
        for f in scanned_files:
            ast_item = ast_map.get(f.relative_path)
            if not ast_item:
                continue

            source_node = file_to_node.get(f.relative_path)
            if not source_node:
                continue

            for imp in ast_item.imports:
                target_node = cls._resolve_target_module(imp.module, file_to_node)
                if target_node and target_node != source_node:
                    edges_dict[(source_node, target_node)] += 1

        # Convert to lists
        nodes = list(nodes_dict.values())
        edges = [
            {
                "source_node_id": s,
                "target_node_id": t,
                "edge_type": "imports",
                "weight": w,
            }
            for (s, t), w in edges_dict.items()
        ]

        # Update node dependency counts
        for edge in edges:
            s_node = nodes_dict.get(edge["source_node_id"])
            if s_node:
                s_node["dependencies_count"] += 1

        # 3. Detect Circular Dependencies (Tarjan / DFS Cycle Detection)
        circular_deps = cls._find_cycles(nodes_dict.keys(), edges_dict.keys())

        # 4. Compute Afferent & Efferent Coupling
        coupling_metrics = cls._calculate_coupling(nodes_dict.keys(), edges_dict.keys())

        # 5. Architecture Issues (e.g. Circular Dependencies, Layer Violations)
        arch_issues: List[Dict[str, Any]] = []
        for cycle in circular_deps[:5]:
            cycle_str = " -> ".join(cycle)
            arch_issues.append({
                "severity": "HIGH",
                "category": "ARCHITECTURE",
                "title": f"Circular Dependency Detected: {cycle[0]}",
                "description": f"Detected circular dependency cycle: {cycle_str}",
                "file_path": cycle[0],
                "line_number": 1,
                "code_snippet": None,
                "impact": "Tight coupling, preventing modular testing, lazy-loading, and clean refactoring.",
                "recommendation": "Decouple modules using Dependency Inversion (interfaces/abstractions) or mediator patterns.",
                "suggested_fix": None,
                "tool": "architecture_analyzer",
                "confidence": "HIGH",
            })

        # 6. Calculate architecture health score
        cycle_penalty = min(40, len(circular_deps) * 15)
        layer_coverage = min(100, len(set(n["layer"] for n in nodes)) * 20)
        arch_score = max(30.0, min(100.0, 95.0 - cycle_penalty + (layer_coverage * 0.05)))

        return {
            "nodes": nodes,
            "edges": edges,
            "layers": ["frontend", "api", "service", "repository", "database", "infra", "core"],
            "circular_dependencies": circular_deps,
            "coupling_metrics": coupling_metrics,
            "architecture_score": round(arch_score, 1),
            "architecture_issues": arch_issues,
        }

    @classmethod
    def _classify_layer(cls, relative_path: str) -> str:
        path_lower = "/" + relative_path.replace("\\", "/").lower()
        for layer_name, patterns in LAYER_RULES:
            for pat in patterns:
                if pat in path_lower:
                    return layer_name
        return "core"

    @classmethod
    def _get_module_id(cls, relative_path: str) -> str:
        parts = relative_path.replace("\\", "/").split("/")
        if len(parts) > 2:
            return "/".join(parts[:2])
        elif len(parts) == 2:
            return parts[0]
        return "root"

    @classmethod
    def _resolve_target_module(cls, raw_module: str, file_to_node: Dict[str, str]) -> str | None:
        clean = raw_module.replace(".", "/").replace("\\", "/").strip("/ ")
        for rel_path, node_id in file_to_node.items():
            if clean in rel_path or os.path.splitext(rel_path)[0].endswith(clean):
                return node_id
        return None

    @classmethod
    def _find_cycles(cls, nodes: Set[str], edges: Set[Tuple[str, str]]) -> List[List[str]]:
        """DFS cycle detector for directed graphs."""
        adj = defaultdict(list)
        for s, t in edges:
            adj[s].append(t)

        visited = set()
        rec_stack = []
        cycles = []

        def dfs(node):
            visited.add(node)
            rec_stack.append(node)

            for neighbor in adj[node]:
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found cycle
                    idx = rec_stack.index(neighbor)
                    cycle = rec_stack[idx:] + [neighbor]
                    if cycle not in cycles and len(cycle) > 2:
                        cycles.append(cycle)

            rec_stack.pop()

        for n in list(nodes):
            if n not in visited:
                dfs(n)

        return cycles

    @classmethod
    def _calculate_coupling(cls, nodes: Set[str], edges: Set[Tuple[str, str]]) -> Dict[str, Any]:
        ca = defaultdict(int)  # Afferent coupling (incoming)
        ce = defaultdict(int)  # Efferent coupling (outgoing)

        for s, t in edges:
            ce[s] += 1
            ca[t] += 1

        metrics = {}
        for n in nodes:
            incoming = ca[n]
            outgoing = ce[n]
            total = incoming + outgoing
            instability = round(outgoing / total, 2) if total > 0 else 0.0
            metrics[n] = {
                "ca_afferent": incoming,
                "ce_efferent": outgoing,
                "instability": instability,
            }
        return metrics
