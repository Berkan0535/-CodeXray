from typing import Dict, Any, Optional

ISSUE_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Security
    "Potential SQL Injection": {
        "title": "Olası SQL Enjeksiyonu (SQL Injection)",
        "description": "SQL sorgu ifadesi içinde parametrelendirilmemiş değişken birleştirme veya f-string kullanımı tespit edildi.",
        "impact": "Saldırganlar kimlik doğrulamasını atlayabilir, veritabanı kayıtlarını okuyabilir, değiştirebilir, silebilir veya yönetici işlemleri yürütebilir.",
        "recommendation": "Dize birleştirme/f-string yerine parametreli sorgular (parameterized queries), prepared statements veya ORM parametre bağlama yöntemlerini kullanın."
    },
    "Command Injection Vulnerability": {
        "title": "Komut Enjeksiyonu Zafiyeti (Command Injection)",
        "description": "Kullanıcı kontrolündeki girdilerle veya shell=True etkinleştirilerek sistem kabuk komutlarının çalıştırılması.",
        "impact": "Uzaktan kod çalıştırma (RCE) ile ana makine dosya sistemine, ağa ve ortam değişkenlerindeki gizli anahtarlara yetkisiz erişim riski.",
        "recommendation": "Kabuk komutlarını doğrudan çağırmaktan kaçının. shell=False ile subprocess argüman listesi kullanın veya yerel dil API'lerini tercih edin."
    },
    "Insecure Deserialization (Pickle/YAML/Object)": {
        "title": "Güvensiz Serileştirme Çözme (Insecure Deserialization)",
        "description": "Güvenilmeyen bayt akışlarının veya güvenli yükleyiciler olmadan YAML/Pickle verilerinin deserialization işlemine tabi tutulması.",
        "impact": "Zararlı veri yüklendiğinde rastgele nesne oluşturma ve uzaktan kod çalıştırma (RCE) tehlikesi.",
        "recommendation": "Pickle veya güvensiz YAML yerine JSON (json.loads) gibi güvenli serileştirme formatları veya yaml.safe_load() kullanın."
    },
    "Potential Server-Side Request Forgery (SSRF)": {
        "title": "Olası Sunucu Taraflı İstek Sahteciliği (SSRF)",
        "description": "Doğrulanmamış veya kullanıcı tarafından sağlanan hedef URL ile giden HTTP isteği yapılması.",
        "impact": "Saldırgan sunucuyu dahili bulut metadata uç noktalarına (169.254.169.254), dahili servislere veya loopback arayüzlerine istek göndermeye zorlayabilir.",
        "recommendation": "Hedef ana makine adlarını doğrulayın, beyaz liste (whitelist) uygulayın ve özel/loopback IP aralıklarına (127.0.0.1, 169.254.169.254) istekleri engelleyin."
    },
    "Disabled SSL/TLS Certificate Verification": {
        "title": "Devre Dışı Bırakılmış SSL/TLS Sertifika Doğrulaması",
        "description": "HTTP istemci isteklerinde SSL/TLS sertifika doğrulamasının devre dışı bırakılması (verify=False veya InsecureSkipVerify).",
        "impact": "Ortadaki adam (Man-in-the-Middle - MITM) saldırılarına ve hassas aktarım verilerinin dinlenmesine/değiştirilmesine açık hale getirir.",
        "recommendation": "SSL/TLS sertifika doğrulamasını her zaman etkinleştirin ve özel sertifikalar için CA paketlerini kullanın."
    },
    "Hardcoded Secret / API Token": {
        "title": "Sabit Kodlanmış Gizli Anahtar / API Token",
        "description": "Kaynak kod içerisinde açık metin halinde API anahtarı, şifre veya gizli anahtar bulundu.",
        "impact": "Yetkisiz kullanıcılar üçüncü taraf API'lere veya bulut altyapılarına doğrudan erişim sağlayabilir.",
        "recommendation": "Sabit kodlanmış kimlik bilgilerini derhal iptal edin/yenileyin ve Çevre Değişkenleri (Environment Variables) veya Secrets Manager kullanın."
    },
    "Unsafe eval()/exec() Execution": {
        "title": "Güvensiz eval()/exec() Kod Çalıştırma",
        "description": "Dinamik kod dizgilerinin eval() veya exec() ile doğrudan yorumlanması.",
        "impact": "Kullanıcı girdisinin doğrulanmadan çalıştırılması doğrudan uzaktan kod yürütmeye yol açabilir.",
        "recommendation": "Dinamik kod çalıştırmadan kaçının. Güvenli veri ayrıştırma (ast.literal_eval) veya standart veri modelleri kullanın."
    },
    "Path Traversal Vulnerability": {
        "title": "Dizin Geçişi Zafiyeti (Path Traversal)",
        "description": "Kullanıcı girdisinin dosya yollarına doğrudan eklenmesiyle yetkisiz dosya okuma/yazma riski.",
        "impact": "Sistem dosyalarının (/etc/passwd, .env vb.) sızdırılması veya üzerine yazılması.",
        "recommendation": "Dosya yollarını os.path.abspath veya resolve() ile izole bir temel dizine sınırlandırın."
    },

    # Performance
    "N+1 Database Query in Loop": {
        "title": "Döngü İçinde N+1 Veritabanı Sorgusu",
        "description": "For veya while döngüsü içinde yinelenen veritabanı sorguları çalıştırılıyor.",
        "impact": "Her döngü iterasyonunda yeni veritabanı gidiş-dönüşü (round-trip) yapılarak ciddi gecikme artışına ve veritabanı yüküne neden olur.",
        "recommendation": "Sorguları WHERE IN (...) ile toplu (batch) hale getirin veya ORM eager loading (selectinload, joinedload) kullanın."
    },
    "Blocking Sync Call in Async Function": {
        "title": "Asenkron Fonksiyonda Bloklayan Senkron Çağrı",
        "description": "async coroutine içinde event-loop'u kilitleyen senkron I/O veya time.sleep() çağrısı tespit edildi.",
        "impact": "Tüm FastAPI / asyncio event-loop akışını bloke ederek eşzamanlı istek işleme kapasitesini durdurur.",
        "recommendation": "time.sleep yerine await asyncio.sleep(), requests yerine httpx.AsyncClient kullanın."
    },
    "Deeply Nested Loops (High Algorithmic Complexity)": {
        "title": "Derin İç İçe Döngüler (Yüksek Algoritmik Karmaşıklık)",
        "description": "3 veya daha fazla katmanda iç içe geçmiş döngüler tespit edildi (O(N^3)+ karmaşıklık riski).",
        "impact": "Büyük veri kümelerinde CPU darboğazına ve aşırı yürütme sürelerine yol açar.",
        "recommendation": "Veri yapılarını optimize edin (hash map/sözlük indeksleme) veya algoritmayı lineer/logaritmik zaman karmaşıklığına indirgeyin."
    },
    "Unbounded Database Query (Missing LIMIT/Pagination)": {
        "title": "Sınırsız Veritabanı Sorgusu (LIMIT/Sayfalama Eksik)",
        "description": "LIMIT veya sayfalama olmadan tüm tabloyu çeken veritabanı sorgusu.",
        "impact": "Yüksek bellek tüketimi, sunucu çökmesi veya veritabanı bellek taşması.",
        "recommendation": "Tüm listeleme sorgularında LIMIT/OFFSET veya imleç tabanlı sayfalama (cursor pagination) zorunlu tutun."
    },
    "Potential Catastrophic Regex Backtracking (ReDoS)": {
        "title": "Düzenli İfade Hizmet Engelleme Riski (ReDoS)",
        "description": "İç içe tekrarlayıcılar içeren karmaşık Regex deseni felaket düzeyinde geri izleme (backtracking) riski taşıyor.",
        "impact": "Özel hazırlanmış girdiler CPU'yu %100 oranında kilitleyerek servis kesintisine yol açabilir.",
        "recommendation": "Düzenli ifadeleri basitleştirin veya deterministik ayrıştırma motorları kullanın."
    },

    # Quality & Maintainability
    "High Cyclomatic Complexity": {
        "title": "Yüksek Siklomatik Karmaşıklık",
        "description": "Fonksiyon çok fazla karar dalı (if/else/switch/loop) içeriyor ve okunması/test edilmesi zor.",
        "impact": "Hata olasılığını artırır, birim test kapsamını zorlaştırır ve bakım maliyetlerini yükseltir.",
        "recommendation": "Fonksiyonu daha küçük, tek sorumluluklu (Single Responsibility) yardımcı rutinlere bölün."
    },
    "High Code Duplication": {
        "title": "Yüksek Kod Tekrarı (Code Duplication)",
        "description": "Farklı dosyalar arasında tekrarlanan benzer kod blokları tespit edildi.",
        "impact": "Tekrarlanan mantıkta yapılan hata düzeltmelerinin her yerde uygulanması zorlaşır ve teknik borç oluşturur.",
        "recommendation": "Tekrarlayan mantığı ortak yardımcı modüllere, kütüphanelere veya servis fonksiyonlarına taşıyın."
    },
    "Low Code Documentation": {
        "title": "Düşük Kod Dokümantasyon Oranı",
        "description": "Kod tabanında yorum ve docstring oranı %5'in altında.",
        "impact": "Geliştiricilerin kod akışını ve modül sorumluluklarını anlamasını geciktirir.",
        "recommendation": "Kritik servis sınıflarına ve public API fonksiyonlarına docstring ve açıklayıcı yorumlar ekleyin."
    },

    # Architecture
    "Circular Dependency Detected": {
        "title": "Dairesel Bağımlılık Tespit Edildi",
        "description": "Modüller birbirlerine çift yönlü bağımlılıkla referans veriyor (A -> B -> A).",
        "impact": "Modüler test edilebilirliği engeller, başlangıç zamanı döngüsel import hatalarına yol açabilir.",
        "recommendation": "Arayüzleri (interface) veya paylaşılan modelleri ortak bir 'core' veya 'common' katmanına ayırın."
    },
    "Cross-Layer Architecture Boundary Violation": {
        "title": "Katmanlar Arası Mimari Sınır İhlali",
        "description": "Alt katmanların (Repository/DB) doğrudan üst katmanlara (API/UI) bağımlılık oluşturması.",
        "impact": "Mimari katman ayrımını bozar ve bağımlılık enjeksiyonu prensiplerine aykırıdır.",
        "recommendation": "Bağımlılıkları tek yönlü tutun: API -> Servis -> Repository."
    }
}


