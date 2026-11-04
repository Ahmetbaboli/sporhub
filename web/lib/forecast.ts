/** Formatting for forecast chances (0..1). */

const NEARLY_NONE = 0.005;
const NEARLY_SURE = 0.995;

function percent(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    maximumFractionDigits: 0,
  }).format(value);
}

/** "%53", "<%1" for a sliver, ">%99" for nearly certain, "–" for no chance at all. */
export function formatChance(value: number, locale: string): string {
  if (value <= 0) return "–";
  if (value < NEARLY_NONE) return `<${percent(0.01, locale)}`;
  if (value >= 1) return percent(1, locale);
  if (value >= NEARLY_SURE) return `>${percent(0.99, locale)}`;
  return percent(value, locale);
}

/** Most likely finishing place range covering at least `mass` of the runs, 1-based. */
export function likelyRange(positions: number[], mass = 0.8): [number, number] {
  const best = positions.indexOf(Math.max(...positions));
  let lo = best;
  let hi = best;
  let covered = positions[best] ?? 0;
  while (covered < mass && (lo > 0 || hi < positions.length - 1)) {
    const left = lo > 0 ? positions[lo - 1] : -1;
    const right = hi < positions.length - 1 ? positions[hi + 1] : -1;
    if (left >= right) covered += positions[--lo];
    else covered += positions[++hi];
  }
  return [lo + 1, hi + 1];
}
