# Yayına alma rehberi (gerçek veri, `DATA_MODE=live`)

Hedef mimari:

| Parça | Nerede |
| --- | --- |
| web | Vercel |
| api | Render (Docker) |
| veritabanı | Neon PostgreSQL |
| önbellek | Upstash Redis (isteğe bağlı) |

Bu repo yalnızca yapılandırmayı hazırlar; hesapları siz açarsınız ve deploy'u siz yaparsınız.
Gizli değerleri yalnızca barındırma panellerinin gizli değişken alanlarına girin. Repoya, loga
veya ekran görüntüsüne koymayın.

## 1. Veritabanı (Neon)

1. https://neon.tech → yeni proje oluşturun; bölge olarak Frankfurt (`aws-eu-central-1`) seçin.
   Vercel `fra1` ile aynı yerde olur.
2. **Connection Details** → **Pooled connection kapalı** (doğrudan bağlantı) adresini kopyalayın:
   `postgresql://USER:PASS@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require`.
   - Doğrudan bağlantı gerekli, çünkü zamanlayıcı kilidi PostgreSQL *oturum* düzeyinde bir advisory
     lock'tur. Neon'un "-pooler" adresi (PgBouncer, transaction modu) oturum kilitlerini taşımaz.
   - API'nin bağlantı sayısı küçüktür; havuzlayıcıya gerek yoktur.
3. Adresi **olduğu gibi** `DATABASE_URL` olarak girin. API `postgres://`/`postgresql://` önekini
   `postgresql+asyncpg://`'ye, `sslmode=require`'ı da `ssl=require`'a kendisi çevirir;
   `channel_binding` parametresini düşürür.
4. Migration'lar API her açıldığında (`entrypoint.sh` → `alembic upgrade head`) otomatik çalışır.
5. Daha önce demo verisi yüklenmiş bir veritabanı kullanıyorsanız:
   - Migration 0005 eski satırları `demo:` olarak işaretler.
   - Live API açılışta bunları siler; elle silmek için `python -m app.scripts.purge_demo`.

## 2. Redis (Upstash, isteğe bağlı)

1. https://upstash.com → **Create database** → Frankfurt.
2. **Redis URL**'yi (`rediss://default:...@...upstash.io:6379`, TLS) `REDIS_URL` olarak girin.
3. Boş bırakılırsa süreç içi bellek önbelleği kullanılır. Tek örnekte sorun olmaz; birden fazla
   örnekte önbellek örnekler arasında paylaşılmaz.

## 3. API (Render)

1. Repoyu GitHub'a gönderin.
2. Render → **New → Blueprint** → repoyu seçin. `render.yaml`'dan `justsport-api` oluşur.
3. Dashboard'da `sync: false` değişkenlerini doldurun. **API ortam değişkenleri:**

| Değişken | Zorunlu | Açıklama |
| --- | --- | --- |
| `DATABASE_URL` | evet | Neon doğrudan bağlantı adresi (yukarıda) |
| `DATA_MODE` | — | `live` (varsayılan). `demo` herkese açık sitede kullanılmaz |
| `SCHEDULER_ENABLED` | — | `true`: arka plan yenileme. Kilit sayesinde yalnızca bir örnek çalıştırır |
| `CORS_ORIGINS` | evet | Web adresi, ör. `https://justsport.vercel.app` (`*` reddedilir) |
| `ADMIN_TOKEN` | önerilir | ≥16 rastgele karakter (Render `generateValue`); boşsa admin uçları kapalı |
| `API_TOKEN_SECRET` | girişi kullanacaksanız | ≥32 karakter; web'dekiyle **aynı** |
| `INTERNAL_API_KEY` | **evet** | ≥32 rastgele karakter; web'dekiyle **aynı**. Web sunucusu bununla dakikalık istek sınırından muaf olur; boşsa sitenin kendisi de 429 alabilir |
| `TRUSTED_PROXY_HOPS` | Render'da | `1` (blueprint ayarlar): gerçek ziyaretçi IP'si Render'ın eklediği `X-Forwarded-For` değerinden okunur |
| `RATE_LIMIT_PER_MINUTE` | — | IP başına dakikalık kota (varsayılan 120; olasılık 5, maç detayı 3, arama 2 sayılır). `0` kapatır |
| `FOOTBALL_DATA_API_KEY` | futbol için | https://www.football-data.org/client/register (ücretsiz: 12 lig, 10 istek/dk, skorlar gecikmeli) |
| `THESPORTSDB_API_KEY` | Süper Lig için | **Ücretli** anahtar; açık geliştirme anahtarı `123` canlıda yok sayılır |
| `BALLDONTLIE_API_KEY` | NBA için | https://app.balldontlie.io (ücretsiz: 5 istek/dk, kadro yok) |
| `NEWS_FEEDS` | — | **Tanımlamayın**: varsayılan, koşulları kontrol edilmiş akış listesi kullanılır. `[]` haberleri kapatır |
| `NEWS_INTERVAL_MINUTES` | — | Haber yenileme aralığı (varsayılan 15) |
| `REDIS_URL` | — | Upstash adresi veya boş |
| `LOG_LEVEL` | — | `info` |

