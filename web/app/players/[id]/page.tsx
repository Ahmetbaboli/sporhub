import type { Metadata } from "next";
import Link from "next/link";
import { TeamBadge } from "@/components/sport/team-badge";
import { api } from "@/lib/api";
import { orNotFound, parseId } from "@/lib/api-helpers";
import { formatDate } from "@/lib/format";
import { tr } from "@/lib/i18n/tr";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const player = await api.player(parseId(id)).catch(() => null);
  return { title: player?.name ?? tr.app.name };
}

export default async function PlayerPage({ params }: Props) {
  const player = await orNotFound(api.player(parseId((await params).id)));
  const birth =
    typeof player.extra.date_of_birth === "string" ? player.extra.date_of_birth : null;

  const facts: [string, React.ReactNode][] = [
    [tr.player.position, player.position ?? tr.player.unknown],
    [tr.player.nationality, player.nationality ?? tr.player.unknown],
    [tr.player.birthDate, birth ? formatDate(birth) : tr.player.unknown],
    [
      tr.player.team,
      player.team ? (
        <Link
          href={`/teams/${player.team.id}`}
          className="flex items-center gap-2 hover:underline"
        >
          <TeamBadge team={player.team} size="sm" />
          {player.team.name}
        </Link>
      ) : (
        tr.player.unknown
      ),
    ],
  ];

  return (
    <>
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {player.name}
      </h1>
      <dl className="bg-card mt-6 grid max-w-xl gap-px overflow-hidden rounded-lg border sm:grid-cols-2">
        {facts.map(([label, value]) => (
          <div key={label} className="p-4">
            <dt className="text-muted-foreground text-xs font-semibold uppercase">
              {label}
            </dt>
            <dd className="mt-1 text-base font-medium">{value}</dd>
          </div>
        ))}
      </dl>
    </>
  );
}
