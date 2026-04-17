export type ColorScheme = "redToGreen" | "greenToRed" | "blueToRed";

const HUE_RANGES: Record<ColorScheme, [start: number, end: number]> = {
    blueToRed: [240, 360],
    greenToRed: [120, 0],
    redToGreen: [0, 120],
};

export function generateNumericColor(value: number, min: number, max: number, scheme: ColorScheme = "redToGreen"): string {
    const norm = Math.min(Math.max((value - min) / (max - min), 0), 1);
    const smoothNorm = 1 / (1 + Math.exp(-10 * (norm - 0.5)));

    const [start, end] = HUE_RANGES[scheme];
    const hue = Math.round(start + smoothNorm * (end - start));

    return `hsl(${hue}, 70%, 50%)`;
}

export function hsvToRgb(h: number, s: number, v: number): string {
    h = h % 360;
    const c = v * s;
    const x = c * (1 - Math.abs((h / 60) % 2 - 1));
    const m = v - c;

    let r = 0, g = 0, b = 0;
    if (h < 60) { [r, g, b] = [c, x, 0]; }
    else if (h < 120) { [r, g, b] = [x, c, 0]; }
    else if (h < 180) { [r, g, b] = [0, c, x]; }
    else if (h < 240) { [r, g, b] = [0, x, c]; }
    else if (h < 300) { [r, g, b] = [x, 0, c]; }
    else { [r, g, b] = [c, 0, x]; }

    const toHex = (n: number) => Math.round((n + m) * 255).toString(16).padStart(2, '0');
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

const BARCHART_COLOR_PALETTE_SIZE = 6;

/** Skip red/orange/yellow (0–80°), magenta, and red-violet (280°+). */
const BARCHART_HUE_MIN = 80;
const BARCHART_HUE_MAX = 280;

export const barchartColorPalette = Array.from({ length: BARCHART_COLOR_PALETTE_SIZE }, (_, i) => {
  const span = BARCHART_HUE_MAX - BARCHART_HUE_MIN;
  const hue =
    BARCHART_COLOR_PALETTE_SIZE <= 1
      ? Math.round((BARCHART_HUE_MIN + BARCHART_HUE_MAX) / 2)
      : Math.round(BARCHART_HUE_MIN + (i / (BARCHART_COLOR_PALETTE_SIZE - 1)) * span);
  return `hsl(${hue} 60% 53%)`;
});

export const summaryColorPalette = ["#36A2EB", "#FF6384", "#4BC0C0", "#9966FF", "#AA425E", "#FF0000", "#00FF00"];
export const statusQuoColor = "#FFCE56";