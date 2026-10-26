/**
 * All user-facing strings live here so a TR/EN switch (next-intl, Stage 4) only has to
 * replace this one module. Keep keys grouped by screen.
 */
export const tr = {
  app: {
    name: "Just Sport",
    tagline: "Tüm sporlar, tek skor tablosu.",
    description:
      "Futbol, basketbol ve Formula 1 için maçlar, sonuçlar ve puan durumları.",
    skipToContent: "İçeriğe geç",
  },
  nav: {
    home: "Bugün",
    primary: "Ana gezinme",
    search: "Ara",
    searchPlaceholder: "Takım, oyuncu veya lig ara…",
    searchLabel: "Site içi arama",
    toggleTheme: "Temayı değiştir",
    themeLight: "Açık tema",
    themeDark: "Koyu tema",
  },
  sports: {
    football: "Futbol",
    basketball: "Basketbol",
    "formula-1": "Formula 1",
    comingSoon: "Yakında",
    comingSoonBody: "Bu spor için veri kaynağı henüz bağlanmadı.",
  },
  home: {
    title: "Bugünün karşılaşmaları",
    subtitle: "Saatler kendi saat diliminize göre gösterilir.",
    emptyTitle: "Bugün karşılaşma yok",
    emptyBody: "Bugün için planlanmış etkinlik bulunamadı. Liglere göz atabilirsiniz.",
  },
  sport: {
    competitions: "Ligler",
    upcoming: "Yaklaşan karşılaşmalar",
    noUpcoming: "Yaklaşan karşılaşma yok.",
    noCompetitions: "Bu sporda henüz lig yok.",
  },
  competition: {
    season: "Sezon",
    tabs: { fixtures: "Fikstür", results: "Sonuçlar", standings: "Puan Tablosu" },
    tabsLabel: "Lig bölümleri",
    noFixtures: "Yaklaşan karşılaşma yok.",
    noResults: "Henüz oynanmış karşılaşma yok.",
    noStandings: "Puan tablosu henüz yayınlanmadı.",
    round: "Hafta",
  },
  standings: {
    caption: "Puan durumu",
    position: "Sıra",
    team: "Takım",
    played: "O",
    won: "G",
    drawn: "B",
    lost: "M",
    goalsFor: "AG",
    goalsAgainst: "YG",
    goalDifference: "AV",
    points: "P",
    form: "Form",
    legend:
      "O: Oynanan · G: Galibiyet · B: Beraberlik · M: Mağlubiyet · AV: Averaj · P: Puan",
  },
  event: {
    live: "Canlı",
    finished: "MS",
    scheduled: "Planlandı",
    postponed: "Ertelendi",
    cancelled: "İptal",
    versus: "karşı",
    venue: "Stadyum",
  },
  team: {
    squad: "Kadro",
    recent: "Son maçlar",
    upcoming: "Gelecek maçlar",
    noRecent: "Oynanmış maç yok.",
    noUpcoming: "Planlanmış maç yok.",
    noSquad: "Kadro bilgisi yok.",
    country: "Ülke",
    positions: {
      goalkeeper: "Kaleciler",
      defence: "Defans",
      midfield: "Orta saha",
      offence: "Forvet",
      other: "Diğer",
    },
  },
  player: {
    position: "Pozisyon",
    nationality: "Uyruk",
    team: "Takım",
    birthDate: "Doğum tarihi",
    unknown: "Bilinmiyor",
  },
  search: {
    title: "Arama",
    resultsFor: (q: string) => `“${q}” için sonuçlar`,
    competitions: "Ligler",
    teams: "Takımlar",
    players: "Oyuncular",
    empty: (q: string) => `“${q}” için sonuç bulunamadı.`,
    prompt: "Aramak için en az 2 karakter girin.",
    tooShort: "En az 2 karakter girin.",
  },
  pagination: {
    label: "Sayfalama",
    previous: "Önceki",
    next: "Sonraki",
    page: (n: number, total: number) => `Sayfa ${n} / ${total}`,
  },
  states: {
    loading: "Yükleniyor…",
    errorTitle: "Bir şeyler ters gitti",
    errorBody: "Veriler şu anda alınamadı. Birkaç saniye sonra tekrar deneyin.",
    retry: "Tekrar dene",
    notFoundTitle: "Sayfa bulunamadı",
    notFoundBody: "Aradığınız sayfa taşınmış ya da hiç var olmamış olabilir.",
    backHome: "Ana sayfaya dön",
  },
  footer: {
    note: "Veriler üçüncü taraf kaynaklardan derlenir; gösterim amaçlı örnek veri içerebilir.",
    openSource: "Açık kaynak · MIT lisansı",
  },
} as const;

export type Messages = typeof tr;
export const t = tr;
