# Changelog

Biçim [Keep a Changelog](https://keepachangelog.com/), sürümleme [SemVer](https://semver.org/).

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
