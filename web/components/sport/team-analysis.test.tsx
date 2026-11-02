import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FormStrip, TeamAnalysisPanel } from "@/components/sport/team-analysis";
import type { FormEntry, SplitStats, TeamAnalysis } from "@/lib/types";

const opponent = {
  id: 2,
  name: "Rakip FC",
  short_name: "Rakip",
  logo_url: null,
  country: null,
  sport_slug: "football",
};

function entry(id: number, scored: number, conceded: number): FormEntry {
  const result = scored > conceded ? "W" : scored < conceded ? "L" : "D";
  return {
    event_id: id,
    start_time: `2026-10-${String(30 - id).padStart(2, "0")}T18:00:00Z`,
    competition: "Lig",
    side: "home",
    opponent,
    scored,
    conceded,
    result,
  };
}

const stats = (over: Partial<SplitStats> = {}): SplitStats => ({
  played: 3,
  won: 2,
  drawn: 1,
  lost: 0,
  scored: 5,
  conceded: 1,
  win_pct: 0.67,
  avg_scored: 1.67,
  avg_conceded: 0.33,
  clean_sheets: 2,
  ...over,
});

const form = [entry(1, 2, 0), entry(2, 1, 1), entry(3, 2, 1)];

const analysis: TeamAnalysis = {
  team: { ...opponent, id: 1, name: "Biz" },
  season: "2026/27",
  form,
  form_stats: stats(),
  streak: "W1",
  overall: stats(),
  home: stats({ win_pct: 1 }),
  away: stats({ win_pct: 0.5 }),
  biggest_win: form[0],
  biggest_loss: null,
};

describe("FormStrip", () => {
  it("shows the newest result last with an accessible description", () => {
    render(<FormStrip form={form} />);
    const items = screen.getAllByRole("link");
    expect(items).toHaveLength(3);
    expect(items[2]).toHaveTextContent("Galibiyet, 2-0, Rakip FC");
    expect(items[0]).toHaveAttribute("href", "/teams/2");
  });
});

describe("TeamAnalysisPanel", () => {
  it("renders form, streak and home/away splits for football", () => {
    render(
      <TeamAnalysisPanel
        analysis={analysis}
        rules={{ draws: true, cleanSheets: true, unit: "goals" }}
      />,
    );
    expect(screen.getByText("1 maçtır kazanıyor", { exact: false })).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getByRole("columnheader", { name: "B" })).toBeInTheDocument();
    expect(within(table).getByRole("row", { name: /İç saha/ })).toHaveTextContent("%100");
    expect(screen.getByText(/Gol yemediği maç: 2/)).toBeInTheDocument();
  });

  it("hides draws and clean sheets for basketball", () => {
    render(
      <TeamAnalysisPanel
        analysis={analysis}
        rules={{ draws: false, cleanSheets: false, unit: "points" }}
      />,
    );
    const table = screen.getByRole("table");
    expect(within(table).queryByRole("columnheader", { name: "B" })).toBeNull();
    expect(screen.queryByText(/Gol yemediği/)).toBeNull();
  });

  it("renders nothing without matches", () => {
    const { container } = render(
      <TeamAnalysisPanel
        analysis={{ ...analysis, form: [] }}
        rules={{ draws: true, cleanSheets: true, unit: "goals" }}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
