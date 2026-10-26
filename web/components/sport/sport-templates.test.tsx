import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChampionshipTables } from "@/components/sport/championship-tables";
import { ConferenceStandings } from "@/components/sport/conference-standings";
import { EventItem } from "@/components/sport/event-item";
import { groupSquad, positionGroup } from "@/lib/events";
import { templateFor } from "@/lib/sports";
import type { Participant, Player, SportEvent, Standing } from "@/lib/types";
import { competition, event, team } from "@/tests/factories";

const f1 = competition({
  id: 9,
  slug: "formula-1",
  name: "Formula 1",
  sport_slug: "formula-1",
});

const driver = (id: number, name: string): Player => ({
  id,
  name,
  position: "Driver",
  nationality: "British",
  team: null,
  extra: {},
});

function result(position: number, name: string, constructor: string): Participant {
  return {
    team: team(position, constructor, { sport_slug: "formula-1" }),
    player: driver(100 + position, name),
    side: null,
    score: null,
    position,
    points: [25, 18, 15, 12][position - 1] ?? 0,
    extra: {
      driver: name,
      grid: position + 1,
      time: position === 1 ? "1:30:00.000" : "+5.2s",
    },
  };
}

const race = (extra: Partial<SportEvent> = {}): SportEvent => ({
  ...event({ id: 50, kind: "race" }),
  name: "Monaco Grand Prix",
  venue: "Circuit de Monaco, Monte-Carlo, Monaco",
  round: "8",
  competition: f1,
  participants: [
    result(1, "Max Verstappen", "Red Bull"),
    result(2, "Lando Norris", "McLaren"),
    result(3, "Oscar Piastri", "McLaren"),
    result(4, "Charles Leclerc", "Ferrari"),
  ],
  extra: { sessions: { qualifying: "2026-06-06T15:00:00+00:00" } },
  ...extra,
});

describe("templateFor", () => {
  it("gives each sport its own standings layout and labels", () => {
    expect(templateFor("football").standings).toBe("league");
    expect(templateFor("basketball").standings).toBe("conference");
    expect(templateFor("formula-1").standings).toBe("championship");
    expect(templateFor("formula-1").tabs.standings).toBe("Şampiyona");
    expect(templateFor("unknown-sport").standings).toBe("league");
  });
});

describe("EventItem", () => {
  it("renders a race card for races and a scoreline for matches", () => {
    const { rerender } = render(
      <ul>
        <EventItem event={race()} />
      </ul>,
    );
    expect(screen.getByText("Monaco Grand Prix")).toBeInTheDocument();
    expect(screen.getByText("8. yarış")).toBeInTheDocument();
    rerender(
      <ul>
        <EventItem event={event()} />
      </ul>,
    );
    expect(screen.getByLabelText("2 - 1")).toBeInTheDocument();
  });
});

describe("RaceRow", () => {
  it("shows the podium and a collapsible full classification once finished", () => {
    render(
      <ul>
        <EventItem event={race()} />
      </ul>,
    );
    const podium = screen.getByRole("list", { name: "Podyum" });
    expect(within(podium).getAllByRole("listitem")).toHaveLength(3);
    expect(within(podium).getByRole("link", { name: "Max Verstappen" })).toHaveAttribute(
      "href",
      "/players/101",
    );
    expect(screen.getByText("Tüm sonuçlar")).toBeInTheDocument();
    const table = screen.getByRole("table", { name: "Yarış sonuçları" });
    expect(within(table).getAllByRole("row")).toHaveLength(5); // header + 4 drivers
  });

  it("shows the qualifying time instead of results before the race", () => {
    render(
      <ul>
        <EventItem event={race({ status: "scheduled", participants: [] })} />
      </ul>,
    );
    expect(screen.queryByRole("list", { name: "Podyum" })).not.toBeInTheDocument();
    expect(screen.getByText(/Sıralama turları/)).toBeInTheDocument();
  });
});

describe("ChampionshipTables", () => {
  const rows: Standing[] = [
    {
      position: 1,
      team: team(1, "Red Bull"),
      player: driver(101, "Max Verstappen"),
      played: 19,
      won: 6,
      drawn: 0,
      lost: 0,
      points: 270,
      extra: { kind: "driver" },
    },
    {
      position: 1,
      team: team(2, "McLaren"),
      player: null,
      played: 19,
      won: 4,
      drawn: 0,
      lost: 0,
      points: 410,
      extra: { kind: "constructor" },
    },
  ];

  it("renders separate driver and constructor championships", () => {
    render(<ChampionshipTables rows={rows} />);
    const drivers = screen.getByRole("table", { name: "Sürücüler şampiyonası" });
    const teams = screen.getByRole("table", { name: "Takımlar şampiyonası" });
    expect(within(drivers).getByText("Max Verstappen")).toBeInTheDocument();
    expect(within(drivers).getByText("270")).toBeInTheDocument();
    expect(within(teams).getByText("McLaren")).toBeInTheDocument();
    expect(within(teams).queryByText("Max Verstappen")).not.toBeInTheDocument();
  });
});

describe("ConferenceStandings", () => {
  const row = (
    id: number,
    name: string,
    conference: string,
    rank: number,
    won: number,
  ): Standing => ({
    position: id,
    team: team(id, name),
    player: null,
    played: 10,
    won,
    drawn: 0,
    lost: 10 - won,
    points: won,
    extra: { conference, conference_rank: rank, win_pct: won / 10, form: "W,L,W" },
  });

  it("splits teams by conference and orders by conference rank", () => {
    render(
      <ConferenceStandings
        rows={[
          row(1, "Boston Celtics", "East", 2, 6),
          row(2, "Denver Nuggets", "West", 1, 8),
          row(3, "Miami Heat", "East", 1, 7),
        ]}
      />,
    );
    const east = screen.getByRole("table", { name: "Doğu Konferansı sıralaması" });
    const west = screen.getByRole("table", { name: "Batı Konferansı sıralaması" });
    const eastTeams = within(east)
      .getAllByRole("rowheader")
      .map((h) => h.textContent);
    expect(eastTeams[0]).toContain("Miami Heat");
    expect(eastTeams[1]).toContain("Boston Celtics");
    expect(within(west).getAllByRole("rowheader")).toHaveLength(1);
    expect(within(east).getByText(".700")).toBeInTheDocument();
  });
});

describe("sport-specific positions", () => {
  it("maps basketball codes and F1 drivers to their own groups", () => {
    expect(positionGroup("G")).toBe("guard");
    expect(positionGroup("G-F")).toBe("guard");
    expect(positionGroup("F-C")).toBe("forward");
    expect(positionGroup("C")).toBe("center");
    expect(positionGroup("Driver")).toBe("driver");
    expect(positionGroup("Centre-Back")).toBe("defence");
  });

  it("groups a basketball roster guard -> forward -> center", () => {
    const p = (id: number, position: string): Player => ({
      ...driver(id, `P${id}`),
      position,
    });
    const groups = groupSquad([p(1, "C"), p(2, "G"), p(3, "F")]);
    expect(groups.map((g) => g.group)).toEqual(["guard", "forward", "center"]);
  });
});
