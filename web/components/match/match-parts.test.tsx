import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MatchLineups, MatchStats, MatchTimeline } from "@/components/match/match-parts";
import { EventRow } from "@/components/sport/event-row";
import type { Lineup, MatchDetails } from "@/lib/types";
import { event } from "@/tests/factories";

const player = (number: number, position: string, extra = {}) => ({
  external_id: String(number),
  name: `Player ${number}`,
  number: String(number),
  position,
  subbed_in: false,
  subbed_out: false,
  ...extra,
});

const XI = ["G", "LB", "CD-L", "CD-R", "RB", "LM", "CM-L", "CM-R", "RM", "CF-L", "CF-R"];

const lineup = (side: "home" | "away"): Lineup => ({
  side,
  formation: "4-4-2",
  starters: XI.map((pos, i) => player(i + 1, pos, i === 10 ? { subbed_out: true } : {})),
  substitutes: [player(19, "SUB", { subbed_in: true })],
});

const details: MatchDetails = {
  event_id: 1,
  available: true,
  reason: null,
  source: "espn",
  lineups: [lineup("home"), lineup("away")],
  incidents: [
    {
      minute: "12'",
      kind: "goal",
      side: "home",
      player: "Bukayo Saka",
      related_player: null,
    },
    {
      minute: "40'",
      kind: "yellow_card",
      side: "away",
      player: "Moisés Caicedo",
      related_player: null,
    },
    {
      minute: "70'",
      kind: "substitution",
      side: "home",
      player: "Player 19",
      related_player: "Player 11",
    },
  ],
  stats: [
    { key: "possession", home: 60, away: 40 },
    { key: "shots", home: 14, away: 9 },
  ],
  attendance: null,
  fetched_at: null,
};

describe("MatchTimeline", () => {
  it("puts home moments on the left and away moments on the right", () => {
    render(<MatchTimeline incidents={details.incidents} />);
    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(3);
    expect(within(rows[0]).getByText("Bukayo Saka")).toBeInTheDocument();
    expect(within(rows[0]).getByRole("img", { name: "Gol" })).toBeInTheDocument();
    expect(within(rows[1]).getByRole("img", { name: "Sarı kart" })).toBeInTheDocument();
    expect(within(rows[2]).getByText("Player 11")).toBeInTheDocument(); // player off
  });

  it("says so when nothing has happened yet", () => {
    render(<MatchTimeline incidents={[]} />);
    expect(screen.getByText("Henüz önemli bir an yok.")).toBeInTheDocument();
  });
});

describe("MatchStats", () => {
  it("labels stats in Turkish and shows percentages", () => {
    render(<MatchStats stats={details.stats} />);
    expect(screen.getByText("Topa sahip olma")).toBeInTheDocument();
    expect(screen.getByText("%60")).toBeInTheDocument();
    expect(screen.getByText("14")).toBeInTheDocument();
  });
});

describe("MatchLineups", () => {
  it("lists both XIs with formation, substitutes and who came off", () => {
    render(<MatchLineups details={details} event={event()} />);
    expect(screen.getAllByText("Diziliş: 4-4-2")).toHaveLength(2);
    expect(screen.getAllByText("Yedekler")).toHaveLength(2);
    expect(screen.getAllByLabelText("Çıkan").length).toBeGreaterThan(0);
    expect(screen.getAllByLabelText("Giren").length).toBeGreaterThan(0);
  });
});

describe("EventRow match link", () => {
  it("links the score to the match page", () => {
    render(
      <ul>
        <EventRow event={event({ id: 42 })} />
      </ul>,
    );
    expect(screen.getByRole("link", { name: /Maç detayı/ })).toHaveAttribute(
      "href",
      "/matches/42",
    );
  });

  it("does not link races", () => {
    render(
      <ul>
        <EventRow event={event({ kind: "race" })} />
      </ul>,
    );
    expect(screen.queryByRole("link", { name: /Maç detayı/ })).not.toBeInTheDocument();
  });
});
