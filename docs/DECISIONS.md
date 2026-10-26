# Kararlar ve varsayımlar

Biçim: tarih — karar — gerekçe.

- 2026-10-26 — Depo klasörü `sporhub/`, ürün adı "Just Sport". Gerekçe: istenen monorepo yapısı `sporhub/` olarak verildi.
- 2026-10-26 — Python ortamı `uv` ile (winget, kullanıcı düzeyi) kuruldu; makinede Python yoktu. Gerekçe: spec uv'yi öneriyor.
- 2026-10-26 — football-data.org doğrulandı: base `https://api.football-data.org/v4`, `X-Auth-Token`, ücretsiz katman 10 istek/dk (adapter istekler arası 6.5 sn bekler), ücretsiz katman: PL, PD, SA, BL1, CL, FL1, DED, PPL, ELC, BSA, WC, EC. **Süper Lig ücretsiz katmanda yok**; varsayılan liglere eklenmedi.
- 2026-10-26 — Testler SQLite (aiosqlite) üzerinde koşar; JSON kolonu PostgreSQL'de JSONB'ye çevrilir (`JSONType`), upsert dialect'e göre `ON CONFLICT` kullanır. Gerekçe: makinede Docker/PostgreSQL yok, testler internetsiz ve hızlı olsun. CI ayrıca Postgres servisiyle migration + seed doğrular.
- 2026-10-26 — `competitions.slug` kolonu eklendi (spec'te yok): web rotası `/[sport]/[competition]` okunur slug kullanır. `GET /competitions/{ref}` hem sayısal id hem slug kabul eder. `competitions.external_id` football-data için lig kodudur (PL, CL…).
- 2026-10-26 — Enum'lar PostgreSQL enum tipi yerine `String + CHECK` olarak tutuldu (migration kolaylığı).
- 2026-10-26 — Fixture'lar `api/tools/generate_fixtures.py` ile üretilen **sentetik örnek veridir** (gerçek takım adları, uydurma oyuncular/skorlar), ham football-data v4 formatındadır. Fixture modunda maç tarihleri `reference_date` ile bugün arasındaki gün farkı kadar kaydırılır; böylece "bugünün maçları" her zaman dolu görünür.
- 2026-10-26 — `round` kolonu string (futbolda matchday, F1'de tur adı/no taşıyabilsin). `event_participants` ve `standings` için sentetik `id` PK kullanıldı; sync katılımcıları/puan tablosunu ilgili event/sezon için silip yeniden yazar (idempotent).
- 2026-10-26 — `/events/today` `date` ve `tz` (IANA) parametreleri alır; web varsayılan olarak `Europe/Istanbul` gönderir.
- 2026-10-26 — Admin sync `202 Accepted` döner ve arka planda çalışır (gerçek modda rate limit yüzünden dakikalar sürebilir). `ADMIN_TOKEN` boşsa uç 503 ile kapalıdır.
- 2026-10-26 — Docker bu makinede kurulu değil: `docker-compose.yml` ve Dockerfile'lar yazıldı ama burada çalıştırılıp doğrulanmadı (PROGRESS "Engeller").
