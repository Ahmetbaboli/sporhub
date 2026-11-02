# Changelog

Biçim [Keep a Changelog](https://keepachangelog.com/), sürümleme [SemVer](https://semver.org/).

## [0.4.0] — 2026-11-02

Demo'dan gerçek veriye geçiş. (0.3 ayrı etiketlenmedi; o dönemin özellikleri de burada.)

### Eklendi
- **`DATA_MODE=live|demo`.**
  - Live modda fixture ve örnek haber hiçbir koşulda yazılmaz ya da gösterilmez; anahtarsız
    sağlayıcı "yapılandırılmadı" olur.
  - Demo kayıtları `demo:` önekiyle yazılır ve her sayfada "Örnek veri" şeridi görünür.
  - Yeni araçlar: `purge_demo` komutu, migration 0005.
- **Kaynak durumu:** `GET /api/v1/admin/sources` ve `python -m app.scripts.check_sources`.
  Yalnızca evet/hayır ve HTTP kodu döner.
- **Süper Lig / TFF 1. Lig:**
  - TheSportsDB adapter'ı (yalnızca ücretli anahtarla).
  - football-data yalnızca ücretsiz katmandaki (`TIER_ONE`) 12 ligi döndürür.
- **Sağlayıcılar arası kimlik eşleme:** `external_refs` tablosu.
- **Yenileme altyapısı:**
  - Sağlayıcı başına istek bütçesi; 429'da `Retry-After`'a uyulur.
  - Canlı/bugün/F1 hafta sonu/boşta durumuna göre yenileme yapan planlayıcı.
  - Tek süreçte zamanlayıcı (PostgreSQL advisory lock).
- **Tazelik:** her sayfada "Kaynak · Son güncelleme", "Veri gecikmeli" uyarısı ve "skor
  gecikmeli olabilir" notu.
- **Yönetim ve sağlık:** `/admin/status` (yalnızca `ADMIN_ACCOUNT_IDS`); `/health` veritabanı,
  Redis ve tazeliği raporlar.
- **Gerçek haberler:**
  - Koşulları kontrol edilmiş 9 yayıncı akışı (BBC Sport, ESPN, Yahoo, Habertürk, Sporx).
  - En fazla 2 cümle özet; tam metin ve görsel yok.
  - Kopya birleştirme ("Ayrıca: …").
  - Gerçek başlıklarla ayarlanmış sınıflandırıcı (140 etiketli başlıkta %96,4; yanlış "resmî" 0).
- **Hesap:** hesap ve veri silme (`DELETE /api/v1/me`), `/privacy`, `/sources`, `/about`;
  alt bilgide sağlayıcı atıfları.
- **0.3 döneminden:**
  - Giriş ve favoriler, kişisel panel.
  - Renk paletleri, TR/EN.
  - Takım analizi ve karşılaştırma.
  - Lig istatistikleri ve grafikler.
  - Haber modülü.
- **Belgeler:** `docs/DATA-SOURCES.md`, `docs/AUTH-SETUP.md`.

### Değişti
- Geliştirici girişi yalnızca `next dev` + `ENABLE_DEV_LOGIN=true` ile çalışır; üretim
  derlemesinde hiç açılmaz.
- API, Neon'un `postgresql://…?sslmode=require` adresini asyncpg biçimine kendisi çevirir.
  Hatalı yapılandırmada açılmaz; mesaj değişken adını söyler, değeri yazmaz.
- Sağlayıcı logoları gösterilmez: açık gösterim izni doğrulanamadı.
- F1 fixture'ları 2026 Meksika GP sonrası gerçek Jolpica yanıtlarından yeniden üretildi.
- Testler `.env` dosyasını ve kabuktaki sağlayıcı değişkenlerini okumaz.

### Kaldırıldı
- `USE_FIXTURES` (yerine `DATA_MODE`).
- `SYNC_INTERVAL_MINUTES` (yerine planlayıcı).
- `AUTH_DEV_LOGIN` (yerine `ENABLE_DEV_LOGIN`).
- Anahtarsız sağlayıcının fixture'a düşmesi.

### Güvenlik
- Yapılandırılmış anahtar değerleri loglarda ve kaydedilen senkron hatalarında maskelenir
  (TheSportsDB anahtarı URL yolunda taşınır).

## [0.2.0] — 2026-10-26

### Eklendi
- **Basketbol (NBA) adapter'ı** (balldontlie): takımlar, oyuncular (ücretli katmanda kadro), maçlar; puan durumu ücretsiz katmanda olmayan `/standings` yerine sonuçlardan hesaplanır.
- **Formula 1 adapter'ı** (Jolpica): takvim, yarış sonuçları (`kind="race"`), sürücü ve takım şampiyonası, takımlar ve sürücüler.
- Ortak `HttpFixtureAdapter` tabanı (hız sınırı, yeniden deneme, fixture modu, tarih kaydırma); futbol adapter'ı ona taşındı.
- Her adapter için fixture JSON'ları ve üreteç betikleri; **tüm adapter'lar için ortak sözleşme testleri** (registry'yi gezer).
- Arayüzde spora özel şablonlar: NBA konferans sıralaması, F1 şampiyona tabloları ve yarış kartı (podyum + tam sonuç), spor ikonlu spor seçici, basketbol/F1 oyuncu profili bilgileri.
- `docs/adding-a-sport.md`.
- Anahtarı olmayan adapter fixture'a düştüğünde zamanlayıcı onu atlar.

### Değişti
- API testleri gerçek PostgreSQL ve Redis servisleriyle CI'da koşar (`TEST_DATABASE_URL`, `TEST_REDIS_URL`); yerelde SQLite varsayılandır. Postgres'e özgü upsert/timestamptz/JSONB testleri eklendi.
- Dialect'e özgü kod `app/db/dialect.py` içinde toplandı; `UTCDateTime` naive datetime'ı reddeder.
- Web: detay sayfaları artık gerçek HTTP 404 döner (sayfa içi Suspense, `loading.tsx` kaldırıldı).

### Düzeltildi
- İlk lig hatasındaki rollback'in spor satırını silmesi (PostgreSQL FK ile yakalandı).

## [0.1.0] — 2026-10-26

### Eklendi
- Monorepo iskeleti, MIT lisansı, CLAUDE.md ve docs/ (mimari, kararlar, ilerleme, tasarım, deploy).
- **API:** FastAPI uygulaması, yapılandırılmış JSON log, tutarlı hata gövdesi, CORS, `/health`, sürümlü `/api/v1` uçları (sporlar, ligler, fikstür/sonuç, puan tablosu, bugünün etkinlikleri, takım, oyuncu, arama), admin sync ucu.
- **Veri modeli:** `sports`, `competitions`, `seasons`, `teams`, `players`, `events`, `event_participants`, `standings`, `sync_runs` + ilk Alembic migration.
- **Adapter mimarisi:** `BaseAdapter`, ortak DTO'lar, registry, rate limit + tenacity'li HTTP istemcisi, football-data.org adapter'ı ve fixture modu.
- **Senkronizasyon:** idempotent upsert servisi, APScheduler, `sync_runs` kaydı, seed komutu, Redis/bellek cache.
- **Web:** Next.js arayüzü (ana sayfa, spor, lig sekmeleri, takım, oyuncu, arama), tipli API istemcisi, koyu/açık tema, skeleton/boş/hata durumları, TR metin katmanı.
- Docker Compose, Dockerfile'lar, GitHub Actions CI, `render.yaml`.
- Testler: API (pytest, ~%92 kapsam) ve web (Vitest).
