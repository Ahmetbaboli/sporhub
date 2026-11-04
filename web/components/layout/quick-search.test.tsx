import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { QuickSearch } from "@/components/layout/quick-search";
import { competition, team } from "@/tests/factories";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const RESULTS = {
  query: "gal",
  competitions: [competition({ id: 3, name: "Süper Lig", slug: "super-lig" })],
  teams: [team(111, "Galatasaray SK")],
  players: [],
};

describe("QuickSearch", () => {
  beforeEach(() => {
    push.mockReset();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(RESULTS), { status: 200 })),
    );
  });
  afterEach(() => vi.unstubAllGlobals());

  it("opens on Ctrl+K, shows instant results and opens the picked one with Enter", async () => {
    render(<QuickSearch />);
    expect(screen.queryByRole("dialog")).toBeNull();

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const box = screen.getByRole("combobox", { name: "Hızlı arama" });
    expect(box).toHaveFocus();
    expect(screen.getByText(/yazmaya başla/)).toBeInTheDocument();

    fireEvent.change(box, { target: { value: "gal" } });
    await waitFor(() =>
      expect(screen.getByRole("option", { name: /Galatasaray SK/ })).toBeInTheDocument(),
    );
    expect(fetch).toHaveBeenCalledWith("/api/quick-search?q=gal", expect.anything());
    expect(screen.getByText("Ligler")).toBeInTheDocument();
    expect(screen.getByText("Takımlar")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /tüm sonuçlar/ })).toBeInTheDocument();

    // Teams come first; one step down is the league.
    expect(screen.getByRole("option", { name: /Galatasaray SK/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    fireEvent.keyDown(box, { key: "ArrowDown" });
    fireEvent.keyDown(box, { key: "Enter" });
    expect(push).toHaveBeenCalledWith("/football/super-lig");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("closes with Escape and waits for two characters before asking", async () => {
    render(<QuickSearch />);
    fireEvent.click(screen.getByRole("button", { name: /Hızlı arama/ }));
    const box = screen.getByRole("combobox");
    fireEvent.change(box, { target: { value: "g" } });
    await act(() => new Promise((r) => setTimeout(r, 250)));
    expect(fetch).not.toHaveBeenCalled();
    fireEvent.keyDown(box, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("says so when the search fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 502 })),
    );
    render(<QuickSearch />);
    fireEvent.keyDown(window, { key: "/" });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "gal" } });
    await waitFor(() => expect(screen.getByText(/şu an yapılamadı/)).toBeInTheDocument());
  });
});
