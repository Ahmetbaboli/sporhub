import { NewsBox } from "@/components/news/news-parts";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";

const RELATED_LIMIT = 5;

/** Latest headlines tagged with a team or player; renders nothing when there are none. */
export async function RelatedNews({
  kind,
  id,
  name,
}: {
  kind: "team" | "player";
  id: number;
  name: string;
}) {
  const page = await api.news({ [kind]: id, pageSize: RELATED_LIMIT }).catch(() => null);
  if (!page?.items.length) return null;
  return (
    <NewsBox
      title={t().news.newsAbout(name)}
      items={page.items}
      moreHref={`/news?${kind}=${id}`}
    />
  );
}
