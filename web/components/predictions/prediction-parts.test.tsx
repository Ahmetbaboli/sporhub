import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  PredictionHistory,
  PredictionRow,
  PredictionScoreboard,
} from "@/components/predictions/prediction-parts";
import { readPredictions, writePredictions } from "@/lib/predictions";
import { event } from "@/tests/factories";

const FUTURE = new Date(Date.now() + 86_400_000).toISOString();
const PAST = new Date(Date.now() - 86_400_000).toISOString();

describe("prediction game", () => {
  beforeEach(() => {
    localStorage.clear();
    writePredictions({});
  });
  afterEach(() => vi.unstubAllGlobals());

  it("saves a prediction once both scores are typed", () => {
    render(
      <ul>
        <PredictionRow
          event={event({ id: 5, status: "scheduled", start_time: FUTURE })}
        />
      </ul>,
    );
    fireEvent.change(screen.getByLabelText("Arsenal FC golü"), {
      target: { value: "2" },
    });
    expect(readPredictions()[5]).toBeUndefined();
    fireEvent.change(screen.getByLabelText("Chelsea FC golü"), {
      target: { value: "1" },
    });
    expect(readPredictions()[5]).toMatchObject({
      home: 2,
      away: 1,
      homeName: "Arsenal FC",
      competition: "Premier League",
    });
    expect(screen.getByLabelText("Kaydedildi")).toBeInTheDocument();
  });

  it("locks the boxes once the match has started", () => {
    render(
      <ul>
        <PredictionRow event={event({ id: 6, status: "live", start_time: PAST })} />
      </ul>,
    );
    expect(screen.getByLabelText("Arsenal FC golü")).toBeDisabled();
    expect(screen.getByLabelText(/tahmin kilitli/)).toBeInTheDocument();
  });

  it("fetches results for played matches and scores them", async () => {
    writePredictions({
      9: {
        eventId: 9,
        home: 2,
        away: 1,
        kickoff: PAST,
        homeName: "Galatasaray",
        awayName: "Fenerbahçe",
        competition: "Süper Lig",
      },
    });
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ finished: [{ eventId: 9, home: 2, away: 1 }] })),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(
      <>
        <PredictionScoreboard />
        <PredictionHistory />
      </>,
    );
    await waitFor(() => expect(screen.getByText("+3")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/prediction-results?ids=9",
      expect.anything(),
    );
    expect(
      screen.getByText("Tahminin 2-1 · Maç 2-1", { exact: false }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
