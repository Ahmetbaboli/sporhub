# Giriş (OAuth) kurulumu

Just Sport, giriş için Auth.js v5 kullanır. Kullanıcı verisi API'dedir: web, giriş yapan
kullanıcı için her istekte kısa ömürlü bir token imzalar ve API bu token'ı doğrular.

Giriş ayarları eksikse site **girişsiz** çalışır: giriş düğmesi görünmez, hata çıkmaz.

## 1. Ortak sırlar (her ortamda)

| Değişken | Nerede | Değer |
| --- | --- | --- |
| `AUTH_SECRET` | web | Oturum çerezini şifreler. `npx auth secret` veya `openssl rand -base64 33` |
| `API_TOKEN_SECRET` | web **ve** api (aynı değer) | En az 32 karakter rastgele. `openssl rand -base64 48` |
| `AUTH_TRUST_HOST` | web | Vercel dışında (Docker/Render/`next start`) `true` |

Bu değerleri yalnızca `.env` / `.env.local` dosyalarına veya barındırma panelinin gizli değişken
alanına yazın. Repoya asla commit etmeyin.

## 2. GitHub OAuth uygulaması

1. GitHub → **Settings → Developer settings → OAuth Apps → New OAuth App**
   (https://github.com/settings/applications/new).
2. Uygulama bilgilerini doldurun:
   - **Application name:** `Just Sport (yerel)` (canlı için ayrı bir uygulama açın).
   - **Homepage URL:**
     - yerel: `http://localhost:3000`
     - canlı: `https://<alan-adınız>`
   - **Authorization callback URL** (birebir aynı olmalı):
     - yerel: `http://localhost:3000/api/auth/callback/github`
     - canlı: `https://<alan-adınız>/api/auth/callback/github`
3. **Register application** → sayfadaki **Client ID** → `AUTH_GITHUB_ID`.
4. **Generate a new client secret** → çıkan değer → `AUTH_GITHUB_SECRET` (bir kez gösterilir).
5. Web'i yeniden başlatın; sağ üstte **Giriş yap** görünür.

> Bir OAuth uygulaması yalnızca **tek** callback URL kabul eder. Yerel ve canlı için iki ayrı
> uygulama açın; her ortama kendi ID/secret çiftini verin.

## 3. Google OAuth istemcisi (isteğe bağlı)

1. https://console.cloud.google.com/ → bir proje seçin/oluşturun.
2. **APIs & Services → OAuth consent screen:**
   - **External** seçin.
   - Uygulama adını, destek e-postasını ve geliştirici e-postasını girin.
   - Kapsamlar için varsayılan `openid`, `email`, `profile` yeterli.
   - Test aşamasında kendinizi **Test users**'a ekleyin; herkese açmak için **Publish app** deyin.
3. **Credentials → Create credentials → OAuth client ID → Web application:**
   - **Authorized JavaScript origins:**
     - yerel: `http://localhost:3000`
     - canlı: `https://<alan-adınız>`
   - **Authorized redirect URIs:**
     - yerel: `http://localhost:3000/api/auth/callback/google`
     - canlı: `https://<alan-adınız>/api/auth/callback/google`
4. Çıkan **Client ID** → `AUTH_GOOGLE_ID`, **Client secret** → `AUTH_GOOGLE_SECRET`.

## 4. Yerel geliştirme

`web/.env.local` (örnek değerlerle, kendi değerlerinizi girin):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
AUTH_SECRET=...
API_TOKEN_SECRET=...            # api/.env içindekiyle aynı
AUTH_GITHUB_ID=...
AUTH_GITHUB_SECRET=...
```

`api/.env`: `API_TOKEN_SECRET=...` (aynı değer).

**Geliştirici girişi.** OAuth uygulaması açmadan "adını yaz, gir" girişi yalnızca şu iki koşul
birlikte sağlanırsa görünür:

- `npm run dev` ile çalıştırma (`NODE_ENV=development`),
- `ENABLE_DEV_LOGIN=true`.

`next build` / `next start` her zaman `NODE_ENV=production` ile çalışır. Bu yüzden üretim
derlemesinde bu giriş **hiçbir ayarla açılmaz**; `web/lib/auth-config.test.ts` bunu garanti eder.

## 5. Canlı ortam

- Web'in barındığı yerde (Vercel/Render) şu değişkenleri gizli değişken olarak girin:
  - `AUTH_SECRET`
  - `API_TOKEN_SECRET`
  - `AUTH_GITHUB_ID`, `AUTH_GITHUB_SECRET` (ve isterseniz Google çifti)
  - `AUTH_TRUST_HOST=true` (Vercel'de gerekmez)
- API'ye aynı `API_TOKEN_SECRET`'ı verin.
- Callback URL'lerinin canlı alan adıyla birebir eşleştiğini kontrol edin. En sık hata `redirect_uri_mismatch`: http/https, `www`, sondaki `/` farkı.

## 6. Yönetici hesabı (`/admin/status`)

1. Kendi hesabınızla giriş yapın.
2. Hesap kimliğiniz `<sağlayıcı>:<hesap numarası>` biçimindedir. GitHub numaranızı şöyle
   öğrenebilirsiniz: `https://api.github.com/users/<kullanıcı-adı>` adresindeki `id` alanı.
   Örnek: `github:12345`.
3. Web ortamına iki değişken ekleyin:
   - `ADMIN_ACCOUNT_IDS=github:12345` (virgülle birden fazla hesap yazılabilir),
   - `ADMIN_TOKEN=<API'deki ADMIN_TOKEN ile aynı>`.
4. `/admin/status` yalnızca bu hesaplara açılır; diğer herkes 404 görür.

## 7. Hesap silme ve gizlilik

- Kullanıcı **Panelim → Hesabımı sil** ile hesabını ve tüm takip listesini kalıcı olarak siler.
  - API ucu: `DELETE /api/v1/me`.
  - Sonrasında oturum kapanır.
- Hangi verinin neden tutulduğu `/privacy` sayfasında anlatılır.
