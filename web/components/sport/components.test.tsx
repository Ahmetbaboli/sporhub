import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EventRow } from "@/components/sport/event-row";
import { StandingsTable } from "@/components/sport/standings-table";
import { StatusBadge } from "@/components/sport/status-badge";
import { TeamBadge } from "@/components/sport/team-badge";
import { Pagination } from "@/components/ui/pagination";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { TabNav } from "@/components/ui/tab-nav";
import { event, standing, team } from "@/tests/factories";

describe("StatusBadge", () => {
  it("shows Turkish labels", () => {
    render(<StatusBadge status="live" />);
    expect(screen.getByText("Canlı")).toBeInTheDocument();
  });
});

describe("EventRow", () => {
  it("renders the score and a link to each team for finished matches", () => {
    render(
      <ul>
        <EventRow event={event()} showRound />
      </ul>,
    );
    expect(screen.getByLabelText("2 - 1")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Arsenal FC/ })).toHaveAttribute(
      "href",
      "/teams/1",
    );
    expect(screen.getByText("MS")).toBeInTheDocument();
    expect(screen.getByText("Hafta 9")).toBeInTheDocument();
  });

  it("renders a kick-off time instead of a score when scheduled", () => {
    const scheduled = event({
      status: "scheduled",
      participants: event().participants.map((p) => ({ ...p, score: null })),
    });
    const { container } = render(
      <ul>
        <EventRow event={scheduled} />
      </ul>,
    );
    expect(container.querySelector("time")).toHaveAttribute(
      "dateTime",
      "2026-10-26T17:30:00Z",
    );
    expect(screen.queryByText("MS")).not.toBeInTheDocument();
  });

  it("flags live matches", () => {
    render(
      <ul>
        <EventRow event={event({ status: "live" })} />
      </ul>,
    );
    expect(screen.getByText("Canlı")).toBeInTheDocument();
  });
});

describe("StandingsTable", () => {
  it("renders one row per team with accessible headers", () => {
    render(
      <StandingsTable
        rows={[
          standing(1, team(1, "Arsenal FC"), 19),
          standing(2, team(2, "Chelsea FC"), 17),
        ]}
      />,
    );
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    expect(
      within(table).getByRole("rowheader", { name: /Arsenal FC/ }),
    ).toBeInTheDocument();
    expect(within(table).getByRole("columnheader", { name: "P" })).toBeInTheDocument();
    expect(screen.getAllByText("18:9")).toHaveLength(2);
    expect(screen.getAllByText("+9")).toHaveLength(2);
  });

  it("is keyboard-scrollable inside its own region", () => {
    render(<StandingsTable rows={[]} />);
    expect(screen.getByRole("region", { name: "Puan durumu" })).toHaveAttribute(
      "tabindex",
      "0",
    );
  });
});

describe("TeamBadge", () => {
  it("falls back to initials when there is no logo", () => {
    render(<TeamBadge team={{ name: "Manchester City FC", logo_url: null }} />);
    expect(screen.getByText("MC")).toBeInTheDocument();
  });

  it("falls back to initials when the image fails to load", () => {
    const { container } = render(
      <TeamBadge team={{ name: "Arsenal FC", logo_url: "https://example.test/x.png" }} />,
    );
    fireEvent.error(container.querySelector("img")!);
    expect(screen.getByText("AR")).toBeInTheDocument();
  });
});

describe("states", () => {
  it("EmptyState shows title and body", () => {
    render(<EmptyState title="Boş" body="Burada bir şey yok" />);
    expect(screen.getByRole("heading", { name: "Boş" })).toBeInTheDocument();
    expect(screen.getByText("Burada bir şey yok")).toBeInTheDocument();
  });

  it("ErrorState is an alert and wires the retry button", () => {
    let retried = false;
    render(<ErrorState onRetry={() => (retried = true)} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tekrar dene" }));
    expect(retried).toBe(true);
  });
});

describe("Pagination", () => {
  const hrefFor = (p: number) => `/x?page=${p}`;

  it("renders nothing for a single page", () => {
    const { container } = render(
      <Pagination page={1} pageSize={20} total={15} hrefFor={hrefFor} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("links to previous and next pages", () => {
    render(<Pagination page={2} pageSize={20} total={50} hrefFor={hrefFor} />);
    expect(screen.getByRole("link", { name: "Önceki" })).toHaveAttribute(
      "href",
      "/x?page=1",
    );
    expect(screen.getByRole("link", { name: "Sonraki" })).toHaveAttribute(
      "href",
      "/x?page=3",
    );
    expect(screen.getByText("Sayfa 2 / 3")).toBeInTheDocument();
  });
});

describe("TabNav", () => {
  it("marks the active tab with aria-current", () => {
    render(
      <TabNav
        active="results"
        tabs={[
          { id: "fixtures", label: "Fikstür", href: "?tab=fixtures" },
          { id: "results", label: "Sonuçlar", href: "?tab=results" },
        ]}
      />,
    );
    expect(screen.getByRole("link", { name: "Sonuçlar" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Fikstür" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
