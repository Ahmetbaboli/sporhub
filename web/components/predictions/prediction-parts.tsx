"use client";

import { Check, Lock, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, useSyncExternalStore } from "react";
import { LocalTime } from "@/components/sport/local-time";
import { TeamBadge } from "@/components/sport/team-badge";
import { useT } from "@/lib/i18n/client";
import {
  awaitingResult,
  clampGoals,
  EXACT_POINTS,
  type FinishedScore,
  history,
  isLocked,
  OUTCOME_POINTS,
  type Prediction,
  readPredictions,
  removePrediction,
  savePrediction,
  serverPredictions,
  settle,
  subscribePredictions,
  tally,
  writePredictions,
} from "@/lib/predictions";
import type { SportEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

export function usePredictions() {
  return useSyncExternalStore(subscribePredictions, readPredictions, serverPredictions);
}

const noSubscription = () => () => {};
/** False on the server and first paint, so locked/unlocked never mismatches on hydration. */
function useMounted(): boolean {
  return useSyncExternalStore(
    noSubscription,
    () => true,
    () => false,
  );
}

const GOAL_INPUT =
  "bg-background h-10 w-10 rounded-md sm:w-12 border text-center text-lg font-bold tabular-nums disabled:opacity-60";

/** One upcoming match with two score boxes; saved on every change. */
export function PredictionRow({ event }: { event: SportEvent }) {
  const m = useT();
  const all = usePredictions();
  const mounted = useMounted();
  const saved = all[event.id];
  const home = event.participants.find((x) => x.side === "home")?.team;
  const away = event.participants.find((x) => x.side === "away")?.team;
  const [draft, setDraft] = useState<{ home: string; away: string } | null>(null);
  if (!home || !away) return null;

  const locked = mounted && isLocked(event.start_time);
  const shown = draft ?? {
    home: saved ? String(saved.home) : "",
    away: saved ? String(saved.away) : "",
  };

  const change = (side: "home" | "away", value: string) => {
    const next = { ...shown, [side]: value };
    setDraft(next);
    const h = clampGoals(next.home);
    const a = clampGoals(next.away);
    if (h === null || a === null) return;
    savePrediction({
      eventId: event.id,
      home: h,
      away: a,
      kickoff: event.start_time,
      homeName: home.name,
      awayName: away.name,
      competition: event.competition.name,
    });
  };

  const label = (team: string) => m.predict.goalsOf(team);
  return (
    <li className="flex flex-wrap items-center gap-x-2 gap-y-1 px-3 py-2.5 sm:flex-nowrap sm:gap-3">
      <LocalTime
        iso={event.start_time}
        className="text-muted-foreground w-full shrink-0 text-xs tabular-nums sm:w-11"
      />
      <Link
        href={`/teams/${home.id}`}
        className="flex min-w-0 flex-1 items-center justify-end gap-2 text-right text-sm font-medium"
      >
        <TeamName team={home} />
        <TeamBadge team={home} size="sm" />
      </Link>
      <div className="flex shrink-0 items-center gap-1">
        <input
          type="number"
          inputMode="numeric"
          min={0}
          max={20}
          aria-label={label(home.name)}
          value={shown.home}
          disabled={locked}
          onChange={(e) => change("home", e.target.value)}
          className={GOAL_INPUT}
        />
        <span className="text-muted-foreground">–</span>
        <input
          type="number"
          inputMode="numeric"
          min={0}
          max={20}
          aria-label={label(away.name)}
          value={shown.away}
          disabled={locked}
          onChange={(e) => change("away", e.target.value)}
          className={GOAL_INPUT}
        />
      </div>
      <Link
        href={`/teams/${away.id}`}
        className="flex min-w-0 flex-1 items-center gap-2 text-sm font-medium"
      >
        <TeamBadge team={away} size="sm" />
        <TeamName team={away} />
      </Link>
      <span className="w-5 shrink-0" aria-live="polite">
        {locked ? (
          <Lock aria-label={m.predict.locked} className="text-muted-foreground size-4" />
        ) : saved ? (
          <Check aria-label={m.predict.saved} className="text-primary size-4" />
        ) : null}
      </span>
    </li>
  );
}

/** Short code on phones (GAL, AMED), full name from the small breakpoint up. */
function TeamName({ team }: { team: { name: string; short_name: string | null } }) {
  return (
    <>
      <span className="truncate sm:hidden">{team.short_name ?? team.name}</span>
      <span className="hidden truncate sm:inline">{team.name}</span>
    </>
  );
}

/** Asks for the results of started matches once, then stores the points. */
function useSettleResults() {
  const all = usePredictions();
  const ids = useMounted() ? awaitingResult(all).join(",") : "";
  useEffect(() => {
    if (!ids) return;
    const controller = new AbortController();
    fetch(`/api/prediction-results?ids=${ids}`, { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : { finished: [] }))
      .then((body: { finished: FinishedScore[] }) => {
        const current = readPredictions();
        const next = settle(current, body.finished);
        if (next !== current) writePredictions(next);
      })
      .catch(() => {});
    return () => controller.abort();
  }, [ids]);
}

export function PredictionScoreboard() {
  const m = useT();
  const all = usePredictions();
  useSettleResults();
  const t = tally(all);
  const cells = [
    { label: m.predict.points, value: t.points, strong: true },
    { label: m.predict.exact, value: t.exact },
    { label: m.predict.outcome, value: t.outcome },
    { label: m.predict.pending, value: t.pending },
  ];
  return (
    <section aria-label={m.predict.summary} className="bg-card rounded-xl border p-4">
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {cells.map((c) => (
          <div key={c.label}>
            <dt className="text-muted-foreground text-xs font-semibold uppercase">
              {c.label}
            </dt>
            <dd
              className={cn(
                "font-display tabular-nums",
                c.strong ? "text-primary text-4xl font-bold" : "text-3xl font-semibold",
              )}
            >
              {c.value}
            </dd>
          </div>
        ))}
      </dl>
      <p className="text-muted-foreground mt-3 text-xs">
        {m.predict.rules(EXACT_POINTS, OUTCOME_POINTS)} · {m.predict.deviceOnly}
      </p>
    </section>
  );
}

function PointsBadge({ p }: { p: Prediction }) {
  const m = useT();
  if (!p.result)
    return (
      <span className="text-muted-foreground rounded-full border px-2 py-0.5 text-xs">
        {m.predict.waiting}
      </span>
    );
  const pts = p.result.points;
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-xs font-bold tabular-nums",
        pts === EXACT_POINTS
          ? "bg-primary text-primary-foreground"
          : pts > 0
            ? "bg-accent/20 text-foreground"
            : "bg-muted text-muted-foreground",
      )}
    >
      +{pts}
    </span>
  );
}

export function PredictionHistory() {
  const m = useT();
  const list = history(usePredictions());
  const mounted = useMounted();
  if (!mounted) return null;
  if (list.length === 0)
    return <p className="text-muted-foreground text-sm">{m.predict.noHistory}</p>;
  return (
    <ul className="bg-card divide-y rounded-lg border">
      {list.map((p) => (
        <li key={p.eventId} className="flex items-center gap-3 px-3 py-2.5 text-sm">
          <div className="min-w-0 flex-1">
            <Link href={`/matches/${p.eventId}`} className="font-medium hover:underline">
              {p.homeName} – {p.awayName}
            </Link>
            <p className="text-muted-foreground text-xs">
              {p.competition} · {m.predict.yourGuess(p.home, p.away)}
              {p.result ? ` · ${m.predict.final(p.result.home, p.result.away)}` : ""}
            </p>
          </div>
          <PointsBadge p={p} />
          {!isLocked(p.kickoff) ? (
            <button
              type="button"
              onClick={() => removePrediction(p.eventId)}
              aria-label={m.predict.remove(p.homeName, p.awayName)}
              className="text-muted-foreground hover:text-foreground"
            >
              <Trash2 className="size-4" aria-hidden />
            </button>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
