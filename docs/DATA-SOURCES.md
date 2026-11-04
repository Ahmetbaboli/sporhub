# Veri kaynakları

Her limit ve koşul, belirtilen sayfadan **2026-11-02** tarihinde okundu. "Doğrulanamadı" yazan
maddeler resmî sayfada bulunamadı veya sayfa açılmadı; bu durumda en temkinli varsayım uygulanır.
Koşullar değişebilir: canlıya almadan önce bağlantıları yeniden okuyun.

## Özet

| Kaynak | Spor | Anahtar | Doğrulanmış limit | Kullanılan |
| --- | --- | --- | --- | --- |
| football-data.org v4 | Futbol (12 ücretsiz lig) | `FOOTBALL_DATA_API_KEY` | 10 istek/dk, skorlar **gecikmeli** | Evet |
| TheSportsDB v1 | Süper Lig, TFF 1. Lig | `THESPORTSDB_API_KEY` (ücretli) | Ücretli 100 istek/dk | Evet (yalnızca ücretli anahtarla) |
| API-Football (API-Sports) | Süper Lig | — | Ücretsiz 100 istek/gün, eski sezonlar | Hayır |
| balldontlie v1 | NBA | `BALLDONTLIE_API_KEY` | Ücretsiz 5 istek/dk | Evet |
| ESPN site API (resmî olmayan) | Süper Lig | yok (`ESPN_ENABLED=true`) | belgelenmemiş; biz 20/dk, 200/saat | İsteğe bağlı, kişisel kullanım |
| Jolpica-F1 | Formula 1 | yok | 4 istek/sn, 500 istek/saat | Evet |
| RSS/Atom akışları | Haber | yok | yayıncıya göre | Evet, aşağıdaki liste |

## football-data.org (futbol)

- **Ücretsiz katmandaki 12 lig:** CL, PPL, PL, DED, BL1, FL1, SA, PD, ELC, BSA, WC, EC.
  - Kapsam: https://www.football-data.org/coverage
  - Canlı doğrulama: `GET /v4/competitions` yanıtında bu liglerin `plan` değeri `TIER_ONE`.
  - Adapter yalnızca `plan == TIER_ONE` olan ligleri döndürür.
- **Limit:** "Registered clients are allowed for 10 requests/minute in the free plan." Kayıtlı
  istemciler için günlük limit belirtilmemiş.
  - Kaynak: https://docs.football-data.org/general/v4/policies.html
- **Skorlar ücretsiz planda gecikmeli** ("Scores delayed", "Schedules delayed"). Canlı skor ayrı bir
  plan (€12/ay).
  - Kaynak: https://www.football-data.org/pricing
  - Arayüzdeki karşılığı: canlı maçlarda "skor gecikmeli olabilir" notu gösterilir.
- **Kimlik ve kota başlıkları:** kimlik `X-Auth-Token`; kalan kota `X-RequestsAvailable` ve
  `X-RequestCounter-Reset` başlıklarında gelir.
  - Kaynak: https://docs.football-data.org/general/v4/lookup_tables.html
- **Süper Lig (TSL) ve 1. Lig (T1L):** ücretli katmanlarda (TIER_THREE / TIER_FOUR).
  - TSL için Advanced €99/ay gerektiği resmî tabloya dayanan çıkarımdır, doğrulanamadı.
  - Kaynak: https://www.football-data.org/pricing
- **Gol krallığı (`/scorers`):** ücretsiz planda **çalışıyor**. 2026-11-02 gerçek senkronunda
  PL için 50 satır geldi. Adapter yine de 401/403/404'te senkronu düşürmeden boş döner.
- **Atıf:** eski koşul sayfası açılmadı (404). Arama özetine göre istenen ifade "Football data
  provided by the Football-Data.org API"; bu ifade `/sources` sayfasında ve alt bilgide kullanılır.
- **Arma (crest) URL'leri:** gösterim izni doğrulanamadı → **gösterilmez**, baş harfli yer tutucu
  kullanılır.

## Süper Lig sağlayıcı karşılaştırması

