import { initLocale, t } from "@/lib/i18n";
import { OG_SIZE, OG_TYPE, OgSubtitle, OgTitle, ogCard, OgColumn } from "@/lib/og";
import { siteUrl } from "@/lib/site";

export const size = OG_SIZE;
export const contentType = OG_TYPE;
export const alt = "Just Sport";

/** Default share card for every page without its own. */
export default async function Image() {
  await initLocale();
  const { app, share } = t();
  return ogCard(
    <OgColumn>
      <OgTitle size={96}>{app.tagline}</OgTitle>
      <OgSubtitle>{share.siteLine}</OgSubtitle>
    </OgColumn>,
    { footer: new URL(siteUrl()).host },
  );
}
