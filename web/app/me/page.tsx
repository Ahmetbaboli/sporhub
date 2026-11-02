import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Suspense } from "react";
import {
  CompetitionPlaceCard,
  PlayerChips,
  SECTION_TITLE,
  TeamActivityCard,
} from "@/components/account/dashboard";
import { DeleteAccountForm } from "@/components/account/delete-account-form";
import { EventCardsSkeleton } from "@/components/sport/skeletons";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { initLocale, t } from "@/lib/i18n";
import { authEnabled, getViewer, type Viewer } from "@/lib/session";

export const dynamic = "force-dynamic";
export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().me.title };
}

export default async function MePage() {
  await initLocale();
  if (!authEnabled()) notFound();
  const viewer = await getViewer();
  if (!viewer) redirect("/signin?callbackUrl=/me");

  return (
    <>
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {viewer.name ? t().me.greeting(viewer.name) : t().me.title}
      </h1>
      <p className="text-muted-foreground mt-1 mb-6 text-sm">{t().me.subtitle}</p>
      <Suspense fallback={<EventCardsSkeleton cards={2} />}>
        <MyDashboard viewer={viewer} />
      </Suspense>
      <section
        aria-labelledby="account-danger"
        className="border-accent/40 bg-card mt-12 max-w-xl rounded-lg border p-4"
      >
        <h2
          id="account-danger"
          className="font-display mb-2 text-xl font-semibold uppercase"
        >
          {t().account.deleteTitle}
        </h2>
        <DeleteAccountForm />
        <p className="text-muted-foreground mt-3 text-xs">
          <Link href="/privacy" className="underline">
            {t().account.privacyLink}
          </Link>
        </p>
      </section>
    </>
  );
}

async function MyDashboard({ viewer }: { viewer: Viewer }) {
  const token = await viewer.token();
  const [dashboard, favorites] = await Promise.all([
    api.me.dashboard(token),
    api.me.favorites(token),
  ]);
  const nothing =
    dashboard.teams.length === 0 &&
    dashboard.competitions.length === 0 &&
    favorites.players.length === 0;

  if (nothing) {
    return (
      <EmptyState title={t().me.emptyTitle} body={t().me.emptyBody}>
        <Link
          href="/football"
          className="text-primary mt-2 text-sm font-medium underline"
        >
          {t().me.browse}
        </Link>
      </EmptyState>
    );
  }
  return (
    <div className="space-y-8">
      {dashboard.teams.length ? (
        <section aria-labelledby="my-teams">
          <h2 id="my-teams" className={SECTION_TITLE}>
            {t().me.myTeams}
          </h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {dashboard.teams.map((activity) => (
              <TeamActivityCard key={activity.team.id} activity={activity} />
            ))}
          </div>
        </section>
      ) : null}
      {favorites.players.length ? (
        <section aria-labelledby="my-players">
          <h2 id="my-players" className={SECTION_TITLE}>
            {t().me.myPlayers}
          </h2>
          <PlayerChips players={favorites.players} />
        </section>
      ) : null}
      {dashboard.competitions.length ? (
        <section aria-labelledby="my-competitions">
          <h2 id="my-competitions" className={SECTION_TITLE}>
            {t().me.myCompetitions}
          </h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {dashboard.competitions.map((place) => (
              <CompetitionPlaceCard key={place.competition.id} place={place} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
