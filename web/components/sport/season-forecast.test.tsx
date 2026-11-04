import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MatchForecastBar } from "@/components/match/match-forecast";
import { SeasonForecastView } from "@/components/sport/season-forecast";
import type { SeasonForecast, TeamForecast } from "@/lib/types";
import { competition, event, team } from "@/tests/factories";

const row = (id: number, name: string, extra: Partial<TeamForecast>): TeamForecast => ({
  team: team(id, name),
  elo: 1500,
  played: 10,
  points: 20,
  goal_difference: 0,
  expected_points: 60,
  positions: [0.5, 0.3, 0.2],
  title: 0.5,
  top: 0.9,
  relegation: 0,
  ...extra,
});

const forecast = (extra: Partial<SeasonForecast> = {}): SeasonForecast => ({
  competition: competition(),
  season: "2026/27",
  available: true,
  reason: null,
  simulations: 10000,
  played: 90,
  remaining: 216,
  top_spots: 2,
  top_kind: "europe",
  relegation_spots: 1,
  teams: [
    row(1, "Galatasaray SK", { title: 0.53, expected_points: 69.9 }),
    row(2, "Trabzonspor", { title: 0.25, top: 0.88 }),
    row(3, "Eyüpspor", {
      title: 0,
      top: 0,
      relegation: 0.97,
      positions: [0, 0.03, 0.97],
    }),
  ],
  generated_at: null,
  ...extra,
});

describe("SeasonForecastView", () => {
  it("shows title, Europe and relegation chances per team", () => {
    render(<SeasonForecastView forecast={forecast()} />);
    const table = screen.getByRole("table");
    expect(within(table).getByText("Avrupa")).toBeInTheDocument();
    expect(within(table).getByText("Düşme")).toBeInTheDocument();
    const gs = screen.getByRole("row", { name: /Galatasaray SK/ });
    expect(within(gs).getByText("%53")).toBeInTheDocument();
    expect(within(gs).getByText("70")).toBeInTheDocument(); // expected points, rounded
    const eyup = screen.getByRole("row", { name: /Eyüpspor/ });
    expect(within(eyup).getByText("%97")).toBeInTheDocument();
    expect(screen.getByText(/10.000 kez oynatıldı/)).toBeInTheDocument();
  });

  it("uses a top-N column and no relegation where the league has none", () => {
    render(
      <SeasonForecastView
        forecast={forecast({ top_kind: "top", top_spots: 8, relegation_spots: null })}
      />,
    );
    expect(screen.getByText("İlk 8")).toBeInTheDocument();
    expect(screen.queryByText("Düşme")).toBeNull();
  });

  it("explains why there is no forecast", () => {
    render(
      <SeasonForecastView
        forecast={forecast({ available: false, reason: "unsupported" })}
      />,
    );
    expect(screen.getByText(/eleme\/kupa/)).toBeInTheDocument();
  });
});

describe("MatchForecastBar", () => {
  it("shows the three outcomes for an upcoming match", () => {
    render(
      <MatchForecastBar
        event={event({ status: "scheduled" })}
        forecast={{
          event_id: 1,
          available: true,
          reason: null,
          home: 0.51,
          draw: 0.23,
          away: 0.26,
          home_elo: 1607.1,
          away_elo: 1579.9,
        }}
      />,
    );
    expect(screen.getByText("%51")).toBeInTheDocument();
    expect(screen.getByText("Beraberlik")).toBeInTheDocument();
    expect(screen.getByText(/Elo 1607 – 1580/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sezon olasılıkları" })).toHaveAttribute(
      "href",
      "/football/premier-league?tab=forecast",
    );
  });

  it("renders nothing without odds", () => {
    const { container } = render(<MatchForecastBar event={event()} forecast={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});