| Sağlayıcı | Güncel sezon (2026/27) ücretsiz mi | Limit | Koşul | Karar |
| --- | --- | --- | --- | --- |
| **TheSportsDB** (lig 4339, 1. Lig 4676) | Kısmen | Ücretsiz 30/dk, Premium 100/dk | Ücretsiz: yalnızca geliştirme | **Seçildi (Premium)** |
| API-Football (lig 203/204) | **Hayır** | 100/gün | Yayın lisansı kullanıcıda | Elendi |
| football-data.org | Hayır | — | — | Elendi |
| Sportmonks | Hayır | — | — | Elendi |
| **ESPN site API** (`tur.1`) | **Evet** (2026/27: 297 maç, 18 takımlı tablo) | Belgelenmemiş | Resmî ürün değil, koşul yayımlanmamış | **İsteğe bağlı** (`ESPN_ENABLED`) |
| FotMob / SofaScore iç API'leri | Evet | Belgelenmemiş | Otomatik erişimi yasaklıyor/koruyor | Elendi |
| TFF resmî sitesi | Evet | — | Yalnızca HTML (kazıma) | Elendi |

**ESPN (2026-11-03, canlı denendi):** `site.api.espn.com/apis/site/v2/sports/soccer/tur.1/{scoreboard,teams}`
ve `/apis/v2/sports/soccer/tur.1/standings`; anahtar yok. Fikstür `dates=YYYYMM` ile ay ay
(sezon ~12 istek), tablo satırlarında sağlayıcının kendi bölge notu (Şampiyonlar Ligi, küme düşme)
ve takım logoları var. **TFF 1. Lig yok** (`tur.2` boş). ESPN'in kendi web/uygulama arka ucudur,
üçüncü taraflar için koşul ya da limit yayımlanmamıştır: bu yüzden varsayılan kapalı, yalnızca
kişisel/ticari olmayan kullanım için açılır; istek bütçesi bilinçli olarak düşük tutulur.

**ESPN maç özeti (2026-11-04, canlı denendi):** `/apis/site/v2/sports/soccer/tur.1/summary?event=<id>`
bitmiş maçta iki kadroyu (diziliş, ilk 11, yedekler, oyuncu değişikliği bayrakları), `keyEvents`
(gol, kart, değişiklik; dakika ve takım kimliğiyle) ve `boxscore` takım istatistiklerini
(topa sahip olma, şut, korner, faul, pas…) veriyor; maç öncesi kadro ve olay boş, istatistik yerine
sezon toplamları geliyor (kullanılmaz). Sync'e girmez, yalnızca maç sayfası açılınca istenir
(aynı `espn` bütçesinden) ve önbelleğe alınır (bkz. DECISIONS 2026-11-04). Değişiklikte
`participants` sırası [giren, çıkan]; `attendance` bilinmiyorsa 0 (gösterilmez).

Satır ayrıntıları:

- **TheSportsDB**
  - Ücretsiz anahtar güncel sezonu veriyor ama ucu başına kesik sonuç dönüyor: puan tablosu 5
    satır, sezon maçları 15, sıradaki/geçmiş maç 1.
  - Livescore yalnızca Premium ($9/ay, 2 dk gecikmeli).
- **API-Football:** ücretsiz plan yalnızca 2022–2024 sezonlarını açıyor. Sayfalar 403 verdi; bilgi
  resmî sayfaların arama özetlerinden alındı.
- **football-data.org:** Süper Lig ~€99/ay (çıkarım, doğrulanamadı).
- **Sportmonks:** ücretsiz plan yalnızca Danimarka ve İskoçya liglerini kapsıyor.

**TheSportsDB ayrıntıları**

- **Uçlar:** base `https://www.thesportsdb.com/api/v1/json/{key}/`.
  - `lookuptable.php?l=4339&s=2026-2027`
  - `eventsseason.php?id=4339&s=2026-2027`
  - `eventspastleague.php`, `eventsnextleague.php`, `lookupleague.php`
  - Limitler: ücretsiz 30/dk, Premium 100/dk, Business 120/dk. Aşılırsa HTTP 429 döner ve bir
    dakika beklenir.
  - Kaynak: https://www.thesportsdb.com/documentation
- **Ücretsiz anahtarla canlı doğrulama (2026-11-02, geliştirme amaçlı birkaç istek):**
  - `lookuptable` 5 satır döndü.
  - `eventsseason` 15 maç döndü.
  - `lookup_all_teams?id=4339` Süper Lig yerine başka bir ligin takımlarını döndürdü.
  - Sonuç: ücretsiz anahtar tam bir lig sayfası için yetersiz ve yanıltıcı.
