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
export interface HeatmapPoint { temp: number; hum: number; count: number }
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

/** Heatmap bins for temperature (x) vs humidity (y), value=count */
export function tempHumidityHeatmapData(
  temps: (number | null)[],
  hums: (number | null)[],
  tempStep = 1,
  humStep = 1,
): HeatmapPoint[] {
  const buckets = new Map<string, number>();
  const safeTempStep = Number.isFinite(tempStep) && tempStep > 0 ? tempStep : 1;
  const safeHumStep = Number.isFinite(humStep) && humStep > 0 ? humStep : 1;
  const scale = 1_000_000;
  const keyOf = (tempBin: number, humBin: number) => `${tempBin.toFixed(6)}|${humBin.toFixed(6)}`;

  let minTemp: number | null = null;
  let maxTemp: number | null = null;
  let minHum: number | null = null;
  let maxHum: number | null = null;

  temps.forEach((temp, i) => {
    const hum = hums[i];
    if (temp == null || hum == null || Number.isNaN(temp) || Number.isNaN(hum)) {
      return;
    }

    // Round raw sensor values first, then bucket for frequency counting.
    const roundedTemp = Math.round(temp);
    const roundedHum = Math.round(hum);
    const tempBin = Math.round(roundedTemp / safeTempStep) * safeTempStep;
    const humBin = Math.round(roundedHum / safeHumStep) * safeHumStep;
    const key = keyOf(tempBin, humBin);
    const existing = buckets.get(key) ?? 0;

    buckets.set(key, existing + 1);

    minTemp = minTemp == null ? tempBin : Math.min(minTemp, tempBin);
    maxTemp = maxTemp == null ? tempBin : Math.max(maxTemp, tempBin);
    minHum = minHum == null ? humBin : Math.min(minHum, humBin);
    maxHum = maxHum == null ? humBin : Math.max(maxHum, humBin);
  });

  if (minTemp == null || maxTemp == null || minHum == null || maxHum == null) {
    return [];
  }

  // Always keep a ±10 margin from observed min/max on both axes.
  const expandedMinTemp = minTemp - 2;
  const expandedMaxTemp = maxTemp + 2;
  const expandedMinHum = minHum - 2;
  const expandedMaxHum = maxHum + 2;

  const tempStart = Math.round((expandedMinTemp * scale) / (safeTempStep * scale));
  const tempEnd = Math.round((expandedMaxTemp * scale) / (safeTempStep * scale));
  const humStart = Math.round((expandedMinHum * scale) / (safeHumStep * scale));
  const humEnd = Math.round((expandedMaxHum * scale) / (safeHumStep * scale));

  const points: HeatmapPoint[] = [];
  for (let ti = tempStart; ti <= tempEnd; ti += 1) {
    const tempBin = ti * safeTempStep;
    for (let hi = humStart; hi <= humEnd; hi += 1) {
      const humBin = hi * safeHumStep;
      const key = keyOf(tempBin, humBin);
      points.push({
        temp: Number(tempBin.toFixed(6)),
        hum: Number(humBin.toFixed(6)),
        count: buckets.get(key) ?? 0,
      });
    }
  }

  return points.sort((a, b) => {
    if (a.temp !== b.temp) {
      return a.temp - b.temp;
    }
    return a.hum - b.hum;
  });
}

/** Pie / Doughnut chart */
export function pieData(obj: Record<string, number>): PiePoint[] {
  return Object.entries(obj).map(([name, value]) => ({ name, value }));
}

/** Bar chart */
export function barData(obj: Record<string, number>): BarPoint[] {
  return Object.entries(obj).map(([name, value]) => ({ name, value }));
}
