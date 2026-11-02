import { Star } from "lucide-react";
import Link from "next/link";
import { FavoriteButton } from "@/components/account/favorite-button";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";
import { authEnabled, getViewer } from "@/lib/session";
import type { FavoriteKind } from "@/lib/types";

/**
 * Follow button for a team, player or competition page. Signed-out visitors get a link to the
 * sign-in page; when login is not configured nothing is rendered.
 */
export async function FavoriteToggle({
  kind,
  id,
  name,
  returnTo,
}: {
  kind: FavoriteKind;
  id: number;
  name: string;
  returnTo: string;
}) {
  if (!authEnabled()) return null;
  const viewer = await getViewer();
  if (!viewer) {
    return (
      <Link
        href={`/signin?callbackUrl=${encodeURIComponent(returnTo)}`}
        className="hover:bg-muted bg-card inline-flex h-9 items-center gap-1.5 rounded-md border px-3 text-sm font-medium"
        title={t().account.signInToFollow}
      >
        <Star className="size-4" aria-hidden />
        {t().account.follow}
      </Link>
    );
  }
  const ids = await api.me.favoriteIds(await viewer.token()).catch(() => null);
  if (!ids) return null;
  return (
    <FavoriteButton kind={kind} id={id} name={name} initial={ids[kind].includes(id)} />
  );
}
