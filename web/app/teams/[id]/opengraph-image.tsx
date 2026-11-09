import { api } from "@/lib/api";
import { initLocale, t } from "@/lib/i18n";
import {
  ACCENT,
  kitColor,
  OG_SIZE,
  OG_TYPE,
  OgSubtitle,
  OgTitle,
  ogCard,
  PRIMARY,
  OgColumn,
} from "@/lib/og";
import { siteUrl } from "@/lib/site";

export const size = OG_SIZE;
export const contentType = OG_TYPE;
export const alt = "Just Sport";

type Props = { params: Promise<{ id: string }> };

/** Club name on its own colours. */
export default async function Image({ params }: Props) {
  await initLocale();
  const footer = new URL(siteUrl()).host;
  const team = await api.team(Number((await params).id)).catch(() => null);
  if (!team) return ogCard(<OgTitle>{t().app.tagline}</OgTitle>, { footer });
  const main = kitColor(team.color, PRIMARY);
  const second = kitColor(team.alternate_color, ACCENT);
  return ogCard(
    <OgColumn>
      <div style={{ display: "flex", width: 320, height: 16, marginBottom: 36 }}>
        <div
          style={{
            display: "flex",
            flex: 3,
            background: main,
            borderRadius: "8px 0 0 8px",
          }}
        />
        <div
          style={{
            display: "flex",
            flex: 2,
            background: second,
            borderRadius: "0 8px 8px 0",
          }}
        />
      </div>
      <OgTitle size={team.name.length > 22 ? 72 : 96}>{team.name}</OgTitle>
      <OgSubtitle>
        {[team.country, t().share.teamLine].filter(Boolean).join(" · ")}
      </OgSubtitle>
    </OgColumn>,
    { footer, glow: [main, second] },
  );
}
