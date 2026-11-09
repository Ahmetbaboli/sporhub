import { api, DEFAULT_TIME_ZONE } from "@/lib/api";
import { formatDay, formatTime } from "@/lib/format";
import { initLocale, intlLocale, t } from "@/lib/i18n";
import {
  ACCENT,
  kitColor,
  OG_COLORS,
  OG_SIZE,
  OG_TYPE,
  OgTeam,
  OgTitle,
  ogCard,
  PRIMARY,
} from "@/lib/og";
import { siteUrl } from "@/lib/site";

export const size = OG_SIZE;
export const contentType = OG_TYPE;
export const alt = "Just Sport";

type Props = { params: Promise<{ id: string }> };

/** Score (or kick-off) between the two clubs, in their colours. */
export default async function Image({ params }: Props) {
  await initLocale();
  const footer = new URL(siteUrl()).host;
  const event = await api.event(Number((await params).id)).catch(() => null);
  const home = event?.participants.find((p) => p.side === "home");
  const away = event?.participants.find((p) => p.side === "away");
  if (!event || !home?.team || !away?.team) {
    return ogCard(<OgTitle>{t().app.tagline}</OgTitle>, { footer });
  }
  const homeColor = kitColor(home.team.color, PRIMARY);
  const awayColor = kitColor(away.team.color, ACCENT);
  const played = event.status === "finished" || event.status === "live";
  const locale = intlLocale();
  const center = played
    ? `${home.score ?? 0} – ${away.score ?? 0}`
    : formatTime(event.start_time, DEFAULT_TIME_ZONE, locale);
  const below = played
    ? t().event[event.status]
    : formatDay(event.start_time, DEFAULT_TIME_ZONE, locale);
  const eyebrow = [
    event.competition.name,
    event.round ? `${t().competition.round} ${event.round}` : null,
  ]
    .filter(Boolean)
    .join(" · ");
  return ogCard(
    <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
      <OgTeam name={home.team.name} color={homeColor} align="left" />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          minWidth: 300,
        }}
      >
        <div style={{ display: "flex", fontSize: 120, letterSpacing: -4 }}>{center}</div>
        <div
          style={{
            display: "flex",
            marginTop: 8,
            fontSize: 28,
            color: event.status === "live" ? "#FF4D5E" : OG_COLORS.MUTED,
            textTransform: "uppercase",
          }}
        >
          {below}
        </div>
      </div>
      <OgTeam name={away.team.name} color={awayColor} align="right" />
    </div>,
    { eyebrow, footer, glow: [homeColor, awayColor] },
  );
}
