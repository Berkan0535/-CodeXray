import hashlib
import json
import math
import re
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel
from app.ai.base import AIProvider
from app.core.config import settings


class MockProvider(AIProvider):
    """
    Intelligent local AI provider that generates context-aware,
    realistic code reviews, structured evaluations, and semantic vectors.
    """

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        prompt_lower = prompt.lower()
        is_tr = "türkçe" in prompt_lower or "turkish" in prompt_lower or "lütfen" in prompt_lower or "neden" in prompt_lower or "soru" in prompt_lower

        # Chat question answering
        if "developer question:" in prompt_lower or "ask your codebase" in prompt_lower or "soru" in prompt_lower:
            return self._generate_chat_answer(prompt, is_tr=is_tr)

        # Issue explanation
        if "expert ai pair programmer" in prompt_lower or "explain clearly" in prompt_lower or "neden problemli" in prompt_lower:
            if is_tr:
                return (
                    "### 🔍 Yapay Zeka Kök Neden ve Çözüm Analizi\n\n"
                    "**1. Problemin Kök Nedeni:**\n"
                    "Bu kod bloğu, girdi parametrelerinin güvenli şekilde doğrulanmadan veya parametrelendirilmeden kullanılmasına "
                    "ya da bloklayan/verimsiz operasyonların yürütülmesine neden olmaktadır.\n\n"
                    "**2. Gerçek Dünya Etkisi:**\n"
                    "Üretim ortamında güvenlik zafiyetlerine (yetkisiz veri erişimi, enjeksiyon), performans darboğazlarına veya kaynak tükenmesine yol açabilir.\n\n"
                    "**3. Önerilen Çözüm ve İyileştirme:**\n"
                    "- Girdileri parametreli yapılarla bağlayın veya modern async fonksiyonları tercih edin.\n"
                    "- Hata yakalama ve doğrulama sınırlarını güçlendirin."
                )
            return (
                "### 🔍 AI Root Cause & Fix Analysis\n\n"
                "**1. Root Cause:**\n"
                "The code either interpolates unvalidated input dynamically or uses blocking operations in high-throughput routines.\n\n"
                "**2. Real-World Impact:**\n"
                "Can lead to security vulnerabilities, event-loop starvation, or database latency degradation.\n\n"
                "**3. Recommended Remediation:**\n"
                "- Enforce parameterized bindings or native async APIs.\n"
                "- Add boundary validation and structured error handling."
            )

        # Architecture review
        if "architectural code review" in prompt_lower or "architecture" in prompt_lower:
            if is_tr:
                return (
                    "### 🏛️ Mimari Değerlendirme ve Katman Yapısı\n\n"
                    "**1. Katmanlama ve Sorumlulukların Ayrımı (Separation of Concerns):**\n"
                    "Kod tabanı; API rotaları, iş mantığı servisleri ve veri modelleri arasında net sınırlara sahip standart katmanlı bir mimari sergilemektedir. "
                    "Katmanlar arası gevşek bağlılık (loose coupling), sistemin bakımını ve genişletilebilirliğini kolaylaştırmaktadır.\n\n"
                    "**2. Tasarım Kalıpları ve Modülerlik:**\n"
                    "Servis katmanında Bağımlılık Enjeksiyonu (Dependency Injection) prensipleri benimsenmiştir. Veri erişim mantığı merkezi modeller ve repolarda "
                    "toplanarak birim test yazımı ve olası veritabanı geçişleri pratik hale getirilmiştir.\n\n"
                    "**3. Ölçeklenebilirlik ve Temel Tavsiyeler:**\n"
                    "- Sık okunan veritabanı sorguları için merkezi bir Redis önbellekleme (caching) katmanı devreye alınmalıdır.\n"
                    "- Ağır analiz veya I/O gerektiren işlemler, senkron HTTP rotalarından tamamen ayrılarak asenkron arka plan kuyruklarına devredilmelidir.\n"
                    "- Harici istemcilerle entegrasyonu güvenceye almak için API sürümleme (API versioning) standartları titizlikle uygulanmalıdır."
                )
            return (
                "### Architectural Assessment\n\n"
                "**1. Layering & Separation of Concerns:**\n"
                "The repository displays a standard layered architecture with clear boundaries between API handlers, "
                "business services, and data models. Clean contracts reduce coupling across layers.\n\n"
                "**2. Design Patterns & Modularity:**\n"
                "Services follow Dependency Injection principles. Data access is centralized into models/repositories, "
                "which simplifies testing and future database migrations.\n\n"
                "**3. Scalability & Recommendations:**\n"
                "- Introduce centralized Redis caching for frequently accessed read queries.\n"
                "- Ensure background task queues (Celery/workers) are decoupled from synchronous HTTP routes.\n"
                "- Enforce API schema versioning for external clients."
            )

        # Security review
        if "application security engineer" in prompt_lower or "security" in prompt_lower:
            if is_tr:
                return (
                    "### 🛡️ Güvenlik İncelemesi ve Sıkılaştırma Stratejisi\n\n"
                    "**1. Tehdit Modellemesi ve Saldırı Yüzeyi:**\n"
                    "Uygulamanın başlıca saldırı yüzeyleri; kullanıcıdan alınan parametrelerle oluşturulan veritabanı sorguları, dosya sistemi yolları ve dışa açık REST uç noktalarıdır.\n\n"
                    "**2. Öncelikli İyileştirme Planı:**\n"
                    "- **SQL ve Komut Güvenliği:** Dinamik dize birleştirmeleri ve f-string sorgu ifadeleri yerine kesinlikle parametreli sorgular (parameterized queries) veya ORM parametre bağlama kullanılmalıdır.\n"
                    "- **Kimlik Bilgisi ve Gizli Anahtar Yönetimi:** Kod deposunda bulunan tüm test token'ları ve anahtarlar iptal edilmeli, hassas kimlik bilgileri yalnızca güvenli Çevre Değişkenleri (.env) üzerinden yüklenmelidir.\n"
                    "- **İletişim Güvenliği (TLS/SSL):** Dış servislere yapılan tüm HTTP/HTTPS isteklerinde SSL sertifika doğrulaması (verify=True) zorunlu tutulmalıdır."
                )
            return (
                "### Security Review & Hardening Strategy\n\n"
                "**1. Threat Modeling Overview:**\n"
                "Primary attack surfaces include user-supplied parameters to database queries, file system paths, and API endpoints.\n\n"
                "**2. Remediation Priorities:**\n"
                "- **SQL & Command Safety:** Enforce parameterized queries and eliminate raw string interpolations.\n"
                "- **Credential Management:** Rotate any committed test tokens and load credentials strictly via Environment Variables.\n"
                "- **Transport Security:** Ensure TLS/SSL validation is strictly enforced on all outbound HTTP calls."
            )

        # Performance review
        if "performance engineer" in prompt_lower or "performance" in prompt_lower:
            if is_tr:
                return (
                    "### ⚡ Performans Analizi ve Darboğaz İyileştirme\n\n"
                    "**1. Tespit Edilen Kritik Darboğazlar:**\n"
                    "- Döngü iterasyonları içerisinde yinelenen veritabanı sorgu çağrıları (N+1 Sorgu Problemi).\n"
                    "- `async` tanımlanmış coroutine'ler içerisinde event-loop'u bloke eden senkron I/O işlemleri (`time.sleep`, senkron `requests`).\n\n"
                    "**2. Önerilen Optimizasyon Stratejileri:**\n"
                    "- Veritabanı sorgularını `WHERE IN (...)` kalıbıyla toplu (batch) hale getirin veya ORM ilişkili yükleme (eager loading) tekniklerini uygulayın.\n"
                    "- Bloklayan senkron çağrıları asenkron karşılıklarıyla (`asyncio.sleep`, `httpx.AsyncClient`) değiştirerek event-loop akışını serbest bırakın.\n"
                    "- Veritabanı sorgularında uygun indekslemeler ve sayfalama (pagination) sınırları tanımlayın."
                )
            return (
                "### Performance Analysis & Optimization\n\n"
                "**1. Identified Bottlenecks:**\n"
                "- Iterative database query calls inside loops (N+1 queries).\n"
                "- Synchronous blocking I/O calls within async handlers.\n\n"
                "**2. Recommended Optimizations:**\n"
                "- Batch query operations with `WHERE IN (...)` or ORM joined eager loading.\n"
                "- Replace blocking calls with async non-blocking alternatives (`asyncio.sleep`, `httpx.AsyncClient`)."
            )

        # Quality review
        if "quality engineer" in prompt_lower or "quality" in prompt_lower:
            if is_tr:
                return (
                    "### 📊 Kod Kalitesi ve Sürdürülebilirlik Raporu\n\n"
                    "**1. Kod Tabanı Sağlığı ve Sürdürülebilirlik:**\n"
                    "Kod tabanı genel olarak iyi bir modüler yapı ve çekirdek modüllerde kabul edilebilir bir siklomatik karmaşıklık skoru sergilemektedir.\n\n"
                    "**2. Refactoring ve İyileştirme Hedefleri:**\n"
                    "- Siklomatik karmaşıklığı 10'un üzerinde olan veya 500 satırı aşan büyük fonksiyon ve sınıflar, tek sorumluluklu (Single Responsibility) yardımcı modüllere bölünmelidir.\n"
                    "- Kritik iş mantığı dallarını kapsayan otomatik birim ve entegrasyon testlerinin kapsam oranı artırılmalıdır.\n"
                    "- Kod tabanındaki yorum ve dokümantasyon kalitesi standartlaştırılmalıdır."
                )
            return (
                "### Code Quality & Maintainability Report\n\n"
                "**1. Maintainability Assessment:**\n"
                "Codebase demonstrates good modularity with acceptable cyclomatic complexity across most core modules.\n\n"
                "**2. Refactoring Targets:**\n"
                "- Decompose oversized functions with cyclomatic complexity > 10 into specialized helper routines.\n"
                "- Maintain automated unit test coverage across all critical business logic branches."
            )

        # Default fallback review
        if is_tr:
            return (
                "### 🤖 Yapay Zeka Kod Tabanı Değerlendirmesi\n\n"
                "Kod deposu tutarlı programlama kalıpları sergilemektedir. İnceleme bulguları; güvenlik parametrelendirmesi, "
                "döngü sorgularının toplu hale getirilmesi ve modüler ayrıştırma alanlarında iyileştirme fırsatları sunmaktadır."
            )
        return (
            "### AI Codebase Evaluation\n\n"
            "The repository demonstrates consistent coding patterns. Review findings highlight potential improvements in "
            "security parameterization, loop query batching, and modular decoupling."
        )

    async def generate_structured(self, prompt: str, schema_cls: Type[BaseModel], system_prompt: Optional[str] = None) -> BaseModel:
        # Default mock structured object
        return schema_cls()

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates deterministic 384-dimensional vector embeddings based on text n-gram hashes.
        Produces genuine semantic-like cosine similarity matching for local test verification!
        """
        dim = settings.EMBEDDING_DIMENSION
        embeddings = []

        for text in texts:
            words = re.findall(r"\w+", text.lower())
            vector = [0.0] * dim

            if not words:
                embeddings.append(vector)
                continue

            for word in words:
                # Hash word to dimensional indices
                h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
                idx = h % dim
                sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
                vector[idx] += sign

            # Normalize vector to unit length (L2 norm)
            norm = math.sqrt(sum(v * v for v in vector))
            if norm > 0:
                vector = [round(v / norm, 5) for v in vector]

            embeddings.append(vector)

        return embeddings

    def _generate_chat_answer(self, prompt: str, is_tr: bool = True) -> str:
        # Extract question from prompt
        question_match = re.search(r"Developer Question:\s*(.*?)(?=\n\s*Rules:|\n\s*ÖNEMLİ:|\Z)", prompt, re.DOTALL | re.IGNORECASE)
        question = question_match.group(1).strip() if question_match else prompt.strip()

        # Extract file citations from context if present
        file_matches = re.findall(r"File:\s*([^\n\r|]+)", prompt)
        unique_files = list(dict.fromkeys(file_matches))[:4]

        file_list_str = ""
        if unique_files:
            file_header = "\n\n**İlgili Kod Tabanı Dosyaları:**\n" if is_tr else "\n\n**Relevant Codebase Files:**\n"
            file_list_str = file_header + "\n".join(f"- `{f.strip()}`" for f in unique_files)

        if is_tr:
            return (
                f"Kod tabanınız üzerinde **'{question}'** sorusu için yapılan semantik analiz doğrultusunda:\n\n"
                f"İlgili iş mantığı ve mimari akış, projenin çekirdek servis ve yönlendirici (router) modülleri üzerinden koordine edilmektedir. "
                f"Gelen istekler doğrulama aşamasından sonra ilgili servis sınıflarına aktarılır ve veritabanı/analiz işlemleri yürütülür.\n"
                f"{file_list_str}\n\n"
                f"Bu davranışı düzenlemek veya genişletmek için yukarıda listelenen servis metotlarını inceleyebilir, hata yönetimi ve girdi doğrulama kurallarını kontrol edebilirsiniz."
            )

        return (
            f"Based on the analysis of your codebase for the question: **'{question}'**\n\n"
            f"The implementation coordinates across the core modules and services. "
            f"Key entrypoints handle request routing, validation, and downstream service execution.\n"
            f"{file_list_str}\n\n"
            f"To modify or extend this behavior, review the corresponding service methods and ensure "
            f"proper validation and error handling are maintained."
        )
