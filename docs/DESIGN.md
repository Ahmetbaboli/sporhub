# Tasarım notları

**Kimlik: "skor tabelası + tebeşir çizgisi".** Sade, okunaklı, spora ait; hazır şablon hissi yok.

- **Renk (açık tema):** tebeşir/kâğıt zemin `#f5f2ea`, çim yeşili `#0e4a36` (birincil), canlı vurgusu için sıcak kırmızı-turuncu `#d7340f`.
- **Renk (koyu tema):** gece sahası `#0a100d`, vurgu için fosforlu tebeşir yeşili `#c8f23a`, canlı için `#ff6b4a`.
- Tüm renkler `globals.css` içinde CSS değişkenidir; tema `.dark` sınıfıyla (next-themes) değişir.
- **Tipografi:** başlık ve skorlar için *Barlow Condensed* (stadyum panosu hissi, dar ekranda yer kazandırır), gövde için *Geist*. Skor ve tablolarda `tabular-nums`.
- **Bileşen dili:** ince çizgili kartlar, köşeleri hafif yuvarlak; başlıklar büyük harf. Takım logosu yoksa baş harf rozeti (dış sitelerden logo çekmeye bağımlı değiliz).
- **Canlı durum:** nabız atan nokta + "Canlı" rozeti; `prefers-reduced-motion` ile animasyon kapanır.
- **Mobil öncelikli:** tek sütun, 40 px+ dokunma hedefleri, sticky üst menü, sporlar yatay kaydırılan sekme şeridi. Geniş puan tablosu kendi kapsayıcısında yatay kayar; takım sütunu sabit (sticky) kalır.
- **Erişilebilirlik:** "içeriğe geç" bağlantısı, anlamlı başlık sırası (h1 → h2 → h3), görünür odak halkası, tablolarda `caption`/`scope`, durumlar yalnızca renkle değil metinle de verilir, kaydırılabilir bölgeler klavye ile odaklanabilir, skeleton'larda `role="status"`.
- **Durumlar:** her sayfada `loading.tsx` (skeleton), boş durum (`EmptyState`), hata (`error.tsx` + yeniden dene) ve 404.
- **Metinler:** tek dosyada (`web/lib/i18n/tr.ts`); TR/EN için hazır.
- **Saat:** API UTC verir; kullanıcının tarayıcı saat diliminde gösterilir (ilk render `Europe/Istanbul`, hidrasyon sonrası yerel saat).