def localize_issue_item(issue: Dict[str, Any], lang: str = "tr") -> Dict[str, Any]:
    if lang != "tr":
        return issue

    title = issue.get("title", "")
    
    # Try exact match or partial match
    trans = None
    for key, val in ISSUE_TRANSLATIONS.items():
        if key.lower() in title.lower() or title.lower() in key.lower():
            trans = val
            break
        # Match pattern like "Oversized File" or "Oversized Function"
        if "oversized file" in title.lower():
            trans = {
                "title": f"Aşırı Büyük Dosya ({title})",
                "description": f"Dosya tek sorumluluk ilkesini (SRP) zorlayacak düzeyde çok sayıda kod satırı içeriyor.",
                "impact": "Gezinmesi, test edilmesi ve bakımı zordur.",
                "recommendation": "Daha küçük ve odaklanmış modüllere veya yardımcı dosyalara bölün."
            }
            break
        if "oversized function" in title.lower():
            trans = {
                "title": f"Aşırı Büyük Fonksiyon ({title})",
                "description": f"Fonksiyon çok fazla satır içeriyor.",
                "impact": "Okunabilirliği ve test kapsamını olumsuz etkiler.",
                "recommendation": "Fonksiyon mantığını küçük yardımcı alt fonksiyonlara ayırın."
            }
            break
        if "high cyclomatic complexity" in title.lower():
            trans = ISSUE_TRANSLATIONS["High Cyclomatic Complexity"]
            break

    if trans:
        new_issue = dict(issue)
        new_issue["title"] = trans.get("title", issue.get("title"))
        if not issue.get("description") or issue.get("description", "").startswith("File '") or "contains" in issue.get("description", "") or "violating" in issue.get("description", "") or "Dynamic" in issue.get("description", "") or "Execution" in issue.get("description", "") or "Outbound" in issue.get("description", ""):
            new_issue["description"] = trans.get("description", issue.get("description"))
        new_issue["impact"] = trans.get("impact", issue.get("impact"))
        new_issue["recommendation"] = trans.get("recommendation", issue.get("recommendation"))
        return new_issue

    return issue
