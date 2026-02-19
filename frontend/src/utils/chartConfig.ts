// ── Color palette ──────────────────────────────────────────────────────────
export const COLORS = {
  green:  '#22c55e',
  blue:   '#38bdf8',
  red:    '#f87171',
  orange: '#fb923c',
  purple: '#a78bfa',
  yellow: '#fbbf24',
  slate:  '#475569',
} as const;

// Pie slice palettes
export const PIE_COLORS_LIGHT = [COLORS.slate,  COLORS.yellow]; // DARK, BRIGHT
export const PIE_COLORS_SOIL  = [COLORS.orange, COLORS.blue];   // DRY,  WET

// ── Data-shape types ───────────────────────────────────────────────────────
export interface AreaPoint    { time: string; value: number | null }
export interface DualPoint    { time: string; temp: number | null; hum: number | null }
export interface PiePoint     { name: string; value: number }
export interface BarPoint     { name: string; value: number }

// ── Builders ───────────────────────────────────────────────────────────────

/** Single-series area / line chart */
export function areaData(
  labels: string[],
  values: (number | null)[],
): AreaPoint[] {
  return labels.map((time, i) => ({ time, value: values[i] ?? null }));
}

/** Dual-line chart (Temp vs Humidity) */
export function dualLineData(
  labels: string[],
  temps: (number | null)[],
  hums:  (number | null)[],
): DualPoint[] {
  return labels.map((time, i) => ({
    time,
    temp: temps[i] ?? null,
    hum:  hums[i]  ?? null,
  }));
}

/** Pie / Doughnut chart */
export function pieData(obj: Record<string, number>): PiePoint[] {
  return Object.entries(obj).map(([name, value]) => ({ name, value }));
}

/** Bar chart */
export function barData(obj: Record<string, number>): BarPoint[] {
  return Object.entries(obj).map(([name, value]) => ({ name, value }));
}
