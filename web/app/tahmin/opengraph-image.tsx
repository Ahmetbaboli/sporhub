import { initLocale, t } from "@/lib/i18n";
import { OG_SIZE, OG_TYPE, OgSubtitle, OgTitle, ogCard, OgColumn } from "@/lib/og";
import { siteUrl } from "@/lib/site";

export const size = OG_SIZE;
export const contentType = OG_TYPE;
export const alt = "Just Sport";

export default async function Image() {
  await initLocale();
  return ogCard(
    <OgColumn>
      <OgTitle size={110}>{t().predict.title}</OgTitle>
      <OgSubtitle>{t().share.predictLine}</OgSubtitle>
    </OgColumn>,
    { footer: new URL(siteUrl()).host },
  );
}
