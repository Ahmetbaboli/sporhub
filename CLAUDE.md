# CLAUDE.md — Just Sport

Çok sporlu, modüler spor veri platformu. Python servisi dış API'lerden veri çeker, ortak şemaya normalize edip PostgreSQL'e yazar; Next.js arayüzü yalnızca kendi API'mizi okur. **Frontend asla dış spor API'lerine doğrudan istek atmaz.** Yeni spor eklemek = yeni adapter sınıfı + registry satırı.

## Mimari özet
`adapters/` (dış veri → DTO, DB'ye yazmaz) → `services/sync_service.py` (upsert) → PostgreSQL. Okuma: `routers/ → services/ → repositories/ → models/`. Redis sık okunan uçları cache'ler. Ayrıntı: `docs/ARCHITECTURE.md`.

## Klasörler
- `api/` Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic (`app/`, `tests/`, `fixtures/`, `alembic/`)
- `web/` Next.js App Router, TypeScript strict, Tailwind, shadcn/ui tarzı bileşenler
- `docs/` ARCHITECTURE, DECISIONS, PROGRESS, DESIGN, DEPLOY
- `.github/workflows/ci.yml`, `docker-compose.yml`, `render.yaml`

## Komutlar
```bash
# Hepsi birden (Docker)
docker compose up --build

# API (api/ içinde; uv gerekir)
uv sync
uv run alembic upgrade head
uv run python -m app.scripts.seed        # fixture verisiyle doldur
uv run uvicorn app.main:app --reload
uv run pytest --cov=app                  # test + kapsam
uv run ruff check . && uv run ruff format --check .
uv run alembic revision --autogenerate -m "mesaj"

# Web (web/ içinde)
npm install
npm run dev
npm run lint && npx tsc --noEmit && npm test && npm run build
```

## Kod kuralları
- Python: tip ipuçları zorunlu, ruff, kısa tek sorumluluklu fonksiyonlar, sihirli sayı yerine sabit.
- TypeScript: `strict: true`; tüm API çağrıları `web/lib/api.ts` üzerinden; UI metinleri `web/lib/i18n/tr.ts` içinde (tek yer).
- Zamanlar UTC saklanır, arayüzde kullanıcı saat dilimine çevrilir. Spora özel alanlar `extra` JSONB'de.
- Her dış kayıt `(source, external_id)` ile benzersiz; sync upsert'tir, idempotenttir.
- Loglar yapılandırılmış (JSON); gizli bilgi loglanmaz. Yeni env değişkeni `.env.example`'a açıklamasıyla eklenir.
- Adapter'lar: rate limit saygısı, tenacity ile üstel geri çekilme, timeout, `USE_FIXTURES=true` desteği.

## Commit formatı
Conventional Commits: `feat(api): ...`, `fix(web): ...`, `docs: ...`, `test: ...`, `chore: ...`.

## Çalışma şekli (otonom oturumlar)
- Soru sorma, onay bekleme; belirsizlikte makul varsayım yap ve `docs/DECISIONS.md`'ye tarih + gerekçeyle yaz.
- Görevleri aşama sırasıyla tek tek yap. Her görev sonunda: test + lint çalıştır (kırmızı bırakma) → Conventional Commit → `docs/PROGRESS.md`'de işaretle.
- Bir şey çalışmazsa üç farklı yaklaşım dene; olmazsa `docs/PROGRESS.md` "Engeller" altına yaz, sonraki göreve geç.
- `git push` yok, uzak repo ayarlama yok (sahibi yapar).
- `.env` dosyalarını okuma/oluşturma; yalnızca `.env.example`. Koda/commit'e gizli anahtar girmez.
- Yıkıcı komut yok (`rm -rf`, `git reset --hard`, volume silme vb.).
- Büyük işlerde önce kısa plan (`docs/PROGRESS.md`), sonra uygulama.
- Aşama bitiminde kısa rapor: yapılanlar, çalıştırma, varsayımlar, engeller, sıradaki iş.
