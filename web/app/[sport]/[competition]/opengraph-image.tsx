import { api } from "@/lib/api";
import { initLocale, t } from "@/lib/i18n";
import { OG_SIZE, OG_TYPE, OgRows, OgTitle, ogCard, OgColumn } from "@/lib/og";
import { siteUrl } from "@/lib/site";

export const size = OG_SIZE;
export const contentType = OG_TYPE;
export const alt = "Just Sport";

const ROWS = 3;

type Props = { params: Promise<{ sport: string; competition: string }> };

/** League name and the top of its table. */
export default async function Image({ params }: Props) {
  await initLocale();
  const footer = new URL(siteUrl()).host;
  const { competition } = await params;
  const [detail, standings] = await Promise.all([
    api.competition(competition).catch(() => null),
    api.standings(competition).catch(() => null),
  ]);
  if (!detail) return ogCard(<OgTitle>{t().app.tagline}</OgTitle>, { footer });
  const rows = (standings?.items ?? [])
    .filter((s) => s.team || s.player)
    .slice(0, ROWS)
    .map((s) => ({
      place: s.position,
      name: s.team?.name ?? s.player?.name ?? "",
      value: t().share.points(Math.round(s.points)),
    }));
  const eyebrow = [detail.country, detail.current_season?.year_label]
    .filter(Boolean)
    .join(" · ");
  return ogCard(
    <OgColumn>
      <OgTitle size={detail.name.length > 22 ? 68 : 88}>{detail.name}</OgTitle>
      {rows.length ? <OgRows rows={rows} /> : null}
    </OgColumn>,
    { eyebrow, footer },
  );
}
