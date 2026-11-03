/**
 * Colour palettes layered on top of light/dark mode. The choice lives in localStorage and is
 * applied as `data-palette` on <html> by an inline script before first paint (no flash).
 * Colours themselves are CSS variables in app/globals.css.
 */
export const PALETTES = [
  "justsport",
  "pitch",
  "ocean",
  "crimson",
  "violet",
  "sunset",
  "contrast",
] as const;
export type Palette = (typeof PALETTES)[number];

export const DEFAULT_PALETTE: Palette = "justsport";
export const PALETTE_STORAGE_KEY = "justsport-palette";

/** Swatch colour shown in the picker (the palette's light-mode primary). */
export const PALETTE_SWATCHES: Record<Palette, string> = {
  justsport: "#43c7f4",
  pitch: "#0e4a36",
  ocean: "#0b4f8a",
  crimson: "#a3122a",
  violet: "#5b2a9e",
  sunset: "#b4430b",
  contrast: "#000000",
};

export function parsePalette(value: string | null | undefined): Palette {
  return PALETTES.includes(value as Palette) ? (value as Palette) : DEFAULT_PALETTE;
}

/** Runs inline in <head>; must stay self-contained (no imports, no closures). */
export const PALETTE_BOOT_SCRIPT = `try{var p=localStorage.getItem(${JSON.stringify(
  PALETTE_STORAGE_KEY,
)});if(${JSON.stringify(PALETTES)}.indexOf(p)>0)document.documentElement.dataset.palette=p}catch(e){}`;
