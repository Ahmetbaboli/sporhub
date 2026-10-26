# İlerleme

## Aşama 0 — Hazırlık
- [x] git init, LICENSE, .gitignore, .editorconfig
- [x] Monorepo klasör yapısı
- [x] CLAUDE.md
- [x] docs/PROGRESS, DECISIONS, ARCHITECTURE
- [x] api/.env.example, web/.env.example

## Aşama 1 — Altyapı ve veri modeli
- [x] docker-compose.yml
- [x] FastAPI iskeleti (ayarlar, /health, CORS, hata işleyici, log)
- [x] SQLAlchemy modelleri + ilk Alembic migration
- [x] BaseAdapter, DTO'lar, registry
- [x] Futbol adapter'ı + fixture'lar + fixture modu
- [x] sync_service (upsert) + APScheduler + sync_runs
- [x] Seed komutu
- [x] Redis cache katmanı
- [x] REST uçları (/api/v1)
- [x] pytest testleri

## Aşama 2 — Futbol MVP
- [ ] Next.js iskeleti, tema, layout
- [ ] Tipli API istemcisi
- [ ] Ana sayfa (bugünün maçları)
- [ ] Lig sayfası (Fikstür, Sonuçlar, Puan Tablosu)
- [ ] Takım ve oyuncu sayfaları
- [ ] Arama (API + sayfa)
- [ ] Skeleton, boş ve hata durumları
- [ ] GitHub Actions CI
- [ ] Deploy hazırlığı (render.yaml, docs/DEPLOY.md)
- [ ] README ilk sürüm
- [ ] v0.1.0 etiketi + CHANGELOG.md

## Sonraki oturumlar (şimdi yapma)
### Aşama 3 — Modülerliği kanıtla
- [ ] Basketbol (balldontlie) ve F1 (Jolpica/OpenF1) adapter'ları
- [ ] Spora özel sayfa şablonları (F1 şampiyona sıralaması)
- [ ] docs/adding-a-sport.md
- [ ] Tüm adapter'lar için ortak sözleşme testleri
### Aşama 4 — Kullanıcı özellikleri
- [ ] Auth.js girişi, favori takımlar, kişisel panel
- [ ] İstatistik grafikleri (Recharts), karşılaştırma ekranı
- [ ] TR/EN (next-intl)
### Aşama 5 — Öne çıkaran özellikler
- [ ] SSE ile canlı skor
- [ ] Claude API ile AI maç özeti (backend'de)
- [ ] Spor bilgi yarışması, PWA, Playwright e2e
### Aşama 6 — Vitrin
- [ ] README ekran görüntüleri/GIF, repo konu etiketleri, v1.0.0

## Engeller
(henüz yok)
- Docker bu makinede yok: `docker compose up` yazıldı ama doğrulanamadı; API yerelde SQLite + uvicorn ile doğrulandı. Docker'lı makinede ilk iş: `docker compose up --build`.