- Eksik veya hatalı değişkende API açılmaz. Hata mesajı **değişkenin adını ve kuralı** söyler,
  değeri yazmaz.
- Anahtarı olmayan sporlar sitede "Bu veri kaynağı henüz yapılandırılmadı" gösterir. Örnek veriye
  düşülmez.
- İlk veri: zamanlayıcı açıldıktan sonraki ilk dakikada her yapılandırılmış kaynak tam
  senkronlanır. Elle tetiklemek için:

  ```bash
  curl -X POST https://<api>.onrender.com/api/v1/admin/sync/football-data -H "X-Admin-Token: $ADMIN_TOKEN"
  curl -X POST https://<api>.onrender.com/api/v1/admin/sync/news -H "X-Admin-Token: $ADMIN_TOKEN"
  ```

- Ücretsiz Render planı boşta uyur. Uyanınca zamanlayıcı yeniden başlar ve tazelik göstergesi
  aradaki gecikmeyi "Veri gecikmeli" olarak gösterir.

### Zamanlayıcı neden yalnızca bir süreçte çalışır

- Her API örneği açılışta `pg_try_advisory_lock` dener. Kilidi alan örnek zamanlayıcıyı başlatır;
  diğerleri yalnızca istek karşılar.
- Kilit, o örnek kapanınca bağlantıyla birlikte bırakılır ve bir sonraki açılan örnek devralır.
- Böylece ölçeklendirmede çift senkron ve çift istek bütçesi harcanmaz (`app/db/dialect.py`).

## 4. Web (Vercel)

1. Vercel → **Add New → Project** → repo, **Root Directory = `web`**. Framework Next.js;
   `web/vercel.json` bölgeyi `fra1` yapar.
2. **Web ortam değişkenleri:**

| Değişken | Zorunlu | Açıklama |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | evet | `https://<api>.onrender.com` |
| `AUTH_SECRET` | girişi kullanacaksanız | `npx auth secret` |
| `API_TOKEN_SECRET` | girişi kullanacaksanız | API'dekiyle aynı |
| `INTERNAL_API_KEY` | **evet** | API'dekiyle aynı; yalnızca sunucuda kullanılır, tarayıcıya gitmez |
| `NEXT_PUBLIC_SITE_URL` | — | Sitenin adresi (paylaşım kartları, sitemap). Vercel'de boş bırakılabilir |
| `AUTH_GITHUB_ID` / `AUTH_GITHUB_SECRET` | girişi kullanacaksanız | `docs/AUTH-SETUP.md` |
| `AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` | — | isteğe bağlı |
| `ADMIN_ACCOUNT_IDS` | — | `/admin/status`'u görebilecek hesaplar, ör. `github:12345` |
| `ADMIN_TOKEN` | `/admin/status` için | API'dekiyle aynı; yalnızca sunucu tarafında kullanılır |

- `ENABLE_DEV_LOGIN` üretimde **etkisizdir** (yalnızca `next dev`).
- Eksik veya yarım giriş ayarında web sunucusu açılmaz (`instrumentation.ts`); mesaj değişken
  adlarını söyler.

## 5. Doğrulama listesi

- [ ] `GET /health`:
  - `"status": "ok"` dönüyor;
  - `database.ok` true;
  - Redis girildiyse `redis.ok` true;
  - `stale_sources` boş.
  - Veritabanına ulaşılamazsa HTTP 503 ve `"down"`; Redis hatası veya gecikmeli kaynak varsa
    `"degraded"`.
- [ ] `python -m app.scripts.check_sources` (Render Shell): her anahtarlı kaynak "yapılandırıldı" ve
  HTTP 200.
- [ ] Sitede hiçbir sayfada "Örnek veri" şeridi yok.
- [ ] Anahtarsız sporlar "yapılandırılmadı" diyor.
- [ ] Her sayfanın altında "Kaynak · Son güncelleme" satırı var.
- [ ] `/news` kartlarında kaynak adı var ve tıklayınca yayıncıya gidiyor.
- [ ] `/sources`, `/about`, `/privacy` açılıyor; alt bilgide atıflar var.
- [ ] `/admin/status` yalnızca `ADMIN_ACCOUNT_IDS` hesaplarına açılıyor (diğerlerine 404).
