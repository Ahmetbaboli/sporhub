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
- [x] Next.js iskeleti, tema, layout
- [x] Tipli API istemcisi
- [x] Ana sayfa (bugünün maçları)
- [x] Lig sayfası (Fikstür, Sonuçlar, Puan Tablosu)
- [x] Takım ve oyuncu sayfaları
- [x] Arama (API + sayfa)
- [x] Skeleton, boş ve hata durumları
- [x] GitHub Actions CI
- [x] Deploy hazırlığı (render.yaml, docs/DEPLOY.md)
- [x] README ilk sürüm
- [x] v0.1.0 etiketi + CHANGELOG.md

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

- Docker bu makinede yok: `docker compose up` yazıldı ama doğrulanamadı; API yerelde SQLite + uvicorn ile doğrulandı. Docker'lı makinede ilk iş: `docker compose up --build`.
- Docker doğrulanamadı (kurulu değil): `docker-compose.yml`, `api/Dockerfile`, `web/Dockerfile` yazıldı; yerelde API (SQLite + uvicorn) ve web (`next build` + `next start`) çalıştırılıp doğrulandı. CI'daki Postgres adımı da ilk push'ta görülecek.
- `localhost:3000` bu makinede başka bir uygulama tarafından kullanılıyordu; web duman testi 3100'de yapıldı.
- Süreç sonlandırma izni reddedildi: duman testi için başlattığım `uvicorn` (8000) ve `next start` (3100) süreçleri açık kalmış olabilir; elle kapatın.
- Hata/404 sayfaları `loading.tsx` streaming'i yüzünden HTTP 200 dönüyor (içerik doğru, durum kodu değil). Aşama 3'te `generateMetadata`/ön kontrolle 404 durum koduna çevrilebilir.
