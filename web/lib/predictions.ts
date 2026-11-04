/**
 * Score prediction game. Everything lives in this browser (localStorage): no account, nothing
 * is sent anywhere. Exact score = 3 points, right outcome (win/draw/loss) = 1, otherwise 0.
 */
import type { SportEvent } from "@/lib/types";

export const PREDICTIONS_KEY = "js:predictions:v1";
export const EXACT_POINTS = 3;
export const OUTCOME_POINTS = 1;
export const MAX_GOALS = 20;
/** Upper bound on matches asked for in one results request. */
export const RESULTS_BATCH = 40;

export interface Score {
  home: number;
  away: number;
}

export interface Prediction extends Score {
  eventId: number;
  kickoff: string;
  homeName: string;
  awayName: string;
  competition: string;
  /** Set once the match is finished: the real score and the points won. */
  result?: Score & { points: number };
}

export type Predictions = Record<string, Prediction>;

const outcome = (s: Score) => Math.sign(s.home - s.away);

export function pointsFor(guess: Score, real: Score): number {
  if (guess.home === real.home && guess.away === real.away) return EXACT_POINTS;
  return outcome(guess) === outcome(real) ? OUTCOME_POINTS : 0;
}

export function clampGoals(value: string): number | null {
  if (value.trim() === "") return null;
  const n = Number(value);
  if (!Number.isInteger(n) || n < 0) return null;
  return Math.min(n, MAX_GOALS);
}

export function isLocked(kickoff: string, now: number = Date.now()): boolean {
  return Date.parse(kickoff) <= now;
}

export interface Tally {
  points: number;
  settled: number;
  exact: number;
  outcome: number;
  pending: number;
}

export function tally(all: Predictions): Tally {
  const t: Tally = { points: 0, settled: 0, exact: 0, outcome: 0, pending: 0 };
  for (const p of Object.values(all)) {
    if (!p.result) {
      t.pending += 1;
      continue;
    }
    t.settled += 1;
    t.points += p.result.points;
    if (p.result.points === EXACT_POINTS) t.exact += 1;
    else if (p.result.points === OUTCOME_POINTS) t.outcome += 1;
  }
  return t;
}

/** Predictions whose match has started but whose result is not known yet. */
export function awaitingResult(all: Predictions, now: number = Date.now()): number[] {
  return Object.values(all)
    .filter((p) => !p.result && isLocked(p.kickoff, now))
    .map((p) => p.eventId)
    .slice(0, RESULTS_BATCH);
}

export interface FinishedScore extends Score {
  eventId: number;
}

/** Final score of a finished two-sided match, else null. */
export function finishedScore(event: SportEvent): FinishedScore | null {
  if (event.status !== "finished") return null;
  const home = event.participants.find((p) => p.side === "home")?.score;
  const away = event.participants.find((p) => p.side === "away")?.score;
  if (home == null || away == null) return null;
  return { eventId: event.id, home, away };
}

export function settle(all: Predictions, finished: FinishedScore[]): Predictions {
  let next = all;
  for (const f of finished) {
    const p = all[f.eventId];
    if (!p || p.result) continue;
    if (next === all) next = { ...all };
    const real = { home: f.home, away: f.away };
    next[f.eventId] = { ...p, result: { ...real, points: pointsFor(p, real) } };
  }
  return next;
}

/** Newest kickoff first. */
export function history(all: Predictions): Prediction[] {
  return Object.values(all).sort((a, b) => Date.parse(b.kickoff) - Date.parse(a.kickoff));
}

// ---- storage (shared by every component through useSyncExternalStore) ----------------------

const EMPTY: Predictions = {};
const listeners = new Set<() => void>();
let cachedRaw: string | null = null;
let cached: Predictions = EMPTY;
// After a failed write (storage full or blocked) the in-memory copy is the truth for this visit.
let memoryOnly = false;

function parse(raw: string | null): Predictions {
  if (!raw) return EMPTY;
  try {
    const value: unknown = JSON.parse(raw);
    return value && typeof value === "object" ? (value as Predictions) : EMPTY;
  } catch {
    return EMPTY;
  }
}

export function readPredictions(): Predictions {
  if (memoryOnly) return cached;
  let raw: string | null = null;
  try {
    raw = localStorage.getItem(PREDICTIONS_KEY);
  } catch {
    return cached; // storage blocked (private mode): keep the in-memory copy
  }
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    cached = parse(raw);
  }
  return cached;
}

export function serverPredictions(): Predictions {
  return EMPTY;
}

export function writePredictions(next: Predictions): void {
  cached = next;
  try {
    cachedRaw = JSON.stringify(next);
    localStorage.setItem(PREDICTIONS_KEY, cachedRaw);
  } catch {
    memoryOnly = true; // the game still works for this visit
  }
  listeners.forEach((l) => l());
}

export function subscribePredictions(listener: () => void): () => void {
  listeners.add(listener);
  const onStorage = (e: StorageEvent) => {
    if (e.key === PREDICTIONS_KEY) listener();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

export function savePrediction(p: Omit<Prediction, "result">): void {
  const all = readPredictions();
  writePredictions({ ...all, [p.eventId]: { ...p } });
}

export function removePrediction(eventId: number): void {
  const rest = { ...readPredictions() };
  delete rest[eventId];
  writePredictions(rest);
}
