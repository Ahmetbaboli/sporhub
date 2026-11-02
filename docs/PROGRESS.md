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

## v0.1.0 sonrası ön görevler (Aşama 3 öncesi)
- [x] CI'da API testleri gerçek PostgreSQL + Redis ile; yerelde SQLite (`TEST_DATABASE_URL` ile seçilir)
- [x] Upsert / timezone / JSONB testleri Postgres'te; dialect kodu tek yerde; timestamptz'ye hep UTC-aware yazılır
- [x] Detay sayfalarında gerçek HTTP 404 (loading.tsx yerine sayfa içi Suspense)
- [x] Fixture tarih kaydırmasının yalnızca `USE_FIXTURES=true` iken çalıştığı testlerle güvence altında

## Sonraki oturumlar (şimdi yapma)
### Aşama 3 — Modülerliği kanıtla
- [x] Basketbol (balldontlie) ve F1 (Jolpica) adapter'ları
- [x] Spora özel sayfa şablonları (F1 şampiyona sıralaması, NBA konferans sıralaması, yarış kartı)
- [x] docs/adding-a-sport.md
- [x] Tüm adapter'lar için ortak sözleşme testleri
### Aşama 4 — Kullanıcı özellikleri
- [x] API: kullanıcılar, favoriler (takım/oyuncu/lig), imzalı token, panel ucu
- [x] 4a Web: Auth.js girişi (GitHub/Google), favori yıldızları (takım/sporcu/lig), "Panelim" + giriş yapmış kullanıcıya özel ana sayfa
- [x] 4b Farklı renk temaları (açık/koyu × 6 palet, yüksek kontrast dahil)
- [x] 4c Takım analizi: son 5-10 maç formu, ev/deplasman performansı, geçmiş karşılaşmalar (H2H)
- [x] 4d Karşılaştırma: iki takım, iki sporcu (`/compare`)
- [x] 4e Lig istatistikleri + liderlik tabloları (gol krallığı / sayı / şampiyona puanı), sezon geçmişi
- [ ] 4f Oyuncu sezonluk performans grafikleri (Recharts), branşa özel gelişmiş istatistikler
- [ ] 4g TR/EN dil seçeneği (next-intl; `tr.ts` → `messages/{tr,en}`)
### Aşama 4.5 — Haber modülü
- [ ] Veri modeli: `news_articles` (spor, kategori, etiketli takım/oyuncu/lig, kaynak, yayın zamanı), `(source, external_id)` benzersiz
- [ ] Kategoriler: genel, son dakika, transfer (resmî), transfer söylentisi, röportaj, organizasyon/turnuva
- [ ] Haber adapter'ı (RSS/Atom; yalnızca başlık + özet + kaynağa link) + fixture modu; admin'den elle haber girişi
- [ ] Haber sayfaları: `/news`, kategori/spor filtresi, arşiv (sayfalı, tarihe göre), takım/oyuncu sayfasında ilgili haberler
### Aşama 5 — Öne çıkaran özellikler
- [ ] SSE ile canlı skor
- [ ] Bildirimler: Web Push (VAPID) — takip edilen maç başladı / gol / bitti, son dakika haberi; kullanıcı bazlı tercihler
- [ ] Claude API ile AI maç özeti (backend'de)
- [ ] Spor bilgi yarışması, PWA, Playwright e2e
### Öneri havuzu (sıraya alınmadı)
- Maç tahmin oyunu + arkadaş ligi; maç sayfasında taraftar anketi ("kim kazanır?")
- Takvime ekle (.ics) — favori takımın fikstürü tek tıkla
- Maç detay sayfası: kadro/diziliş, olay zaman çizelgesi, istatistik barları
- "Bu hafta" özet sayfası ve e-posta bülteni; favori takıma göre haftalık özet
- Embed edilebilir puan tablosu/skor widget'ı
- Sezon geçmişinde şampiyonlar listesi; "bugün tarihte" kartı
- Erişilebilirlik: yüksek kontrastlı tema, klavyeyle tam gezinme
### Aşama 6 — Vitrin
- [ ] README ekran görüntüleri/GIF, repo konu etiketleri, v1.0.0

## Engeller

- Docker bu makinede yok: `docker compose up` yazıldı ama doğrulanamadı; API yerelde SQLite + uvicorn ile doğrulandı. Docker'lı makinede ilk iş: `docker compose up --build`.
- Docker doğrulanamadı (kurulu değil): `docker-compose.yml`, `api/Dockerfile`, `web/Dockerfile` yazıldı; yerelde API (SQLite + uvicorn) ve web (`next build` + `next start`) çalıştırılıp doğrulandı. CI'daki Postgres adımı da ilk push'ta görülecek.
- `localhost:3000` bu makinede başka bir uygulama tarafından kullanılıyordu; web duman testi 3100'de yapıldı.
- Süreç sonlandırma: geniş filtreli `Stop-Process` reddedildi; yalnızca kendi başlattığım süreçler PID ile durduruldu.
- ~~Hata/404 sayfaları HTTP 200 dönüyordu~~ — v0.2.0'da çözüldü (gerçek 404).
- Docker hâlâ bu makinede yok: compose dosyaları doğrulanamadı. PostgreSQL yerelde `pgserver` (taşınabilir PG 16.2) ile, Redis `fakeredis` ile doğrulandı; gerçek Redis yalnızca CI'da koşar.
- balldontlie ücretsiz katmanı kadro (`/players/active`) ve `/standings` vermez: puan durumu hesaplanır, kadro yalnızca ücretli katmanda dolar. Gerçek anahtarla uçtan uca deneme yapılamadı (anahtar yok); davranış `respx` ile doğrulandı.
- Jolpica canlı API'sine bu oturumda gerçek bir senkronizasyon çalıştırılmadı (yalnızca dokümandaki yapı ve örnek yanıtlar doğrulandı); `respx` testleri doküman şemasına göre yazıldı.
