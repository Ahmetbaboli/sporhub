# Changelog

Biçim [Keep a Changelog](https://keepachangelog.com/), sürümleme [SemVer](https://semver.org/).

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
