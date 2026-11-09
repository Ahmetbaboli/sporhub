/**
 * Share cards (Open Graph / X) drawn in code with next/og: the picture a link shows when it is
 * posted on WhatsApp, X, Slack... No provider images (crests, photos) are drawn: only our own
 * text and the clubs' colours, so a card can be shared anywhere.
 */
import { ImageResponse } from "next/og";
import type { ReactNode } from "react";

export const OG_SIZE = { width: 1200, height: 630 };
export const OG_TYPE = "image/png";

const BACKGROUND = "#0B1018";
const CARD = "#151E2C";
const TEXT = "#F3F6FA";
const MUTED = "#93A4B8";
export const PRIMARY = "#43C7F4";
export const ACCENT = "#FFAA45";
const HEX = /^#[0-9a-f]{6}$/i;

export function kitColor(color: string | null | undefined, fallback: string): string {
  return color && HEX.test(color) ? color : fallback;
}

/** Common frame: brand at the top, the content, the site address at the bottom. */
export function ogCard(
  content: ReactNode,
  opts: { eyebrow?: string; footer: string; glow?: [string, string] },
) {
  const [left, right] = opts.glow ?? [PRIMARY, ACCENT];
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: "56px 64px",
        color: TEXT,
        backgroundColor: BACKGROUND,
        backgroundImage: `radial-gradient(circle at 0% 0%, ${left}55, transparent 45%), radial-gradient(circle at 100% 100%, ${right}44, transparent 45%)`,
      }}
    >
      <div
        style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
      >
        <div style={{ display: "flex", fontSize: 40, letterSpacing: -1 }}>
          <span style={{ color: PRIMARY }}>JUST</span>
          <span style={{ color: ACCENT }}>SPORT</span>
        </div>
        {opts.eyebrow ? (
          <div style={{ display: "flex", fontSize: 28, color: MUTED }}>
            {opts.eyebrow}
          </div>
        ) : null}
      </div>
      <div
        style={{
          display: "flex",
          flex: 1,
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        {content}
      </div>
      <div style={{ display: "flex", fontSize: 24, color: MUTED }}>{opts.footer}</div>
    </div>,
    OG_SIZE,
  );
}

/** Stacks its children; next/og does not lay out a fragment's children as a column. */
export function OgColumn({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", width: "100%" }}>
      {children}
    </div>
  );
}

export function OgTitle({ children, size = 84 }: { children: ReactNode; size?: number }) {
  return (
    <div
      style={{
        display: "flex",
        flexShrink: 0,
        fontSize: size,
        lineHeight: 1.05,
        letterSpacing: -2,
      }}
    >
      {children}
    </div>
  );
}

export function OgSubtitle({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: "flex", marginTop: 20, fontSize: 34, color: MUTED }}>
      {children}
    </div>
  );
}

/** A team name with its kit colour as a bar beside it. */
export function OgTeam({
  name,
  color,
  align,
}: {
  name: string;
  color: string;
  align: "left" | "right";
}) {
  return (
    <div
      style={{
        display: "flex",
        flex: 1,
        flexDirection: align === "left" ? "row" : "row-reverse",
        alignItems: "center",
        gap: 24,
      }}
    >
      <div
        style={{
          display: "flex",
          width: 14,
          height: 120,
          borderRadius: 7,
          background: color,
        }}
      />
      <div
        style={{
          display: "flex",
          fontSize: name.length > 16 ? 46 : 58,
          lineHeight: 1.1,
          textAlign: align,
          justifyContent: align === "left" ? "flex-start" : "flex-end",
          maxWidth: 360,
        }}
      >
        {name}
      </div>
    </div>
  );
}

/** Small table rows (league card): place, name, points. */
export function OgRows({
  rows,
}: {
  rows: { place: number; name: string; value: string }[];
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        marginTop: 28,
        gap: 10,
        width: "100%",
      }}
    >
      {rows.map((r) => (
        <div
          key={r.place}
          style={{
            display: "flex",
            alignItems: "center",
            background: CARD,
            borderRadius: 14,
            padding: "12px 24px",
            fontSize: 32,
            width: "100%",
          }}
        >
          <span style={{ display: "flex", width: 56, color: MUTED }}>{r.place}</span>
          <span style={{ display: "flex", flex: 1 }}>{r.name}</span>
          <span style={{ display: "flex", color: PRIMARY }}>{r.value}</span>
        </div>
      ))}
    </div>
  );
}

export const OG_COLORS = { MUTED, CARD, TEXT };
