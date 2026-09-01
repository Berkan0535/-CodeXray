import os
import json
import re
from typing import List, Dict, Any, Set
from app.analyzers.file_scanner import ScannedFile


class ProjectDetector:
    """
    Detects framework, database, infrastructure, build tool, and ecosystem signals.
    """

    FRAMEWORK_PATTERNS = {
        # Python
        "FastAPI": [r"from fastapi import", r"import fastapi", r"fastapi>="],
        "Django": [r"from django", r"import django", r"django-admin", r"DJANGO_SETTINGS_MODULE"],
        "Flask": [r"from flask import", r"import flask", r"Flask\(__name__\)"],
        "Celery": [r"from celery import", r"import celery", r"celery = Celery\("],
        "SQLAlchemy": [r"from sqlalchemy", r"import sqlalchemy", r"create_engine\("],
        "PyTorch": [r"import torch", r"from torch import"],
        "TensorFlow": [r"import tensorflow", r"from tensorflow import"],
        
        # JavaScript / TypeScript
        "Next.js": [r"next/router", r"next/navigation", r"next/image", r"\"next\":"],
        "React": [r"from ['\"]react['\"]", r"import React", r"\"react\":"],
        "Vue.js": [r"from ['\"]vue['\"]", r"\"vue\":"],
        "Angular": [r"@angular/core", r"\"@angular/core\":"],
        "Express.js": [r"require\(['\"]express['\"]", r"from ['\"]express['\"]", r"\"express\":"],
        "NestJS": [r"@nestjs/core", r"@nestjs/common", r"\"@nestjs/core\":"],
        "Tailwind CSS": [r"tailwindcss", r"@tailwind", r"tailwind.config"],
        "Prisma": [r"@prisma/client", r"prisma.schema", r"\"prisma\":"],
        
        # Java
        "Spring Boot": [r"org\.springframework\.boot", r"@SpringBootApplication", r"spring-boot-starter"],
        "Hibernate": [r"org\.hibernate", r"@Entity", r"@Table"],
        "Quarkus": [r"io\.quarkus", r"@QuarkusMain"],
        
        # Go
        "Gin": [r"github\.com/gin-gonic/gin"],
        "Echo": [r"github\.com/labstack/echo"],
        "Fiber": [r"github\.com/gofiber/fiber"],
        "GORM": [r"gorm\.io/gorm"],
    }

    INFRA_INDICATORS = {
        "Docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
        "Kubernetes": ["k8s", "helm", "deployment.yaml", "service.yaml", "ingress.yaml"],
        "Terraform": [".tf", "main.tf", "variables.tf"],
        "GitHub Actions": [".github/workflows"],
        "GitLab CI": [".gitlab-ci.yml"],
        "Makefile": ["Makefile", "makefile"],
        "Alembic": ["alembic.ini", "alembic/env.py"],
    }

    DATABASE_INDICATORS = {
        "PostgreSQL": ["postgres", "postgresql", "psycopg2", "asyncpg", "pgvector"],
        "MySQL": ["mysql", "pymysql", "mysqlclient"],
        "SQLite": ["sqlite3", "sqlite", "aiosqlite"],
        "Redis": ["redis", "ioredis", "aioredis"],
        "MongoDB": ["mongodb", "mongoose", "pymongo", "motor"],
    }

    @classmethod
    def detect(cls, base_dir: str, scanned_files: List[ScannedFile]) -> Dict[str, Any]:
        detected_frameworks: Set[str] = set()
        detected_infra: Set[str] = set()
        detected_databases: Set[str] = set()
        build_tools: Set[str] = set()

        file_map = {f.relative_path.lower(): f for f in scanned_files}

        # 1. Manifest / Build Tool checks
        if "package.json" in file_map:
            build_tools.add("npm/yarn/pnpm")
        if "requirements.txt" in file_map or "pyproject.toml" in file_map or "setup.py" in file_map:
            build_tools.add("pip/poetry/uv")
        if "go.mod" in file_map:
            build_tools.add("go modules")
        if "pom.xml" in file_map or "build.gradle" in file_map or "build.gradle.kts" in file_map:
            build_tools.add("maven/gradle")
        if "cargo.toml" in file_map:
            build_tools.add("cargo")

        # 2. Infra checks
        for infra_name, patterns in cls.INFRA_INDICATORS.items():
            for p in patterns:
                if any(p.lower() in rel_path for rel_path in file_map):
                    detected_infra.add(infra_name)
                    break

        # 3. Content-based framework & database detection (sample first 100 text files)
        sample_files = [f for f in scanned_files if not f.is_binary][:100]
        
        for file in sample_files:
            try:
                with open(file.absolute_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(15000)  # Read up to 15KB per sample file
                    
                    # Check frameworks
                    for fw, regexes in cls.FRAMEWORK_PATTERNS.items():
                        if fw not in detected_frameworks:
                            for rx in regexes:
                                if re.search(rx, content):
                                    detected_frameworks.add(fw)
                                    break
                                    
                    # Check databases
                    for db, keywords in cls.DATABASE_INDICATORS.items():
                        if db not in detected_databases:
                            for kw in keywords:
                                if kw in content.lower():
                                    detected_databases.add(db)
                                    break
            except Exception:
                continue

        return {
            "frameworks": sorted(list(detected_frameworks)),
            "infrastructure": sorted(list(detected_infra)),
            "databases": sorted(list(detected_databases)),
            "build_tools": sorted(list(build_tools)),
        }