- **Koşullar** (https://www.thesportsdb.com/docs_terms_of_use.php, son güncelleme 17/09/2026):
  - "You may use our API to lookup data and artwork for your development projects" (ücretsiz).
  - "You may use our API to develop apps and services as long as you stay within the rate limit"
    (ücretli).
  - Atıf zorunlu: "must mention us as the source of the data".
  - "Artwork marked unknown must not be used … publicly", "does not relicense third-party
    photographs, logos".
- **Karar:**
  - Herkese açık sitede yalnızca ücretli anahtar kabul edilir.
  - Herkese açık deneme anahtarı `123` **live modda "yapılandırılmadı" sayılır**: kesik tabloyu tam
    lig gibi göstermemek için.
  - Ücretsiz katman güncel sezonu tam vermiyor; eski sezon güncelmiş gibi gösterilmez.

## balldontlie (NBA)

- **Limit ve uçlar:** ücretsiz 5 istek/dk; yalnızca Teams, Players, Games.
  - ALL-STAR $9.99 (60/dk), GOAT $39.99 (600/dk).
  - Kimlik başlığı `Authorization: <anahtar>`.
  - Kaynak: https://docs.balldontlie.io/
- **Koşullar:** veri "for any lawful personal or commercial purpose", gösterim dahil kullanılabilir.
  Atıf zorunlu değil; ikame API kurmak yasak.
  - Kaynak: https://www.balldontlie.io/terms (§6, §11)
- **Logolar:** takım nesnesinde logo alanı yok; baş harfli yer tutucu kullanılır.
- **Gerçek senkron (2026-11-02):** 2026/27 için 1200 normal sezon maçı geldi. NBA, NBA Cup
  dönemindeki 30 maçı grup aşamasından sonra ilan eder.
- **Kadro ve puan durumu:** kadro (`/players/active`) ve `/standings` ücretli katmanda. Puan durumu
  maçlardan hesaplanır, kadro boş kalabilir.

## Jolpica-F1 (Formula 1)

- **Limit:** "4 requests per second" anlık, "500 requests per hour" sürekli. Aşılırsa 429; limitlerin
  ileride düşebileceği belirtiliyor.
  - Kaynak: https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md
- **User-Agent:** özel bir User-Agent zorunlu.
  - Kaynak: https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md
- **Lisans:** "freely available for non-commercial use"; veri CC BY-NC-SA 4.0. Bu proje ticari
  değildir; atıf `/sources` sayfasında ve alt bilgide.
  - Kaynak: https://github.com/jolpica/jolpica-f1/blob/main/TERMS.md
- **Canlı zamanlama yok;** sonuçlar yarıştan sonra yayımlanır (gecikme süresi doğrulanamadı).
  Arayüz F1'i hiçbir zaman "canlı" göstermez.
- **Görsel yok.**

## Görsel politikası

- Takım logoları ve oyuncu fotoğrafları yalnızca sağlayıcı açıkça izin veriyorsa ve sağlayıcının
  URL'si üzerinden gösterilir. Hiçbir görsel sunucuya indirilmez.
- 2026-11-02 itibarıyla hiçbir sağlayıcı için açık bir hotlink/gösterim izni bulunamadı:
  - football-data: doğrulanamadı.
  - TheSportsDB: kullanıcı yapımı içerik; "does not relicense … logos".
  - balldontlie ve Jolpica: görsel yok.
- NBA logoları: balldontlie'de yok; `abbreviation` → ESPN CDN kodu açık tablosu (30/30 doğrulandı,
  2026-11-03). Haber fotoğrafları: akışın kendi `enclosure`/`media:*` adresi (yalnızca https).
- Bu yüzden takım ve lig görselleri varsayılan olarak **kısaltmalı rozet** ile gösterilir. API `logo_url`
  alanını `SHOW_PROVIDER_IMAGES=true` olmadıkça boş döndürür; aynı anahtar haber fotoğraflarını da
  açar. Sahibi kişisel/portföy kurulumunda (yayın değil) açabilir; herkese açık yayında hak gerekir.
