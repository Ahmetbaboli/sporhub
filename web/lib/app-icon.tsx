import { ImageResponse } from "next/og";

/** Brand colours of the default "Just Sport" palette (globals.css). */
const BACKGROUND = "#0B1018";
const PRIMARY = "#43C7F4";
const ACCENT = "#FFAA45";
/** Share of the square the letters may use; maskable icons need a safe centre zone. */
const LETTER_SCALE = 0.42;

/** The app icon ("JS" on the dark brand background), drawn at build time. */
export function appIcon(px: number): ImageResponse {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: BACKGROUND,
        fontSize: px * LETTER_SCALE,
        fontWeight: 800,
        letterSpacing: -px * 0.02,
      }}
    >
      <span style={{ color: PRIMARY }}>J</span>
      <span style={{ color: ACCENT }}>S</span>
    </div>,
    { width: px, height: px },
  );
}
