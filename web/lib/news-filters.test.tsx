import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NewsCard, tagHref } from "@/components/news/news-parts";
import { formatMonth, formatRelative } from "@/lib/format";
import { apiCategory, newsHref, parseNewsState } from "@/lib/news-filters";
import type { NewsItem } from "@/lib/types";

describe("parseNewsState", () => {
  it("keeps valid filters and drops junk", () => {
    const state = parseNewsState({
      category: "transfer",
      sport: "football",
      month: "2026-10",
      q: " Demir ",
      team: "7",
      page: "2",
    });
    expect(state).toMatchObject({
      tab: "transfer",
      sport: "football",
      month: "2026-10",
      q: "Demir",
      team: 7,
      page: 2,
    });
    const junk = parseNewsState({
      category: "x",
      sport: "<b>",
      month: "2026-13",
      q: "a",
      team: "-1",
      page: "0",
    });
    expect(junk).toEqual({ tab: "all", page: 1 });
  });
});

describe("newsHref", () => {
  const state = parseNewsState({ category: "interview", sport: "football", page: "3" });

  it("changes one filter and resets the page", () => {
    expect(newsHref(state, { month: "2026-09" })).toBe(
      "/news?category=interview&sport=football&month=2026-09",
    );
    expect(newsHref(state, { tab: "all", sport: undefined })).toBe("/news");
    expect(newsHref(state, { page: 4 })).toBe(
      "/news?category=interview&sport=football&page=4",
    );
  });

  it("maps tabs to API categories", () => {
    expect(apiCategory("all")).toBeUndefined();
    expect(apiCategory("breaking")).toBeUndefined();
    expect(apiCategory("transfer")).toBe("transfer");
  });
});

describe("time formatting", () => {
  const now = new Date("2026-11-02T12:00:00Z");

  it("is relative within a week", () => {
    expect(formatRelative("2026-11-02T10:00:00Z", now, "en-GB")).toBe("2 hours ago");
    expect(formatRelative("2026-11-02T11:55:00Z", now, "tr-TR")).toBe("5 dakika önce");
    expect(formatRelative("2026-10-31T12:00:00Z", now, "en-GB")).toBe("2 days ago");
  });

  it("falls back to a date after a week, and names months", () => {
    expect(formatRelative("2026-09-14T08:00:00Z", now, "en-GB")).toBe("14 Sept 2026");
    expect(formatMonth("2026-10", "tr-TR")).toBe("Ekim 2026");
  });
});

const item: NewsItem = {
  id: 5,
  title: "Kulüp yıldızını resmen açıkladı",
  summary: "Özet metni.",
  url: "https://example.com/a",
  image_url: null,
  author: null,
  source: "Örnek",
  published_at: new Date().toISOString(),
  category: "transfer_official",
  is_breaking: true,
  language: "tr",
  sport_slug: "football",
  tags: [
    { kind: "team", id: 1, name: "Kulüp FC", sport_slug: "football", slug: null },
    { kind: "competition", id: 2, name: "Lig", sport_slug: "football", slug: "lig" },
  ],
};

describe("NewsCard", () => {
  it("links the headline to our page and tags to entity pages", () => {
    render(<NewsCard item={item} />);
    expect(screen.getByRole("link", { name: item.title })).toHaveAttribute(
      "href",
      "/news/5",
    );
    expect(screen.getByText("Son dakika")).toBeInTheDocument();
    expect(screen.getByText("Resmî transfer")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Lig" })).toHaveAttribute(
      "href",
      "/football/lig",
    );
    expect(tagHref(item.tags[0])).toBe("/teams/1");
  });
});