- F1 pist çizimleri: [bacinger/f1-circuits](https://github.com/bacinger/f1-circuits) (MIT, © Tomislav Bacinger), `api/tools/generate_circuits.py` ile SVG; Jolpica `circuitId` açık tabloyla eşlenir.
- Kulüp armaları kulüplerin ticari markasıdır; hiçbir sağlayıcı marka hakkı vermez (balldontlie §11).

## Haber akışları (RSS/Atom)

Akışlar 2026-11-02'de canlı olarak çekildi ve her yayıncının koşulları okundu.

Sitede yalnızca şunlar gösterilir:
- başlık,
- akışın kendi özetinden en fazla 2 cümle (Yahoo için özet değiştirilmeden, sığmıyorsa hiç),
- tarih,
- kaynak adı,
- orijinal habere link.

Görsel, tam metin ve kazıma yok.

**Kullanılanlar (varsayılan `NEWS_FEEDS`):**

| Akış | URL | Dil | Spor |
| --- | --- | --- | --- |
| BBC Sport Football | https://feeds.bbci.co.uk/sport/football/rss.xml | en | futbol |
| BBC Sport Formula 1 | https://feeds.bbci.co.uk/sport/formula1/rss.xml | en | F1 |
| BBC Sport Basketball | https://feeds.bbci.co.uk/sport/basketball/rss.xml | en | basketbol |
| ESPN Soccer | https://www.espn.com/espn/rss/soccer/news | en | futbol |
| ESPN NBA | https://www.espn.com/espn/rss/nba/news | en | basketbol |
| ESPN F1 | https://www.espn.com/espn/rss/f1/news | en | F1 |
| Yahoo Sports NBA | https://sports.yahoo.com/nba/rss/ | en | basketbol |
| Habertürk Spor | https://www.haberturk.com/rss/spor.xml | tr | çok sporlu |
| Sporx | https://www.sporx.com/_xml/rss.php | tr | çok sporlu (ISO-8859-9) |

Koşullar (alıntı ve kaynak):

- **BBC:** "We encourage the use of BBC News feeds as part of a website, however, we do require that
  the proper format and attribution is used." Kaynak: https://www.bbc.co.uk/news/10628494
- **ESPN:** "only permitted to display the content that is provided in the feed, you must link to
  the full article … and you must indicate that the content has been provided by ESPN." Kaynak:
  https://www.espn.com/espn/news/story?page=rssinfo
- **Yahoo:**
  - "only permitted to display the content that is provided in the feed, without modification, and
    you must provide attribution … and link to the full article. You may not incorporate
    advertising."
  - Uygulama: özet kırpılmaz; tek parçada sığmıyorsa hiç gösterilmez. Sitede reklam yok.
  - Kaynak: https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html
- **Habertürk:** alıntı serbest (FSEK m.35 sınırı içinde): "kaynak olarak İnternet Sitesi'nin adı
  açıkça belirtilmeli, alıntı yapılan içeriğe doğrudan ve aktif bağlantı (link) verilmeli". Görselleri
  kullanılamaz. Kaynak: https://www.haberturk.com/kullanim-kosullari
- **Sporx:** "kaynak gösterilmeden kullanılamaz, çoğaltılamaz ve yayınlanamaz", yani kaynak
  gösterilerek kullanım mümkün. Kaynak: https://www.sporx.com/hakkimizda/yasal_uyari.php

**Koşullu (varsayılanda kapalı):**
- The Guardian (football/F1/NBA) ve CNN Türk Spor.
- Koşulları "personal, non-commercial" kullanım diyor; başka bir sitede gösterimi açıkça kapsamıyor.
- Kaynaklar: https://www.theguardian.com/help/feeds, https://www.cnnturk.com/yasal-uyari/

**Kullanılmayanlar (yeniden yayını açıkça yasaklıyor):**

| Yayıncı | Koşul sayfası |
| --- | --- |
| Anadolu Ajansı | https://www.aa.com.tr/tr/p/yasal-uyari |
| Hürriyet | https://www.hurriyet.com.tr/kullanim-kosullari/ |
| NTV Spor | https://www.ntvspor.net/kullanim-kosullari |
| TRT Haber | https://www.trthaber.com/kullanim-sartlari.html |
| Sözcü | https://www.sozcu.com.tr/rss-servisleri |
| Star | https://www.star.com.tr/rss/ |
| Mynet | https://www.mynet.com/yasal-uyari |
| Motorsport.com / Autosport | https://www.motorsport.com/info/terms-of-use/ |
| The Race | https://www.the-race.com/terms-and-conditions/ |
| CBS Sports | https://legalterms.cbsinteractive.com/terms-of-use |

**Belirsiz (koşul bulunamadı, kullanılmıyor):**
- Sky Sports, Eurohoops, RaceFans, The Independent, Daily Sabah, Cumhuriyet, Yeni Şafak,
  Sabah/A Haber/Takvim, Ajansspor.
- Formula1.com: yalnızca F1.com'dan oluşan bir toplama sayfası koşullarla yasak, öğelerde tarih yok.

**Resmî akışlar:** TFF, UEFA, FIFA, NBA.com, Premier League ve EuroLeague'in çalışan herkese açık RSS
akışı bulunamadı (404/403/429).
