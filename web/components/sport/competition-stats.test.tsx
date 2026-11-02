import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  boardTitle,
  CompetitionStatsView,
  formatLeaderValue,
} from "@/components/sport/competition-stats";
import { templateFor } from "@/lib/sports";
import type { CompetitionStats } from "@/lib/types";

const team = {
  id: 3,
  name: "Kulüp FC",
  short_name: "Kulüp",
  logo_url: null,
  country: null,
  sport_slug: "football",
};
const player = {
  id: 9,
  name: "Gol Makinesi",
  position: "Offence",
  nationality: null,
  team,
  extra: {},
};

const stats: CompetitionStats = {
  season: {
    id: 1,
    year_label: "2026/27",
    start_date: null,
    end_date: null,
    is_current: true,
  },
  matches: {
    played: 10,
    total_scored: 27,
    avg_per_match: 2.7,
    home_win_pct: 0.5,
    draw_pct: 0.2,
    away_win_pct: 0.3,
    biggest_win: null,
    highest_scoring: null,
  },
  races: null,
  leaders: [
    {
      key: "goals",
      subject: "player",
      rows: [{ rank: 1, player, team, value: 8, played: 9 }],
    },
    {
      key: "home_win_pct",
      subject: "team",
      rows: [{ rank: 1, player: null, team, value: 0.75, played: 4 }],
    },
  ],
  history: [
    {
      season: {
        id: 1,
        year_label: "2026/27",
        start_date: null,
        end_date: null,
        is_current: true,
      },
      leader: null,
    },
  ],
};

describe("leader formatting", () => {
  it("formats percentages, rates and counts", () => {
    expect(formatLeaderValue("home_win_pct", 0.756)).toBe("%76");
    expect(formatLeaderValue("best_attack", 2.5)).toBe("2.50");
    expect(formatLeaderValue("goals", 8)).toBe("8");
  });

  it("uses sport-specific titles", () => {
    expect(boardTitle("best_attack", "points")).toMatch(/skorer/);
    expect(boardTitle("goals", "goals")).toBe("Gol krallığı");
    expect(boardTitle("unknown", "goals")).toBe("unknown");
  });
});

describe("CompetitionStatsView", () => {
  it("renders the summary, the scorers board and season history", () => {
    render(<CompetitionStatsView stats={stats} template={templateFor("football")} />);
    expect(screen.getByRole("table", { name: "Gol krallığı" })).toHaveTextContent(
      "Gol Makinesi",
    );
    expect(screen.getByRole("link", { name: "Gol Makinesi" })).toHaveAttribute(
      "href",
      "/players/9",
    );
    expect(screen.getByText("Sezon geçmişi")).toBeInTheDocument();
    expect(screen.getByText("2.70")).toBeInTheDocument();
  });

  it("shows an empty state when nothing is available", () => {
    render(
      <CompetitionStatsView
        stats={{ ...stats, matches: null, leaders: [], history: [] }}
        template={templateFor("football")}
      />,
    );
    expect(screen.getByText(/henüz istatistik yok/)).toBeInTheDocument();
  });
});
