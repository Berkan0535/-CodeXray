# 🔍 CodeXray

<div align="center">

![CI Pipeline](https://img.shields.io/badge/CI-Passing-emerald?style=for-the-badge&logo=githubactions)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14.2-black?style=for-the-badge&logo=next.js&logoColor=white)
![Tree-sitter](https://img.shields.io/badge/Tree--sitter-AST-358a5b?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<p align="center">
  <strong>Production-grade Code Intelligence Platform for Architecture, Security, Performance & Code Quality Analysis with Semantic RAG Chat.</strong>
  <br />
  <em>Mimari, Güvenlik, Performans ve Kod Kalitesi Analizi ile Semantik RAG Sohbet Destekli Yeni Nesil Kod Tabanı Zeka Platformu.</em>
</p>

### 🌐 Dil Seçimi / Language Selection
[🇹🇷 **Türkçe Dokümantasyon**](#-türkçe-dokümantasyon) • [🇬🇧 **English Documentation**](#-english-documentation)

---

</div>

---

# 🇹🇷 Türkçe Dokümantasyon

## 🌟 Genel Bakış

**CodeXray**, açık veya özel herhangi bir Git deposunu derinlemesine inceleyen yeni nesil bir kod zekası ve statik analiz platformudur. Depoyu izole bir sandbox ortamına klonlar, **Tree-sitter AST** ile kod yapılarını ayrıştırır, yüksek entropili gizli anahtarları ve CVE açıklarını tarar, N+1 ve asenkron performans darboğazlarını yakalar, çok katmanlı mimari haritasını çıkarır ve doğal dille kod tabanına soru sorabilmeniz için **RAG (Retrieval-Augmented Generation)** vektör indekslemesi yapar.

---

## 🏗️ Sistem Mimarisi

```mermaid
flowchart TB
    Client["Next.js 14 Dashboard"] --> API["FastAPI Backend Motoru"]
    
    subgraph BackendCore ["Backend Çekirdeği"]
        API --> RepoMgr["Depo Yöneticisi / Sandbox"]
        API --> TaskQueue["Celery Worker Kuyruğu"]
        API --> AIService["Yapay Zeka Servis Soyutlaması"]
        API --> RAG["RAG Vektör Arama Motoru"]
    end

    subgraph AnalysisEngine ["Analiz Motoru"]
        TaskQueue --> Scanner["Dosya ve Yol Tarayıcı"]
        TaskQueue --> AST["Tree-sitter AST Ayrıştırıcı"]
        TaskQueue --> Security["Güvenlik ve Gizli Anahtar Tarayıcı"]
        TaskQueue --> Perf["Performans ve Gecikme Analizörü"]
        TaskQueue --> Quality["Sürdürülebilirlik ve Karmaşıklık"]
        TaskQueue --> Arch["Mimari Katman Sınıflandırıcı"]
        TaskQueue --> Scoring["Deterministik Skorlama"]
    end

    subgraph StorageDB ["Depolama ve Veritabanı"]
        API --> DB[("PostgreSQL + pgvector / SQLite")]
        TaskQueue --> Redis[("Redis Broker ve Önbellek")]
    end
```

---

## ⚡ 14 Aşamalı Analiz Boru Hattı

```mermaid
flowchart TD
    S1["1. URL Doğrulama ve SSRF Kontrolü"] --> S2["2. Sığ Git Klonlama"]
    S2 --> S3["3. Dosya Tarama ve Yol İzolasyonu"]
    S3 --> S4["4. Programlama Dili Tespiti"]
    S4 --> S5["5. Framework ve Altyapı Tespiti"]
    S5 --> S6["6. Tree-sitter AST Sembol Ayrıştırması"]
    S6 --> S7["7. Bağımlılık ve CVE Açık Taraması"]
    S7 --> S8["8. Gitleaks Düzeyinde Gizli Anahtar Taraması"]
    S8 --> S9["9. Performans ve N+1 Sorgu Tespiti"]
    S9 --> S10["10. Kod Kalitesi ve Sürdürülebilirlik İndeksi"]
    S10 --> S11["11. Mimari Katman ve Bağımlılık Grafiği"]
    S11 --> S12["12. Çok Faktörlü Deterministik Skorlama"]
    S12 --> S13["13. Modüler Yapay Zeka Kod İncelemesi"]
    S13 --> S14["14. Semantik RAG Kod Vektör İndekslemesi"]
```

---

## ✨ Temel Yetenekler

### 1. 🏛️ Mimari ve Katman Haritalama
- Dosyaları mantıksal mimari katmanlara ayırır: **Frontend, API, Servis, Repository, Veritabanı, Altyapı, Çekirdek (Core)**.
- Modüller arası yönlü import grafiği oluşturur.
- **Afferent ($C_a$)** & **Efferent ($C_e$)** bağımlılık ve kararsızlık (instability) metriklerini hesaplar.
- Döngüsel bağımlılıkları ($A \to B \to A$) tespit eder.

### 2. 🛡️ Derin Güvenlik ve Gizli Anahtar Tarayıcısı
- **Gitleaks Düzeyinde Gizli Anahtar Motoru**: AWS, GitHub PAT, JWT, OpenAI API anahtarları, Slack webhook'ları ve özel anahtarları **Shannon Entropi Analizi** ile yanlış pozitifleri önleyerek tespit eder.
- **AST Zafiyet Kuralları**: SQL Enjeksiyonu, Komut Çalıştırma (`shell=True`), Güvensiz Serileştirme (`pickle`/güvensiz `yaml`), SSRF ve Devre Dışı Bırakılmış SSL sertifikalarını (`verify=False`) yakalar.
- **Yapay Zeka ile Çözüm**: "Explain with AI" özelliğiyle zafiyetin kök nedenini açıklar ve refactor edilmiş kod önerir.

### 3. ⚡ Performans ve Verimlilik Teşhisi
- **N+1 Sorgu Tespiti**: Döngüler (`for`/`while`) içinde çalıştırılan veritabanı sorgularını tespit eder.
- **Asenkron Bloklanma Analizi**: `async` fonksiyonlar içinde çalışan senkron bloklayıcı I/O işlemlerini (`time.sleep`, senkron `requests`) bulur.
- **Algoritmik Karmaşıklık**: Aşırı iç içe döngüleri ($O(N^3)+$) ve ReDoS (düzenli ifade kilitlenmeleri) risklerini listeler.

### 4. 📊 Kod Kalitesi ve Sürdürülebilirlik İndeksi
- **Sürdürülebilirlik İndeksi (MI)**: Standart SEI / Radon formülleriyle hesaplanır.
- **Siklomatik Karmaşıklık (CC)**: Fonksiyon başına ortalama karmaşıklık, riskli odaklar ve aşırı büyük rutinler.
- **Kod Tekrarı (Duplication)**: Dosyalar arası token hashing ile kod kopyalarını belirler.

### 5. 📦 Çoklu Ekosistem Bağımlılık ve CVE Denetimi
- `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.toml` dosyalarını ayrıştırır.
- Sabitlenmemiş paket sürümlerini ve bilinen güvenlik açıklarını haritalar.

### 6. 🤖 "Kod Tabanına Sor" Semantik RAG Sohbeti
- Fonksiyon ve sınıf sınırlarını koruyan AST uyumlu sembol parçalama (chunking).
- Satır düzeyinde kod alıntıları ve kod önizlemeleri içeren vektör benzerlik araması.
- Prompt injection saldırılarına karşı güvenli sınır filtreleri (`<UNTRUSTED_CODE>`).

---

## 🚀 Hızlı Başlangıç

### Seçenek 1: Docker Compose (Önerilen Tam Yığın)

```bash
# Projeyi klonlayın
git clone https://github.com/Berkan0535/-CodeXray.git
cd -CodeXray

# Ortam değişkenlerini kopyalayın
cp .env.example .env

# Tüm servisleri ayağa kaldırın (Backend, Frontend, PostgreSQL+pgvector, Redis, Worker)
docker compose up --build
```

- **Frontend Arayüzü:** [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Seçenek 2: Yerel Geliştirme (Standalone Local)

#### 1. Backend Kurulumu:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Kurulumu:
```bash
cd frontend
npm install
npm run dev
```

Tarayıcınızdan [http://localhost:3000](http://localhost:3000) adresine gidin.

---

<br />

---

# 🇬🇧 English Documentation

## 🌟 Executive Overview

**CodeXray** is an advanced developer tool and code intelligence engine. It ingests any public or private Git repository, clones it into an isolated sandbox, parses code structures with **Tree-sitter AST**, scans for secrets & CVEs, traces performance bottlenecks, maps multi-tier architectural layers, and indexes code into a vector store for natural language semantic Q&A with line-level code citations.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    Client["Next.js 14 Dashboard"] --> API["FastAPI Backend Engine"]
    
    subgraph BackendCore ["Backend Core"]
        API --> RepoMgr["Repository Manager / Sandbox"]
        API --> TaskQueue["Celery Worker Queue"]
        API --> AIService["AI Provider Service"]
        API --> RAG["RAG Vector Retriever"]
    end

    subgraph AnalysisEngine ["Analysis Engine"]
        TaskQueue --> Scanner["File & Path Scanner"]
        TaskQueue --> AST["Tree-sitter AST Parser"]
        TaskQueue --> Security["Security & Secret Scanner"]
        TaskQueue --> Perf["Performance & Latency Analyzer"]
        TaskQueue --> Quality["Maintainability & Complexity Analyzer"]
        TaskQueue --> Arch["Architecture Layer Classifier"]
        TaskQueue --> Scoring["Deterministic Scoring Service"]
    end

    subgraph StorageDB ["Storage & Vector Database"]
        API --> DB[("PostgreSQL + pgvector / SQLite")]
        TaskQueue --> Redis[("Redis Broker & Cache")]
    end
```

---

## ⚡ 14-Stage Analysis Pipeline

```mermaid
flowchart TD
    S1["1. Validate URL & SSRF Check"] --> S2["2. Shallow Git Clone"]
    S2 --> S3["3. File Scanner & Path Normalization"]
    S3 --> S4["4. Language Classification"]
    S4 --> S5["5. Project & Framework Detection"]
    S5 --> S6["6. Tree-sitter AST Symbol Parsing"]
    S6 --> S7["7. Dependency & Known CVE Analysis"]
    S7 --> S8["8. Gitleaks Secrets & AST Security Scan"]
    S8 --> S9["9. Performance & N+1 Query Detection"]
    S9 --> S10["10. Code Quality & Maintainability Index"]
    S10 --> S11["11. Architecture Layer & Graph Building"]
    S11 --> S12["12. Deterministic Multi-Factor Scoring"]
    S12 --> S13["13. Modular Section AI Review"]
    S13 --> S14["14. Semantic RAG Code Chunk Indexing"]
```

---

## ✨ Key Capabilities

### 1. 🏛️ Architecture & Modularity Mapping
- Classifies codebase files into logical architectural tiers: **Frontend, API, Service, Repository, Database, Infrastructure, Core**.
- Constructs a directed module import graph.
- Calculates **Afferent ($C_a$)** & **Efferent ($C_e$)** Coupling and Instability indices.
- Discovers **Circular Dependencies** ($A \to B \to A$) using cycle-detection algorithms.

### 2. 🛡️ Deep Security & Secret Scanner
- **Gitleaks-Grade Secret Engine**: Scans for AWS keys, GitHub PATs, JWT tokens, OpenAI keys, Slack webhooks, and private keys with **Shannon Entropy analysis** to prevent false alarms.
- **AST Vulnerability Rules**: Detects SQL Injection, Command Injection (`shell=True`), Insecure Deserialization (`pickle`/unsafe `yaml`), SSRF vulnerabilities, and Disabled SSL certificates (`verify=False`).
- **Interactive Remediation**: "Explain with AI" breaks down threat vectors and suggests refactored code snippets.

### 3. ⚡ Performance & Efficiency Diagnostics
- **N+1 Query Detection**: Flags database queries executed inside iterative `for`/`while` loops.
- **Async Event-Loop Blocking**: Identifies blocking synchronous I/O (`time.sleep`, synchronous `requests`) inside async coroutines.
- **Algorithm Complexity**: Identifies deeply nested loops ($O(N^3)+$) and catastrophic regular expression backtracking risks (ReDoS).

### 4. 📊 Code Quality, Maintainability & Technical Debt
- **Maintainability Index (MI)**: Computed via standard SEI / Radon formulas.
- **Cyclomatic Complexity (CC)**: Average complexity per routine, max complexity hotspots, and oversized function warnings.
- **Code Duplication**: Line-block token hashing across files.

### 5. 📦 Multi-Ecosystem Dependency & CVE Checker
- Parses `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.toml`.
- Flags unpinned dependencies and maps known security advisories.

### 6. 🤖 "Ask Your Codebase" Semantic RAG Chat
- AST-aware symbol chunking preserving function/class boundaries.
- Fast vector similarity search with line-level code citations and snippet previews.
- Prompt injection defense boundaries (`<UNTRUSTED_CODE>` delimiters).

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/repositories/analyze` | Initiates asynchronous 14-stage codebase analysis |
| `GET` | `/api/v1/repositories` | Lists analyzed repositories with scores & summaries |
| `GET` | `/api/v1/repositories/{id}/analyses` | Lists all historical analysis runs for a repository |
| `GET` | `/api/v1/analyses/{id}` | Retrieves full analysis results, scores, and summaries |
| `GET` | `/api/v1/analyses/{id}/status` | Real-time stage and progress polling endpoint |
| `GET` | `/api/v1/analyses/{id}/events` | Server-Sent Events (SSE) progress stream |
| `GET` | `/api/v1/analyses/{id}/issues` | Lists filtered issues (CRITICAL, HIGH, MEDIUM, LOW) |
| `POST` | `/api/v1/analyses/{id}/issues/{issue_id}/explain` | AI explanation and suggested code refactor diff |
| `GET` | `/api/v1/analyses/{id}/architecture` | Module nodes, layers, and dependency edges graph |
| `GET` | `/api/v1/analyses/{id}/dependencies` | Tracked dependencies and known CVE alerts |
| `POST` | `/api/v1/analyses/{id}/chat` | RAG 'Ask Your Codebase' question answering |
| `GET` | `/api/v1/analyses/{id}/report` | Exports full report (JSON or Markdown format) |

---

## 🔒 Security & Sandboxing

1. **SSRF Defense**: Strict URL validation blocking loopback (`127.0.0.1`, `localhost`), link-local, internal cloud metadata IP (`169.254.169.254`), and non-standard protocols (`file://`).
2. **Path Traversal Protection**: All filesystem accesses resolve relative to isolated cache boundaries.
3. **Resource Limits**: Strict limits on max repo size (150MB), max file size (1.5MB), max analyzed files (3000), and execution timeouts (300s).
4. **Prompt Injection Boundary Sanitization**: Untrusted repository source code and comments are enclosed in explicit safety delimiters so LLMs never treat code comments as instructions.

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v
```

All 18 test suites test security filters, AST multi-language parsers, analyzers, deterministic scoring formulas, RAG vector retrieval, and REST API flows.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

