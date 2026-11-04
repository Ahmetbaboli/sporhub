/** Team kit colours from the provider ("#rrggbb"): contrast and clash helpers. */

const HEX = /^#([0-9a-f]{6})$/i;
// WCAG relative-luminance midpoint between black and white text.
const LIGHT_BACKGROUND = 0.179;
// Below this RGB distance two kits look alike on the pitch (0 = same, ~441 = black vs white).
const CLASH_DISTANCE = 120;

type Rgb = [number, number, number];

function rgb(hex: string): Rgb | null {
  const m = HEX.exec(hex);
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function luminance([r, g, b]: Rgb): number {
  const lin = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

/** Black or white, whichever reads better on `hex`. */
export function readableOn(hex: string): "#000000" | "#ffffff" {
  const c = rgb(hex);
  return c && luminance(c) > LIGHT_BACKGROUND ? "#000000" : "#ffffff";
}

export function colorDistance(a: string, b: string): number {
  const x = rgb(a);
  const y = rgb(b);
  if (!x || !y) return Infinity;
  return Math.hypot(x[0] - y[0], x[1] - y[1], x[2] - y[2]);
}

export interface KitColors {
  color?: string | null;
  alternate_color?: string | null;
}

/**
 * Colours for two teams side by side: home keeps its main colour; away uses its main one, or
 * its alternate when that would look like home's. Null when either side has no usable colour
 * (the caller keeps the theme colours rather than guessing).
 */
export function kitPair(home?: KitColors, away?: KitColors): [string, string] | null {
  const h = home?.color && HEX.test(home.color) ? home.color : null;
  if (!h) return null;
  const candidates = [away?.color, away?.alternate_color].filter((c): c is string =>
    Boolean(c && HEX.test(c)),
  );
  const a = candidates.find((c) => colorDistance(c, h) >= CLASH_DISTANCE);
  return a ? [h, a] : null;
}
