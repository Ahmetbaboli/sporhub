# Yayına alma rehberi

Hedef: **web → Vercel**, **api → Render**, **veritabanı → Neon**. Bu repo yalnızca yapılandırmayı hazırlar; deploy'u siz yaparsınız.

## 1. Veritabanı (Neon)
1. <https://neon.tech> üzerinde proje oluşturun, bir veritabanı (örn. `justsport`) açın.
2. Bağlantı dizesini kopyalayın: `postgresql://USER:PASS@HOST/justsport?sslmode=require`.
3. API için sürücü önekini ve SSL parametresini değiştirin (asyncpg `sslmode` yerine `ssl` bekler):
   `postgresql+asyncpg://USER:PASS@HOST/justsport?ssl=require`
4. Migration'lar API her açıldığında (`entrypoint.sh`) otomatik çalışır; elle gerekmez.

## 2. API (Render)
1. Repo'yu GitHub'a push'layın.
2. Render → **New → Blueprint** → repo'yu seçin; `render.yaml` okunur ve `justsport-api` servisi oluşur.
3. Dashboard'da `sync: false` değişkenlerini doldurun:
   | Değişken | Değer |
   | --- | --- |
   | `DATABASE_URL` | Neon dizesi (yukarıdaki asyncpg biçimi) |
   | `FOOTBALL_DATA_API_KEY` | football-data.org token'ı (ücretsiz kayıt) |
   | `CORS_ORIGINS` | Vercel adresiniz, örn. `https://justsport.vercel.app` |
   | `REDIS_URL` | İsteğe bağlı (Upstash/Render Key Value). Boşsa bellek içi cache kullanılır |
4. `ADMIN_TOKEN` otomatik üretilir (Render → Environment).
5. Anahtarsız demo için `USE_FIXTURES=true` ve `SEED_ON_START=true` yapın; gerçek veri için `false` bırakın.
6. İlk açılışta veri çekmek için:
   ```bash
   curl -X POST https://<api>.onrender.com/api/v1/admin/sync/football-data -H "X-Admin-Token: <ADMIN_TOKEN>"
   ```
   Zamanlayıcı (`SCHEDULER_ENABLED=true`) sonraki senkronizasyonları 30 dakikada bir yapar. Ücretsiz Render planı boşta uyur; uyanınca zamanlayıcı yeniden başlar.
7. Sağlık: `https://<api>.onrender.com/health`, dokümantasyon: `/docs`.

> football-data.org ücretsiz katmanı dakikada 10 istek verir; ilk tam senkronizasyon 5 lig × 3 istek ≈ 2 dakika sürer. Süper Lig ücretsiz katmanda yoktur.

## 3. Web (Vercel)
1. Vercel → **Add New → Project** → repo'yu seçin, **Root Directory = `web`**. Framework otomatik "Next.js" algılanır (`vercel.json` gerekmez).
2. Ortam değişkeni: `NEXT_PUBLIC_API_URL = https://<api>.onrender.com`.
3. Deploy. Sayfalar istek anında render edilir (`force-dynamic`); API yanıtları Next veri önbelleğinde 60 sn tutulur.
4. Render'daki `CORS_ORIGINS` değerini Vercel alan adınızla güncelleyin (sunucu tarafı istekler CORS'a takılmaz; tarayıcı tarafı eklenirse gerekir).

## 4. Doğrulama listesi
- [ ] `/health` → `{"status":"ok"}`
- [ ] `/api/v1/sports` boş değil
- [ ] Vercel ana sayfası bugünün maçlarını listeliyor
- [ ] `POST /api/v1/admin/sync/football-data` yanlış token ile 401 dönüyor

## Sorun giderme
- **API 503 `admin_disabled`**: `ADMIN_TOKEN` tanımlı değil.
- **Web "API'ye ulaşılamıyor"**: `NEXT_PUBLIC_API_URL` yanlış veya Render servisi uyuyor (ilk istek ~30 sn sürebilir).
- **Migration hatası**: bağlantı dizesinde `postgresql+asyncpg://` öneki ve `?ssl=require` olduğundan emin olun.
